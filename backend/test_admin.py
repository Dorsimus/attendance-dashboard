from flask import Flask
from app.admin import admin_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

# Register the admin blueprint
app.register_blueprint(admin_bp)

@app.route('/')
def home():
    return '<h1>Test Server</h1><p><a href="/admin/login">Admin Login</a></p>'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
