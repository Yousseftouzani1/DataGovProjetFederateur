"""
Quick script to create an Admin user in MongoDB
Run: python create_admin.py <password>
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path="../../.env")

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_admin():
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <admin_password>")
        print("ERROR: Password must be provided as argument. Never hardcode passwords.")
        sys.exit(1)

    admin_password = sys.argv[1]
    if len(admin_password) < 8:
        print("ERROR: Password must be at least 8 characters.")
        sys.exit(1)

    MONGO_URL = os.getenv("MONGODB_URI")
    if not MONGO_URL:
        print("ERROR: MONGODB_URI not found in .env file.")
        sys.exit(1)
    DATABASE_NAME = os.getenv("DATABASE_NAME", "DataGovDB")

    print(f"Connecting to MongoDB...")
    print(f"   Database: {DATABASE_NAME}")

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]

    existing = await db["users"].find_one({"username": "admin"})
    if existing:
        print("Admin user already exists! Updating password...")
        await db["users"].update_one(
            {"username": "admin"},
            {"$set": {"password": hash_password(admin_password), "status": "active"}}
        )
        print("Admin password updated.")
    else:
        admin_user = {
            "username": "admin",
            "password": hash_password(admin_password),
            "role": "admin",
            "status": "active",
            "email": "admin@datagov.ma"
        }
        await db["users"].insert_one(admin_user)
        print("Admin user created!")

    print(f"\n   Username: admin")
    print(f"   Role: Admin")

    print(f"\nAll users in database:")
    async for user in db["users"].find():
        print(f"   - {user['username']} ({user['role']}) - {user['status']}")

    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
