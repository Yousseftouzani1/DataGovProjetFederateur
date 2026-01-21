import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_users():
    uri = "mongodb+srv://projetFD:ensias2025@datagovdb.sjhsdum.mongodb.net/?retryWrites=true&w=majority&appName=DataGovDB"
    db_name = "DataGovDB"
    
    print(f"Connecting to Atlas...")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    try:
        users = await db["users"].find({}, {"username": 1}).to_list(length=20)
        print("Usernames found in Atlas:")
        for u in users:
            print(f"- {u.get('username')}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_users())
