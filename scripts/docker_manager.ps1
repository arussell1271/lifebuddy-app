# docker_manager.ps1

## 🚀 Execution Function - Entry Point
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("rebuild", "stop", "remove_all", "remove_project")]
    [string]$Action,
    
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot, # Path to the directory containing docker-compose.yml

    # New parameter to accept an optional environment file path
    [string]$EnvFile 
)

# -----------------------------------------------------------------------------
## ⚙️ Helper Functions
# -----------------------------------------------------------------------------

# Helper function to execute docker-compose commands with the specified project root
function Invoke-DockerCompose {
    param(
        [string]$Command,
        [string]$ProjectRoot,
        [string]$EnvFile
    )
    
    # 1. Start building the argument list for the native 'docker' command
    # This array method correctly handles paths with spaces (e.g., 'VS Code')
    $dockerArgs = @("compose", "--project-directory", $ProjectRoot)

    # 2. Add the optional --env-file argument if a file was provided
    if (-not [string]::IsNullOrWhiteSpace($EnvFile)) {
        $dockerArgs += @("--env-file", $EnvFile)
    }
    
    # 3. Add the specific command and its parameters
    # Splitting the command string ensures that arguments (like 'down' and '--volumes') are separate array elements
    $commandArray = $Command -split ' ' | Where-Object { $_ }
    $dockerArgs += $commandArray
    
    # Execute the command by passing the argument array to the native 'docker' executable.
    $output = docker @dockerArgs
    
    # Check the $LASTEXITCODE which holds the exit code of the last executed native command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker Compose command failed: $Command" -ForegroundColor Red
        # Return $null on failure
        return $null
    }
    
    return $output
}

# -----------------------------------------------------------------------------
## ⚙️ Core Management Functions
# -----------------------------------------------------------------------------

# 1. Start Up/Rebuild
function Start-DockerServices {
    param([string]$ProjectRoot, [string]$EnvFile)
    Write-Host "Starting/Rebuilding Docker services in $ProjectRoot..." -ForegroundColor Green
    Invoke-DockerCompose "up --build -d" -ProjectRoot $ProjectRoot -EnvFile $EnvFile
}

# 2. Shut Down
function Stop-DockerServices {
    param([string]$ProjectRoot)
    Write-Host "Stopping and removing Docker services in $ProjectRoot..." -ForegroundColor Yellow
    # 'down' stops and removes containers, networks, and default volumes
    Invoke-DockerCompose "down" -ProjectRoot $ProjectRoot -EnvFile $EnvFile
}

# 3. Remove / Delete All (System-wide)
function Remove-AllDockerAssets {
    Write-Host "--- WARNING: EXTREME CLEANUP MODE INITIATED (System-wide) ---" -ForegroundColor Red
    
    Write-Host "Stopping all running containers..." -ForegroundColor Red
    docker stop $(docker ps -aq) 2>$null 

    Write-Host "Removing all containers..." -ForegroundColor Red
    docker rm $(docker ps -aq) -f 2>$null 

    Write-Host "Removing all unused volumes..." -ForegroundColor Red
    docker volume prune -f

    Write-Host "Removing all unused images..." -ForegroundColor Red
    # -a removes all images without at least one container associated with them
    docker image prune -a -f

    Write-Host "Docker system assets (containers, volumes, images) cleaned." -ForegroundColor Green
}

# 4. Remove / Delete Project Assets (Project-specific)
function Remove-ProjectDockerAssets {
    param([string]$ProjectRoot)
    Write-Host "Stopping and removing project containers and volumes in $ProjectRoot..." -ForegroundColor Yellow
    
    # Stop and remove containers, networks, and project volumes
    Invoke-DockerCompose "down --volumes" -ProjectRoot $ProjectRoot -EnvFile $EnvFile

    Write-Host "Removing project images..." -ForegroundColor Yellow
    
    # Get service names using the project directory context
    $services = (Invoke-DockerCompose "config --services" -ProjectRoot $ProjectRoot -EnvFile $EnvFile) -split "`n" | Where-Object { $_ }
    
    foreach ($service in $services) {
        # Get the image name. If Invoke-DockerCompose fails, it returns $null, preventing the .Trim() error.
        $imageName = (Invoke-DockerCompose "config --images --services $service" -ProjectRoot $ProjectRoot -EnvFile $EnvFile).Trim()
        
        # Check if an image name was successfully retrieved and not an error message
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

switch ($Action) {
    "rebuild" { Start-DockerServices -ProjectRoot $ProjectRoot -EnvFile $EnvFile }
    "stop" { Stop-DockerServices -ProjectRoot $ProjectRoot -EnvFile $EnvFile }
    "remove_all" { Remove-AllDockerAssets }
    "remove_project" { Remove-ProjectDockerAssets -ProjectRoot $ProjectRoot -EnvFile $EnvFile }
    default { Write-Host "Invalid action specified." -ForegroundColor Red }
}