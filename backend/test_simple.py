from flask import Flask
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>🚀 Server is Running!</h1>
    <p>This confirms the server is working on port 8000.</p>
    <p><a href="/admin/login">Try Admin Login</a></p>
    '''

@app.route('/admin/login')
def admin_login():
    return '''
    <h1>🔐 Admin Login</h1>
    <form method="POST" action="/admin/login">
        <p><input type="text" name="username" placeholder="Username" style="padding: 10px; margin: 5px;"></p>
        <p><input type="password" name="password" placeholder="Password" style="padding: 10px; margin: 5px;"></p>
        <p><button type="submit" style="padding: 10px 20px; background: #007cba; color: white; border: none;">Login</button></p>
    </form>
    <p><small>Test credentials: admin / admin123</small></p>
    '''

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    return '<h1>✅ Login Form Submitted!</h1><p>Admin interface would process login here.</p>'

if __name__ == '__main__':
    print("🚀 Starting test server on port 8000...")
    print("🌐 Open: http://localhost:8000")
    print("🔐 Admin: http://localhost:8000/admin/login")
    print("⚡ Press Ctrl+C to stop")
    
    try:
        app.run(debug=False, host='127.0.0.1', port=8000, threaded=True)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
