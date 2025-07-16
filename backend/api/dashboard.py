from flask import Flask, jsonify, request
import json
import os
from datetime import datetime
import redis
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

# Initialize Redis connection for session/cache
redis_client = None
if os.getenv('UPSTASH_REDIS_REST_URL'):
    redis_client = redis.from_url(os.getenv('UPSTASH_REDIS_REST_URL'))

# Database connection
def get_db_connection():
    if os.getenv('DATABASE_URL'):
        url = urlparse(os.getenv('DATABASE_URL'))
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    return None

def get_cached_data(key):
    """Get data from cache (Redis or fallback)"""
    if redis_client:
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except:
            pass
    return None

def set_cached_data(key, data, expire=300):
    """Set data in cache (Redis or fallback)"""
    if redis_client:
        try:
            redis_client.setex(key, expire, json.dumps(data))
        except:
            pass

def get_dashboard_data():
    """Get dashboard data from database or cache"""
    # Check cache first
    cached_data = get_cached_data('dashboard_data')
    if cached_data:
        return cached_data
    
    # Get from database
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get attendance metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_employees,
                    COUNT(CASE WHEN status = 'Present' THEN 1 END) as present_count,
                    ROUND(AVG(CASE WHEN status = 'Present' THEN 100 ELSE 0 END), 1) as attendance_rate
                FROM attendance_records 
                WHERE date = CURRENT_DATE
            """)
            
            metrics = cursor.fetchone()
            
            # Get recent history
            cursor.execute("""
                SELECT date, 
                       COUNT(*) as total,
                       COUNT(CASE WHEN status = 'Present' THEN 1 END) as present
                FROM attendance_records 
                WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY date
                ORDER BY date DESC
                LIMIT 30
            """)
            
            history = cursor.fetchall()
            
            dashboard_data = {
                'metrics': {
                    'attendance_rate': metrics[2] if metrics else 0,
                    'present_count': metrics[1] if metrics else 0,
                    'total_employees': metrics[0] if metrics else 0,
                    'engagement_score': 78,  # Calculate this based on your logic
                    'week_over_week_change': 2.3  # Calculate this based on your logic
                },
                'attendance_history': {
                    'data': [{'date': str(row[0]), 'rate': round((row[2]/row[1])*100, 1)} for row in history],
                    'weeks': len(history) // 7,
                    'average_rate': sum([(row[2]/row[1])*100 for row in history]) / len(history) if history else 0,
                    'trend': 'stable'
                },
                'alerts': [],
                'regional_data': [],
                'at_risk_employees': [],
                'last_updated': datetime.now().isoformat(),
                'data_source': 'database'
            }
            
            # Cache the result
            set_cached_data('dashboard_data', dashboard_data, 300)  # 5 minutes
            return dashboard_data
            
        finally:
            conn.close()
    
    # Fallback to sample data
    return {
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
        'data_source': 'fallback'
    }

@app.route('/api/dashboard/data')
def dashboard_data():
    """API endpoint for complete dashboard data"""
    try:
        data = get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'metrics': {
                'attendance_rate': 0,
                'present_count': 0,
                'total_employees': 0,
                'engagement_score': 0,
                'week_over_week_change': 0
            },
            'alerts': [],
            'regional_data': [],
            'attendance_history': {'data': [], 'weeks': 0, 'average_rate': 0, 'trend': 'unknown'},
            'at_risk_employees': [],
            'last_updated': datetime.now().isoformat(),
            'data_source': 'error'
        }), 500

@app.route('/api/dashboard/metrics')
def dashboard_metrics():
    """Get current dashboard metrics"""
    try:
        data = get_dashboard_data()
        return jsonify({
            'success': True,
            'data': data['metrics'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# This is required for Vercel
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)
