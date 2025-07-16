from flask import Flask, request, render_template, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key-123'

# Simple admin credentials
ADMIN_USERS = {
    'admin': generate_password_hash('admin123'),
    'manager': generate_password_hash('manager123')
}

@app.route('/')
def home():
    return '<h1>Admin Test Server</h1><p><a href="/admin/login">Admin Login</a></p>'

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
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 400px; margin: 0 auto; }
            input { width: 100%; padding: 10px; margin: 10px 0; }
            button { width: 100%; padding: 10px; background: #007cba; color: white; border: none; }
            .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .alert-error { background: #ffebee; color: #c62828; }
            .alert-success { background: #e8f5e8; color: #2e7d32; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Admin Login</h2>
            {% for category, message in get_flashed_messages(with_categories=true) %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p><small>Default: admin / admin123</small></p>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #007cba; color: white; padding: 20px; margin-bottom: 20px; }}
            .card {{ border: 1px solid #ddd; padding: 20px; margin: 10px 0; }}
            button {{ padding: 10px 20px; margin: 10px 0; background: #007cba; color: white; border: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Admin Dashboard</h1>
            <p>Welcome, {session.get('admin_username', 'Admin')}!</p>
        </div>
        
        <div class="card">
            <h3>✅ Admin Interface Working!</h3>
            <p>The admin authentication is working correctly.</p>
            <p>You can now access the admin features.</p>
        </div>
        
        <div class="card">
            <h3>📤 File Upload</h3>
            <p>Upload People Hub Directory or Attendance files.</p>
            <button onclick="alert('Upload functionality ready!')">Upload Files</button>
        </div>
        
        <div class="card">
            <h3>📊 System Status</h3>
            <p>System is running normally.</p>
            <p>Ready to process files.</p>
        </div>
        
        <p><a href="/admin/logout">Logout</a></p>
    </body>
    </html>
    '''

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    print("🚀 Starting Simple Admin Server...")
    print("🔐 Admin Login: http://localhost:8000/admin/login")
    print("👤 Credentials: admin / admin123")
    print("⚡ Press Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=8000)
