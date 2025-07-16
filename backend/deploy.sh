#!/bin/bash

# Redstone Attendance Dashboard - Production Deployment Script
# This script deploys the attendance dashboard to production

set -e  # Exit on any error

echo "🚀 Starting Redstone Attendance Dashboard Production Deployment"
echo "=================================================================="

# Configuration
DOMAIN_NAME="${DOMAIN_NAME:-attendance.yourdomain.com}"
SSL_EMAIL="${SSL_EMAIL:-your-email@domain.com}"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo "📋 Deployment Configuration:"
echo "   Domain: $DOMAIN_NAME"
echo "   SSL Email: $SSL_EMAIL"
echo "   Backup Directory: $BACKUP_DIR"
echo ""

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if required files exist
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found. Please create it from .env.production template."
    exit 1
fi

if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ docker-compose.prod.yml not found. Please ensure it exists."
    exit 1
fi

echo "✅ Pre-deployment checks passed"

# Create backup of current deployment
echo "💾 Creating backup of current deployment..."
mkdir -p "$BACKUP_DIR"
if [ -d "data" ]; then
    cp -r data "$BACKUP_DIR/"
    echo "✅ Data backed up to $BACKUP_DIR"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start new containers
echo "🏗️  Building and starting containers..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Running health checks..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.prod.yml exec -T attendance-dashboard curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Health check failed after $max_attempts attempts"
    echo "🔍 Checking logs..."
    docker-compose -f docker-compose.prod.yml logs attendance-dashboard
    exit 1
fi

# Final verification
echo "🔍 Final verification..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🎉 Redstone Attendance Dashboard is now running in production!"
    echo "=================================================================="
    echo "📊 Dashboard URL: https://$DOMAIN_NAME"
    echo "🔐 Admin URL: https://$DOMAIN_NAME/admin/login"
    echo "📋 Admin Username: admin"
    echo "📋 Manager Username: manager"
    echo ""
    echo "🔒 Security Note: Please change default admin passwords immediately!"
    echo "📖 View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "🛑 Stop services: docker-compose -f docker-compose.prod.yml down"
else
    echo "❌ Deployment failed. Checking logs..."
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi
