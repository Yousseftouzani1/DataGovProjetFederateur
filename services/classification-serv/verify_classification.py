
import requests
import json
import time

SERVICE_URL = "http://localhost:8005/api/v1/classification"

def verify_classification():
    print("="*60)
    print("🧠 VERIFYING CLASSIFICATION SERVICE (Tâche 5)")
    print("="*60)
    
    # Payload simulating different column types
    payload = {
        "dataset_id": "test-dataset-001",
        "data_sample": {
            "email_col": ["test@gmail.com", "contact@data.ma", "admin@site.com"], # PII (Rules should catch)
            "salary_col": [50000, 60000, 75000, 100000],  # Confidential? Or Internal? (RF stats)
            "random_public": ["Casablanca", "Rabat", "Tanger", "Fes"], # Public
            "mixed_pii": ["Mohammed", 0.5, "Ali", "Fatima"] # PII (BERT should catch context if trained)
        }
    }
    
    print("\n1. Sending Classification Request...")
    try:
        res = requests.post(f"{SERVICE_URL}/classify", json=payload)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    if res.status_code == 200:
        data = res.json()
        print("✅ Success! Response received.")
        
        results = data.get("classifications", {})
        for col, res in results.items():
            print(f"\n   Column: {col}")
            print(f"   -> Level: {res['level']} ({res['code']})")
            print(f"   -> Confidence: {res['confidence']}")
            print(f"   -> Manual Review? {res['review']}")
            print(f"   -> Sources: {res['details']}")
            
            # Simple assertive checks
            if col == "email_col" and res['code'] == "PII":
                print("      ✅ Rule Engine correctly identified PII.")
            
    else:
        print(f"❌ Error {res.status_code}: {res.text}")

if __name__ == "__main__":
    verify_classification()
