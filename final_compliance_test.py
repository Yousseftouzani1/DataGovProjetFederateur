import requests
import json

BASE_URL = "http://localhost:8002"

def audit_case(name, text, language="fr"):
    print(f"\n--- AUDIT CASE: {name} ---")
    payload = {"text": text, "language": language}
    try:
        resp = requests.post(f"{BASE_URL}/analyze", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Text: {text}")
            print(f"Detections: {len(data['detections'])}")
            for d in data['detections']:
                print(f"  - [{d['entity_type']}] Conf: {d['confidence_score']} | Score: {d['sensitivity_score']} | Level: {d['sensitivity_level'].upper()}")
                print(f"    Reason: {d.get('analysis_explanation', 'N/A')}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # Case 1: Complex Moroccan Financial (Algorithm 2 & S_total)
    audit_case("Moroccan Financial SPI", 
               "ALERTE: Virement suspect détecté. RIB: MA640011223344556677889900. Code PIN requis: 1234.")

    # Case 2: Arabic PII (Tâche 2 Compliance)
    audit_case("Arabic Identity", 
               "رقم البطاقة الوطنية هو AB123456 لغرض التحقق من الهوية", "ar")

    # Case 3: Mixed Identity (Algorithm 2 Context)
    audit_case("Mixed Context Identity", 
               "Le CIN du client (رقم البطاقة الوطنية) est CD998877.")

    # Case 4: International Strict Mode (Presidio Tâche 3)
    # Note: Using localhost:8003 for Presidio Audit
    audit_case("Presidio International", 
               "Japanese contact: +81-3-1234-5678 vs Random noise: 1234567890", "en")
