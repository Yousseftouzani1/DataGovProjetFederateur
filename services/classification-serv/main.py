
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import classification

app = FastAPI(
    title="Data Classification Service (Fine-Grained)",
    description="Tâche 5: Ensemble Classification (RF + BERT + Rules) with 6 Sensitivity Levels.",
    version="1.0.0"
)

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

# Include Router
app.include_router(classification.router)

@app.get("/health")
async def health_check():
    return {"status": "UP", "service": "classification-service"}

@app.get("/")
def root():
    return {"message": "Classification Service Ready (Ensemble Model)"}
