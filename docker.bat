@echo off
setlocal

:: Define the Project Root as the current directory where Menu.bat lives (%~dp0)
set "PROJECT_ROOT=%~dp0"

:: Define the path to the PowerShell script in the 'scripts' subdirectory
set "PS_SCRIPT_PATH=%PROJECT_ROOT%scripts\docker_manager.ps1"

:: Define the environment file path once, as it's needed for all project actions to avoid the .env lookup error
set "ENV_FILE_PATH=%PROJECT_ROOT%.env.dev"

:MENU
cls
echo =========================================================
echo    Docker Management Menu
echo =========================================================
echo.
echo    (Root: %PROJECT_ROOT%)
echo    (Script Path: %PS_SCRIPT_PATH%)
echo    (ENV File: %ENV_FILE_PATH%)
echo.
echo.
echo    1. Rebuild & Start Services
echo    2. Shut Down Services
echo    3. DELETE Project Assets (Containers, Volumes, Images for this project)
echo    4. DELETE ALL Docker Assets (!!! WARNING: System-wide cleanup !!!)
echo.
echo    X. Exit
echo.
set /p CHOICE="Enter your choice: "

if /i "%CHOICE%"=="1" goto REBUILD
if /i "%CHOICE%"=="2" goto STOP
if /i "%CHOICE%"=="3" goto REMOVE_PROJECT
if /i "%CHOICE%"=="4" goto REMOVE_ALL
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
::powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "rebuild" -ProjectRoot "%PROJECT_ROOT%" -EnvFile "%ENV_FILE_PATH%"
powershell.exe -File "%PS_SCRIPT_PATH%" -Action "rebuild" -ProjectRoot "%PROJECT_ROOT%"
echo.
pause
goto MENU

:STOP
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "stop" -ProjectRoot "%PROJECT_ROOT%" -EnvFile "%ENV_FILE_PATH%"
echo.
pause
goto MENU

:REMOVE_PROJECT
echo.
echo WARNING: This will remove all containers, volumes, and images ONLY related to this project.
pause
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "remove_project" -ProjectRoot "%PROJECT_ROOT%" -EnvFile "%ENV_FILE_PATH%"
echo.
pause
goto MENU

:REMOVE_ALL
echo.
echo !!! CRITICAL WARNING !!!
echo This will forcibly STOP AND REMOVE *ALL* containers, volumes, and images on your entire system.
echo Press any key to continue with the system-wide cleanup, or CTRL+C to cancel.
pause
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%" -Action "remove_all" -ProjectRoot "%PROJECT_ROOT%"
echo.
pause
goto MENU

:END
echo Exiting Docker Manager. Goodbye!
endlocal
exit