import sys
sys.path.append('/opt/airflow/dags')
from daily_export_pipeline import fetch_and_export_validated_data

print("Running manual exported...")
try:
    path = fetch_and_export_validated_data()
    print(f"EXPORT_SUCCESS: {path}")
except Exception as e:
    print(f"EXPORT_FAILED: {e}")
