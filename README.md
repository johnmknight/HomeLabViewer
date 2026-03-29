# HomeLabViewer

Network topology visualization for SmartLab homelab environment.

## Features

- Real-time network topology visualization using Cytoscape.js
- Integration with Home Assistant network discovery
- Clean, modern dark UI
- Docker deployment ready

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
python main.py
```

Access at: http://localhost:8200

### Docker Deployment
```bash
docker build -t homelabviewer .
docker run -p 8200:8200 homelabviewer
```

## Architecture

- **Backend:** FastAPI (Python)
- **Frontend:** Vanilla JS + Cytoscape.js
- **Data Source:** Home Assistant network topology
- **Port:** 8200

## Configuration

Set environment variables:
- `HA_URL`: Home Assistant URL (default: http://192.168.4.51:8123)
- `HA_TOKEN`: Home Assistant API token
