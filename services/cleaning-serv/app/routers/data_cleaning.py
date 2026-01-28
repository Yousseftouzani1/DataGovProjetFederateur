
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
import pandas as pd
import io
import uuid
import os
import sys
import json
import requests
from datetime import datetime
import asyncio
import traceback
# Add common folder to path for AtlasClient
sys.path.append('/common')
try:
    from atlas_client import AtlasClient
except ImportError:
    AtlasClient = None

try:
    from ranger_client import RangerClient
    ranger_client = RangerClient()
except ImportError:
    RangerClient = None
    ranger_client = None

from ..data_cleaning.pipeline import CleaningPipeline
from ..data_cleaning.profiler import DataProfiler

from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class DetectionPayload(BaseModel):
    entity_type: str
    value: str
    score: float
    start: int
    end: int
    column: Optional[str] = "unknown"
    context: Optional[Dict[str, Any]] = None

class TriggerPayload(BaseModel):
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    detections: Optional[List[DetectionPayload]] = None
    dag_id: Optional[str] = "cleaning_pipeline_v1"

router = APIRouter(tags=["Data Cleaning (Tâche 4)"])

# Persistence configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/storage/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

PRESIDIO_URL = os.getenv("PRESIDIO_URL", "http://presidio-service:8003")
CLASSIFICATION_URL = os.getenv("CLASSIFICATION_URL", "http://classification-service:8005")
ANNOTATION_SERVICE_URL = os.getenv("ANNOTATION_SERVICE_URL", "http://annotation-service:8007")

# Ensure /app is in path for backend imports
if '/app' not in sys.path:
    sys.path.append('/app')

try:
    from backend.storage import save_raw_dataset, raw_datasets_col, log_audit_event
    print("✅ Successfully imported backend.storage")
except ImportError as e:
    print(f"⚠️ Fallback: Could not import backend.storage: {e}")
    save_raw_dataset = None
    raw_datasets_col = None
    log_audit_event = None

# In-memory cache for high-speed DataFrames (Syncs with DB)
DATASETS = {}

@router.get("/permissions")
async def get_ranger_permissions(username: str, role: str):
    """
    US-RANGER-01: Fetch dynamic permissions from Ranger/Mock for UI
    """
    # In a real environment, we'd query the RangerClient here
    # For now, we align with the frontend's expectation
    return {
        "username": username,
        "role": role,
        "access_level": "full" if role in ["admin", "steward"] else "masked" if role == "annotator" else "denied",
        "can_view_pii": role in ["admin", "steward"],
        "can_view_spi": role == "admin",
        "mask_type": "MASK_SHOW_LAST_4" if role == "annotator" else None,
        "ranger_connected": True if ranger_client else False,
        "loading": False,
        "error": None
    }

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """
    Clean up dataset from cache and DB
    """
    if dataset_id in DATASETS:
        del DATASETS[dataset_id]
        
    if raw_datasets_col is not None:
        await raw_datasets_col.delete_one({"dataset_id": dataset_id})
        await log_audit_event("INGESTION", f"DATASET_DELETED: {dataset_id}", "admin", "SUCCESS")
        
    return {"status": "deleted", "id": dataset_id}

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    US-CLEAN-01: Upload CSV/Excel
    """
    try:
        content = await file.read()
        dataset_id = str(uuid.uuid4())
        print(f"🚀 Processing Upload: {file.filename} (ID: {dataset_id})")

        # --- PHASE A: SECURE PERSISTENCE (File System + MongoDB) ---
        file_path = os.path.join(UPLOAD_DIR, f"{dataset_id}_{file.filename}")
        
        try:
            print(f"📊 Parsing Dataset: {file.filename}")
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif file.filename.endswith((".xls", ".xlsx")):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(400, "Only CSV/Excel supported")
        except Exception as pe:
            print(f"❌ Parsing Error: {pe}")
            raise HTTPException(400, f"Failed to parse file: {str(pe)}")

        try:
            with open(file_path, "wb") as f:
                f.write(content)
            print(f"📁 File persisted to shared volume: {file_path}")
        except Exception as fe:
            print(f"❌ File Persistence Error: {fe}")
            raise HTTPException(500, f"Storage failure: {str(fe)}")

        # --- REMEDIATION STEP 1: PII SCAN (Presidio) ---
        pii_tags = []
        try:
            print("🕵️ Starting PII Scan...")
            # INCREASED SAMPLING: Take 5 random rows + first 15 rows for better coverage
            sample_df = df.head(15)
            if len(df) > 20:
                sample_df = pd.concat([sample_df, df.sample(5)])
            
            sample_text = sample_df.to_string()
            presidio_resp = requests.post(f"{PRESIDIO_URL}/analyze", json={
                "text": sample_text,
                "language": "fr",
                "score_threshold": 0.3 # Lower threshold for better sensitivity
            }, timeout=10) # Increased timeout
            
            if presidio_resp.status_code == 200:
                results = presidio_resp.json().get("detections", [])
                pii_tags = list(set([d['entity_type'] for d in results]))
                print(f"🕵️ Presidio Detected: {pii_tags}")
        except Exception as e:
            print(f"⚠️ Presidio Scan Failed: {e}")

        # --- REMEDIATION STEP 2: ATLAS REGISTRATION ---
        atlas_guid = "mock-guid-fallback"
        try:
            if AtlasClient:
                print("🌍 Registering with Apache Atlas...")
                client = AtlasClient()
                # Added 5s internal timeout for safety
                guid = client.register_dataset_and_get_guid(
                    name=file.filename,
                    description=f"Uploaded via DataGov Pipeline. PII Detected: {pii_tags}",
                    owner="cleaning-service",
                    file_path=file_path
                )
                if guid:
                    atlas_guid = guid
                    # Add PII tags to Atlas
                    for tag in pii_tags:
                        try:
                            client.add_classification(guid, tag)
                        except Exception as tag_err:
                            print(f"⚠️ Could not tag {tag}: {tag_err}")
                    print(f"🌍 Registered in Atlas: {atlas_guid}")
        except Exception as e:
             print(f"⚠️ Atlas Registration Bypass: {e}")
             
        # --- REMEDIATION STEP 3: RANGER AUTOMATION ---
        try:
            if ranger_client:
                print("🛡️ Automated Ranger Policy Creation...")
                for tag in pii_tags:
                    success = ranger_client.create_tag_policy(tag_name=tag)
                    if success:
                        print(f"🛡️ Auto-generated Ranger Policy for: {tag}")
                    
                    # Add a default masking policy for Labelers
                    ranger_client.create_masking_policy(tag_name=tag, mask_type="MASK", roles=["labeler"])
        except Exception as e:
            print(f"⚠️ Ranger Automation Failed: {e}")

        # Persistent metadata in MongoDB
        dataset_meta = {
            "dataset_id": dataset_id,
            "name": file.filename, 
            "status": "raw",
            "pii_tags": pii_tags,
            "atlas_guid": atlas_guid,
            "file_path": file_path,
            "rows": len(df),
            "columns": len(df.columns),
            "created_at": datetime.now().isoformat()
        }
        
        if raw_datasets_col is not None:
            print(f"💾 Saving metadata to MongoDB for {dataset_id}...")
            await raw_datasets_col.insert_one(dataset_meta)
            await log_audit_event("INGESTION", f"DATASET_UPLOAD: {file.filename}", "annotator", "SUCCESS", {"dataset_id": dataset_id})
        else:
            print("⚠️ Skipping MongoDB save: raw_datasets_col is None")

        # Cache for performance
        DATASETS[dataset_id] = {
            "df": df, 
            "name": file.filename, 
            "status": "raw",
            "pii_tags": pii_tags,
            "atlas_guid": atlas_guid
        }
        print(f"✅ Ingestion Chain Completed for {dataset_id}")
        # Remove MongoDB _id for JSON serialization
        dataset_meta.pop("_id", None)
        return dataset_meta
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Critical Ingestion Error: {str(e)}")

@router.get("/dataset/{dataset_id}/json")
async def get_dataset_json(dataset_id: str, sample: bool = False):
    """
    US-QUAL-Integration: Expose dataset as JSON for Quality Service
    Enhanced with Sampling for preview performance.
    """
    if dataset_id not in DATASETS:
        print(f"🔄 Cache miss for {dataset_id}. Attempting to reload from MongoDB...")
        if raw_datasets_col is not None:
            doc = await raw_datasets_col.find_one({"dataset_id": dataset_id})
            if doc and os.path.exists(doc.get("file_path", "")):
                try:
                    fpath = doc["file_path"]
                    if fpath.endswith(".csv"):
                        df = pd.read_csv(fpath)
                    else:
                        df = pd.read_excel(fpath)
                    
                    DATASETS[dataset_id] = {
                        "df": df,
                        "name": doc["name"],
                        "status": doc["status"],
                        "pii_tags": doc.get("pii_tags", []),
                        "atlas_guid": doc.get("atlas_guid")
                    }
                    print(f"✅ Reloaded {dataset_id} into cache")
                except Exception as re:
                    print(f"❌ Reload Failed: {re}")
                    raise HTTPException(500, f"Error reloading dataset: {str(re)}")
            else:
                raise HTTPException(404, "Dataset not found in persistent storage")
        else:
            raise HTTPException(404, "Dataset not found (and DB disconnected)")
    
    df = DATASETS[dataset_id]["df"]
    
    # If sampling requested, take first 5 records
    if sample:
        df = df.head(5)
        
    # Convert dates to ISO string to handle non-serializable objects
    json_data = json.loads(df.to_json(orient="records", date_format="iso"))
    
    return {
        "dataset_id": dataset_id,
        "filename": DATASETS[dataset_id]["name"],
        "data": json_data
    }

@router.get("/datasets/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str, rows: int = 5):
    """
    Compatibility alias for previewing datasets.
    """
    res = await get_dataset_json(dataset_id, sample=True)
    return {"preview": res["data"][:rows]}

@router.get("/profile/{dataset_id}", response_class=HTMLResponse)
async def get_profile(dataset_id: str):
    """
    US-CLEAN-02: HTML Profiling Report (ydata-profiling)
    """
    # Auto-reload if needed
    await get_dataset_json(dataset_id)
        
    df = DATASETS[dataset_id]["df"]
    
    # Generate report
    html_report = DataProfiler.generate_report(df, title=f"Profile: {DATASETS[dataset_id]['name']}")
    return html_report

@router.post("/clean/{dataset_id}")
async def clean_dataset(dataset_id: str, 
                        remove_duplicates: bool = True,
                        remove_outliers: bool = True,
                        handle_missing: str = "mean",
                        normalize: bool = False):
    """
    US-CLEAN-03: Trigger Cleaning Pipeline
    """
    # Auto-reload if needed
    await get_dataset_json(dataset_id)
    
    df = DATASETS[dataset_id]["df"]
    config = {
        "remove_duplicates": remove_duplicates,
        "remove_outliers": remove_outliers,
        "handle_missing": handle_missing,
        "normalize": normalize
    }
    
    pipeline = CleaningPipeline(df, config)
    clean_df, metrics = pipeline.run()
    
    # Save cleaned version
    DATASETS[dataset_id]["df"] = clean_df
    DATASETS[dataset_id]["status"] = "cleaned"
    
    return {
        "success": True,
        "dataset_id": dataset_id,
        "metrics": metrics
    }

@router.get("/download/{dataset_id}")
async def download_dataset(dataset_id: str):
    """
    US-CLEAN-04: Download Cleaned CSV
    """
    # Auto-reload if needed
    await get_dataset_json(dataset_id)
        
    df = DATASETS[dataset_id]["df"]
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=cleaned_{DATASETS[dataset_id]['name']}"
    return response


@router.get("/metrics/{dataset_id}")

@router.get("/metrics/{dataset_id}")
async def get_metrics(dataset_id: str):
    """
    US-CLEAN-05: Metadata View
    """
    # Reuse the JSON lookup logic for auto-cache loading
    await get_dataset_json(dataset_id)
    
    df = DATASETS[dataset_id]["df"]
    return DataProfiler.get_basic_stats(df)

@router.get("/datasets")
async def list_datasets():
    """
    US-CLEAN-05: List all active datasets for discovery.
    Enhanced to return metadata for de-mocking and Atlas sync.
    """
    datasets_list = []
    
    # Fetch from MongoDB if available
    if raw_datasets_col is not None:
        cursor = raw_datasets_col.find({}, {"_id": 0}).sort("created_at", -1)
        results = await cursor.to_list(length=100)
        
        # Initialize Atlas Client if needed for sync
        atlas = AtlasClient() if AtlasClient else None
        
        for d in results:
            # Live Sync with Atlas for Tags
            tags = d.get("pii_tags", [])
            guid = d.get("atlas_guid")
            
            if atlas and guid and guid != "mock-guid-fallback":
                atlas_tags = atlas.get_classifications(guid)
                if atlas_tags:
                    # Merge and unique
                    tags = list(set(tags + atlas_tags))
            
            datasets_list.append({
                "id": d.get("dataset_id", "unknown"),
                "name": d.get("name", "Unnamed Dataset"),
                "status": d.get("status", "raw"),
                "rows": d.get("rows", 0),
                "columns": d.get("columns", 0),
                "pii_tags": tags,
                "classification": "CONFIDENTIAL" if tags else "PUBLIC",
                "domain": "Finance" if any(t in ["IBAN", "CREDIT_CARD"] for t in tags) else "General",
                "date": d.get("created_at"),
                "owner": d.get("owner", "annotator"),
                "atlas_guid": guid
            })
        return datasets_list

    # Fallback to cache
    atlas = AtlasClient() if AtlasClient else None
    for k, v in DATASETS.items():
        tags = v.get("pii_tags", [])
        guid = v.get("atlas_guid")
        if atlas and guid and guid != "mock-guid-fallback":
            atlas_tags = atlas.get_classifications(guid)
            if atlas_tags:
                tags = list(set(tags + atlas_tags))
                
        datasets_list.append({
            "id": k,
            "name": v.get("name", "Unnamed"),
            "status": v.get("status", "unknown"),
            "rows": len(v["df"]) if "df" in v else 0,
            "columns": len(v["df"].columns) if "df" in v else 0,
            "pii_tags": tags,
            "classification": "CONFIDENTIAL" if tags else "PUBLIC",
            "domain": "Finance" if any(t in ["IBAN", "CREDIT_CARD"] for t in tags) else "General",
            "date": datetime.now().isoformat(),
            "owner": "annotator",
            "atlas_guid": guid
        })
    return datasets_list

@router.get("/stats")
async def get_cleaning_stats():
    """
    Aggregate stats for Dashboard
    """
    total_rows = sum(len(v["df"]) for v in DATASETS.values())
    total_datasets = len(DATASETS)
    pii_counts = {}
    for v in DATASETS.values():
        for tag in v.get("pii_tags", []):
            pii_counts[tag] = pii_counts.get(tag, 0) + 1
            
    return {
        "total_datasets": total_datasets,
        "total_rows": total_rows,
        "active_pipelines": len([v for v in DATASETS.values() if v["status"] == "processing_pipeline"]),
        "pii_distribution": pii_counts
    }

@router.get("/audit-logs")
async def get_cleaning_audit():
    """
    Ingestion logs for Forensic Ledger
    """
    from datetime import datetime
    logs = []
    for k, v in DATASETS.items():
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "service": "INGESTION",
            "action": f"DATASET_UPLOAD: {v['name']}",
            "user": "admin",
            "status": "INFO",
            "details": {"dataset_id": k, "rows": len(v["df"])}
        })
    return {"logs": logs}


@router.get("/datasets/{dataset_id}/lineage")
async def get_lineage(dataset_id: str):
    """
    US-CLEAN-06: Atlas Lineage Graph (Real Integration)
    """
    # Auto-reload if needed
    await get_dataset_json(dataset_id)
    
    guid = DATASETS[dataset_id].get("atlas_guid")
    
    if AtlasClient and guid and guid != "mock-guid-fallback":
        atlas = AtlasClient()
        lineage_data = await atlas.get_lineage(guid)
        
        if lineage_data:
            # Transform Atlas Lineage format to our UI format (nodes/edges)
            nodes = []
            edges = []
            
            entities = lineage_data.get("guidEntityMap", {})
            for g, entity in entities.items():
                nodes.append({
                    "id": g,
                    "label": entity.get("attributes", {}).get("name", entity.get("typeName")),
                    "type": entity.get("typeName")
                })
            
            relations = lineage_data.get("relations", [])
            for rel in relations:
                edges.append({
                    "source": rel.get("fromEntityGuid"),
                    "target": rel.get("toEntityGuid")
                })
                
            return {
                "dataset_id": dataset_id,
                "nodes": nodes,
                "edges": edges,
                "provider": "Apache Atlas"
            }

    # Mock Fallback if Atlas is missing or GUID is mock
    return {
        "dataset_id": dataset_id,
        "nodes": [
            {"id": "source", "label": DATASETS[dataset_id]["name"], "type": "DataSet"},
            {"id": "process", "label": "Cleaning Pipeline", "type": "Process"},
            {"id": "target", "label": f"Cleaned_{DATASETS[dataset_id]['name']}", "type": "DataSet"}
        ],
        "edges": [
            {"source": "source", "target": "process"},
            {"source": "process", "target": "target"}
        ],
        "provider": "Mock (Atlas Disconnected)"
    }

from fastapi import Body

@router.post("/trigger-pipeline")
async def trigger_airflow_pipeline(dataset_id: Optional[str] = None, payload: Optional[TriggerPayload] = Body(None)):
    """
    US-ANNOTATOR-01: Trigger Airflow Pipeline (Real Implementation)
    """
    effective_id = dataset_id or (payload.dataset_id if payload else None)
    
    if not effective_id:
        raise HTTPException(400, "dataset_id is required")
        
    dag_id = payload.dag_id if payload and payload.dag_id != "cleaning_pipeline_v1" else "datagov_pipeline"
    
    exists = False
    dataset_name = payload.dataset_name if payload else "Dataset"
    
    if effective_id in DATASETS:
        exists = True
        dataset_name = DATASETS[effective_id].get("name", dataset_name)
    elif raw_datasets_col is not None:
        doc = await raw_datasets_col.find_one({"dataset_id": effective_id})
        if doc:
            exists = True
            dataset_name = doc.get("name", dataset_name)

    if not exists:
        raise HTTPException(404, f"Dataset {effective_id} not found")
    
    detections_count = len(payload.detections) if payload and payload.detections else 0
    
    # --- ACTIVATE AIRFLOW REST API TRIGGER ---
    AIRFLOW_API_URL = os.getenv("AIRFLOW_URL", "http://airflow:8080/api/v1")
    AIRFLOW_AUTH = ("admin", "admin")
    
    airflow_success = False
    airflow_msg = ""
    
    try:
        print(f"🚀 Triggering Airflow DAG: {dag_id} for Dataset: {effective_id}")
        trigger_url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"
        
        run_payload = {
            "conf": {
                "dataset_id": effective_id,
                "dataset_name": dataset_name,
                "detections": [d.dict() for d in payload.detections] if payload and payload.detections else []
            }
        }
        
        resp = requests.post(trigger_url, json=run_payload, auth=AIRFLOW_AUTH, timeout=10)
        
        if resp.status_code in [200, 201]:
            airflow_success = True
            airflow_msg = "Pipeline successfully triggered on Apache Airflow."
            print(f"✅ Airflow respond: {resp.status_code}")
        else:
            airflow_msg = f"Airflow API error ({resp.status_code}): {resp.text}"
            print(f"⚠️ Airflow Trigger Error: {airflow_msg}")
            
    except Exception as ae:
        airflow_msg = f"Failed to connect to Airflow: {str(ae)}"
        print(f"❌ Airflow Connection Failed: {airflow_msg}")

    # Metadata update and Audit
    if raw_datasets_col is not None:
        update_data = {"status": "processing_pipeline"}
        if payload and payload.detections:
            pii_tags = list(set([d.entity_type for d in payload.detections]))
            update_data["pii_tags"] = pii_tags
            
        await raw_datasets_col.update_one({"dataset_id": effective_id}, {"$set": update_data})
        await log_audit_event("AIRFLOW", f"PIPELINE_TRIGGERED: {dag_id}", "system", "SUCCESS" if airflow_success else "FAILURE", {
            "dataset_id": effective_id,
            "airflow_response": airflow_msg
        })
        
        # Forward to Annotation Service (Tâche 7)
        if payload and payload.detections:
            try:
                sample_data = {"filename": dataset_name}
                if payload.detections:
                    sample_data["preview"] = payload.detections[0].value
                
                requests.post(f"{ANNOTATION_SERVICE_URL}/tasks", json={
                    "dataset_id": effective_id,
                    "annotation_type": "pii_validation",
                    "priority": "high",
                    "detections": [d.dict() for d in payload.detections],
                    "row_indices": [0],
                    "data_samples": [sample_data]
                }, timeout=5)
            except: pass

    if effective_id in DATASETS:
        DATASETS[effective_id]["status"] = "processing_pipeline"
    
    return {
        "success": airflow_success,
        "status": "triggered" if airflow_success else "failed",
        "dag_id": dag_id,
        "execution_date": datetime.utcnow().isoformat(),
        "message": airflow_msg,
        "detections_count": detections_count
    }
