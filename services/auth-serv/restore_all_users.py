"""
Script to restore ALL users in MongoDB
Run this to fix "User not found" errors after migration.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load .env from project root
# Try multiple paths for robustness
load_dotenv(dotenv_path=".env")
load_dotenv(dotenv_path="../../.env")

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def restore_users():
    # Connect to MongoDB (Atlas/Remote as per .env)
    MONGO_URL = os.getenv("MONGODB_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "datagov")
    
    print(f"🔌 Connecting to MongoDB at {MONGO_URL}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    users_col = db["users"]
    
    # List of users to restore
    users_to_create = [
        {"username": "admin", "password": "admin123", "role": "admin", "email": "admin@datagov.ma"},
        {"username": "labeler_user", "password": "Labeler123", "role": "labeler", "email": "labeler@datagov.ma"},
        {"username": "annotator_user", "password": "Annotator123", "role": "annotator", "email": "annotator@datagov.ma"},
        {"username": "steward_user", "password": "Steward123", "role": "steward", "email": "steward@datagov.ma"}
    ]
    
    print("\n📦 Restoring users...")
    
    for u in users_to_create:
        existing = await users_col.find_one({"username": u["username"]})
        
        user_doc = {
            "username": u["username"],
            "password": hash_password(u["password"]),
            "role": u["role"],
            "status": "active",
            "email": u["email"]
        }
        
        if existing:
            # Update password and ensuring active
            await users_col.update_one(
                {"username": u["username"]},
                {"$set": user_doc}
            )
            print(f"   ✅ Updated existing user: {u['username']}")
        else:
            # Insert new
            await users_col.insert_one(user_doc)
            print(f"   ✨ Created new user: {u['username']}")

    print("\n🎉 All 4 users restored successfully!")
    print("   You can now login with:")
    for u in users_to_create:
        print(f"   - {u['username']} / {u['password']} ({u['role']})")

    client.close()

if __name__ == "__main__":
    asyncio.run(restore_users())
