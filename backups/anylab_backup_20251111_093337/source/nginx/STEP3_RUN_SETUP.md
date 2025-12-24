# Step 3: Run SSL Certificate Setup

## ✅ Token Created - Ready to Continue!

Now that you have your Cloudflare API token, let's get the SSL certificate.

## Step 1: Install Plugin (If Not Done)

First, make sure the certbot Cloudflare plugin is installed:

```bash
pip3 install certbot-dns-cloudflare --break-system-packages
```

If that doesn't work, try:
```bash
sudo pip3 install certbot-dns-cloudflare --break-system-packages
```

Verify installation:
```bash
python3 -c "import certbot_dns_cloudflare" && echo "✅ Plugin installed"
```

## Step 2: Run Setup Script

Navigate to the project directory and run the setup script:

```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-cloudflare-ssl.sh
```

## What the Script Will Do

1. **Check Certbot** - Verify certbot is installed
2. **Install Plugin** - Install certbot-dns-cloudflare if needed
3. **Ask for Token** - Prompt you to enter your Cloudflare API token
4. **Create Credentials** - Save token securely in `/etc/letsencrypt/cloudflare.ini`
5. **Get Certificate** - Request SSL certificate via DNS challenge
6. **Configure Nginx** - Update nginx config with certificate paths
7. **Test & Reload** - Verify nginx config and reload

## When Prompted for Token

The script will ask:
```
Enter your Cloudflare API token (it will be hidden):
```

1. **Paste your token** (the long string you copied)
2. Press **Enter**
3. The token will be hidden as you type (for security)

## Expected Output

You should see:
```
✅ Certbot is installed
✅ Plugin installed
📝 Creating credentials file...
✅ Credentials file created
🔐 Obtaining SSL certificate...
✅ Certificate obtained successfully!
⚙️  Configuring nginx...
✅ Nginx configured
✅ SSL Certificate Setup Complete!
```

## Troubleshooting

### Issue: "Plugin not found"
**Solution:**
```bash
pip3 install certbot-dns-cloudflare --break-system-packages
```

### Issue: "Token authentication failed"
**Solution:**
- Verify token is correct (no extra spaces)
- Check token has correct permissions (Zone Read, DNS Edit)
- Ensure token is for `dpdns.org` zone

### Issue: "DNS challenge failed"
**Solution:**
- Verify domain `anylab.dpdns.org` is in Cloudflare
- Check DNS is pointing to Cloudflare
- Ensure token has DNS Edit permission

### Issue: "Permission denied"
**Solution:**
- Make sure you're using `sudo`
- Check `/etc/letsencrypt` directory permissions

## After Successful Setup

1. **Set Cloudflare SSL Mode:**
   - Go to Cloudflare Dashboard
   - SSL/TLS → Overview
   - Set to **"Full (strict)"**
   - Save

2. **Test HTTPS:**
   ```bash
   curl -I https://anylab.dpdns.org
   ```

3. **Verify Certificate:**
   ```bash
   sudo certbot certificates
   ```

4. **Check Nginx:**
   ```bash
   sudo nginx -t
   sudo nginx -s reload
   ```

## Manual Method (If Script Fails)

If the script doesn't work, you can do it manually:

```bash
# 1. Create credentials file
sudo mkdir -p /etc/letsencrypt
sudo nano /etc/letsencrypt/cloudflare.ini
# Add: dns_cloudflare_api_token = YOUR_TOKEN_HERE
sudo chmod 600 /etc/letsencrypt/cloudflare.ini

# 2. Get certificate
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d anylab.dpdns.org \
  --agree-tos \
  --email admin@anylab.dpdns.org

# 3. Configure nginx
sudo certbot --nginx -d anylab.dpdns.org
```

## Next Steps After Certificate

Once you have the certificate:

1. ✅ Certificate installed
2. ✅ Nginx configured
3. ⏭️ Set Cloudflare to "Full (strict)"
4. ⏭️ Test https://anylab.dpdns.org
5. ⏭️ Enjoy encrypted connection! 🔒

## Ready?

Run the setup script now:
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-cloudflare-ssl.sh
```

Good luck! 🚀

