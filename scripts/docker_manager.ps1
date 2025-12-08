# DockerManager.ps1

## ⚙️ Core Functions (Modified to accept -ProjectRoot)

# Helper function to execute docker-compose commands
function Invoke-DockerCompose {
    param(
        [string]$Command,
        [string]$ProjectRoot
    )
    # The -f flag tells docker-compose where the file is.
    # If the file is named docker-compose.yml, -f is technically not needed,
    # but the -p (project-name) and --project-directory are the most robust ways
    # to control the execution context from another location.
    
    # Using '--project-directory' is the simplest way to specify the context.
    docker-compose --project-directory $ProjectRoot $Command
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker Compose command failed: $Command" -ForegroundColor Red
        return $false
    }
    return $true
}

# 1. Start Up/Rebuild
function Start-DockerServices {
    param([string]$ProjectRoot)
    Write-Host "Starting/Rebuilding Docker services in $ProjectRoot..." -ForegroundColor Green
    Invoke-DockerCompose "up --build -d" -ProjectRoot $ProjectRoot
}

# 2. Shut Down
function Stop-DockerServices {
    param([string]$ProjectRoot)
    Write-Host "Stopping and removing Docker services in $ProjectRoot..." -ForegroundColor Yellow
    Invoke-DockerCompose "down" -ProjectRoot $ProjectRoot
}

# 3. Remove / Delete All (No change needed, as these are system-wide commands)
function Remove-AllDockerAssets {
    # ... (contents remain the same as the original script) ...
    <#
        .SYNOPSIS
        Stops all running containers and forcibly removes all containers,
        volumes, and images on the system.
        .WARNING
        This command is destructive and removes ALL non-running containers,
        ALL volumes, and ALL images (even those not related to your project).
    #>
    Write-Host "--- WARNING: EXTREME CLEANUP MODE INITIATED ---" -ForegroundColor Red
    Write-Host "Stopping all running containers..." -ForegroundColor Red
    docker stop $(docker ps -aq) 2>$null 

    Write-Host "Removing all containers..." -ForegroundColor Red
    docker rm $(docker ps -aq) -f 2>$null 

    Write-Host "Removing all volumes (dangling and in-use)..." -ForegroundColor Red
    docker volume prune -f

    Write-Host "Removing all images (including those used by other projects)..." -ForegroundColor Red
    docker image prune -a -f

    Write-Host "Docker system assets (containers, volumes, images) cleaned." -ForegroundColor Green
}

# 4. Remove / Delete Project Assets (Modified to use ProjectRoot)
function Remove-ProjectDockerAssets {
    <#
        .SYNOPSIS
        Stops and removes containers, networks, and volumes defined in the
        docker-compose.yml, and then removes only the images associated with the project.
    #>
    param([string]$ProjectRoot)
    Write-Host "Stopping and removing project containers and volumes in $ProjectRoot..." -ForegroundColor Yellow
    
    # Use the Invoke-DockerCompose helper for 'down'
    Invoke-DockerCompose "down --volumes" -ProjectRoot $ProjectRoot

    Write-Host "Removing project images..." -ForegroundColor Yellow
    
    # Get the names of the services defined in the compose file
    $services = (Invoke-DockerCompose "config --services" -ProjectRoot $ProjectRoot) -split "`n" | Where-Object { $_ }
    
    foreach ($service in $services) {
        # Get the image name using the project directory context
        $imageName = (docker-compose --project-directory $ProjectRoot config --images --services $service)
        if ($imageName) {
            Write-Host "Attempting to remove image: $imageName" -ForegroundColor Cyan
            docker rmi -f $imageName 2>$null 
        }
    }

    Write-Host "Project containers, volumes, and images removed." -ForegroundColor Green
}

## 🚀 Execution Function (The menu entry point)

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("rebuild", "stop", "clean_all", "remove_project")]
    [string]$Action,
    
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot # New mandatory parameter for the location of docker-compose.yml
)

switch ($Action) {
    "rebuild" { Start-DockerServices -ProjectRoot $ProjectRoot }
    "stop" { Stop-DockerServices -ProjectRoot $ProjectRoot }
    "clean_all" { Remove-AllDockerAssets }
    "clean_project" { Remove-ProjectDockerAssets -ProjectRoot $ProjectRoot }
    default { Write-Host "Invalid action specified." -ForegroundColor Red }
}