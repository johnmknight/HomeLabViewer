# HomeLabViewer

**Network Topology Visualization for SmartLab Infrastructure**

A clean, modern web application for visualizing your home lab network topology with SVG icons, device groupings, and color-coded connection types.

![Network Topology](https://img.shields.io/badge/Status-Production-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)

---

## Features

### Visual Design
- **📦 Device Groupings** - Semi-transparent category boxes organize devices by type:
  - Infrastructure (Core Raspberry Pis)
  - Home Automation (Smart devices, ESP32s)
  - Network Equipment (Router, mesh nodes)
  - Virtual Services (Containers)
  - Other Devices (PCs, dev services)

- **🎨 SVG Icons** - Tabler icons show device function at a glance:
  - Router icon (purple) - Network routers
  - Server/Pi icon (cyan) - Raspberry Pis
  - TV icon (orange) - Streaming devices
  - Chip icon (yellow) - ESP32 microcontrollers
  - Stack icon (gray) - Virtual/containers

- **🌈 Color-Coded Devices** - Type-based color system:
  - **Purple** - Routers (eero)
  - **Cyan** - Raspberry Pis (mgmt1, dev1, appserv1, Home Assistant)
  - **Orange** - Streaming (Chromecast, Roku)
  - **Yellow** - ESP32 devices
  - **Gray** - Containers
  - **Blue** - Unknown devices

- **📡 Connection Line Colors** - Visual connection type indicators:
  - **Blue solid** - Ethernet (wired connections)
  - **Orange dashed** - Wireless (WiFi)
  - **Gray dotted** - Virtual (container/VM connections)

---

## Architecture

```
Home Assistant (192.168.4.51)
    ↓ Discovers devices
SmartLabNetOps API (192.168.4.150:8096)
    ↓ Provides /api/topology endpoint
HomeLabViewer Backend (FastAPI)
    ↓ Pass-through proxy
Cytoscape.js Frontend
    ↓ Renders with icons + colors
User's Browser
```

### Data Flow
1. **Home Assistant** discovers devices on the network
2. **SmartLabNetOps** reads HA inventory and formats as Cytoscape.js topology
3. **HomeLabViewer** serves the visualization frontend
4. **Frontend** fetches `/api/topology` and renders 29 devices + 5 category groups

---

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework with async support
- **httpx** - Async HTTP client for proxying SmartLabNetOps API
- **uvicorn** - ASGI server

### Frontend
- **Cytoscape.js 3.28.1** - Graph visualization library
- **Cose layout** - Force-directed graph layout algorithm
- **Tabler Icons** - SVG icon library (filled versions)
- **Vanilla JavaScript** - No framework dependencies

### Infrastructure
- **Docker** - Containerized deployment
- **nginx** - Reverse proxy on appserv1
- **Raspberry Pi** - Deployment target (appserv1)

---

## Installation

### Prerequisites
- Python 3.11+
- Docker (optional, for containerized deployment)
- Access to SmartLabNetOps API at `http://192.168.4.150:8096`

### Local Development

```bash
# Clone the repository
git clone https://github.com/johnmknight/HomeLabViewer.git
cd HomeLabViewer

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8200 --reload

# Access at http://localhost:8200
```

### Docker Deployment

```bash
# Build the image
docker build -t homelabviewer:latest .

# Run the container
docker run -d \
  --name homelabviewer \
  --restart unless-stopped \
  -p 8200:8200 \
  homelabviewer:latest
```

### Production Deployment (appserv1)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions including:
- Raspberry Pi setup
- nginx reverse proxy configuration
- Docker container management
- Health checks and monitoring

---

## API Endpoints

### `GET /`
Serves the main visualization interface

### `GET /api/topology`
Returns network topology data in Cytoscape.js format

**Response Format:**
```json
{
  "nodes": [
    {
      "data": {
        "id": "mgmt1",
        "label": "mgmt1",
        "type": "pi",
        "ip": "192.168.4.150",
        "status": "online",
        "parent": "cat_infrastructure"
      }
    },
    {
      "data": {
        "id": "cat_infrastructure",
        "label": "INFRASTRUCTURE",
        "isParent": true
      }
    }
  ],
  "edges": [
    {
      "data": {
        "source": "mgmt1",
        "target": "eero-router",
        "type": "ethernet"
      }
    }
  ]
}
```

---

## Customization

### Adding New Device Types

Edit `client/index.html`:

1. **Add SVG icon** to the `icons` object:
```javascript
const icons = {
  'icon-newtype': `<svg>...</svg>`
};
```

2. **Add color styling** in Cytoscape style array:
```javascript
{
  selector: 'node[type="newtype"]',
  style: {
    'background-color': '#hex-color',
    'border-color': '#hex-color',
    'background-image': 'data:image/svg+xml;utf8,' + 
      encodeURIComponent(icons['icon-newtype'].replace(/currentColor/g, '#ffffff'))
  }
}
```

### Changing Layout Parameters

Adjust the Cose layout in `client/index.html`:

```javascript
layout: {
  name: 'cose',
  nodeRepulsion: 8000,    // Spacing between nodes
  idealEdgeLength: 150,   // Preferred edge length
  numIter: 1000,          // Layout iterations
  randomize: true         // Random initial positions
}
```

### Connection Type Colors

Modify edge styles in `client/index.html`:

```javascript
{
  selector: 'edge[type="ethernet"]',
  style: {
    'line-color': '#58a6ff',  // Blue
    'line-style': 'solid'
  }
}
```

---

## Network Topology

**Current Display: 29 Devices + 5 Category Groups**

### Infrastructure (4 devices)
- mgmt1 (192.168.4.150) - Management Pi
- dev1 (192.168.4.49) - DNS/Pi-hole
- appserv1 (192.168.4.148) - Docker workload host
- Home Assistant (192.168.4.51) - HA server

### Home Automation (9 devices)
- SmartToolbox ESP32
- SwitchBox controller
- 2× ESP32 nodes
- Chromecast
- Roku
- Garage door controller
- Smart sensors

### Network Equipment (4 devices)
- eero router (primary)
- eero mesh node
- TP-Link switch
- Network printer

### Virtual Services (1 device)
- Container service (.210)

### Other Devices (11+ devices)
- Gaming PC
- AI PC
- Dev services
- Unknown devices

---

## Development

### Project Structure

```
HomeLabViewer/
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container build config
├── client/
│   ├── index.html         # Main visualization page
│   └── lib/               # JavaScript libraries
│       ├── cytoscape.min.js
│       ├── cola.min.js
│       └── cytoscape-cola.min.js
├── README.md              # This file
├── DEPLOYMENT.md          # Production deployment guide
└── PROJECT_SUMMARY.md     # Project overview
```

### Git Workflow

```bash
# Feature development
git checkout -b feature/new-feature
git commit -am "Add new feature"
git push origin feature/new-feature

# Production deployment
git checkout master
git merge feature/new-feature
git push origin master
```

---

## Related Projects

- **[SmartLabNetOps](https://github.com/johnmknight/SmartLabNetOps)** - Network operations dashboard (data source)
- **[HA Device Atlas](https://github.com/johnmknight/ha-device-atlas)** - Home Assistant device categorization
- **[smartlab-infra](https://github.com/johnmknight/smartlab-infra)** - Docker compose infrastructure

---

## License

MIT License - See LICENSE file for details

---

## Author

**John Knight**  
Senior Program Manager | IoT & Connected Products  
[GitHub](https://github.com/johnmknight) | [LinkedIn](https://linkedin.com/in/johnmknight)

---

## Acknowledgments

- **Cytoscape.js** - Graph visualization framework
- **Tabler Icons** - SVG icon library
- **FastAPI** - Modern Python web framework
- **Home Assistant** - Device discovery and inventory
