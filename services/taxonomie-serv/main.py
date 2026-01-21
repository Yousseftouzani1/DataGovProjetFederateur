
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🇲🇦 TAXONOMY SERVICE - Tâche 2 (Refactored)")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
