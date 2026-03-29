# HomeLabViewer Deployment Guide

## Deployment to appserv1

### Prerequisites
- Docker installed on appserv1
- nginx configured for reverse proxy
- Port 8200 available

### Build & Deploy Steps

1. **Copy files to appserv1:**
```bash
scp -r C:\Users\john_\dev\HomeLabViewer john@192.168.4.148:/home/john/
```

2. **Build Docker image on appserv1:**
```bash
ssh john@192.168.4.148
cd /home/john/HomeLabViewer
docker build -t homelabviewer:latest .
```

3. **Run container:**
```bash
docker run -d --name homelabviewer -p 8200:8200 homelabviewer:latest
```

4. **Configure nginx reverse proxy:**
Add to `/etc/nginx/sites-available/default`:
```nginx
location /homelabviewer/ {
    proxy_pass http://localhost:8200/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

5. **Reload nginx:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Access
- Local: http://localhost:8200
- Production: http://192.168.4.148/homelabviewer/

### Docker Commands
- View logs: `docker logs homelabviewer`
- Restart: `docker restart homelabviewer`
- Stop: `docker stop homelabviewer`
- Remove: `docker rm homelabviewer`

### Update Deployment
```bash
cd /home/john/HomeLabViewer
git pull
docker stop homelabviewer
docker rm homelabviewer
docker build -t homelabviewer:latest .
docker run -d --name homelabviewer -p 8200:8200 homelabviewer:latest
```
