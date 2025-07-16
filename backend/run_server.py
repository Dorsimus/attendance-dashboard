from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.security import check_password_hash, generate_password_hash
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Admin credentials
ADMIN_USERS = {
    'admin': generate_password_hash('admin123'),
    'manager': generate_password_hash('manager123')
}

# === DASHBOARD ROUTES ===
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/dashboard/data')
def dashboard_data():
    """API endpoint for dashboard data"""
    return jsonify({
        'metrics': {
            'attendance_rate': 85.5,
            'present_count': 342,
            'total_employees': 400,
            'engagement_score': 78,
            'week_over_week_change': 2.3
        },
        'alerts': [
            {
                'id': '1',
                'title': 'Low Attendance Alert',
                'message': 'Sales department attendance below 80%',
                'severity': 'medium'
            }
        ],
        'regional_data': [
            {
                'manager_name': 'John Smith',
                'manager_title': 'Regional Manager',
                'region_name': 'North Region',
                'attendance_rate': 88.5,
                'manager_current_status': 'Present',
                'manager_personal_attendance': 95,
                'team_present_count': 42,
                'team_size': 50,
                'team_engagement_score': 82,
                'team_four_week_rate': 87,
                'team_at_risk_count': 2
            }
        ],
        'attendance_history': {
            'data': [
                {'date': '2025-07-01', 'attendance_rate': 82.3},
                {'date': '2025-07-02', 'attendance_rate': 84.1},
                {'date': '2025-07-03', 'attendance_rate': 83.8},
                {'date': '2025-07-04', 'attendance_rate': 85.2},
                {'date': '2025-07-05', 'attendance_rate': 85.5}
            ]
        },
        'at_risk_employees': [
            {
                'id': '1',
                'name': 'Jane Doe',
                'role': 'Sales Representative',
                'location': 'New York',
                'risk_score': 75,
                'four_week_rate': 65,
                'current_streak': 3
            }
        ]
    })

@app.route('/api/dashboard/available-dates')
def available_dates():
    """API endpoint for available dates"""
    return jsonify({
        'success': True,
        'dates': ['2025-07-10', '2025-07-09', '2025-07-08', '2025-07-05']
    })

@app.route('/api/dashboard/detailed-attendance/<date>')
def detailed_attendance(date):
    """API endpoint for detailed attendance by date"""
    return jsonify({
        'success': True,
        'data': {
            'date': date,
            'attendance_rate': 85.5,
            'detailed_attendees': [
                {
                    'name': 'John Smith',
                    'title': 'Manager',
                    'department': 'Sales',
                    'office': 'New York',
                    'status': 'Present',
                    'duration': '8h 15m',
                    'engagement_score': 85
                },
                {
                    'name': 'Jane Doe',
                    'title': 'Representative',
                    'department': 'Sales',
                    'office': 'New York',
                    'status': 'Partial',
                    'duration': '4h 30m',
                    'engagement_score': 65
                },
                {
                    'name': 'Bob Johnson',
                    'title': 'Analyst',
                    'department': 'Marketing',
                    'office': 'Boston',
                    'status': 'Absent',
                    'duration': '0h 0m',
                    'engagement_score': 0
                }
            ]
        }
    })

# === ADMIN ROUTES ===
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in ADMIN_USERS and check_password_hash(ADMIN_USERS[username], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/upload')
@admin_required
def admin_upload():
    return render_template('admin/upload.html')

@app.route('/admin/api/files')
@admin_required
def admin_files():
    return jsonify({
        'success': True,
        'files': [
            {
                'id': '1',
                'filename': 'people_hub_july.xlsx',
                'file_type': 'people_hub',
                'upload_time': datetime.now().isoformat(),
                'uploaded_by': session.get('admin_username'),
                'validation_info': {
                    'row_count': 755,
                    'columns': ['Name', 'Position', 'Department', 'Office']
                },
                'archived': False
            }
        ]
    })

# === WEBSOCKET EVENTS ===
@socketio.on('connect')
def handle_connect():
    print('Client connected to WebSocket')
    emit('status', {'msg': 'Connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from WebSocket')

@socketio.on('join_dashboard')
def handle_join_dashboard():
    print('Client joined dashboard')
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
            'attendance_history': {'data': []},
            'at_risk_employees': []
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Redstone Attendance Intelligence Platform...")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🔐 Admin Login: http://localhost:8000/admin/login")
    print("👤 Admin Credentials: admin / admin123")
    print("⚡ Press Ctrl+C to stop")
    
    try:
        socketio.run(app, debug=True, host='127.0.0.1', port=8000)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
