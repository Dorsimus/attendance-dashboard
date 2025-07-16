# 🔐 HTTPS and Remote Access Setup Guide

## ✅ Current Status
- **Domain:** `attendance.redstoneintelligence.com`
- **DNS:** ✅ Correctly pointing to `97.75.162.142`
- **Local IP:** `10.100.1.187`
- **Public IP:** `97.75.162.142`

## 🚀 Step-by-Step Setup

### **Step 1: Configure Windows Firewall (REQUIRED)**

**⚠️ Run as Administrator:**
```powershell
# Open PowerShell as Administrator, then run:
.\setup_firewall.ps1 -Enable
```

**Manual Firewall Setup (if PowerShell script fails):**
1. **Open Windows Firewall with Advanced Security**
2. **Create Inbound Rules:**
   - **HTTP (Port 80):** For Let's Encrypt certificate validation
   - **HTTPS (Port 443):** For secure dashboard access
   - **Port 8080:** For Traefik admin dashboard (optional)

### **Step 2: Deploy Production Configuration**

**Run the deployment script:**
```powershell
.\deploy_production.ps1 -Deploy
```

**Manual deployment (if script fails):**
```powershell
# Stop development containers
docker-compose down

# Create directories
mkdir letsencrypt
mkdir traefik-logs

# Deploy production setup
docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build
```

### **Step 3: Verify DNS Propagation**

**Check DNS resolution:**
```powershell
nslookup attendance.redstoneintelligence.com
```

**Expected result:**
```
Name:    attendance.redstoneintelligence.com
Address: 97.75.162.142
```

### **Step 4: Wait for SSL Certificate Generation**

**Let's Encrypt will automatically generate SSL certificates:**
- **Time required:** 2-3 minutes after deployment
- **Verification:** Check Traefik logs for certificate generation
- **Manual check:** `docker-compose -f docker-compose.production.yml logs traefik`

### **Step 5: Test Access**

**Internal Access:**
- **HTTP:** `http://10.100.1.187:8000`
- **HTTPS:** `https://attendance.redstoneintelligence.com`

**External Access:**
- **HTTPS:** `https://attendance.redstoneintelligence.com`
- **HTTP:** Should automatically redirect to HTTPS

## 🔧 Router Configuration (If Behind NAT)

**If your server is behind a router, configure port forwarding:**
1. **Access your router's admin panel**
2. **Port forwarding rules:**
   - **Port 80** → `10.100.1.187:80`
   - **Port 443** → `10.100.1.187:443`
   - **Port 8080** → `10.100.1.187:8080` (optional)

## 🛡️ Security Features

### **Automatic HTTPS:**
- **SSL/TLS certificates** from Let's Encrypt
- **Automatic renewal** every 90 days
- **HTTP to HTTPS redirect** for all traffic
- **HSTS headers** for enhanced security

### **Additional Security:**
- **Secure session cookies**
- **CSRF protection**
- **XSS protection headers**
- **Content Security Policy**
- **Rate limiting** (configurable)

## 📊 Monitoring and Management

### **Check Deployment Status:**
```powershell
.\deploy_production.ps1 -Status
```

### **View Logs:**
```powershell
.\deploy_production.ps1 -Logs
```

### **Container Management:**
```powershell
# Check container status
docker-compose -f docker-compose.production.yml ps

# Restart services
docker-compose -f docker-compose.production.yml restart

# Stop production deployment
.\deploy_production.ps1 -Stop
```

## 🌐 Access Information

### **Executive Access:**
- **URL:** `https://attendance.redstoneintelligence.com`
- **Username:** `admin`
- **Password:** `RedstoneAttendance2025!SecureAdmin`

### **Manager Access:**
- **URL:** `https://attendance.redstoneintelligence.com`
- **Username:** `manager`
- **Password:** `RedstoneAttendance2025!SecureManager`

### **Admin Dashboard:**
- **Traefik Admin:** `http://10.100.1.187:8080`
- **Local Dashboard:** `http://10.100.1.187:8000`

## 🔍 Troubleshooting

### **Common Issues:**

1. **DNS not resolving:**
   - Wait 5-10 minutes for DNS propagation
   - Check with your DNS provider
   - Verify A record: `attendance.redstoneintelligence.com` → `97.75.162.142`

2. **SSL certificate not generated:**
   - Check Traefik logs: `docker-compose -f docker-compose.production.yml logs traefik`
   - Ensure ports 80 and 443 are open
   - Verify domain is accessible from internet

3. **Cannot access from external network:**
   - Check Windows Firewall rules
   - Verify router port forwarding
   - Confirm public IP hasn't changed

4. **Internal access works, external doesn't:**
   - Check router configuration
   - Verify firewall rules
   - Test from mobile network

### **Diagnostic Commands:**
```powershell
# Test local connectivity
Test-NetConnection -ComputerName localhost -Port 80
Test-NetConnection -ComputerName localhost -Port 443

# Test external connectivity
Test-NetConnection -ComputerName attendance.redstoneintelligence.com -Port 443

# Check public IP
(Invoke-RestMethod -Uri "https://api.ipify.org?format=json").ip

# View container logs
docker-compose -f docker-compose.production.yml logs -f
```

## 📱 Mobile and Remote Access

### **Mobile Access:**
- **URL:** `https://attendance.redstoneintelligence.com`
- **Responsive design:** Optimized for mobile devices
- **Touch-friendly:** Easy navigation on tablets and phones

### **Remote Access:**
- **VPN not required:** Direct internet access
- **Secure connection:** HTTPS encryption
- **Session management:** Automatic timeout for security

## 🔄 Maintenance

### **Regular Tasks:**
- **SSL certificates:** Auto-renewed every 90 days
- **Container updates:** Run `docker-compose pull` monthly
- **Log rotation:** Configured automatically
- **Data backup:** Ensure attendance data is backed up

### **Security Updates:**
- **Monitor logs:** Check for suspicious activity
- **Update credentials:** Change passwords periodically
- **Review access:** Audit user access regularly

## 🎯 Success Checklist

**✅ DNS Resolution:** `attendance.redstoneintelligence.com` → `97.75.162.142`
**✅ Firewall Rules:** Ports 80, 443, 8080 open
**✅ SSL Certificate:** Auto-generated and valid
**✅ HTTPS Access:** `https://attendance.redstoneintelligence.com`
**✅ HTTP Redirect:** Automatic redirect to HTTPS
**✅ Mobile Access:** Works on all devices
**✅ Remote Access:** Accessible from anywhere

---

## 🚀 Next Steps

1. **Run deployment script:** `.\deploy_production.ps1 -Deploy`
2. **Configure firewall:** Run `setup_firewall.ps1 -Enable` as Admin
3. **Wait for SSL:** Allow 2-3 minutes for certificate generation
4. **Test access:** Try `https://attendance.redstoneintelligence.com`
5. **Share with executives:** Provide secure access credentials

**Your dashboard will be securely accessible from anywhere with HTTPS encryption!**
