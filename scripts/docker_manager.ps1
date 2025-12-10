# docker_manager.ps1 - Core Docker Compose Management Script

## 🚀 Execution Function - Entry Point
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("rebuild", "stop", "remove_all", "remove_project")]
    [string]$Action,
    
    # New parameter to accept the full path to the docker-compose file
    [Parameter(Mandatory = $true)]
    [string]$ComposeFilePath, 

    # Parameter to accept the profile name (e.g., 'dev' or 'prod')
    [string]$ProfileName 
)

# -----------------------------------------------------------------------------
## ⚙️ Helper Functions
# -----------------------------------------------------------------------------

# Helper function to execute docker-compose commands with the specified compose file and profile
function Invoke-DockerCompose {
    param(
        [string]$Command,
        [string]$ComposeFilePath,
        [string]$ProfileName
    )
    
    # 1. Start building the argument list for the native 'docker' command
    # Use -f to explicitly specify the file name using the passed parameter
    $dockerArgs = @("compose", "-f", $ComposeFilePath)

    # 2. Add the optional --profile argument if a profile name was provided
    if (-not [string]::IsNullOrWhiteSpace($ProfileName)) {
        $dockerArgs += @("--profile", $ProfileName)
    }
    
    # 3. Add the specific command and its parameters
    $commandArray = $Command -split ' ' | Where-Object { $_ }
    $dockerArgs += $commandArray 

    # Execute the command
    $output = docker @dockerArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker Compose command failed: $Command" -ForegroundColor Red
        return $null
    }
    
    return $output
}

# -----------------------------------------------------------------------------
## ⚙️ Core Management Functions
# -----------------------------------------------------------------------------

# 1. Start Up/Rebuild
function Start-DockerServices {
    param([string]$ComposeFilePath, [string]$ProfileName)
    Write-Host "Starting/Rebuilding Docker services using file '$ComposeFilePath' with profile '$ProfileName'..." -ForegroundColor Green
    
    # Use the command arguments: 'up -d --build'
    Invoke-DockerCompose "up -d --build --force-recreate " $ComposeFilePath -ProfileName $ProfileName
}

# 2. Shut Down
function Stop-DockerServices {
    param([string]$ComposeFilePath, [string]$ProfileName)
    Write-Host "Stopping and removing Docker services for profile '$ProfileName' using file '$ComposeFilePath'..." -ForegroundColor Yellow

    # 'down' stops and removes containers, networks, and default volumes
    Invoke-DockerCompose "down" -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName
}

# 3. Remove / Delete All (System-wide)
function Remove-AllDockerAssets {
    # Note: This function remains system-wide and does not use the Compose file path
    Write-Host "--- WARNING: EXTREME CLEANUP MODE INITIATED (System-wide) ---" -ForegroundColor Red
    
    Write-Host "Stopping all running containers..." -ForegroundColor Red
    docker stop $(docker ps -aq) 2>$null 

    Write-Host "Removing all containers..." -ForegroundColor Red
    docker rm $(docker ps -aq) -f 2>$null 

    Write-Host "Removing all unused volumes..." -ForegroundColor Red
    docker volume prune -f

    Write-Host "Removing all unused images..." -ForegroundColor Red
    docker image prune -a -f

    Write-Host "Docker system assets (containers, volumes, images) cleaned." -ForegroundColor Green
}

# 4. Remove / Delete Project Assets (Project-specific)
function Remove-ProjectDockerAssets {
    param([string]$ComposeFilePath, [string]$ProfileName)
    Write-Host "Stopping and removing project containers and volumes for profile '$ProfileName' defined in file '$ComposeFilePath'..." -ForegroundColor Yellow
    
    # Use 'down --volumes' to also remove named volumes associated with the services
    Invoke-DockerCompose "down --volumes" -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName

    Write-Host "Attempting to remove project images..." -ForegroundColor Yellow
    
    # Get service names using the profile context
    $services = (Invoke-DockerCompose "config --services" -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName) -split "`n" | Where-Object { $_ }
    
    foreach ($service in $services) {
        # Get the image name.
        $imageName = (Invoke-DockerCompose "config --images --services $service" -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName).Trim()
        
        if (-not [string]::IsNullOrWhiteSpace($imageName)) { 
            Write-Host "Attempting to remove image: $imageName" -ForegroundColor Cyan
            docker rmi -f $imageName 2>$null 
        }
    }

    Write-Host "Project containers, volumes, and images removed." -ForegroundColor Green
}

# -----------------------------------------------------------------------------
## 🚀 Execution Logic
# -----------------------------------------------------------------------------

# Use the -ComposeFilePath parameter for all relevant actions
switch ($Action) {
    "rebuild" { Start-DockerServices -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName }
    "stop" { Stop-DockerServices -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName }
    "remove_all" { Remove-AllDockerAssets }
    "remove_project" { Remove-ProjectDockerAssets -ComposeFilePath $ComposeFilePath -ProfileName $ProfileName }
    default { Write-Host "Invalid action specified." -ForegroundColor Red }
}