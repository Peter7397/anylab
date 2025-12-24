# Neo4j Manual Installation Guide

## Current Issue

There appears to be a network connectivity issue when trying to pull the Neo4j Docker image. The error suggests:
- Network/firewall blocking Docker registry access
- IPv6 connectivity issue
- Proxy configuration needed

## Solutions

### Option 1: Fix Network & Retry (Recommended)

#### Check Network Connectivity
```bash
# Test Docker registry access
ping hub.docker.com

# Test if you can access Docker Hub
curl -I https://hub.docker.com
```

#### If Behind a Proxy
If you're behind a corporate firewall or proxy, configure Docker:

**On macOS (Docker Desktop):**
1. Open Docker Desktop
2. Go to Settings → Resources → Proxies
3. Configure your proxy settings
4. Click "Apply & Restart"

**On Linux:**
Create/edit `/etc/docker/daemon.json`:
```json
{
  "proxies": {
    "http-proxy": "http://proxy.example.com:8080",
    "https-proxy": "http://proxy.example.com:8080",
    "no-proxy": "localhost,127.0.0.1"
  }
}
```
Then restart Docker: `sudo systemctl restart docker`

#### Disable IPv6 (if IPv6 is the issue)
Try using IPv4 only by modifying Docker daemon settings.

### Option 2: Use Alternative Image Source

Try pulling from a different registry or use a mirror:

```bash
# Try official Neo4j registry
docker pull neo4j/neo4j:5.15-community

# Or try a different version
docker pull neo4j:5.14-community
```

### Option 3: Manual Download & Import

1. **Download image on a machine with internet access:**
   ```bash
   docker pull neo4j:5.15-community
   docker save neo4j:5.15-community -o neo4j-5.15-community.tar
   ```

2. **Transfer to your machine** (via USB, network share, etc.)

3. **Load the image:**
   ```bash
   docker load -i neo4j-5.15-community.tar
   ```

4. **Start the container:**
   ```bash
   docker compose up -d neo4j
   ```

### Option 4: Use Docker Desktop's Image Download

If using Docker Desktop on macOS:
1. Open Docker Desktop
2. Go to Images tab
3. Click "Pull" or "+" button
4. Search for "neo4j:5.15-community"
5. Pull the image through the UI

## Quick Retry After Network Fix

Once network is fixed, try again:

```bash
# Pull the image
docker pull neo4j:5.15-community

# Start Neo4j
docker compose up -d neo4j

# Check status
docker ps | grep neo4j

# View logs
docker compose logs neo4j
```

## Verify Installation

Once Neo4j is running:

1. **Check container status:**
   ```bash
   docker ps | grep neo4j
   ```

2. **Access Neo4j Browser:**
   - Open: http://localhost:7474
   - Username: `neo4j`
   - Password: `anylab_neo4j_password`

3. **Test from Django:**
   ```bash
   cd backend
   python manage.py shell
   ```
   ```python
   from ai_assistant.services.neo4j_service import get_neo4j_service
   neo4j = get_neo4j_service()
   print("Connected!" if neo4j.test_connection() else "Failed!")
   ```

## Alternative: Install Neo4j Locally (Without Docker)

If Docker continues to have issues, you can install Neo4j directly:

### macOS (Homebrew)
```bash
brew install neo4j
brew services start neo4j
```

### Linux
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
sudo systemctl start neo4j
```

**Note:** If installing locally, update `NEO4J_URI` in `settings.py` to match your installation.

## Troubleshooting Network Issues

### Check Docker Network Settings
```bash
# Check Docker info
docker info | grep -i proxy
docker info | grep -i network
```

### Test Direct Connection
```bash
# Test if you can reach Docker Hub
curl -v https://registry-1.docker.io/v2/

# Check DNS resolution
nslookup registry-1.docker.io
```

### Try Different DNS
Edit `/etc/docker/daemon.json`:
```json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```
Restart Docker after changes.

## Still Having Issues?

1. **Check firewall settings** - Docker needs outbound HTTPS access
2. **Check VPN** - Some VPNs block Docker registry
3. **Try at different time** - Network might be temporarily down
4. **Contact network admin** - If on corporate network, may need whitelist

## Next Steps After Installation

Once Neo4j is running, proceed with:
1. Test connection from Django
2. Create constraints/indexes
3. Begin graph construction (Week 2 of migration plan)

---

**Need help?** Check the main setup guide: `NEO4J_SETUP_GUIDE.md`

