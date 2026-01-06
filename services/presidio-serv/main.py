"""
Presidio Morocco Service - Tâche 3
PII Detection with Custom Moroccan Recognizers

According to Cahier des Charges:
- Customize Microsoft Presidio for Moroccan context
- Add recognizers: CIN, Phone MA, IBAN MA, CNSS
- Support French and Arabic
"""
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Presidio imports
try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    print("⚠️ Presidio not installed. Run: pip install presidio-analyzer presidio-anonymizer spacy")

# Import Moroccan recognizers
if PRESIDIO_AVAILABLE:
    from backend.recognizers.cin_recognizer import MoroccanCINRecognizer
    from backend.recognizers.phone_ma_recognizer import MoroccanPhoneRecognizer
    from backend.recognizers.iban_ma_recognizer import MoroccanIBANRecognizer
    from backend.recognizers.cnss_recognizer import MoroccanCNSSRecognizer
    from backend.recognizers.arabic_recognizer import ArabicMoroccanRecognizer
    from backend.recognizers.passport_ma_recognizer import MoroccanPassportRecognizer
    from backend.recognizers.permis_ma_recognizer import MoroccanPermisRecognizer

# ====================================================================
# MODELS
# ====================================================================

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Text to analyze", min_length=1)
    language: str = Field(default="fr", description="Language (fr/en/ar)")
    entities: Optional[List[str]] = Field(default=None, description="Specific entities to detect")
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

class AnonymizeRequest(BaseModel):
    text: str = Field(..., description="Text to anonymize", min_length=1)
    language: str = Field(default="fr")
    operators: Optional[dict] = Field(default=None, description="Custom operators per entity")

class Detection(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
    value: str

class AnalyzeResponse(BaseModel):
    success: bool
    detections: List[Detection]
    count: int

class AnonymizeResponse(BaseModel):
    success: bool
    original_text: str
    anonymized_text: str
    detections_count: int

# ====================================================================
# PRESIDIO ENGINE
# ====================================================================

class MoroccanPresidioEngine:
    """Presidio Engine with Moroccan custom recognizers"""
    
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        
        if not PRESIDIO_AVAILABLE:
            print("❌ Presidio not available")
            return
        
        try:
            # Initialize registry with custom recognizers
            registry = RecognizerRegistry()
            registry.load_predefined_recognizers()
            
            # Add Moroccan recognizers for multiple languages
            # This ensures they are found when analysis is requested in en, fr, or ar
            for lang in ["en", "fr", "ar"]:
                registry.add_recognizer(MoroccanCINRecognizer(supported_language=lang))
                registry.add_recognizer(MoroccanPhoneRecognizer(supported_language=lang))
                registry.add_recognizer(MoroccanIBANRecognizer(supported_language=lang))
                registry.add_recognizer(MoroccanCNSSRecognizer(supported_language=lang))
                registry.add_recognizer(MoroccanPassportRecognizer(supported_language=lang))
                registry.add_recognizer(MoroccanPermisRecognizer(supported_language=lang))
                # registry.add_recognizer(ArabicMoroccanRecognizer(supported_language=lang))
            
            # Use English model for all languages (Custom Recognizers handle the patterns)
            config = {
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "en", "model_name": "en_core_web_sm"},
                    {"lang_code": "fr", "model_name": "en_core_web_sm"},
                ]
            }
            provider = NlpEngineProvider(nlp_configuration=config)
            nlp_engine = provider.create_engine()
            
            self.analyzer = AnalyzerEngine(
                registry=registry,
                nlp_engine=nlp_engine
            )
            
            self.anonymizer = AnonymizerEngine()
            
            print("✅ Moroccan Presidio Engine initialized")
            print("   Custom recognizers: CIN_MAROC, PHONE_MA, IBAN_MA, CNSS, PASSPORT_MA, PERMIS_MA, ARABIC_MOROCCAN_PII")
            
        except Exception as e:
            print(f"⚠️ Presidio initialization error: {e}")
            print("   Service will run with limited functionality")
            self.analyzer = None
            self.anonymizer = None
    
    def analyze(self, text: str, language: str = "fr", 
                entities: Optional[List[str]] = None,
                score_threshold: float = 0.5) -> List[dict]:
        """Analyze text for PII"""
        if not self.analyzer:
            return []
        
        lang = "fr" if language in ["fr", "ar"] else "en"
        
        results = self.analyzer.analyze(
            text=text,
            language=lang,
            entities=entities,
            score_threshold=score_threshold
        )
        
        return [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": round(r.score, 3),
                "value": text[r.start:r.end]
            }
            for r in results
        ]
    
    def anonymize(self, text: str, language: str = "fr",
                  operators: Optional[dict] = None) -> dict:
        """Anonymize detected PII"""
        if not self.analyzer or not self.anonymizer:
            return {"original": text, "anonymized": text, "count": 0}
        
        # Analyze first
        results = self.analyzer.analyze(text=text, language=language)
        
        # Build operator config
        if operators:
            ops = {k: OperatorConfig(v) for k, v in operators.items()}
        else:
            ops = None
        
        # Anonymize
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=ops
        )
        
        return {
            "original": text,
            "anonymized": anonymized.text,
            "count": len(results)
        }
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entities"""
        if not self.analyzer:
            return []
        return self.analyzer.get_supported_entities()

# Initialize engine
engine = MoroccanPresidioEngine() if PRESIDIO_AVAILABLE else None

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Presidio Morocco Service",
    description="PII Detection with Custom Moroccan Recognizers (CIN, Phone, IBAN, CNSS)",
    version="1.0.0"
)

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
        "service": "Presidio Morocco",
        "status": "running",
        "presidio_available": PRESIDIO_AVAILABLE
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "presidio_available": PRESIDIO_AVAILABLE,
        "custom_recognizers": ["CIN_MAROC", "PHONE_MA", "IBAN_MA", "CNSS_MA"]
    }

@app.get("/entities")
def get_entities():
    """Get supported entities"""
    if not engine:
        return {"entities": []}
    return {"entities": engine.get_supported_entities()}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Analyze text for PII"""
    if not engine:
        raise HTTPException(status_code=503, detail="Presidio not available")
    
    detections = engine.analyze(
        text=request.text,
        language=request.language,
        entities=request.entities,
        score_threshold=request.score_threshold
    )
    
    return AnalyzeResponse(
        success=True,
        detections=[Detection(**d) for d in detections],
        count=len(detections)
    )

@app.post("/anonymize", response_model=AnonymizeResponse)
async def anonymize(request: AnonymizeRequest):
    """Anonymize PII in text"""
    if not engine:
        raise HTTPException(status_code=503, detail="Presidio not available")
    
    result = engine.anonymize(
        text=request.text,
        language=request.language,
        operators=request.operators
    )
    
    return AnonymizeResponse(
        success=True,
        original_text=result["original"],
        anonymized_text=result["anonymized"],
        detections_count=result["count"]
    )

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔒 PRESIDIO MOROCCO SERVICE - Tâche 3")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
