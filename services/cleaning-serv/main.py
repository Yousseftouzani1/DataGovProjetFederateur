from fastapi import FastAPI, UploadFile, File, HTTPException
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

app = FastAPI(title="Cleaning Service", version="1.0")


# --------------------------------------------------
# Upload dataset
# --------------------------------------------------
@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")

    dataset_id = str(uuid.uuid4())

    await save_raw_dataset(dataset_id, df)

    return {
        "dataset_id": dataset_id,
        "rows": len(df),
        "columns": list(df.columns)
    }


# --------------------------------------------------
# Profiling endpoint
# --------------------------------------------------
@app.get("/profile/{dataset_id}")
async def profile(dataset_id: str):
    data = await load_raw_dataset(dataset_id)

    if data is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = pd.DataFrame(data)

    profile_result = profile_dataset(df)

    await save_metadata(dataset_id, profile_result, metadata_type="profiling")

    return profile_result


# --------------------------------------------------
# Cleaning endpoint
# --------------------------------------------------
@app.post("/clean/{dataset_id}")
async def clean(dataset_id: str, config: dict):
    data = await load_raw_dataset(dataset_id)

    if data is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = pd.DataFrame(data)

    clean_df, metrics = clean_dataframe(df, config)

    await save_clean_dataset(dataset_id, clean_df)
    await save_metadata(dataset_id, metrics, metadata_type="cleaning")

    return {
        "dataset_id": dataset_id,
        "metrics": metrics,
        "rows_after_cleaning": len(clean_df)
    }


# --------------------------------------------------
# Health check (for Docker / Airflow)
# --------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "UP"}
