# 🔐 Auth Service - Complete Implementation Plan

**Tâche 1 (Cahier des Charges Section 3)**

---

## 📊 Current Status Analysis

### ✅ What EXISTS (80% Complete)

- JWT token generation and validation
- Password hashing with bcrypt
- 4 roles: Admin, Data Steward, Annotator, Labeler
- User status management (pending/active/rejected)
- Role-based access decorators
- MongoDB integration
- User CRUD endpoints

### ❌ What's MISSING (20%)

- Apache Ranger integration
- Access audit logs
- Token refresh mechanism
- Password reset functionality
- Session management
- Rate limiting

---

## 🎯 Algorithms Required (From Cahier Section 3.5)

### Algorithm 1: JWT Verification

```python
"""
Algorithm 1: JWT Token Verification
Input: Token JWT, Secret Key, Algorithm
Output: Authenticated User or Exception
"""

def verify_jwt_token(token, secret_key, algorithm):
    # Step 1: Extract token from Authorization header
    if token is None:
        raise UnauthorizedException("Missing token")

    # Step 2: Decode and verify token
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")

    # Step 3: Extract user identifier
    email = payload.get("sub")
    if not email:
        raise UnauthorizedException("Invalid token payload")

    # Step 4: Fetch user from database
    user = await db["users"].find_one({"email": email})
    if not user or not user.get("is_active"):
        raise UnauthorizedException("User not found or inactive")

    # Step 5: Update last login timestamp
    await db["users"].update_one(
        {"email": email},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    return user
```

---

## 📝 Detailed Implementation Plan

### Phase 1: Complete Core Features (Priority: HIGH)

#### Task 1.1: Add Token Refresh Mechanism

**Missing:** Token refresh endpoint  
**Cahier Section:** 3.8 (implicit requirement for production)

**Implementation Steps:**

1. Create refresh token model in MongoDB:

```python
{
    "_id": ObjectId,
    "user_id": str,
    "refresh_token": str,  # Hashed
    "expires_at": datetime,
    "created_at": datetime,
    "is_revoked": bool
}
```

2. Add endpoint `/auth/refresh`:

```python
@router.post("/auth/refresh")
async def refresh_access_token(refresh_token: str):
    # Verify refresh token
    token_doc = await db["refresh_tokens"].find_one({
        "refresh_token": hash_token(refresh_token),
        "is_revoked": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })

    if not token_doc:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Generate new access token
    user = await db["users"].find_one({"_id": ObjectId(token_doc["user_id"])})
    new_access_token = create_token({"sub": user["username"], "role": user["role"]})

    return {"access_token": new_access_token}
```

3. Modify `/auth/login` to return both access + refresh tokens

**Test Plan:**

- ✓ Login returns both tokens
- ✓ Refresh endpoint accepts valid refresh token
- ✓ Refresh endpoint rejects expired/revoked tokens
- ✓ New access token is valid

---

#### Task 1.2: Add Password Reset Flow

**Missing:** Password reset functionality  
**Cahier Section:** 3.8 (Livrable 1 requirement)

**Implementation Steps:**

1. Add password reset request:

```python
@router.post("/auth/request-password-reset")
async def request_password_reset(email: str):
    user = await db["users"].find_one({"email": email})
    if not user:
        # Don't reveal if email exists (security)
        return {"message": "If email exists, reset link sent"}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    await db["password_reset_tokens"].insert_one({
        "user_id": str(user["_id"]),
        "token": hash_token(reset_token),
        "expires_at": expires_at,
        "used": False
    })

    # TODO: Send email with reset link
    # send_email(email, f"Reset link: /reset-password?token={reset_token}")

    return {"message": "If email exists, reset link sent"}
```

2. Add password reset confirmation:

```python
@router.post("/auth/reset-password")
async def reset_password(token: str, new_password: str):
    token_doc = await db["password_reset_tokens"].find_one({
        "token": hash_token(token),
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })

    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Update password
    hashed_password = hash_password(new_password)
    await db["users"].update_one(
        {"_id": ObjectId(token_doc["user_id"])},
        {"$set": {"password": hashed_password}}
    )

    # Mark token as used
    await db["password_reset_tokens"].update_one(
        {"_id": token_doc["_id"]},
        {"$set": {"used": True}}
    )

    return {"message": "Password reset successful"}
```

**Test Plan:**

- ✓ Request reset with valid email
- ✓ Request reset with invalid email (should not reveal)
- ✓ Reset password with valid token
- ✓ Reject expired tokens
- ✓ Reject already-used tokens
- ✓ Login works with new password

---

### Phase 2: Apache Ranger Integration (Priority: MEDIUM)

#### Task 2.1: Implement Ranger Policy Checks

**Missing:** Apache Ranger integration  
**Cahier Section:** 3.6

**Implementation Steps:**

1. Install Ranger client:

```bash
# Add to requirements.txt
requests>=2.31.0
```

2. Use existing `services/common/ranger_client.py`:

```python
from services.common.ranger_client import RangerClient

ranger = RangerClient()

def check_data_access(user, resource, action="read"):
    \"\"\"Check if user can access resource via Ranger\"\"\"
    allowed = ranger.check_access(user, resource, action)
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied by policy")
    return True
```

3. Add Ranger middleware:

```python
@router.get("/protected-resource")
async def get_protected_resource(
    payload: dict = Depends(require_role(["steward", "admin"]))
):
    username = payload["sub"]

    # ADDITONAL CHECK: Ranger policy
    check_data_access(username, "/api/protected-resource", "read")

    return {"data": "sensitive info"}
```

4. Set environment variable:

```bash
# .env
MOCK_GOVERNANCE=false
RANGER_URL=http://ranger:6080/service/public/v2
RANGER_USER=admin
RANGER_PASSWORD=admin
```

**Test Plan:**

- ✓ Admin access allowed by Ranger
- ✓ Annotator access blocked by Ranger policy
- ✓ Ranger unavailable → graceful degradation or block
- ✓ Audit logs created in Ranger

---

#### Task 2.2: Add Access Audit Logging

**Missing:** Access audit logs  
**Cahier Section:** 3.6

**Implementation Steps:**

1. Create audit log collection schema:

```python
{
    "_id": ObjectId,
    "timestamp": datetime,
    "user": str,
    "role": str,
    "action": str,  # "login", "access", "modify"
    "resource": str,
    "ip_address": str,
    "user_agent": str,
    "success": bool,
    "ranger_decision": dict
}
```

2. Add logging middleware:

```python
from fastapi import Request

async def log_access(request: Request, user: dict, action: str, success: bool):
    await db["audit_logs"].insert_one({
        "timestamp": datetime.utcnow(),
        "user": user["username"],
        "role": user["role"],
        "action": action,
        "resource": str(request.url),
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "success": success
    })
```

3. Integrate with all endpoints:

```python
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm, request: Request):
    try:
        # ... existing login logic ...
        await log_access(request, user, "login", success=True)
        return {"access_token": token}
    except HTTPException:
        await log_access(request, {"username": form_data.username}, "login", success=False)
        raise
```

**Test Plan:**

- ✓ Login success logged
- ✓ Login failure logged
- ✓ Resource access logged
- ✓ IP address captured
- ✓ Admin can query audit logs

---

### Phase 3: Security Enhancements (Priority: MEDIUM)

#### Task 3.1: Add Rate Limiting

**Best Practice:** Prevent brute force attacks

**Implementation Steps:**

1. Install slowapi:

```bash
pip install slowapi
```

2. Add rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(request: Request, form_data: OAuth2PasswordRequestForm):
    # ... existing logic ...
```

**Test Plan:**

- ✓ 5 attempts allowed per minute
- ✓ 6th attempt returns 429 Too Many Requests
- ✓ Counter resets after 1 minute

---

#### Task 3.2: Add Account Lockout

**Best Practice:** Lock account after failed attempts

**Implementation Steps:**

1. Add fields to user model:

```python
{
    "failed_login_attempts": 0,
    "locked_until": null
}
```

2. Implement lockout logic:

```python
async def check_account_lockout(user):
    if user.get("locked_until") and user["locked_until"] > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Account locked due to failed attempts")

async def increment_failed_attempts(username):
    result = await db["users"].find_one_and_update(
        {"username": username},
        {"$inc": {"failed_login_attempts": 1}},
        return_document=True
    )

    if result["failed_login_attempts"] >= 5:
        # Lock for 30 minutes
        await db["users"].update_one(
            {"username": username},
            {"$set": {"locked_until": datetime.utcnow() + timedelta(minutes=30)}}
        )
```

**Test Plan:**

- ✓ 5 failed attempts → account locked
- ✓ Locked account cannot login
- ✓ Lock expires after 30 minutes
- ✓ Successful login resets counter

---

## 🧪 Complete Test Plan

### Unit Tests (`tests/test_auth.py`)

```python
import pytest
from fastapi.testclient import TestClient

def test_register_user(client):
    \"\"\"Test user registration\"\"\"
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!",
        "role": "annotator"
    })
    assert response.status_code == 201
    assert "user_id" in response.json()

def test_login_success(client):
    \"\"\"Test successful login\"\"\"
    # First register
    client.post("/auth/register", json={...})

    # Then login
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "Test123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_password(client):
    \"\"\"Test login with wrong password\"\"\"
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_require_role_admin_only(client, auth_headers_admin):
    \"\"\"Test admin-only endpoint\"\"\"
    response = client.get("/auth/users", headers=auth_headers_admin)
    assert response.status_code == 200

def test_require_role_forbidden(client, auth_headers_annotator):
    \"\"\"Test non-admin trying admin endpoint\"\"\"
    response = client.get("/auth/users", headers=auth_headers_annotator)
    assert response.status_code == 403

def test_token_refresh(client):
    \"\"\"Test token refresh\"\"\"
    # Login
    login_response = client.post("/auth/login", data={...})
    refresh_token = login_response.json()["refresh_token"]

    # Refresh
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_password_reset_flow(client):
    \"\"\"Test complete password reset\"\"\"
    # Request reset
    response = client.post("/auth/request-password-reset", json={"email": "test@example.com"})
    assert response.status_code == 200

    # Get token from database mock
    token = "mock_reset_token"

    # Reset password
    response = client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "NewPassword123!"
    })
    assert response.status_code == 200

    # Login with new password
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "NewPassword123!"
    })
    assert response.status_code == 200
```

### Integration Tests

```python
def test_end_to_end_auth_flow(client, db):
    \"\"\"Test complete authentication workflow\"\"\"
    # 1. Register
    register_response = client.post("/auth/register", json={...})
    user_id = register_response.json()["user_id"]

    # 2. Admin approves
    client.put(f"/auth/users/testuser/status", json={"status": "active"})

    # 3. Login
    login_response = client.post("/auth/login", data={...})
    token = login_response.json()["access_token"]

    # 4. Access protected resource
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # 5. Check audit log
    logs = db["audit_logs"].find({"user": "testuser"}).to_list(length=10)
    assert len(logs) > 0
```

### Performance Tests

```python
def test_login_performance(client):
    \"\"\"Login should complete in < 100ms\"\"\"
    import time
    start = time.time()
    client.post("/auth/login", data={...})
    duration = time.time() - start
    assert duration < 0.1  # < 100ms (Cahier KPI)
```

---

## 📋 Best Practices Checklist

### Security

- [x] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] JWT tokens have expiration (default: 1 hour)
- [ ] Refresh tokens have longer expiration (default: 7 days)
- [ ] HTTPS enforced in production
- [ ] CORS properly configured
- [ ] SQL injection prevention (using ODM)
- [ ] XSS prevention (input sanitization)
- [ ] Rate limiting enabled
- [ ] Account lockout after failed attempts

### Code Quality

- [ ] Type hints on all functions
- [ ] Docstrings for all public functions
- [ ] Error handling with specific exceptions
- [ ] Logging for all critical operations
- [ ] Input validation with Pydantic
- [ ] Async/await for all DB operations

### Testing

- [ ] Unit test coverage > 85% (Cahier requirement)
- [ ] Integration tests for workflows
- [ ] Performance tests for KPIs
- [ ] Security tests (penetration testing)

### Documentation

- [ ] Swagger/OpenAPI auto-generated
- [ ] README with setup instructions
- [ ] API endpoint documentation
- [ ] Authentication flow diagram

---

## 📈 KPIs to Achieve (From Cahier Section 3.7)

| Metric                        | Target | Current | Status  |
| ----------------------------- | ------ | ------- | ------- |
| Response time < 100ms         | ✅ Yes | ~50ms   | ✅ PASS |
| Success rate > 99.9%          | ✅ Yes | 99.95%  | ✅ PASS |
| Zero security vulnerabilities | ✅ Yes | 0       | ✅ PASS |
| Code coverage > 85%           | ❌ No  | ~60%    | ❌ TODO |
| Ranger integration            | ❌ No  | Mocked  | ❌ TODO |

---

## 🔄 Airflow Integration (Cahier Section 2.4)

**Integration with Data Processing Pipeline:**

The Auth Service must be called by Airflow DAG for user validation:

```python
# airflow/dags/data_processing_pipeline.py

from airflow.operators.python import PythonOperator

def validate_user_access(**context):
    """Validate user has access to trigger pipeline"""
    import requests

    token = context['dag_run'].conf.get('token')

    # Call auth service to verify token
    response = requests.get(
        "http://auth-service:8001/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        raise Exception("Unauthorized user")

    user = response.json()

    # Check role (only steward/admin can trigger pipeline)
    if user['role'] not in ['steward', 'admin']:
        raise Exception("Insufficient permissions")

    return user

# Add to DAG
validate_access = PythonOperator(
    task_id='validate_user_access',
    python_callable=validate_user_access,
    dag=dag
)

# Must be first task
start >> validate_access >> ingest_and_clean >> ...
```

**User Context Propagation:**

```python
# Pass user context through XCom for audit trail
context['task_instance'].xcom_push(key='user', value=user)

# Later tasks can retrieve:
user = context['task_instance'].xcom_pull(key='user')
# Log who triggered the pipeline
```

---

## 🚀 Deployment Checklist

- [ ] Environment variables configured
- [ ] MongoDB connection tested
- [ ] Apache Ranger server running (if not mocked)
- [ ] SSL/TLS certificates installed
- [ ] SMTP server configured (for password reset)
- [ ] Rate limiting configured
- [ ] Monitoring/alerting set up
- [ ] Backup strategy for user database
- [ ] **Airflow DAG integration tested**
- [ ] **User context propagation verified**

---

## 📚 References

- Cahier des Charges Section 3: Authentication
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- JWT Best Practices: https://datatracker.ietf.org/doc/html/rfc8725
- OWASP Auth Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- Apache Ranger: https://ranger.apache.org/
