from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..core.data_processor import AttendanceDataProcessor

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Create a dependency to get the processor instance
async def get_processor():
    from ..main import processor
    return processor

@router.get("/detailed-attendance/{date}")
async def get_detailed_attendance(date: str, processor: AttendanceDataProcessor = Depends(get_processor)):
    """Get detailed attendance for a specific date"""
    try:
        attendance_data = await processor.get_detailed_attendance_by_date(date)
        if not attendance_data:
            raise HTTPException(status_code=404, detail="No attendance data for the specified date")
        return {
            "success": True,
            "data": attendance_data,
            "date": date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-dates")
async def get_available_dates(processor: AttendanceDataProcessor = Depends(get_processor)):
    """Get a list of dates with available attendance data"""
    try:
        dates = await processor.get_available_dates()
        return {
            "success": True,
            "dates": dates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
