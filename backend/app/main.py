from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from pathlib import Path

# Import our custom modules
from .core.data_processor import AttendanceDataProcessor
from .core.analytics_engine import AnalyticsEngine
from .models import AttendanceMetrics, RealTimeUpdate, AlertData
from .routers import dashboard

# Global variables for real-time data
processor = AttendanceDataProcessor()
analytics = AnalyticsEngine()
connected_clients = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Starting Redstone Attendance Intelligence Platform...")
    # Initialize data processor with existing attendance data
    await processor.initialize()
    yield
    print("⚠️  Shutting down...")

app = FastAPI(
    title="Redstone Attendance Intelligence Platform",
    description="Real-time workforce engagement and attendance analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ==== WEBSOCKET FOR REAL-TIME UPDATES ====
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    connected_clients.add(websocket)
    
    try:
        # Send initial data
        initial_data = await get_dashboard_data()
        await websocket.send_json({
            "type": "initial_data",
            "data": initial_data
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (could be pings from client)
                message = await websocket.receive_text()
                # Echo back or handle specific commands
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            except:
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)

# ==== CORE API ENDPOINTS ====

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "🏢 Redstone Attendance Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics():
    """Get current dashboard metrics"""
    try:
        metrics = await processor.get_current_metrics()
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get complete dashboard data"""
    try:
        # Get current metrics
        metrics = await processor.get_current_metrics()
        
        # Get alerts
        alerts = await processor.get_active_alerts()
        
        # Get predictive insights
        predictions = await analytics.get_predictions()
        
        # Get regional data
        regional_data = await processor.get_regional_breakdown()
        
        # Get attendance history for the chart
        attendance_history = await processor.get_attendance_history()
        
        # Get at-risk employees
        at_risk_employees = await processor.get_at_risk_employees()
        
        return {
            "metrics": metrics,
            "alerts": alerts,
            "predictions": predictions,
            "regional_data": regional_data,
            "attendance_history": attendance_history,
            "at_risk_employees": at_risk_employees,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attendance/history")
async def get_attendance_history(weeks: int = 8):
    """Get historical attendance data"""
    try:
        history = await processor.get_attendance_history(weeks)
        return {
            "success": True,
            "data": history,
            "weeks": weeks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/predictions")
async def get_predictions():
    """Get AI-powered predictions"""
    try:
        predictions = await analytics.get_detailed_predictions()
        return {
            "success": True,
            "predictions": predictions,
            "model_version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts():
    """Get current alerts and notifications"""
    try:
        alerts = await processor.get_active_alerts()
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        success = await processor.acknowledge_alert(alert_id)
        if success:
            # Broadcast update to connected clients
            await broadcast_update({
                "type": "alert_acknowledged",
                "alert_id": alert_id,
                "timestamp": datetime.now().isoformat()
            })
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/regions/{region_name}")
async def get_region_detail(region_name: str):
    """Get detailed data for a specific region"""
    try:
        region_data = await processor.get_region_detail(region_name)
        return {
            "success": True,
            "region": region_name,
            "data": region_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employees/at-risk")
async def get_at_risk_employees():
    """Get employees who are at risk based on attendance patterns"""
    try:
        at_risk = await processor.get_at_risk_employees()
        return {
            "success": True,
            "employees": at_risk,
            "count": len(at_risk)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/refresh")
async def refresh_data():
    """Manually refresh data from source"""
    try:
        await processor.refresh_data()
        
        # Broadcast update to all connected clients
        await broadcast_update({
            "type": "data_refreshed",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"success": True, "message": "Data refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==== UTILITY FUNCTIONS ====

async def broadcast_update(update_data: dict):
    """Broadcast updates to all connected WebSocket clients"""
    if connected_clients:
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send_json(update_data)
            except:
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            connected_clients.discard(client)

# ==== BACKGROUND TASKS ====

async def periodic_updates():
    """Send periodic updates to dashboard"""
    while True:
        try:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Get fresh data
            dashboard_data = await get_dashboard_data()
            
            # Broadcast to all connected clients
            await broadcast_update({
                "type": "periodic_update",
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error in periodic updates: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Start background tasks
@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(periodic_updates())

# ==== HEALTH CHECK ====

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(connected_clients),
        "version": "1.0.0"
    }

@app.get("/dashboard")
async def serve_dashboard():
    """Serve the HTML dashboard"""
    from fastapi.responses import FileResponse
    dashboard_path = Path("app/static/dashboard.html")
    if dashboard_path.exists():
        return FileResponse(dashboard_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
