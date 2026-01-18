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
audit_logs_col = db["audit_logs"]


# --------------------------------------------------
# Save raw dataset
# --------------------------------------------------
async def save_raw_dataset(dataset_id: str, df, filename: str = None):
    document = {
        "dataset_id": dataset_id,
        "filename": filename or "unknown_file",
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

# --------------------------------------------------
# Audit Logs (Persistent)
# --------------------------------------------------
async def log_audit_event(service: str, action: str, user: str, status: str, details: dict = None):
    """
    Log an event to the persistent audit trail.
    """
    document = {
        "service": service,
        "action": action,
        "user": user,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    await audit_logs_col.insert_one(document)

async def get_recent_audit_logs(limit: int = 50):
    """
    Retrieve recent audit logs from MongoDB.
    """
    cursor = audit_logs_col.find({}, {'_id': 0}).sort("timestamp", -1).limit(limit)
    logs = []
    async for doc in cursor:
        # doc["id"] = str(doc["_id"]) # _id removed by projection for cleaner JSON
        # Generate a synthetic ID if needed or just use index
        logs.append(doc)
    return logs