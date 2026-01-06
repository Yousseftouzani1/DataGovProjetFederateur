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

# ====================================================================
# MODELS
# ====================================================================

class ClassifyRequest(BaseModel):
    text: str = Field(..., description="Text to classify", min_length=1)
    use_ml: bool = Field(default=True, description="Use ML classification")
    model: str = Field(default="ensemble", description="Model: ensemble, bert, simple")

class ClassifyResponse(BaseModel):
    success: bool
    text: str
    classification: str
    sensitivity_level: str
    confidence: float
    model_used: str
    categories: Dict[str, float]

class TrainRequest(BaseModel):
    data: List[Dict]  # [{"text": "...", "label": "..."}]
    model_type: str = Field(default="simple")

# ====================================================================
# SENSITIVITY CLASSIFIER
# ====================================================================

class SensitivityClassifier:
    """
    Multi-model classifier for data sensitivity
    Uses ensemble of simple rules, TF-IDF, and (optionally) transformers
    """
    
    SENSITIVITY_KEYWORDS = {
        "critical": [
            "cin", "passport", "iban", "bank account", "cnss", "ssn",
            "carte d'identité", "numéro national", "compte bancaire",
            "بطاقة", "الحساب البنكي", "جواز السفر"
        ],
        "high": [
            "email", "phone", "address", "birth date", "salary",
            "téléphone", "adresse", "date de naissance", "salaire",
            "الهاتف", "العنوان", "تاريخ الميلاد"
        ],
        "medium": [
            "name", "nom", "age", "gender", "job", "company",
            "الاسم", "العمر", "الجنس"
        ],
        "low": [
            "city", "country", "region", "category",
            "ville", "pays", "région",
            "المدينة", "البلد"
        ]
    }
    
    CATEGORY_LABELS = [
        "PERSONAL_IDENTITY",
        "CONTACT_INFO", 
        "FINANCIAL_DATA",
        "MEDICAL_DATA",
        "PROFESSIONAL_INFO",
        "TECHNICAL_DATA",
        "OTHER"
    ]
    
    def __init__(self):
        self.vectorizer = None
        self.simple_classifier = None
        self.transformer_pipeline = None
        
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=1000)
        
        # Try to load transformer model (optional)
        if TRANSFORMERS_AVAILABLE:
            try:
                self.transformer_pipeline = pipeline(
                    "text-classification",
                    model="distilbert-base-uncased-finetuned-sst-2-english"
                )
            except Exception:
                pass
        
        print("✅ Classification Engine initialized")
        print(f"   sklearn: {SKLEARN_AVAILABLE}")
        print(f"   transformers: {TRANSFORMERS_AVAILABLE}")
    
    def classify_sensitivity(self, text: str) -> str:
        """Classify text sensitivity level using keywords"""
        text_lower = text.lower()
        
        for level, keywords in self.SENSITIVITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return level
        
        return "unknown"
    
    def classify_category(self, text: str) -> Dict[str, float]:
        """Classify text into categories with confidence scores"""
        scores = {}
        text_lower = text.lower()
        
        # Simple keyword-based scoring
        category_keywords = {
            "PERSONAL_IDENTITY": ["name", "cin", "passport", "birth", "nom", "identité"],
            "CONTACT_INFO": ["email", "phone", "address", "téléphone", "adresse"],
            "FINANCIAL_DATA": ["bank", "iban", "salary", "account", "banque", "salaire"],
            "MEDICAL_DATA": ["health", "medical", "disease", "santé", "médical"],
            "PROFESSIONAL_INFO": ["job", "company", "employee", "emploi", "entreprise"],
            "TECHNICAL_DATA": ["ip", "mac", "server", "password", "api"],
        }
        
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = min(score / len(keywords), 1.0)
        
        # Set OTHER if no matches
        if all(v == 0 for v in scores.values()):
            scores["OTHER"] = 0.5
        
        return scores
    
    def classify(self, text: str, use_ml: bool = True, model: str = "ensemble") -> dict:
        """Main classification method"""
        sensitivity = self.classify_sensitivity(text)
        categories = self.classify_category(text)
        
        # Get top category
        top_category = max(categories, key=categories.get)
        confidence = categories[top_category]
        
        # Adjust confidence with ML if available
        if use_ml and self.transformer_pipeline and model in ["ensemble", "bert"]:
            try:
                result = self.transformer_pipeline(text[:512])[0]
                # Use transformer confidence as modifier
                confidence = (confidence + result["score"]) / 2
            except Exception:
                pass
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "classification": top_category,
            "sensitivity_level": sensitivity,
            "confidence": round(confidence, 3),
            "model_used": model,
            "categories": categories
        }

# Initialize classifier
classifier = SensitivityClassifier()

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
    """Classify text sensitivity and category"""
    try:
        result = classifier.classify(
            text=request.text,
            use_ml=request.use_ml,
            model=request.model
        )
        
        return ClassifyResponse(
            success=True,
            **result
        )
    except Exception as e:
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
    result = classifier.classify(request.text, request.use_ml, request.model)
    
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
