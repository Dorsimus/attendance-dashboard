# External Hosting Deployment Guide

This guide covers deploying your attendance dashboard to external hosting providers.

## Hosting Provider Options

### 1. DigitalOcean Droplet (Recommended)
- **Cost**: $12-48/month
- **Specs**: 2GB-8GB RAM, 1-4 vCPUs
- **Benefits**: Simple, reliable, good documentation

### 2. AWS EC2
- **Cost**: $15-50/month (t3.small to t3.large)
- **Benefits**: Full AWS ecosystem, scalable
- **Drawbacks**: More complex setup

### 3. Google Cloud Platform
- **Cost**: Similar to AWS
- **Benefits**: Good container support, global network

### 4. Linode
- **Cost**: $10-40/month
- **Benefits**: Simple pricing, good performance

## Quick Setup Steps

### Step 1: Create Server
1. Create a new server/droplet with Ubuntu 22.04
2. Choose at least 2GB RAM for production
3. Set up SSH keys for secure access

### Step 2: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create app directory
mkdir -p /opt/attendance-dashboard
cd /opt/attendance-dashboard
```

### Step 3: Deploy Application
```bash
# Upload your code (use SCP, Git, or SFTP)
git clone https://github.com/your-username/attendance-dashboard.git .

# Copy environment file
cp .env.external .env

# Edit environment variables
nano .env

# Build and start services
docker-compose -f docker-compose.external.yml up -d
```

### Step 4: Configure DNS
Point your domain to the server's IP address:
- `attendance.redstoneintelligence.com` → `your-server-ip`

### Step 5: Security Setup
```bash
# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Set up fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Data Sync Solutions

### Option 1: API-Based Sync (Recommended)
Add these endpoints to your Flask app:

```python
@app.route('/api/sync/upload', methods=['POST'])
@require_auth
def sync_upload():
    # Secure file upload endpoint
    # Authenticate with API key
    pass
```

Then modify your local sync script to POST to this endpoint.

### Option 2: Cloud Storage Bridge
1. Set up AWS S3 or Google Cloud Storage
2. Local sync uploads to cloud storage
3. Server polls cloud storage for updates

### Option 3: VPN Connection
Set up a VPN tunnel between your office and cloud server.

## Monitoring Setup

### Health Checks
```bash
# Check service status
docker-compose -f docker-compose.external.yml ps

# View logs
docker-compose -f docker-compose.external.yml logs -f attendance-dashboard
```

### Automated Monitoring
Set up monitoring with:
- Uptime monitoring (UptimeRobot, Pingdom)
- Log monitoring (ELK stack or similar)
- Performance monitoring (New Relic, DataDog)

## Backup Strategy

### Database Backups
```bash
# Create backup script
cat > /opt/attendance-dashboard/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec attendance-dashboard_postgres_1 pg_dump -U attendance_user attendance_db > /opt/backups/db_backup_$DATE.sql
aws s3 cp /opt/backups/db_backup_$DATE.sql s3://your-backup-bucket/db-backups/
EOF

chmod +x /opt/attendance-dashboard/backup.sh

# Schedule with cron
echo "0 2 * * * /opt/attendance-dashboard/backup.sh" | crontab -
```

### Volume Backups
```bash
# Backup Docker volumes
docker run --rm -v attendance_data:/data -v /opt/backups:/backup alpine tar czf /backup/data_backup_$(date +%Y%m%d).tar.gz /data
```

## Security Considerations

### 1. SSL/TLS
- Let's Encrypt certificates (automatic with Traefik)
- Strong cipher suites
- HSTS headers

### 2. Authentication
- Strong passwords (use password manager)
- Consider 2FA for admin access
- Regular password rotation

### 3. Network Security
- Firewall rules (UFW)
- Rate limiting (Traefik middleware)
- DDoS protection (Cloudflare)

### 4. Application Security
- Input validation
- SQL injection prevention
- XSS protection
- CSRF tokens

## Performance Optimization

### 1. Caching
- Redis for session storage
- Application-level caching
- CDN for static assets

### 2. Database
- PostgreSQL for better performance
- Connection pooling
- Query optimization

### 3. Load Balancing
- Multiple app instances
- Traefik load balancing
- Health checks

## Maintenance

### Regular Updates
```bash
# Update containers
docker-compose -f docker-compose.external.yml pull
docker-compose -f docker-compose.external.yml up -d

# Update system
sudo apt update && sudo apt upgrade -y
```

### Log Rotation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/attendance-dashboard
```

## Troubleshooting

### Common Issues
1. **SSL Certificate Issues**: Check domain DNS, firewall rules
2. **Database Connection**: Verify PostgreSQL container health
3. **File Upload Issues**: Check volume permissions
4. **Performance**: Monitor resource usage

### Useful Commands
```bash
# Check container health
docker-compose -f docker-compose.external.yml ps

# View logs
docker-compose -f docker-compose.external.yml logs -f [service-name]

# Restart services
docker-compose -f docker-compose.external.yml restart

# Check disk usage
df -h
docker system df
```

## Cost Estimation

### Monthly Costs
- **Server**: $12-48/month
- **Domain**: $12/year
- **Backup Storage**: $5-15/month
- **Monitoring**: $0-20/month
- **Total**: ~$20-85/month

### Cost Optimization
- Use reserved instances for predictable workloads
- Implement auto-scaling
- Use spot instances for non-critical workloads
- Regular resource usage reviews

## Next Steps

1. Choose hosting provider
2. Set up server and domain
3. Deploy application
4. Configure monitoring
5. Set up backups
6. Implement data sync solution
7. Test thoroughly
8. Document procedures for your team

Would you like me to help you with any specific part of this deployment process?
