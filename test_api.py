import httpx
import json

try:
    response = httpx.get('http://192.168.4.150:8096/api/topology', timeout=5.0)
    print(f'Status: {response.status_code}')
    data = response.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {e}')
