"""
MongoDB Configuration for DataGov Platform
Uses MongoDB Atlas cluster for production
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os

# MongoDB Atlas Connection String
# Set MONGODB_URI in your .env file or environment variables
MONGO_URL = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://USERNAME:PASSWORD@your-cluster.mongodb.net/?retryWrites=true&w=majority"
)

# Database name
DATABASE_NAME = os.getenv("DATABASE_NAME", "DataGovDB")

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGO_URL)
db = async_client[DATABASE_NAME]

# Sync client for scripts and loaders
sync_client = MongoClient(MONGO_URL)
sync_db = sync_client[DATABASE_NAME]

# Collection names
COLLECTIONS = {
    "taxonomies": "taxonomies",           # Main taxonomy collection
    "domains": "domains",                 # Domain metadata
    "entities": "entities",               # Individual entities
    "users": "users",                     # User accounts
    "data_stewards": "data_stewards",     # Data steward assignments
    "audit_logs": "audit_logs",           # Audit trail
    "classifications": "classifications"  # Classification results
}

def get_collection(name: str):
    """Get a collection by name (async)"""
    return db[COLLECTIONS.get(name, name)]

def get_sync_collection(name: str):
    """Get a collection by name (sync)"""
    return sync_db[COLLECTIONS.get(name, name)]

# Test connection function
async def test_connection():
    """Test MongoDB Atlas connection"""
    try:
        await async_client.admin.command('ping')
        collections = await db.list_collection_names()
        return {
            "status": "connected",
            "database": DATABASE_NAME,
            "collections": collections
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def test_sync_connection():
    """Test MongoDB Atlas connection (sync)"""
    try:
        sync_client.admin.command('ping')
        collections = sync_db.list_collection_names()
        return {
            "status": "connected",
            "database": DATABASE_NAME,
            "collections": list(collections)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = test_sync_connection()
    print(f"MongoDB Connection Test: {result}")
