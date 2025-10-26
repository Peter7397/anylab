# Cloudflare Configuration Guide for AnyLab

## 🔒 **Security Configuration Checklist**

### **SSL/TLS Settings**
- [ ] **Encryption Mode**: Full (strict)
- [ ] **Always Use HTTPS**: On
- [ ] **HTTP Strict Transport Security (HSTS)**: On
- [ ] **Minimum TLS Version**: TLS 1.2
- [ ] **Edge Certificates**: All enabled

### **Security Settings**
- [ ] **Security Level**: Medium
- [ ] **Bot Fight Mode**: Enable
- [ ] **Challenge Passage**: 30 minutes
- [ ] **Browser Integrity Check**: Enable

### **WAF (Web Application Firewall)**
- [ ] **Managed Rules**: Enable
- [ ] **Cloudflare Managed Ruleset**: On
- [ ] **Cloudflare OWASP Core Ruleset**: On

### **Rate Limiting**
- [ ] **API Rate Limiting**: 100 requests/minute per IP
- [ ] **Login Rate Limiting**: 5 attempts/minute per IP

## ⚡ **Performance Configuration Checklist**

### **Speed Optimization**
- [ ] **Auto Minify**: HTML, CSS, JavaScript
- [ ] **Brotli Compression**: Enable
- [ ] **HTTP/2**: Enable
- [ ] **HTTP/3 (QUIC)**: Enable

### **Caching**
- [ ] **Caching Level**: Standard
- [ ] **Browser Cache TTL**: 4 hours
- [ ] **Always Online**: Enable
- [ ] **Development Mode**: Off

### **Page Rules**
- [ ] **Rule 1**: `anylab.dpdns.org/*` → Cache Everything
- [ ] **Rule 2**: `api.anylab.dpdns.org/*` → Cache Level: Bypass

## 🛡️ **Advanced Security Features**

### **DDoS Protection**
- [ ] **DDoS Protection**: Enable
- [ ] **Network-layer DDoS**: Automatic

### **Access Control**
- [ ] **IP Access Rules**: Configure if needed
- [ ] **Country Blocking**: Configure if needed
- [ ] **User Agent Blocking**: Configure if needed

## 📊 **Monitoring & Analytics**

### **Analytics**
- [ ] **Web Analytics**: Enable
- [ ] **Web Vitals**: Enable
- [ ] **Real User Monitoring**: Enable (optional)

## 🧪 **Testing Your Configuration**

### **Security Tests**
1. **HTTPS Test**: Visit `https://anylab.dpdns.org` - should show green lock
2. **HSTS Test**: Check headers include `Strict-Transport-Security`
3. **TLS Test**: Use SSL Labs test (https://www.ssllabs.com/ssltest/)

### **Performance Tests**
1. **Page Speed**: Use Google PageSpeed Insights
2. **Caching Test**: Check response headers for cache-control
3. **Compression Test**: Verify Brotli/Gzip headers

### **Rate Limiting Test**
1. **API Test**: Make multiple requests to `api.anylab.dpdns.org`
2. **Login Test**: Try multiple failed login attempts

## 🔧 **Useful Cloudflare URLs**

- **Dashboard**: https://dash.cloudflare.com
- **SSL/TLS**: https://dash.cloudflare.com/ssl-tls
- **Security**: https://dash.cloudflare.com/security
- **Speed**: https://dash.cloudflare.com/speed
- **Caching**: https://dash.cloudflare.com/caching
- **Analytics**: https://dash.cloudflare.com/analytics

## 📈 **Expected Performance Improvements**

After configuration, you should see:
- **Faster page loads** (30-50% improvement)
- **Better security** (DDoS protection, WAF)
- **Reduced server load** (caching)
- **Better SEO** (HTTPS, performance)

## 🚨 **Important Notes**

1. **Changes take 5-10 minutes** to propagate globally
2. **Test thoroughly** before going live
3. **Monitor analytics** for any issues
4. **Keep backups** of your configuration
5. **Review settings** monthly for optimization

## 🆘 **Troubleshooting**

### **If site becomes inaccessible:**
1. Check SSL/TLS settings
2. Verify DNS records
3. Check WAF rules
4. Review rate limiting rules

### **If performance degrades:**
1. Check caching settings
2. Review page rules
3. Verify compression settings
4. Check origin server response

### **If security issues:**
1. Review WAF logs
2. Check rate limiting
3. Verify SSL certificates
4. Review access rules
