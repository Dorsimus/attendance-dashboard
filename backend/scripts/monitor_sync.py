#!/usr/bin/env python3
"""
Attendance Dashboard Data Sync Monitor
This script monitors the health and status of the data sync system.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

def load_metrics(metrics_file):
    """Load sync metrics from file"""
    try:
        with open(metrics_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading metrics: {e}")
        return None

def check_sync_health(metrics, config):
    """Check the health of the sync system"""
    issues = []
    
    if not metrics:
        issues.append("CRITICAL: No metrics available")
        return issues
    
    # Check last sync time
    if metrics.get('last_sync'):
        last_sync = datetime.fromisoformat(metrics['last_sync'])
        time_since_last_sync = datetime.now() - last_sync
        max_age = timedelta(hours=config['alert_thresholds']['data_age_hours'])
        
        if time_since_last_sync > max_age:
            issues.append(f"WARNING: Last sync was {time_since_last_sync} ago")
    else:
        issues.append("WARNING: No sync has been performed yet")
    
    # Check consecutive failures
    consecutive_failures = metrics.get('consecutive_failures', 0)
    if consecutive_failures >= config['alert_thresholds']['sync_failure_count']:
        issues.append(f"CRITICAL: {consecutive_failures} consecutive sync failures")
    
    # Check success rate
    total_syncs = metrics.get('total_syncs', 0)
    successful_syncs = metrics.get('successful_syncs', 0)
    
    if total_syncs > 0:
        success_rate = (successful_syncs / total_syncs) * 100
        if success_rate < 90:
            issues.append(f"WARNING: Low success rate: {success_rate:.1f}%")
    
    return issues

def display_status(metrics, config):
    """Display the current sync status"""
    print("=" * 60)
    print("ATTENDANCE DASHBOARD DATA SYNC STATUS")
    print("=" * 60)
    
    if not metrics:
        print("❌ No metrics available")
        return
    
    # Basic stats
    print(f"Total Syncs: {metrics.get('total_syncs', 0)}")
    print(f"Successful Syncs: {metrics.get('successful_syncs', 0)}")
    print(f"Failed Syncs: {metrics.get('failed_syncs', 0)}")
    print(f"Consecutive Failures: {metrics.get('consecutive_failures', 0)}")
    
    # Last sync info
    last_sync = metrics.get('last_sync')
    if last_sync:
        last_sync_dt = datetime.fromisoformat(last_sync)
        time_ago = datetime.now() - last_sync_dt
        print(f"Last Sync: {last_sync_dt.strftime('%Y-%m-%d %H:%M:%S')} ({time_ago} ago)")
    else:
        print("Last Sync: Never")
    
    # Last success info
    last_success = metrics.get('last_success')
    if last_success:
        last_success_dt = datetime.fromisoformat(last_success)
        time_ago = datetime.now() - last_success_dt
        print(f"Last Success: {last_success_dt.strftime('%Y-%m-%d %H:%M:%S')} ({time_ago} ago)")
    else:
        print("Last Success: Never")
    
    print("\n" + "=" * 60)
    
    # Health check
    issues = check_sync_health(metrics, config)
    if issues:
        print("🚨 HEALTH ISSUES DETECTED:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ All systems healthy")
    
    print("=" * 60)

def display_recent_runs(metrics, count=5):
    """Display recent sync runs"""
    print(f"\nRECENT SYNC RUNS (last {count}):")
    print("-" * 60)
    
    recent_runs = metrics.get('sync_runs', [])[-count:]
    
    if not recent_runs:
        print("No sync runs recorded")
        return
    
    for run in reversed(recent_runs):
        timestamp = datetime.fromisoformat(run['timestamp'])
        status = "✅ SUCCESS" if run['success'] else "❌ FAILED"
        files = ", ".join(run['files_synced']) if run['files_synced'] else "None"
        
        print(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {status} | Files: {files}")
        
        if run.get('errors'):
            for error in run['errors']:
                print(f"  ERROR: {error}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Monitor attendance data sync system')
    parser.add_argument('--config', default='sync_config.json', help='Config file path')
    parser.add_argument('--metrics', default=None, help='Metrics file path (overrides config)')
    parser.add_argument('--recent', type=int, default=5, help='Number of recent runs to show')
    parser.add_argument('--health-check', action='store_true', help='Only perform health check')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # Load metrics
    metrics_file = args.metrics or config.get('metrics_file', 'sync_metrics.json')
    metrics = load_metrics(metrics_file)
    
    if args.health_check:
        # Only run health check
        issues = check_sync_health(metrics, config)
        if issues:
            print("Health check failed:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)
        else:
            print("Health check passed")
            sys.exit(0)
    
    # Display full status
    display_status(metrics, config)
    
    if metrics:
        display_recent_runs(metrics, args.recent)

if __name__ == '__main__':
    main()
