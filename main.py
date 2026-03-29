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
    # Color mapping for groups
    group_colors = {
        "Management": "#f59e0b",  # Orange
        "IoT": "#10b981",         # Green
        "Networking": "#3b82f6",  # Blue
        "Compute": "#8b5cf6",     # Purple
        "Unassigned": "#6b7280"   # Gray
    }
    
    # Fetch enriched devices from microservice
    devices = await fetch_devices_from_registry()
    
    # Transform to Cytoscape format
    nodes = []
    edges = []
    groups = set()
    
    for device in devices:
        # Filter to relevant device types (skip pure update entities)
        domain = device.get('domain', '')
        if domain == 'update':
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
    
    return {"nodes": nodes, "edges": edges}
