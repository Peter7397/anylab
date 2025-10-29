# Network Access Issue Analysis

**Issue**: Accessing `anylab.dpdns.org` from another PC results in "Connection Refused" and redirects to localhost.

**Date**: January 2025  
**Status**: ⚠️ **DIAGNOSIS ONLY - NO CODE CHANGES**

---

## 🔍 Root Cause Analysis

### **Problem Identified**

1. **ALLOWED_HOSTS Configuration** (`backend/anylab/settings.py` line 25):
   ```python
   ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,192.168.1.24,10.96.17.21').split(',')
   ```

   **❌ Missing**: `anylab.dpdns.org` domain name
   **✅ Has**: Local IPs (192.168.1.24, 10.96.17.21) and localhost

2. **CORS Configuration** (`backend/anylab/settings.py` lines 197-203):
   ```python
   CORS_ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://127.0.0.1:3000',
       'http://192.168.1.24:3000',
       'http://10.96.17.21:3000',
       'https://anylab.dpdns.org',  # ✅ This IS included
   ]
   ```

   **✅ CORS is configured** for the domain

3. **Server Bind Configuration**:
   - Django server is running on `0.0.0.0:8000` (all interfaces) ✅
   - This is correct for external access

---

## 🎯 Why It Fails

### **Access Flow from External PC**:

1. External PC accesses: `https://anylab.dpdns.org` (via DNS/port forwarding)
2. Request reaches Django server
3. **Django checks ALLOWED_HOSTS** ❌
4. Domain name `anylab.dpdns.org` is NOT in the list
5. Django **rejects the connection** with "DisallowedHost"
6. Connection refused error
7. User sees "localhost" in error (Django's default reject response)

---

## 🔧 What Needs to be Fixed

### **Required Changes**:

#### 1. **Update ALLOWED_HOSTS**
Add the domain name to the configuration:

**Option A** (Environment Variable - Recommended):
```bash
# Set in .env file or environment
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.24,10.96.17.21,anylab.dpdns.org
```

**Option B** (Direct Code Change):
```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,192.168.1.24,10.96.17.21,anylab.dpdns.org').split(',')
```

#### 2. **Add HTTP (not just HTTPS) to CORS if needed**
Current CORS only has `https://anylab.dpdns.org`, but you may also need:
```python
CORS_ALLOWED_ORIGINS = [
    # ... existing entries ...
    'https://anylab.dpdns.org',
    'http://anylab.dpdns.org',  # Add if using HTTP
]
```

#### 3. **Also Add to Frontend CORS** (if applicable)
Check if frontend also needs to allow the domain.

---

## 🌐 Network Configuration Check

### **Additional Checks Needed** (Not in code):

1. **DNS Resolution**:
   - Does `anylab.dpdns.org` resolve to the correct IP (192.168.1.24 or 10.96.17.21)?
   - Check with: `nslookup anylab.dpdns.org` or `ping anylab.dpdns.org`

2. **Port Forwarding**:
   - Is port 8000 forwarded from external → server's local IP?
   - External access needs proper port forwarding in router/firewall

3. **SSL/TLS Certificate**:
   - If using HTTPS (https://anylab.dpdns.org), certificate must be valid
   - If using HTTP only, that should work too

4. **Firewall Rules**:
   - Server firewall must allow port 8000 from external
   - Router firewall must allow the connection

---

## 📋 Solution Summary

### **Immediate Fix** (Required):

1. **Add domain to ALLOWED_HOSTS**:
   ```python
   ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,192.168.1.24,10.96.17.21,anylab.dpdns.org').split(',')
   ```

2. **Optionally add HTTP to CORS**:
   ```python
   CORS_ALLOWED_ORIGINS = [
       # ... existing ...
       'https://anylab.dpdns.org',
       'http://anylab.dpdns.org',  # Add if HTTP access needed
   ]
   ```

3. **Restart Django server** after changes

### **Why This Happens**:

Django's `ALLOWED_HOSTS` is a **security feature** to prevent HTTP Host header attacks. When you access via IP address, the Host header matches one of the IPs in the list. But when accessing via domain name, Django expects that domain in ALLOWED_HOSTS.

### **Why It Shows "localhost"**:

Django's rejection response includes "localhost" as a fallback suggestion, not the actual redirect destination.

---

## ✅ Verification Checklist

After fix, verify:
- [ ] `anylab.dpdns.org` resolves to correct IP
- [ ] ALLOWED_HOSTS includes `anylab.dpdns.org`
- [ ] CORS includes the protocol being used (http:// or https://)
- [ ] Port forwarding is configured (if external access)
- [ ] Firewall allows port 8000
- [ ] Server is restarted with new configuration
- [ ] Can access from external PC via domain name

---

## 🚨 Security Note

When adding domain to ALLOWED_HOSTS, make sure:
- DNS is properly configured and trustworthy
- SSL certificate is valid (if using HTTPS)
- Firewall rules are properly configured
- Not exposing development server to public internet without proper security measures

---

**Date**: January 2025  
**Status**: ⚠️ **READY FOR FIX** - Add domain to ALLOWED_HOSTS configuration

