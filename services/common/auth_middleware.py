"""
Shared JWT Auth Middleware for DataGov Microservices
====================================================
Verifies JWT tokens issued by auth-serv without needing
to call auth-serv. Uses the same SECRET_KEY and algorithm.

Usage in any FastAPI service:
    from common.auth_middleware import require_role, get_current_user

    @router.get("/protected")
    async def protected_endpoint(user=Depends(get_current_user)):
        ...

    @router.get("/admin-only")
    async def admin_only(user=Depends(require_role(["admin"]))):
        ...
"""

import os
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extract and validate JWT token from Authorization header.
    Returns the token payload dict with 'sub' (username) and 'role'.
    """
    if not auth:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="Auth not configured (SECRET_KEY missing)")

    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(allowed_roles: list):
    """
    Dependency factory: requires the user to have one of the allowed roles.

    Usage:
        @router.get("/admin-stuff")
        async def admin_stuff(user=Depends(require_role(["admin", "steward"]))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        role = user.get("role", "").lower()
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied: insufficient role")
        return user

    return role_checker
