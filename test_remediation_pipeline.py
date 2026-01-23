
import requests
import time
import pandas as pd
import io

BASE_URL_CLEANING = "http://localhost:8004/api/v1/cleaning"
BASE_URL_QUALITY = "http://localhost:8008"

def test_pipeline_integration():
    print("🚀 Starting Remediation Integration Test...")

    # 1. Create a Synthetic CSV with PII
    print("\n[Step 1] Creating Synthetic CSV with PII...")
    csv_content = """id,name,email,phone,salary
1,Mohammed Alami,alami@gmail.com,0661234567,15000
2,Fatima B.,fatima.b@yahoo.fr,0661112233,20000
3,John Doe,john.doe@corporate.com,+1555123456,50000
"""
    files = {'file': ('test_pii_data.csv', csv_content, 'text/csv')}

    # 2. Upload to Cleaning Service (Should trigger Presidio & Atlas)
    print("\n[Step 2] Uploading to Cleaning Service...")
    start_time = time.time()
    try:
        # Increased timeout for synchronous PII/Atlas calls
        resp = requests.post(f"{BASE_URL_CLEANING}/upload", files=files, timeout=30)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.json()}")
        
        if resp.status_code != 200:
            print("❌ Upload Failed!")
            return
            
        dataset_id = resp.json().get("dataset_id")
        pii_detected = resp.json().get("pii_detected", [])
        atlas_guid = resp.json().get("atlas_guid")
        
        print(f"✅ Upload Success! ID: {dataset_id}")
        
        # Verify PII Detection (Mocked response check if Presidio was reachable)
        # Note: In real env, this depends on Presidio response. 
        # Since we modified the code to capture PII in response, we check it.
        if pii_detected:
            print(f"✅ PII Detected by Pipeline: {pii_detected}")
        else:
            print("⚠️ No PII Detected (Check Presidio logs or content)")
            
        if atlas_guid != "mock-guid-fallback":
            print(f"✅ Atlas Registration Real GUID: {atlas_guid}")
        else:
            print("ℹ️ Atlas returned mock/fallback GUID (Expected if Atlas unavailable)")

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return

    # 3. Verify JSON Endpoint (New)
    print("\n[Step 3] Verifying New JSON Endpoint...")
    try:
        resp = requests.get(f"{BASE_URL_CLEANING}/dataset/{dataset_id}/json", timeout=5)
        if resp.status_code == 200:
             data_len = len(resp.json().get("data", []))
             print(f"✅ JSON Endpoint Works! Retrieved {data_len} records.")
        else:
             print(f"❌ JSON Endpoint Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ JSON Endpoint Error: {e}")

    # 4. Trigger Quality Evaluation (The Consumer Test)
    print("\n[Step 4] Triggering Quality Evaluation (Uses new endpoint)...")
    try:
        resp = requests.post(f"{BASE_URL_QUALITY}/evaluate/{dataset_id}", timeout=10)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            report = resp.json()
            grade = report.get("grade")
            score = report.get("global_score")
            print(f"✅ Quality Evaluation Success!")
            print(f"   Grade: {grade}")
            print(f"   Score: {score}")
        else:
            print(f"❌ Quality Evaluation Failed: {resp.text}")
            
    except Exception as e:
        print(f"❌ Quality Service Error: {e}")

if __name__ == "__main__":
    try:
        test_pipeline_integration()
    except KeyboardInterrupt:
        print("\nTest interrupted.")
