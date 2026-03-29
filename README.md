# HomeLabViewer

**Full Network Topology Visualization for Home Assistant**

HomeLabViewer provides a comprehensive visual representation of your entire network, pulling device data from Home Assistant's discovery system and displaying it with SVG icons, color-coded device types, and connection indicators (ethernet vs wireless).

![Network Topology](docs/screenshot.png)

## Features

✅ **Complete Network Visibility**
- Displays all 29+ devices discovered by Home Assistant
- Category groupings (Infrastructure, Automation, Network, Virtual, Other)

✅ **Visual Device Icons**
- SVG Tabler icons for each device type
- Router, Raspberry Pi, Streaming, ESP32, Container icons

✅ **Color-Coded Devices**
- Purple - Routers (eero)
- Cyan - Raspberry Pis (mgmt1, dev1, appserv1, Home Assistant)
- Orange - Streaming devices (Chromecast, Roku)
- Yellow - ESP32 microcontrollers
- Gray - Virtual/Container services
- Blue - Unknown/Other devices

✅ **Connection Type Visualization**
- Blue solid lines - Ethernet (wired) connections
- Orange dashed lines - Wireless (WiFi) connections
- Gray dotted lines - Virtual connections

✅ **Live Data Integration**
- Pulls from SmartLabNetOps API endpoint
- Real-time device status
- Home Assistant discovery integration

## Architecture

```
HomeLabViewer
├── client/
│   ├── index.html          # Main application (SVG icons, Cytoscape.js)
│   └── lib/                # Local JavaScript libraries (no CDN)
│       ├── cytoscape.min.js
│       ├── cola.min.js
│       └── cytoscape-cola.min.js
├── main.py                 # FastAPI backend
├── requirements.txt
├── Dockerfile
└── README.md
```

**Data Flow:**
```
Home Assistant → SmartLabNetOps API → HomeLabViewer Backend → Cytoscape.js Frontend
     (discovers devices)    (aggregates)     (passes through)      (renders topology)
```

## Technology Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Vanilla JavaScript + Cytoscape.js 3.28.1
- **Layout:** Cose force-directed algorithm
- **Data Source:** SmartLabNetOps API (`http://192.168.4.150:8096/api/topology`)
- **Icons:** SVG Tabler icons (embedded, no CDN)

## Installation

### Prerequisites
- Python 3.11+
- Access to SmartLabNetOps API endpoint
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/johnmknight/HomeLabViewer.git
   cd HomeLabViewer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```

4. **Open in browser:**
   ```
   http://localhost:8200
   ```

### Docker Deployment

1. **Build the image:**
   ```bash
   docker build -t homelabviewer:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d --name homelabviewer -p 8200:8200 homelabviewer:latest
   ```

3. **Access the application:**
   ```
   http://your-server-ip:8200
   ```

## Production Deployment

For deployment to appserv1 with nginx reverse proxy, see [DEPLOYMENT.md](DEPLOYMENT.md).

**Recommended setup:**
- **Host:** appserv1 (192.168.4.148)
- **Port:** 8200
- **Reverse Proxy:** nginx at `/homelabviewer/`
- **URL:** `http://192.168.4.148/homelabviewer/`

## Configuration

The application fetches topology data from the SmartLabNetOps API. To change the data source, update `main.py`:

```python
async def fetch_ha_topology():
    response = await client.get("http://192.168.4.150:8096/api/topology")
    # Change URL to your SmartLabNetOps instance
```

## API Endpoint

### GET /api/topology

Returns network topology in Cytoscape.js format:

```json
{
  "nodes": [
    {
      "data": {
        "id": "mgmt1",
        "label": "mgmt1 (Management Node)",
        "type": "pi",
        "ip": "192.168.4.150",
        "status": "online",
        "parent": "infrastructure",
        "isParent": false
      }
    }
  ],
  "edges": [
    {
      "data": {
        "source": "router-main",
        "target": "mgmt1",
        "type": "ethernet"
      }
    }
  ]
}
```

## Development

### Project Structure

**Backend (`main.py`):**
- FastAPI server on port 8200
- Single endpoint: `/api/topology`
- Proxies data from SmartLabNetOps API
- No data transformation (pass-through)

**Frontend (`client/index.html`):**
- Cytoscape.js initialization
- SVG icon library (6 device types)
- Category node styling (parent containers)
- Connection line styling (ethernet/wireless/virtual)
- Cose force-directed layout algorithm

### Customization

**Add new device icons:**
```javascript
const icons = {
  'icon-yourdevice': `<svg xmlns="http://www.w3.org/2000/svg" ...>
    <!-- SVG path here -->
  </svg>`
};
```

**Change color scheme:**
```javascript
{
  selector: 'node[type="pi"]',
  style: {
    'background-color': '#06b6d4',  // Change color here
    'border-color': '#22d3ee'
  }
}
```

## Related Projects

- **[SmartLabNetOps](https://github.com/johnmknight/SmartLabNetOps)** - Network operations dashboard (data source)
- **[smartlab-infra](https://github.com/johnmknight/smartlab-infra)** - Docker compose infrastructure
- **[HA Device Atlas](https://github.com/johnmknight/ha-device-atlas)** - Home Assistant device categorization

## Screenshots

**Full Network Topology:**
- 29 devices with category groupings
- Color-coded device types
- Connection type indicators

**Device Categories:**
- Infrastructure (Core) - Raspberry Pis
- Home Automation - IoT, ESP32, smart sensors
- Network Equipment - Router, mesh nodes
- Virtual Services - Containers
- Other Devices - PCs, unknown devices

## License

MIT License - see LICENSE file for details

## Author

**John M. Knight**
- GitHub: [@johnmknight](https://github.com/johnmknight)
- Project: SmartLab Home Network Visualization

## Acknowledgments

- **Cytoscape.js** - Graph visualization library
- **Tabler Icons** - SVG icon library
- **FastAPI** - Python web framework
- **Home Assistant** - Smart home platform
