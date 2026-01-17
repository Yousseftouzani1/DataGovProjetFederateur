import requests
import sys

url = "http://annotation-service:8007/tasks"
params = {"status": "completed", "limit": 200}

try:
    print(f"Connecting to {url}...")
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    tasks = data.get("tasks", [])
    print(f"Status Code: {resp.status_code}")
    print(f"Total Tasks: {data.get('total')}")
    print(f"Tasks in Response: {len(tasks)}")
    
    if len(tasks) > 0:
        print("First Task ID:", tasks[0].get("id"))
        print("First Task Status:", tasks[0].get("status"))
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    sys.exit(1)
