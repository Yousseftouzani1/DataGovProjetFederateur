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
    """Upload dataset to cleaning service"""
    url = f"{SERVICE_URLS['cleaning']}/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.split('/')[-1], f)}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        dataset_id = result['dataset_id']
        print(f"✅ Uploaded dataset: {dataset_id}")
        # Push to XCom for downstream tasks
        context['ti'].xcom_push(key='dataset_id', value=dataset_id)
        return dataset_id
    else:
        raise Exception(f"Upload failed: {response.text}")


def profile_data(**context):
    """Profile the dataset"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    url = f"{SERVICE_URLS['cleaning']}/profile/{dataset_id}"
    
    response = requests.get(url)
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile complete: {profile['profile']['rows']} rows")
        context['ti'].xcom_push(key='profile', value=profile['profile'])
        return profile
    else:
        raise Exception(f"Profiling failed: {response.text}")


def clean_data(**context):
    """Apply automatic cleaning"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    url = f"{SERVICE_URLS['cleaning']}/clean/{dataset_id}/auto"
    
    response = requests.post(url)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cleaned: {result['rows_removed']} rows removed")
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
    """Classify sensitivity using classification service"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    
    # Get dataset preview
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=100"
    preview_response = requests.get(preview_url)
    
    if preview_response.status_code != 200:
        raise Exception("Cannot get dataset preview")
    
    data = preview_response.json()['preview']
    
    classifications = []
    for row in data:
        text = " ".join(str(v) for v in row.values() if v)
        response = requests.post(
            f"{SERVICE_URLS['classification']}/classify",
            json={"text": text}
        )
        if response.status_code == 200:
            classifications.append(response.json())
    
    print(f"✅ Classified {len(classifications)} rows")
    context['ti'].xcom_push(key='classifications', value=classifications)
    return classifications


def detect_inconsistencies(**context):
    """Detect data inconsistencies"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    
    # Register dataset with correction service
    preview_url = f"{SERVICE_URLS['cleaning']}/datasets/{dataset_id}/preview?rows=1000"
    preview_response = requests.get(preview_url)
    data = preview_response.json()['preview']
    
    requests.post(
        f"{SERVICE_URLS['correction']}/datasets/{dataset_id}/register",
        json={"records": data}
    )
    
    # Detect inconsistencies
    response = requests.post(f"{SERVICE_URLS['correction']}/detect/{dataset_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {result['total_inconsistencies']} inconsistencies")
        context['ti'].xcom_push(key='inconsistencies', value=result)
        return result
    else:
        raise Exception(f"Detection failed: {response.text}")


def apply_corrections(**context):
    """Apply automatic corrections"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    
    response = requests.post(f"{SERVICE_URLS['correction']}/correct/{dataset_id}/auto")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Applied {result['corrections_applied']} corrections")
        return result
    else:
        print(f"⚠️ Corrections failed, continuing: {response.text}")
        return None


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
    """Create annotation tasks for human validation"""
    dataset_id = context['ti'].xcom_pull(key='dataset_id')
    detections = context['ti'].xcom_pull(key='taxonomie_detections') or []
    
    # Create tasks for items with detections
    response = requests.post(
        f"{SERVICE_URLS['annotation']}/tasks",
        json={
            "dataset_id": dataset_id,
            "row_indices": list(range(10)),  # First 10 rows for review
            "annotation_type": "pii_validation",
            "priority": "medium",
            "detections": detections[:50]
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Created {result['created']} annotation tasks")
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
    schedule_interval='0 2 * * *',  # Daily at 2AM
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
    op_kwargs={'file_path': '/opt/airflow/datasets/test_data/test_data_morocco.csv'},
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
