import motor.motor_asyncio
import asyncio

async def purge_tasks():
    uri = "mongodb+srv://projetFD:ensias2025@datagovdb.sjhsdum.mongodb.net/?retryWrites=true&w=majority&appName=DataGovDB"
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    db = client["DataGovDB"]
    
    result = await db.tasks.delete_many({})
    print(f"🧹 Purge Complete: Removed {result.deleted_count} stale tasks.")
    
    # Also clear any other demo data if needed
    # await db.quality_metadata.delete_many({})
    
if __name__ == "__main__":
    asyncio.run(purge_tasks())
