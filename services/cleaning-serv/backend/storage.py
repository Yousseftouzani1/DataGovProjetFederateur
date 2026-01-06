from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from bson import ObjectId


# --------------------------------------------------
# MongoDB configuration (via environment variables)
# --------------------------------------------------
MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "datagov")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]


# Collections
raw_datasets_col = db["raw_datasets"]
clean_datasets_col = db["clean_datasets"]
metadata_col = db["cleaning_metadata"]


# --------------------------------------------------
# Save raw dataset
# --------------------------------------------------
async def save_raw_dataset(dataset_id: str, df):
    document = {
        "dataset_id": dataset_id,
        "data": df.to_dict(orient="records"),
        "created_at": datetime.utcnow()
    }
    await raw_datasets_col.insert_one(document)


# --------------------------------------------------
# Load raw dataset
# --------------------------------------------------
async def load_raw_dataset(dataset_id: str):
    doc = await raw_datasets_col.find_one({"dataset_id": dataset_id})
    if not doc:
        return None
    return doc["data"]


# --------------------------------------------------
# Save cleaned dataset
# --------------------------------------------------
async def save_clean_dataset(dataset_id: str, df):
    document = {
        "dataset_id": dataset_id,
        "data": df.to_dict(orient="records"),
        "created_at": datetime.utcnow()
    }
    await clean_datasets_col.insert_one(document)


# --------------------------------------------------
# Load cleaned dataset
# --------------------------------------------------
async def load_clean_dataset(dataset_id: str):
    doc = await clean_datasets_col.find_one({"dataset_id": dataset_id})
    if not doc:
        return None
    return doc["data"]


# --------------------------------------------------
# Save profiling or cleaning metadata
# --------------------------------------------------
async def save_metadata(dataset_id: str, metadata: dict, metadata_type: str):
    document = {
        "dataset_id": dataset_id,
        "type": metadata_type,  # "profiling" or "cleaning"
        "metadata": metadata,
        "created_at": datetime.utcnow()
    }
    await metadata_col.insert_one(document)