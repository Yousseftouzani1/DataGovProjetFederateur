import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8004"

def test_full_pipeline():
    print("🚀 Starting Cleaning Service Verification...")
    
    # 1. Check health
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"✅ Service health: {resp.json()}")
    except:
        print("❌ Service not running. Start it first with uvicorn.")
        return

    # 2. Prepare Sample Data
    data = {
        "id": [1, 2, 2, 3, 4, 100],
        "val": [10.0, 20.0, 20.0, None, 15.0, 1000.0],
        "cat": [" A ", "b", "b", "c", "D", "e"]
    }
    import pandas as pd
    df = pd.DataFrame(data)
    csv_buf = df.to_csv(index=False).encode('utf-8')
    
    # 3. Upload File
    files = {"file": ("test_dirty.csv", csv_buf, "text/csv")}
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    dataset_id = resp.json()["dataset_id"]
    print(f"✅ Uploaded dataset. ID: {dataset_id}")

    # 4. Generate Profiling Report
    print("📋 Generating Profiling Report...")
    resp = requests.get(f"{BASE_URL}/profile/{dataset_id}")
    profile_data = resp.json()
    print(f"✅ Profiling Metadata: {json.dumps(profile_data['metrics'], indent=2)}")
    print(f"🔗 View Report: {BASE_URL}{profile_data['report_url']}")

    # 5. Run Cleaning with Validation Rules
    print("🧹 Running Cleaning with Validation...")
    config = {
        "missing_strategy": "mean",
        "iqr_multiplier": 1.5,
        "validation_rules": {
            "val": {"min": 0, "max": 500} # Rules to catch 1000.0 if IQR missed it
        }
    }
    resp = requests.post(f"{BASE_URL}/clean/{dataset_id}", json=config)
    clean_data = resp.json()
    print(f"✅ Cleaning Result: success={clean_data['success']}, cdc_compliant={clean_data['cdc_compliant']}")
    print(f"🔗 Summary Report: {BASE_URL}{clean_data['summary_report_url']}")

    # 6. Verify Summary Report (HTML)
    print("📝 Verifying Summary Report content...")
    resp = requests.get(f"{BASE_URL}{clean_data['summary_report_url']}")
    if "CDC COMPLIANT" in resp.text:
        print("✅ HTML Report contains CDC COMPLIANT badge!")
    else:
        print("❌ HTML Report missing compliance badge.")

    print("\n🎉 Full Pipeline Verification Complete!")

if __name__ == "__main__":
    test_full_pipeline()
