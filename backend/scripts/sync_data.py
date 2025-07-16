#!/usr/bin/env python3
"""
Redstone Attendance Dashboard - Enhanced Data Sync Script
This script automatically syncs attendance data from your attendance tracker
to the dashboard's data directory with monitoring, notifications, and Docker integration.
"""

import os
import sys
import json
import shutil
import logging
import smtplib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler
import argparse
import time

# Import configuration
from sync_config import load_config, validate_config

# Global variables
logger = None
config = None

def setup_logging(log_config):
    """Setup logging with rotation"""
    global logger
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_config['log_level']))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_config['log_file'],
        maxBytes=log_config['log_max_size_mb'] * 1024 * 1024,
        backupCount=log_config['log_backup_count']
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class NotificationManager:
    """Handle email notifications"""
    
    def __init__(self, email_config):
        self.config = email_config
        self.enabled = email_config.get('email_notifications', False)
    
    def send_notification(self, subject, message, is_error=False):
        """Send email notification"""
        if not self.enabled:
            return
        
        # Check if we should send this type of notification
        if is_error and not self.config.get('email_on_error', True):
            return
        if not is_error and not self.config.get('email_on_success', False):
            return
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = f"[Attendance Dashboard] {subject}"
            
            body = f"""Attendance Dashboard Data Sync Report
            
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {'ERROR' if is_error else 'SUCCESS'}
            
Details:
{message}
            
This is an automated message from the Attendance Dashboard data sync system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")


class MetricsCollector:
    """Collect and store sync metrics"""
    
    def __init__(self, metrics_file):
        self.metrics_file = Path(metrics_file)
        self.metrics = self.load_metrics()
    
    def load_metrics(self):
        """Load existing metrics"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metrics: {e}")
        
        return {
            'sync_runs': [],
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync': None,
            'last_success': None,
            'consecutive_failures': 0
        }
    
    def record_sync(self, success, files_synced, errors=None):
        """Record a sync operation"""
        now = datetime.now().isoformat()
        
        sync_record = {
            'timestamp': now,
            'success': success,
            'files_synced': files_synced,
            'errors': errors or []
        }
        
        self.metrics['sync_runs'].append(sync_record)
        self.metrics['total_syncs'] += 1
        self.metrics['last_sync'] = now
        
        if success:
            self.metrics['successful_syncs'] += 1
            self.metrics['last_success'] = now
            self.metrics['consecutive_failures'] = 0
        else:
            self.metrics['failed_syncs'] += 1
            self.metrics['consecutive_failures'] += 1
        
        # Keep only last 100 runs
        if len(self.metrics['sync_runs']) > 100:
            self.metrics['sync_runs'] = self.metrics['sync_runs'][-100:]
        
        self.save_metrics()
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save metrics: {e}")
    
    def get_metrics(self):
        """Get current metrics"""
        return self.metrics.copy()


class DockerManager:
    """Manage Docker container operations"""
    
    def __init__(self, docker_config):
        self.config = docker_config
        self.enabled = docker_config.get('docker_enabled', False)
    
    def check_container_health(self):
        """Check if the dashboard container is healthy"""
        if not self.enabled:
            return True
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.config["docker_service_name"]}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and 'healthy' in result.stdout.lower():
                return True
            
            logger.warning(f"Container health check failed: {result.stdout}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking container health: {e}")
            return False
    
    def restart_container(self):
        """Restart the dashboard container"""
        if not self.enabled or not self.config.get('restart_container_on_sync', False):
            return True
        
        try:
            logger.info("Restarting dashboard container...")
            
            result = subprocess.run(
                ['docker-compose', 'restart', self.config['docker_service_name']],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Container restarted successfully")
                return True
            else:
                logger.error(f"Container restart failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting container: {e}")
            return False


class AttendanceDataSync:
    def __init__(self, source_dir, target_dir, dry_run=False, sync_config=None):
        """
        Initialize the data sync process
        
        Args:
            source_dir (str): Path to the source attendance data directory
            target_dir (str): Path to the dashboard data directory
            dry_run (bool): If True, only show what would be done
            sync_config (dict): Configuration dictionary
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.config = sync_config or {}
        
        # Initialize managers
        self.notification_manager = NotificationManager(self.config)
        self.metrics_collector = MetricsCollector(self.config.get('metrics_file', 'sync_metrics.json'))
        self.docker_manager = DockerManager(self.config)
        
        # Ensure target directory exists
        if not self.dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sync state
        self.files_synced = []
        self.errors = []
    
    def sync_attendance_history(self):
        """Sync the main attendance history file"""
        source_file = self.source_dir / 'attendance_history.json'
        target_file = self.target_dir / 'attendance_history.json'
        
        if not source_file.exists():
            logger.warning(f"Source file not found: {source_file}")
            return False
        
        try:
            # Check if source is newer than target
            if target_file.exists():
                source_mtime = source_file.stat().st_mtime
                target_mtime = target_file.stat().st_mtime
                
                if source_mtime <= target_mtime:
                    logger.info("Attendance history is up to date")
                    return True
            
            logger.info(f"Syncing attendance history: {source_file} -> {target_file}")
            
            if not self.dry_run:
                # Validate JSON before copying
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create backup of existing file
                if target_file.exists():
                    backup_file = target_file.with_suffix('.json.backup')
                    shutil.copy2(target_file, backup_file)
                    logger.info(f"Backed up existing file to {backup_file}")
                
                # Copy new file
                shutil.copy2(source_file, target_file)
                logger.info(f"Successfully synced {len(data)} dates of attendance data")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing attendance history: {e}")
            return False
    
    def sync_rm_attendance(self):
        """Sync the regional manager attendance file"""
        source_file = self.source_dir / 'rm_attendance_history.json'
        target_file = self.target_dir / 'rm_attendance_history.json'
        
        if not source_file.exists():
            logger.info("Regional manager attendance file not found, skipping")
            return True
        
        try:
            # Check if source is newer than target
            if target_file.exists():
                source_mtime = source_file.stat().st_mtime
                target_mtime = target_file.stat().st_mtime
                
                if source_mtime <= target_mtime:
                    logger.info("Regional manager attendance is up to date")
                    return True
            
            logger.info(f"Syncing RM attendance: {source_file} -> {target_file}")
            
            if not self.dry_run:
                # Validate JSON before copying
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create backup of existing file
                if target_file.exists():
                    backup_file = target_file.with_suffix('.json.backup')
                    shutil.copy2(target_file, backup_file)
                
                # Copy new file
                shutil.copy2(source_file, target_file)
                logger.info(f"Successfully synced {len(data)} dates of RM attendance data")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing RM attendance: {e}")
            return False
    
    def sync_employee_directory(self):
        """Sync the employee directory file"""
        # Look for the most recent employee directory file
        source_files = list(self.source_dir.glob('peoplehub*.csv'))
        
        if not source_files:
            logger.warning("No employee directory files found")
            return False
        
        # Get the most recent file
        source_file = max(source_files, key=lambda f: f.stat().st_mtime)
        target_file = self.target_dir / 'peoplehubdirectory20250708.csv'
        
        try:
            # Check if source is newer than target
            if target_file.exists():
                source_mtime = source_file.stat().st_mtime
                target_mtime = target_file.stat().st_mtime
                
                if source_mtime <= target_mtime:
                    logger.info("Employee directory is up to date")
                    return True
            
            logger.info(f"Syncing employee directory: {source_file} -> {target_file}")
            
            if not self.dry_run:
                # Create backup of existing file
                if target_file.exists():
                    backup_file = target_file.with_suffix('.csv.backup')
                    shutil.copy2(target_file, backup_file)
                
                # Copy new file
                shutil.copy2(source_file, target_file)
                logger.info("Successfully synced employee directory")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing employee directory: {e}")
            return False
    
    def validate_data_integrity(self):
        """Validate the integrity of synced data"""
        logger.info("Validating data integrity...")
        
        # Check attendance history
        attendance_file = self.target_dir / 'attendance_history.json'
        if attendance_file.exists():
            try:
                with open(attendance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, dict):
                    logger.error("Attendance history is not a valid dictionary")
                    return False
                
                # Check for required structure
                for date, date_data in data.items():
                    if not isinstance(date_data, dict):
                        logger.error(f"Invalid data structure for date {date}")
                        return False
                
                logger.info(f"Attendance history validation passed: {len(data)} dates")
                
            except Exception as e:
                logger.error(f"Error validating attendance history: {e}")
                return False
        
        # Check employee directory
        employee_file = self.target_dir / 'peoplehubdirectory20250708.csv'
        if employee_file.exists():
            try:
                with open(employee_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) < 2:  # Header + at least one data row
                    logger.error("Employee directory file is empty or has no data")
                    return False
                
                logger.info(f"Employee directory validation passed: {len(lines)-1} employees")
                
            except Exception as e:
                logger.error(f"Error validating employee directory: {e}")
                return False
        
        logger.info("Data integrity validation completed successfully")
        return True
    
    def sync_all(self):
        """Sync all data files"""
        logger.info("Starting data synchronization...")
        
        success_count = 0
        total_count = 3
        
        # Sync attendance history
        if self.sync_attendance_history():
            success_count += 1
            self.files_synced.append('attendance_history.json')
        else:
            self.errors.append('Failed to sync attendance history')
        
        # Sync RM attendance
        if self.sync_rm_attendance():
            success_count += 1
            self.files_synced.append('rm_attendance_history.json')
        else:
            self.errors.append('Failed to sync RM attendance')
        
        # Sync employee directory
        if self.sync_employee_directory():
            success_count += 1
            self.files_synced.append('employee_directory.csv')
        else:
            self.errors.append('Failed to sync employee directory')
        
        # Validate data integrity
        validation_success = True
        if not self.dry_run and success_count > 0:
            if not self.validate_data_integrity():
                logger.error("Data integrity validation failed")
                self.errors.append('Data integrity validation failed')
                validation_success = False
        
        # Record metrics
        overall_success = success_count == total_count and validation_success
        if self.config.get('metrics_enabled', True):
            self.metrics_collector.record_sync(
                overall_success, 
                self.files_synced, 
                self.errors if not overall_success else None
            )
        
        # Send notifications
        if overall_success:
            message = f"Successfully synchronized {len(self.files_synced)} files: {', '.join(self.files_synced)}"
            self.notification_manager.send_notification("Data Sync Success", message, is_error=False)
        else:
            message = f"Sync failed. Errors: {'; '.join(self.errors)}"
            self.notification_manager.send_notification("Data Sync Failed", message, is_error=True)
        
        # Docker container health check
        if self.config.get('container_health_check', True):
            if not self.docker_manager.check_container_health():
                logger.warning("Container health check failed")
        
        logger.info(f"Synchronization completed: {success_count}/{total_count} successful")
        return overall_success


def main():
    """Main function to run the data sync"""
    parser = argparse.ArgumentParser(description='Enhanced attendance data sync with monitoring and notifications')
    parser.add_argument('--source', help='Source data directory (overrides config)')
    parser.add_argument('--target', help='Target dashboard data directory (overrides config)')
    parser.add_argument('--config', help='Configuration file path', default='sync_config.json')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (continuous sync)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    # Load configuration
    global config
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.source:
        config['source_directory'] = args.source
    if args.target:
        config['target_directory'] = args.target
    
    # Validate configuration
    config_errors = validate_config(config)
    if config_errors:
        print("Configuration errors:")
        for error in config_errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Setup logging
    global logger
    logger = setup_logging(config)
    
    logger.info("Starting Attendance Data Sync")
    logger.info(f"Source: {config['source_directory']}")
    logger.info(f"Target: {config['target_directory']}")
    
    # Create sync instance with configuration
    sync = AttendanceDataSync(
        config['source_directory'], 
        config['target_directory'], 
        args.dry_run,
        config
    )
    
    if args.daemon and not args.once:
        # Run as daemon
        logger.info(f"Starting daemon mode with {config['sync_interval_minutes']} minute intervals")
        run_daemon(sync, config)
    else:
        # Run once
        success = sync.sync_all()
        
        if success:
            logger.info("Data synchronization completed successfully")
            sys.exit(0)
        else:
            logger.error("Data synchronization failed")
            sys.exit(1)


def run_daemon(sync, config):
    """Run the sync process as a daemon"""
    interval = config['sync_interval_minutes'] * 60  # Convert to seconds
    
    logger.info(f"Daemon started, syncing every {config['sync_interval_minutes']} minutes")
    
    while True:
        try:
            logger.info("Starting scheduled sync...")
            success = sync.sync_all()
            
            if success:
                logger.info("Scheduled sync completed successfully")
            else:
                logger.error("Scheduled sync failed")
                
                # Check if we should alert on consecutive failures
                metrics = sync.metrics_collector.get_metrics()
                if metrics['consecutive_failures'] >= config['alert_thresholds']['sync_failure_count']:
                    logger.critical(f"Critical: {metrics['consecutive_failures']} consecutive sync failures")
                    sync.notification_manager.send_notification(
                        "Critical Sync Failures",
                        f"Sync has failed {metrics['consecutive_failures']} times consecutively",
                        is_error=True
                    )
            
            logger.info(f"Waiting {config['sync_interval_minutes']} minutes until next sync...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying


if __name__ == '__main__':
    main()
