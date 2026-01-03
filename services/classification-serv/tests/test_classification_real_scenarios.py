import requests
import json
import uuid

BASE_URL = "http://localhost:8005"

def run_scenario(name, text, language="en"):
    print(f"\n🚀 Running Scenario: {name}")
    print(f"📝 Input: '{text}' (Lang: {language})")
    
    payload = {
        "text": text,
        "language": language,
        "use_ml": True,
        "model": "ensemble"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/classify", json=payload)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Classification: {result['classification']}")
        print(f"📊 Sensitivity: {result['sensitivity_level']}")
        print(f"🎯 Confidence: {result['confidence']}")
        print(f"🔍 Triggers: {result['explainability']['triggers']}")
        
        # Check if it should be pending (simulated low confidence check)
        if result['confidence'] < 0.6:
            print("⚠️ Low confidence detected. Adding to pending for review...")
            pending_resp = requests.post(f"{BASE_URL}/add-pending", json=payload)
            print(f"📥 Added to pending. ID: {pending_resp.json().get('classification_id')}")
            
        return result
    except Exception as e:
        print(f"❌ Error in scenario {name}: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Starting Stress Tests for Classification Intelligence...")
    
    # 1. Displaced Identifier (CIN in Phone field context)
    run_scenario(
        "Displaced Identifier",
        "My phone number is BK123456 call me soon",
        "en"
    )
    
    # 2. Semantic Detection (FR - Medical context without keywords)
    run_scenario(
        "Semantic Medical Detection (FR)",
        "Le patient présente une toux sèche et une forte fièvre depuis trois jours.",
        "fr"
    )
    
    # 3. Mixed Language Noise (Arabic/French)
    run_scenario(
        "Mixed Language Financial",
        "يرجى العلم أن mon nouveau salaire est 15000 MAD",
        "ar"
    )
    
    # 4. Ambiguous / Low Confidence (Generic text)
    run_scenario(
        "Ambiguous Content",
        "We are planning a trip to the mountains next summer.",
        "en"
    )
    
    # 5. Misplaced Identity in Arabic
    run_scenario(
        "Arabic Misplaced ID",
        "اسمي خالد ورقم هاتفي هو AB998877",
        "ar"
    )
    
    print("\n✅ Stress Testing Sequence Completed.")
