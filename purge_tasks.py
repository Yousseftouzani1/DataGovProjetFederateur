
import asyncio
import motor.motor_asyncio
import os

async def purge_atlas():
    # URI from .env
    uri = "mongodb+srv://projetFD:ensias2025@datagovdb.sjhsdum.mongodb.net/?retryWrites=true&w=majority&appName=DataGovDB"
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    db = client["DataGovDB"]
    
    print(f"🧹 Purging 'tasks' collection in DataGovDB (Atlas)...")
    result = await db.tasks.delete_many({})
    print(f"✅ Successfully deleted {result.deleted_count} tasks.")

if __name__ == "__main__":
    asyncio.run(purge_atlas())
