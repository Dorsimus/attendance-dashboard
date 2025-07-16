#!/usr/bin/env python3
"""
Simple startup script for the Redstone Attendance Intelligence Platform
"""

import uvicorn
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

if __name__ == "__main__":
    print("🚀 Starting Redstone Attendance Intelligence Platform...")
    print("📊 Dashboard will be available at: http://localhost:8000/dashboard")
    print("👨‍💼 Admin Portal will be available at: http://localhost:8000/admin/login")
    print("⚡ Press Ctrl+C to stop the server")
    
    try:
        from app import create_app

        app, socketio = create_app()
        socketio.run(app, host="0.0.0.0", port=8000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
