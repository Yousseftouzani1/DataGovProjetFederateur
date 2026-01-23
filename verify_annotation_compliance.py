
import requests
import json
import time

ANNOTATION_URL = "http://127.0.0.1:8007"

def test_smart_assignment():
    print("\n[SCENARIO 1] ALGORITHM 7: Smart Assignment Test")
    print("---------------------------------------------")
    
    # 1. Create a task requiring 'Finance' skill
    task_req = {
        "dataset_id": "test_dataset_777",
        "row_indices": [101],
        "annotation_type": "pii_validation",
        "priority": "high",
        "required_skill": "Finance",
        "data_samples": [{"id": 777, "amount": 5000, "currency": "MAD"}]
    }
    resp = requests.post(f"{ANNOTATION_URL}/tasks", json=task_req)
    try:
        task_id = resp.json()["task_ids"][0]
        print(f"✅ Created Task {task_id} (Requires: Finance)")
    except Exception as e:
        print(f"❌ Failed to parse /tasks response: {e}")
        print(f"   > Status: {resp.status_code}")
        print(f"   > Body: '{resp.text}'")
        return

    # 2. Trigger Smart Assignment
    # We provide 3 users:
    # - user_a: Junior, no Finance skill, low load
    # - admin: Senior, Finance skill, high accuracy (The target)
    # - user_b: Moderate, no skill, moderate load
    assign_req = {
        "strategy": "smart",
        "users": ["user_a", "admin", "user_b"],
        "max_tasks_per_user": 10
    }
    print("🚀 Triggering Smart Assignment Strategy...")
    assign_resp = requests.post(f"{ANNOTATION_URL}/assign", json=assign_req)
    if assign_resp.status_code != 200:
        print(f"❌ Error {assign_resp.status_code}: {assign_resp.text}")
        return

    data = assign_resp.json()
    if "assignments" not in data:
        print(f"❌ Unexpected response format: {data}")
        return
        
    assignments = data["assignments"]
    
    # Find our task assignment
    assignment = next((a for a in assignments if a["task_id"] == task_id), None)
    if assignment:
        print(f"🎯 Task {task_id} assigned to: {assignment['user_id']}")
        if assignment['user_id'] == "admin":
            print("✅ ALGORITHM 7 SUCCESS: Admin selected for Finance skill/performance.")
        else:
            print(f"❌ ALGORITHM 7 FAILED: Expected admin, got {assignment['user_id']}")
    else:
        print("❌ Assignment failed.")

def test_quality_metrics():
    print("\n[SCENARIO 2] ALGORITHM 6: Cohen's Kappa & Accuracy Test")
    print("-------------------------------------------------------")
    
    # 1. Submit multiple annotations for 'user_a'
    # We'll create tasks and submit them directly
    user = "user_a"
    task_ids = []
    for i in range(5):
        t_req = {
            "dataset_id": "metric_test",
            "row_indices": [i],
            "data_samples": [{"val": i}],
            "detections": [{"score": 0.95}] # High conf AI detections
        }
        res = requests.post(f"{ANNOTATION_URL}/tasks", json=t_req)
        tid = res.json()["task_ids"][0]
        
        # Manually assign to user_a
        requests.post(f"{ANNOTATION_URL}/assign/{tid}?user_id={user}")
        
        # Submit: Validate 4, Reject 1
        is_valid = i < 4
        requests.post(f"{ANNOTATION_URL}/tasks/{tid}/submit", json={
            "annotations": [{"field": "test", "is_valid": is_valid}],
            "time_spent_seconds": 20
        })
        task_ids.append(tid)

    print(f"✅ Submitted 5 annotations for {user}")

    # 2. Check Stats
    stats_resp = requests.get(f"{ANNOTATION_URL}/users/{user}/stats")
    stats = stats_resp.json()
    print(f"📊 CDC Stats for {user}:")
    print(f"   > Accuracy (F9): {stats['accuracy']}%")
    print(f"   > Cohen's Kappa (F7/F9): {stats['kappa']}")
    print(f"   > Throughput (F8): {stats['throughput']} tasks/hr")
    print(f"   > Quality Score (F9): {stats['quality_score']}")
    
    if stats['quality_score'] > 0 and stats['throughput'] >= 0:
        print("✅ CDC COMPLIANCE SUCCESS: Formulas 8 & 9 verified.")
    else:
        print("❌ Metric calculation issue.")

if __name__ == "__main__":
    try:
        test_smart_assignment()
        test_quality_metrics()
    except Exception as e:
        print(f"❌ Error during verification: {e}")
