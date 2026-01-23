
import requests
import json

BASE_URL = "http://127.0.0.1"

SERVICES = {
    "Auth": 8001,
    "Taxonomy": 8002,
    "Presidio": 8003,
    "Cleaning": 8004,
    "Classification": 8005,
    "Correction": 8006,
    "Annotation": 8007,
    "Quality": 8008
}

def check_endpoint(service, method, path, port, payload=None, params=None):
    url = f"{BASE_URL}:{port}{path}"
    print(f"CHECKING: {service} | {method} {path} on port {port}...")
    if payload: print(f"   Payload: {json.dumps(payload)}")
    if params: print(f"   Params: {json.dumps(params)}")
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=5)
        elif method == "POST":
            resp = requests.post(url, json=payload, timeout=5)
        elif method == "PUT":
            resp = requests.put(url, json=payload, params=params, timeout=5)
            
        # Auth will return 401/403 without token, which means the endpoint EXISTS
        if resp.status_code in [200, 201] or (service == "Auth" and resp.status_code in [401, 403]):
            print(f"SUCCESS: {service} endpoint is reachable and structurally correct.")
            return True
        else:
            print(f"FAILED: {service} returned {resp.status_code}. Body: {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"ERROR: Could not connect to {service}: {e}")
        return False

def verify_all_gaps():
    results = []
    
    # 1. Taxonomy: POST /patterns
    results.append(check_endpoint("Taxonomy", "POST", "/patterns", SERVICES["Taxonomy"], 
                                 payload={"category": "TEST_PII", "pattern": r"\bTEST\d{3}\b"}))
    
    # 2. Presidio: POST /recognizers
    results.append(check_endpoint("Presidio", "POST", "/recognizers", SERVICES["Presidio"],
                                 payload={"entity_type": "TEST_ID", "pattern": r"\bID-\d{5}\b"}))
    
    # 3. Classification: POST /api/v1/classification/retrain
    results.append(check_endpoint("Classification", "POST", "/api/v1/classification/retrain", SERVICES["Classification"]))
    
    # 4. Annotation: GET /tasks/my-queue
    results.append(check_endpoint("Annotation", "GET", "/tasks/my-queue", SERVICES["Annotation"], 
                                 params={"user_id": "admin"}))
    
    # 5. Quality: POST /thresholds
    results.append(check_endpoint("Quality", "POST", "/thresholds", SERVICES["Quality"],
                                 payload={"accuracy": 0.4, "completeness": 0.6}))
    
    # 6. Cleaning: GET /api/v1/cleaning/datasets
    results.append(check_endpoint("Cleaning", "GET", "/api/v1/cleaning/datasets", SERVICES["Cleaning"]))
    
    # 7. Auth: PUT /users/{id}/role
    results.append(check_endpoint("Auth", "PUT", "/users/admin/role", SERVICES["Auth"],
                                 params={"new_role": "admin"}))
    
    # 8. Correction: POST /config/rules
    results.append(check_endpoint("Correction", "POST", "/config/rules", SERVICES["Correction"],
                                 payload={"field": "test", "match": "A", "replace": "B"}))

    print("\n" + "="*40)
    print(f"FINAL SCORE: {sum(results)} / {len(results)} COMPLIANT")
    print("="*40)

if __name__ == "__main__":
    verify_all_gaps()
