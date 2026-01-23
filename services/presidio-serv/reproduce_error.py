import requests
import json

url = "http://localhost:8003/analyze"
payload = {
  "text": "Mon CIN est AB123456 et mon CNSS est 1234567890",
  "language": "fr",
  "entities": [
    "string"
  ],
  "score_threshold": 0.3
}

try:
    print("Sending request with valid payload but 'string' as entity...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
