import asyncio
from backend.database.mongodb import db
from backend.auth.utils import hash_password

async def create_steward():
    await db["users"].insert_one({
        "username": "steward1",
        "password": hash_password("Password123"),
        "role": "Data Steward"
    })

asyncio.run(create_steward())
