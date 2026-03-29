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
    Fetch network topology from Home Assistant
    Expects HA to provide topology data via API or integration
    """
    # For now, return SmartLab production topology
    # TODO: Integrate with HA network discovery when available
    return {
        "nodes": [
            # Infrastructure
            {"data": {"id": "mgmt1", "label": "mgmt1", "type": "raspberry-pi", "ip": "192.168.4.150", "role": "management"}},
            {"data": {"id": "dev1", "label": "dev1", "type": "raspberry-pi", "ip": "192.168.4.49", "role": "dns"}},
            {"data": {"id": "appserv1", "label": "appserv1", "type": "raspberry-pi", "ip": "192.168.4.148", "role": "workload"}},
            {"data": {"id": "homeassistant", "label": "homeassistant", "type": "raspberry-pi", "ip": "192.168.4.51", "role": "automation"}},
            
            # Network
            {"data": {"id": "ugreen-switch", "label": "UGREEN CM753", "type": "switch", "ip": "192.168.4.1", "ports": "5x 2.5GbE + SFP+"}},
            {"data": {"id": "eero-router", "label": "Eero Pro 6E", "type": "router", "ip": "192.168.4.254"}},
        ],
        "edges": [
            # Pi nodes to switch
            {"data": {"source": "ugreen-switch", "target": "mgmt1", "type": "ethernet"}},
            {"data": {"source": "ugreen-switch", "target": "dev1", "type": "ethernet"}},
            {"data": {"source": "ugreen-switch", "target": "appserv1", "type": "ethernet"}},
            {"data": {"source": "ugreen-switch", "target": "homeassistant", "type": "ethernet"}},
            
            # Switch to router
            {"data": {"source": "eero-router", "target": "ugreen-switch", "type": "ethernet"}},
        ]
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
