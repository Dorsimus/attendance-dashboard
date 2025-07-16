# Attendance Dashboard Data Sync System

## Overview
This document provides detailed instructions for setting up and managing the automated attendance data sync system for the Attendance Dashboard.

## Components
- **Sync Script (`sync_data.py`)**: The main script responsible for syncing data from the specified source directory to the target dashboard data directory.
- **Configuration (`sync_config.json`)**: JSON configuration file for setting up various parameters like source paths, logging, intervals, and more.
- **Batch Files**:
  - `run_sync_once.bat`: Runs the sync process once.
  - `run_sync_daemon.bat`: Runs the sync process continuously at specified intervals.
- **Scheduled Task XML (`AttendanceDataSync.xml`)**: Task Scheduler XML file to import into Windows Task Scheduler for automated execution.
- **PowerShell Script (`setup_sync_task.ps1`)**: Script to set up a Windows Scheduled Task.
- **Log Files**: Located in `C:\CM_Attendance\logs`, containing logs and metrics.

## Setup Instructions

1. **Prepare the Environment**
   - Ensure Python is installed and added to the PATH.
   - Install necessary Python packages: `pip install -r requirements.txt` if additional packages are required.

2. **Configure Paths**
   - Update `sync_config.json` to reflect the correct paths for your source and target directories.

3. **Setup Automated Sync**
   - Use the Task Scheduler XML file to import the task manually or run the `setup_sync_task.ps1` PowerShell script (with admin rights) to automatically create the scheduled task.

4. **Manual Execution**
   - To run the script manually, use the batch files:
     - `run_sync_once.bat`: Executes the sync once.
     - `run_sync_daemon.bat`: Executes continuously.

5. **Logs and Monitoring**
   - Logs are stored in `C:\CM_Attendance\logs`. Review `data_sync.log` and `sync_metrics.json` for insights into operation and health.

## Troubleshooting

- **Script Failures**: Ensure paths and permissions are correctly set.
- **Task Scheduler Issues**: Verify the task is enabled and the user account has sufficient privileges.
- **Check Logs**: Consult the log files for error messages and more context.

## FAQs

- **How to change the sync interval?**
  Edit `sync_config.json` and adjust the `sync_interval_minutes` value.

- **How to change log levels?**
  Modify the `log_level` value in `sync_config.json`.

- **How to enable email notifications?**
  Provide the necessary SMTP details and toggle the `email_notifications` flag in the configuration file.

- **How to import the Task Scheduler XML?**
  - Open Task Scheduler.
  - Action > Import Task...
  - Select `AttendanceDataSync.xml` and follow the prompts.

## Support
For further assistance, please contact the support team or visit the project documentation site.
