"""
Moteur de Classification de Données Sensibles - Maroc
Basé sur taxonomie personnalisée + Microsoft Presidio
"""

import re
import json
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from pathlib import Path
# ============================================================================
# CONFIGURATION
# ============================================================================

app = FastAPI(
    title="Classification Engine API",
    description="API de détection et classification de données personnelles et sensibles (Maroc)",
    version="1.1.0"
)

# ============================================================================
# MODÈLES DE DONNÉES
# ============================================================================
taxonomy_file = Path(__file__).parent / "taxonomie" / "taxonomie.json"
detection_engine = PIIDetectionEngine(taxonomy_path=str(taxonomy_file))
class SensitivityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class DetectionMethod(str, Enum):
    REGEX = "regex"
    KEYWORD = "keyword"
    PRESIDIO = "presidio"
    HYBRID = "hybrid"

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Texte à analyser", min_length=1)
    language: str = Field(default="fr", description="Langue du texte (fr/en/ar)")
    use_presidio: bool = Field(default=True, description="Activer Presidio pour détection avancée")
    anonymize: bool = Field(default=False, description="Anonymiser les résultats")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Seuil de confiance minimum")

class DetectionResult(BaseModel):
    entity_type: str
    category: str
    value: str
    start: int
    end: int
    sensitivity_level: str
    confidence_score: float
    detection_method: str
    context: Optional[str] = None
    anonymized_value: Optional[str] = None

class AnalyzeResponse(BaseModel):
    success: bool
    text_length: int
    detections_count: int
    detections: List[DetectionResult]
    summary: Dict[str, int]
    execution_time_ms: float

# ============================================================================
# CLASSE PRINCIPALE DE DÉTECTION
# ============================================================================

class PIIDetectionEngine:
    def __init__(self, taxonomy_path: Optional[str] = None):
        if taxonomy_path is None:
            # chemin par défaut vers ton projet
            taxonomy_path = Path(__file__).parent / "taxonomie" / "taxonomie.json"
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        self.presidio_analyzer = self._init_presidio()
        self.presidio_anonymizer = AnonymizerEngine()
        self.compiled_patterns = self._compile_patterns()

    def _load_taxonomy(self, path: str) -> Dict:
        """Charge la taxonomie JSON"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

# ============================================================================
# ENDPOINTS FASTAPI
# ============================================================================

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Analyse un texte et détecte les données personnelles et sensibles
    """
    import time
    start_time = time.time()
    
    try:
        # Analyse
        detections = detection_engine.analyze(
            text=request.text,
            language=request.language,
            use_presidio=request.use_presidio,
            confidence_threshold=request.confidence_threshold
        )
        
        # Anonymisation si demandée
        anonymized_text = None
        if request.anonymize:
            anonymized_text = detection_engine.anonymize_text(request.text, detections)
            for det in detections:
                if "anonymized_value" not in det:
                    det["anonymized_value"] = detection_engine._get_anonymization_replacement(det)
        
        # Statistiques
        summary = {}
        for det in detections:
            category = det["category"]
            summary[category] = summary.get(category, 0) + 1
        
        execution_time = (time.time() - start_time) * 1000
        
        # Conversion en modèle Pydantic
        detection_results = [
            DetectionResult(
                entity_type=d["entity_type"],
                category=d["category"],
                value=d["value"],
                start=d["start"],
                end=d["end"],
                sensitivity_level=d["sensitivity_level"],
                confidence_score=d["confidence_score"],
                detection_method=d["detection_method"],
                context=d.get("context"),
                anonymized_value=d.get("anonymized_value")
            )
            for d in detections
        ]
        
        return AnalyzeResponse(
            success=True,
            text_length=len(request.text),
            detections_count=len(detections),
            detections=detection_results,
            summary=summary,
            execution_time_ms=round(execution_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")

@app.post("/anonymize")
async def anonymize_text_endpoint(request: AnalyzeRequest):
    """
    Anonymise un texte en masquant les données sensibles détectées
    """
    try:
        detections = detection_engine.analyze(
            text=request.text,
            language=request.language,
            use_presidio=request.use_presidio,
            confidence_threshold=request.confidence_threshold
        )
        
        anonymized = detection_engine.anonymize_text(request.text, detections)
        
        return {
            "success": True,
            "original_text": request.text,
            "anonymized_text": anonymized,
            "detections_count": len(detections),
            "detections": detections
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'anonymisation: {str(e)}")

@app.get("/taxonomy")
async def get_taxonomy():
    """
    Retourne la taxonomie complète utilisée
    """
    return detection_engine.taxonomy

@app.get("/categories")
async def get_categories():
    """
    Liste toutes les catégories et sous-classes disponibles
    """
    categories = []
    for cat in detection_engine.taxonomy["categories"]:
        categories.append({
            "class": cat["class"],
            "class_en": cat["class_en"],
            "type": cat["type"],
            "subclasses_count": len(cat["subclasses"]),
            "subclasses": [s["name"] for s in cat["subclasses"]]
        })
    return {"categories": categories}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine": "ready",
        "presidio_enabled": True,
        "taxonomy_loaded": detection_engine.taxonomy is not None
    }

# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Test local
    texte_test = """
    Mr Mohamed BENJELLOUN, CIN KB123456, né le 15/03/1987 à Casablanca,
    téléphone 0654789123, email: m.benjelloun@example.ma,
    IBAN MA64011519000001205000643917, code Massar M123456789,
    groupe sanguin O+, CNSS 1234567890, immatriculation véhicule 12345 ب 67
    """
    
    print("=== TEST DE DÉTECTION ===\n")
    results = detection_engine.analyze(texte_test, use_presidio=True)
    
    for i, res in enumerate(results, 1):
        print(f"{i}. {res['entity_type']} ({res['category']})")
        print(f"   Valeur: {res['value']}")
        print(f"   Sensibilité: {res['sensitivity_level']}")
        print(f"   Confiance: {res['confidence_score']:.2f}")
        print(f"   Méthode: {res['detection_method']}")
        print(f"   Contexte: {res['context']}\n")
    
    # Démarrage du serveur
    print("\n=== DÉMARRAGE DU SERVEUR ===")
    uvicorn.run(app, host="0.0.0.0", port=8000)