# Cloudflare: Zone vs Subdomain Explained

## Important Distinction

### Zone (Root Domain)
- **`dpdns.org`** = This is your **zone** in Cloudflare
- This is what you select when creating the API token
- The zone contains all subdomains

### Subdomain
- **`anylab.dpdns.org`** = This is your **subdomain**
- This is what you're getting the certificate for
- It's part of the `dpdns.org` zone

## When Creating API Token

✅ **Select Zone:** `dpdns.org` (the root domain)

This token will work for:
- `anylab.dpdns.org` ✅
- `www.dpdns.org` ✅
- `api.dpdns.org` ✅
- Any other subdomain under `dpdns.org` ✅

## When Getting Certificate

✅ **Certificate Domain:** `anylab.dpdns.org` (the subdomain)

This is what you specify in the certbot command:
```bash
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d anylab.dpdns.org  # <-- This is your subdomain
```

## Summary

- **API Token Zone:** `dpdns.org` (root domain)
- **Certificate Domain:** `anylab.dpdns.org` (subdomain)
- **Both are correct!** ✅

The zone gives you permission to manage DNS for the entire domain, which allows certbot to add the necessary TXT records for the DNS challenge.
