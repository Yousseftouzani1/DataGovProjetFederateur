import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_users():
    load_dotenv(dotenv_path=".env")
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DATABASE_NAME", "datagov")
    
    print(f"Connecting to: {uri[:20]}...")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    try:
        users = await db["users"].find({}, {"username": 1, "role": 1, "status": 1}).to_list(length=10)
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"- {u.get('username')} (Role: {u.get('role')}, Status: {u.get('status')})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_users())
