
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
from pymongo import MongoClient
import os
import sys

# Add common to path to import AtlasClient
sys.path.append("/common")
# Try importing AtlasClient, handle failure if common volume not mounted yet
try:
    from atlas_client import AtlasClient
except ImportError:
    AtlasClient = None

from ..ml_models.ensemble import EnsembleClassifier

router = APIRouter(prefix="/classification", tags=["Classification (Tâche 5)"])

# Load model ONCE at startup
classifier = EnsembleClassifier() 

# Database Setup (US-CLASS-04 Persistence)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://datagov-mongo:27017")
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["datagov_classification"]
    history_col = db["classification_history"]
except Exception as e:
    print(f"⚠️ Warning: MongoDB not connected: {e}")
    history_col = None

# Atlas Setup (US-CLASS-05)
atlas_client = AtlasClient() if AtlasClient else None

class ClassificationRequest(BaseModel):
    dataset_id: str
    data_sample: Dict[str, List[Any]] 
    # Optional GUIDs for Atlas tagging
    # col_guids: Dict[str, str] = None 

@router.post("/classify")
async def classify_dataset(request: ClassificationRequest, background_tasks: BackgroundTasks):
    """
    US-CLASS-01: Automatically classify every column.
    """
    results = {}
    
    for col_name, values in request.data_sample.items():
        # Clean nulls
        clean_vals = [v for v in values if v is not None]
        
        # Run Ensemble
        res = classifier.classify_column(col_name, clean_vals)
        results[col_name] = res
        
        # US-CLASS-05: Integrate with Atlas
        # Tag the column in Atlas with the classification code (e.g., PII, SPI)
        if atlas_client and request.dataset_id:
            background_tasks.add_task(tag_in_atlas, request.dataset_id, col_name, res['code'])

async def tag_in_atlas(dataset_id: str, col_name: str, classification_code: str):
    """
    Push classification tag to Atlas entity.
    """
    if not atlas_client:
        return

    try:
        # 1. Find the column entity GUID (or dataset GUID first)
        # For simplicity in this demo, we assume dataset_id is the name
        dataset_guid = atlas_client.get_entity_guid(dataset_id)
        
        if dataset_guid:
            # 2. In a real real-world scenario, we'd tag the COLUMN entity.
            # Here we might tag the DATASET with a detailed attribute or try to find the column.
            # Let's use the 'register_pii_columns' helper which does exactly this.
            
            detection = {
                "field": col_name,
                "type": classification_code,
                "confidence": 0.95 # Assumed from Ensemble
            }
            
            atlas_client.register_pii_columns(dataset_guid, dataset_id, [detection])
            print(f"✅ [Atlas] Tagged {col_name} as {classification_code} in {dataset_id}")
            
    except Exception as e:
        print(f"⚠️ [Atlas] Failed to tag {col_name}: {e}")

    # Persistence for US-CLASS-04 (Visualization)
    if history_col is not None:
        doc = {
            "dataset_id": request.dataset_id,
            "classifications": results,
            "stats": {
                "total_cols": len(results),
                "pii_cols": sum(1 for r in results.values() if r['level'] >= 3)
            }
        }
        history_col.insert_one(doc)
        
    return {
        "dataset_id": request.dataset_id,
        "classifications": results
    }

@router.get("/stats")
async def get_classification_stats():
    """
    US-CLASS-04: Get classification statistics for visualization.
    """
    if history_col is None:
        return {"error": "Database not connected"}
        
    # Aggregate total classes
    pipeline = [
        {"$project": {"classifications": {"$objectToArray": "$classifications"}}},
        {"$unwind": "$classifications"},
        {"$group": {
            "_id": "$classifications.v.code",
            "count": {"$sum": 1}
        }}
    ]
    
    stats = list(history_col.aggregate(pipeline))
    formatted = {item["_id"]: item["count"] for item in stats}
    
    return {
        "global_distribution": formatted,
        "total_datasets": history_col.count_documents({})
    }

@router.get("/config")
async def get_config():
    """
    US-CLASS-02 (Part 1): Get Thresholds
    """
    return {
        "weights": classifier.weights,
        "manual_review_threshold": classifier.manual_review_threshold
    }

class ConfigUpdate(BaseModel):
    weights: Dict[str, float]
    manual_review_threshold: float

@router.post("/config")
async def update_config(config: ConfigUpdate):
    """
    US-CLASS-02 (Part 2): Allow Data Steward to adjust thresholds.
    """
    classifier.weights = config.weights
    classifier.manual_review_threshold = config.manual_review_threshold
    return {"message": "Configuration updated", "new_config": config}

@router.post("/retrain")
async def retrain_model():
    """
    US-CLASS-03: Trigger ensemble model retraining with new data.
    """
    # Triggering the internal re-fit logic
    success = classifier.fit() # Assuming fit exists in EnsembleClassifier
    return {"status": "success" if success else "failed", "message": "Model retraining triggered"}
