
import requests
import json
import time

SERVICE_URL = "http://localhost:8008"
DATASET_ID = "iso_25012_test_dataset"

# Mock Data with controlled defects to test ISO logic
TEST_DATA = {
    "filename": "quality_test.csv",
    "records": [
        # 1. Complete, Valid
        {"id": 1, "email": "valid@test.com", "phone": "0661123456", "age": 25, "start_date": "2023-01-01", "end_date": "2023-01-10"},
        # 2. Missing Email (Completeness issue)
        {"id": 2, "email": None, "phone": "0661123456", "age": 30, "start_date": "2023-01-01", "end_date": "2023-01-10"},
        # 3. Invalid Phone (Validity issue - Moroccan format)
        {"id": 3, "email": "test3@test.com", "phone": "12345", "age": 35, "start_date": "2023-01-01", "end_date": "2023-01-10"},
        # 4. Inconsistent Dates (Consistency issue)
        {"id": 4, "email": "test4@test.com", "phone": "0661123456", "age": 40, "start_date": "2023-02-01", "end_date": "2023-01-01"},
        # 5. Negative Age (Accuracy issue - Rule: numeric >= 0)
        {"id": 5, "email": "test5@test.com", "phone": "0661123456", "age": -5, "start_date": "2023-01-01", "end_date": "2023-01-10"},
        # 6. Duplicate (Uniqueness issue)
        {"id": 1, "email": "valid@test.com", "phone": "0661123456", "age": 25, "start_date": "2023-01-01", "end_date": "2023-01-10"},
        # 7. Old Date (Timeliness issue - assume default 365 days)
        {"id": 7, "email": "old@test.com", "phone": "0661123456", "age": 50, "start_date": "2015-01-01", "end_date": "2015-01-10"}
    ]
}

def run_tests():
    print(f"🔬 Testing Quality Service at {SERVICE_URL}")
    print("="*60)
    
    # 1. Register Dataset (Bypass fetch from cleaning-service)
    try:
        print(f"Registering dataset {DATASET_ID}...")
        resp = requests.post(f"{SERVICE_URL}/datasets/{DATASET_ID}/register", json=TEST_DATA)
        if resp.status_code == 200:
            print("✅ Dataset Registered")
        else:
            print(f"❌ Registration Failed: {resp.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Evaluate (US-QUAL-01, US-QUAL-02)
    print("\n📊 Evaluating Quality (US-QUAL-01, US-QUAL-02)...")
    config = {
        "max_age_days": 365
    }
    resp = requests.post(f"{SERVICE_URL}/evaluate/{DATASET_ID}", json=config)
    if resp.status_code != 200:
        print(f"❌ Evaluation Failed: {resp.text}")
        return
        
    report = resp.json()
    print("✅ Evaluation Successful")
    print(f"Global Score: {report['global_score']}/100")
    print(f"Grade: {report['grade']}")
    
    # Verify Dimensions
    scores = {d['dimension']: d['score'] for d in report['dimensions']}
    
    # Expected Logic Checks:
    # Records: 7
    # Completeness: 1 missing email. Total cells = 7*6=42. Non-null = 41. (41/42)*100 = 97.62
    # Accuracy: 1 negative age. Validated 7 ages. 6 valid. (6/7)*100 = 85.71
    # Consistency: 1 inconsistent date row. 7 checks. (6/7)*100 = 85.71
    # Uniqueness: 1 duplicate row. Unique=6. (6/7)*100 = 85.71
    # Validity: Email&Phone checks. 7 Emails (1 null) + 7 Phones. 
    #   - Emails: 6 valid strings, 1 null (ignored or counted?). Code: `vals.str.match`. Nulls in pandas become NaN/False or ignored. Logic said `vals = df[col].astype(str)`. None becomes "None". "None" regex match email? No.
    #   - Phones: 1 invalid ("12345"). 
    #   Let's see actual results.
    
    print("\nDIMENSIONS BREAKDOWN:")
    for dim, score in scores.items():
        print(f"  - {dim.ljust(15)}: {score}%")
    
    # 3. Recommendations (US-QUAL-05)
    print(f"\n💡 Recommendations (US-QUAL-05):")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    if len(report['recommendations']) > 0:
        print("✅ Recommendations Generated")
        
    # 4. PDF Export (US-QUAL-06)
    print("\n📄 Testing PDF Export (US-QUAL-06)...")
    resp = requests.get(f"{SERVICE_URL}/report/{DATASET_ID}/pdf")
    if resp.status_code == 200 and resp.headers.get("content-type") == "application/pdf":
        print("✅ PDF Export Successful (bytes received)")
    else:
        print(f"❌ PDF Export Failed: {resp.status_code}")

if __name__ == "__main__":
    run_tests()
