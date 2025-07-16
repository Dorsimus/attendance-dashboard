# PowerShell script to configure Windows Firewall for HTTPS remote access
# Run this script as Administrator

param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status
)

# Ensure we're running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Please run PowerShell as Administrator and try again."
    exit 1
}

Write-Host "Configuring Windows Firewall for Attendance Dashboard Remote Access" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

function Enable-FirewallRules {
    Write-Host "Enabling firewall rules for remote access..." -ForegroundColor Yellow
    
    # HTTP (port 80) - for Let's Encrypt challenge
    try {
        New-NetFirewallRule -DisplayName "Attendance Dashboard - HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow -ErrorAction Stop
        Write-Host "✅ HTTP (port 80) rule created successfully" -ForegroundColor Green
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Host "ℹ️  HTTP (port 80) rule already exists" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Error creating HTTP rule: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # HTTPS (port 443) - for secure dashboard access
    try {
        New-NetFirewallRule -DisplayName "Attendance Dashboard - HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow -ErrorAction Stop
        Write-Host "✅ HTTPS (port 443) rule created successfully" -ForegroundColor Green
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Host "ℹ️  HTTPS (port 443) rule already exists" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Error creating HTTPS rule: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Traefik Dashboard (port 8080) - optional, for admin access
    try {
        New-NetFirewallRule -DisplayName "Attendance Dashboard - Traefik Admin" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow -ErrorAction Stop
        Write-Host "✅ Traefik Dashboard (port 8080) rule created successfully" -ForegroundColor Green
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Host "ℹ️  Traefik Dashboard (port 8080) rule already exists" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Error creating Traefik Dashboard rule: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n✅ Firewall configuration completed!" -ForegroundColor Green
}

function Disable-FirewallRules {
    Write-Host "Disabling firewall rules..." -ForegroundColor Yellow
    
    $rules = @(
        "Attendance Dashboard - HTTP",
        "Attendance Dashboard - HTTPS", 
        "Attendance Dashboard - Traefik Admin"
    )
    
    foreach ($rule in $rules) {
        try {
            Remove-NetFirewallRule -DisplayName $rule -ErrorAction Stop
            Write-Host "✅ Removed rule: $rule" -ForegroundColor Green
        } catch {
            Write-Host "ℹ️  Rule not found: $rule" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n✅ Firewall rules disabled!" -ForegroundColor Green
}

function Show-FirewallStatus {
    Write-Host "Current Firewall Status:" -ForegroundColor Cyan
    Write-Host "=======================" -ForegroundColor Cyan
    
    $rules = @(
        @{Name="Attendance Dashboard - HTTP"; Port="80"},
        @{Name="Attendance Dashboard - HTTPS"; Port="443"},
        @{Name="Attendance Dashboard - Traefik Admin"; Port="8080"}
    )
    
    foreach ($rule in $rules) {
        try {
            $firewall_rule = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction Stop
            $status = if ($firewall_rule.Enabled -eq "True") { "✅ ENABLED" } else { "❌ DISABLED" }
            Write-Host "$($rule.Name) (Port $($rule.Port)): $status" -ForegroundColor White
        } catch {
            Write-Host "$($rule.Name) (Port $($rule.Port)): ❌ NOT FOUND" -ForegroundColor Red
        }
    }
    
    Write-Host "`nTesting port connectivity..." -ForegroundColor Cyan
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
}

function Show-NetworkInfo {
    Write-Host "`nNetwork Information:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    
    # Get IP addresses
    $ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -eq "Manual" -or $_.PrefixOrigin -eq "Dhcp" }
    
    foreach ($ip in $ipAddresses) {
        if ($ip.InterfaceAlias -notlike "*Loopback*") {
            Write-Host "$($ip.InterfaceAlias): $($ip.IPAddress)" -ForegroundColor White
        }
    }
    
    # Get public IP
    try {
        $publicIP = (Invoke-RestMethod -Uri "https://api.ipify.org?format=json").ip
        Write-Host "Public IP: $publicIP" -ForegroundColor Green
    } catch {
        Write-Host "Public IP: Unable to determine" -ForegroundColor Yellow
    }
    
    Write-Host "`nDomain Configuration:" -ForegroundColor Cyan
    Write-Host "Domain: attendance.redstoneintelligence.com" -ForegroundColor White
    Write-Host "Should point to: $publicIP" -ForegroundColor White
}

# Main script logic
if ($Enable) {
    Enable-FirewallRules
    Show-NetworkInfo
} elseif ($Disable) {
    Disable-FirewallRules
} elseif ($Status) {
    Show-FirewallStatus
    Show-NetworkInfo
} else {
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  .\setup_firewall.ps1 -Enable    # Enable firewall rules" -ForegroundColor White
    Write-Host "  .\setup_firewall.ps1 -Disable   # Disable firewall rules" -ForegroundColor White
    Write-Host "  .\setup_firewall.ps1 -Status    # Show current status" -ForegroundColor White
    Write-Host ""
    Write-Host "Run with -Enable to configure firewall for remote access" -ForegroundColor Yellow
}
