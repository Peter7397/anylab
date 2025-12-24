# 🚀 Domain Setup - Ready to Proceed!

## ✅ Prerequisites Status

All prerequisites are **PASSED**! Your system is ready for domain setup.

- ✅ DNS configured: `anylab.dpdns.org` → `172.67.211.104`
- ✅ Homebrew installed
- ✅ Ports 80 and 443 available
- ✅ Backend running on port 8001
- ✅ Frontend running on port 3000
- ✅ Docker services running (PostgreSQL, Redis)

## 🎯 Next Steps (2 Commands)

### Step 1: Install and Configure Nginx

Run this command (you'll need to enter your password):
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh
```

This will:
- Install nginx
- Configure reverse proxy
- Set up the domain configuration

### Step 2: Set Up SSL Certificate

After nginx is installed, run:
```bash
sudo certbot --nginx -d anylab.dpdns.org
```

Follow the prompts to complete SSL setup.

## 📋 Quick Reference

### Access URLs (After Setup)
- **Frontend**: https://anylab.dpdns.org
- **Backend API**: https://anylab.dpdns.org/api/
- **Admin Panel**: https://anylab.dpdns.org/admin/

### Verification Commands
```bash
# Check DNS
nslookup anylab.dpdns.org

# Test HTTP (should redirect to HTTPS)
curl -I http://anylab.dpdns.org

# Test HTTPS
curl -I https://anylab.dpdns.org

# Check nginx status
sudo systemctl status nginx  # Linux
# or
ps aux | grep nginx  # macOS
```

### Logs
```bash
# Nginx logs
sudo tail -f /var/log/nginx/anylab_error.log

# Application logs
tail -f logs/django.log
tail -f logs/frontend.log
```

## 📚 Documentation

- **Detailed Guide**: `DOMAIN_SETUP_GUIDE.md`
- **Step-by-Step**: `nginx/STEP_BY_STEP_SETUP.md`
- **Quick Setup**: `QUICK_DOMAIN_SETUP.md`

## ⚠️ Important Notes

1. **Firewall**: Ensure ports 80 and 443 are open in your firewall/router
2. **Port Forwarding**: Configure router to forward ports 80/443 to your server
3. **DNS**: Verify DNS propagation (may take a few minutes to hours)
4. **SSL**: Certbot requires domain to be accessible from internet

## 🆘 Troubleshooting

If you encounter issues:

1. **Run prerequisites check:**
   ```bash
   ./nginx/verify-prerequisites.sh
   ```

2. **Check nginx configuration:**
   ```bash
   sudo nginx -t
   ```

3. **Check service status:**
   ```bash
   ps aux | grep nginx
   ps aux | grep "manage.py runserver"
   ps aux | grep "react-scripts\|craco"
   ```

4. **Review logs:**
   - Nginx: `/var/log/nginx/anylab_error.log`
   - Django: `logs/django.log`
   - Frontend: `logs/frontend.log`

## ✨ What's Already Configured

- ✅ Nginx configuration file (`nginx/anylab.conf`)
- ✅ Setup automation script (`nginx/setup-nginx.sh`)
- ✅ CORS settings updated in backend
- ✅ Frontend API configuration updated
- ✅ Domain added to ALLOWED_HOSTS

You're all set! Just run the two commands above to complete the setup.

