@echo off
echo Starting Attendance Data Sync (Daemon Mode)...
echo This will run continuously every 30 minutes.
echo Press Ctrl+C to stop.
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if sync script exists
if not exist "sync_data.py" (
    echo ERROR: sync_data.py not found in current directory
    pause
    exit /b 1
)

:: Check if config file exists
if not exist "sync_config.json" (
    echo ERROR: sync_config.json not found in current directory
    pause
    exit /b 1
)

echo Starting daemon mode...
python sync_data.py --config sync_config.json --daemon

echo.
echo Daemon stopped. Press any key to exit...
pause > nul
