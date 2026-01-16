import motor.motor_asyncio
import asyncio
import os

async def check_tasks():
    uri = "mongodb+srv://projetFD:ensias2025@datagovdb.sjhsdum.mongodb.net/?retryWrites=true&w=majority&appName=DataGovDB"
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    db = client["DataGovDB"]
    
    print("--- Tasks Summary ---")
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    async for doc in db.tasks.aggregate(pipeline):
        print(f"Status: {doc['_id']}, Total: {doc['count']}")
    
    print("\n--- Recent Tasks ---")
    async for task in db.tasks.find().sort("created_at", -1).limit(5):
        print(f"ID: {task.get('id')}, Dataset: {task.get('dataset_id')}, Status: {task.get('status')}")

if __name__ == "__main__":
    asyncio.run(check_tasks())
