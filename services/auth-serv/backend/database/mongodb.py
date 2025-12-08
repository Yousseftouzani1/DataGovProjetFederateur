from motor.motor_asyncio import AsyncIOMotorClient
import os

# Load from environment variables (set by Docker)
MONGO_URL = os.getenv("MONGO_URL", "44")
DATABASE_NAME = os.getenv("DATABASE_NAME", "datagov")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]
