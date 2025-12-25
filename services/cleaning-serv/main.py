from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import uuid

from backend.cleaning_engine import clean_dataframe
from backend.profiling_engine import profile_dataset
from backend.storage import (
    save_raw_dataset,
    load_raw_dataset,
    save_clean_dataset,
    save_metadata
)

# Add common services to path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../common")))

try:
    from atlas_client import AtlasClient
    atlas_client = AtlasClient()
except ImportError:
    print("⚠️ Could not import AtlasClient. Governance features disabled.")
    atlas_client = None

app = FastAPI(title="Cleaning Service", version="2.0")

# CORS for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for quick access (MongoDB is primary storage)
datasets_cache = {}


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
        await save_raw_dataset(dataset_id, df)
    except Exception as e:
        print(f"MongoDB save warning: {e}")
    
    # Register in Atlas
    if atlas_client:
        try:
            atlas_client.register_dataset(
                name=file.filename,
                description=f"Uploaded dataset {file.filename}",
                owner="admin", # TODO: Get from token
                file_path=f"mongodb://datasets/{dataset_id}"
            )
        except Exception as e:
            print(f"⚠️ Atlas registration failed: {e}")
    
    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns)
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
# Profiling endpoint
# --------------------------------------------------
@app.get("/profile/{dataset_id}")
async def profile(dataset_id: str):
    df = await _get_dataframe(dataset_id)
    profile_result = profile_dataset(df)
    
    try:
        await save_metadata(dataset_id, profile_result, metadata_type="profiling")
    except:
        pass
    
    return profile_result


# --------------------------------------------------
# Cleaning endpoint (with config)
# --------------------------------------------------
@app.post("/clean/{dataset_id}")
async def clean(dataset_id: str, config: dict = None):
    if config is None:
        config = {}
    
    df = await _get_dataframe(dataset_id)
    clean_df, metrics = clean_dataframe(df, config)
    
    # Update cache
    datasets_cache[dataset_id] = {
        "df": clean_df,
        "filename": datasets_cache.get(dataset_id, {}).get("filename", "cleaned")
    }
    
    try:
        await save_clean_dataset(dataset_id, clean_df)
        await save_metadata(dataset_id, metrics, metadata_type="cleaning")
    except:
        pass
    
    return {
        "dataset_id": dataset_id,
        "success": True,
        "original_rows": metrics.get("rows_before", 0),
        "cleaned_rows": metrics.get("rows_after", len(clean_df)),
        "rows_removed": metrics.get("rows_before", 0) - metrics.get("rows_after", len(clean_df)),
        "metrics": metrics
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