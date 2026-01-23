
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8005"

def test_health():
    print(f"\n--- Testing Health Check {BASE_URL}/health ---")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
    except Exception as e:
        print(f"Failed to connect: {e}")

def test_classify():
    print(f"\n--- Testing Classification {BASE_URL}/api/v1/classification/classify ---")
    
    # Payload matching ClassificationRequest
    payload = {
        "dataset_id": "test_ds_clean",
        "data_sample": {
            # 1. PII (Emails) - Should be detected by RuleEngine (3)
            "emails_col": ["john@example.com", "sarah@company.org", "contact@business.ma"],
            
            # 2. PII (Phones) - Should be detected by RuleEngine (3)
            "phones_col": ["0661223344", "0700112233", "0612345678"],
            
            # 3. CRITICAL (IBAN) - Should be detected by RuleEngine (5)
            # Regex expects spaces: FRXX XXXX ...
            "ibans_col": ["FR76 1234 5678 9012 3456 7890 12", "FR76 1234 5678 9012 3456 7890 12"],
            
            # 4. PUBLIC (0) - Should be detected by ML (BERT/RF)
            "public_desc": ["This is a public description of a city.", "The weather is very nice today.", "Visit Casablanca for tourism."],
            
            # 5. CONFIDENTIAL (2) - Should be detected by ML (BERT/RF)
            "confidential_doc": ["Strictly confidential internal memo.", "Budget forecast for 2026 restricted.", "Do not share this secret project."]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/classification/classify", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            pprint(response.json())
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Failed: {e}")

def test_get_config():
    print(f"\n--- Testing Get Config {BASE_URL}/api/v1/classification/config ---")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/classification/config")
        print(f"Status Code: {response.status_code}")
        pprint(response.json())
    except Exception as e:
        print(f"Failed: {e}")

def test_update_config():
    print(f"\n--- Testing Update Config {BASE_URL}/api/v1/classification/config ---")
    
    new_config = {
        "weights": {
            "RuleEngine": 4.0,
            "BertClassifier": 1.5,
            "RandomForest": 0.5
        },
        "manual_review_threshold": 0.9
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/classification/config", json=new_config)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        
        # Verify update
        print("Verifying update...")
        check = requests.get(f"{BASE_URL}/api/v1/classification/config")
        pprint(check.json())
        
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_health()
    test_get_config()
    test_classify()
    test_update_config()
