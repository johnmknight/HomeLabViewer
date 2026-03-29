"""
HomeLabViewer - Network Topology Visualization
Backend API server with Home Assistant integration
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
import asyncio

app = FastAPI(title="HomeLabViewer")

# Configuration
HA_URL = os.getenv("HA_URL", "http://192.168.4.51:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjZDM0Zjk5OWFhNjA0YjhkYjkzZWI0ZWQ3OGIwNzFhOCIsImlhdCI6MTc3NDQ4MTEzNCwiZXhwIjoyMDg5ODQxMTM0fQ.1HFOqDQfgpB7e5DhEJZOne3rYynxMmn1CuefQDJ7W4k")

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

async def fetch_ha_states() -> List[Dict]:
    """Fetch all entity states from Home Assistant"""
    if not HA_TOKEN:
        return []
    
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{HA_URL}/api/states", headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching HA states: {e}")
        return []

def assign_device_group(device: Dict, manual_tags: Dict, areas: Dict) -> str:
    """
    Assign group using priority stack:
    1. Manual tag override
    2. HA area
    3. HA domain/integration
    4. IP subnet
    5. Unassigned
    """
    device_id = device.get('entity_id', '')
    
    # Priority 1: Manual tag override
    if device_id in manual_tags:
        return manual_tags[device_id]
    
    # Priority 2: HA area
    area_id = device.get('attributes', {}).get('area_id')
    if area_id and area_id in areas:
        return areas[area_id]
    
    # Priority 3: HA domain/integration inference
    domain = device_id.split('.')[0] if '.' in device_id else ''
    integration = device.get('attributes', {}).get('integration', '').lower()
    
    if domain in ['update', 'sensor'] and any(x in device_id for x in ['hassio', 'homeassistant']):
        return 'Management'
    if integration in ['esphome', 'mqtt', 'zigbee', 'zwave'] or domain in ['light', 'switch']:
        return 'IoT'
    if domain in ['device_tracker'] or 'router' in device_id.lower():
        return 'Networking'
    
    # Priority 4: IP subnet (if IP available)
    # Would need to parse IPs from attributes - simplified for now
    
    # Priority 5: Unassigned fallback
    return 'Unassigned'

@app.get("/api/topology")
async def get_topology():
    """
    Fetch Home Assistant devices and return enriched topology
    with group assignments
    """
    # Fetch HA data
    states = await fetch_ha_states()
    
    # Load manual tags and areas
    manual_tags = load_json_file("tags.json", {})
    areas = {}  # Would fetch from HA areas API in full implementation
    
    # Transform to Cytoscape format
    nodes = []
    edges = []
    groups = set()
    
    for entity in states:
        entity_id = entity.get('entity_id', '')
        
        # Filter to relevant device types (skip pure update entities)
        domain = entity_id.split('.')[0] if '.' in entity_id else ''
        if domain == 'update':
            continue
            
        # Assign group
        group = assign_device_group(entity, manual_tags, areas)
        groups.add(group)
        
        # Create node
        node_data = {
            "id": entity_id,
            "label": entity.get('attributes', {}).get('friendly_name', entity_id),
            "group": group,
            "parent": f"group_{group}",  # Compound node parent
            "domain": domain,
            "state": entity.get('state', 'unknown'),
            "integration": entity.get('attributes', {}).get('integration', ''),
            "last_changed": entity.get('last_changed', ''),
            "attributes": entity.get('attributes', {})
        }
        
        nodes.append({"data": node_data})
    
    # Create group/parent nodes
    for group_name in groups:
        nodes.append({
            "data": {
                "id": f"group_{group_name}",
                "label": group_name.upper(),
                "isParent": True
            }
        })
    
    return {"nodes": nodes, "edges": edges}

# Tag management endpoints
@app.get("/api/tags")
async def get_tags():
    """Get all manual tag overrides"""
    return load_json_file("tags.json", {})

@app.post("/api/tags")
async def save_tag(tag: TagUpdate):
    """Save a manual tag override"""
    tags = load_json_file("tags.json", {})
    tags[tag.device_id] = tag.group
    save_json_file("tags.json", tags)
    return {"status": "saved", "device_id": tag.device_id, "group": tag.group}

# Position management endpoints (per layout mode)
@app.get("/api/positions/{mode}")
async def get_positions(mode: str):
    """Get saved node positions for a specific layout mode"""
    filename = f"positions_{mode}.json"
    return load_json_file(filename, {})

@app.post("/api/positions/{mode}")
async def save_positions(mode: str, update: PositionUpdate):
    """Save node positions for a specific layout mode"""
    filename = f"positions_{mode}.json"
    save_json_file(filename, update.positions)
    return {"status": "saved", "mode": mode, "count": len(update.positions)}

# Layout mode management
@app.get("/api/layout")
async def get_layout_mode():
    """Get last selected layout mode"""
    layout_data = load_json_file("layout.json", {"mode": "zone"})
    return layout_data

@app.post("/api/layout")
async def save_layout_mode(layout: LayoutMode):
    """Save selected layout mode"""
    save_json_file("layout.json", {"mode": layout.mode, "updated": datetime.now().isoformat()})
    return {"status": "saved", "mode": layout.mode}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
