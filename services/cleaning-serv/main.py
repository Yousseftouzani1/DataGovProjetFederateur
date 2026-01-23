
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import data_cleaning

app = FastAPI(
    title="Data Cleaning & Profiling Service",
    description="Tâche 4: Complete cleaning pipeline with IQR, ydata-profiling, and Airflow integration.",
    version="2.1.0"
)

# CORS Compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the refactored router (Tâche 4 Core)
app.include_router(data_cleaning.router, prefix="/api/v1")

@app.middleware("http")
async def set_root_path(request: Request, call_next):
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    return response

@app.get("/health")
async def health_check():
    return {"status": "UP", "service": "cleaning-service-v2"}

@app.get("/")
def root():
    return {"message": "Data Cleaning Service Ready"}