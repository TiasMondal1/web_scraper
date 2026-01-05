@echo off
REM Batch script to set up Windows Task Scheduler (alternative method)
REM Run this script as Administrator

set SCRIPT_DIR=%~dp0
set TASK_NAME=PriceTracker_ScheduledRun
set PYTHON_SCRIPT=%SCRIPT_DIR%scheduler.py

echo Setting up Windows Task Scheduler for Price Tracker...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Remove existing task if it exists
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

REM Create new scheduled task (daily at 9 AM)
schtasks /Create /TN "%TASK_NAME%" /TR "python \"%PYTHON_SCRIPT%\" --once" /SC DAILY /ST 09:00 /RL HIGHEST /F

if errorlevel 1 (
    echo Error: Failed to create scheduled task
    echo Make sure you are running this script as Administrator
    pause
    exit /b 1
)

echo.
echo Windows Task Scheduler configured successfully!
echo Task Name: %TASK_NAME%
echo Schedule: Daily at 9:00 AM
echo.
echo To view the task, run:
echo   schtasks /Query /TN "%TASK_NAME%"
echo.
pause



