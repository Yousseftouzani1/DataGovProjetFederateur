from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "datagov")

try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    print("✅ Correction Service connected to MongoDB")
except Exception as e:
    print(f"⚠️ Mongo error: {e}")
    db = None
