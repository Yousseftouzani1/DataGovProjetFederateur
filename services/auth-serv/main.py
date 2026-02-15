from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.auth.routes import router as auth_router
from backend.users.routes import router as user_router
from backend.airflow_routes import router as airflow_router

# Rate limiter - keyed by client IP
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Auth Service",
    description="Tâche 1 - Module d'Authentification et Gestion des Rôles",
    version="2.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
    # Standard security definitions for Swagger
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    openapi_extra={
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
        "security": [{"BearerAuth": []}],
    },
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time as _time
    start = _time.perf_counter()
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    process_time = _time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response

# CORS Security - Restricted origins
import os
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.get("/")
def root():
    return {
        "service": "Auth Service",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

from backend.database.mongodb import db

@app.get("/test-db")
async def test_db():
    try:
        collections = await db.list_collection_names()
        return {"status": "connected", "collections": collections}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection error: {str(e)}")

# Routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(airflow_router)
