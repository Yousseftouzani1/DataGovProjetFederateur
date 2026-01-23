
import requests
import json
import time
from pprint import pprint

BASE_URL = "http://localhost:8006"

def test_health():
    print(f"\n{'='*50}")
    print("🏥 Testing Health Check...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Status: {resp.status_code}")
        pprint(resp.json())
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def test_detection():
    print(f"\n{'='*50}")
    print("🔍 Testing Inconsistency Detection...")
    
    # Row with multiple issues:
    # - format: invalid date
    # - domain: age 250
    # - referential: Paris in Morocco
    # - semantic: email has no @
    payload = {
        "row": {
            "id": "1",
            "date_naissance": "32/13/2024",  # Format
            "age": 250,                      # Domain
            "ville": "Paris",                # Referential mismatch
            "pays": "Maroc",
            "email": "invalid_email_at_gmail.com" # Format/Semantic
        },
        "dataset_id": "test_dataset_1"
    }
    
    resp = requests.post(f"{BASE_URL}/detect", json=payload)
    if resp.status_code == 200:
        print("✅ Detection Success:")
        data = resp.json()
        print(f"Found {data['count']} inconsistencies.")
        for inc in data['inconsistencies']:
            print(f" - [{inc['type']}] {inc['field']}: {inc['message']}")
    else:
        print(f"❌ Detection Failed: {resp.text}")

def test_correction():
    print(f"\n{'='*50}")
    print("✨ Testing Automatic Correction...")
    
    # Same row
    payload = {
        "row": {
            "id": "1",
            "date_naissance": "2024/13/32",  # Complex date
            "age": 250,
            "email": "TEST@GMAIL.COM" # Easy fix (lowercase)
        },
        "dataset_id": "test_dataset_1",
        "auto_apply": True
    }
    
    resp = requests.post(f"{BASE_URL}/correct", json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print("✅ Correction Response:")
        print(f"Auto-applied: {data['auto_applied_count']}")
        print(f"Manual Review: {data['manual_review_count']}")
        
        print("\nCorrections:")
        for c in data['corrections']:
            status = "✅ FIXED" if c['auto'] else "⚠️ REVIEW"
            print(f" {status} {c['field']}: {c['old_value']} -> {c['new_value']} (Conf: {c['confidence']})")
            
        return data['corrections']
    else:
        print(f"❌ Correction Failed: {resp.text}")
        return []

def test_validation(corrections):
    print(f"\n{'='*50}")
    print("Testing Validation Workflow...")
    
    # Find a correction that needs validation or was applied
    # We'll just validate the first one we find for demo purposes
    # In real flow, we'd fetch pending corrections
    
    # First, list pending
    resp = requests.get(f"{BASE_URL}/corrections/pending")
    pending = resp.json().get("pending_validations", [])
    print(f"Pending validations in queue: {len(pending)}")
    
    if pending:
        cid = pending[0]["_id"]
        print(f"Validating Correction ID: {cid}")
        
        payload = {
            "decision": "accept",
            "final_value": pending[0]["suggested_value"],
            "validator_id": "user_test",
            "comments": "Looks good to me"
        }
        
        resp = requests.post(f"{BASE_URL}/corrections/validate/{cid}", json=payload)
        print(f"Validation Status: {resp.status_code}")
        pprint(resp.json())
    else:
        print("No pending corrections to validate.")

if __name__ == "__main__":
    if test_health():
        test_detection()
        corrections = test_correction()
        test_validation(corrections)
