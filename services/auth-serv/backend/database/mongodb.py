from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../.env"))

# Load from environment variables
# Uses MONGODB_URI from .env file
MONGO_URL = os.getenv("MONGODB_URI")
if not MONGO_URL:
    raise RuntimeError("MONGODB_URI environment variable is required. Set it in .env file.")
DATABASE_NAME = os.getenv("DATABASE_NAME", "DataGovDB")

try:
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client[DATABASE_NAME]
    print(f"✅ MongoDB Atlas connected!")
    print(f"   📁 Database: {DATABASE_NAME}")
except Exception as e:
    print(f"⚠️ MongoDB connection error: {e}")
    db = None
