@echo off
echo Attendance Dashboard Data Sync Monitor
echo =====================================
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if monitoring script exists
if not exist "monitor_sync.py" (
    echo ERROR: monitor_sync.py not found in current directory
    pause
    exit /b 1
)

:: Check if config file exists
if not exist "sync_config.json" (
    echo ERROR: sync_config.json not found in current directory
    pause
    exit /b 1
)

:: Run the monitoring script
python monitor_sync.py --config sync_config.json

echo.
echo Press any key to exit...
pause > nul
