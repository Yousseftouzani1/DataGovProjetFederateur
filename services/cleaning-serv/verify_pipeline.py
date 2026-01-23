
import requests
import json
import pandas as pd
import io
import time

SERVICE_URL = "http://localhost:8004/api/v1/cleaning"

# 1. Create a messy CSV
csv_content = """id,age,salary,city
1,25,50000,Casablanca
2,30,60000,Rabat
3,35,70000,Tanger
1,25,50000,Casablanca
5,200,1000000,Marrakech
6,,55000,Fes
"""
# Issues:
# - Row 4 is duplicate of Row 1
# - Row 5 has outlier age (200) and salary (1000000)
# - Row 6 has missing age

def verify_pipeline():
    print("="*60)
    print("🧹 VERIFYING CLEANING PIPELINE (Tâche 4)")
    print("="*60)
    
    # 1. Upload
    print("\n1. Uploading messy dataset...")
    files = {'file': ('messy.csv', csv_content, 'text/csv')}
    res = requests.post(f"{SERVICE_URL}/upload", files=files)
    if res.status_code != 200:
        print(f"❌ Upload Failed: {res.text}")
        return
        
    data = res.json()
    dataset_id = data['dataset_id']
    print(f"✅ Uploaded! ID: {dataset_id}")
    print(f"   Rows: {data['rows']}, Cols: {data['columns']}")
    
    # 2. Trigger Cleaning (Auto)
    print("\n2. Triggering Cleaning Pipeline (IQR + Duplicates)...")
    payload = {
        "remove_duplicates": True,
        "remove_outliers": True,
        "handle_missing": "mean"
    }
    # Note: query params for POST? No, my router defined them as query params in Post! 
    # Let me check router... yes "dataset_id: str, remove_duplicates: bool..."
    # So I pass them as query params
    res = requests.post(
        f"{SERVICE_URL}/clean/{dataset_id}", 
        params=payload
    )
    if res.status_code != 200:
        print(f"❌ Cleaning Failed: {res.text}")
        return
        
    clean_metrics = res.json()["metrics"]
    print(f"✅ Cleaning Complete!")
    print(f"   Rows Before: {clean_metrics['rows_before']}")
    print(f"   Rows After:  {clean_metrics['rows_after']}")
    print(f"   Duplicates Removed: {clean_metrics['duplicates_removed']} (Expected: 1)")
    print(f"   Outliers Removed:   {clean_metrics['outliers_removed']} (Expected: 1 - Age 200)")
    
    if clean_metrics['duplicates_removed'] == 1 and clean_metrics['outliers_removed'] > 0:
        print("   ✅ Logic Verified: Algorithm 4 & Deduplication working.")
    else:
        print("   ⚠️ Logic Warning: Check numbers.")

    # 3. Get HTML Profile
    print("\n3. Generating HTML Profile (US-CLEAN-02)...")
    t0 = time.time()
    res = requests.get(f"{SERVICE_URL}/profile/{dataset_id}")
    t1 = time.time()
    
    if res.status_code == 200:
        if "<!doctype html>" in res.text.lower() or "<html" in res.text.lower():
            print(f"✅ HTML Report Generated! Size: {len(res.text)} bytes")
            print(f"   Time taken: {t1-t0:.2f}s (KPI < 10s for small data)")
        else:
            print("❌ Response is NOT HTML!")
    else:
        print(f"❌ Profiling Failed: {res.status_code}")

    # 4. Download CSV
    print("\n4. Downloading Cleaned CSV (US-CLEAN-04)...")
    res = requests.get(f"{SERVICE_URL}/download/{dataset_id}")
    if res.status_code == 200:
        content = res.text
        print(f"✅ Download Successful!")
        print("   Preview:")
        print(content)
        if "200" not in content and "Casablanca" in content:
             print("   ✅ Content Verified: Clean data received.")
    else:
        print(f"❌ Download Failed: {res.status_code}")

if __name__ == "__main__":
    # Wait for service to warm up
    print("Waiting 5s for service to start...")
    time.sleep(5) 
    try:
        verify_pipeline()
    except Exception as e:
        print(f"Script Error: {e}")
