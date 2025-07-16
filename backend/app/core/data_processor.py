import asyncio
import json
import numpy as np
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import os
import sys
import random
from collections import defaultdict
import pandas as pd
from werkzeug.utils import secure_filename

# Add the parent directory to sys.path to import the original attendance tracker
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# from ..models import (
#     AttendanceMetrics, AlertData, RegionalData, EmployeeData, 
#     AttendanceStatus, AlertSeverity, TrendDirection, HistoricalData, AttendanceHistory
# )

class AttendanceDataProcessor:
    """
    Data processor that integrates with your existing attendance_tracker_v3.py
    Provides real-time data processing and analytics
    """
    
    def __init__(self):
        self.data_cache = {}
        self.last_refresh = None
        self.history_file = 'attendance_history.json'
        self.rm_history_file = 'rm_attendance_history.json'
        self.employee_file = 'peoplehubdirectory20250708.csv'
        self.alerts_cache = []
        self.employee_data = {}
        self.attendance_data = {}
        self.rm_attendance_data = {}
        # Set data directory based on environment
        self.data_dir = Path(__file__).parent.parent.parent / 'data'
        
    async def initialize(self):
        """Initialize the data processor"""
        try:
            # Load existing attendance history
            await self.load_historical_data()
            print("✅ Data processor initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize data processor: {e}")
            # Create sample data for demo
            await self.create_sample_data()
    
    async def load_historical_data(self):
        """Load historical attendance data from your existing JSON file"""
        try:
            # Check for data in the container data directory first
            history_path = self.data_dir / self.history_file
            
            print(f"🔍 Looking for history file at: {history_path}")
            print(f"🔍 File exists: {history_path.exists()}")
            
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    self.attendance_data = json.load(f)
                    
                # Process historical data into aggregated format
                self.historical_data = self._process_attendance_data()
                print(f"✅ Loaded attendance data for {len(self.attendance_data)} dates")
                
                # Load Regional Manager attendance data
                await self.load_rm_attendance_data()
                
                # Load employee data
                await self.load_employee_data()
            else:
                print("⚠️  No historical data found, creating sample data")
                await self.create_sample_data()
                
        except Exception as e:
            print(f"❌ Error loading historical data: {e}")
            await self.create_sample_data()
    
    async def load_rm_attendance_data(self):
        """Load Regional Manager attendance data from JSON file"""
        try:
            rm_history_path = self.data_dir / self.rm_history_file

            if rm_history_path.exists():
                with open(rm_history_path, 'r', encoding='utf-8') as f:
                    self.rm_attendance_data = json.load(f)
                print(f"✅ Loaded Regional Manager attendance data for {len(self.rm_attendance_data)} dates")
        except Exception as e:
            print(f"❌ Error loading Regional Manager attendance data: {e}")

    async def load_employee_data(self):
        """Load employee data from CSV file"""
        try:
            employee_path = self.data_dir / self.employee_file
            
            if employee_path.exists():
                with open(employee_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    for row in csv_reader:
                        email = row.get('email', '').strip()
                        if email and '@' in email:
                            self.employee_data[email] = {
                                "name": row.get('name', '').strip('"'),
                                "title": row.get('title', '').strip('"'),
                                "department": row.get('department', '').strip('"'),
                                "office": row.get('office', '').strip('"'),
                                "manager": row.get('manager', '').strip('"'),
                                "email": email
                            }
                print(f"✅ Loaded {len(self.employee_data)} employee records")
        except Exception as e:
            print(f"❌ Error loading employee data: {e}")
    
    def _process_attendance_data(self) -> Dict[str, Dict[str, Any]]:
        """Process raw attendance data into historical format"""
        processed_data = {}
        
        for date_str, date_data in self.attendance_data.items():
            total_employees = len(date_data)
            present_count = sum(1 for emp in date_data.values() if emp.get('status') == 'Present')
            partial_count = sum(1 for emp in date_data.values() if emp.get('status') == 'Partial')
            absent_count = sum(1 for emp in date_data.values() if emp.get('status') == 'Absent')
            
            attendance_rate = (present_count / total_employees * 100) if total_employees > 0 else 0
            
            processed_data[date_str] = {
                'attendance_rate': attendance_rate,
                'present_count': present_count,
                'partial_count': partial_count,
                'absent_count': absent_count,
                'total_count': total_employees
            }
        
        return processed_data
    
    async def create_sample_data(self):
        """Create sample data for demonstration purposes"""
        # Create sample historical data
        sample_dates = []
        current_date = datetime.now()
        
        for i in range(8):
            date = current_date - timedelta(weeks=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Generate sample attendance data
            sample_dates.append({
                'date': date_str,
                'attendance_rate': np.random.uniform(75, 95),
                'present_count': np.random.randint(300, 400),
                'total_count': 400
            })
        
        self.historical_data = {}
        for data in sample_dates:
            self.historical_data[data['date']] = {
                'attendance_rate': data['attendance_rate'],
                'present_count': data['present_count'],
                'total_count': data['total_count']
            }
        
        print("📊 Created sample historical data for demo")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current attendance metrics from real data"""
        try:
            # Get the most recent date from our real data
            if hasattr(self, 'attendance_data') and self.attendance_data:
                # Sort dates and get the most recent
                recent_date = max(self.attendance_data.keys())
                recent_data = self.attendance_data[recent_date]
                
                # Calculate real metrics
                total_employees = len(recent_data)
                present_count = sum(1 for emp in recent_data.values() if emp.get('status') == 'Present')
                partial_count = sum(1 for emp in recent_data.values() if emp.get('status') == 'Partial')
                absent_count = sum(1 for emp in recent_data.values() if emp.get('status') == 'Absent')
                
                attendance_rate = (present_count / total_employees * 100) if total_employees > 0 else 0
                
                # Calculate average engagement score for present employees
                engagement_scores = [emp.get('engagement_score', 0) for emp in recent_data.values() 
                                   if emp.get('status') in ['Present', 'Partial'] and emp.get('engagement_score', 0) > 0]
                avg_engagement = np.mean(engagement_scores) if engagement_scores else 0
                
                # Calculate week-over-week change if we have enough data
                week_change = 0
                if len(self.attendance_data) >= 2:
                    sorted_dates = sorted(self.attendance_data.keys())
                    if len(sorted_dates) >= 2:
                        prev_date = sorted_dates[-2]
                        prev_data = self.attendance_data[prev_date]
                        prev_present = sum(1 for emp in prev_data.values() if emp.get('status') == 'Present')
                        prev_total = len(prev_data)
                        prev_rate = (prev_present / prev_total * 100) if prev_total > 0 else 0
                        week_change = attendance_rate - prev_rate
                
                metrics = {
                    'total_employees': total_employees,
                    'present_count': present_count,
                    'partial_count': partial_count,
                    'absent_count': absent_count,
                    'attendance_rate': round(attendance_rate, 1),
                    'target_rate': 85.0,
                    'week_over_week_change': round(week_change, 1),
                    'engagement_score': round(avg_engagement, 1),
                    'last_updated': recent_date,
                    'data_source': 'real'
                }
                
                return metrics
            else:
                # Fall back to default if no real data available
                return self._get_default_metrics()
            
        except Exception as e:
            print(f"Error getting current metrics: {e}")
            return self._get_default_metrics()
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default metrics when data is unavailable"""
        return {
            'total_employees': 400,
            'present_count': 340,
            'partial_count': 20,
            'absent_count': 40,
            'attendance_rate': 85.0,
            'target_rate': 85.0,
            'week_over_week_change': 0.0,
            'engagement_score': 75.0,
            'data_source': 'sample'
        }
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts and notifications"""
        alerts = []
        
        # Generate sample alerts for demo
        current_metrics = await self.get_current_metrics()
        
        # Critical attendance alert
        if current_metrics['attendance_rate'] < 80:
            alerts.append({
                'id': 'alert_1',
                'severity': 'critical',
                'title': 'Critical Attendance Alert',
                'message': f"Attendance dropped to {current_metrics['attendance_rate']:.1f}%",
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False,
                'action_required': True
            })
        
        # At-risk employees alert
        alerts.append({
            'id': 'alert_2',
            'severity': 'high',
            'title': 'At-Risk Employees',
            'message': '5 employees have 0% attendance in past 4 weeks',
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False,
            'action_required': True
        })
        
        # Positive recognition alert
        alerts.append({
            'id': 'alert_3',
            'severity': 'low',
            'title': 'Recognition Opportunity',
            'message': '15 employees have perfect attendance streaks',
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False,
            'action_required': False
        })
        
        return alerts
    
    async def get_regional_breakdown(self) -> List[Dict[str, Any]]:
        """Get manager and team performance data"""
        try:
            manager_data = []
            
            if hasattr(self, 'attendance_data') and self.attendance_data and hasattr(self, 'employee_data'):
                # Get the most recent date
                recent_date = max(self.attendance_data.keys())
                recent_data = self.attendance_data[recent_date]
                
                # Find all Regional and Area Managers
                regional_managers = {}
                area_managers = {}
                for email, emp_info in self.employee_data.items():
                    title = emp_info.get('title', '').strip('"')
                    if 'Regional Manager' in title:
                        regional_managers[email] = emp_info
                    elif 'Area Manager' in title:
                        area_managers[email] = emp_info
                
                # Process Regional Managers first
                for manager_email, manager_info in regional_managers.items():
                    manager_data.append(self._create_manager_data(manager_email, manager_info, recent_data, 'Regional Manager'))
                
                # Process Area Managers
                for manager_email, manager_info in area_managers.items():
                    manager_data.append(self._create_manager_data(manager_email, manager_info, recent_data, 'Area Manager'))
            
            # If no real data, fall back to sample data
            if not manager_data:
                regions = ['Texas', 'Florida', 'California', 'Arizona', 'Nevada']
                
                for region in regions:
                    total_employees = np.random.randint(30, 60)
                    present_count = int(total_employees * np.random.uniform(0.7, 0.95))
                    attendance_rate = (present_count / total_employees) * 100
                    
                    manager_data.append({
                        'manager_name': f'Manager {region}',
                        'manager_title': 'Regional Manager',
                        'manager_email': f'manager.{region.lower()}@redstone.com',
                        'manager_office': region,
                        'manager_personal_attendance': round(np.random.uniform(80, 100), 1),
                        'manager_current_status': np.random.choice(['Present', 'Absent']),
                        'manager_current_attendance': np.random.randint(0, 2),
                        'team_size': total_employees - 1,
                        'team_attendance_rate': round(attendance_rate, 1),
                        'team_present_count': present_count,
                        'team_engagement_score': round(np.random.uniform(60, 90), 1),
                        'team_four_week_rate': round(np.random.uniform(70, 95), 1),
                        'team_at_risk_count': np.random.randint(0, 8),
                        'region_name': region,
                        'total_employees': total_employees,
                        'present_count': present_count,
                        'attendance_rate': round(attendance_rate, 1),
                        'risk_score': round(np.random.uniform(10, 80), 1),
                        'at_risk_count': np.random.randint(0, 8),
                        'trend': np.random.choice(['improving', 'stable', 'declining'])
                    })
            
            # Sort by attendance rate (lowest first for attention)
            manager_data.sort(key=lambda x: x['attendance_rate'])
            
            return manager_data
            
        except Exception as e:
            print(f"Error getting regional breakdown: {e}")
            return []
    
    async def get_attendance_history(self, weeks: int = 8) -> Dict[str, Any]:
        """Get historical attendance data from real data"""
        try:
            historical_points = []
            
            # Use real historical data if available
            if hasattr(self, 'historical_data') and self.historical_data:
                # Sort available dates
                sorted_dates = sorted(self.historical_data.keys())
                
                for date_str in sorted_dates:
                    data = self.historical_data[date_str]
                    historical_points.append({
                        'date': date_str,
                        'attendance_rate': round(data.get('attendance_rate', 0), 1),
                        'present_count': data.get('present_count', 0),
                        'total_count': data.get('total_count', 0)
                    })
            
            # If no real data, fall back to sample data
            if not historical_points:
                current_date = datetime.now()
                for i in range(weeks):
                    date = current_date - timedelta(weeks=i)
                    date_str = date.strftime('%Y-%m-%d')
                    
                    historical_points.append({
                        'date': date_str,
                        'attendance_rate': round(np.random.uniform(75, 95), 1),
                        'present_count': np.random.randint(300, 400),
                        'total_count': 400
                    })
            
            # Sort by date
            historical_points.sort(key=lambda x: x['date'])
            
            # Calculate average and trend
            rates = [point['attendance_rate'] for point in historical_points]
            average_rate = np.mean(rates) if rates else 0
            
            # Simple trend calculation
            if len(rates) >= 2:
                recent_avg = np.mean(rates[-3:]) if len(rates) >= 3 else rates[-1]
                older_avg = np.mean(rates[:3]) if len(rates) >= 3 else rates[0]
                if recent_avg > older_avg + 2:
                    trend = 'improving'
                elif recent_avg < older_avg - 2:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            return {
                'data': historical_points,
                'weeks': len(historical_points),
                'average_rate': round(average_rate, 1),
                'trend': trend
            }
            
        except Exception as e:
            print(f"Error getting attendance history: {e}")
            return {
                'data': [],
                'weeks': weeks,
                'average_rate': 85.0,
                'trend': 'stable'
            }
    
    async def get_at_risk_employees(self) -> List[Dict[str, Any]]:
        """Get employees who are at risk based on attendance patterns from real data"""
        try:
            at_risk_employees = []
            
            if hasattr(self, 'attendance_data') and self.attendance_data and hasattr(self, 'employee_data'):
                # Calculate attendance rates for each employee across all available dates
                employee_attendance = defaultdict(lambda: {'total': 0, 'present': 0, 'absent': 0})
                
                # Count attendance for each employee
                for date_str, date_data in self.attendance_data.items():
                    for email, attendance in date_data.items():
                        employee_attendance[email]['total'] += 1
                        
                        status = attendance.get('status', 'Absent')
                        if status == 'Present':
                            employee_attendance[email]['present'] += 1
                        elif status == 'Absent':
                            employee_attendance[email]['absent'] += 1
                
                # Find employees with poor attendance
                for email, stats in employee_attendance.items():
                    if stats['total'] > 0:
                        attendance_rate = (stats['present'] / stats['total']) * 100
                        
                        # Consider employees with <50% attendance as at-risk
                        if attendance_rate < 50:
                            emp_info = self.employee_data.get(email, {})
                            
                            # Find last attendance date
                            last_attendance_date = None
                            for date_str in sorted(self.attendance_data.keys(), reverse=True):
                                if email in self.attendance_data[date_str]:
                                    if self.attendance_data[date_str][email].get('status') == 'Present':
                                        last_attendance_date = date_str
                                        break
                            
                            at_risk_employees.append({
                                'id': email.replace('@', '_').replace('.', '_'),
                                'name': emp_info.get('name', 'Unknown'),
                                'email': email,
                                'location': emp_info.get('office', 'Unknown'),
                                'role': emp_info.get('title', 'Unknown'),
                                'risk_score': round(100 - attendance_rate, 1),
                                'four_week_rate': round(attendance_rate, 1),
                                'current_streak': stats['absent'],
                                'trend': 'declining',
                                'last_attendance': last_attendance_date or 'Never'
                            })
                
                # Sort by risk score (highest first)
                at_risk_employees.sort(key=lambda x: x['risk_score'], reverse=True)
            
            # If no real data, fall back to sample data
            if not at_risk_employees:
                sample_names = [
                    'John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Wilson',
                    'David Brown', 'Maria Garcia', 'Robert Jones', 'Jennifer Taylor'
                ]
                
                for i, name in enumerate(sample_names[:5]):
                    at_risk_employees.append({
                        'id': f'emp_{i+1}',
                        'name': name,
                        'email': f'{name.lower().replace(" ", ".")}.{i+1}@redstone.com',
                        'location': np.random.choice(['Texas', 'Florida', 'California']),
                        'role': 'Community Manager',
                        'risk_score': round(np.random.uniform(75, 95), 1),
                        'four_week_rate': round(np.random.uniform(0, 40), 1),
                        'current_streak': 0,
                        'trend': 'declining',
                        'last_attendance': (datetime.now() - timedelta(days=np.random.randint(7, 30))).strftime('%Y-%m-%d')
                    })
            
            return at_risk_employees
            
        except Exception as e:
            print(f"Error getting at-risk employees: {e}")
            return []
    
    async def get_region_detail(self, region_name: str) -> Dict[str, Any]:
        """Get detailed data for a specific region"""
        # Generate sample regional detail
        return {
            'region_name': region_name,
            'total_employees': np.random.randint(40, 80),
            'present_count': np.random.randint(25, 70),
            'attendance_rate': round(np.random.uniform(70, 95), 1),
            'manager_count': np.random.randint(3, 8),
            'at_risk_employees': await self.get_at_risk_employees(),
            'top_performers': [
                {'name': 'Top Performer 1', 'streak': 12},
                {'name': 'Top Performer 2', 'streak': 10}
            ]
        }
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            # In a real implementation, this would update the database
            print(f"Alert {alert_id} acknowledged")
            return True
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            return False
    
    async def refresh_data(self):
        """Refresh data from source"""
        try:
            # In a real implementation, this would re-run your attendance_tracker_v3.py
            # or reload data from the source files
            await self.load_historical_data()
            self.last_refresh = datetime.now()
            print("📊 Data refreshed successfully")
        except Exception as e:
            print(f"Error refreshing data: {e}")
            raise
    
    async def get_detailed_attendance_by_date(self, date: str) -> Dict[str, Any]:
        """Get detailed attendance for a specific date"""
        try:
            if hasattr(self, 'attendance_data') and self.attendance_data:
                # Check if the date exists in our data
                if date in self.attendance_data:
                    date_data = self.attendance_data[date]
                    detailed_attendees = []
                    
                    for email, attendance in date_data.items():
                        # Get employee info
                        emp_info = self.employee_data.get(email, {})
                        
                        # Format duration from minutes to readable format
                        duration_minutes = attendance.get('duration_minutes', 0)
                        if duration_minutes > 0:
                            hours = int(duration_minutes // 60)
                            minutes = int(duration_minutes % 60)
                            if hours > 0:
                                duration_str = f"{hours}h {minutes}m"
                            else:
                                duration_str = f"{minutes}m"
                        else:
                            duration_str = "0m"
                        
                        # Use the actual name from the data, fall back to employee directory
                        display_name = attendance.get('name', emp_info.get('name', 'Unknown'))
                        
                        attendee_info = {
                            'email': email,
                            'name': display_name,
                            'title': emp_info.get('title', 'Unknown'),
                            'department': emp_info.get('department', 'Unknown'),
                            'office': emp_info.get('office', attendance.get('location', 'Unknown')),
                            'status': attendance.get('status', 'Unknown'),
                            'join_time': 'N/A',  # Not available in this data format
                            'leave_time': 'N/A',  # Not available in this data format
                            'duration': duration_str,
                            'engagement_score': attendance.get('engagement_score', 0),
                            'location': attendance.get('location', 'Unknown')
                        }
                        detailed_attendees.append(attendee_info)
                    
                    # Sort by status (Present first, then Partial, then Absent)
                    status_order = {'Present': 1, 'Partial': 2, 'Absent': 3}
                    detailed_attendees.sort(key=lambda x: status_order.get(x['status'], 4))
                    
                    # Calculate summary stats
                    total_employees = len(detailed_attendees)
                    present_count = sum(1 for emp in detailed_attendees if emp['status'] == 'Present')
                    partial_count = sum(1 for emp in detailed_attendees if emp['status'] == 'Partial')
                    absent_count = sum(1 for emp in detailed_attendees if emp['status'] == 'Absent')
                    
                    return {
                        'date': date,
                        'total_employees': total_employees,
                        'present_count': present_count,
                        'partial_count': partial_count,
                        'absent_count': absent_count,
                        'attendance_rate': round((present_count / total_employees * 100) if total_employees > 0 else 0, 1),
                        'detailed_attendees': detailed_attendees
                    }
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error getting detailed attendance for date {date}: {e}")
            return None
    
    async def get_available_dates(self) -> List[str]:
        """Get a list of dates with available attendance data"""
        try:
            if hasattr(self, 'attendance_data') and self.attendance_data:
                # Return sorted list of available dates
                dates = sorted(self.attendance_data.keys())
                return dates
            else:
                return []
        except Exception as e:
            print(f"Error getting available dates: {e}")
            return []
    
    def _calculate_employee_attendance(self, employee_email: str) -> Dict[str, Any]:
        """Calculate attendance rate for a specific employee"""
        try:
            if not hasattr(self, 'attendance_data') or not self.attendance_data:
                return {'rate': 0, 'total': 0, 'present': 0, 'absent': 0}
            
            total_days = 0
            present_days = 0
            absent_days = 0
            
            for date_str, date_data in self.attendance_data.items():
                if employee_email in date_data:
                    total_days += 1
                    status = date_data[employee_email].get('status', 'Absent')
                    if status == 'Present':
                        present_days += 1
                    elif status == 'Absent':
                        absent_days += 1
            
            rate = (present_days / total_days * 100) if total_days > 0 else 0
            
            return {
                'rate': rate,
                'total': total_days,
                'present': present_days,
                'absent': absent_days
            }
        except Exception as e:
            print(f"Error calculating attendance for {employee_email}: {e}")
            return {'rate': 0, 'total': 0, 'present': 0, 'absent': 0}
    
    def _calculate_employee_attendance_with_rm(self, employee_email: str, manager_type: str) -> Dict[str, Any]:
        """Calculate attendance rate for a specific employee including Regional Manager data"""
        try:
            if not hasattr(self, 'attendance_data') or not self.attendance_data:
                return {'rate': 0, 'total': 0, 'present': 0, 'absent': 0}
            
            total_days = 0
            present_days = 0
            absent_days = 0
            
            # First check regular attendance data for all dates
            for date_str, date_data in self.attendance_data.items():
                if employee_email in date_data:
                    total_days += 1
                    status = date_data[employee_email].get('status', 'Absent')
                    if status == 'Present':
                        present_days += 1
                    elif status == 'Absent':
                        absent_days += 1
            
            # For Regional Managers, also check the RM attendance data for all dates
            if manager_type == 'Regional Manager' and hasattr(self, 'rm_attendance_data') and self.rm_attendance_data:
                for date_str, rm_date_data in self.rm_attendance_data.items():
                    if employee_email in rm_date_data:
                        # Check if we already counted this date in regular attendance
                        if date_str not in self.attendance_data or employee_email not in self.attendance_data[date_str]:
                            total_days += 1
                            status = rm_date_data[employee_email].get('status', 'Absent')
                            if status == 'Present':
                                present_days += 1
                            elif status == 'Absent':
                                absent_days += 1
                        else:
                            # If we have both regular and RM data for the same date, prefer RM data for Regional Managers
                            # Remove the regular attendance count and add RM data
                            regular_status = self.attendance_data[date_str][employee_email].get('status', 'Absent')
                            rm_status = rm_date_data[employee_email].get('status', 'Absent')
                            
                            # Adjust counts by removing regular data and adding RM data
                            if regular_status == 'Present':
                                present_days -= 1
                            elif regular_status == 'Absent':
                                absent_days -= 1
                            
                            if rm_status == 'Present':
                                present_days += 1
                            elif rm_status == 'Absent':
                                absent_days += 1
            
            rate = (present_days / total_days * 100) if total_days > 0 else 0
            
            return {
                'rate': rate,
                'total': total_days,
                'present': present_days,
                'absent': absent_days
            }
        except Exception as e:
            print(f"Error calculating attendance with RM data for {employee_email}: {e}")
            return {'rate': 0, 'total': 0, 'present': 0, 'absent': 0}
    
    def _calculate_team_performance(self, team_member_emails: List[str], recent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate team performance metrics"""
        try:
            if not team_member_emails:
                return {
                    'attendance_rate': 0,
                    'present_count': 0,
                    'engagement_score': 0,
                    'at_risk_count': 0
                }
            
            present_count = 0
            total_engagement = 0
            engagement_count = 0
            at_risk_count = 0
            
            for email in team_member_emails:
                if email in recent_data:
                    status = recent_data[email].get('status', 'Absent')
                    if status == 'Present':
                        present_count += 1
                    
                    # Calculate engagement score
                    engagement = recent_data[email].get('engagement_score', 0)
                    if engagement > 0:
                        total_engagement += engagement
                        engagement_count += 1
                
                # Check if employee is at risk (using historical data)
                employee_attendance = self._calculate_employee_attendance(email)
                if employee_attendance['rate'] < 50:
                    at_risk_count += 1
            
            attendance_rate = (present_count / len(team_member_emails) * 100) if len(team_member_emails) > 0 else 0
            avg_engagement = (total_engagement / engagement_count) if engagement_count > 0 else 0
            
            return {
                'attendance_rate': attendance_rate,
                'present_count': present_count,
                'engagement_score': avg_engagement,
                'at_risk_count': at_risk_count
            }
        except Exception as e:
            print(f"Error calculating team performance: {e}")
            return {
                'attendance_rate': 0,
                'present_count': 0,
                'engagement_score': 0,
                'at_risk_count': 0
            }
    
    def _create_manager_data(self, manager_email: str, manager_info: Dict[str, Any], recent_data: Dict[str, Any], manager_type: str) -> Dict[str, Any]:
        """Create manager data object with personal and team performance"""
        try:
            # Calculate manager's personal attendance (including RM data for Regional Managers)
            manager_attendance = self._calculate_employee_attendance_with_rm(manager_email, manager_type)
            
            # Find team members managed by this manager
            team_members = []
            manager_name = manager_info.get('name', '').strip('"')
            
            # Look for employees who report to this manager
            for email, emp_info in self.employee_data.items():
                emp_manager = emp_info.get('manager', '').strip('"')
                if emp_manager == manager_name and email != manager_email:
                    team_members.append(email)
            
            # Calculate team performance
            team_stats = self._calculate_team_performance(team_members, recent_data)
            
            # Get manager's current attendance status
            # For Regional Managers, check the separate RM attendance file first
            manager_current_status = 'Absent'
            manager_current_attendance = 0
            
            # Get the most recent date from our attendance data
            recent_date = max(self.attendance_data.keys()) if self.attendance_data else None
            
            if manager_type == 'Regional Manager' and hasattr(self, 'rm_attendance_data') and self.rm_attendance_data:
                # Check if we have RM attendance data for the recent date
                if recent_date and recent_date in self.rm_attendance_data:
                    rm_data = self.rm_attendance_data[recent_date].get(manager_email, {})
                    manager_current_status = rm_data.get('status', 'Absent')
                    manager_current_attendance = 1 if manager_current_status == 'Present' else 0
            else:
                # Fall back to regular attendance data
                manager_current_status = recent_data.get(manager_email, {}).get('status', 'Absent')
                manager_current_attendance = 1 if manager_current_status == 'Present' else 0
            
            return {
                'manager_name': manager_name,
                'manager_title': manager_info.get('title', '').strip('"'),
                'manager_type': manager_type,
                'manager_email': manager_email,
                'manager_office': manager_info.get('office', '').strip('"'),
                'manager_personal_attendance': round(manager_attendance['rate'], 1),
                'manager_current_status': manager_current_status,
                'manager_current_attendance': manager_current_attendance,
                'team_size': len(team_members),
                'team_attendance_rate': round(team_stats['attendance_rate'], 1),
                'team_present_count': team_stats['present_count'],
                'team_engagement_score': round(team_stats['engagement_score'], 1),
                'team_four_week_rate': round(team_stats['attendance_rate'], 1),
                'team_at_risk_count': team_stats['at_risk_count'],
                'region_name': manager_info.get('office', '').strip('"'),
                'total_employees': len(team_members) + 1,  # Team + manager
                'present_count': team_stats['present_count'] + manager_current_attendance,
                'attendance_rate': round((team_stats['present_count'] + manager_current_attendance) / (len(team_members) + 1) * 100, 1) if len(team_members) > 0 else manager_current_attendance * 100,
                'risk_score': round(100 - team_stats['attendance_rate'], 1),
                'at_risk_count': team_stats['at_risk_count'],
                'trend': 'stable'  # Would need historical data for real trend
            }
        except Exception as e:
            print(f"Error creating manager data for {manager_email}: {e}")
            return {}
    
    async def process_directory_file(self, file_path: str) -> bool:
        """Process uploaded directory file and update employee data"""
        try:
            import pandas as pd
            
            # Determine file type and read accordingly
            if file_path.endswith('.csv'):
                # Try different encodings for CSV files
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='cp1252')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            # Process the directory data
            updated_count = 0
            for _, row in df.iterrows():
                email = str(row.get('email', '')).strip()
                if email and '@' in email:
                    self.employee_data[email] = {
                        "name": str(row.get('name', '')).strip('"'),
                        "title": str(row.get('title', '')).strip('"'),
                        "department": str(row.get('department', '')).strip('"'),
                        "office": str(row.get('office', '')).strip('"'),
                        "manager": str(row.get('manager', '')).strip('"'),
                        "email": email
                    }
                    updated_count += 1
            
            # No need to save to file - just keep in memory for now
            # The data processor will use the in-memory data
            
            print(f"✅ Processed directory file: {updated_count} employees updated in memory")
            return True
            
        except Exception as e:
            print(f"❌ Error processing directory file: {e}")
            return False
    
    async def process_attendance_file(self, file_path: str) -> bool:
        """Process uploaded attendance file and update attendance data"""
        try:
            import pandas as pd
            
            # Determine file type and read accordingly
            if file_path.endswith('.csv'):
                # Try different encodings and separators for CSV files
                df = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    for sep in [',', ';', '\t']:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding, sep=sep, on_bad_lines='skip')
                            if not df.empty and len(df.columns) > 1:
                                break
                        except (UnicodeDecodeError, pd.errors.ParserError):
                            continue
                    if df is not None and not df.empty:
                        break
                
                if df is None or df.empty:
                    raise ValueError("Could not parse CSV file with any encoding/separator combination")
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.json'):
                # Try different encodings for JSON files
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            json_data = json.load(f)
                    except UnicodeDecodeError:
                        with open(file_path, 'r', encoding='cp1252') as f:
                            json_data = json.load(f)
                
                # If it's already in the format we expect
                if isinstance(json_data, dict) and all(isinstance(v, dict) for v in json_data.values()):
                    # Update attendance data directly
                    for date_str, date_data in json_data.items():
                        self.attendance_data[date_str] = date_data
                    
                    # Save updated attendance data
                    await self._save_attendance_data()
                    
                    print(f"✅ Processed attendance JSON file: {len(json_data)} dates updated")
                    return True
                else:
                    raise ValueError("JSON file format not recognized")
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            # Process CSV/Excel data
            if not file_path.endswith('.json'):
                # Expected columns: Date, Employee (email), Status, Duration (optional)
                required_columns = ['Date', 'Employee', 'Status']
                
                # Check if required columns exist (case-insensitive)
                df_columns = df.columns.str.lower()
                for col in required_columns:
                    if col.lower() not in df_columns:
                        raise ValueError(f"Missing required column: {col}")
                
                # Normalize column names
                df.columns = df.columns.str.lower()
                
                # Group by date and process
                dates_processed = set()
                for _, row in df.iterrows():
                    date_str = str(row['date']).strip()
                    email = str(row['employee']).strip()
                    status = str(row['status']).strip()
                    duration = row.get('duration', 0) if 'duration' in df.columns else 0
                    
                    # Parse date if needed
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        date_str = parsed_date.strftime('%Y-%m-%d')
                    except:
                        try:
                            parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                            date_str = parsed_date.strftime('%Y-%m-%d')
                        except:
                            continue  # Skip invalid dates
                    
                    # Initialize date if not exists
                    if date_str not in self.attendance_data:
                        self.attendance_data[date_str] = {}
                    
                    # Get employee name from directory or use email
                    emp_name = self.employee_data.get(email, {}).get('name', email)
                    
                    # Add attendance record
                    self.attendance_data[date_str][email] = {
                        'name': emp_name,
                        'status': status,
                        'duration': duration,
                        'duration_minutes': duration,
                        'location': self.employee_data.get(email, {}).get('office', 'Unknown')
                    }
                    
                    dates_processed.add(date_str)
                
                # Save updated attendance data
                await self._save_attendance_data()
                
                print(f"✅ Processed attendance file: {len(dates_processed)} dates updated")
                return True
            
        except Exception as e:
            print(f"❌ Error processing attendance file: {e}")
            return False
    
    async def _save_attendance_data(self):
        """Save attendance data to JSON file"""
        try:
            parent_dir = Path(__file__).parent.parent.parent.parent.parent
            history_path = parent_dir / self.history_file
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.attendance_data, f, indent=2, ensure_ascii=False)
            
            # Reprocess historical data
            self.historical_data = self._process_attendance_data()
            
            print(f"✅ Saved attendance data to {history_path}")
            
        except Exception as e:
            print(f"❌ Error saving attendance data: {e}")
            raise
