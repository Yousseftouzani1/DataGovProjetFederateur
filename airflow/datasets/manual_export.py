from datetime import datetime
import requests
import csv
import os
import json
import re

# Configuration
ANNOTATION_SERVICE_URL = "http://annotation-service:8007"
EXPORT_PATH = "/opt/airflow/datasets/certified"

def fetch_and_export_validated_data():
    print("Fetching completed tasks from Annotation Service...")
    try:
        response = requests.get(f"{ANNOTATION_SERVICE_URL}/tasks", params={"status": "completed", "limit": 200})
        response.raise_for_status()
        tasks = response.json().get('tasks', [])
        print(f"Found {len(tasks)} completed tasks.")
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return

    if not tasks:
        print("No Data")
        return

    golden_records = []
    
    for task in tasks:
        # Simplified extracting logic from DAG
        data_sample = task.get('data_sample', {})
        # Just use the sample field for now to verify file creation
        
        metadata = {
            '_validation_status': task.get('status', 'completed'),
            '_annotator_id': task.get('assigned_to', 'system'),
            '_completion_time': task.get('completed_at') or datetime.now().isoformat()
        }
        
        row = data_sample.copy() if isinstance(data_sample, dict) else {"raw": str(data_sample)}
        row.update(metadata)
        golden_records.append(row)

    print(f"Extracted {len(golden_records)} flattened golden records.")

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
            
            sorted_keys = sorted(list(all_keys))

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted_keys)
                writer.writeheader()
                writer.writerows(golden_records)
                
            print(f"✅ Successfully exported to {filepath}")
            
    except Exception as e:
        print(f"Error saving CSV: {e}")
        raise

if __name__ == "__main__":
    fetch_and_export_validated_data()
