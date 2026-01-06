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
    
    # Use status from request (admin can set 'active') or default to 'pending'
    status = user.status if hasattr(user, 'status') and user.status else "pending"

    await db["users"].insert_one({
        "username": user.username,
        "email": user.email if hasattr(user, 'email') else "",
        "password": hashed_pw,
        "role": user.role.lower(),
        "status": status
    })

    msg = "User created and activated!" if status == "active" else "User created. Awaiting admin approval."
    return {"message": msg}

def serialize_user(user):
    user["_id"] = str(user["_id"])
    return user


@router.get("/pending", dependencies=[Depends(require_role(["admin"]))])
async def list_pending_users():
    users_cursor = db["users"].find({"status": "pending"})
    users = await users_cursor.to_list(None)

    # Convert ObjectId → string
    users = [serialize_user(u) for u in users]

    return users



@router.post("/approve/{username}", dependencies=[Depends(require_role(["admin"]))])
async def approve_user(username: str):
    result = await db["users"].update_one(
        {"username": username},
        {"$set": {"status": "active"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User approved and activated"}



@router.post("/reject/{username}", dependencies=[Depends(require_role(["admin"]))])
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
        "role": "admin",
        "status": "active"
    })
    return {"msg": "Admin created"}
