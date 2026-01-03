import requests
import json
import time

BASE_URL = "http://localhost:8005"

def run_extreme_scenario(name, text, lang="en"):
    print(f"\n🔥 [EXTREME] {name}")
    print(f"📝 Input: '{text}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/classify",
            json={"text": text, "language": lang},
            timeout=10
        )
        if response.status_code == 200:
            res = response.json()
            print(f"✅ Classification: {res['classification']}")
            print(f"📊 Sensitivity: {res['sensitivity_level']}")
            print(f"🎯 Confidence: {res['confidence']}")
            print(f"🔍 Triggers: {res['explainability']['triggers']}")
            return res
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
    return None

def test_active_learning():
    print("\n🧠 Testing Active Learning (Self-Improvement)")
    
    # 1. Create a fake validated sample
    print("📥 Injecting fake validated labels...")
    fake_data = [
        {"text": "Special token X-99", "classification": "TECHNICAL_DATA", "id": "test-1"},
        {"text": "X-99 is a server secret", "classification": "TECHNICAL_DATA", "id": "test-2"}
    ]
    
    # We use add-pending then validate to simulate the workflow
    for item in fake_data:
        requests.post(f"{BASE_URL}/add-pending", json={"text": item["text"]})
        # We'd need the ID to validate, but for testing we can insert directly if testing the endpoint
    
    # 2. Trigger Retrain
    print("🔄 Triggering Re-training...")
    try:
        # Note: In a real test we would actually validate items in DB first
        # But for this simulation, we check if the endpoint responds
        res = requests.post(f"{BASE_URL}/retrain")
        print(f"📡 API Response: {res.json()}")
    except Exception as e:
        print(f"❌ Retrain Error: {e}")

if __name__ == "__main__":
    print("🚀 STARTING EXTREME ADVERSARIAL STRESS TESTS\n" + "="*50)
    
    # Scenario 1: Obfuscated ID (Fuzzy)
    run_extreme_scenario(
        "Obfuscated CIN (Fuzzy Matching)", 
        "Mon numero de C.I.N est : B - K - 9 9 8 8 7 7", 
        "fr"
    )
    
    # Scenario 2: Context Conflict (Financial + Medical)
    run_extreme_scenario(
        "Mixed Category Conflict", 
        "The patient needs surgery, pay the 5000 MAD to IBAN MA64 1234 5678 9012 3456 7890 1234", 
        "en"
    )
    
    # Scenario 3: Linguistic Chaos (AR/FR Mix)
    run_extreme_scenario(
        "Language Chaos (FR/AR Mix)", 
        "خبر عurgent: Le dossier du patient n° AB-123-456 est prêt.", 
        "fr"
    )

    # Scenario 4: Deep Obfuscated RIB
    run_extreme_scenario(
        "Obfuscated RIB (Bank Account)", 
        "RIB: 123.456.7890123456789012.34.56", 
        "fr"
    )
    
    test_active_learning()
    
    print("\n" + "="*50 + "\n✅ Extreme Stress Test Sequence Finished.")
