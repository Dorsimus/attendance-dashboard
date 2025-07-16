#!/usr/bin/env python3
"""
Setup script for Redstone Attendance Intelligence Dashboard POC
Creates the full project structure and initial files
"""

import os
import json

def create_project_structure():
    """Create the full project structure"""
    
    # Define the project structure
    structure = {
        'backend': {
            'app': {
                '__init__.py': '',
                'main.py': '',
                'models.py': '',
                'database.py': '',
                'routers': {
                    '__init__.py': '',
                    'attendance.py': '',
                    'analytics.py': '',
                    'dashboard.py': ''
                },
                'core': {
                    '__init__.py': '',
                    'config.py': '',
                    'data_processor.py': '',
                    'analytics_engine.py': ''
                },
                'static': {},
                'templates': {}
            },
            'requirements.txt': '',
            'Dockerfile': '',
            '.env.example': ''
        },
        'frontend': {
            'public': {
                'index.html': '',
                'favicon.ico': '',
                'manifest.json': ''
            },
            'src': {
                'components': {
                    'Dashboard': {},
                    'Charts': {},
                    'Metrics': {},
                    'Alerts': {}
                },
                'pages': {},
                'hooks': {},
                'utils': {},
                'styles': {},
                'types': {}
            },
            'package.json': '',
            'tailwind.config.js': '',
            'next.config.js': ''
        },
        'data': {
            'sample': {},
            'processed': {},
            'exports': {}
        },
        'docs': {},
        'scripts': {},
        'README.md': '',
        'docker-compose.yml': ''
    }
    
    def create_structure(base_path, structure_dict):
        """Recursively create directory structure"""
        for name, content in structure_dict.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                # It's a directory
                os.makedirs(path, exist_ok=True)
                create_structure(path, content)
            else:
                # It's a file
                with open(path, 'w') as f:
                    f.write(content)
    
    create_structure('.', structure)
    print("✅ Project structure created successfully!")

if __name__ == "__main__":
    create_project_structure()
