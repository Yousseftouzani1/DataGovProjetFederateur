from fastapi import APIRouter
from backend.database.mongodb import db
from backend.users.models import User
from backend.auth.utils import hash_password

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/create")
async def create_user(user: User):
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)

    await db["users"].insert_one(user_dict)
    return {"message": "User created"}
