@echo off
setlocal

:: --- Configuration from dockerbuild.bat ---
:: Define the Project Root as the current directory where the script lives (%~dp0)
set "PROJECT_ROOT=%~dp0"

:: Define the path to the PowerShell scripts in the 'scripts' subdirectory
set "PS_DOCKER_MANAGER_SCRIPT=%PROJECT_ROOT%scripts\docker_manager.ps1"
set "PS_DOCKER_TRANSFER_SCRIPT=%PROJECT_ROOT%scripts\docker_transfer.ps1"
set "PS_GITHUB_TRANSFER_SCRIPT=%PROJECT_ROOT%scripts\github_transfer.ps1"

:: Define the path to the docker-compose.yml file.
set "PS_DOCKER_COMPOSE=%PROJECT_ROOT%lifebuddy-app.yml"

:: Define the default profile name to be used (e.g., 'dev' or 'prod')
set "PROFILE_NAME=dev"
:: ------------------------------------------

:MAIN_MENU
cls
echo =========================================================
echo    🚀 Project Manager Menu (Profile: %PROFILE_NAME%)
echo =========================================================
echo.
echo    --- 1. Docker and Service Management ---
echo    1. Rebuild and Start Services (Profile: %PROFILE_NAME%)
echo    2. Pull 'mistral' model to 'ollama' container
echo    3. Shut Down Services (Profile: %PROFILE_NAME%)
echo    4. DELETE Project Assets (Containers, Volumes, Images)
echo    5. DELETE ALL Docker Assets (!!! WARNING: System-wide !!!)
echo.
echo    --- 2. Data and Code Transfer ---
echo    6. Backup Database Volume (FROM Docker)
echo    7. Restore Database Volume (TO Docker)
echo    8. Upload Code to GitHub
echo.
echo    --- 3. Configuration and Exit ---
echo    C. Change Profile (Current: %PROFILE_NAME%)
echo    X. Exit Manager
echo.
set /p CHOICE="Enter your choice (1-8, C, X): "

if /i "%CHOICE%"=="1" goto REBUILD
if /i "%CHOICE%"=="2" goto PULL_MISTRAL
if /i "%CHOICE%"=="3" goto STOP
if /i "%CHOICE%"=="4" goto REMOVE_PROJECT
if /i "%CHOICE%"=="5" goto REMOVE_ALL

if /i "%CHOICE%"=="6" goto DB_BACKUP
if /i "%CHOICE%"=="7" goto DB_RESTORE
if /i "%CHOICE%"=="8" goto GITHUB_PUSH

if /i "%CHOICE%"=="C" goto CHANGE_PROFILE
if /i "%CHOICE%"=="X" goto END

pause
echo.
echo Invalid choice. Please try again.
pause
goto MAIN_MENU

:: --- 1. Docker & Service Management ---

:REBUILD
echo.
echo Rebuilding and Starting Services...
echo.
:: Call PowerShell with -Action "rebuild"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_MANAGER_SCRIPT%" -Action "rebuild" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
if %errorlevel% neq 0 (
    echo !!! ERROR: Docker rebuild failed (Error Level: %errorlevel%) !!!
    pause
)
:: Then ensure the model is pulled (essential for the application)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_MANAGER_SCRIPT%" -Action "pull_mistral" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
if %errorlevel% neq 0 (
    echo !!! WARNING: Mistral model pull failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:PULL_MISTRAL
echo.
echo Attempting to pull 'mistral' model in the 'ollama' container...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_MANAGER_SCRIPT%" -Action "pull_mistral" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
if %errorlevel% neq 0 (
    echo !!! ERROR: Mistral model pull failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
echo Model pull command finished.
pause
goto MAIN_MENU

:STOP
echo.
echo Shutting Down Services...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_MANAGER_SCRIPT%" -Action "stop" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
if %errorlevel% neq 0 (
    echo !!! ERROR: Docker stop failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:REMOVE_PROJECT
echo.
echo WARNING: This will remove all containers, volumes, and images ONLY related to the '%PROFILE_NAME%' project.
pause
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_MANAGER_SCRIPT%" -Action "remove_project" -ComposeFilePath "%PS_DOCKER_COMPOSE%" -ProfileName "%PROFILE_NAME%"
if %errorlevel% neq 0 (
    echo !!! ERROR: Project removal failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:REMOVE_ALL
echo.
echo !!! CRITICAL WARNING !!!
echo This will forcibly STOP AND REMOVE *ALL* containers, volumes, and images on your entire system.
echo Press any key to continue with the system-wide cleanup, or CTRL+C to cancel.
pause
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_MANAGER_SCRIPT%" -Action "remove_all" -ComposeFilePath "%PS_DOCKER_COMPOSE%"
if %errorlevel% neq 0 (
    echo !!! ERROR: System-wide cleanup failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:: --- 2. Data & Code Transfer ---

:DB_BACKUP
echo.
echo Starting Database Backup (FROM Docker Volume)...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_TRANSFER_SCRIPT%" -Direction From -ComposeFilePath "%PS_DOCKER_COMPOSE%"
if %errorlevel% neq 0 (
    echo !!! ERROR: Database Backup failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:DB_RESTORE
echo.
echo Starting Database Restore (TO Docker Volume)...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_DOCKER_TRANSFER_SCRIPT%" -Direction To -ComposeFilePath "%PS_DOCKER_COMPOSE%"
if %errorlevel% neq 0 (
    echo !!! ERROR: Database Restore failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:GITHUB_PUSH
echo.
echo Starting GitHub Code Upload...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_GITHUB_TRANSFER_SCRIPT%"
if %errorlevel% neq 0 (
    echo !!! ERROR: GitHub Push failed (Error Level: %errorlevel%) !!!
    pause
)
echo.
pause
goto MAIN_MENU

:: --- 3. Configuration & Exit ---

:CHANGE_PROFILE
echo.
echo Current Profile: %PROFILE_NAME%
set /p NEW_PROFILE="Enter new profile name (e.g., 'dev' or 'prod'): "

:: Basic validation for empty input
if not defined NEW_PROFILE (
    echo Profile not changed.
    pause
    goto MAIN_MENU
)

set "PROFILE_NAME=%NEW_PROFILE%"
echo Profile successfully changed to: %PROFILE_NAME%
pause
goto MAIN_MENU

:END
echo.
echo Exiting Project Manager. Goodbye!
endlocal
exit