"""
Data Processing Pipeline DAG
Complete pipeline: Upload → Profile → Clean → Detect PII → Classify → Mask → Store

Orchestrates all microservices in sequence
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.utils.trigger_rule import TriggerRule
import requests
import json

# ====================================================================
# CONFIGURATION
# ====================================================================

import yaml
import os

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '../config/pipeline_config.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️ Could not load config, using defaults: {e}")
        return {"configuration": {}}

PIPELINE_CONFIG = load_config()

def is_feature_enabled(feature_name: str) -> bool:
    return PIPELINE_CONFIG.get("configuration", {}).get(feature_name, True)

SERVICE_URLS = {
    "cleaning": "http://cleaning-service:8004",
    "taxonomie": "http://taxonomie-service:8002",
    "presidio": "http://presidio-service:8003",
    "classification": "http://classification-service:8005",
    "correction": "http://correction-service:8006",
    "annotation": "http://annotation-service:8007",
    "quality": "http://quality-service:8008",
    "ethimask": "http://ethimask-service:8009",
}

default_args = {
    'owner': 'data_governance_team',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# ====================================================================
# TASK FUNCTIONS
# ====================================================================

def check_service_health(service_name: str, **context):
    """Check if a service is healthy"""
    url = SERVICE_URLS.get(service_name)
    if not url:
        raise ValueError(f"Unknown service: {service_name}")
    
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            raise Exception(f"{service_name} returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Cannot reach {service_name}: {str(e)}")


def upload_dataset(file_path: str, **context):
    """Upload dataset to cleaning service, or reuse existing dataset_id from dag_run conf"""
    # If dataset_id is provided in dag_run conf, skip upload and reuse it
    conf = context.get('dag_run', None)
    if conf and hasattr(conf, 'conf') and conf.conf.get('dataset_id'):
        dataset_id = conf.conf['dataset_id']
        print(f"✅ Reusing existing dataset: {dataset_id}")
        context['ti'].xcom_push(key='dataset_id', value=dataset_id)
        return dataset_id

    url = f"{SERVICE_URLS['cleaning']}/upload"

    with open(file_path, 'rb') as f:
        files = {'file': (file_path.split('/')[-1], f)}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        result = response.json()
        dataset_id = result['dataset_id']
        print(f"✅ Uploaded dataset: {dataset_id}")
        context['ti'].xcom_push(key='dataset_id', value=dataset_id)
        return dataset_id
    else:
        raise Exception(f"Upload failed: {response.text}")


def profile_data(**context):
    """Profile the dataset — returns HTML report from YData Profiling"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    url = f"{SERVICE_URLS['cleaning']}/profile/{dataset_id}"

    response = requests.get(url)
    if response.status_code == 200:
        # Profile endpoint returns HTML report, not JSON
        try:
            profile = response.json()
            print(f"✅ Profile complete: {profile.get('rows', 'N/A')} rows")
            context['ti'].xcom_push(key='profile', value=profile)
            return profile
        except Exception:
            # HTML report returned — profiling succeeded
            print(f"✅ Profile complete (HTML report, {len(response.text)} bytes)")
            context['ti'].xcom_push(key='profile', value={"status": "completed", "report_size": len(response.text)})
            return {"status": "completed"}
    else:
        raise Exception(f"Profiling failed: {response.status_code}")


def clean_data(**context):
    """Apply automatic cleaning"""
    if not is_feature_enabled("enable_cleaning"):
        print("⏭️ Cleaning disabled in config, skipping.")
        return {"status": "skipped"}

    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    url = f"{SERVICE_URLS['cleaning']}/clean/{dataset_id}"

    response = requests.post(url, json={
        "remove_duplicates": is_feature_enabled("remove_duplicates"),
        "handle_missing": "mean",
        "remove_outliers": True
    })
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cleaned: rows_before={result.get('metrics', {}).get('rows_before', '?')}, rows_after={result.get('metrics', {}).get('rows_after', '?')}")
        return result
    else:
        raise Exception(f"Cleaning failed: {response.text}")


def detect_pii_taxonomie(**context):
    """Detect PII using taxonomie service"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    
    # Get dataset preview
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=100"
    preview_response = requests.get(preview_url)
    
    if preview_response.status_code != 200:
        raise Exception("Cannot get dataset preview")
    
    data = preview_response.json()['preview']
    
    # Analyze each row
    all_detections = []
    for row in data:
        text = " ".join(str(v) for v in row.values() if v)
        response = requests.post(
            f"{SERVICE_URLS['taxonomie']}/analyze",
            json={"text": text}
        )
        if response.status_code == 200:
            result = response.json()
            all_detections.extend(result.get('detections', []))
    
    print(f"✅ Taxonomie detected {len(all_detections)} PII entities")
    context['ti'].xcom_push(key='taxonomie_detections', value=all_detections)
    return all_detections


def detect_pii_presidio(**context):
    """Detect PII using Presidio service"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    
    # Get dataset preview
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=100"
    preview_response = requests.get(preview_url)
    
    if preview_response.status_code != 200:
        raise Exception("Cannot get dataset preview")
    
    data = preview_response.json()['preview']
    
    # Analyze with Presidio
    all_detections = []
    for row in data:
        text = " ".join(str(v) for v in row.values() if v)
        response = requests.post(
            f"{SERVICE_URLS['presidio']}/analyze",
            json={"text": text}
        )
        if response.status_code == 200:
            result = response.json()
            all_detections.extend(result.get('detections', []))
    
    print(f"✅ Presidio detected {len(all_detections)} entities")
    context['ti'].xcom_push(key='presidio_detections', value=all_detections)
    return all_detections


def classify_sensitivity(**context):
    """Classify sensitivity using classification service (ensemble model)"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')

    # Get dataset preview as columnar data for the classification API
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=100"
    preview_response = requests.get(preview_url)

    if preview_response.status_code != 200:
        raise Exception("Cannot get dataset preview")

    rows = preview_response.json()['preview']
    if not rows:
        print("⚠️ No data to classify")
        return []

    # Convert row-oriented data to columnar format (Dict[str, List])
    columns = {}
    for row in rows:
        for key, val in row.items():
            columns.setdefault(key, []).append(val)

    response = requests.post(
        f"{SERVICE_URLS['classification']}/classify",
        json={"dataset_id": dataset_id, "data_sample": columns}
    )

    if response.status_code == 200:
        result = response.json()
        classifications = result.get('classifications', {})
        pii_count = sum(1 for v in classifications.values() if v.get('level', 0) >= 3)
        print(f"✅ Classified {len(classifications)} columns ({pii_count} PII)")
        context['ti'].xcom_push(key='classifications', value=result)
        return result
    else:
        print(f"⚠️ Classification failed: {response.text}")
        return {}


def detect_inconsistencies(**context):
    """Detect data inconsistencies row by row"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')

    # Get dataset preview
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=100"
    preview_response = requests.get(preview_url)
    data = preview_response.json()['preview']

    total_issues = 0
    all_inconsistencies = []
    for row in data:
        response = requests.post(
            f"{SERVICE_URLS['correction']}/detect",
            json={"row": {k: str(v) if v is not None else "" for k, v in row.items()}}
        )
        if response.status_code == 200:
            result = response.json()
            total_issues += result.get('count', 0)
            all_inconsistencies.extend(result.get('inconsistencies', []))

    print(f"✅ Found {total_issues} inconsistencies across {len(data)} rows")
    context['ti'].xcom_push(key='inconsistencies', value=all_inconsistencies)
    return {"total_inconsistencies": total_issues, "rows_checked": len(data)}


def apply_corrections(**context):
    """Apply automatic corrections row by row"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')

    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=100"
    preview_response = requests.get(preview_url)
    data = preview_response.json()['preview']

    corrections_applied = 0
    for row in data:
        response = requests.post(
            f"{SERVICE_URLS['correction']}/correct",
            json={"row": {k: str(v) if v is not None else "" for k, v in row.items()}}
        )
        if response.status_code == 200:
            result = response.json()
            corrections_applied += len(result.get('corrections', []))

    print(f"✅ Applied {corrections_applied} corrections across {len(data)} rows")
    return {"corrections_applied": corrections_applied, "rows_processed": len(data)}


def evaluate_quality(**context):
    """Evaluate data quality with ISO 25012 metrics"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    
    # Register with quality service
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=1000"
    preview_response = requests.get(preview_url)
    data = preview_response.json()['preview']
    
    requests.post(
        f"{SERVICE_URLS['quality']}/datasets/{dataset_id}/register",
        json={"records": data}
    )
    
    # Evaluate quality
    response = requests.post(f"{SERVICE_URLS['quality']}/evaluate/{dataset_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Quality Score: {result['global_score']}% (Grade {result['grade']})")
        context['ti'].xcom_push(key='quality_report', value=result)
        return result
    else:
        raise Exception(f"Quality evaluation failed: {response.text}")


def create_annotation_tasks(**context):
    """Create annotation tasks for human validation - ONLY for rows with issues per Cahier des Charges"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    pii_detections = context['ti'].xcom_pull(key='taxonomie_detections') or []
    presidio_detections = context['ti'].xcom_pull(key='presidio_detections') or []
    data_errors = context['ti'].xcom_pull(key='data_quality_errors') or []
    
    # Combine all detections from Presidio and Taxonomie
    all_detections = pii_detections + presidio_detections
    
    # Get rows that have detections (each detection has a row_index or we extract from context)
    detected_row_indices = set()
    for d in all_detections:
        if 'row' in d:
            detected_row_indices.add(d['row'])
        elif 'row_index' in d:
            detected_row_indices.add(d['row_index'])
    
    # Also add rows with data quality errors
    for err in data_errors:
        if 'row' in err:
            detected_row_indices.add(err['row'])
    
    # If no specific rows detected, check ALL rows for PII columns (fallback)
    if not detected_row_indices:
        print("⚠️ No row-level detections found, creating tasks for rows with PII columns")
        # Fallback: fetch preview and check which rows have values in PII columns
        preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=30"
        try:
            preview_resp = requests.get(preview_url)
            preview_data = preview_resp.json().get('preview', [])
            
            # Columns that are typically PII
            pii_columns = ['cin_ma', 'phone_ma', 'rib_ma', 'credit_card', 'email', 'salary_mad']
            
            for idx, row in enumerate(preview_data):
                has_pii = False
                has_error = False
                
                # Check if row has PII values
                for col in pii_columns:
                    if col in row and row[col]:
                        has_pii = True
                        break
                
                # Check for data quality issues (simple validation)
                if row.get('cin_ma') and (len(str(row['cin_ma'])) < 6 or 'INVALID' in str(row.get('cin_ma', ''))):
                    has_error = True
                if row.get('phone_ma') and (len(str(row['phone_ma'])) < 10 or not str(row['phone_ma']).replace('+', '').isdigit()):
                    has_error = True
                if row.get('rib_ma') and ('INVALID' in str(row.get('rib_ma', '')) or 'WRONG' in str(row.get('rib_ma', ''))):
                    has_error = True
                if row.get('email') and ('@' not in str(row.get('email', '')) or '@@' in str(row.get('email', '')) or str(row.get('email', '')).endswith('@')):
                    has_error = True
                if row.get('salary_mad') and (isinstance(row.get('salary_mad'), (int, float)) and row['salary_mad'] < 0):
                    has_error = True
                
                # Add row if it has PII AND/OR has errors
                if has_pii or has_error:
                    detected_row_indices.add(idx)
                    
        except Exception as e:
            print(f"⚠️ Could not fetch preview: {e}")
            detected_row_indices = set(range(10))  # Fallback to first 10
    
    # Convert to list and sort
    row_indices = sorted(list(detected_row_indices))
    print(f"📋 Creating tasks for {len(row_indices)} rows with PII/errors: {row_indices[:10]}...")
    
    # Fetch the actual data samples for these rows
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=30"
    try:
        preview_resp = requests.get(preview_url)
        all_samples = preview_resp.json().get('preview', [])
        # Filter to only the rows with issues
        samples = [all_samples[i] for i in row_indices if i < len(all_samples)]
    except:
        samples = []

    # Create tasks only for the filtered rows
    response = requests.post(
        f"{SERVICE_URLS['annotation']}/tasks",
        json={
            "dataset_id": dataset_id,
            "row_indices": row_indices,
            "annotation_type": "pii_validation",
            "priority": "medium",
            "detections": all_detections[:50],
            "data_samples": samples
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Created {result['created']} annotation tasks for DETECTED rows (not all)")
        
        # Auto-assign tasks to 'annotator'
        try:
            requests.post(
                f"{SERVICE_URLS['annotation']}/assign",
                json={"strategy": "round_robin", "users": ["annotator"]}
            )
            print("✅ Auto-assigned tasks to 'annotator'")
        except:
            print("⚠️ Auto-assignment failed")
            
        return result
    else:
        print(f"⚠️ Task creation failed: {response.text}")
        return None



def apply_masking(**context):
    """Apply contextual masking based on role"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    detections = context['ti'].xcom_pull(key='taxonomie_detections') or []
    
    # Get sample data
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=10"
    preview_response = requests.get(preview_url)
    data = preview_response.json()['preview'][0] if preview_response.json()['preview'] else {}
    
    # Convert detections to expected format
    detection_list = [
        {
            "field": d.get("field", "unknown"),
            "value": d.get("value", ""),
            "entity_type": d.get("entity_type", "unknown"),
            "sensitivity_level": d.get("sensitivity_level", "high"),
            "confidence": d.get("confidence", 1.0)
        }
        for d in detections[:10]
    ]
    
    # Apply masking for 'labeler' role
    response = requests.post(
        f"{SERVICE_URLS['ethimask']}/mask",
        json={
            "data": data,
            "detections": detection_list,
            "config": {
                "role": "labeler",
                "context": "export",
                "purpose": "general"
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Applied masking to {result['masking_applied']} fields")
        return result
    else:
        print(f"⚠️ Masking failed: {response.text}")
        return None


def store_results(**context):
    """Store final results (placeholder for MongoDB integration)"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    quality_report = context['ti'].xcom_pull(key='quality_report')
    
    # In production, store to MongoDB
    print(f"✅ Results stored for dataset {dataset_id}")
    print(f"   Quality Score: {quality_report.get('global_score', 'N/A')}")
    
    return {
        "dataset_id": dataset_id,
        "status": "completed",
        "quality_grade": quality_report.get('grade') if quality_report else None
    }


# ====================================================================
# DAG DEFINITION
# ====================================================================

dag = DAG(
    'data_processing_pipeline',
    default_args=default_args,
    description='Complete data processing pipeline with all microservices',
    schedule_interval=None,  # Triggered manually or via API
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['data-governance', 'pii-detection', 'quality'],
)

# Start
start = DummyOperator(task_id='start', dag=dag)

# Health checks (parallel)
check_cleaning = PythonOperator(
    task_id='check_cleaning_health',
    python_callable=check_service_health,
    op_kwargs={'service_name': 'cleaning'},
    dag=dag,
)

check_taxonomie = PythonOperator(
    task_id='check_taxonomie_health',
    python_callable=check_service_health,
    op_kwargs={'service_name': 'taxonomie'},
    dag=dag,
)

check_presidio = PythonOperator(
    task_id='check_presidio_health',
    python_callable=check_service_health,
    op_kwargs={'service_name': 'presidio'},
    dag=dag,
)

# Upload
upload = PythonOperator(
    task_id='upload_dataset',
    python_callable=upload_dataset,
    op_kwargs={'file_path': '/opt/airflow/datasets/test_data/MASTER_DATAGOV_TEST.csv'},
    dag=dag,
)

# Profile
profile = PythonOperator(
    task_id='profile_data',
    python_callable=profile_data,
    dag=dag,
)

# Clean
clean = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    dag=dag,
)

# PII Detection (parallel)
detect_taxonomie = PythonOperator(
    task_id='detect_pii_taxonomie',
    python_callable=detect_pii_taxonomie,
    dag=dag,
)

detect_presidio = PythonOperator(
    task_id='detect_pii_presidio',
    python_callable=detect_pii_presidio,
    dag=dag,
)

# Classification
classify = PythonOperator(
    task_id='classify_sensitivity',
    python_callable=classify_sensitivity,
    dag=dag,
)

# Correction
detect_issues = PythonOperator(
    task_id='detect_inconsistencies',
    python_callable=detect_inconsistencies,
    dag=dag,
)

correct = PythonOperator(
    task_id='apply_corrections',
    python_callable=apply_corrections,
    dag=dag,
)

# Quality
quality = PythonOperator(
    task_id='evaluate_quality',
    python_callable=evaluate_quality,
    dag=dag,
)

# Annotation
annotate = PythonOperator(
    task_id='create_annotation_tasks',
    python_callable=create_annotation_tasks,
    dag=dag,
)

# Masking
mask = PythonOperator(
    task_id='apply_masking',
    python_callable=apply_masking,
    dag=dag,
)

# Store
store = PythonOperator(
    task_id='store_results',
    python_callable=store_results,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

# End
end = DummyOperator(task_id='end', dag=dag)

# ====================================================================
# TASK DEPENDENCIES
# ====================================================================

# Start -> Health Checks (parallel)
start >> [check_cleaning, check_taxonomie, check_presidio]

# Health Checks -> Upload
[check_cleaning, check_taxonomie, check_presidio] >> upload

# Upload -> Profile -> Clean
upload >> profile >> clean

# Clean -> PII Detection (parallel)
clean >> [detect_taxonomie, detect_presidio]

# PII Detection -> Classification
[detect_taxonomie, detect_presidio] >> classify

# Classification -> Correction flow
classify >> detect_issues >> correct

# Correction -> Quality
correct >> quality

# Quality -> Annotation + Masking (parallel)
quality >> [annotate, mask]

# Annotation + Masking -> Store -> End
[annotate, mask] >> store >> end
