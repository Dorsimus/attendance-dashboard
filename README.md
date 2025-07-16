# Attendance Dashboard

A real-time attendance tracking and analytics dashboard built with Flask, Docker, and modern web technologies.

## Features

- **Real-time Dashboard**: Live attendance metrics and analytics
- **File Upload Management**: Admin interface for uploading attendance and directory files
- **Data Sync Pipeline**: Automated synchronization of attendance data
- **Responsive Design**: Modern, mobile-friendly interface
- **Docker Deployment**: Containerized for easy deployment
- **SSL/HTTPS**: Automatic SSL certificate management with Traefik
- **Monitoring**: Health checks and metrics collection

## Architecture

- **Backend**: Flask (Python) with Gunicorn
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS
- **Database**: File-based (JSON/CSV) with optional PostgreSQL support
- **Reverse Proxy**: Traefik with automatic SSL
- **Deployment**: Docker Compose
- **Monitoring**: Built-in health checks and metrics

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Domain name (for production deployment)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/Dorsimus/attendance-dashboard.git
cd attendance-dashboard
```

2. Set up environment variables:
```bash
cp backend/.env.external backend/.env
# Edit backend/.env with your configuration
```

3. Start the development environment:
```bash
cd backend
docker-compose up -d
```

4. Access the dashboard at `http://localhost:8000`

### Production Deployment

See [EXTERNAL_HOSTING_GUIDE.md](backend/EXTERNAL_HOSTING_GUIDE.md) for detailed deployment instructions.

## Configuration

### Environment Variables

Key environment variables (see `.env.external` for full list):

- `SECRET_KEY`: Flask secret key for sessions
- `ADMIN_USERNAME/ADMIN_PASSWORD`: Admin login credentials
- `MANAGER_USERNAME/MANAGER_PASSWORD`: Manager login credentials
- `LETSENCRYPT_EMAIL`: Email for SSL certificate generation

### Data Sync

The system includes an automated data sync pipeline:

- **Source**: Local attendance tracking files
- **Target**: Dashboard data directory
- **Frequency**: Configurable (default: 30 minutes)
- **Monitoring**: Built-in metrics and email notifications

## API Endpoints

- `GET /api/dashboard/data` - Complete dashboard data
- `GET /api/dashboard/metrics` - Current attendance metrics
- `GET /api/attendance/history` - Historical attendance data
- `POST /admin/upload/directory` - Upload employee directory
- `POST /admin/upload/attendance` - Upload attendance data

## Data Structure

### Attendance Data Format
```json
{
  "2024-01-15": {
    "employee@company.com": {
      "name": "John Doe",
      "status": "Present",
      "duration": "8.5",
      "engagement_score": 85
    }
  }
}
```

### Employee Directory Format
```csv
name,email,title,department,office,manager
John Doe,john.doe@company.com,Developer,IT,New York,Jane Smith
```

## Security

- **Authentication**: Session-based admin authentication
- **HTTPS**: Automatic SSL certificate management
- **Security Headers**: CSP, HSTS, and other security headers
- **Input Validation**: File upload validation and sanitization
- **Access Control**: Role-based access for admin functions

## Monitoring

- **Health Checks**: Docker container health monitoring
- **Metrics**: Attendance rates, engagement scores, trends
- **Alerts**: Configurable alerts for attendance issues
- **Logging**: Comprehensive logging with rotation

## Development

### Project Structure
```
attendance-dashboard/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── data_processor.py
│   │   ├── static/
│   │   │   └── dashboard.html
│   │   └── templates/
│   ├── scripts/
│   │   ├── sync_data.py
│   │   └── sync_config.py
│   ├── dashboard_server.py
│   ├── Dockerfile
│   └── docker-compose*.yml
├── README.md
└── .gitignore
```

### Running Tests
```bash
# TODO: Add test suite
python -m pytest tests/
```

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions and classes
- Use type hints where appropriate

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software for Redstone Intelligence.

## Support

For support, please contact the development team or create an issue in the GitHub repository.

## Changelog

### v1.0.0
- Initial release
- Real-time dashboard
- File upload management
- Data sync pipeline
- Docker deployment
- SSL support
