# DigitalOcean Deployment Checklist

## Pre-Deployment Setup

### 1. DigitalOcean Account Setup
- [ ] DigitalOcean account created
- [ ] SSH key added to DigitalOcean account
- [ ] Payment method configured

### 2. Domain Configuration
- [ ] Domain `attendance.redstoneintelligence.com` ready
- [ ] DNS access available (to point to server IP)

### 3. Email Setup (for notifications)
- [ ] SMTP server details ready
- [ ] Email account for notifications configured

## Droplet Creation

### 1. Create Droplet
- [ ] Go to DigitalOcean dashboard
- [ ] Click "Create" → "Droplets"
- [ ] Select **Ubuntu 22.04 LTS**
- [ ] Choose **Basic plan**
- [ ] Select **$12/month** (2GB RAM, 1 vCPU, 50GB SSD)
- [ ] Choose datacenter region (closest to your users)
- [ ] Select your SSH key
- [ ] Name: `attendance-dashboard-prod`
- [ ] Create droplet

### 2. Initial Connection
- [ ] Connect via SSH: `ssh root@YOUR_DROPLET_IP`
- [ ] Update system: `apt update && apt upgrade -y`

## Automated Setup

### 1. Run Setup Script
```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/Dorsimus/attendance-dashboard/main/deploy/setup_digitalocean.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

### 2. Configuration
- [ ] Edit `/opt/attendance-dashboard/backend/.env`:
  - [ ] Set `LETSENCRYPT_EMAIL` to your email
  - [ ] Set `ADMIN_USERNAME` and `ADMIN_PASSWORD`
  - [ ] Set `MANAGER_USERNAME` and `MANAGER_PASSWORD`
  - [ ] Configure email settings if needed

## DNS Configuration

### 1. Point Domain to Server
- [ ] Get server IP: `curl ifconfig.me`
- [ ] Update DNS A record: `attendance.redstoneintelligence.com` → `YOUR_SERVER_IP`
- [ ] Wait for DNS propagation (5-30 minutes)

### 2. Test DNS
- [ ] Test: `nslookup attendance.redstoneintelligence.com`
- [ ] Should return your server IP

## Start Services

### 1. Start the Application
```bash
cd /opt/attendance-dashboard/backend
docker-compose -f docker-compose.external.yml up -d
```

### 2. Check Status
```bash
# Check container status
docker-compose -f docker-compose.external.yml ps

# Check logs
docker-compose -f docker-compose.external.yml logs -f
```

### 3. Monitor SSL Certificate
- [ ] Wait for SSL certificate generation (may take 1-2 minutes)
- [ ] Check Traefik logs: `docker-compose -f docker-compose.external.yml logs traefik`

## Testing

### 1. Access Dashboard
- [ ] Open browser: `https://attendance.redstoneintelligence.com`
- [ ] Should show dashboard (may show sample data initially)
- [ ] SSL certificate should be valid (green lock icon)

### 2. Test Admin Access
- [ ] Go to: `https://attendance.redstoneintelligence.com/admin/login`
- [ ] Login with admin credentials
- [ ] Test file upload functionality

### 3. Health Check
- [ ] Check health endpoint: `https://attendance.redstoneintelligence.com/health`
- [ ] Should return `{"status": "healthy"}`

## Data Sync Setup

### 1. Prepare Local Data Sync
- [ ] Update local sync script to use production server
- [ ] Set up secure data transfer method (SCP/SFTP/API)
- [ ] Test data sync from your local machine

### 2. Configure Sync (Choose one option)

#### Option A: API-Based Sync (Recommended)
- [ ] Use admin endpoints for data upload
- [ ] Set up automated script to POST data to server
- [ ] Configure authentication for API calls

#### Option B: Direct File Transfer
- [ ] Set up SCP/SFTP access
- [ ] Configure sync script to transfer files
- [ ] Set up cron job for regular sync

## Security & Monitoring

### 1. Security Check
- [ ] Firewall rules configured (ports 22, 80, 443 only)
- [ ] Fail2ban installed and running
- [ ] SSL certificates working
- [ ] Strong passwords set

### 2. Monitoring Setup
- [ ] Daily backups configured
- [ ] Log rotation set up
- [ ] Container health monitoring active
- [ ] Disk usage monitoring enabled

### 3. Optional: External Monitoring
- [ ] Set up UptimeRobot or similar for uptime monitoring
- [ ] Configure email alerts for downtime

## Post-Deployment

### 1. Documentation
- [ ] Update internal documentation with server details
- [ ] Share login credentials with team (securely)
- [ ] Document maintenance procedures

### 2. Backup Verification
- [ ] Verify backup script works: `/opt/attendance-dashboard/backup.sh`
- [ ] Check backup files created in `/opt/attendance-dashboard/backups/`

### 3. Performance Monitoring
- [ ] Monitor server resources (CPU, memory, disk)
- [ ] Check response times
- [ ] Monitor SSL certificate expiration

## Troubleshooting

### Common Issues
- **SSL Certificate Issues**: Check domain DNS, wait for propagation
- **Container Won't Start**: Check logs, verify environment variables
- **502 Bad Gateway**: Application container may be failing to start
- **Domain Not Accessible**: Check DNS configuration and firewall

### Useful Commands
```bash
# Check all containers
docker-compose -f docker-compose.external.yml ps

# View logs
docker-compose -f docker-compose.external.yml logs -f [service-name]

# Restart services
docker-compose -f docker-compose.external.yml restart

# Update application
cd /opt/attendance-dashboard
git pull
docker-compose -f docker-compose.external.yml up -d --build

# Check system resources
htop
df -h
```

## Success Criteria
- [ ] Dashboard accessible at `https://attendance.redstoneintelligence.com`
- [ ] SSL certificate valid and working
- [ ] Admin login functional
- [ ] File upload working
- [ ] Health check passing
- [ ] Monitoring and backups configured
- [ ] Data sync pipeline operational

## Emergency Contacts
- Server IP: `______________________`
- Admin Username: `__________________`
- SSH Key Location: `________________`
- Domain Registrar: `________________`

---

**Deployment Date**: ___________
**Deployed By**: _______________
**Server IP**: _________________
**Status**: ___________________
