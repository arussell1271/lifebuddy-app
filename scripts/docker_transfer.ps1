<#
.SYNOPSIS
Transfers (backs up or restores) the PostgreSQL database volume data.

.DESCRIPTION
This script handles the robust transfer of the dev_postgres_data volume 
to or from a local backup file (postgres_backup.tar.gz).

.PARAMETER Direction
Specifies the direction of the transfer:
    'From' (Backup): Stops the database container and archives the volume to a local file.
    'To' (Restore): Restores the volume from a local archive and starts the containers.

.PARAMETER ComposeFilePath
The absolute path to the docker compose configuration file (e.g., lifebuddy-app.yml).

.EXAMPLE
# Called from manager.bat:
# powershell.exe -File .\docker_transfer.ps1 -Direction From -ComposeFilePath "C:\path\lifebuddy-app.yml"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('From', 'To')]
    [string]$Direction,
    
    [Parameter(Mandatory = $true)]
    [string]$ComposeFilePath, 

    # Accept the profile name
    [Parameter(Mandatory = $true)]
    [string]$ProfileName
)

# --- Configuration ---
# ProjectName MUST match the prefix used by your Docker volumes (lifebuddy-app).
$ProjectName = "lifebuddy-app" 
# FIX: Use the absolute path passed from the batch file
$ComposeFileName = $ComposeFilePath 
# Volume name is hardcoded based on your docker-compose.yml: dev_postgres_data
# If profile is dev, use dev_postgres_data. If prod, use prod_postgres_data.
$InternalVolumeName = if ($ProfileName -eq "dev") { "dev_postgres_data" } else { "prod_postgres_data" }
$VolumeName = "${ProjectName}_${InternalVolumeName}"

$BackupFileName = "postgres_backup_$($ProfileName).tar.gz" # Profile-specific backup file
# Backup Path: Set the path to the 'backups' directory one level up from the script's location
$BackupPath = Join-Path -Path $PSScriptRoot -ChildPath '..\backups' 
# ---------------------

function StopAndRemoveOrphans {
    Write-Host "Stopping all project services..." -ForegroundColor Yellow
    # FIX: Use -p $ProjectName and -f $ComposeFileName for robustness.
    docker compose -p $ProjectName -f $ComposeFileName stop
    
    # Use 'down' to remove containers and orphaned resources, but KEEP VOLUMES (-v is omitted)
    Write-Host "Shutting down services for profile '$ProfileName' to ensure data consistency..." -ForegroundColor Yellow
    # Added -p for project isolation and --profile to target the right services
    docker compose -f $ComposeFileName -p $ProjectName --profile $ProfileName down --remove-orphans
    
    # The network warning 'Resource is still in use' (lifebuddy_core-network) can be ignored here.
}

function StartContainers {
    Write-Host "Restarting services for profile '$ProfileName'..." -ForegroundColor Cyan
    # Added -p and --profile to ensure the correct environment starts back up
    docker compose -f $ComposeFileName -p $ProjectName --profile $ProfileName up -d

    docker volume prune -f
        
    # --- START OF NEW WAIT/RETRY LOGIC ---
    # $OllamaReady = $false
    # $MaxRetries = 5
    # $RetryCount = 0
    # $WaitTimeSeconds = 5

    # Write-Host "Waiting for Ollama API to be ready (up to $($MaxRetries * $WaitTimeSeconds) seconds)..." -ForegroundColor Magenta
    
    # while (-not $OllamaReady -and $RetryCount -lt $MaxRetries) {
    # Check if the service name 'ollama' is resolvable and the port is listening.
    # docker compose exec ollama curl -s --fail http://ollama:11434/api/tags 2>&1 | Out-Null

    # if ($LASTEXITCODE -eq 0) {
    #     $OllamaReady = $true
    #     Write-Host "✅ Ollama API is ready." -ForegroundColor Green
    # }
    # else {
    #     $RetryCount++
    #     Write-Host "Ollama not ready. Retrying in $($WaitTimeSeconds)s... (Attempt $($RetryCount)/$MaxRetries)" -ForegroundColor Yellow
    #     Start-Sleep -Seconds $WaitTimeSeconds
    # }
    # }
    
    # if (-not $OllamaReady) {
    #     Write-Host "❌ Error: Ollama API failed to start after multiple retries. Skipping model pull." -ForegroundColor Red
    #     return # Exit the function early if Ollama isn't ready
    # }
    # --- END OF NEW WAIT/RETRY LOGIC ---

    # Pull the latest Mistral model into the running Ollama container
    # Write-Host "Pulling the latest Mistral model for Ollama..." -ForegroundColor Magenta
    # docker compose exec ollama ollama pull mistral
    
    # if ($LASTEXITCODE -eq 0) {
    #     Write-Host "✅ Ollama model pull successful." -ForegroundColor Green
    # }
    # else {
    #     Write-Host "⚠️ Warning: Ollama model pull failed. Check the container logs." -ForegroundColor Yellow
    # }
}

if ($Direction -eq 'From') {
    # === BACKUP (FROM container TO local directory) ===
    Write-Host "=== Starting Database Backup (FROM Container) ===" -ForegroundColor Cyan
    
    StopAndRemoveOrphans
    
    Write-Host "Archiving data from volume '$VolumeName' to local file '$BackupFileName'..." -ForegroundColor Yellow

    # Archive command: Uses a temporary Alpine container to tar the volume's contents
    $BackupCommand = "tar cvzf /backup/$BackupFileName -C /volume ."
    
    $DockerRunParams = @(
        'run', '--rm',
        # Corrected syntax: Use ${} for variable expansion in complex strings
        '-v', "${VolumeName}:/volume",
        '-v', "${BackupPath}:/backup",
        'alpine',
        'sh', '-c', $BackupCommand
    )
    
    docker @DockerRunParams
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backup successful! Data saved to $($BackupPath)\$($BackupFileName)" -ForegroundColor Green
        StartContainers
    }
    else {
        Write-Host "❌ Backup failed. Check Docker logs." -ForegroundColor Red
    }

}
elseif ($Direction -eq 'To') {
    # === RESTORE (FROM local directory TO container) ===
    Write-Host "=== Starting Database Restore (TO Container) ===" -ForegroundColor Cyan
    
    if (-not (Test-Path "$BackupPath\$BackupFileName")) {
        Write-Host "❌ Error: Backup file '$BackupFileName' not found at $($BackupPath)." -ForegroundColor Red
        return
    }
    
    StopAndRemoveOrphans
    
    Write-Host "Removing old volume data '$VolumeName' to prepare for restore..." -ForegroundColor Yellow
    # FIX: Use 2>&1 | Out-Null to suppress errors and command output robustly (fixes "unknown shorthand flag: 'E'" error).
    docker volume rm $VolumeName 2>&1 | Out-Null
    
    Write-Host "Restoring data from '$BackupFileName' to volume '$VolumeName'..." -ForegroundColor Yellow
    
    # Restore command: Extracts the archive to the newly created volume
    $RestoreCommand = "mkdir -p /volume; tar xvzf /backup/$BackupFileName -C /volume"
    
    $DockerRunParams = @(
        'run', '--rm',
        # Corrected syntax: Use ${} for variable expansion in complex strings
        '-v', "${VolumeName}:/volume",
        '-v', "${BackupPath}:/backup",
        'alpine',
        'sh', '-c', $RestoreCommand
    )
    
    docker @DockerRunParams
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Restore successful! Starting containers..." -ForegroundColor Green
        StartContainers
    }
    else {
        Write-Host "❌ Restore failed. Check Docker logs." -ForegroundColor Red
    }
}