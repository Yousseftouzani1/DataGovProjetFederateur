"""
Classification Service - Tâche 5
Fine-Grained ML/NLP Classification for Sensitive Data

According to Cahier des Charges:
- ML-based classification using HuggingFace/BERT models
- Ensemble voting mechanism
- Integration with taxonomy service
- MongoDB Persistence for Validation Workflow
"""
import uvicorn
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os

from backend.database.mongodb import db

# ML imports (optional - will use simple classifier if not available)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.ensemble import VotingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from backend.models.ensemble_classifier import EnsembleSensitivityClassifier

# ====================================================================
# MODELS
# ====================================================================

class ClassifyRequest(BaseModel):
    text: str = Field(..., description="Text to classify", min_length=1)
    language: str = Field(default="en", description="Language: en, fr, ar")
    use_ml: bool = Field(default=True, description="Use ML classification")
    model: str = Field(default="ensemble", description="Model: ensemble, bert, simple")

class ClassifyResponse(BaseModel):
    success: bool
    text: str
    classification: str
    sensitivity_level: str
    confidence: float
    model_used: str
    explainability: Optional[Dict] = None
    categories: Dict[str, float]

class TrainRequest(BaseModel):
    data: List[Dict]  # [{"text": "...", "label": "..."}]
    model_type: str = Field(default="simple")

# Initialize advanced classifier
# Set explicit model path relative to app root
MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "models")
classifier = EnsembleSensitivityClassifier(model_dir=MODEL_PATH)

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Classification Service",
    description="Fine-Grained ML/NLP Classification (Mongo Persisted)",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    count = 0
    if db is not None:
        count = await db.pending_classifications.count_documents({})
    return {
        "service": "Classification Service",
        "status": "running",
        "db_connected": db is not None,
        "pending_count": count,
        "sklearn_available": SKLEARN_AVAILABLE,
        "transformers_available": TRANSFORMERS_AVAILABLE
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "models": {
            "sklearn": SKLEARN_AVAILABLE,
            "transformers": TRANSFORMERS_AVAILABLE
        }
    }

@app.post("/classify", response_model=ClassifyResponse)
async def classify_text(request: ClassifyRequest):
    """
    Advanced Ensemble Classification (Tâche 5)
    Combines Keywords, Multi-language BERT, and Statistical Models
    """
    try:
        # 1. Run Ensemble Inference
        result = classifier.classify(
            text=request.text,
            lang=request.language
        )
        
        # 2. Extract results
        top_category = result["classification"]
        confidence = result["confidence"]
        explainability = result["explainability"]
        
        # 3. Determine Sensitivity based on logic + triggers
        sensitivity = "unknown"
        text_lower = request.text.lower()
        
        # Priority 1: Direct Keyword/Regex/Medical triggers from classifier
        triggers_str = str(explainability["triggers"])
        if "Rules: " in triggers_str:
            if top_category == "PERSONAL_IDENTITY": sensitivity = "critical"
            elif top_category == "FINANCIAL_DATA": sensitivity = "critical"
            elif top_category == "MEDICAL_DATA": sensitivity = "high"
            
        # Priority 2: Keyword scanning (Secondary backup)
        if sensitivity == "unknown":
            for level, keywords in classifier.SENSITIVITY_KEYWORDS.items():
                if any(kw in text_lower for kw in keywords):
                    sensitivity = level
                    break
        
        # Priority 3: Confidence-based elevation
        if sensitivity == "unknown" and confidence > 0.6:
             if top_category in ["PERSONAL_IDENTITY", "FINANCIAL_DATA"]:
                 sensitivity = "high"
             elif top_category in ["MEDICAL_DATA"]:
                 sensitivity = "medium"

        return ClassifyResponse(
            success=True,
            text=result["text_preview"],
            classification=top_category,
            sensitivity_level=sensitivity,
            confidence=confidence,
            model_used=request.model,
            explainability=explainability,
            categories=result["raw_scores"]["statistical"] if result["raw_scores"]["statistical"] else {top_category: confidence}
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories():
    """Get available classification categories"""
    return {
        "categories": classifier.CATEGORY_LABELS,
        "sensitivity_levels": list(classifier.SENSITIVITY_KEYWORDS.keys())
    }

# ====================================================================
# VALIDATION WORKFLOW (For Human Review) - MONGO DB
# ====================================================================

@app.get("/pending")
async def get_pending_classifications():
    """Get classifications awaiting human validation"""
    if db is not None:
        cursor = db.pending_classifications.find().limit(50)
        # Convert _id to string if needed, or exclude it
        classifications = []
        async for doc in cursor:
             doc["_id"] = str(doc["_id"])
             classifications.append(doc)
    else:
        classifications = []
        
    return {
        "pending": len(classifications),
        "classifications": classifications
    }

@app.post("/validate/{classification_id}")
async def validate_classification(classification_id: str, action: str = "confirm"):
    """Validate a pending classification"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    classification = await db.pending_classifications.find_one({"id": classification_id})
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    # Remove from pending
    await db.pending_classifications.delete_one({"id": classification_id})
    
    # Add validation metadata
    classification["validation"] = {
        "action": action,
        "validated_at": datetime.now().isoformat()
    }
    
    # Add to validated collection if confirmed
    if action == "confirm":
        await db.validated_classifications.insert_one(classification)
    
    return {
        "success": True,
        "message": f"Classification {action}ed",
        "classification_id": classification_id
    }

@app.post("/add-pending")
async def add_pending_classification(request: ClassifyRequest):
    """Classify and add to pending queue for validation"""
    result = classifier.classify(text=request.text, lang=request.language)
    
    classification_id = str(uuid.uuid4())
    classification_data = {
        "id": classification_id,
        "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
        "created_at": datetime.now().isoformat(),
        **result
    }
    
    if db is not None:
        await db.pending_classifications.insert_one(classification_data)
        # Remove _id from response
        if "_id" in classification_data:
            del classification_data["_id"]
    
    return {
        "success": True,
        "classification_id": classification_id,
        "classification": result
    }

@app.post("/retrain")
async def retrain_model():
    """Trigger active learning from human-validated data"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
        
    try:
        # 1. Fetch all validated classifications
        cursor = db.validated_classifications.find()
        validated_data = []
        async for doc in cursor:
            validated_data.append({
                "text": doc.get("text_preview", doc.get("text", "")),
                "label": doc.get("classification", "OTHER")
            })
            
        if not validated_data:
             return {"success": False, "message": "No validated data found to retrain"}

        # 2. Trigger retraining
        success = classifier.retrain_from_validated(validated_data)
        
        return {
            "success": success,
            "message": f"Retrained on {len(validated_data)} samples" if success else "Retraining failed",
            "samples_used": len(validated_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validated")
async def get_validated():
    """Get validated classifications"""
    if db is not None:
        cursor = db.validated_classifications.find().sort("created_at", -1).limit(50)
        validated = []
        async for doc in cursor:
             doc["_id"] = str(doc["_id"])
             validated.append(doc)
    else:
        validated = []
        
    return {
        "count": len(validated),
        "validated": validated
    }

if __name__ == "__main__":
    print(f"\\n" + "="*60)
    print(f"🧠 CLASSIFICATION SERVICE (MONGO) - Tâche 5")
    print(f"="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
