"""
Script to restore ALL users in MongoDB
Run: python restore_all_users.py
Passwords are read from environment variables for security.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
load_dotenv(dotenv_path="../../.env")

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def restore_users():
    MONGO_URL = os.getenv("MONGODB_URI")
    if not MONGO_URL:
        print("ERROR: MONGODB_URI not found in .env file.")
        sys.exit(1)
    DATABASE_NAME = os.getenv("DATABASE_NAME", "DataGovDB")

    # Read passwords from environment or prompt
    admin_pw = os.getenv("ADMIN_PASSWORD")
    if not admin_pw:
        print("ERROR: Set ADMIN_PASSWORD environment variable before running.")
        print("Example: ADMIN_PASSWORD=MySecurePass123 python restore_all_users.py")
        sys.exit(1)

    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    users_col = db["users"]

    users_to_create = [
        {"username": "admin", "password": admin_pw, "role": "admin", "email": "admin@datagov.ma"},
        {"username": "labeler_user", "password": os.getenv("LABELER_PASSWORD", admin_pw), "role": "labeler", "email": "labeler@datagov.ma"},
        {"username": "annotator_user", "password": os.getenv("ANNOTATOR_PASSWORD", admin_pw), "role": "annotator", "email": "annotator@datagov.ma"},
        {"username": "steward_user", "password": os.getenv("STEWARD_PASSWORD", admin_pw), "role": "steward", "email": "steward@datagov.ma"}
    ]

    print("\nRestoring users...")

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
            await users_col.update_one(
                {"username": u["username"]},
                {"$set": user_doc}
            )
            print(f"   Updated existing user: {u['username']}")
        else:
            await users_col.insert_one(user_doc)
            print(f"   Created new user: {u['username']}")

    print("\nAll 4 users restored successfully!")
    print("   Usernames: admin, labeler_user, annotator_user, steward_user")

    client.close()

if __name__ == "__main__":
    asyncio.run(restore_users())
