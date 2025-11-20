from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.database.mongodb import db
from backend.auth.utils import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db["users"].find_one({"username": form_data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")

    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_access_token({
        "sub": user["username"],
        "role": user["role"]
    })

    return {"access_token": token, "token_type": "bearer"}
