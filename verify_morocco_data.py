
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8006"

def verify_row(label, row_data):
    print(f"\n{'='*60}")
    print(f"🇲🇦  VERIFYING MOROCCO DATA: {label}")
    print(f"📝 Input: {json.dumps(row_data, indent=2, ensure_ascii=False)}")
    print(f"{'-'*60}")
    
    # 1. Detect
    resp_detect = requests.post(f"{BASE_URL}/detect", json={"row": row_data, "dataset_id": "DATAGOV_MOROCCO_FULL"})
    detect_data = resp_detect.json()
    print(f"🔍 DETECTED ({detect_data['count']}):")
    for inc in detect_data['inconsistencies']:
        print(f"   - [{inc['type']}] Field '{inc['field']}': {inc['message']}")
        
    # 2. Correct
    resp_correct = requests.post(f"{BASE_URL}/correct", json={"row": row_data, "dataset_id": "DATAGOV_MOROCCO_FULL", "auto_apply": True})
    correct_data = resp_correct.json()
    
    print(f"\n✨ CORRECTIONS:")
    if not correct_data['corrections']:
        print("   (No corrections suggested)")
    
    for c in correct_data['corrections']:
        status = "✅ AUTO-FIXED" if c['auto'] else "⚠️  SUGGESTION"
        print(f"   {status} '{c['field']}': '{c['old_value']}' -> '{c['new_value']}'")
        print(f"      Confidence: {c['confidence']} | Source: {c['source']}")

# Row 9: Invalid Date (June 31 doesn't exist) + Short RIB
row_9_samira = {
    "id": 8,
    "full_name": "Samira El Alaoui",
    "rib_ma": "MA64088007850033445566", # Looks short/invalid
    "phone_ma": "+212661778899",
    "salary_mad": 19500,
    "birth_date": "31/06/1987", # INVALID DATE
    "city": "Kenitra"
}

# Row 14: Text Phone + Zero Salary
row_14_khalid = {
    "id": 13,
    "full_name": "Khalid El Fassi",
    "phone_ma": "zero six cent vingt", # Text instead of number
    "salary_mad": 0,
    "email": "kef@email.ma"
}

if __name__ == "__main__":
    verify_row("Row 9: Invalid Date (31/06) & RIB", row_9_samira)
    verify_row("Row 14: Text Phone & Zero Salary", row_14_khalid)
