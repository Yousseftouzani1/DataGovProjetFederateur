from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm

from backend.database.mongodb import db
from backend.auth.utils import verify_password, create_token, decode_token

router = APIRouter(tags=["Authentication"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


# LOGIN ROUTE -----------------------------------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    from datetime import datetime
    
    print(f"🔐 Login attempt: username='{form_data.username}'")
    
    try:
        user = await db["users"].find_one({"username": form_data.username})
        print(f"   User found: {user is not None}")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        raise HTTPException(status_code=503, detail="Database connection error. Please try again.")

    if not user:
        print(f"   ❌ User '{form_data.username}' not found in database")
        # Log failed login attempt
        await db["audit_logs"].insert_one({
            "service": "AUTH",
            "action": "LOGIN_FAILED",
            "user": form_data.username,
            "status": "WARNING",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {"reason": "User not found"}
        })
        raise HTTPException(status_code=401, detail="User not found")

    print(f"   Checking password...")
    if not verify_password(form_data.password, user["password"]):
        print(f"   ❌ Password incorrect")
        # Log failed login attempt
        await db["audit_logs"].insert_one({
            "service": "AUTH",
            "action": "LOGIN_FAILED",
            "user": form_data.username,
            "status": "WARNING",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {"reason": "Incorrect password"}
        })
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

    # Algorithm 1: Update last_login timestamp
    await db["users"].update_one(
        {"username": user["username"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    # Log successful login
    await db["audit_logs"].insert_one({
        "service": "AUTH",
        "action": "LOGIN_SUCCESS",
        "user": user["username"],
        "status": "INFO",
        "timestamp": datetime.utcnow().isoformat(),
        "details": {"role": user["role"]}
    })

    print(f"   ✅ Login successful! Role: {user['role']}")
    return {
        "access_token": token, 
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"]
    }



from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_token_payload(auth: HTTPAuthorizationCredentials = Depends(security)):
    """
    Standard token extractor and validator.
    Works with Swagger's global 'Authorize' button.
    """
    token = auth.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# ROLE REQUIREMENT ------------------------------------
def require_role(allowed_roles: list):
    async def role_checker(payload: dict = Depends(get_token_payload)):
        role = payload.get("role", "").lower()
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


# ====================================================================
# US-AUTH-05: APACHE RANGER INTEGRATION
# ====================================================================
import requests as ranger_requests

RANGER_URL = "http://100.91.176.196:6080"
RANGER_AUTH = ("admin", "hortonworks1")

@router.get("/ranger/check-access")
async def check_ranger_access(
    resource: str,
    action: str = "read",
    payload: dict = Depends(require_role(["admin", "steward"]))
):
    """
    US-AUTH-05: Check Ranger policy for user access to sensitive data.
    Per Cahier des Charges Section 3.6: FastAPI → Ranger REST API
    """
    username = payload.get("sub")
    role = payload.get("role")
    
    try:
        # Query Ranger for policy check
        policy_check = {
            "resource": {"path": resource},
            "accessType": action,
            "user": username,
            "context": {"role": role}
        }
        
        response = ranger_requests.post(
            f"{RANGER_URL}/service/plugins/policies/evaluate",
            json=policy_check,
            auth=RANGER_AUTH,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "allowed": result.get("allowed", False),
                "resource": resource,
                "action": action,
                "user": username,
                "role": role,
                "policy_id": result.get("policyId")
            }
        else:
            return {
                "allowed": False,
                "error": f"Ranger returned {response.status_code}",
                "fallback": "Using role-based default"
            }
            
    except Exception as e:
        # Fallback: Use role-based logic if Ranger unavailable
        role_permissions = {
            "admin": True,
            "steward": True,
            "annotator": action == "read",
            "labeler": False
        }
        return {
            "allowed": role_permissions.get(role, False),
            "resource": resource,
            "fallback": True,
            "reason": f"Ranger unavailable: {str(e)}"
        }


# ====================================================================
# US-AUTH-06: ATLAS AUDIT LOGS FOR DATA STEWARDS
# ====================================================================

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    service: str = None,
    payload: dict = Depends(require_role(["admin", "steward"]))
):
    """
    US-AUTH-06: Data Steward consults audit logs.
    Returns audit entries from MongoDB (synced with Atlas).
    """
    query = {}
    if service:
        query["service"] = service.upper()
    
    logs = await db["audit_logs"].find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    # Serialize ObjectIds
    for log in logs:
        log["_id"] = str(log["_id"])
    
    return {
        "total": len(logs),
        "logs": logs,
        "queried_by": payload.get("sub"),
        "role": payload.get("role")
    }


@router.get("/audit-logs/stats")
async def get_audit_stats(payload: dict = Depends(require_role(["admin", "steward"]))):
    """
    US-AUTH-06: Aggregate audit statistics for dashboard.
    """
    from datetime import datetime, timedelta
    
    # Last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": cutoff.isoformat()}}},
        {"$group": {
            "_id": {"service": "$service", "action": "$action"},
            "count": {"$sum": 1}
        }}
    ]
    
    try:
        results = await db["audit_logs"].aggregate(pipeline).to_list(length=100)
        
        stats = {}
        for r in results:
            service = r["_id"]["service"]
            action = r["_id"]["action"]
            if service not in stats:
                stats[service] = {}
            stats[service][action] = r["count"]
        
        return {
            "period": "last_24h",
            "stats_by_service": stats,
            "total_events": sum(r["count"] for r in results)
        }
    except Exception as e:
        return {"error": str(e)}

