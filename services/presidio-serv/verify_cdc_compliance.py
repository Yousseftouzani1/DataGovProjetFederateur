import requests
import json
import time
from datetime import datetime

# Configuration
SERVICE_URL = "http://localhost:8003"
CDC_REQUIREMENTS = {
    "US-PRES-01": "Détetction CIN Marocain",
    "US-PRES-02": "Configuration Personnalisée",
    "US-PRES-03": "Anonymisation",
    "US-PRES-05": "Intégration Airflow",
    "PERF-01": "Temps de réponse < 200ms",
    "KPI-01": "Precision (CIN) > 95%",
    "KPI-02": "Recall > 85%",
    "KPI-03": "F1-Score > 87%"
}

# Test Data with Ground Truth
TEST_DATASET = [
    # True Positives (Should be detected)
    {"text": "Mon CIN est AB123456.", "expected": "CIN_MAROC", "type": "TP"},
    {"text": "CIN: S765432.", "expected": "CIN_MAROC", "type": "TP"},
    {"text": "Appelez le 0661234567.", "expected": "PHONE_MA", "type": "TP"},
    {"text": "Contact +212600000000.", "expected": "PHONE_MA", "type": "TP"},
    {"text": "IBAN: MA64000111222333444555666777.", "expected": "IBAN_MA", "type": "TP"},
    {"text": "CNSS: 1234567890.", "expected": "CNSS", "type": "TP"},
    {"text": "Passeport PX1234567 valide.", "expected": "PASSPORT_MA", "type": "TP"},
    {"text": "Permis 10/123456.", "expected": "PERMIS_MA", "type": "TP"},
    
    # False Positives (Should NOT be detected or different type)
    {"text": "Mon code promo est AB123456.", "expected": None, "type": "TN"}, # Similar structure to CIN but context differs
    {"text": "La valeur est 06612.", "expected": None, "type": "TN"}, # Too short for phone
    {"text": "Juste un nombre 1234567890 sans contexte.", "expected": None, "type": "TN"}, # CNSS needs context or strict validation
]

def calculate_metrics(results):
    tp = 0
    fp = 0
    fn = 0
    
    for res in results:
        if res["type"] == "TP":
            if res["detected"]: tp += 1
            else: fn += 1
        elif res["type"] == "TN":
            if res["detected"]: fp += 1
            # else: true negative (we don't count for these specific KPIs usually, but good for accuracy)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": precision * 100,
        "recall": recall * 100,
        "f1": f1 * 100
    }

def run_compliance_check():
    print("="*60)
    print("🛡️  PRESIDIO COMPLIANCE JUDGEMENT DAY (Tâche 3 - CDC)")
    print("="*60)
    
    # 1. Health Check
    try:
        requests.get(f"{SERVICE_URL}/health")
        print(f"✅ Service UP: {SERVICE_URL}")
    except:
        print("❌ Service DOWN")
        return

    results = []
    latencies = []

    # 2. Run Dataset
    print("\n📊 Running Performance Benchmark...")
    for item in TEST_DATASET:
        payload = {"text": item["text"], "language": "fr", "score_threshold": 0.3}
        start_t = time.time()
        resp = requests.post(f"{SERVICE_URL}/analyze", json=payload).json()
        latency = (time.time() - start_t) * 1000
        latencies.append(latency)
        
        detections = resp.get("detections", [])
        detected_types = [d["entity_type"] for d in detections]
        
        is_detected = item["expected"] in detected_types if item["expected"] else bool(detections)
        
        results.append({
            "text": item["text"],
            "expected": item["expected"],
            "type": item["type"],
            "detected": is_detected,
            "latency": latency
        })
        
        mark = "✅" if (item["type"] == "TP" and is_detected) or (item["type"] == "TN" and not is_detected) else "❌"
        # print(f"{mark} {item['text'][:30]:<30} | {int(latency)}ms | Exp: {item['expected']} -> Got: {detected_types}")

    # 3. Calculate Metrics
    metrics = calculate_metrics(results)
    avg_latency = sum(latencies) / len(latencies)
    
    print("\n📈 PERFORMANCE REPORT:")
    print(f"   Precision: {metrics['precision']:.2f}%  (Target: >95%)")
    print(f"   Recall:    {metrics['recall']:.2f}%  (Target: >85%)")
    print(f"   F1-Score:  {metrics['f1']:.2f}%  (Target: >87%)")
    print(f"   Avg Latency: {int(avg_latency)}ms   (Target: <200ms)")
    
    # 4. Airflow Integration Check (US-PRES-05)
    print("\n⚙️ Testing Airflow Integration (US-PRES-05)...")
    try:
        task_id = "test_airflow_123"
        exec_resp = requests.post(f"{SERVICE_URL}/execute", json={"task_id": task_id, "dataset_path": "/tmp/test.csv"})
        if exec_resp.status_code == 200:
            print(f"   ✅ Batch Execution Triggered (Task: {task_id})")
            
            # Poll Status
            status_resp = requests.get(f"{SERVICE_URL}/status/{task_id}")
            if status_resp.status_code == 200:
                 status = status_resp.json().get("status")
                 print(f"   ✅ Status Check Works (Status: {status})")
            else:
                 print(f"   ❌ Status Check Failed: {status_resp.status_code}")
        else:
            print(f"   ❌ Execution Trigger Failed: {exec_resp.status_code}")
    except Exception as e:
        print(f"   ❌ Airflow Test Exception: {e}")

    # Final Verdict
    print("\n" + "="*60)
    if metrics['precision'] >= 95 and metrics['recall'] >= 85 and avg_latency < 200:
        print("🏆 VERDICT: COMPLIANT WITH CDC")
    else:
        print("⚠️ VERDICT: PARTIALLY COMPLIANT (Check Metrics)")
    print("="*60)

if __name__ == "__main__":
    run_compliance_check()
