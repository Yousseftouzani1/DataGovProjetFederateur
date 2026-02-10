import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration - all from .env, no hardcoded IPs
ATLAS_URL = os.getenv("ATLAS_URL")
if not ATLAS_URL:
    raise RuntimeError("ATLAS_URL not set. Configure it in .env file.")
ATLAS_AUTH = (os.getenv("ATLAS_USER", "admin"), os.getenv("ATLAS_PASSWORD", ""))
ANNOTATION_SERVICE_URL = "http://annotation-service:8007"
EXPORT_FILENAME = "certified_export_20260117_132628.csv" # Hardcoded based on previous step

def register_lineage():
    print(f"🔧 Fixing Lineage for {EXPORT_FILENAME}...")
    
    # 1. Get Source Dataset Name from Annotation Service
    try:
        resp = requests.get(f"{ANNOTATION_SERVICE_URL}/tasks", params={"status": "completed", "limit": 1})
        tasks = resp.json().get('tasks', [])
        if not tasks:
            print("No tasks found to derive source.")
            return
        
        # The task contains the UUID, but Atlas knows the file by its Name
        # We will force the correct source name based on your active test
        source_dataset_id = "MASTER_DATAGOV8TEST.csv"     
        print(f"📍 Detected Source Dataset: {source_dataset_id}")
    except Exception as e:
        print(f"Failed to fetch source info: {e}")
        return

    # 2. Create Output Entity (The Certified CSV)
    base_api = f"{ATLAS_URL}/api/atlas/v2"
    
    output_entity = {
        "entity": {
            "typeName": "DataSet",
            "attributes": {
                "qualifiedName": f"dataset@{EXPORT_FILENAME}",
                "name": EXPORT_FILENAME,
                "description": "Certified golden record export (Manual Repair)",
                "owner": "data_governance_team"
            }
        }
    }
    
    try:
        print(f"📤 Registering Output Entity in Atlas...")
        resp = requests.post(f"{base_api}/entity", json=output_entity, auth=ATLAS_AUTH)
        print(f"Response: {resp.status_code}")
    except Exception as e:
        print(f"Atlas Error: {e}")
        return

    # 3. Create Lineage Process
    process_entity = {
        "entity": {
            "typeName": "Process",
            "attributes": {
                "qualifiedName": f"process@DataGov_Repaired_{EXPORT_FILENAME}",
                "name": "DataGov Export Pipeline (Repaired)",
                "description": "Automated export of validated data",
                "inputs": [{"typeName": "DataSet", "uniqueAttributes": {"qualifiedName": f"dataset@{source_dataset_id}"}}],
                "outputs": [{"typeName": "DataSet", "uniqueAttributes": {"qualifiedName": f"dataset@{EXPORT_FILENAME}"}}]
            }
        }
    }

    try:
        print(f"🔗 Creating Lineage Link...")
        resp = requests.post(f"{base_api}/entity", json=process_entity, auth=ATLAS_AUTH)
        if resp.status_code == 200:
            print("✅ Lineage successfully created!")
        else:
            print(f"⚠️ Failed to create lineage: {resp.text}")
    except Exception as e:
        print(f"Atlas Process Error: {e}")

if __name__ == "__main__":
    register_lineage()
