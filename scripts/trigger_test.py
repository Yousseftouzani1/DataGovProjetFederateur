
import requests
import json
import sys

# Define payload for MASTER_DATAGOVY.csv (which matches the user's file)
payload = {
    "dataset_id": "MASTER_DATAGOV.csv",
    "dataset_name": "MASTER_DATAGOV.csv",
    "detections": [
        {
            "entity_type": "PHONE_MA", 
            "score": 0.95, 
            "start": 0, 
            "end": 10, 
            "value": "0600112233",
            "column": "PHONE_NUM",
            "context": {
                "text": "Call me at 0600112233 immediately.",
                "snippet": "Call me at 0600112233 immediately.",
                "full_structure": "Raw Text"
            }
        },
        {
            "entity_type": "CIN_MA",
            "score": 0.99,
            "start": 20,
            "end": 28,
            "value": "AB123456",
            "context": {
                "text": "ID: AB123456",
                "snippet": "ID: AB123456",
                "full_structure": "Raw Text"
            }
        }
    ]
}

try:
    print("🚀 Sending trace request to cleaning-service...")
    resp = requests.post("http://localhost:8004/trigger-pipeline", json=payload, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print("Response:")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"❌ Error: {e}")
