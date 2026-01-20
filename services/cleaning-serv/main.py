from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import uuid

from backend.cleaning_engine import clean_dataframe, generate_profile
from backend.storage import (
    save_raw_dataset,
    load_raw_dataset,
    save_clean_dataset,
    save_metadata,
    log_audit_event,
    get_recent_audit_logs,
    audit_logs_col,
    raw_datasets_col,
    clean_datasets_col,
    metadata_col
)


try:
    # Try importing from proper integration module first
    from atlas_integration.client import AtlasClient
    atlas_client = AtlasClient()
    # Auto-setup classification types for production
    if hasattr(atlas_client, 'ensure_classification_types'):
        atlas_client.ensure_classification_types()
    print("🔌 Loaded AtlasClient from atlas_integration")
except ImportError:
    try:
        # Fallback to common library (sys.path hack)
        import sys
        sys.path.insert(0, '/common')
        from atlas_client import AtlasClient
        atlas_client = AtlasClient()
        if hasattr(atlas_client, '_ensure_classification_types'):
            atlas_client._ensure_classification_types()
        print("🔌 Loaded AtlasClient from /common (Fallback)")
    except Exception as e:
        print(f"⚠️ Could not import AtlasClient: {e}. Governance features disabled.")
        atlas_client = None
except Exception as e:
    print(f"⚠️ Error initializing AtlasClient: {e}")
    atlas_client = None

# from backend.storage import raw_datasets_col, clean_datasets_col, metadata_col # Imported above

# =======================================================
# RANGER INTEGRATION - Per Cahier des Charges Section 3.6
# =======================================================
import requests as ranger_requests
import os

# Configuration via environment variables for flexibility
RANGER_URL = os.getenv("RANGER_URL", "http://localhost:6080")
RANGER_AUTH = (os.getenv("RANGER_USER", "admin"), os.getenv("RANGER_PASS", "hortonworks1"))
RANGER_BYPASS = os.getenv("RANGER_BYPASS", "false").lower() == "true"

class AccessDecision:
    ALLOWED = "allowed"
    DENIED = "denied"
    MASKED = "masked"

def check_ranger_permission(username: str, resource_tag: str = "PII"):
    """
    Check Ranger for user permission on tagged resources.
    Per Cahier des Charges: FastAPI → Ranger REST API
    """
    # Bypass for local testing without Ranger
    if RANGER_BYPASS:
        print(f"🔓 RANGER BYPASS: Granting full access to '{username}'")
        return {"decision": AccessDecision.ALLOWED, "reason": "Bypassed for testing"}

    try:
        # Direct Ranger API call - most reliable method
        resp = ranger_requests.get(
            f"{RANGER_URL}/service/plugins/policies",
            params={"serviceName": "data_gov_tags"},
            auth=RANGER_AUTH,
            timeout=2 # Faster timeout for local testing
        )
        
        if resp.status_code != 200:
            print(f"⚠️ Ranger API returned {resp.status_code}")
            # Default DENY if Ranger is down (security-first)
            return {"decision": AccessDecision.DENIED, "reason": f"Ranger returned {resp.status_code}"}
        
        policies = resp.json().get('policies', [])
        
        # Check policies (Simple linear scan for matching user/tag)
        is_allowed = False
        is_denied = False
        
        for policy in policies:
            if not policy.get('isEnabled', False):
                continue
            
            # Check tag match
            resource_resources = policy.get('resources', {})
            tag_resource = resource_resources.get('tag', {})
            policy_tags = tag_resource.get('values', [])
            
            if resource_tag not in policy_tags:
                continue
            
            # Check allow items
            for allow_item in policy.get('policyItems', []):
                if username in allow_item.get('users', []) or 'public' in allow_item.get('groups', []):
                    is_allowed = True
            
            # Check deny items
            for deny_item in policy.get('denyPolicyItems', []):
                if username in deny_item.get('users', []) or 'public' in deny_item.get('groups', []):
                    is_denied = True
        
        # Explicit allow overrides public deny in some logic, but usually Deny wins.
        # Here we follow a simple Allow-then-Deny check.
        if is_denied:
            return {"decision": AccessDecision.DENIED, "reason": "Denied by policy"}
        
        if is_allowed:
            return {"decision": AccessDecision.ALLOWED}
        
        # Default deny if no explicit allow
        return {"decision": AccessDecision.DENIED, "reason": "No explicit allow policy"}
        
    except Exception as e:
        print(f"⚠️ Ranger check failed: {e}")
        # Default DENY if Ranger is unreachable (security-first)
        return {"decision": AccessDecision.DENIED, "reason": f"Connection failed: {str(e)}"}


app = FastAPI(title="Cleaning Service", version="2.0")

@app.middleware("http")
async def set_root_path(request: Request, call_next):
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    return response

# CORS for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for reports
from fastapi.staticfiles import StaticFiles
os.makedirs("static/reports", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory cache for quick access (MongoDB is primary storage)
datasets_cache = {}

# Access log for audit trail
access_log = []


# --------------------------------------------------
# HEALTH AND AUDIT ENDPOINTS
# --------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "cleaning-service"}

@app.get("/audit-logs")
async def get_audit_logs():
    """
    Returns system audit logs from MongoDB.
    """
    try:
        logs = await get_recent_audit_logs(limit=50)
        return logs
    except Exception as e:
        print(f"⚠️ Failed to fetch audit logs: {e}")
        return []



# --------------------------------------------------
# RANGER PERMISSIONS ENDPOINT (For Frontend)
# --------------------------------------------------
@app.get("/permissions")
async def get_user_permissions(username: str = Query(...), role: str = Query(default="unknown")):
    """
    Returns user's access permissions for frontend to use.
    Per Cahier des Charges: Frontend awareness of Ranger policies.
    
    Returns:
        - access_level: "full", "masked", "denied"
        - can_view_pii: bool
        - can_view_spi: bool
        - mask_type: if masked, which type (MASK, HASH, etc.)
    """
    from datetime import datetime
    
    # Check "PII" tag permission
    ranger_check = check_ranger_permission(username, "PII")
    
    print(f"🔒 Ranger Permission Check for {username}: {ranger_check}")
    
    return {
        "access_level": "full" if ranger_check['decision'] == AccessDecision.ALLOWED else "denied",
        "can_view_pii": ranger_check['decision'] == AccessDecision.ALLOWED,
        "can_view_spi": False, # Future use
        "ranger_decision": ranger_check
    }

    # Check PII permission
    pii_permission = check_ranger_permission(username, "PII")
    spi_permission = check_ranger_permission(username, "SPI")
    
    # Determine access level
    pii_decision = pii_permission.get("decision", AccessDecision.DENIED)
    spi_decision = spi_permission.get("decision", AccessDecision.DENIED)
    
    # Map decisions to frontend-friendly format
    if pii_decision == AccessDecision.ALLOWED:
        access_level = "full"
        can_view_pii = True
    elif pii_decision == AccessDecision.MASKED:
        access_level = "masked"
        can_view_pii = True  # Can view but masked
    else:
        access_level = "denied"
        can_view_pii = False
    
    # Log this access check (Audit Trail)
    # Use await log_audit_event from persistent storage
    await log_audit_event(
        service="RANGER",
        action="PERMISSION_CHECK",
        user=username,
        status="INFO" if pii_decision == AccessDecision.ALLOWED else "WARNING",
        details={
            "role": role,
            "pii_decision": str(pii_decision),
            "spi_decision": str(spi_decision),
            "ranger_reachable": ranger_reached
        }
    )
    
    print(f"🔐 Access Check: {username} ({role}) → PII:{pii_decision}, SPI:{spi_decision}")
    
    # Determine if Ranger API was actually reached
    ranger_reached = pii_permission.get("reason") != "Ranger unavailable"
    
    return {
        "username": username,
        "role": role,
        "access_level": access_level,
        "can_view_pii": can_view_pii,
        "can_view_spi": spi_decision == AccessDecision.ALLOWED,
        "mask_type": pii_permission.get("mask_type") if access_level == "masked" else None,
        "ranger_connected": ranger_reached
    }


@app.get("/access-log")
async def get_access_log(limit: int = Query(default=50)):
    """Return recent access log entries for audit trail"""
    return {"entries": access_log[-limit:]}


# --------------------------------------------------
# Upload dataset (supports CSV, Excel, JSON)
# --------------------------------------------------
@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(contents))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, Excel, or JSON.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file: {str(e)}")

    dataset_id = str(uuid.uuid4())
    
    # Cache for quick access
    datasets_cache[dataset_id] = {
        "df": df,
        "filename": file.filename
    }
    
    # Try to save to MongoDB (non-blocking if fails)
    try:
        await save_raw_dataset(dataset_id, df, filename=file.filename)
    except Exception as e:
        print(f"MongoDB save warning: {e}")
    
    # Register in Atlas and get GUID for later classification
    atlas_guid = None
    if atlas_client:
        try:
            atlas_guid = atlas_client.register_dataset_and_get_guid(
                name=file.filename,
                description=f"Uploaded dataset {file.filename}",
                owner="admin", # TODO: Get from token
                file_path=f"mongodb://datasets/{dataset_id}"
            )
        except Exception as e:
            print(f"⚠️ Atlas registration failed: {e}")
    
    # Log audit event for dataset upload
    await log_audit_event(
        service="CLEANING",
        action="DATASET_UPLOAD",
        user="admin",  # TODO: Get from token
        status="INFO",
        details={
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns)
        }
    )
    
    # -------------------------------------------------------------------------
    # TRIGGER AIRFLOW DAG (Critical Fix)
    # -------------------------------------------------------------------------
    try:
        import requests
        print(f"🚀 Triggering Airflow DAG for {file.filename}...")
        airflow_url = "http://airflow:8080/api/v1/dags/data_processing_pipeline/dagRuns"
        response = requests.post(
            airflow_url,
            json={"conf": {"dataset_id": dataset_id, "filename": file.filename}},
            auth=("admin", "admin")
        )
        if response.status_code == 200:
            print("✅ Airflow DAG triggered successfully")
        else:
            print(f"⚠️ Airflow Trigger Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Could not trigger Airflow: {e}")

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "atlas_guid": atlas_guid,  # For PII classification later
        "airflow_triggered": True
    }


# --------------------------------------------------
# Get dataset info
# --------------------------------------------------
@app.get("/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    df = await _get_dataframe(dataset_id)
    return {
        "dataset_id": dataset_id,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns)
    }


# --------------------------------------------------
# Get full dataset data (for quality-service integration)
# --------------------------------------------------
@app.get("/dataset/{dataset_id}")
async def get_dataset_full(dataset_id: str):
    """Return full dataset records for quality evaluation"""
    df = await _get_dataframe(dataset_id)
    # Get metadata for filename
    metadata = await load_raw_dataset(dataset_id)
    filename = "unknown"
    if metadata and "filename" in str(metadata):
        filename = dataset_id  # Fallback to ID
    
    return {
        "data": df.fillna("").to_dict(orient="records"),
        "filename": filename,
        "rows": len(df),
        "columns": len(df.columns)
    }


# --------------------------------------------------
# Preview dataset (REQUIRED by frontend)
# --------------------------------------------------
@app.get("/datasets/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, rows: int = Query(default=10, le=1000)):
    df = await _get_dataframe(dataset_id)
    preview_df = df.head(rows).fillna("")
    return {
        "dataset_id": dataset_id,
        "preview": preview_df.to_dict(orient="records"),
        "showing": len(preview_df)
    }


# --------------------------------------------------
# Profiling endpoint - CDC Section 6.4.1
# --------------------------------------------------
@app.get("/profile/{dataset_id}")
async def profile(dataset_id: str):
    """
    Generate a full profiling report (HTML + JSON).
    Usage: GET /profile/{dataset_id}
    """
    df = await _get_dataframe(dataset_id)
    
    # Generate profile using the new engine
    profile_report, metrics = generate_profile(df)
    
    # Save the HTML report to a local static folder for viewing
    report_dir = "static/reports"
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/profile_{dataset_id}.html"
    profile_report.to_file(report_path)
    
    # Save metadata to MongoDB
    try:
        metrics["report_url"] = f"/static/reports/profile_{dataset_id}.html"
        await save_metadata(dataset_id, metrics, metadata_type="profiling")
    except Exception as e:
        print(f"⚠️ Metadata save failed: {e}")
    
    return {
        "dataset_id": dataset_id,
        "metrics": metrics,
        "report_url": metrics["report_url"]
    }

@app.get("/reports/{dataset_id}/summary")
async def get_cleaning_summary(dataset_id: str):
    """
    Returns a beautiful HTML summary of the cleaning process.
    """
    from fastapi.responses import HTMLResponse
    
    # Fetch metrics from MongoDB
    meta = await metadata_col.find_one({"dataset_id": dataset_id, "type": "cleaning"}, sort=[("created_at", -1)])
    if not meta:
        raise HTTPException(status_code=404, detail="Cleaning metrics not found for this dataset.")
    
    metrics = meta["metadata"]
    
    # Create a beautiful HTML summary
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
                .container {{ max-width: 800px; margin: auto; background: #1e293b; padding: 40px; border-radius: 24px; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); }}
                h1 {{ color: #38bdf8; font-size: 2.5rem; margin-bottom: 30px; }}
                .stat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 40px; }}
                .stat-card {{ background: #0f172a; padding: 20px; border-radius: 16px; border: 1px solid #334155; }}
                .stat-value {{ font-size: 1.5rem; font-weight: bold; color: #fff; }}
                .stat-label {{ font-size: 0.875rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
                .score {{ font-size: 4rem; font-weight: 800; color: #10b981; }}
                .step-list {{ list-style: none; padding: 0; }}
                .step-item {{ padding: 15px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
                .step-name {{ font-weight: 600; text-transform: capitalize; }}
                .tag {{ padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; }}
                .tag-success {{ background: #065f46; color: #34d399; }}
                .tag-warning {{ background: #78350f; color: #fbbf24; }}
                .badge-iso {{ border: 2px solid #10b981; color: #10b981; padding: 10px 20px; border-radius: 12px; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Cleaning Report</h1>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-label">Initial Rows</div>
                        <div class="stat-value">{metrics.get('rows_before', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Cleaned Rows</div>
                        <div class="stat-value">{metrics.get('rows_after', 0)}</div>
                    </div>
                </div>
                
                <center>
                    <div class="stat-label">Cleaning Quality Score</div>
                    <div class="score">{metrics.get('cleaning_score', 0)}%</div>
                    <div class="badge-iso">CDC COMPLIANT</div>
                </center>
                
                <h2 style="margin-top: 50px;">Processing Steps</h2>
                <ul class="step-list">
    """
    
    for step in metrics.get("steps", []):
        name = step.get("step")
        removed = step.get("removed", 0)
        corrected = step.get("corrected", 0)
        info = f"Removed {removed}" if removed > 0 else f"Corrected {corrected}" if corrected > 0 else "Completed"
        
        html_content += f"""
                    <li class="step-item">
                        <span class="step-name">{name.replace('_', ' ')}</span>
                        <span class="tag tag-success">{info}</span>
                    </li>
        """
        
    html_content += """
                </ul>
                <div style="margin-top: 40px; text-align: center; color: #64748b; font-size: 0.875rem;">
                    Generated by DataGov Cleaning Service ISO-CDC Engine v2.0
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# --------------------------------------------------
# Stats & History (NEW for Dashboard)
# --------------------------------------------------
@app.get("/stats")
async def get_stats():
    """Get aggregate statistics for the dashboard"""
    try:
        total_datasets = await raw_datasets_col.count_documents({})
        # Simple heuristic: total records count
        # For performance, in a real app we'd use a metadata counter
        pipeline = [{"$project": {"count": {"$size": "$data"}}}, {"$group": {"_id": None, "total": {"$sum": "$count"}}}]
        cursor = raw_datasets_col.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        total_records = result[0]["total"] if result else 0
        
        return {
            "total_datasets": total_datasets,
            "total_records": total_records,
            "uptime": "100%", # Placeholder or real uptime
            "storage_used": f"{total_datasets * 0.5:.1f} MB" # Simulated
        }
    except Exception as e:
        return {"error": str(e), "total_datasets": 0, "total_records": 0}

@app.get("/datasets")
async def list_datasets(limit: int = Query(default=10, le=100), username: str = Query(default="admin")):
    """
    List recent datasets for the pipeline table.
    RANGER INTEGRATION: Checks user permission before returning data.
    """
    # Check Ranger permission before returning sensitive data
    permission = check_ranger_permission(username, "PII")
    
    if permission.get("decision") == AccessDecision.DENIED:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied by Ranger policy. User '{username}' is not authorized to view PII-tagged datasets."
        )
    
    try:
        cursor = raw_datasets_col.find({}, {"data": 0}).sort("created_at", -1).limit(limit)
        datasets = await cursor.to_list(length=limit)
        
        # Format for frontend
        formatted = []
        for d in datasets:
            formatted.append({
                "id": d["dataset_id"],
                "name": d.get("filename", "unknown_file"),
                "date": d["created_at"].isoformat() if "created_at" in d else None,
                "status": "Ready",
                "type": "Raw"
            })
        return formatted
    except Exception as e:
        return []


@app.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a dataset from the system (Steward/Admin only)"""
    try:
        # Delete from MongoDB
        result = await raw_datasets_col.delete_one({"dataset_id": dataset_id})
        
        # Also delete from clean_datasets if exists
        await clean_datasets_col.delete_one({"dataset_id": dataset_id})
        
        # Also delete from metadata
        await metadata_col.delete_many({"dataset_id": dataset_id})
        
        # Remove from cache if present
        if dataset_id in datasets_cache:
            del datasets_cache[dataset_id]
        
        if result.deleted_count > 0:
            return {"success": True, "message": f"Dataset {dataset_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Dataset not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")


# --------------------------------------------------
# Cleaning endpoint (with config)
# --------------------------------------------------
@app.post("/clean/{dataset_id}")
async def clean(dataset_id: str, config: dict = None):
    if config is None:
        config = {}
    
    df = await _get_dataframe(dataset_id)
    clean_df, metrics = clean_dataframe(df, config)
    
    # KPI Verification - CDC Section 6.4 Compliance
    kpi_warnings = []
    if metrics.get("cleaning_score", 0) < 50:
        kpi_warnings.append("Low cleaning yield: More than 50% of data was removed during cleaning.")
    
    # Ensure no duplicates remain
    if clean_df.duplicated().any():
        kpi_warnings.append("CDC Violation: Duplicates detected in cleaned dataset.")
    
    # Update metrics with warnings
    metrics["kpi_warnings"] = kpi_warnings
    metrics["cdc_compliant"] = len(kpi_warnings) == 0
    
    # Update cache
    datasets_cache[dataset_id] = {
        "df": clean_df,
        "filename": datasets_cache.get(dataset_id, {}).get("filename", "cleaned")
    }
    
    try:
        await save_clean_dataset(dataset_id, clean_df)
        await save_metadata(dataset_id, metrics, metadata_type="cleaning")
        
        # Log success/failure to audit
        await log_audit_event(
            service="CLEANING",
            action="DATA_CLEANED",
            user="admin",
            status="SUCCESS" if metrics["cdc_compliant"] else "WARNING",
            details={
                "dataset_id": dataset_id,
                "score": metrics["cleaning_score"],
                "warnings": kpi_warnings
            }
        )
    except Exception as e:
        print(f"⚠️ Storage failed: {e}")
    
    return {
        "dataset_id": dataset_id,
        "success": True,
        "cdc_compliant": metrics["cdc_compliant"],
        "metrics": metrics,
        "summary_report_url": f"/reports/{dataset_id}/summary"
    }


# --------------------------------------------------
# Auto clean (REQUIRED by frontend)
# --------------------------------------------------
@app.post("/clean/{dataset_id}/auto")
async def auto_clean(dataset_id: str):
    config = {
        "remove_duplicates": True,
        "handle_missing": "mean",
        "remove_outliers": True
    }
    return await clean(dataset_id, config)

# --------------------------------------------------
# Trigger Pipeline - Create Annotation Tasks
# --------------------------------------------------
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PipelineTriggerRequest(BaseModel):
    dataset_id: str
    detections: List[dict]
    dataset_name: Optional[str] = None

@app.post("/trigger-pipeline")
async def trigger_pipeline(request: PipelineTriggerRequest):
    """
    Trigger the pipeline processing after labeler finishes PII detection.
    Creates annotation tasks for the annotator to review.
    """
    from pymongo import MongoClient
    import os
    
    try:
        print(f"🚀 Triggering pipeline for Dataset ID: {request.dataset_id} | Name: {request.dataset_name}")
        
        # Connect to MongoDB Atlas
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "DataGovDB")
        client = MongoClient(mongo_uri)
        db = client[db_name]
        tasks_col = db["tasks"]
        
        # Create annotation tasks for each detection
        tasks_created = []
        for i, detection in enumerate(request.detections):
            # Ensure strict adherence to AnnotationTask definition in annotation-service
            task_id = f"TASK-{request.dataset_id[:8]}-{i+1:03d}-{uuid.uuid4().hex[:4]}"
            
            task = {
                "id": task_id,  # Changed from task_id to id
                "dataset_id": request.dataset_id,
                "row_index": i, # Required field
                "data_sample": detection.get("context", {"text": detection.get("text", "No context")}), # Must be a dict
                "detections": [detection], # Must be a list
                "annotation_type": "pii_validation", # Required field
                "priority": "medium",
                "status": "pending",
                "assigned_to": "annotator_user",
                "annotations": [],
                "created_at": datetime.utcnow().isoformat(), # Must be string
                # Extra metadata
                "created_by": "labeler_user",
                "dataset_name": request.dataset_name or "Unknown"
            }
            tasks_col.insert_one(task)
            tasks_created.append(task["id"])
        
        print(f"✅ Created {len(tasks_created)} annotation tasks for dataset {request.dataset_id}")

        # ---------------------------------------------------------
        # Airflow Integration (As requested by User)
        # ---------------------------------------------------------
        try:
            import requests
            airflow_url = os.getenv("AIRFLOW_URL", "http://airflow:8080")
            dag_id = "data_processing_pipeline"
            
            # Trigger DAG run
            response = requests.post(
                f"{airflow_url}/api/v1/dags/{dag_id}/dagRuns",
                json={"conf": {"dataset_id": request.dataset_id}},
                auth=("admin", "admin"), # Default credentials
                timeout=2 # Short timeout to not block
            )
            if response.status_code == 200:
                print(f"✅ Airflow DAG {dag_id} triggered successfully")
            else:
                print(f"⚠️ Airflow Trigger Warning: {response.status_code} - {response.text}")
        except Exception as af_error:
            print(f"⚠️ Could not trigger Airflow (Soft Fail): {af_error}")
        
        # ---------------------------------------------------------
        # Governance Integration: Update Atlas Classifications
        # ---------------------------------------------------------
        
        # ---------------------------------------------------------
        # 4. Call Classification Service (Task 5) - Compliance Check
        # ---------------------------------------------------------
        classification_result = None
        sensitivity_level = "unknown"
        try:
            # Prepare text for classification (aggregate from detections or task)
            sample_text = ""
            if request.detections:
                # Use context from first few detections (Handle both dict and Pydantic model)
                contexts = []
                for d in request.detections[:3]:
                    # Safe extraction of context
                    ctx = getattr(d, 'context', None)
                    if ctx is None and isinstance(d, dict):
                        ctx = d.get('context')
                    
                    if ctx:
                        # Extract text from context dict
                        contexts.append(ctx.get("text", "") if isinstance(ctx, dict) else str(ctx))
                
                sample_text = " ".join(contexts)
            
            if not sample_text:
                sample_text = "Dataset with PII detections"

            # Call Classification Service
            cls_url = os.getenv("CLASSIFICATION_SERVICE_URL", "http://classification-service:8005")
            cls_resp = requests.post(f"{cls_url}/classify", json={
                "text": sample_text,
                "language": "fr", # Default to FR context
                "use_ml": True
            }, timeout=3)
            
            if cls_resp.status_code == 200:
                classification_result = cls_resp.json()
                sensitivity_level = classification_result.get("sensitivity_level", "unknown")
                print(f"🧠 Classification Service: {classification_result.get('classification')} ({sensitivity_level})")
            else:
                print(f"⚠️ Classification Service Error: {cls_resp.status_code}")

        except Exception as cls_err:
            print(f"⚠️ Could not consult Classification Service: {cls_err}")


        # ---------------------------------------------------------
        # Governance Integration: Update Atlas Classifications
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # Governance Integration: Update Atlas Classifications
        # ---------------------------------------------------------
        print(f"🔍 Starting Governance Update | Client: {bool(atlas_client)} | Detections: {len(request.detections)}")

        if atlas_client and request.detections:
            try:
                # Look up the dataset GUID in Atlas
                dataset_name = request.dataset_name or request.dataset_id
                entity_guid = atlas_client.get_entity_guid(dataset_name)
                
                if entity_guid:
                    print(f"📍 Found Entity GUID: {entity_guid}")
                    
                    # 1. Add PII classification (Specific PII details)
                    # request.detections is already a list of objects or dicts depending on context
                    # Safer approach: check type before converting
                    detections_list = []
                    for d in request.detections:
                        if hasattr(d, 'dict'):
                            detections_list.append(d.dict())
                        else:
                            detections_list.append(d)
                            
                    atlas_client.add_classification_with_attributes(
                        entity_guid=entity_guid,
                        classification="PII",
                        detections=detections_list
                    )
                    
                    # 2. Add SENSITIVITY classification (Based on ML Service)
                    if sensitivity_level in ["critical", "high"]:
                        atlas_client.create_classification(
                            entity_guid=entity_guid, 
                            classification_name="CONFIDENTIAL",
                            attributes={"detectedTypes": classification_result.get("classification", "UNKNOWN")}
                        )
                    elif sensitivity_level == "medium":
                        atlas_client.create_classification(
                            entity_guid=entity_guid, 
                            classification_name="SENSITIVE",
                            attributes={"detectedTypes": classification_result.get("classification", "UNKNOWN")}
                        )

                    # 3. Register PII columns as data_attribute entities
                    atlas_client.register_pii_columns(
                        dataset_guid=entity_guid,
                        dataset_name=dataset_name,
                        detections=detections_list
                    )
                    
                    print(f"🏷️ Governance updated: PII + {sensitivity_level.upper()} tags applied.")
                else:
                    print(f"❌ Could not find Atlas entity for dataset '{dataset_name}'")
            except Exception as atlas_err:
                import traceback
                print(traceback.format_exc())
                print(f"❌ Governance Update Warning: {atlas_err}")
        else:
            print("⚠️ Skipping Governance: No Client or No Detections")


        return {
            "success": True,
            "message": f"Pipeline triggered! Created {len(tasks_created)} tasks. Airflow notified. Governance updated.",
            "tasks_created": len(tasks_created),
            "task_ids": tasks_created[:10]
        }
        
    except Exception as e:
        print(f"❌ Pipeline trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline trigger failed: {str(e)}")


# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "UP"}


# --------------------------------------------------
# Helper function
# --------------------------------------------------
async def _get_dataframe(dataset_id: str) -> pd.DataFrame:
    # Check cache first
    if dataset_id in datasets_cache:
        return datasets_cache[dataset_id]["df"]
    
    # Try MongoDB
    try:
        data = await load_raw_dataset(dataset_id)
        if data:
            df = pd.DataFrame(data)
            datasets_cache[dataset_id] = {"df": df, "filename": "from_db"}
            return df
    except:
        pass
    
    raise HTTPException(status_code=404, detail="Dataset not found")