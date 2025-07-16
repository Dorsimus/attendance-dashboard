from flask_socketio import emit, join_room, leave_room
import json

def register_socketio_events(socketio):
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('status', {'msg': 'Connected successfully'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('join_dashboard')
    def handle_join_dashboard():
        """Handle dashboard room join"""
        join_room('dashboard')
        emit('joined', {'room': 'dashboard'})
        
        # Send initial data
        emit('initial_data', {
            'type': 'initial_data',
            'data': {
                'metrics': {
                    'attendance_rate': 85.5,
                    'present_count': 342,
                    'total_employees': 400,
                    'engagement_score': 78,
                    'week_over_week_change': 2.3
                },
                'alerts': [],
                'regional_data': [],
                'attendance_history': {
                    'data': []
                },
                'at_risk_employees': []
            }
        })
    
    @socketio.on('leave_dashboard')
    def handle_leave_dashboard():
        """Handle dashboard room leave"""
        leave_room('dashboard')
        emit('left', {'room': 'dashboard'})
