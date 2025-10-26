# AnyLab Testing Guide

## 🧪 **Comprehensive Testing Checklist**

### **1. Local Testing**
- [ ] Frontend accessible at: http://localhost:3000
- [ ] Backend accessible at: http://localhost:8000
- [ ] Database connection working
- [ ] All features functional locally

### **2. External Testing**
- [ ] **Main site**: https://anylab.dpdns.org
- [ ] **API endpoint**: https://api.anylab.dpdns.org
- [ ] **Mobile access**: Test on phone/tablet
- [ ] **Different networks**: Test from different WiFi/mobile data

### **3. Performance Testing**
- [ ] Page load speed
- [ ] API response times
- [ ] File upload/download
- [ ] Database queries

### **4. Security Testing**
- [ ] HTTPS working (green lock icon)
- [ ] No mixed content warnings
- [ ] CORS headers working
- [ ] Authentication flows

### **5. Auto-Startup Testing**
- [ ] Restart Mac
- [ ] Check tunnel starts automatically
- [ ] Verify application accessible after restart

## 🚀 **Quick Commands**

### **Start Everything:**
```bash
cd /Volumes/Orico/AnyLab0812
./start-anylab.sh
```

### **Stop Everything:**
```bash
cd /Volumes/Orico/AnyLab0812
./stop-anylab.sh
```

### **Check Tunnel Status:**
```bash
cloudflared tunnel info anylab
```

### **Check Service Status:**
```bash
launchctl list | grep cloudflare
```

## 🌐 **Public URLs**
- **Main Application**: https://anylab.dpdns.org
- **API Endpoint**: https://api.anylab.dpdns.org
- **GitHub Repository**: https://github.com/Peter7397/anylab

## 📊 **Monitoring**
- **Cloudflare Analytics**: Check dashboard for traffic stats
- **Tunnel Logs**: `~/.cloudflared/tunnel.log`
- **Error Logs**: `~/.cloudflared/tunnel.error.log`

## 🔧 **Troubleshooting**
- If tunnel stops: `launchctl start com.cloudflare.tunnel.anylab`
- If services don't start: Check Docker containers are running
- If DNS issues: Wait 5-10 minutes for propagation
