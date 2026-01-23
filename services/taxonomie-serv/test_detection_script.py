import requests
import json
import sys

# Define color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

SERVICE_URL = "http://localhost:8002"

def test_health():
    print(f"{Colors.HEADER}Testing Health Endpoint...{Colors.ENDC}")
    try:
        response = requests.get(f"{SERVICE_URL}/health")
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ Service is HEALTHY{Colors.ENDC}")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"{Colors.FAIL}❌ Service Unhealthy: {response.status_code}{Colors.ENDC}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}❌ Could not connect to {SERVICE_URL}. Is the service running?{Colors.ENDC}")
        return False

def test_analyze(description, text, language="fr"):
    print(f"\n{Colors.HEADER}Testing: {description}{Colors.ENDC}")
    print(f"Text: '{text}'")
    
    payload = {
        "text": text,
        "language": language,
        "confidence_threshold": 0.5,
        "detect_names": False
    }
    
    try:
        response = requests.post(f"{SERVICE_URL}/analyze", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            detections = result.get("detections", [])
            
            if detections:
                print(f"{Colors.GREEN}✅ Found {len(detections)} detection(s):{Colors.ENDC}")
                for det in detections:
                    sensitivity = det.get('sensitivity_level')
                    color = Colors.FAIL if sensitivity in ['critical', 'high'] else Colors.WARNING
                    print(f"  - [{color}{det['entity_type']}{Colors.ENDC}] value='{det['value']}' "
                          f"Sensitivity={sensitivity.upper()} (Score: {det['sensitivity_score']})")
            else:
                print(f"{Colors.WARNING}⚠️ No detections found.{Colors.ENDC}")
                
            return result
        else:
            print(f"{Colors.FAIL}❌ Error {response.status_code}: {response.text}{Colors.ENDC}")
            return None
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Request failed: {str(e)}{Colors.ENDC}")
        return None

if __name__ == "__main__":
    if not test_health():
        sys.exit(1)
        
    # Test Case 1: Moroccan Identity (High Impact)
    test_analyze(
        "Moroccan Identity and Contact",
        "Bonjour, mon CIN est AB123456 et mon téléphone est le 0661234567."
    )
    
    # Test Case 2: Financial Data (Critical)
    test_analyze(
        "Financial Data",
        "Voici mon RIB: 123456789012345678901234 pour le virement."
    )
    
       # Test Case 3: Email (Medium)
    test_analyze(
        "Standard Email",
        "Contactez-nous sur support@datasentinel.ma pour plus d'infos."
    )

    # Test Case 4: Arabic Text
    test_analyze(
        "Arabic Content",
         "رقم البطاقة الوطنية هو AB123456",
        "ar"
    )
