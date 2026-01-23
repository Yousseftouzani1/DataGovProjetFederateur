
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8006"

def verify_row(label, row_data):
    print(f"\n{'='*60}")
    print(f"🕵️  VERIFYING: {label}")
    print(f"📝 Input: {json.dumps(row_data, indent=2, ensure_ascii=False)}")
    print(f"{'-'*60}")
    
    # 1. Detect
    resp_detect = requests.post(f"{BASE_URL}/detect", json={"row": row_data, "dataset_id": "DATAGOV_INTERNATIONAL"})
    detect_data = resp_detect.json()
    print(f"🔍 DETECTED ({detect_data['count']}):")
    for inc in detect_data['inconsistencies']:
        print(f"   - [{inc['type']}] Field '{inc['field']}': {inc['message']}")
        
    # 2. Correct
    resp_correct = requests.post(f"{BASE_URL}/correct", json={"row": row_data, "dataset_id": "DATAGOV_INTERNATIONAL", "auto_apply": True})
    correct_data = resp_correct.json()
    
    print(f"\n✨ CORRECTIONS:")
    if not correct_data['corrections']:
        print("   (No corrections suggested)")
    
    for c in correct_data['corrections']:
        status = "✅ AUTO-FIXED" if c['auto'] else "⚠️  SUGGESTION"
        print(f"   {status} '{c['field']}': '{c['old_value']}' -> '{c['new_value']}'")
        print(f"      Confidence: {c['confidence']} | Source: {c['source']}")

# Defined from reading the CSV
row_8_zhao = {
    "id": 7,
    "full_name": "Zhao Xiaolong",
    "bank_account": "INVALID_BANK_NUMBER",
    "salary": 19000,
    "email": "xiaolong@tech.cn",
    "country": "China"
}

row_10_huang = {
    "id": 9,
    "full_name": "Huang Lina",
    "salary": 0,
    "email": "lina.h@email.cn",
    "status": "待审核" 
}

if __name__ == "__main__":
    verify_row("Row 8: Invalid Bank Account", row_8_zhao)
    verify_row("Row 10: Zero Salary (Statistical)", row_10_huang)
