"""
Daily Export Pipeline DAG
Exports validated 'Golden Records' from the Annotation Service to a certified dataset file.
Triggers daily or manually.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import csv
import os
import json
import re

# Configuration
ANNOTATION_SERVICE_URL = "http://annotation-service:8007"
EXPORT_PATH = "/opt/airflow/datasets/certified"

default_args = {
    'owner': 'data_governance_team',
    'depends_on_past': False,
    'email': ['admin@data-gov.ma'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_and_export_validated_data(**context):
    """
    Fetches completed tasks, Robustly extracts JSON rows from any field,
    Enriches with Metadata, Saves to CSV.
    """
    print("Fetching completed tasks from Annotation Service...")
    try:
        response = requests.get(f"{ANNOTATION_SERVICE_URL}/tasks", params={"status": "completed", "limit": 200})
        response.raise_for_status()
        tasks = response.json().get('tasks', [])
        print(f"Found {len(tasks)} completed tasks.")
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        raise

    if not tasks:
        return "No Data"

    golden_records = []
    PRIORITY_MAP = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}

    for task in tasks:
        annotations = task.get('annotations', [])
        corrected_data = None
        if annotations:
             corrected_data = annotations[-1].get('corrected_data')
        
        # Base Data
        raw_data = corrected_data if corrected_data else task.get('data_sample', {})
        
        items_to_export = []

        # Strategy 1: Is it already a list?
        if isinstance(raw_data, list):
            items_to_export = raw_data
        
        # Strategy 2: Check potential fields if it's a dict
        elif isinstance(raw_data, dict):
            # Fields to search for JSON content
            candidates = [
                raw_data.get("full_structure"),
                raw_data.get("snippet"),
                raw_data.get("source_text")
            ]
            
            found_parsed = None
            
            for c in candidates:
                if not c or not isinstance(c, str):
                    if isinstance(c, list):
                        found_parsed = c
                        break
                    continue
                
                # Try Parsing String
                try:
                    p = json.loads(c)
                    if isinstance(p, list):
                        found_parsed = p
                        print(f"DEBUG: Successfully parsed JSON from a field.", flush=True)
                        break
                except:
                    # Try Regex
                    match = re.search(r'\[.*\]', c, re.DOTALL)
                    if match:
                        try:
                            p = json.loads(match.group(0))
                            if isinstance(p, list):
                                found_parsed = p
                                print(f"DEBUG: Successfully parsed Regex JSON from a field.", flush=True)
                                break
                        except: pass
            
            if found_parsed:
                items_to_export = found_parsed
            else:
                items_to_export = [raw_data] # Fallback to raw dict
        
        # Strategy 3: Is it a string?
        elif isinstance(raw_data, str):
             try:
                 p = json.loads(raw_data)
                 items_to_export = p if isinstance(p, list) else [p]
             except:
                match = re.search(r'\[.*\]', raw_data, re.DOTALL)
                if match:
                    try:
                        p = json.loads(match.group(0))
                        items_to_export = p if isinstance(p, list) else [p]
                    except:
                        continue
                else:
                    continue

        # Prepare Metadata
        metadata = {
            '_validation_status': task.get('status', 'completed'),
            '_annotator_id': task.get('assigned_to', 'system'),
            '_completion_time': task.get('completed_at') or datetime.now().isoformat()
        }
        
        detections = task.get('detections', [])
        max_sens = "low"
        max_score = 0
        for d in detections:
            sens = d.get('sensitivity_level', 'unknown').lower()
            score = PRIORITY_MAP.get(sens, 0)
            if score > max_score:
                max_score = score
                max_sens = sens
        metadata['_sensitivity_level'] = max_sens
        metadata['_detection_count'] = len(detections)

        # Flatten logic
        for item in items_to_export:
            if isinstance(item, dict):
                row = item.copy()
                row.update(metadata)
                golden_records.append(row)

    print(f"Extracted {len(golden_records)} flattened golden records.")

    if not golden_records:
        return "No Golden Records extracted"
        
    if golden_records:
         print(f"DEBUG: First Record Keys: {list(golden_records[0].keys())}", flush=True)

    # Save to CSV
    os.makedirs(EXPORT_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"certified_export_{timestamp}.csv"
    filepath = os.path.join(EXPORT_PATH, filename)

    try:
        if golden_records:
            all_keys = set()
            for r in golden_records:
                all_keys.update(r.keys())
            
            exclude_keys = {'full_structure', 'snippet', 'source_text'}
            
            sorted_keys = sorted([k for k in all_keys if not k.startswith('_') and k not in exclude_keys]) + \
                          sorted([k for k in all_keys if k.startswith('_')])

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted_keys, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(golden_records)
                
            print(f"✅ Successfully exported to {filepath}")
            
            # ---------------------------------------------------------
            # Create Lineage in Apache Atlas
            # ---------------------------------------------------------
            try:
                import requests as atlas_requests
                import os
                
                atlas_url = os.getenv("ATLAS_URL", "http://192.168.110.132:21000")
                atlas_user = os.getenv("ATLAS_USER", "admin")
                atlas_pass = os.getenv("ATLAS_PASSWORD", "ensias2025")
                mock_mode = os.getenv("MOCK_GOVERNANCE", "true").lower() == "true"
                
                if not mock_mode:
                    # Register the output dataset
                    output_entity = {
                        "entity": {
                            "typeName": "DataSet",
                            "attributes": {
                                "qualifiedName": f"dataset@{filename}",
                                "name": filename,
                                "description": "Certified golden record export from DataGov",
                                "owner": "data_governance_team"
                            }
                        }
                    }
                    
                    base_api = f"{atlas_url}/api/atlas/v2"
                    auth = (atlas_user, atlas_pass)
                    
                    # Create output entity
                    out_resp = atlas_requests.post(f"{base_api}/entity", json=output_entity, auth=auth)
                    print(f"Created output entity: {out_resp.status_code}")
                    
                    # Create Process (lineage) entity
                    # Get source dataset names from tasks
                    source_names = set()
                    for task in tasks:
                        ds_name = task.get("dataset_name", "")
                        if ds_name:
                            source_names.add(ds_name)
                    
                    for source_name in source_names:
                        process_entity = {
                            "entity": {
                                "typeName": "Process",
                                "attributes": {
                                    "qualifiedName": f"process@DataGov_Export_{timestamp}",
                                    "name": f"DataGov Export Pipeline",
                                    "description": "Automated export of validated data",
                                    "inputs": [{"typeName": "DataSet", "uniqueAttributes": {"qualifiedName": f"dataset@{source_name}"}}],
                                    "outputs": [{"typeName": "DataSet", "uniqueAttributes": {"qualifiedName": f"dataset@{filename}"}}]
                                }
                            }
                        }
                        proc_resp = atlas_requests.post(f"{base_api}/entity", json=process_entity, auth=auth)
                        print(f"📈 Created lineage: {source_name} -> {filename} (Status: {proc_resp.status_code})")
                    
            except Exception as lineage_err:
                print(f"⚠️ Lineage creation warning: {lineage_err}")
                
    except Exception as e:
        print(f"Error saving CSV: {e}")
        raise

    return filepath

def trigger_retraining_stub(**context):
    export_path = context['ti'].xcom_pull(task_ids='export_validated_data')
    if export_path and export_path != "No Data":
        print(f"🚀 Triggering Retraining Pipeline using dataset: {export_path}")
    else:
        print("Skipping retraining.")

with DAG(
    'approved_data_export_pipeline',
    default_args=default_args,
    description='Daily export of validated golden records',
    schedule_interval=None, 
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['production', 'export', 'golden-records'],
) as dag:

    export_task = PythonOperator(
        task_id='export_validated_data',
        python_callable=fetch_and_export_validated_data,
        provide_context=True,
    )

    retrain_task = PythonOperator(
        task_id='trigger_retraining_simulation',
        python_callable=trigger_retraining_stub,
        provide_context=True,
    )

    export_task >> retrain_task
