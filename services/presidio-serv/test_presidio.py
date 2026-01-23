import requests
import json
import sys

# Color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

SERVICE_URL = "http://localhost:8003"

def test_health():
    print(f"{Colors.HEADER}Testing Health...{Colors.ENDC}")
    try:
        response = requests.get(f"{SERVICE_URL}/health")
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ Service Healthy{Colors.ENDC}")
            print(json.dumps(response.json(), indent=2))
            return True
        return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Connection failed: {e}{Colors.ENDC}")
        return False

def test_analyze(name, text, language="fr"):
    print(f"\n{Colors.HEADER}Testing Analysis: {name}{Colors.ENDC}")
    print(f"Text: '{text}'")
    
    payload = {
        "text": text,
        "language": language,
        "score_threshold": 0.4
    }
    
    try:
        response = requests.post(f"{SERVICE_URL}/analyze", json=payload)
        if response.status_code == 200:
            res = response.json()
            detections = res.get("detections", [])
            if detections:
                print(f"{Colors.GREEN}✅ Detected {len(detections)} entities:{Colors.ENDC}")
                for d in detections:
                    print(f"  - [{d['entity_type']}] '{d['value']}' (Score: {d['score']})")
            else:
                print(f"{Colors.WARNING}⚠️ No detections.{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Error {response.status_code}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")

def test_anonymize(name, text):
    print(f"\n{Colors.HEADER}Testing Anonymization: {name}{Colors.ENDC}")
    
    payload = {
        "text": text,
        "language": "fr",
        "operators": {
            "CIN_MAROC": {"type": "replace", "new_value": "<CIN_MASKED>"},
            "PHONE_NUMBER": {"type": "mask", "masking_char": "*", "chars_to_ignore": 4, "from_end": True}
        }
    }
    
    try:
        response = requests.post(f"{SERVICE_URL}/anonymize", json=payload)
        if response.status_code == 200:
            res = response.json()
            print(f"Original:   {res['original_text']}")
            print(f"Anonymized: {Colors.BLUE}{res['anonymized_text']}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Error {response.status_code}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")

if __name__ == "__main__":
    if test_health():
        # Case 1: Moroccan Identity
        test_analyze("Moroccan ID", "Mon CIN est AB123456 et mon passeport est 1234567AB.")
        
        # Case 2: Moroccan Phone
        test_analyze("Moroccan Phone", "Appelez le 0661234567 ou le +212600000000.")
        
        # Case 3: International PII
        test_analyze("Crypto & Email", "My bitcoin wallet is 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 and email is test@google.com", "en")
        
        # Case 4: CNSS
        test_analyze("CNSS", "Mon numéro CNSS est le 1234567890.")
        
        # Case 5: Anonymization
        test_anonymize("Redaction", "Le CIN AB123456 appartient à Mr. X sur le 0661234567.")
