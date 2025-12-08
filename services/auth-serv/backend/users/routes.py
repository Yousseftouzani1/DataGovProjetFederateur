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
        "role": user.role,
        "status": "pending"
    })

    return {"message": "User created successfully"}

def serialize_user(user):
    user["_id"] = str(user["_id"])
    return user


@router.get("/pending", dependencies=[Depends(require_role(["Admin"]))])
async def list_pending_users():
    users_cursor = db["users"].find({"status": "pending"})
    users = await users_cursor.to_list(None)

    # Convert ObjectId → string
    users = [serialize_user(u) for u in users]

    return users



@router.post("/approve/{username}", dependencies=[Depends(require_role(["Admin"]))])
async def approve_user(username: str):
    result = await db["users"].update_one(
        {"username": username},
        {"$set": {"status": "approved"}}
    )
    return {"message": "User approved"}



@router.post("/reject/{username}", dependencies=[Depends(require_role(["Admin"]))])
async def reject_user(username: str):
    result = await db["users"].update_one(
        {"username": username},
        {"$set": {"status": "rejected"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User rejected"}


@router.post("/create-admin")
async def create_admin_temp():
    hashed = hash_password("Admin123")
    await db["users"].insert_one({
        "username": "admin",
        "password": hashed,
        "role": "Admin",
        "status": "approved"
    })
    return {"msg": "Admin created"}
