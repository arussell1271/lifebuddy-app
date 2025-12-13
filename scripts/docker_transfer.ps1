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

.EXAMPLE
.\DB-Transfer.ps1 -Direction From
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('From', 'To')]
    [string]$Direction
)

# --- Configuration ---
# ProjectName is determined by your folder name (e.g., 'LifeBuddy'). 
# We'll use 'lifebuddy' as the prefix for volumes based on previous successful commands.
$ProjectName = "lifebuddy-app" 
# Volume name is hardcoded based on your docker-compose.yml: dev_postgres_data
$VolumeName = "$($ProjectName)_dev_postgres_data"
$BackupFileName = "postgres_backup.tar.gz"
# Backup Path: Set the path to the 'backups' directory one level up from the script's location
$BackupPath = Join-Path -Path $PSScriptRoot -ChildPath '..\backups' # Local directory where the script is run
# ---------------------

function StopAndRemoveOrphans {
    Write-Host "Stopping all project services..." -ForegroundColor Yellow
    # Stopping services ensures the database is not actively writing to the volume
    docker compose stop
    
    # Use 'down' to remove containers and orphaned resources, but KEEP VOLUMES (-v is omitted)
    Write-Host "Removing containers and checking for orphans..." -ForegroundColor Yellow
    docker compose down --remove-orphans
    
    # The network warning 'Resource is still in use' (lifebuddy_core-network) can be ignored here.
}

function StartContainers {
    Write-Host "Starting all development services..." -ForegroundColor Green
    # This uses the specific, corrected command structure to ensure all required dev services start properly.
    docker compose -p lifebuddy up -d dev_db app cognitive-engine pgadmin open_webui ollama
    
    # --- START OF NEW WAIT/RETRY LOGIC ---
    $OllamaReady = $false
    $MaxRetries = 12
    $RetryCount = 0
    $WaitTimeSeconds = 5

    Write-Host "Waiting for Ollama API to be ready (up to $($MaxRetries * $WaitTimeSeconds) seconds)..." -ForegroundColor Magenta
    
    while (-not $OllamaReady -and $RetryCount -lt $MaxRetries) {
        # Use curl to check if the Ollama API's health endpoint is reachable
        # We use a temp container for this check since the core services might not be fully up yet.
        # Check if the service name 'ollama' is resolvable and the port is listening.
        docker compose exec ollama curl -s --fail http://ollama:11434/api/tags 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            $OllamaReady = $true
            Write-Host "✅ Ollama API is ready." -ForegroundColor Green
        }
        else {
            $RetryCount++
            Write-Host "Ollama not ready. Retrying in $($WaitTimeSeconds)s... (Attempt $($RetryCount)/$MaxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds $WaitTimeSeconds
        }
    }
    
    if (-not $OllamaReady) {
        Write-Host "❌ Error: Ollama API failed to start after multiple retries. Skipping model pull." -ForegroundColor Red
        return # Exit the function early if Ollama isn't ready
    }
    # --- END OF NEW WAIT/RETRY LOGIC ---

    # Pull the latest Mistral model into the running Ollama container
    Write-Host "Pulling the latest Mistral model for Ollama..." -ForegroundColor Magenta
    # Use 'docker compose exec' to run the ollama command inside the running 'ollama' service container
    docker compose exec ollama ollama pull mistral
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Ollama model pull successful." -ForegroundColor Green
    }
    else {
        # The ollama container might take a moment to be ready, hence the warning instead of failure.
        Write-Host "⚠️ Warning: Ollama model pull failed. Check the container logs." -ForegroundColor Yellow
    }
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
    # This ensures a clean slate for the restore.
    docker volume rm $VolumeName -ErrorAction SilentlyContinue | Out-Null
    
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