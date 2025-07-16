from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class AttendanceStatus(str, Enum):
    """Attendance status enumeration"""
    PRESENT = "present"
    PARTIAL = "partial"
    ABSENT = "absent"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TrendDirection(str, Enum):
    """Trend direction"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"

class AttendanceMetrics(BaseModel):
    """Core attendance metrics"""
    total_employees: int = Field(..., description="Total number of employees")
    present_count: int = Field(..., description="Number of present employees")
    partial_count: int = Field(..., description="Number of partially present employees")
    absent_count: int = Field(..., description="Number of absent employees")
    attendance_rate: float = Field(..., description="Overall attendance rate (%)")
    target_rate: float = Field(85.0, description="Target attendance rate (%)")
    week_over_week_change: float = Field(0.0, description="Week-over-week change (%)")
    engagement_score: float = Field(0.0, description="Average engagement score")
    
class EmployeeData(BaseModel):
    """Individual employee data"""
    id: str = Field(..., description="Employee ID")
    name: str = Field(..., description="Employee name")
    email: str = Field(..., description="Employee email")
    location: str = Field(..., description="Employee location")
    role: str = Field(..., description="Employee role")
    manager: Optional[str] = Field(None, description="Manager name")
    status: AttendanceStatus = Field(..., description="Current attendance status")
    duration_minutes: int = Field(0, description="Meeting duration in minutes")
    engagement_score: float = Field(0.0, description="Engagement score (0-100)")
    risk_score: float = Field(0.0, description="Risk score (0-100)")
    current_streak: int = Field(0, description="Current attendance streak")
    four_week_rate: float = Field(0.0, description="4-week attendance rate (%)")
    trend: TrendDirection = Field(TrendDirection.STABLE, description="Attendance trend")
    
class AlertData(BaseModel):
    """Alert/notification data"""
    id: str = Field(..., description="Alert ID")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    employee_id: Optional[str] = Field(None, description="Related employee ID")
    location: Optional[str] = Field(None, description="Related location")
    timestamp: datetime = Field(..., description="Alert timestamp")
    acknowledged: bool = Field(False, description="Whether alert has been acknowledged")
    action_required: bool = Field(False, description="Whether action is required")
    
class RegionalData(BaseModel):
    """Regional attendance data"""
    region_name: str = Field(..., description="Region name")
    total_employees: int = Field(..., description="Total employees in region")
    present_count: int = Field(..., description="Present employees")
    attendance_rate: float = Field(..., description="Region attendance rate (%)")
    risk_score: float = Field(..., description="Average risk score")
    at_risk_count: int = Field(..., description="Number of at-risk employees")
    trend: TrendDirection = Field(..., description="Regional trend")
    
class PredictionData(BaseModel):
    """Predictive analytics data"""
    next_week_forecast: float = Field(..., description="Next week attendance forecast (%)")
    confidence: float = Field(..., description="Prediction confidence (0-100)")
    factors: Dict[str, float] = Field(..., description="Factors affecting prediction")
    recommendations: List[str] = Field(..., description="Recommended actions")
    
class RealTimeUpdate(BaseModel):
    """Real-time update message"""
    type: str = Field(..., description="Update type")
    data: Dict[str, Any] = Field(..., description="Update data")
    timestamp: datetime = Field(..., description="Update timestamp")
    
class DashboardData(BaseModel):
    """Complete dashboard data"""
    metrics: AttendanceMetrics
    alerts: List[AlertData]
    predictions: PredictionData
    regional_data: List[RegionalData]
    last_updated: datetime
    
class HistoricalData(BaseModel):
    """Historical attendance data point"""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    attendance_rate: float = Field(..., description="Attendance rate for that date")
    present_count: int = Field(..., description="Number present")
    total_count: int = Field(..., description="Total employees")
    
class AttendanceHistory(BaseModel):
    """Historical attendance collection"""
    data: List[HistoricalData] = Field(..., description="Historical data points")
    weeks: int = Field(..., description="Number of weeks included")
    average_rate: float = Field(..., description="Average attendance rate")
    trend: TrendDirection = Field(..., description="Overall trend")
    
class ActionItem(BaseModel):
    """Action item for managers"""
    id: str = Field(..., description="Action item ID")
    type: str = Field(..., description="Action type")
    priority: str = Field(..., description="Priority level")
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    employee_id: Optional[str] = Field(None, description="Related employee")
    due_date: Optional[datetime] = Field(None, description="Due date")
    completed: bool = Field(False, description="Whether completed")
    
class TeamPerformance(BaseModel):
    """Team performance metrics"""
    manager_name: str = Field(..., description="Manager name")
    team_size: int = Field(..., description="Team size")
    attendance_rate: float = Field(..., description="Team attendance rate")
    average_engagement: float = Field(..., description="Average engagement score")
    at_risk_count: int = Field(..., description="At-risk team members")
    top_performers: List[str] = Field(..., description="Top performing team members")
    
class RecognitionData(BaseModel):
    """Recognition and achievements"""
    employee_id: str = Field(..., description="Employee ID")
    employee_name: str = Field(..., description="Employee name")
    achievement_type: str = Field(..., description="Type of achievement")
    description: str = Field(..., description="Achievement description")
    streak_count: Optional[int] = Field(None, description="Streak count if applicable")
    date_achieved: datetime = Field(..., description="Date of achievement")
