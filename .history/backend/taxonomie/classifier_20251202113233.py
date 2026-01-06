"""
Moteur de Classification de Données Sensibles - Maroc
Basé sur taxonomie personnalisée + Microsoft Presidio
"""

import re
import json
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# ====================================================================
# MODÈLES DE DONNÉES
# ====================================================================

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

# ====================================================================
# CLASSE PRINCIPALE DE DÉTECTION
# ====================================================================

class PIIDetectionEngine:
    def __init__(self, taxonomy_path: Optional[str] = None):
        if taxonomy_path is None:
            taxonomy_path = Path(__file__).parent / "taxonomie" / "taxonomie.json"
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        # Ici tu peux ajouter Presidio si besoin
        self.presidio_analyzer = None  # placeholder
        self.presidio_anonymizer = AnonymizerEngine()
        self.compiled_patterns = self._compile_patterns()

    def _load_taxonomy(self, path: str) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        # Exemple minimal
        return {}

    def analyze(self, text: str, language: str = "fr", use_presidio: bool = True,
                confidence_threshold: float = 0.5) -> List[Dict]:
        # Exemple minimal, renvoie texte brut comme détection
        return [{
            "entity_type": "EXAMPLE",
            "category": "TEST",
            "value": text[:10],
            "start": 0,
            "end": min(10, len(text)),
            "sensitivity_level": "low",
            "confidence_score": 1.0,
            "detection_method": "regex",
            "context": text[:50]
        }]

    def anonymize_text(self, text: str, detections: List[Dict]) -> str:
        # Exemple minimal
        return text.replace(detections[0]["value"], "[ANONYMIZED]")

# ====================================================================
# INITIALISATION DU MOTEUR
# ====================================================================

taxonomy_file = Path(__file__).parent / "taxonomie" / "taxonomie.json"
detection_engine = PIIDetectionEngine(taxonomy_path=str(taxonomy_file))

# ====================================================================
# FASTAPI
# ====================================================================

app = FastAPI(
    title="Classification Engine API",
    description="API de détection et classification de données personnelles et sensibles (Maroc)",
    version="1.1.0"
)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    start_time = time.time()
    try:
        detections = detection_engine.analyze(
            text=request.text,
            language=request.language,
            use_presidio=request.use_presidio,
            confidence_threshold=request.confidence_threshold
        )
        anonymized_text = None
        if request.anonymize:
            anonymized_text = detection_engine.anonymize_text(request.text, detections)
            for det in detections:
                det["anonymized_value"] = "[ANONYMIZED]"
        summary = {}
        for det in detections:
            summary[det["category"]] = summary.get(det["category"], 0) + 1
        execution_time = (time.time() - start_time) * 1000
        detection_results = [
            DetectionResult(**d) for d in detections
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "engine": "ready",
        "taxonomy_loaded": detection_engine.taxonomy is not None
    }

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    import uvicorn

    print("=== DÉMARRAGE DU SERVEUR ===")
    uvicorn.run(app, host="0.0.0.0", port=8000)
