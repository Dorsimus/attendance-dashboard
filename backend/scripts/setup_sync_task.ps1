# PowerShell script to set up Windows Scheduled Task for attendance data sync

param(
    [string]$TaskName = "AttendanceDataSync",
    [string]$ScriptPath = "C:\CM_Attendance\attendance-dashboard\backend\scripts\sync_data.py",
    [string]$ConfigPath = "C:\CM_Attendance\attendance-dashboard\backend\scripts\sync_config.json",
    [string]$LogPath = "C:\CM_Attendance\logs",
    [int]$IntervalMinutes = 30,
    [string]$RunAsUser = "SYSTEM"
)

# Ensure we're running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Please run PowerShell as Administrator and try again."
    exit 1
}

Write-Host "Setting up Windows Scheduled Task for Attendance Data Sync..." -ForegroundColor Green

# Create log directory if it doesn't exist
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force
    Write-Host "Created log directory: $LogPath" -ForegroundColor Yellow
}

# Check if Python is available
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Error "Python is not found in PATH. Please install Python and ensure it's in your PATH."
    exit 1
}

# Validate script path
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Sync script not found at: $ScriptPath"
    exit 1
}

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$ScriptPath`" --config `"$ConfigPath`" --daemon"

# Create the scheduled task trigger (start at system startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create additional trigger for immediate execution
$triggerNow = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)

# Create the scheduled task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create the scheduled task principal
$principal = New-ScheduledTaskPrincipal -UserId $RunAsUser -LogonType ServiceAccount -RunLevel Highest

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Register the scheduled task
Write-Host "Registering scheduled task: $TaskName" -ForegroundColor Green
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automated attendance data synchronization for dashboard"

# Create a backup batch file for manual execution
$batchContent = @"
@echo off
cd /d "$(Split-Path $ScriptPath -Parent)"
python.exe "$ScriptPath" --config "$ConfigPath" --once
pause
"@

$batchPath = Join-Path (Split-Path $ScriptPath -Parent) "run_sync_once.bat"
$batchContent | Out-File -FilePath $batchPath -Encoding ASCII

Write-Host "Created manual sync batch file: $batchPath" -ForegroundColor Green

# Create a daemon batch file
$daemonBatchContent = @"
@echo off
cd /d "$(Split-Path $ScriptPath -Parent)"
python.exe "$ScriptPath" --config "$ConfigPath" --daemon
pause
"@

$daemonBatchPath = Join-Path (Split-Path $ScriptPath -Parent) "run_sync_daemon.bat"
$daemonBatchContent | Out-File -FilePath $daemonBatchPath -Encoding ASCII

Write-Host "Created daemon sync batch file: $daemonBatchPath" -ForegroundColor Green

# Show task information
Write-Host "`nScheduled Task Configuration:" -ForegroundColor Cyan
Write-Host "  Task Name: $TaskName" -ForegroundColor White
Write-Host "  Script: $ScriptPath" -ForegroundColor White
Write-Host "  Config: $ConfigPath" -ForegroundColor White
Write-Host "  Run As: $RunAsUser" -ForegroundColor White
Write-Host "  Trigger: At system startup" -ForegroundColor White

Write-Host "`nTo manage the task:" -ForegroundColor Cyan
Write-Host "  Start task: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  Stop task: Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  View task: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  Remove task: Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White

Write-Host "`nManual execution:" -ForegroundColor Cyan
Write-Host "  Run once: $batchPath" -ForegroundColor White
Write-Host "  Run daemon: $daemonBatchPath" -ForegroundColor White

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "The sync task will start automatically when the system boots." -ForegroundColor Green
Write-Host "You can start it manually now with: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
