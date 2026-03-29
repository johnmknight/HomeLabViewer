"""
HomeLabViewer - Network Topology Visualization
Backend API server using FastAPI
"""
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import httpx
import os
from typing import Dict, List
import asyncio
import json

app = FastAPI(title="HomeLabViewer")

# Configuration
HA_URL = os.getenv("HA_URL", "http://192.168.4.51:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

# Serve static files
app.mount("/lib", StaticFiles(directory="client/lib"), name="lib")
app.mount("/static", StaticFiles(directory="client"), name="static")

@app.get("/")
async def root():
    """Serve the main application page"""
    return FileResponse("client/index.html")

async def fetch_ha_topology():
    """
    Fetch complete network topology from SmartLabNetOps API
    The API already returns Cytoscape.js format, so we just pass it through
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://192.168.4.150:8096/api/topology")
            response.raise_for_status()
            data = response.json()
        
        # API already returns Cytoscape.js format with nodes/edges
        # Just return it as-is
        return data
        
    except Exception as e:
        # Fallback to minimal topology if API fails
        print(f"Error fetching topology: {e}")
        return {
            "nodes": [
                {"data": {"id": "error", "label": f"API Error: {str(e)}", "type": "error", "size": 60}}
            ],
            "edges": []
        }
        connection_types = data.get("connection_types", {})
        
        # Transform devices into Cytoscape.js format
        nodes = []
        edges = []
        router_id = None
        
        # Color mapping based on device type/category
        color_map = {
            "router": "#a855f7",      # Purple
            "switch": "#22c55e",       # Green
            "raspberry-pi": "#06b6d4", # Cyan
            "streaming": "#f97316",    # Orange
            "esp32": "#eab308",        # Yellow
            "homeassistant": "#ec4899",# Pink
            "container": "#6b7280",    # Gray
            "default": "#3b82f6"       # Blue
        }
        
        for device in devices:
            # Determine node color and size
            device_type = device.get("type", "unknown")
            category = device.get("category", "")
            icon = device.get("icon", "")
            
            # Size based on importance
            size = 60
            if device_type == "router":
                size = 70
                router_id = device["id"]
            elif "switch" in device.get("name", "").lower() or category == "network":
                size = 80
            
            # Color based on type
            color = color_map.get("default")
            if device_type == "router":
                color = color_map["router"]
            elif "switch" in device.get("name", "").lower():
                color = color_map["switch"]
            elif icon == "icon-pi" or "raspberry" in device.get("model", "").lower():
                color = color_map["raspberry-pi"]
            elif icon == "icon-streaming":
                color = color_map["streaming"]
            elif icon == "icon-esp32":
                color = color_map["esp32"]
            elif icon == "icon-homeassistant":
                color = color_map["homeassistant"]
            elif icon == "icon-container":
                color = color_map["container"]
            
            nodes.append({
                "data": {
                    "id": device["id"],
                    "label": device["name"],
                    "ip": device.get("ip", ""),
                    "type": device_type,
                    "category": category,
                    "icon": icon,
                    "status": device.get("status", "unknown"),
                    "connection_type": device.get("connection_type", "unknown"),
                    "manufacturer": device.get("manufacturer", ""),
                    "model": device.get("model", ""),
                    "color": color,
                    "size": size
                }
            })
            
            # Create edge to router or switch (find the hub)
            # Most devices connect to either router or switch
            conn_type = device.get("connection_type", "unknown")
            if device_type != "router" and device_type != "switch":
                # Find the switch or router to connect to
                target_id = None
                for other in devices:
                    if "switch" in other.get("name", "").lower():
                        target_id = other["id"]
                        break
                
                if not target_id and router_id:
                    target_id = router_id
                
                if target_id:
                    edges.append({
                        "data": {
                            "source": target_id,
                            "target": device["id"],
                            "type": conn_type
                        }
                    })
            elif device_type == "switch" and router_id and device["id"] != router_id:
                # Connect switch to router
                edges.append({
                    "data": {
                        "source": router_id,
                        "target": device["id"],
                        "type": "ethernet"
                    }
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "connection_types": connection_types
        }
        
    except Exception as e:
        # Fallback to minimal topology if API fails
        print(f"Error fetching topology: {e}")
        return {
            "nodes": [
                {"data": {"id": "error", "label": f"API Error: {str(e)}", "type": "error", "color": "#ef4444", "size": 60}}
            ],
            "edges": [],
            "connection_types": {}
        }

@app.get("/api/topology")
async def get_topology():
    """
    Fetch network topology and convert to Cytoscape.js format
    Returns nodes and edges for visualization
    """
    topology = await fetch_ha_topology()
    return topology

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
