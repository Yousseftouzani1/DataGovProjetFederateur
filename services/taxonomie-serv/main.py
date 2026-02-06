
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api.routes import router

load_dotenv()

app = FastAPI(
    title="Taxonomy Service",
    description="Moroccan PII/SPI Taxonomy - Tâche 2",
    version="2.1.0"
)

@app.middleware("http")
async def set_root_path(request: Request, call_next):
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    return response

# CORS Security - Restricted origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router)

# ====================================================================
# STARTUP EVENT (REMEDIATION STEP 3)
# ====================================================================
@app.on_event("startup")
async def startup_event():
    print("🚀 Taxonomy Service Starting... Initiating Atlas Sync...")
    try:
        from backend.services.atlas_service import sync_taxonomy_to_atlas
        # Run in background to not block startup
        import asyncio
        asyncio.create_task(sync_taxonomy_to_atlas())  # Fixed: removed undefined 'engine' parameter
    except Exception as e:
        print(f"⚠️ Startup Sync Failed: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🇲🇦 TAXONOMY SERVICE - Tâche 2 (Refactored)")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
