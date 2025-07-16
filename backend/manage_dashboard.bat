@echo off
title Attendance Dashboard Management
color 0A

:menu
cls
echo.
echo ================================================
echo     ATTENDANCE DASHBOARD MANAGEMENT
echo ================================================
echo.
echo Current Status:
docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Dashboard URL: http://10.100.1.187:8000
echo.
echo ================================================
echo 1. Start Dashboard
echo 2. Stop Dashboard
echo 3. Restart Dashboard
echo 4. View Logs
echo 5. Check Health
echo 6. Open Dashboard in Browser
echo 7. View Network Status
echo 8. Exit
echo ================================================
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto health
if "%choice%"=="6" goto browser
if "%choice%"=="7" goto network
if "%choice%"=="8" goto exit

echo Invalid choice. Please try again.
pause
goto menu

:start
echo Starting dashboard...
docker-compose up -d
echo Dashboard started!
pause
goto menu

:stop
echo Stopping dashboard...
docker-compose down
echo Dashboard stopped!
pause
goto menu

:restart
echo Restarting dashboard...
docker-compose restart
echo Dashboard restarted!
pause
goto menu

:logs
echo Viewing dashboard logs (Press Ctrl+C to exit)...
docker-compose logs -f
goto menu

:health
echo Checking dashboard health...
echo.
echo Testing connection to dashboard...
powershell -Command "Test-NetConnection -ComputerName 10.100.1.187 -Port 8000"
echo.
echo Docker container status:
docker-compose ps
echo.
echo Dashboard URL: http://10.100.1.187:8000
echo.
pause
goto menu

:browser
echo Opening dashboard in browser...
start http://10.100.1.187:8000
goto menu

:network
echo Network Information:
echo.
echo Server IP Address: 10.100.1.187
echo Dashboard Port: 8000
echo Dashboard URL: http://10.100.1.187:8000
echo.
echo Network connectivity test:
powershell -Command "Test-NetConnection -ComputerName 10.100.1.187 -Port 8000"
echo.
echo Current network configuration:
ipconfig | findstr /C:"IPv4 Address"
echo.
pause
goto menu

:exit
echo Goodbye!
exit
