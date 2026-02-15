from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
import requests
import json
from datetime import timedelta

# Service URLs (Docker Network)
CLEANING_SERVICE_URL = "http://cleaning-service:8004"
PRESIDIO_SERVICE_URL = "http://presidio-service:8003"
CLASSIFICATION_SERVICE_URL = "http://classification-service:8005"
QUALITY_SERVICE_URL = "http://quality-service:8008"
ETHIMASK_SERVICE_URL = "http://ethimask-service:8009"
CORRECTION_SERVICE_URL = "http://correction-service:8006"

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
    """Step 1: Trigger cleaning on the uploaded dataset"""
    conf = context['dag_run'].conf
    dataset_id = conf.get('dataset_id')

    if not dataset_id:
        raise ValueError("No dataset_id provided in DAG run configuration")

    print(f"Starting pipeline for dataset: {dataset_id}")

    # Trigger auto-clean on the dataset (uses actual endpoint)
    resp = requests.post(
        f"{CLEANING_SERVICE_URL}/clean/{dataset_id}",
        json={"auto_clean": True},
        timeout=120
    )
    resp.raise_for_status()
    clean_result = resp.json()
    print(f"Cleaning complete: {json.dumps(clean_result, indent=2)}")

    return dataset_id

def detect_pii(**context):
    """Step 2: Fetch dataset data and run PII detection via Presidio"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='ingest_and_clean')

    # Fetch dataset JSON from cleaning service
    resp = requests.get(
        f"{CLEANING_SERVICE_URL}/dataset/{dataset_id}/json",
        timeout=30
    )
    resp.raise_for_status()
    dataset = resp.json()
    rows = dataset.get("data", [])

    if not rows:
        print("No data rows found, skipping PII detection")
        return dataset_id

    # Concatenate first 10 rows into a text block for Presidio analysis
    sample_text = "\n".join(
        " | ".join(str(v) for v in row.values())
        for row in rows[:10]
    )

    resp = requests.post(
        f"{PRESIDIO_SERVICE_URL}/analyze",
        json={"text": sample_text, "language": "fr", "score_threshold": 0.4},
        timeout=60
    )
    resp.raise_for_status()
    detections = resp.json()
    print(f"PII detections: {detections.get('count', 0)} entities found")

    return dataset_id

def classify_sensitivity(**context):
    """Step 3: Classify column sensitivity using ensemble ML"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='detect_pii')

    # Fetch dataset columns and sample values
    resp = requests.get(
        f"{CLEANING_SERVICE_URL}/dataset/{dataset_id}/json",
        timeout=30
    )
    resp.raise_for_status()
    dataset = resp.json()
    rows = dataset.get("data", [])

    if not rows:
        print("No data rows, skipping classification")
        return dataset_id

    # Build data_sample: {col_name: [list of values]}
    columns = list(rows[0].keys())
    data_sample = {col: [row.get(col) for row in rows] for col in columns}

    resp = requests.post(
        f"{CLASSIFICATION_SERVICE_URL}/classify",
        json={"dataset_id": dataset_id, "data_sample": data_sample},
        timeout=120
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"Classification complete: {len(result.get('classifications', {}))} columns classified")

    return dataset_id

def evaluate_quality(**context):
    """Step 4: Run ISO 25012 quality evaluation"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='classify_sensitivity')

    resp = requests.post(
        f"{QUALITY_SERVICE_URL}/evaluate/{dataset_id}",
        timeout=60
    )
    resp.raise_for_status()
    report = resp.json()
    print(f"Quality Grade: {report.get('grade', 'N/A')} ({report.get('global_score', 0)}%)")

    return dataset_id

def apply_masking(**context):
    """Step 5: Log masking audit (actual masking happens on-demand per role)"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='evaluate_quality')

    print(f"Pipeline complete for dataset {dataset_id}. "
          f"Masking will be applied on-demand based on user role via EthiMask.")

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
    task_id='detect_pii',
    python_callable=detect_pii,
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
