from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
def dashboard():
    """Render the main dashboard page"""
    return render_template('dashboard.html')
