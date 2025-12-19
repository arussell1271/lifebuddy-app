@echo off
setlocal

:: Define the two script names
set SCRIPT_FROM=docker_transfer.ps1 -Direction From
set SCRIPT_TO=docker_transfer.ps1 -Direction To
set SCRIPT_GITHUB=github_transfer.ps1

:: --- Main Menu Loop ---
:MENU_LOOP
CLS
set TARGET_SCRIPT=
echo.
ECHO ===========================================
ECHO  Welcome to the Backup Runner
ECHO ===========================================
echo.

:: Check for direct parameter execution (from/to) and execute once
IF /I "%~1"=="from" (
    set TARGET_SCRIPT=%SCRIPT_FROM%
    GOTO :EXECUTE
)
IF /I "%~1"=="to" (
    set TARGET_SCRIPT=%SCRIPT_TO%
    GOTO :EXECUTE
)
IF /I "%~1"=="github" (
    set TARGET_SCRIPT=%SCRIPT_GITHUB%
    GOTO :EXECUTE
)

:: --- No parameter was provided, or returning from execution, so prompt the user ---
:PROMPT_USER
ECHO Which backup script would you like to run?
ECHO.
ECHO 1. [FROM]: Backup Files From Docker - (%SCRIPT_FROM%)
ECHO 2. [TO]: Restore Files To Docker   - (%SCRIPT_TO%)
ECHO 3. [GITHUB]: Upload Code to GitHub - (%SCRIPT_GITHUB%)
ECHO 4. [EXIT] - Exit the Backup Runner
ECHO.
SET /P CHOICE="Enter '1-From', '2-To', '3-GitHub', '4-Exit' (exit), or just press Enter to exit: "

:: Validate the user's choice
IF /I "%CHOICE%"=="from" (
    set TARGET_SCRIPT=%SCRIPT_FROM%
    GOTO :EXECUTE
)
IF "%CHOICE%"=="1" (
    set TARGET_SCRIPT=%SCRIPT_FROM%
    GOTO :EXECUTE
)

IF /I "%CHOICE%"=="to" (
    set TARGET_SCRIPT=%SCRIPT_TO%
    GOTO :EXECUTE
)
IF "%CHOICE%"=="2" (
    set TARGET_SCRIPT=%SCRIPT_TO%
    GOTO :EXECUTE
)
IF /I "%CHOICE%"=="github" (
    set TARGET_SCRIPT=%SCRIPT_GITHUB%
    GOTO :EXECUTE
)
IF "%CHOICE%"=="3" (
    set TARGET_SCRIPT=%SCRIPT_GITHUB%
    GOTO :EXECUTE
)

IF /I "%CHOICE%"=="exit" (
    GOTO :END
)
IF "%CHOICE%"=="4" (
    GOTO :END
)

:: If input is invalid or empty, exit
ECHO.
ECHO Invalid selection or no choice entered.
GOTO :END

:: --- Execute the selected PowerShell script ---
:EXECUTE
ECHO.
ECHO Running %TARGET_SCRIPT%...
ECHO.
:: Run the selected PowerShell script using -NoProfile -Command
:: NOTE: The %SCRIPT_GITHUB% script MUST contain the 'Set-Location ..' command
::       to move up to the root 'lifebuddy-app' folder before running Git commands.
powershell.exe -NoProfile -Command "& {.\scripts\%TARGET_SCRIPT%}"

:: Clear the parameter so the script doesn't try to run it on the next loop
set "CHOICE="

:: Pause and loop back to the menu after execution
PAUSE
GOTO :MENU_LOOP

:: --- End Script ---
:END
ECHO.
ECHO Exiting Backup Runner.
endlocal
