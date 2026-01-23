from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.routes import router as auth_router
from backend.users.routes import router as user_router
from backend.airflow_routes import router as airflow_router

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


@app.middleware("http")
async def set_root_path(request: Request, call_next):
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    return response

# CORS for frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        return {"status": "error", "detail": str(e)}

# Routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(airflow_router)
