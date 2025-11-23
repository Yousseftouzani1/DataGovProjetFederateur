from fastapi import APIRouter, Depends, HTTPException
from backend.database.mongodb import db
from backend.users.models import User, VALID_ROLES
from backend.auth.utils import hash_password
from backend.auth.routes import require_role

router = APIRouter(prefix="/users", tags=["Users"])

# Create a new user (ONLY Data Steward)
@router.post("/create")
async def create_user(user: User):

    if user.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    exists = await db["users"].find_one({"username": user.username})

    if exists:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password)

    await db["users"].insert_one({
        "username": user.username,
        "password": hashed_pw,
        "role": user.role
    })

    return {"message": "User created successfully"}
