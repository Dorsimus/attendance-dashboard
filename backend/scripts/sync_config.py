#!/usr/bin/env python3
"""
Configuration settings for the attendance data sync system
"""

import os
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    # Source data directory (where your attendance files are generated)
    'source_directory': r'C:\CM_Attendance\data_source',
    
    # Target data directory (dashboard data directory)
    'target_directory': r'C:\CM_Attendance\attendance-dashboard\backend\data',
    
    # Backup settings
    'backup_enabled': True,
    'backup_directory': r'C:\CM_Attendance\backups',
    'backup_retention_days': 30,
    
    # Sync settings
    'sync_interval_minutes': 30,
    'force_sync': False,
    'validate_data': True,
    
    # File patterns
    'attendance_history_file': 'attendance_history.json',
    'rm_attendance_file': 'rm_attendance_history.json',
    'employee_directory_pattern': 'peoplehub*.csv',
    'employee_directory_target': 'peoplehubdirectory20250708.csv',
    
    # Logging
    'log_level': 'INFO',
    'log_file': 'data_sync.log',
    'log_max_size_mb': 10,
    'log_backup_count': 5,
    
    # Notifications
    'email_notifications': False,
    'email_on_error': True,
    'email_on_success': False,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email_from': '',
    'email_to': '',
    'email_password': '',
    
    # Docker integration
    'docker_enabled': True,
    'docker_compose_file': 'docker-compose.yml',
    'docker_service_name': 'attendance-dashboard',
    'restart_container_on_sync': False,
    'container_health_check': True,
    
    # Monitoring
    'metrics_enabled': True,
    'metrics_file': 'sync_metrics.json',
    'alert_thresholds': {
        'sync_failure_count': 3,
        'data_age_hours': 24,
        'file_size_change_percent': 50
    }
}

def load_config(config_file=None):
    """Load configuration from file or environment variables"""
    config = DEFAULT_CONFIG.copy()
    
    # Load from config file if provided
    if config_file and Path(config_file).exists():
        import json
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    # Override with environment variables
    env_mappings = {
        'SYNC_SOURCE_DIR': 'source_directory',
        'SYNC_TARGET_DIR': 'target_directory',
        'SYNC_BACKUP_DIR': 'backup_directory',
        'SYNC_INTERVAL': 'sync_interval_minutes',
        'SYNC_LOG_LEVEL': 'log_level',
        'SYNC_EMAIL_FROM': 'email_from',
        'SYNC_EMAIL_TO': 'email_to',
        'SYNC_EMAIL_PASSWORD': 'email_password',
    }
    
    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            # Convert to appropriate type
            if config_key.endswith('_minutes') or config_key.endswith('_days') or config_key.endswith('_count'):
                try:
                    config[config_key] = int(value)
                except ValueError:
                    pass
            elif config_key.endswith('_enabled'):
                config[config_key] = value.lower() in ('true', '1', 'yes', 'on')
            else:
                config[config_key] = value
    
    return config

def save_config(config, config_file):
    """Save configuration to file"""
    import json
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def validate_config(config):
    """Validate configuration settings"""
    errors = []
    
    # Check required directories
    source_dir = Path(config['source_directory'])
    if not source_dir.exists():
        errors.append(f"Source directory does not exist: {source_dir}")
    
    target_dir = Path(config['target_directory'])
    if not target_dir.parent.exists():
        errors.append(f"Target directory parent does not exist: {target_dir.parent}")
    
    # Check email settings if notifications enabled
    if config['email_notifications']:
        required_email_fields = ['email_from', 'email_to', 'email_password']
        for field in required_email_fields:
            if not config[field]:
                errors.append(f"Email notification enabled but {field} not configured")
    
    # Check sync interval
    if config['sync_interval_minutes'] < 1:
        errors.append("Sync interval must be at least 1 minute")
    
    return errors
