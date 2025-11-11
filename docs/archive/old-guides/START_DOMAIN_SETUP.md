# 🚀 Start Domain Setup

## Quick Start (2 Commands)

### 1. Install Nginx and Configure
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-nginx.sh
```

### 2. Set Up SSL Certificate
```bash
sudo certbot --nginx -d anylab.dpdns.org
```

## That's it! 🎉

After running these commands, your application will be accessible at:
- **https://anylab.dpdns.org**

## Need Help?

- Run prerequisites check: `./nginx/verify-prerequisites.sh`
- See detailed guide: `DOMAIN_SETUP_GUIDE.md`
- See step-by-step: `nginx/STEP_BY_STEP_SETUP.md`

## Current Status

✅ All prerequisites passed
✅ Configuration files ready
✅ Services running
✅ Ready to proceed
