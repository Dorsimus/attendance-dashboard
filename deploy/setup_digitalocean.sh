#!/bin/bash

# DigitalOcean Droplet Setup Script for Attendance Dashboard
# Run this script on your fresh Ubuntu 22.04 droplet

set -e

echo "🚀 Starting DigitalOcean Droplet Setup for Attendance Dashboard"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🛠️  Installing essential packages..."
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "🐙 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
echo "👤 Adding user to docker group..."
sudo usermod -aG docker $USER

# Install Node.js (for potential future use)
echo "📱 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Install fail2ban for security
echo "🛡️  Installing fail2ban..."
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/attendance-dashboard
sudo chown $USER:$USER /opt/attendance-dashboard

# Clone the repository
echo "📥 Cloning attendance dashboard repository..."
cd /opt/attendance-dashboard
git clone https://github.com/Dorsimus/attendance-dashboard.git .

# Create data directories
echo "📊 Creating data directories..."
mkdir -p data logs uploads backups

# Set proper permissions
sudo chown -R $USER:$USER /opt/attendance-dashboard
chmod -R 755 /opt/attendance-dashboard

# Create environment file
echo "⚙️  Creating environment file..."
if [ ! -f backend/.env ]; then
    cp backend/.env.external backend/.env
    echo "✅ Environment file created. Please edit backend/.env with your settings."
fi

# Generate a secret key
echo "🔑 Generating secret key..."
SECRET_KEY=$(openssl rand -hex 32)
sed -i "s/your-super-secret-key-generate-a-new-one-for-production/$SECRET_KEY/" backend/.env

# Create systemd service for auto-start
echo "🔄 Creating systemd service..."
sudo tee /etc/systemd/system/attendance-dashboard.service > /dev/null <<EOF
[Unit]
Description=Attendance Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/attendance-dashboard/backend
ExecStart=/usr/local/bin/docker-compose -f docker-compose.external.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.external.yml down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable attendance-dashboard

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/attendance-dashboard > /dev/null <<EOF
/opt/attendance-dashboard/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Create backup script
echo "💾 Creating backup script..."
tee /opt/attendance-dashboard/backup.sh > /dev/null <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/attendance-dashboard/backups"

# Create backup directory
mkdir -p \$BACKUP_DIR

# Backup data directory
tar -czf \$BACKUP_DIR/data_backup_\$DATE.tar.gz -C /opt/attendance-dashboard/backend data/

# Backup Docker volumes
docker run --rm -v attendance_data:/data -v \$BACKUP_DIR:/backup alpine tar czf /backup/volumes_backup_\$DATE.tar.gz /data

# Clean old backups (keep 7 days)
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x /opt/attendance-dashboard/backup.sh

# Setup cron for daily backups
echo "⏰ Setting up daily backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/attendance-dashboard/backup.sh >> /opt/attendance-dashboard/logs/backup.log 2>&1") | crontab -

# Create monitoring script
echo "📊 Creating monitoring script..."
tee /opt/attendance-dashboard/monitor.sh > /dev/null <<EOF
#!/bin/bash
cd /opt/attendance-dashboard/backend

# Check if containers are running
if ! docker-compose -f docker-compose.external.yml ps | grep -q "Up"; then
    echo "⚠️  Containers are not running. Starting them..."
    docker-compose -f docker-compose.external.yml up -d
fi

# Check disk usage
DISK_USAGE=\$(df /opt/attendance-dashboard | tail -1 | awk '{print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 80 ]; then
    echo "⚠️  Disk usage is high: \$DISK_USAGE%"
fi

# Check container health
docker-compose -f docker-compose.external.yml ps
EOF

chmod +x /opt/attendance-dashboard/monitor.sh

# Setup monitoring cron (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/attendance-dashboard/monitor.sh >> /opt/attendance-dashboard/logs/monitor.log 2>&1") | crontab -

# Print completion message
echo ""
echo "🎉 DigitalOcean Droplet Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/attendance-dashboard/backend/.env with your settings"
echo "2. Update your domain DNS to point to this server IP"
echo "3. Start the services: cd /opt/attendance-dashboard/backend && docker-compose -f docker-compose.external.yml up -d"
echo "4. Check logs: docker-compose -f docker-compose.external.yml logs -f"
echo ""
echo "Your server IP: $(curl -s ifconfig.me)"
echo "Dashboard will be available at: https://attendance.redstoneintelligence.com"
echo ""
echo "Useful commands:"
echo "- Check status: docker-compose -f docker-compose.external.yml ps"
echo "- View logs: docker-compose -f docker-compose.external.yml logs -f"
echo "- Restart: docker-compose -f docker-compose.external.yml restart"
echo "- Update: git pull && docker-compose -f docker-compose.external.yml up -d --build"
echo ""
echo "🔐 IMPORTANT: Please reboot or run 'newgrp docker' to apply docker group changes!"
EOF
