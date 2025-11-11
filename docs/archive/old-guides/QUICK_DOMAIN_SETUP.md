# Quick Domain Setup - anylab.dpdns.org

**AnyLab uses Cloudflare Tunnel** - no nginx, SSL certificates, or port forwarding needed!

## 🚀 Quick Setup

### Step 1: Ensure Cloudflare Tunnel is Running
```bash
# Check if tunnel is running
ps aux | grep cloudflared

# If not running, start it:
cloudflared tunnel run anylab
```

### Step 2: Verify Configuration
The tunnel config is at: `~/.cloudflared/config.yml`

It should route:
- `/api/*`, `/admin/*`, `/media/*`, `/static/*` → Backend (port 8001)
- Everything else → Frontend (port 3000)

### Step 3: Access Your Site
- **Frontend**: https://anylab.dpdns.org
- **API**: https://anylab.dpdns.org/api/
- **Admin**: https://anylab.dpdns.org/admin/

**That's it!** No firewall, no port forwarding, no SSL certificates needed.

For detailed setup, see: [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)

## ✅ What's Already Configured

- ✅ Backend CORS settings updated
- ✅ Frontend API configuration updated
- ✅ Nginx configuration file created
- ✅ Domain name added to ALLOWED_HOSTS

## 📍 Access URLs

Once set up:
- **Frontend**: https://anylab.dpdns.org
- **API**: https://anylab.dpdns.org/api/
- **Admin**: https://anylab.dpdns.org/admin/

## 🔍 Troubleshooting

**Can't access from internet?**
1. Check DNS: `nslookup anylab.dpdns.org`
2. Check firewall: `sudo ufw status` (Linux) or check System Preferences (macOS)
3. Check router port forwarding
4. Check nginx: `sudo systemctl status nginx`

**502 Bad Gateway?**
1. Check backend: `ps aux | grep "manage.py runserver"`
2. Check frontend: `ps aux | grep "react-scripts"`
3. Check logs: `tail -f logs/django.log`

**SSL Certificate Error?**
1. Renew certificate: `sudo certbot renew`
2. Check certificate: `sudo certbot certificates`

## 📚 Full Documentation

See `DOMAIN_SETUP_GUIDE.md` for detailed instructions.

