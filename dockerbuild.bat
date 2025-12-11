@echo off
setlocal

:: Define the Project Root as the current directory where Menu.bat lives (%~dp0)
set "PROJECT_ROOT=%~dp0"

:: Define the path to the PowerShell script in the 'scripts' subdirectory
set "PS_SCRIPT_PATH=%PROJECT_ROOT%scripts\docker_manager.ps1"

:: Define the path to the docker-compose.yml file.
set "PS_DOCKER_COMPOSE=%PROJECT_ROOT%lifebuddy-app.yml"

:: Define the profile name to be used (e.g., 'dev' or 'prod')
set "PROFILE_NAME=dev"

:MENU
cls
echo =========================================================
echo    Docker Management Menu (Profile: %PROFILE_NAME%)
echo =========================================================
echo.
echo    (Root: %PROJECT_ROOT%)
echo    (Script Path: %PS_SCRIPT_PATH%)
echo    (Docker Compose: %PS_DOCKER_COMPOSE%)
echo.
echo.
echo    1. Rebuild & Start Services (Profile: %PROFILE_NAME%)
echo    2. Pull 'mistral' model to 'ollama' container (docker exec)
echo    3. Shut Down Services (Profile: %PROFILE_NAME%)
echo    4. DELETE Project Assets (Containers, Volumes, Images for this project)
echo    5. DELETE ALL Docker Assets (!!! WARNING: System-wide cleanup !!!)

echo.
echo    X. Exit
echo.
set /p CHOICE="Enter your choice: "

if /i "%CHOICE%"=="1" goto REBUILD
if /i "%CHOICE%"=="2" goto PULL_MISTRAL
if /i "%CHOICE%"=="3" goto STOP
if /i "%CHOICE%"=="4" goto REMOVE_PROJECT
if /i "%CHOICE%"=="5" goto REMOVE_ALL
if /i "%CHOICE%"=="X" goto END
if /i "%CHOICE%"=="x" goto END

echo.
echo Invalid choice. Please try again.
pause
goto MENU

:REBUILD
echo.
echo Rebuilding and Starting Services...
echo.
:: Call PowerShell with -Action "rebuild" and -ProfileName
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "rebuild" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
::powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "pull_mistral" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
echo.
pause
goto MENU

:PULL_MISTRAL
echo.
echo Attempting to pull 'mistral' model in the 'ollama' container...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "pull_mistral" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
echo.
echo Model pull command finished.
pause
goto MENU

:STOP
echo.
echo Stopping Services...
:: Note: Corrected parameter from -ProjectRoot to -ComposeFilePath to match docker_manager.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "stop" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
echo.
pause
goto MENU

:REMOVE_PROJECT
echo.
echo WARNING: This will remove all containers, volumes, and images ONLY related to this project.
pause
:: Note: Corrected parameter from -ProjectRoot to -ComposeFilePath to match docker_manager.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "remove_project" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
echo.
pause
goto MENU

:REMOVE_ALL
echo.
echo !!! CRITICAL WARNING !!!
echo This will forcibly STOP AND REMOVE *ALL* containers, volumes, and images on your entire system.
echo Press any key to continue with the system-wide cleanup, or CTRL+C to cancel.
pause
:: Note: Corrected parameter from -ProjectRoot to -ComposeFilePath to match docker_manager.ps1
:: ProfileName is NOT needed for this action. -ComposeFilePath is still required by the powershell script's param block.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "remove_all" -ComposeFilePath "%PS_DOCKER_COMPOSE%"
echo.
pause
goto MENU

:END
echo Exiting Docker Manager. Goodbye!
endlocal
exit