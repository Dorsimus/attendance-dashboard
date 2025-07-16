# 🚀 Redstone Attendance Dashboard - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Redstone Attendance Dashboard to a production environment with SSL/HTTPS support.

## Prerequisites

### Server Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: Minimum 2GB, Recommended 4GB
- **Storage**: Minimum 10GB free space
- **Network**: Static IP address with ports 80 and 443 open

### Software Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Domain name pointing to your server's IP address

## Quick Start

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 2. Deploy Application

```bash
# Clone or copy your application files to the server
cd /opt/
sudo mkdir redstone-attendance
sudo chown $USER:$USER redstone-attendance
cd redstone-attendance

# Copy your application files here
# - docker-compose.prod.yml
# - .env.production
# - Dockerfile
# - All application code

# Update configuration
cp .env.production .env.prod
nano .env.prod  # Update domain, email, and credentials

# Make deployment script executable
chmod +x deploy.sh

# Deploy
./deploy.sh
```

## Configuration Details

### Environment Variables

Update `.env.prod` with your production values:

```env
# Domain Configuration
DOMAIN_NAME=attendance.yourdomain.com
LETSENCRYPT_EMAIL=your-email@domain.com

# Admin Credentials (CHANGE THESE!)
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_admin_password
MANAGER_USERNAME=your_manager_username  
MANAGER_PASSWORD=your_secure_manager_password

# Security
SECRET_KEY=your_secure_secret_key_here
SESSION_COOKIE_SECURE=True
CORS_ORIGINS=https://attendance.yourdomain.com
```

### Docker Compose Configuration

The production configuration includes:
- **Traefik**: Reverse proxy with automatic SSL certificates
- **Application**: Your attendance dashboard
- **Health Checks**: Automatic monitoring and restart
- **SSL**: Let's Encrypt certificates

### SSL Certificate Setup

SSL certificates are automatically managed by Let's Encrypt through Traefik:
- Certificates are automatically obtained and renewed
- HTTP traffic is redirected to HTTPS
- Certificates are stored in `./letsencrypt/`

## DNS Configuration

Point your domain to your server's IP address:

```
Type: A
Name: attendance (or your subdomain)
Value: YOUR_SERVER_IP_ADDRESS
TTL: 300
```

## Security Checklist

- [ ] Change default admin passwords
- [ ] Update SECRET_KEY
- [ ] Configure CORS_ORIGINS correctly
- [ ] Set up firewall (UFW recommended)
- [ ] Enable fail2ban
- [ ] Set up regular backups
- [ ] Monitor logs regularly

## Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

## Monitoring and Maintenance

### View Logs
```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f attendance-dashboard

# View Traefik logs
docker-compose -f docker-compose.prod.yml logs -f traefik

# View all logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Backup Data
```bash
# Create backup
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r data backups/$(date +%Y%m%d_%H%M%S)/
cp -r uploads backups/$(date +%Y%m%d_%H%M%S)/
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
   - Verify DNS is pointing to server
   - Check if ports 80/443 are open
   - Verify email address is correct

2. **Application Won't Start**
   - Check logs: `docker-compose -f docker-compose.prod.yml logs`
   - Verify environment variables
   - Check file permissions

3. **Database Connection Issues**
   - Verify data directory exists and has correct permissions
   - Check if data files are in correct location

### Health Check
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Test health endpoint
curl -f https://attendance.yourdomain.com/health
```

## Performance Optimization

### For Large Datasets
- Consider upgrading to PostgreSQL database
- Implement caching with Redis
- Use CDN for static assets
- Monitor resource usage

### Scaling
- Use Docker Swarm or Kubernetes for horizontal scaling
- Implement load balancing
- Set up database replication

## Backup Strategy

### Automated Backups
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/attendance-dashboard"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR/$DATE"
cp -r data "$BACKUP_DIR/$DATE/"
cp -r uploads "$BACKUP_DIR/$DATE/"
cp .env.prod "$BACKUP_DIR/$DATE/"
# Keep only last 7 days
find "$BACKUP_DIR" -type d -mtime +7 -exec rm -rf {} \;
EOF

# Make executable
chmod +x backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /opt/redstone-attendance/backup.sh" | crontab -
```

## Support and Maintenance

### Regular Tasks
- Monitor application logs
- Check SSL certificate expiry
- Update Docker images
- Backup data regularly
- Monitor server resources

### Security Updates
- Keep Docker updated
- Update base images regularly
- Monitor for security vulnerabilities
- Review access logs

## Contact Information

For support with this deployment:
- Application Issues: Check logs and troubleshooting guide
- Infrastructure Issues: Contact your system administrator
- Security Concerns: Review security checklist and update immediately

---

**Note**: This deployment guide is specifically configured for the Redstone Attendance Dashboard. Always test deployments in a staging environment before production.
