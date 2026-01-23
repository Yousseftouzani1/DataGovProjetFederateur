
import requests
import json
import time

SERVICE_URL = "http://localhost:8003/analyze"

# The USER'S TRAP INPUT
TRAP_TEXT = "CONTEXTE MAROC: Mon CIN est AB123456 et CNSS 1234567890. CONTEXTE INTERNATIONAL: Mon ID Chinois est 110101199001011234 et mon NIR Français est 1 80 05 92 012 345 67. PIEGE: Ce nombre 1234567890 n'est pas un CNSS car il manque le contexte."

def verify_trap():
    print("="*60)
    print("🪤 VERIFYING THE TRAP FIX")
    print("="*60)
    
    payload = {
        "text": TRAP_TEXT,
        "language": "fr",
        "score_threshold": 0.4
    }
    
    try:
        resp = requests.post(SERVICE_URL, json=payload)
        res = resp.json()
        detections = res["detections"]
        
        print(f"\nFound {len(detections)} detections used threshold 0.4:")
        cnss_count = 0
        trap_detected = False
        
        for d in detections:
            val = d["value"]
            etype = d["entity_type"]
            score = d["score"]
            start = d["start"]
            
            print(f"[{etype:<20}] {val:<15} (Score: {score}) @ {start}")
            
            if etype == "CNSS":
                cnss_count += 1
                if start > 150: # The Trap is typically near end (index ~183)
                    trap_detected = True
                    print("   ❌ TRAP DETECTED! (Failure)")
                else:
                    print("   ✅ Valid CNSS (Success)")
                    
        print("\n--- VERDICT ---")
        if not trap_detected:
            print("✅ SUCCESS: The Trap CNSS was NOT detected!")
        else:
            print("❌ FAILURE: The Trap CNSS WAS detected.")
            
        if cnss_count >= 1:
            print("✅ SUCCESS: The Real CNSS WAS detected.")
        else:
            print("❌ FAILURE: The Real CNSS was MISSED (Over-correction?).")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_trap()
