# HomeLabViewer - Production Deployment Guide

This guide covers deploying HomeLabViewer to appserv1 (192.168.4.148) with nginx reverse proxy.

## Prerequisites

- appserv1 running and accessible
- SSH access to appserv1 (`ssh john@192.168.4.148`)
- Docker installed on appserv1
- nginx configured for reverse proxy
- SmartLabNetOps API running at `http://192.168.4.150:8096`

## Quick Deployment

### 1. Copy Files to appserv1

From your development PC:

```bash
# Copy entire project directory
scp -r C:\Users\john_\dev\HomeLabViewer john@192.168.4.148:/home/john/
```

Or copy individual files:

```bash
# Copy application files
type main.py | ssh john@192.168.4.148 "cat > /home/john/HomeLabViewer/main.py"
type client\index.html | ssh john@192.168.4.148 "cat > /home/john/HomeLabViewer/client/index.html"

# Copy dependencies
type requirements.txt | ssh john@192.168.4.148 "cat > /home/john/HomeLabViewer/requirements.txt"
type Dockerfile | ssh john@192.168.4.148 "cat > /home/john/HomeLabViewer/Dockerfile"
```

### 2. Build Docker Image

SSH into appserv1:

```bash
ssh john@192.168.4.148
cd /home/john/HomeLabViewer

# Build the image
docker build -t homelabviewer:latest .
```

### 3. Run Docker Container

```bash
# Stop and remove old container if exists
docker stop homelabviewer 2>/dev/null || true
docker rm homelabviewer 2>/dev/null || true

# Run new container
docker run -d \
  --name homelabviewer \
  --restart unless-stopped \
  -p 8200:8200 \
  homelabviewer:latest

# Check status
docker ps | grep homelabviewer
docker logs homelabviewer
```

### 4. Configure nginx Reverse Proxy

Create nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/homelabviewer
```

Add this configuration:

```nginx
location /homelabviewer/ {
    proxy_pass http://localhost:8200/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support (if needed in future)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

Enable and reload nginx:

```bash
sudo ln -s /etc/nginx/sites-available/homelabviewer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Access the Application

Open in browser:
```
http://192.168.4.148/homelabviewer/
```

## Container Management

### View Logs
```bash
docker logs -f homelabviewer
```

### Restart Container
```bash
docker restart homelabviewer
```

### Stop Container
```bash
docker stop homelabviewer
```

### Remove Container
```bash
docker stop homelabviewer
docker rm homelabviewer
```

### Update to New Version
```bash
cd /home/john/HomeLabViewer
git pull origin master  # If using git
docker build -t homelabviewer:latest .
docker stop homelabviewer
docker rm homelabviewer
docker run -d --name homelabviewer --restart unless-stopped -p 8200:8200 homelabviewer:latest
```

## Docker Compose (Alternative)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  homelabviewer:
    build: .
    container_name: homelabviewer
    restart: unless-stopped
    ports:
      - "8200:8200"
    environment:
      - TZ=America/New_York
```

Deploy with docker-compose:

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker logs homelabviewer
```

Common issues:
- Port 8200 already in use: `netstat -tuln | grep 8200`
- Python dependencies missing: Rebuild image
- File permissions: Check ownership of files

### Can't Access API

Test SmartLabNetOps API from appserv1:
```bash
curl http://192.168.4.150:8096/api/topology
```

If this fails:
- Check SmartLabNetOps is running on mgmt1
- Verify network connectivity between appserv1 and mgmt1
- Check firewall rules

### nginx 404 Error

Verify nginx configuration:
```bash
sudo nginx -t
cat /etc/nginx/sites-enabled/homelabviewer
```

Check proxy is reaching container:
```bash
curl http://localhost:8200/api/topology
```

### No Devices Showing

1. Check SmartLabNetOps API:
   ```bash
   curl http://192.168.4.150:8096/api/topology | python3 -m json.tool
   ```

2. Check browser console for errors (F12)

3. Verify container logs:
   ```bash
   docker logs homelabviewer
   ```

## Monitoring

### Health Check Script

Create `/home/john/scripts/check-homelabviewer.sh`:

```bash
#!/bin/bash
if ! docker ps | grep -q homelabviewer; then
    echo "HomeLabViewer container is not running!"
    # Optional: Restart automatically
    docker start homelabviewer
fi
```

Add to crontab:
```bash
crontab -e
# Add: */5 * * * * /home/john/scripts/check-homelabviewer.sh
```

### Resource Usage

```bash
docker stats homelabviewer
```

## Production URLs

- **Local development:** http://localhost:8200
- **Direct container access:** http://192.168.4.148:8200
- **Reverse proxy (production):** http://192.168.4.148/homelabviewer/

## Security Considerations

1. **API Access:** SmartLabNetOps API is internal-only (192.168.4.0/24 network)
2. **No Authentication:** Currently no auth layer (internal network only)
3. **nginx:** Acts as reverse proxy, provides additional security layer
4. **Docker:** Containerization isolates the application

## Backup Strategy

Regular backups of configuration:
```bash
# Backup entire project
tar -czf homelabviewer-backup-$(date +%Y%m%d).tar.gz /home/john/HomeLabViewer

# Backup to remote location
scp homelabviewer-backup-*.tar.gz user@backup-server:/backups/
```

## Performance Optimization

For large networks (50+ devices):

1. **Increase layout iterations:** Edit `client/index.html`
   ```javascript
   layout: {
     name: 'cose',
     numIter: 2000,  // Increase from 1000
     ...
   }
   ```

2. **Adjust node repulsion:** For tighter clustering
   ```javascript
   nodeRepulsion: 6000,  // Decrease from 8000
   ```

3. **Enable caching:** Add nginx caching for static assets

## Integration with smartlab-infra

To include in smartlab-infra docker-compose stack, add to main compose file:

```yaml
homelabviewer:
  image: ghcr.io/johnmknight/homelabviewer:latest
  container_name: homelabviewer
  restart: unless-stopped
  ports:
    - "8200:8200"
  networks:
    - smartlab
```

## Support

For issues, check:
1. Container logs: `docker logs homelabviewer`
2. nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. SmartLabNetOps API status
4. Home Assistant connectivity

---

**Last Updated:** 2026-03-28  
**Version:** 1.0.0  
**Deployed on:** appserv1 (192.168.4.148)
