# 🔥 Manual Firewall Setup Guide

## ⚠️ Required: Open Ports for HTTPS Access

Your SSL certificate generation is failing because Let's Encrypt can't reach your server on port 80. You need to open these ports:

### **Step 1: Open Windows Firewall Advanced Settings**

1. **Press Windows + R**
2. **Type:** `wf.msc`
3. **Press Enter**
4. **Click "Yes"** if prompted by User Account Control

### **Step 2: Create Inbound Rules**

#### **Rule 1: HTTP (Port 80)**
1. **Right-click** on "Inbound Rules"
2. **Select** "New Rule..."
3. **Rule Type:** Port
4. **Protocol:** TCP
5. **Specific Local Ports:** 80
6. **Action:** Allow the connection
7. **Profile:** Check all (Domain, Private, Public)
8. **Name:** "Attendance Dashboard - HTTP"
9. **Description:** "Allow HTTP for Let's Encrypt certificate validation"
10. **Click Finish**

#### **Rule 2: HTTPS (Port 443)**
1. **Right-click** on "Inbound Rules"
2. **Select** "New Rule..."
3. **Rule Type:** Port
4. **Protocol:** TCP
5. **Specific Local Ports:** 443
6. **Action:** Allow the connection
7. **Profile:** Check all (Domain, Private, Public)
8. **Name:** "Attendance Dashboard - HTTPS"
9. **Description:** "Allow HTTPS for secure dashboard access"
10. **Click Finish**

#### **Rule 3: Traefik Admin (Port 8080) - Optional**
1. **Right-click** on "Inbound Rules"
2. **Select** "New Rule..."
3. **Rule Type:** Port
4. **Protocol:** TCP
5. **Specific Local Ports:** 8080
6. **Action:** Allow the connection
7. **Profile:** Check all (Domain, Private, Public)
8. **Name:** "Attendance Dashboard - Traefik Admin"
9. **Description:** "Allow Traefik admin dashboard access"
10. **Click Finish**

### **Step 3: Verify Rules Are Created**

1. **In Windows Firewall Advanced Settings**
2. **Click "Inbound Rules"**
3. **Look for these rules:**
   - ✅ "Attendance Dashboard - HTTP" (Port 80)
   - ✅ "Attendance Dashboard - HTTPS" (Port 443)
   - ✅ "Attendance Dashboard - Traefik Admin" (Port 8080)

### **Step 4: Test Port Access**

**Open PowerShell and run:**
```powershell
Test-NetConnection -ComputerName localhost -Port 80
Test-NetConnection -ComputerName localhost -Port 443
Test-NetConnection -ComputerName localhost -Port 8080
```

**Expected results:**
- Port 80: TcpTestSucceeded : True
- Port 443: TcpTestSucceeded : True
- Port 8080: TcpTestSucceeded : True

### **Step 5: Router Configuration (If Needed)**

**If your server is behind a router/NAT:**
1. **Access your router's admin panel**
2. **Find Port Forwarding section**
3. **Add these rules:**
   - **Port 80** → Forward to `10.100.1.187:80`
   - **Port 443** → Forward to `10.100.1.187:443`
   - **Port 8080** → Forward to `10.100.1.187:8080`

### **Step 6: Restart Production Deployment**

**After configuring firewall:**
```powershell
# Stop and restart to trigger SSL certificate generation
.\deploy_production.ps1 -Stop
.\deploy_production.ps1 -Deploy
```

### **Step 7: Monitor SSL Certificate Generation**

**Check Traefik logs:**
```powershell
docker-compose -f docker-compose.production.yml logs -f traefik
```

**Look for:**
- ✅ "Certificate obtained successfully"
- ✅ "Serving certificate"
- ❌ "Unable to obtain ACME certificate" (should be gone)

### **Step 8: Test HTTPS Access**

**After 2-3 minutes:**
1. **Open browser**
2. **Go to:** `https://attendance.redstoneintelligence.com`
3. **Should see:** 🔒 Secure connection with valid SSL certificate

---

## 🚨 Common Issues

### **Issue 1: "Connection Timeout" in Traefik logs**
- **Cause:** Port 80 is blocked by firewall
- **Solution:** Ensure Windows Firewall rule for port 80 is created and enabled

### **Issue 2: "DNS problem: NXDOMAIN"**
- **Cause:** Domain not properly configured
- **Solution:** Verify DNS is pointing to correct IP address

### **Issue 3: "Cannot access from external network"**
- **Cause:** Router not forwarding ports
- **Solution:** Configure port forwarding in router settings

### **Issue 4: "SSL certificate not generated"**
- **Cause:** Let's Encrypt can't reach your server
- **Solution:** Check firewall rules and router configuration

---

## 🔧 Alternative: PowerShell Command (Admin Required)

**If you prefer PowerShell commands (run as Administrator):**
```powershell
# HTTP (Port 80)
New-NetFirewallRule -DisplayName "Attendance Dashboard - HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# HTTPS (Port 443)
New-NetFirewallRule -DisplayName "Attendance Dashboard - HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow

# Traefik Admin (Port 8080)
New-NetFirewallRule -DisplayName "Attendance Dashboard - Traefik Admin" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

---

## ✅ Success Checklist

After completing these steps, you should have:
- ✅ Windows Firewall rules for ports 80, 443, and 8080
- ✅ Router port forwarding configured (if behind NAT)
- ✅ SSL certificate generated successfully
- ✅ HTTPS access working: `https://attendance.redstoneintelligence.com`
- ✅ Secure dashboard access for executives

**Once firewall is configured, your dashboard will be securely accessible from anywhere!**
