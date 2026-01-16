import requests

ATLAS_URL = "http://192.168.110.132:21000/api/atlas/v2"
ATLAS_AUTH = ("admin", "ensias2025")

def final_atlas_proof():
    print("--- 🔬 Ultimate Atlas Proof ---")
    # hdfs_path is a standard type in HDP
    payload = {
        "entity": {
            "typeName": "hdfs_path",
            "attributes": {
                "qualifiedName": "/tmp/ensias_audit_folder@sandbox",
                "name": "REAL_ENSIAS_DATA_LOCATION",
                "path": "/tmp/ensias_audit_folder",
                "description": "This is a real HDFS path tracked by Atlas.",
                "owner": "Admin"
            }
        }
    }
    
    try:
        resp = requests.post(f"{ATLAS_URL}/entity", json=payload, auth=ATLAS_AUTH, timeout=15)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    final_atlas_proof()
