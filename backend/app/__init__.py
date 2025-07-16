from flask import Flask
from flask_socketio import SocketIO
from .routes import main_bp
from .admin import admin_bp
from .websocket import register_socketio_events

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Register WebSocket events
    register_socketio_events(socketio)
    
    return app, socketio
