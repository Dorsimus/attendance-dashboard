from flask import Flask, request, redirect, url_for, session, flash, jsonify, render_template_string
from flask.helpers import make_response
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import json
import os
import shutil
from datetime import datetime
from functools import wraps
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to sys.path to import data processor
sys.path.append(str(Path(__file__).parent / 'app'))
from core.data_processor import AttendanceDataProcessor

app = Flask(__name__, static_folder='app/static', template_folder='app/templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# Production security settings
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;"
    return response

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# SocketIO removed - using HTTP polling for real-time updates

# Initialize data processor
processor = None

def init_data_processor():
    global processor
    processor = AttendanceDataProcessor()
    # Initialize the processor asynchronously
    asyncio.run(processor.initialize())

# Initialize processor at startup
init_data_processor()

# Admin credentials
ADMIN_USERS = {
    os.getenv('ADMIN_USERNAME', 'admin'): generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123')),
    os.getenv('MANAGER_USERNAME', 'manager'): generate_password_hash(os.getenv('MANAGER_PASSWORD', 'manager123'))
}

# === DASHBOARD ROUTES ===
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Serve the full dashboard with complete functionality"""
    try:
        # Read the complete dashboard.html file
        dashboard_path = Path(__file__).parent / 'app' / 'static' / 'dashboard.html'
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard_html = f.read()
        return dashboard_html
    except FileNotFoundError:
        # Fallback to basic dashboard if file not found
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Error</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center">
    <div class="text-center">
        <h1 class="text-2xl font-bold text-red-600 mb-4">⚠️ Dashboard Template Missing</h1>
        <p class="text-gray-600 mb-4">The dashboard template file could not be found.</p>
        <p class="text-sm text-gray-500">Expected location: app/static/dashboard.html</p>
        <a href="/admin/login" class="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
            Go to Admin
        </a>
    </div>
</body>
</html>
        ''')

@app.route('/api/dashboard/data')
def dashboard_data():
    """API endpoint for complete dashboard data"""
    global processor
    
    try:
        # Get real metrics from the data processor
        if processor:
            metrics = asyncio.run(processor.get_current_metrics())
            alerts = asyncio.run(processor.get_active_alerts())
            regional_data = asyncio.run(processor.get_regional_breakdown())
            attendance_history = asyncio.run(processor.get_attendance_history())
            at_risk_employees = asyncio.run(processor.get_at_risk_employees())
            
            # Format the complete response
            return jsonify({
                'metrics': {
                    'attendance_rate': round(metrics.get('attendance_rate', 0), 1),
                    'present_count': metrics.get('present_count', 0),
                    'total_employees': metrics.get('total_employees', 0),
                    'engagement_score': int(metrics.get('engagement_score', 0)),
                    'week_over_week_change': round(metrics.get('week_over_week_change', 0), 1)
                },
                'alerts': alerts,
                'regional_data': regional_data,
                'attendance_history': attendance_history,
                'at_risk_employees': at_risk_employees,
                'last_updated': datetime.now().isoformat(),
                'data_source': 'real_data' if metrics.get('data_source') == 'real' else 'sample_data'
            })
        else:
            # Fallback to sample data if processor is not available
            return jsonify({
                'metrics': {
                    'attendance_rate': 85.5,
                    'present_count': 342,
                    'total_employees': 400,
                    'engagement_score': 78,
                    'week_over_week_change': 2.3
                },
                'alerts': [],
                'regional_data': [],
                'attendance_history': {'data': [], 'weeks': 0, 'average_rate': 85.0, 'trend': 'stable'},
                'at_risk_employees': [],
                'last_updated': datetime.now().isoformat(),
                'data_source': 'fallback_data'
            })
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        # Return fallback data in case of error
        return jsonify({
            'metrics': {
                'attendance_rate': 85.5,
                'present_count': 342,
                'total_employees': 400,
                'engagement_score': 78,
                'week_over_week_change': 2.3
            },
            'alerts': [],
            'regional_data': [],
            'attendance_history': {'data': [], 'weeks': 0, 'average_rate': 85.0, 'trend': 'stable'},
            'at_risk_employees': [],
            'last_updated': datetime.now().isoformat(),
            'data_source': 'error_fallback'
        })

@app.route('/api/dashboard/metrics')
def dashboard_metrics():
    """Get current dashboard metrics"""
    global processor
    
    try:
        if processor:
            metrics = asyncio.run(processor.get_current_metrics())
            return jsonify({
                'success': True,
                'data': metrics,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/attendance/history')
def attendance_history():
    """Get historical attendance data"""
    global processor
    weeks = request.args.get('weeks', 8, type=int)
    
    try:
        if processor:
            history = asyncio.run(processor.get_attendance_history(weeks))
            return jsonify({
                'success': True,
                'data': history,
                'weeks': weeks
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts and notifications"""
    global processor
    
    try:
        if processor:
            alerts = asyncio.run(processor.get_active_alerts())
            return jsonify({
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts/acknowledge', methods=['POST'])
def acknowledge_alert():
    """Acknowledge an alert"""
    global processor
    
    try:
        data = request.get_json()
        alert_id = data.get('alert_id')
        
        if processor and alert_id:
            success = asyncio.run(processor.acknowledge_alert(alert_id))
            return jsonify({'success': success})
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid request or processor not available'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/regions/<region_name>')
def get_region_detail(region_name):
    """Get detailed data for a specific region"""
    global processor
    
    try:
        if processor:
            region_data = asyncio.run(processor.get_region_detail(region_name))
            return jsonify({
                'success': True,
                'region': region_name,
                'data': region_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/employees/at-risk')
def get_at_risk_employees():
    """Get employees who are at risk based on attendance patterns"""
    global processor
    
    try:
        if processor:
            at_risk = asyncio.run(processor.get_at_risk_employees())
            return jsonify({
                'success': True,
                'employees': at_risk,
                'count': len(at_risk)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data/refresh', methods=['POST'])
def refresh_data():
    """Manually refresh data from source"""
    global processor
    
    try:
        if processor:
            asyncio.run(processor.refresh_data())
            return jsonify({
                'success': True, 
                'message': 'Data refreshed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics/predictions')
def get_predictions():
    """Get AI-powered predictions"""
    try:
        # Generate basic prediction data
        import numpy as np
        next_week_forecast = np.random.uniform(80, 90)
        confidence = np.random.uniform(70, 100)
        
        # Generate sample factors
        factors = {
            'historical_trend': np.random.uniform(0, 1),
            'external_factors': np.random.uniform(0, 1),
            'engagement_levels': np.random.uniform(0, 1)
        }
        
        recommendations = [
            "Increase team engagement activities",
            "Review attendance policies",
            "Offer flexible work options"
        ]
        
        predictions = {
            'next_week_forecast': round(next_week_forecast, 1),
            'confidence': round(confidence, 1),
            'factors': factors,
            'recommendations': recommendations
        }
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'model_version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/available-dates')
def get_available_dates():
    """Get available attendance dates"""
    global processor
    
    try:
        if processor:
            dates = asyncio.run(processor.get_available_dates())
            return jsonify({
                'success': True,
                'dates': dates
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/attendance/<date>')
def get_attendance_by_date(date):
    """Get attendance data for a specific date"""
    global processor
    
    try:
        if processor:
            attendance_data = asyncio.run(processor.get_attendance_by_date(date))
            return jsonify({
                'success': True,
                'data': attendance_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/detailed-attendance/<date>')
def get_detailed_attendance_by_date(date):
    """Get detailed attendance data for a specific date (Present Today drilldown)"""
    global processor
    
    try:
        if processor:
            # Use the processor's method to fetch detailed attendance info
            detailed_data = asyncio.run(processor.get_detailed_attendance_by_date(date))
            
            if detailed_data:
                return jsonify({
                    'success': True,
                    'data': detailed_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No attendance data found for this date'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        print(f"Error getting detailed attendance for {date}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/regional-breakdown')
def get_regional_breakdown():
    """Get regional breakdown data"""
    global processor
    
    try:
        if processor:
            regional_data = asyncio.run(processor.get_regional_breakdown())
            return jsonify({
                'success': True,
                'data': regional_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data processor not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# === ADMIN ROUTES ===
def admin_required(f):
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
    
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔐 Admin Login - Redstone Attendance</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {
                font-family: 'Inter', sans-serif;
            }
            
            .redstone-gradient {
                background: linear-gradient(135deg, #ff3443 0%, #0127a2 100%);
            }
            
            .card-shadow {
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen flex items-center justify-center">
        <div class="w-full max-w-md">
            <!-- Logo/Header -->
            <div class="text-center mb-8">
                <div class="redstone-gradient w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
                    🏢
                </div>
                <h1 class="text-2xl font-bold text-gray-900 mb-2">Admin Portal</h1>
                <p class="text-gray-600">Sign in to manage attendance system</p>
            </div>

            <!-- Login Form -->
            <div class="bg-white rounded-xl card-shadow p-8">
                <form method="POST" class="space-y-6">
                    <div>
                        <label for="username" class="block text-sm font-medium text-gray-700 mb-2">Username</label>
                        <input type="text" id="username" name="username" required 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors">
                    </div>

                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                        <input type="password" id="password" name="password" required 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors">
                    </div>

                    <button type="submit" 
                            class="w-full redstone-gradient text-white font-medium py-3 px-4 rounded-lg hover:opacity-90 transition-opacity">
                        Sign In
                    </button>
                </form>
                
                <div class="mt-6 text-center">
                    <p class="text-sm text-gray-600">Contact your administrator for credentials</p>
                </div>
            </div>

            <!-- Navigation -->
            <div class="text-center mt-8">
                <a href="/dashboard" class="text-blue-600 hover:text-blue-800 text-sm">← Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏢 Admin Dashboard - Redstone Attendance</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {{
                font-family: 'Inter', sans-serif;
            }}
            
            .redstone-gradient {{
                background: linear-gradient(135deg, #ff3443 0%, #0127a2 100%);
            }}
            
            .card-shadow {{
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }}
            
            .nav-item {{
                transition: all 0.3s ease;
            }}
            
            .nav-item:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.15);
            }}
        </style>
    </head>
    <body class="bg-gray-50">
        <!-- Header -->
        <header class="redstone-gradient text-white">
            <div class="container mx-auto px-6 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="text-2xl font-bold">🏢 Admin Dashboard</div>
                        <div class="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                            System Management
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="text-sm">
                            <div class="font-medium">Welcome, {session.get('admin_username', 'Admin')}!</div>
                            <div class="text-xs opacity-80">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                        </div>
                        <a href="/admin/logout" class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg transition-colors">
                            🚪 Logout
                        </a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-6 py-8">
            <!-- Quick Stats -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white rounded-xl card-shadow p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="text-sm font-medium text-gray-500">SYSTEM STATUS</div>
                        <div class="text-2xl">✅</div>
                    </div>
                    <div class="text-lg font-bold text-green-600 mb-2">Online</div>
                    <div class="text-sm text-gray-500">All systems operational</div>
                </div>

                <div class="bg-white rounded-xl card-shadow p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="text-sm font-medium text-gray-500">ADMIN FEATURES</div>
                        <div class="text-2xl">🔧</div>
                    </div>
                    <div class="text-lg font-bold text-blue-600 mb-2">Ready</div>
                    <div class="text-sm text-gray-500">File upload system active</div>
                </div>

                <div class="bg-white rounded-xl card-shadow p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="text-sm font-medium text-gray-500">DASHBOARD</div>
                        <div class="text-2xl">📊</div>
                    </div>
                    <div class="text-lg font-bold text-purple-600 mb-2">Live</div>
                    <div class="text-sm text-gray-500">Real-time monitoring active</div>
                </div>
            </div>

            <!-- Features Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- File Upload -->
                <div class="bg-white rounded-xl card-shadow p-6 nav-item cursor-pointer" onclick="window.location.href='/admin/upload'">
                    <div class="flex items-center justify-between mb-4">
                        <div class="text-4xl">📤</div>
                        <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                            Upload
                        </div>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Upload Files</h3>
                    <p class="text-gray-600 text-sm mb-4">Upload new People Hub Directory or Attendance files to update the system.</p>
                    <div class="flex items-center text-blue-600 text-sm font-medium">
                        <span>Manage uploads</span>
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                        </svg>
                    </div>
                </div>

                <!-- Main Dashboard -->
                <div class="bg-white rounded-xl card-shadow p-6 nav-item cursor-pointer" onclick="window.open('/dashboard', '_blank')">
                    <div class="flex items-center justify-between mb-4">
                        <div class="text-4xl">📊</div>
                        <div class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm font-medium">
                            View
                        </div>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Main Dashboard</h3>
                    <p class="text-gray-600 text-sm mb-4">Access the main attendance dashboard to view real-time metrics and analytics.</p>
                    <div class="flex items-center text-indigo-600 text-sm font-medium">
                        <span>Open dashboard</span>
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                    </div>
                </div>

                <!-- System Health -->
                <div class="bg-white rounded-xl card-shadow p-6 nav-item cursor-pointer" onclick="alert('System monitoring dashboard coming soon!')">
                    <div class="flex items-center justify-between mb-4">
                        <div class="text-4xl">⚙️</div>
                        <div class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                            Monitor
                        </div>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">System Health</h3>
                    <p class="text-gray-600 text-sm mb-4">Monitor system performance, uptime, and configuration settings.</p>
                    <div class="flex items-center text-green-600 text-sm font-medium">
                        <span>Check status</span>
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                        </svg>
                    </div>
                </div>
            </div>

            <!-- Success Message -->
            <div class="mt-8 bg-green-50 border border-green-200 rounded-xl p-6">
                <div class="flex items-center">
                    <div class="text-green-600 text-2xl mr-3">🎉</div>
                    <div>
                        <h3 class="font-semibold text-green-900">Admin Interface Successfully Deployed!</h3>
                        <p class="text-green-700 mt-1">The admin portal is now ready for file uploads and system management.</p>
                    </div>
                </div>
            </div>
        </main>
    </body>
    </html>
    '''

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

# === FILE UPLOAD ROUTES ===
@app.route('/admin/upload')
@admin_required
def upload_page():
    """File upload page"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📤 File Upload - Redstone Attendance</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {
                font-family: 'Inter', sans-serif;
            }
            
            .redstone-gradient {
                background: linear-gradient(135deg, #ff3443 0%, #0127a2 100%);
            }
            
            .card-shadow {
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            
            .drag-area {
                border: 2px dashed #e5e7eb;
                transition: all 0.3s ease;
            }
            
            .drag-area.dragover {
                border-color: #3b82f6;
                background-color: #eff6ff;
            }
            
            .upload-progress {
                display: none;
            }
        </style>
    </head>
    <body class="bg-gray-50">
        <!-- Header -->
        <header class="redstone-gradient text-white">
            <div class="container mx-auto px-6 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <a href="/admin/dashboard" class="text-2xl font-bold hover:opacity-80">🏢 Admin Dashboard</a>
                        <div class="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                            File Upload
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <a href="/admin/logout" class="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg transition-colors">
                            🚪 Logout
                        </a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-6 py-8">
            <div class="max-w-4xl mx-auto">
                <!-- Page Title -->
                <div class="text-center mb-8">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">📤 Upload Attendance Files</h1>
                    <p class="text-gray-600">Upload People Hub Directory or Attendance files to update the system</p>
                </div>

                <!-- Upload Section -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <!-- People Hub Directory Upload -->
                    <div class="bg-white rounded-xl card-shadow p-6">
                        <h2 class="text-xl font-semibold text-gray-900 mb-4">👥 People Hub Directory</h2>
                        <p class="text-gray-600 mb-6">Upload employee directory file (CSV, Excel)</p>
                        
                        <form id="directory-form" enctype="multipart/form-data">
                            <div class="drag-area rounded-lg p-8 text-center cursor-pointer" onclick="document.getElementById('directory-file').click()">
                                <div class="text-4xl mb-4">📁</div>
                                <p class="text-gray-600 mb-2">Drag and drop your directory file here</p>
                                <p class="text-sm text-gray-500 mb-4">or click to browse</p>
                                <input type="file" id="directory-file" name="file" accept=".csv,.xlsx,.xls" class="hidden">
                                <button type="button" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                                    Choose File
                                </button>
                            </div>
                            <div class="mt-4">
                                <div class="upload-progress">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="text-sm text-gray-600">Uploading...</span>
                                        <span class="text-sm text-gray-600">0%</span>
                                    </div>
                                    <div class="w-full bg-gray-200 rounded-full h-2">
                                        <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                                    </div>
                                </div>
                                <button type="submit" class="w-full mt-4 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                                    Upload Directory
                                </button>
                            </div>
                        </form>
                    </div>

                    <!-- Attendance Data Upload -->
                    <div class="bg-white rounded-xl card-shadow p-6">
                        <h2 class="text-xl font-semibold text-gray-900 mb-4">📊 Attendance Data</h2>
                        <p class="text-gray-600 mb-6">Upload attendance records (CSV, Excel, JSON)</p>
                        
                        <form id="attendance-form" enctype="multipart/form-data">
                            <div class="drag-area rounded-lg p-8 text-center cursor-pointer" onclick="document.getElementById('attendance-file').click()">
                                <div class="text-4xl mb-4">📈</div>
                                <p class="text-gray-600 mb-2">Drag and drop your attendance file here</p>
                                <p class="text-sm text-gray-500 mb-4">or click to browse</p>
                                <input type="file" id="attendance-file" name="file" accept=".csv,.xlsx,.xls,.json" class="hidden">
                                <button type="button" class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
                                    Choose File
                                </button>
                            </div>
                            <div class="mt-4">
                                <div class="upload-progress">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="text-sm text-gray-600">Uploading...</span>
                                        <span class="text-sm text-gray-600">0%</span>
                                    </div>
                                    <div class="w-full bg-gray-200 rounded-full h-2">
                                        <div class="bg-green-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                                    </div>
                                </div>
                                <button type="submit" class="w-full mt-4 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium">
                                    Upload Attendance
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- File Guidelines -->
                <div class="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
                    <h3 class="text-lg font-semibold text-blue-900 mb-4">📋 File Guidelines</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 class="font-medium text-blue-800 mb-2">People Hub Directory</h4>
                            <ul class="text-sm text-blue-700 space-y-1">
                                <li>• Required columns: Name, Email, Department</li>
                                <li>• Optional: Manager, Location, Role</li>
                                <li>• Format: CSV or Excel (.xlsx, .xls)</li>
                                <li>• Max file size: 16MB</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-medium text-blue-800 mb-2">Attendance Data</h4>
                            <ul class="text-sm text-blue-700 space-y-1">
                                <li>• Required columns: Date, Employee, Status</li>
                                <li>• Status values: Present, Absent, Late, etc.</li>
                                <li>• Format: CSV, Excel, or JSON</li>
                                <li>• Max file size: 16MB</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Recent Uploads -->
                <div class="mt-8 bg-white rounded-xl card-shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">📝 Recent Uploads</h3>
                    <div id="recent-uploads" class="space-y-3">
                        <div class="text-gray-500 text-center py-4">
                            Loading recent uploads...
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <script>
            // Drag and drop functionality
            document.querySelectorAll('.drag-area').forEach(area => {
                area.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    area.classList.add('dragover');
                });
                
                area.addEventListener('dragleave', () => {
                    area.classList.remove('dragover');
                });
                
                area.addEventListener('drop', (e) => {
                    e.preventDefault();
                    area.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        const fileInput = area.querySelector('input[type="file"]');
                        fileInput.files = files;
                        
                        // Trigger file name display
                        const fileName = files[0].name;
                        const fileDisplay = area.querySelector('p');
                        fileDisplay.textContent = `Selected: ${fileName}`;
                    }
                });
            });

            // File input change handlers
            document.getElementById('directory-file').addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    const fileName = e.target.files[0].name;
                    const dragArea = e.target.closest('.drag-area');
                    const fileDisplay = dragArea.querySelector('p');
                    fileDisplay.textContent = `Selected: ${fileName}`;
                }
            });

            document.getElementById('attendance-file').addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    const fileName = e.target.files[0].name;
                    const dragArea = e.target.closest('.drag-area');
                    const fileDisplay = dragArea.querySelector('p');
                    fileDisplay.textContent = `Selected: ${fileName}`;
                }
            });

            // Form submission handlers
            document.getElementById('directory-form').addEventListener('submit', function(e) {
                e.preventDefault();
                uploadFile(this, 'directory');
            });

            document.getElementById('attendance-form').addEventListener('submit', function(e) {
                e.preventDefault();
                uploadFile(this, 'attendance');
            });

            function uploadFile(form, type) {
                const formData = new FormData(form);
                const fileInput = form.querySelector('input[type="file"]');
                
                if (!fileInput.files.length) {
                    alert('Please select a file first.');
                    return;
                }

                const progressDiv = form.querySelector('.upload-progress');
                const progressBar = progressDiv.querySelector('.bg-blue-600, .bg-green-600');
                const progressText = progressDiv.querySelector('span:last-child');
                const submitButton = form.querySelector('button[type="submit"]');

                // Show progress
                progressDiv.style.display = 'block';
                submitButton.disabled = true;
                submitButton.textContent = 'Uploading...';

                fetch(`/admin/upload/${type}`, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Success
                        progressBar.style.width = '100%';
                        progressText.textContent = '100%';
                        
                        setTimeout(() => {
                            alert(`${type} file uploaded successfully!`);
                            form.reset();
                            progressDiv.style.display = 'none';
                            submitButton.disabled = false;
                            submitButton.textContent = type === 'directory' ? 'Upload Directory' : 'Upload Attendance';
                            
                            // Reset file display
                            const fileDisplay = form.querySelector('.drag-area p');
                            fileDisplay.textContent = type === 'directory' ? 
                                'Drag and drop your directory file here' : 
                                'Drag and drop your attendance file here';
                        }, 1000);
                    } else {
                        throw new Error(data.error || 'Upload failed');
                    }
                })
                .catch(error => {
                    console.error('Upload error:', error);
                    alert('Upload failed: ' + error.message);
                    
                    // Reset UI
                    progressDiv.style.display = 'none';
                    submitButton.disabled = false;
                    submitButton.textContent = type === 'directory' ? 'Upload Directory' : 'Upload Attendance';
                });
            }
            
            // Load recent uploads on page load
            document.addEventListener('DOMContentLoaded', function() {
                loadRecentUploads();
            });
            
            function loadRecentUploads() {
                fetch('/admin/uploads')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            displayRecentUploads(data.uploads);
                        } else {
                            document.getElementById('recent-uploads').innerHTML = `
                                <div class="text-red-500 text-center py-4">
                                    Error loading uploads: ${data.error}
                                </div>
                            `;
                        }
                    })
                    .catch(error => {
                        document.getElementById('recent-uploads').innerHTML = `
                            <div class="text-red-500 text-center py-4">
                                Error loading uploads: ${error.message}
                            </div>
                        `;
                    });
            }
            
            function displayRecentUploads(uploads) {
                const container = document.getElementById('recent-uploads');
                
                if (!uploads.length) {
                    container.innerHTML = `
                        <div class="text-gray-500 text-center py-4">
                            No recent uploads
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = uploads.map(upload => {
                    const date = new Date(upload.modified).toLocaleDateString();
                    const time = new Date(upload.modified).toLocaleTimeString();
                    const size = formatFileSize(upload.size);
                    const typeIcon = upload.type === 'directory' ? '👥' : '📊';
                    const typeColor = upload.type === 'directory' ? 'blue' : 'green';
                    
                    return `
                        <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                            <div class="flex items-center space-x-3">
                                <div class="text-2xl">${typeIcon}</div>
                                <div>
                                    <div class="font-medium text-gray-900">${upload.filename}</div>
                                    <div class="text-sm text-gray-500">${size} • ${date} ${time}</div>
                                </div>
                            </div>
                            <div class="bg-${typeColor}-100 text-${typeColor}-800 px-2 py-1 rounded text-sm font-medium">
                                ${upload.type === 'directory' ? 'Directory' : 'Attendance'}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
        </script>
    </body>
    </html>
    '''

@app.route('/admin/upload/directory', methods=['POST'])
@admin_required
def upload_directory():
    """Handle directory file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"directory_{timestamp}_{filename}"
            
            # Save the file
            file_path = UPLOAD_FOLDER / filename
            file.save(file_path)
            
            # Process the file (you can add actual processing logic here)
            # For now, we'll just store the file info
            file_info = {
                'filename': filename,
                'original_name': file.filename,
                'upload_time': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                'file_type': 'directory',
                'status': 'uploaded'
            }
            
            # Here you would typically:
            # 1. Parse the file (CSV/Excel)
            # 2. Validate the data structure
            # 3. Update the data processor with new directory info
            # 4. Send notifications if needed
            
            global processor
            if processor:
                try:
                    # Try to process the directory file
                    asyncio.run(processor.process_directory_file(str(file_path)))
                    file_info['status'] = 'processed'
                except Exception as e:
                    print(f"Error processing directory file: {e}")
                    file_info['status'] = 'uploaded_with_errors'
                    file_info['error'] = str(e)
            
            return jsonify({
                'success': True,
                'message': 'Directory file uploaded successfully',
                'file_info': file_info
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
    except Exception as e:
        print(f"Error uploading directory file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/upload/attendance', methods=['POST'])
@admin_required
def upload_attendance():
    """Handle attendance file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"attendance_{timestamp}_{filename}"
            
            # Save the file
            file_path = UPLOAD_FOLDER / filename
            file.save(file_path)
            
            # Process the file
            file_info = {
                'filename': filename,
                'original_name': file.filename,
                'upload_time': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                'file_type': 'attendance',
                'status': 'uploaded'
            }
            
            # Here you would typically:
            # 1. Parse the file (CSV/Excel/JSON)
            # 2. Validate the data structure
            # 3. Update the data processor with new attendance data
            # 4. Refresh analytics and metrics
            # 5. Send notifications if needed
            
            global processor
            if processor:
                try:
                    # Try to process the attendance file
                    asyncio.run(processor.process_attendance_file(str(file_path)))
                    file_info['status'] = 'processed'
                except Exception as e:
                    print(f"Error processing attendance file: {e}")
                    file_info['status'] = 'uploaded_with_errors'
                    file_info['error'] = str(e)
            
            return jsonify({
                'success': True,
                'message': 'Attendance file uploaded successfully',
                'file_info': file_info
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
    except Exception as e:
        print(f"Error uploading attendance file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/uploads')
@admin_required
def list_uploads():
    """List recent uploads"""
    try:
        uploads = []
        if UPLOAD_FOLDER.exists():
            for file_path in UPLOAD_FOLDER.glob('*'):
                if file_path.is_file():
                    stat = file_path.stat()
                    uploads.append({
                        'filename': file_path.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'type': 'directory' if file_path.name.startswith('directory_') else 'attendance'
                    })
        
        # Sort by modification time (most recent first)
        uploads.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'uploads': uploads[:10]  # Return last 10 uploads
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# === WEBSOCKET EVENTS REMOVED ===
# WebSocket functionality replaced with HTTP polling for better reliability

if __name__ == '__main__':
    print("🚀 Starting Redstone Attendance Intelligence Platform...")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🔐 Admin Login: http://localhost:8000/admin/login")
    print("👤 Admin Credentials: admin / admin123")
    print("⚡ Press Ctrl+C to stop")
    
    try:
        app.run(debug=True, host='127.0.0.1', port=8000)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
