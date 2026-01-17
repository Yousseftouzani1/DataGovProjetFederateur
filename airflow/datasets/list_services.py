import requests
import json

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")

def list_services():
    try:
        url = f"{RANGER_URL}/service/plugins/services"
        resp = requests.get(url, auth=RANGER_AUTH)
        data = resp.json()
        
        print(f"Total Services: {data.get('totalCount')}")
        for s in data.get('services', []):
            print(f" - Name: {s['name']:<20} | Type: {s['type']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_services()
