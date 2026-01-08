from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

# Environment variables
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "datagov")

try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    print("✅ Correction Service connected to MongoDB")
except Exception as e:
    print(f"⚠️ Mongo error: {e}")
    db = None
