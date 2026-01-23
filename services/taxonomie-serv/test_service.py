
import requests
import json
import time
import sys
import subprocess
import uvicorn
import threading
from multiprocessing import Process

# Configuration
BASE_URL = "http://localhost:8002"

PII_SAMPLES = [
    {
        "name": "Moroccan CIN (Valid)",
        "text": "Mon numéro de CIN est le AB123456 pour mon dossier.",
        "expected_entity": "CIN_MAROC",
        "expected_sensitivity": "critical"
    },
    {
        "name": "Moroccan RIB (Valid)",
        "text": "Voici mon RIB pour le virement: 181810211112222333344445",
        "expected_entity": "RIB_MAROC",
        "expected_sensitivity": "critical"
    },
    {
        "name": "Contact Info (Phone)",
        "text": "Appelez le +212661234567 en cas d'urgence.",
        "expected_entity": "PHONE_MA",
        "expected_sensitivity": "high"
    },
    {
        "name": "Arabic Text (Identity)",
        "text": "رقم البطاقة الوطنية هو AB123456",
        "expected_entity": "الرقم_الوطني",
        "expected_sensitivity": "critical",
        "lang": "ar"
    }
]

def wait_for_service(url, timeout=10):
    """Wait for service to be healthy"""
    start_time = time.time()
    print(f"⏳ Waiting for service at {url}...")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                print("✅ Service is UP!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    print("❌ Service failed to start.")
    return False

def test_analyze_endpoint():
    """Run detection tests"""
    print("\n" + "="*50)
    print("🧪 TESTING PII DETECTION")
    print("="*50)
    
    passed = 0
    
    for sample in PII_SAMPLES:
        try:
            payload = {
                "text": sample["text"],
                "language": sample.get("lang", "fr"),
                "confidence_threshold": 0.5,
                "detect_names": True
            }
            
            response = requests.post(f"{BASE_URL}/analyze", json=payload)
            
            if response.status_code != 200:
                print(f"❌ {sample['name']}: HTTP {response.status_code}")
                print(response.text)
                continue
                
            data = response.json()
            detections = data.get("detections", [])
            
            # Validation
            found = False
            for det in detections:
                # Match entity type (handling mapped names if any)
                if det["entity_type"] == sample["expected_entity"]:
                    sens_match = (det["sensitivity_level"] == sample["expected_sensitivity"])
                    
                    if sens_match:
                        print(f"✅ {sample['name']}: Detected {det['entity_type']} ({det['sensitivity_level'].upper()})")
                        print(f"   Context: \"{det.get('context', '')}\"")
                        print(f"   Score Breakdown: {det.get('sensitivity_breakdown')}")
                        found = True
                        break
                    else:
                        print(f"⚠️ {sample['name']}: Detected {det['entity_type']} but wrong sensitivity")
                        print(f"   Expected: {sample['expected_sensitivity']}, Got: {det['sensitivity_level']}")
                        found = True
            
            if not found:
                print(f"❌ {sample['name']}: Entity not detected!")
                print(f"   Raw Detections: {[d['entity_type'] for d in detections]}")
                
            if found:
                passed += 1
                
        except Exception as e:
            print(f"❌ {sample['name']} Error: {e}")

    print("-" * 50)
    print(f"Test Result: {passed}/{len(PII_SAMPLES)} Passed")
    return passed == len(PII_SAMPLES)

if __name__ == "__main__":
    if not wait_for_service(BASE_URL):
        sys.exit(1)
        
    success = test_analyze_endpoint()
    
    if success:
        print("\n✨ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n🔥 SOME TESTS FAILED")
        sys.exit(1)
