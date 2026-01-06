"""
Quick script to create an Admin user in MongoDB
Run this once to create an admin account
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path="../../.env")

# Use same hash as auth-serv (sha256_crypt, NOT bcrypt)
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using sha256_crypt (same as auth-serv)"""
    return pwd_context.hash(password)

async def create_admin():
    # Connect to MongoDB - use same variables as auth-serv
    MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "datagov")
    
    print(f"Connecting to MongoDB...")
    print(f"   Database: {DATABASE_NAME}")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    
    # Check if admin exists
    existing = await db["users"].find_one({"username": "admin"})
    if existing:
        print("⚠️ Admin user already exists! Updating password...")
        await db["users"].update_one(
            {"username": "admin"},
            {"$set": {"password": hash_password("admin123"), "status": "active"}}
        )
        print("✅ Admin password updated to: admin123")
    else:
        # Create admin user
        admin_user = {
            "username": "admin",
            "password": hash_password("admin123"),
            "role": "Admin",
            "status": "active",
            "email": "admin@datagov.ma"
        }
        
        result = await db["users"].insert_one(admin_user)
        print(f"✅ Admin user created!")
    
    print(f"\n   Username: admin")
    print(f"   Password: admin123")
    print(f"   Role: Admin")
    
    # Also approve josef if exists
    result = await db["users"].update_one(
        {"username": "josef"},
        {"$set": {"status": "active"}}
    )
    if result.modified_count > 0:
        print(f"\n✅ 'josef' user approved!")
    
    # List all users
    print(f"\n📋 All users in database:")
    async for user in db["users"].find():
        print(f"   - {user['username']} ({user['role']}) - {user['status']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
