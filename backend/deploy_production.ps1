# Production deployment script for Attendance Dashboard with HTTPS
# This script sets up the dashboard with SSL certificates and remote access

param(
    [switch]$Deploy,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Logs
)

Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  ATTENDANCE DASHBOARD PRODUCTION DEPLOYMENT" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    # Check if Docker is running
    try {
        docker --version | Out-Null
        Write-Host "✅ Docker is installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
        return $false
    }
    
    # Check if Docker Compose is available
    try {
        docker-compose --version | Out-Null
        Write-Host "✅ Docker Compose is available" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker Compose is not available" -ForegroundColor Red
        return $false
    }
    
    # Check if production config exists
    if (Test-Path "docker-compose.production.yml") {
        Write-Host "✅ Production configuration found" -ForegroundColor Green
    } else {
        Write-Host "❌ Production configuration not found" -ForegroundColor Red
        return $false
    }
    
    # Check if .env.production exists
    if (Test-Path ".env.production") {
        Write-Host "✅ Production environment file found" -ForegroundColor Green
    } else {
        Write-Host "❌ Production environment file not found" -ForegroundColor Red
        return $false
    }
    
    return $true
}

function Deploy-Production {
    Write-Host "Starting production deployment..." -ForegroundColor Yellow
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Host "❌ Prerequisites not met. Deployment aborted." -ForegroundColor Red
        return
    }
    
    # Stop current development containers
    Write-Host "Stopping development containers..." -ForegroundColor Yellow
    docker-compose down 2>$null
    
    # Create necessary directories
    Write-Host "Creating necessary directories..." -ForegroundColor Yellow
    if (-not (Test-Path "letsencrypt")) {
        New-Item -ItemType Directory -Path "letsencrypt" -Force
        Write-Host "✅ Created letsencrypt directory" -ForegroundColor Green
    }
    
    if (-not (Test-Path "traefik-logs")) {
        New-Item -ItemType Directory -Path "traefik-logs" -Force
        Write-Host "✅ Created traefik-logs directory" -ForegroundColor Green
    }
    
    # Build and deploy production containers
    Write-Host "Building and deploying production containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Production deployment successful!" -ForegroundColor Green
        
        # Wait for containers to be ready
        Write-Host "Waiting for containers to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Show deployment status
        Show-DeploymentStatus
        
        # Show next steps
        Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Verify DNS: attendance.redstoneintelligence.com → 97.75.162.142" -ForegroundColor White
        Write-Host "2. Wait 2-3 minutes for SSL certificate generation" -ForegroundColor White
        Write-Host "3. Test HTTPS access: https://attendance.redstoneintelligence.com" -ForegroundColor White
        Write-Host "4. Configure firewall if needed (run setup_firewall.ps1 -Enable as Admin)" -ForegroundColor White
        
    } else {
        Write-Host "❌ Production deployment failed!" -ForegroundColor Red
    }
}

function Stop-Production {
    Write-Host "Stopping production deployment..." -ForegroundColor Yellow
    docker-compose -f docker-compose.production.yml down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Production deployment stopped!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to stop production deployment!" -ForegroundColor Red
    }
}

function Show-DeploymentStatus {
    Write-Host "`nDeployment Status:" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    
    # Show container status
    Write-Host "Container Status:" -ForegroundColor White
    docker-compose -f docker-compose.production.yml ps
    
    # Show network information
    Write-Host "`nNetwork Information:" -ForegroundColor White
    Write-Host "Local IP: 10.100.1.187" -ForegroundColor White
    Write-Host "Public IP: 97.75.162.142" -ForegroundColor White
    Write-Host "Domain: attendance.redstoneintelligence.com" -ForegroundColor White
    
    # Test local connectivity
    Write-Host "`nConnectivity Tests:" -ForegroundColor White
    $ports = @(80, 443, 8080)
    foreach ($port in $ports) {
        try {
            $result = Test-NetConnection -ComputerName "localhost" -Port $port -WarningAction SilentlyContinue
            $status = if ($result.TcpTestSucceeded) { "✅ OPEN" } else { "❌ CLOSED" }
            Write-Host "Port $port`: $status" -ForegroundColor White
        } catch {
            Write-Host "Port $port`: ❌ ERROR" -ForegroundColor Red
        }
    }
    
    # Show URLs
    Write-Host "`nAccess URLs:" -ForegroundColor White
    Write-Host "Dashboard: https://attendance.redstoneintelligence.com" -ForegroundColor Green
    Write-Host "Traefik Admin: http://10.100.1.187:8080" -ForegroundColor Yellow
    Write-Host "Local Access: http://10.100.1.187:8000" -ForegroundColor Yellow
}

function Show-Logs {
    Write-Host "Showing production logs (Press Ctrl+C to exit)..." -ForegroundColor Yellow
    docker-compose -f docker-compose.production.yml logs -f
}

function Show-Usage {
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  .\\deploy_production.ps1 -Deploy   # Deploy production setup" -ForegroundColor White
    Write-Host "  .\\deploy_production.ps1 -Stop     # Stop production setup" -ForegroundColor White
    Write-Host "  .\\deploy_production.ps1 -Status   # Show deployment status" -ForegroundColor White
    Write-Host "  .\\deploy_production.ps1 -Logs     # Show production logs" -ForegroundColor White
    Write-Host ""
    Write-Host "Example: .\\deploy_production.ps1 -Deploy" -ForegroundColor Yellow
}

# Main script logic
if ($Deploy) {
    Deploy-Production
} elseif ($Stop) {
    Stop-Production
} elseif ($Status) {
    Show-DeploymentStatus
} elseif ($Logs) {
    Show-Logs
} else {
    Show-Usage
}
