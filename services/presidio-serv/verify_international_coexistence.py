
import requests
import json
import time

SERVICE_URL = "http://localhost:8003/analyze"

# The "Mega-Test" Input
MEGA_TEXT = """
=== MOROCCAN CONTEXT (Should be detected as Moroccan) ===
1. Ahmed Benali from Casablanca.
   CIN: AB123456
   Phone: 0661234567
   CNSS: 1234567890
   IBAN: MA64000111222333444555666777
   Passport: PX1234567

=== INTERNATIONAL CONTEXT (Should be detected as International) ===
2. Zhang Wei (China)
   Chinese ID: 110101199001011234
   Phone: +8613800138000

3. Pierre Dupont (France)
   Numéro Sécurité Sociale (NIR): 1 80 05 92 012 345 67
   (Checking if this is confused with CNSS which is 10 digits)

4. Hans Muller (Germany)
   Personalausweis: T220001293

5. Yoshio Tanaka (Japan)
   My Number: 123456789012
   Phone: 09012345678

6. Standard PII (Default Presidio)
   Email: test.user@example.com
   US Phone: +1-555-555-5555
   IP Address: 192.168.1.1
"""

def verify_coexistence():
    print("="*60)
    print("🌍 INTERNATIONAL vs MOROCCAN COEXISTENCE TEST")
    print("="*60)

    payload = {
        "text": MEGA_TEXT,
        "language": "fr", # Using FR as base to test multi-lingual support
        "score_threshold": 0.4
    }

    try:
        start_t = time.time()
        resp = requests.post(SERVICE_URL, json=payload)
        latency = (time.time() - start_t) * 1000

        if resp.status_code != 200:
            print(f"❌ API Error: {resp.status_code} - {resp.text}")
            return

        detections = resp.json()["detections"]
        
        # Organize results
        found_types = set()
        print(f"\n✅ Analysis Successful ({int(latency)}ms)")
        print("\n--- DETAILED FINDINGS ---")
        
        for d in detections:
            etype = d["entity_type"]
            val = d["value"]
            score = d["score"]
            found_types.add(etype)
            print(f"[{etype:<20}] {val:<30} (Score: {score})")

        print("\n--- SAFETY CHECKS ---")
        
        # 1. Check Moroccan
        if "CIN_MAROC" in found_types and "AB123456" in MEGA_TEXT:
            print("✅ Moroccan CIN detected correctly")
        else:
            print("❌ Moroccan CIN MISSED")

        if "CNSS" in found_types and "1234567890" in MEGA_TEXT:
             print("✅ Moroccan CNSS detected correctly")
        else:
             print("❌ Moroccan CNSS MISSED")

        # 2. Check International
        if "CHINESE_NATIONAL_ID" in found_types:
            print("✅ Chinese ID detected correctly")
        else:
            print("❌ Chinese ID MISSED")

        if "FRENCH_NIR" in found_types:
             print("✅ French NIR detected correctly")
        else:
             print("❌ French NIR MISSED")

        # 3. Check Confusion (Crucial)
        # Did we detect French NIR as CNSS?
        french_nir_val = "1 80 05 92 012 345 67"
        bad_cnss = [d for d in detections if d["entity_type"] == "CNSS" and d["value"] == french_nir_val]
        if not bad_cnss:
            print("✅ NO CONFUSION: French NIR was NOT flagged as Moroccan CNSS")
        else:
            print("YOUR ATTENTION PLEASE: French NIR WAS FLAGGED AS CNSS! (Confusion)")

        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    verify_coexistence()
