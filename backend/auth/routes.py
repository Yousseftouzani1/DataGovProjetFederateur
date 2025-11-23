from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm

from backend.database.mongodb import db
from backend.auth.utils import verify_password, create_token, decode_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


# LOGIN ROUTE -----------------------------------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db["users"].find_one({"username": form_data.username})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_token({
        "sub": user["username"],
        "role": user["role"]
    })

    return {"access_token": token, "token_type": "bearer"}



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

        role = payload.get("role")

        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")

        return payload

    return role_checker
