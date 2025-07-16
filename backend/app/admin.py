from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
from datetime import datetime
import uuid
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

# Simple admin credentials (in production, use a proper database)
ADMIN_USERS = {
    'admin': generate_password_hash('admin123'),  # Change this password!
    'manager': generate_password_hash('manager123')
}

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def ensure_upload_folder():
    """Ensure upload folder exists"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'people_hub'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'attendance'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'archive'), exist_ok=True)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in ADMIN_USERS and check_password_hash(ADMIN_USERS[username], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@admin_required
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/upload')
@admin_required
def upload_page():
    return render_template('admin/upload.html')

@admin_bp.route('/api/upload', methods=['POST'])
@admin_required
def upload_file():
    try:
        ensure_upload_folder()
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type')  # 'people_hub' or 'attendance'
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        if file_type not in ['people_hub', 'attendance']:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file
        file_path = os.path.join(UPLOAD_FOLDER, file_type, unique_filename)
        file.save(file_path)
        
        # Validate file content
        validation_result = validate_file_content(file_path, file_type)
        
        if not validation_result['valid']:
            # Remove invalid file
            os.remove(file_path)
            return jsonify({
                'success': False, 
                'error': f'File validation failed: {validation_result["error"]}'
            }), 400
        
        # Save file metadata
        metadata = {
            'id': str(uuid.uuid4()),
            'filename': filename,
            'unique_filename': unique_filename,
            'file_type': file_type,
            'upload_time': datetime.now().isoformat(),
            'uploaded_by': session.get('admin_username'),
            'file_size': os.path.getsize(file_path),
            'validation_info': validation_result['info']
        }
        
        save_file_metadata(metadata)
        
        return jsonify({
            'success': True,
            'file_id': metadata['id'],
            'filename': filename,
            'validation_info': validation_result['info']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/files')
@admin_required
def list_files():
    try:
        metadata_file = os.path.join(UPLOAD_FOLDER, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                files = json.load(f)
        else:
            files = []
        
        # Sort by upload time (newest first)
        files.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return jsonify({'success': True, 'files': files})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/process/<file_id>', methods=['POST'])
@admin_required
def process_file(file_id):
    try:
        # Get file metadata
        metadata_file = os.path.join(UPLOAD_FOLDER, 'metadata.json')
        if not os.path.exists(metadata_file):
            return jsonify({'success': False, 'error': 'No files found'}), 404
        
        with open(metadata_file, 'r') as f:
            files = json.load(f)
        
        file_metadata = next((f for f in files if f['id'] == file_id), None)
        if not file_metadata:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Process the file based on type
        file_path = os.path.join(UPLOAD_FOLDER, file_metadata['file_type'], file_metadata['unique_filename'])
        
        if file_metadata['file_type'] == 'people_hub':
            result = process_people_hub_file(file_path)
        else:
            result = process_attendance_file(file_path)
        
        if result['success']:
            # Archive current file and update metadata
            archive_file(file_metadata, file_path)
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def validate_file_content(file_path, file_type):
    """Validate uploaded file content"""
    try:
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        
        if file_type == 'people_hub':
            required_columns = ['Name', 'Position', 'Department', 'Office']  # Adjust based on your actual columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'valid': False,
                    'error': f'Missing required columns: {", ".join(missing_columns)}'
                }
        
        elif file_type == 'attendance':
            # Basic validation for attendance file
            if df.empty:
                return {
                    'valid': False,
                    'error': 'Attendance file is empty'
                }
        
        return {
            'valid': True,
            'info': {
                'row_count': len(df),
                'columns': list(df.columns),
                'sample_data': df.head(3).to_dict('records')
            }
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Error reading file: {str(e)}'
        }

def save_file_metadata(metadata):
    """Save file metadata to JSON file"""
    metadata_file = os.path.join(UPLOAD_FOLDER, 'metadata.json')
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            files = json.load(f)
    else:
        files = []
    
    files.append(metadata)
    
    with open(metadata_file, 'w') as f:
        json.dump(files, f, indent=2)

def process_people_hub_file(file_path):
    """Process people hub file and update system"""
    try:
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        
        # Here you would update your main data processing logic
        # For now, just return success with basic info
        
        return {
            'success': True,
            'message': f'Successfully processed people hub file with {len(df)} records',
            'processed_count': len(df)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing people hub file: {str(e)}'
        }

def process_attendance_file(file_path):
    """Process attendance file and update system"""
    try:
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        
        # Here you would update your main data processing logic
        # For now, just return success with basic info
        
        return {
            'success': True,
            'message': f'Successfully processed attendance file with {len(df)} records',
            'processed_count': len(df)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing attendance file: {str(e)}'
        }

def archive_file(metadata, file_path):
    """Archive processed file"""
    try:
        archive_path = os.path.join(UPLOAD_FOLDER, 'archive', metadata['unique_filename'])
        os.rename(file_path, archive_path)
        
        # Update metadata
        metadata['archived'] = True
        metadata['archive_time'] = datetime.now().isoformat()
        metadata['archive_path'] = archive_path
        
        # Save updated metadata
        metadata_file = os.path.join(UPLOAD_FOLDER, 'metadata.json')
        with open(metadata_file, 'r') as f:
            files = json.load(f)
        
        # Update the specific file metadata
        for i, file_meta in enumerate(files):
            if file_meta['id'] == metadata['id']:
                files[i] = metadata
                break
        
        with open(metadata_file, 'w') as f:
            json.dump(files, f, indent=2)
            
    except Exception as e:
        print(f"Error archiving file: {e}")
