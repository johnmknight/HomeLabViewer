"""
HomeLabViewer - Network Topology Visualization
Backend API server consuming SmartLabDeviceRegistry microservice
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx
import os
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="HomeLabViewer")

# Configuration
DEVICE_REGISTRY_URL = os.getenv("DEVICE_REGISTRY_URL", "http://192.168.4.148:8150")

# Data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Pydantic models
class TagUpdate(BaseModel):
    device_id: str
    group: str

class PositionUpdate(BaseModel):
    positions: Dict[str, Dict[str, float]]  # {node_id: {x: float, y: float}}

class LayoutMode(BaseModel):
    mode: str  # "zone", "tree", "lanes", "physical"

# Serve static files
app.mount("/lib", StaticFiles(directory="client/lib"), name="lib")
app.mount("/static", StaticFiles(directory="client"), name="static")

@app.get("/")
async def root():
    """Serve the main application page"""
    return FileResponse("client/index.html")

# Helper functions for data persistence
def load_json_file(filename: str, default: Any = None) -> Any:
    """Load JSON from data directory"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json_file(filename: str, data: Any):
    """Save JSON to data directory"""
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

async def fetch_devices_from_registry() -> List[Dict]:
    """Fetch enriched devices from SmartLabDeviceRegistry microservice"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{DEVICE_REGISTRY_URL}/api/devices")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching from device registry: {e}")
        return []

@app.get("/api/topology")
async def get_topology():
    """
    Fetch devices from SmartLabDeviceRegistry and transform to Cytoscape format
    """
    # Color mapping for network types
    group_colors = {
        "Z-Wave": "#9333ea",    # Purple - Z-Wave protocol
        "Zigbee": "#10b981",    # Green - Zigbee protocol
        "WiFi": "#3b82f6",      # Blue - WiFi devices
        "Mobile": "#f59e0b",    # Orange - Phone/mobile trackers
        "Wired": "#6b7280",     # Gray - Ethernet/wired devices
        "Unknown": "#64748b"    # Slate gray - unclassified
    }
    
    # Fetch enriched devices from microservice
    devices = await fetch_devices_from_registry()
    
    # Transform to Cytoscape format
    nodes = []
    edges = []
    groups = set()
    
    # ALLOWLIST: Only include domains that represent PHYSICAL devices
    # This dramatically reduces clutter from virtual entities, scenes, automations, etc.
    physical_device_domains = {
        'light',           # Smart bulbs, LED strips
        'switch',          # Smart switches, plugs
        'climate',         # Thermostats, HVAC
        'lock',            # Smart locks
        'cover',           # Blinds, garage doors
        'fan',             # Fans
        'vacuum',          # Robot vacuums
        'camera',          # Security cameras
        'media_player',    # TVs, speakers, media devices
        'remote',          # IR remotes
        'alarm_control_panel',  # Security systems
        'device_tracker',  # Presence detection (phones, etc.)
        'sensor',          # Physical sensors only (will filter further)
        'binary_sensor'    # Physical binary sensors only (will filter further)
    }
    
    print(f"DEBUG: Total devices before filtering: {len(devices)}")
    
    for device in devices:
        domain = device.get('domain', '')
        entity_id = device.get('id', '')
        
        # ALLOWLIST: Skip anything not in physical device domains
        if domain not in physical_device_domains:
            print(f"DEBUG: Skipping {entity_id} with domain {domain}")
            continue
        
        # Additional filtering for sensors - only include physical measurement sensors
        if domain in ['sensor', 'binary_sensor']:
            # Skip virtual/system sensors
            entity_lower = entity_id.lower()
            skip_patterns = [
                'time', 'date', 'uptime', 'last_boot', 'version',
                'update', 'sun_', 'moon_', 'season', 'nordpool',
                'memory', 'cpu', 'disk', 'load', 'network',
                'battery_state', 'charging', '_ip_', 'ssid',
                'last_changed', 'last_updated', '_status'
            ]
            if any(pattern in entity_lower for pattern in skip_patterns):
                continue
        
        # Extract group (already assigned by microservice)
        group = device.get('group', 'Unassigned')
        groups.add(group)
        
        # Get color for this group
        color = group_colors.get(group, "#6b7280")  # Default to gray
        
        # Create node
        node_data = {
            "id": device['id'],
            "label": device.get('name', device['id']),
            "group": group,
            "color": color,  # Add color property
            # No parent - we'll use colors/styles to show groups instead of compound nodes
            "domain": domain,
            "state": device.get('state', 'unknown'),
            "integration": device.get('integration', ''),
            "last_changed": device.get('last_changed', ''),
            "ip": device.get('ip'),
            "manufacturer": device.get('manufacturer'),
            "model": device.get('model'),
            "group_source": device.get('group_source', ''),  # Shows how group was assigned
            "attributes": device.get('attributes', {})
        }
        
        nodes.append({"data": node_data})
    
    # Generate network topology edges
    # Strategy: Connect devices to infrastructure based on their group/network type
    
    # Find infrastructure nodes (routers, access points, network devices)
    router_ids = [n['data']['id'] for n in nodes if 'router' in n['data']['id'].lower() or n['data']['domain'] == 'device_tracker']
    ha_server_id = next((n['data']['id'] for n in nodes if 'home_assistant' in n['data']['id'].lower() or n['data']['integration'] == 'homeassistant'), None)
    
    # If we have a HA server, use it as central hub, otherwise use first router
    hub_id = ha_server_id if ha_server_id else (router_ids[0] if router_ids else None)
    
    if hub_id:
        for node in nodes:
            node_id = node['data']['id']
            node_group = node['data']['group']
            
            # Don't connect hub to itself
            if node_id == hub_id:
                continue
            
            # Connect based on network group
            if node_group in ['WiFi', 'Wired', 'Mobile']:
                # Direct connection to hub
                edges.append({
                    "data": {
                        "id": f"{hub_id}-{node_id}",
                        "source": hub_id,
                        "target": node_id
                    }
                })
            elif node_group in ['Z-Wave', 'Zigbee']:
                # These connect through their controller (usually HA server)
                if ha_server_id and node_id != ha_server_id:
                    edges.append({
                        "data": {
                            "id": f"{ha_server_id}-{node_id}",
                            "source": ha_server_id,
                            "target": node_id
                        }
                    })
    
    print(f"DEBUG: Generated {len(nodes)} nodes and {len(edges)} edges")
    return {"nodes": nodes, "edges": edges}


# Start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
