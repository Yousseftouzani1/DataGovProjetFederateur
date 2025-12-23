from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../.env"))

# Load from environment variables
# Uses MONGODB_URI from .env file
MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "datagov")

try:
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client[DATABASE_NAME]
    print(f"✅ MongoDB Atlas connected!")
    print(f"   📁 Database: {DATABASE_NAME}")
except Exception as e:
    print(f"⚠️ MongoDB connection error: {e}")
    db = None
