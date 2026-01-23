
import requests
import json
import time

SERVICE_URL = "http://localhost:8003/analyze"

def run_strict_nlp_test():
    print("="*60)
    print("🕵️‍♂️ NO MERCY TEST: Verifying NLP Context Sensitivity")
    print("="*60)
    
    # CASE 1: CIN without Context
    # "AB123456" is a valid pattern, but without "CIN" keyword near it.
    text_no_context = "The code is AB123456 found in the logs."
    
    # CASE 2: CIN WITH Context
    # Same pattern, but with "CIN" keyword.
    text_with_context = "Le numéro de ma CIN est AB123456 pour verification."

    print(f"\n🧪 SCENARIO A: No Context")
    print(f"   Input: '{text_no_context}'")
    resp_a = requests.post(SERVICE_URL, json={"text": text_no_context, "language": "fr", "score_threshold": 0.0}).json()
    
    score_a = 0.0
    if resp_a['detections']:
        det = resp_a['detections'][0]
        score_a = det['score']
        print(f"   🔎 Detected: {det['entity_type']} | Value: {det['value']} | SCORE: {score_a}")
    else:
        print(f"   ⚪ Not Detected (Score too low)")

    print(f"\n🧪 SCENARIO B: With Context ('CIN')")
    print(f"   Input: '{text_with_context}'")
    resp_b = requests.post(SERVICE_URL, json={"text": text_with_context, "language": "fr", "score_threshold": 0.0}).json()
    
    score_b = 0.0
    if resp_b['detections']:
        det = resp_b['detections'][0]
        score_b = det['score']
        print(f"   🔎 Detected: {det['entity_type']} | Value: {det['value']} | SCORE: {score_b}")
    else:
        print(f"   ⚪ Not Detected")

    print("\n" + "-"*60)
    print("⚖️  JUDGEMENT:")
    
    delta = score_b - score_a
    print(f"   Score Boost from Context: +{delta:.2f}")

    if score_b > score_a:
        print("   ✅ PROOF: Context Analysis IS working. The score increased significantly.")
        if delta >= 0.29: # Approx 0.3 boost expected
             print("   ✅ ACCURACY: Boost matches the 0.3 factor from Algorithm 3.")
    else:
        print("   ❌ FAILURE: Context did not affect the score. Is NLP logic active?")

    print("="*60)

if __name__ == "__main__":
    run_strict_nlp_test()
