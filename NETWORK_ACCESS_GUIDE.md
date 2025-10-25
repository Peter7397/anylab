# 🌐 OnLab Network Access Guide

## 📋 **Quick Access Information**

### **Frontend (React UI)**
- **Local Access**: `http://localhost:3000`
- **Network Access**: `http://192.168.1.24:3000`
- **Status**: ✅ Optimized for network access

### **Backend (Django API)**
- **Local Access**: `http://localhost:8000`
- **Network Access**: `http://192.168.1.24:8000`
- **API Endpoint**: `http://192.168.1.24:8000/api`

## 🚀 **How to Access from Other PCs**

### **Step 1: Ensure Both Servers Are Running**
```bash
# Check if servers are running
curl -I http://192.168.1.24:3000  # Frontend
curl -I http://192.168.1.24:8000  # Backend
```

### **Step 2: Access from Any PC on the Network**
1. **Open any web browser** on the other PC
2. **Navigate to**: `http://192.168.1.24:3000`
3. **Login with**:
   - Username: `admin`
   - Password: `admin123`

## 🔧 **Optimization Features**

### **Frontend Optimizations**
- ✅ **Network Access**: Configured for `0.0.0.0` binding
- ✅ **Performance**: Source maps disabled for faster loading
- ✅ **CORS**: Configured for cross-origin requests
- ✅ **Fast Refresh**: Enabled for better development experience

### **Backend Optimizations**
- ✅ **Network Access**: Running on `0.0.0.0:8000`
- ✅ **CORS**: Configured to allow frontend requests
- ✅ **Authentication**: JWT-based with refresh tokens

## 📱 **Mobile Access**

### **From Mobile Devices**
- **Same Network**: Use `http://192.168.1.24:3000`
- **Different Network**: Requires port forwarding or VPN

### **Mobile Optimization**
- ✅ **Responsive Design**: UI adapts to mobile screens
- ✅ **Touch-Friendly**: Optimized for touch interactions
- ✅ **Fast Loading**: Optimized bundle size

## 🔒 **Security Considerations**

### **Network Security**
- ⚠️ **Development Mode**: Not suitable for production
- ⚠️ **No HTTPS**: Use VPN for secure access
- ⚠️ **Firewall**: Ensure ports 3000 and 8000 are open

### **Authentication**
- ✅ **JWT Tokens**: Secure token-based authentication
- ✅ **Session Management**: Automatic token refresh
- ✅ **Logout**: Proper token cleanup

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Can't Access from Other PC**
```bash
# Check if servers are running
ps aux | grep -E "(react-scripts|python.*runserver)"

# Check network connectivity
ping 192.168.1.24

# Check firewall
sudo ufw status
```

#### **2. API Connection Issues**
```bash
# Test API connectivity
curl -X GET http://192.168.1.24:8000/api/health/

# Check CORS configuration
curl -H "Origin: http://192.168.1.24:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS http://192.168.1.24:8000/api/
```

#### **3. Performance Issues**
```bash
# Restart with optimized settings
cd frontend && npm run start:network

# Check bundle size
npm run build:prod
```

## 📊 **Performance Monitoring**

### **Frontend Performance**
- **Bundle Size**: Optimized with code splitting
- **Loading Time**: Fast refresh enabled
- **Memory Usage**: Optimized React components

### **Backend Performance**
- **Response Time**: Fast Django API responses
- **Database**: Optimized PostgreSQL queries
- **Caching**: Redis for session management

## 🎯 **Best Practices**

### **For Development**
1. **Use Network Access**: `http://192.168.1.24:3000`
2. **Monitor Console**: Check browser developer tools
3. **Test Responsiveness**: Test on different screen sizes
4. **Check Performance**: Use browser performance tools

### **For Production**
1. **Use HTTPS**: Configure SSL certificates
2. **Set Up Proxy**: Use nginx for better performance
3. **Enable Caching**: Configure proper caching headers
4. **Monitor Logs**: Set up proper logging

## 📞 **Support**

### **Quick Commands**
```bash
# Start optimized frontend
cd frontend && npm run start:network

# Start backend
cd backend && source venv/bin/activate && python manage.py runserver 0.0.0.0:8000

# Check status
curl -I http://192.168.1.24:3000 && curl -I http://192.168.1.24:8000
```

### **Network Information**
- **Your IP**: `192.168.1.24`
- **Frontend Port**: `3000`
- **Backend Port**: `8000`
- **Network**: Local network access only

---

**🎉 Your OnLab application is now optimized for network access!**
