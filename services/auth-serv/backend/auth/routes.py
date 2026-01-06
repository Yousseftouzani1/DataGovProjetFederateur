from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm

from backend.database.mongodb import db
from backend.auth.utils import verify_password, create_token, decode_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


# LOGIN ROUTE -----------------------------------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"🔐 Login attempt: username='{form_data.username}'")
    
    try:
        user = await db["users"].find_one({"username": form_data.username})
        print(f"   User found: {user is not None}")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        raise HTTPException(status_code=503, detail="Database connection error. Please try again.")

    if not user:
        print(f"   ❌ User '{form_data.username}' not found in database")
        raise HTTPException(status_code=401, detail="User not found")

    print(f"   Checking password...")
    if not verify_password(form_data.password, user["password"]):
        print(f"   ❌ Password incorrect")
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # block pending users
    if user.get("status") == "pending":
        print(f"   ❌ User pending approval")
        raise HTTPException(status_code=403, detail="Account awaiting admin approval")

    # block rejected users
    if user.get("status") == "rejected":
        print(f"   ❌ User rejected")
        raise HTTPException(status_code=403, detail="Account rejected by admin")
    
    token = create_token({
        "sub": user["username"],
        "role": user["role"]
    })

    print(f"   ✅ Login successful! Role: {user['role']}")
    return {
        "access_token": token, 
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"]
    }



# EXTRACT TOKEN SAFELY --------------------------------
async def get_token(authorization: str = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    return token



# ROLE REQUIREMENT ------------------------------------
def require_role(allowed_roles: list):
    async def role_checker(token: str = Depends(get_token)):
        payload = decode_token(token)

        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        role = payload.get("role", "").lower()  # Convert to lowercase for comparison

        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")

        return payload

    return role_checker


# GET ALL USERS (Admin only) -----------------------------
@router.get("/users")
async def get_all_users(payload: dict = Depends(require_role(["admin"]))):
    """Get all users - Admin only"""
    try:
        users = await db["users"].find({}, {"password": 0}).to_list(length=100)
        # Convert ObjectId to string
        for user in users:
            user["_id"] = str(user["_id"])
        
        # Count by role (case-insensitive)
        stats = {
            "total": len(users),
            "admin": sum(1 for u in users if u.get("role", "").lower() == "admin"),
            "steward": sum(1 for u in users if u.get("role", "").lower() == "steward"),
            "annotator": sum(1 for u in users if u.get("role", "").lower() == "annotator"),
            "labeler": sum(1 for u in users if u.get("role", "").lower() == "labeler"),
            "pending": sum(1 for u in users if u.get("status") == "pending")
        }
        
        return {"users": users, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# UPDATE USER ROLE (Admin only) --------------------------
@router.put("/users/{username}/role")
async def update_user_role(username: str, new_role: str, payload: dict = Depends(require_role(["admin"]))):
    """Update user role - Admin only"""
    valid_roles = ["admin", "steward", "annotator", "labeler"]
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    result = await db["users"].update_one(
        {"username": username},
        {"$set": {"role": new_role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {username} role updated to {new_role}"}


# UPDATE USER STATUS (Admin only) ------------------------
@router.put("/users/{username}/status")
async def update_user_status(username: str, status: str, payload: dict = Depends(require_role(["admin"]))):
    """Approve or reject user - Admin only"""
    valid_statuses = ["active", "pending", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = await db["users"].update_one(
        {"username": username},
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {username} status updated to {status}"}
