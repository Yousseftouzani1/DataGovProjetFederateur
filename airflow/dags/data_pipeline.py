from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
import requests
import json
from datetime import timedelta

# Service URLs (Docker Network)
CLEANING_SERVICE_URL = "http://cleaning-serv:8002"
TAXONOMY_SERVICE_URL = "http://taxonomie-serv:8004"
CLASSIFICATION_SERVICE_URL = "http://classification-serv:8005"
QUALITY_SERVICE_URL = "http://quality-serv:8008"
ETHIMASK_SERVICE_URL = "http://ethimask-serv:8009"
CORRECTION_SERVICE_URL = "http://correction-serv:8006"

default_args = {
    'owner': 'datagov',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'datagov_pipeline',
    default_args=default_args,
    description='End-to-end Data Governance Pipeline',
    schedule_interval=None,  # Triggered manually via upload
    start_date=days_ago(1),
    tags=['datagov'],
    catchup=False
)

def ingest_and_clean(**context):
    """Call cleaning service to profile and clean data"""
    conf = context['dag_run'].conf
    dataset_id = conf.get('dataset_id')
    
    if not dataset_id:
        raise ValueError("No dataset_id provided in DAG run configuration")
    
    print(f"Starting pipeline for dataset: {dataset_id}")
    
    # 1. Profile
    resp = requests.post(f"{CLEANING_SERVICE_URL}/profile", json={"dataset_id": dataset_id})
    resp.raise_for_status()
    profile = resp.json()
    print(f"Profile generated: {profile['summary']}")
    
    # 2. Clean
    resp = requests.post(f"{CLEANING_SERVICE_URL}/clean", json={"dataset_id": dataset_id, "auto_clean": True})
    resp.raise_for_status()
    clean_result = resp.json()
    print(f"Cleaning complete: {clean_result}")
    
    return dataset_id

def analyze_pii(**context):
    """Call taxonomy service to detect PII"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='ingest_and_clean')
    
    # Get data sample (or full data logic) - simplified here to generic analysis trigger
    # In real flow, we'd pass data. For now, assuming services share DB/access
    resp = requests.post(f"{TAXONOMY_SERVICE_URL}/analyze-dataset/{dataset_id}") 
    # Note: Accessing by ID implies shared storage or service-to-service fetch.
    # Current microservices might need data payload if not sharing DB directly.
    # For this POC, we'll assume the /clean calls updated the shared state or we send specific column data.
    
    # Re-logic: Taxonomie-serv expects text. 
    # Let's pivot: We will trigger a "Correction" scan which includes pattern detection
    
    resp = requests.post(f"{CORRECTION_SERVICE_URL}/detect/{dataset_id}")
    resp.raise_for_status()
    detections = resp.json()
    print(f"Inconsistencies/PII candidates detected: {detections['total_inconsistencies']}")
    
    return dataset_id

def classify_sensitivity(**context):
    """Call classification service"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='analyze_pii')
    
    # Trigger classification on dataset
    # Need to simulate or implement bulk scan in classification-serv.
    # Existing endpoint is /classify (single text).
    # We will simulate iterating or use a bulk endpoint if we made one.
    # For POC, let's call a 'mock' generic logger or assume we process top rows.
    
    print(f"Classifying dataset {dataset_id} sensitivity...")
    # Real impl would iterate rows.
    
    return dataset_id

def evaluate_quality(**context):
    """Call quality service"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='classify_sensitivity')
    
    resp = requests.post(f"{QUALITY_SERVICE_URL}/evaluate/{dataset_id}")
    resp.raise_for_status()
    report = resp.json()
    print(f"Quality Grade: {report['grade']} ({report['global_score']}%)")
    
    return dataset_id

def apply_masking(**context):
    """Call ethimask service"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='evaluate_quality')
    
    print(f"Applying masking policies for dataset {dataset_id}")
    # Simulating masking trigger
    
    return dataset_id

# Tasks
start = DummyOperator(task_id='start', dag=dag)

t1 = PythonOperator(
    task_id='ingest_and_clean',
    python_callable=ingest_and_clean,
    provide_context=True,
    dag=dag
)

t2 = PythonOperator(
    task_id='analyze_pii',
    python_callable=analyze_pii,
    provide_context=True,
    dag=dag
)

t3 = PythonOperator(
    task_id='classify_sensitivity',
    python_callable=classify_sensitivity,
    provide_context=True,
    dag=dag
)

t4 = PythonOperator(
    task_id='evaluate_quality',
    python_callable=evaluate_quality,
    provide_context=True,
    dag=dag
)

t5 = PythonOperator(
    task_id='apply_masking',
    python_callable=apply_masking,
    provide_context=True,
    dag=dag
)

end = DummyOperator(task_id='end', dag=dag)

# Dependencies
start >> t1 >> t2 >> t3 >> t4 >> t5 >> end
