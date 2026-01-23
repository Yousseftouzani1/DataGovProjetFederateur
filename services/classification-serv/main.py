
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import classification

app = FastAPI(
    title="Data Classification Service (Fine-Grained)",
    description="Tâche 5: Ensemble Classification (RF + BERT + Rules) with 6 Sensitivity Levels.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(classification.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "UP", "service": "classification-service"}

@app.get("/")
def root():
    return {"message": "Classification Service Ready (Ensemble Model)"}
