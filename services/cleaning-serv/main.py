from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import data_cleaning

app = FastAPI(
    title="Data Cleaning & Profiling Service",
    description="Tâche 4: Complete cleaning pipeline with IQR, ydata-profiling, and Airflow integration.",
    version="2.1.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ Validation Error: {exc.errors()}")
    print(f"❌ Body: {await request.body()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": str(await request.body())}),
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
app.include_router(data_cleaning.router)

@app.on_event("startup")
async def startup_db_client():
    try:
        from backend.storage import client
        # Check if we can reach the server
        await client.admin.command('ping')
        print("✅ MongoDB Connection Successful (Startup Check)")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed (Startup Check): {e}")

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