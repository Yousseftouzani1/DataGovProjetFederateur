"""
Moteur de Classification de Données Sensibles - Maroc
Basé sur taxonomie personnalisée + Microsoft Presidio
Version complète et opérationnelle
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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
    COMBINED = "combined"

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Texte à analyser", min_length=1)
    language: str = Field(default="fr", description="Langue du texte (fr/en/ar)")
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
    anonymized_text: Optional[str] = None

# ====================================================================
# CLASSE PRINCIPALE DE DÉTECTION
# ====================================================================

class PIIDetectionEngine:
    def __init__(self, taxonomy_path: Optional[str] = None):
        """Initialise le moteur avec la taxonomie"""
        if taxonomy_path and Path(taxonomy_path).exists():
            self.taxonomy = self._load_taxonomy(taxonomy_path)
        else:
            # Taxonomie embarquée si fichier non trouvé
            self.taxonomy = self._get_embedded_taxonomy()
        
        self.compiled_patterns = self._compile_patterns()
        self.keyword_matchers = self._build_keyword_matchers()

    def _load_taxonomy(self, path: str) -> Dict:
        """Charge la taxonomie depuis un fichier JSON"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_embedded_taxonomy(self) -> Dict:
        """Retourne une taxonomie embarquée minimale"""
        return {
            "categories": [
                {
                    "class": "IDENTITE_PERSONNELLE",
                    "class_en": "PERSONAL_IDENTITY",
                    "type": "PII",
                    "subclasses": [
                        {
                            "name": "Nom complet",
                            "regex_patterns": ["\\b[A-Z][a-zàâçéèêëïîôùûü-]+\\s+[A-Z][a-zàâçéèêëïîôùûü-]+\\b"],
                            "sensitivity_level": "high"
                        },
                        {
                            "name": "CIN - Carte d'Identité Nationale",
                            "regex_patterns": ["\\b[A-Z]{1,2}\\d{5,8}\\b"],
                            "sensitivity_level": "critical"
                        },
                        {
                            "name": "Date de naissance",
                            "regex_patterns": ["\\b(0[1-9]|[12][0-9]|3[01])[-/](0[1-9]|1[0-2])[-/](19|20)\\d{2}\\b"],
                            "sensitivity_level": "high"
                        }
                    ]
                },
                {
                    "class": "COORDONNEES",
                    "class_en": "CONTACT_INFORMATION",
                    "type": "PII",
                    "subclasses": [
                        {
                            "name": "Numéro de téléphone",
                            "regex_patterns": ["\\b(\\+212|0)[5-7]\\d{8}\\b"],
                            "sensitivity_level": "high"
                        },
                        {
                            "name": "Adresse email",
                            "regex_patterns": ["\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b"],
                            "sensitivity_level": "high"
                        }
                    ]
                },
                {
                    "class": "DONNEES_FINANCIERES",
                    "class_en": "FINANCIAL_DATA",
                    "type": "SPI",
                    "subclasses": [
                        {
                            "name": "RIB / IBAN",
                            "regex_patterns": ["\\bMA\\d{2}[A-Z0-9]{22}\\b"],
                            "sensitivity_level": "critical"
                        },
                        {
                            "name": "Numéro de carte bancaire",
                            "regex_patterns": ["\\b(?:\\d{4}[ -]?){3}\\d{4}\\b"],
                            "sensitivity_level": "critical"
                        }
                    ]
                }
            ]
        }

    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Compile tous les regex patterns de la taxonomie"""
        compiled = {}
        
        for category in self.taxonomy.get("categories", []):
            category_name = category["class"]
            compiled[category_name] = []
            
            for subclass in category.get("subclasses", []):
                entity_name = subclass.get("name", "Unknown")
                patterns = subclass.get("regex_patterns", [])
                sensitivity = subclass.get("sensitivity_level", "unknown")
                
                for pattern_str in patterns:
                    try:
                        compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
                        compiled[category_name].append((
                            compiled_pattern,
                            {
                                "entity_type": entity_name,
                                "category": category_name,
                                "sensitivity_level": sensitivity,
                                "type": category.get("type", "PII")
                            }
                        ))
                    except re.error as e:
                        print(f"Erreur compilation regex pour {entity_name}: {e}")
        
        return compiled

    def _build_keyword_matchers(self) -> Dict[str, Dict]:
        """Construit des matchers par mots-clés"""
        matchers = {}
        
        for category in self.taxonomy.get("categories", []):
            for subclass in category.get("subclasses", []):
                entity_name = subclass.get("name", "")
                synonyms = subclass.get("synonyms_fr", []) + subclass.get("synonyms_en", [])
                acronyms = subclass.get("acronyms_fr", []) + subclass.get("acronyms_en", [])
                
                all_keywords = [entity_name] + synonyms + acronyms
                
                for keyword in all_keywords:
                    if keyword and len(keyword) > 2:
                        matchers[keyword.lower()] = {
                            "entity_type": entity_name,
                            "category": category["class"],
                            "sensitivity_level": subclass.get("sensitivity_level", "unknown")
                        }
        
        return matchers

    def _get_context(self, text: str, start: int, end: int, context_size: int = 30) -> str:
        """Extrait le contexte autour d'une détection"""
        ctx_start = max(0, start - context_size)
        ctx_end = min(len(text), end + context_size)
        context = text[ctx_start:ctx_end]
        
        # Ajouter des ellipses si tronqué
        if ctx_start > 0:
            context = "..." + context
        if ctx_end < len(text):
            context = context + "..."
        
        return context

    def _detect_with_regex(self, text: str) -> List[Dict]:
        """Détection par expressions régulières"""
        detections = []
        
        for category_name, patterns in self.compiled_patterns.items():
            for pattern, metadata in patterns:
                for match in pattern.finditer(text):
                    detection = {
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.85,  # Score par défaut pour regex
                        "detection_method": "regex",
                        "context": self._get_context(text, match.start(), match.end())
                    }
                    detections.append(detection)
        
        return detections

    def _detect_with_keywords(self, text: str) -> List[Dict]:
        """Détection par mots-clés"""
        detections = []
        text_lower = text.lower()
        
        for keyword, metadata in self.keyword_matchers.items():
            # Recherche simple de mots-clés
            start_pos = 0
            while True:
                pos = text_lower.find(keyword, start_pos)
                if pos == -1:
                    break
                
                # Vérifier que c'est un mot complet (pas dans un autre mot)
                if (pos == 0 or not text_lower[pos-1].isalnum()) and \
                   (pos + len(keyword) >= len(text_lower) or not text_lower[pos + len(keyword)].isalnum()):
                    
                    detection = {
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "value": text[pos:pos + len(keyword)],
                        "start": pos,
                        "end": pos + len(keyword),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.65,
                        "detection_method": "keyword",
                        "context": self._get_context(text, pos, pos + len(keyword))
                    }
                    detections.append(detection)
                
                start_pos = pos + 1
        
        return detections

    def _merge_overlapping_detections(self, detections: List[Dict]) -> List[Dict]:
        """Fusionne les détections qui se chevauchent"""
        if not detections:
            return []
        
        # Trier par position de début
        sorted_detections = sorted(detections, key=lambda x: (x["start"], -x["confidence_score"]))
        merged = []
        
        for detection in sorted_detections:
            # Vérifier si elle chevauche une détection existante
            overlapping = False
            for existing in merged:
                if (detection["start"] >= existing["start"] and detection["start"] < existing["end"]) or \
                   (detection["end"] > existing["start"] and detection["end"] <= existing["end"]):
                    # Garder la détection avec le meilleur score de confiance
                    if detection["confidence_score"] > existing["confidence_score"]:
                        merged.remove(existing)
                        merged.append(detection)
                    overlapping = True
                    break
            
            if not overlapping:
                merged.append(detection)
        
        return sorted(merged, key=lambda x: x["start"])

    def analyze(self, text: str, language: str = "fr", 
                confidence_threshold: float = 0.5) -> List[Dict]:
        """Analyse le texte et détecte les données sensibles"""
        
        if not text or not text.strip():
            return []
        
        # Détection par regex
        regex_detections = self._detect_with_regex(text)
        
        # Détection par mots-clés
        keyword_detections = self._detect_with_keywords(text)
        
        # Combiner et filtrer
        all_detections = regex_detections + keyword_detections
        all_detections = [d for d in all_detections if d["confidence_score"] >= confidence_threshold]
        
        # Fusionner les chevauchements
        merged_detections = self._merge_overlapping_detections(all_detections)
        
        return merged_detections

    def anonymize_text(self, text: str, detections: List[Dict]) -> str:
        """Anonymise le texte en remplaçant les valeurs détectées"""
        if not detections:
            return text
        
        # Trier par position décroissante pour ne pas décaler les indices
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)
        
        anonymized = text
        for detection in sorted_detections:
            entity_type = detection["entity_type"]
            start = detection["start"]
            end = detection["end"]
            
            # Créer un placeholder basé sur le type
            placeholder = f"[{entity_type.upper().replace(' ', '_')}]"
            
            anonymized = anonymized[:start] + placeholder + anonymized[end:]
        
        return anonymized

# ====================================================================
# INITIALISATION DU MOTEUR
# ====================================================================

# Essayer de charger depuis fichier, sinon utiliser taxonomie embarquée
taxonomy_file = Path(__file__).parent / "taxonomie.json"
detection_engine = PIIDetectionEngine(taxonomy_path=str(taxonomy_file) if taxonomy_file.exists() else None)

# ====================================================================
# FASTAPI
# ====================================================================

app = FastAPI(
    title="Classification Engine API - Maroc",
    description="API de détection et classification de données personnelles et sensibles",
    version="1.1.0"
)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyse un texte et détecte les données sensibles"""
    start_time = time.time()
    
    try:
        # Analyse du texte
        detections = detection_engine.analyze(
            text=request.text,
            language=request.language,
            confidence_threshold=request.confidence_threshold
        )
        
        # Anonymisation si demandée
        anonymized_text = None
        if request.anonymize and detections:
            anonymized_text = detection_engine.anonymize_text(request.text, detections)
            for det in detections:
                det["anonymized_value"] = f"[{det['entity_type'].upper().replace(' ', '_')}]"
        
        # Créer un résumé par catégorie
        summary = {}
        for det in detections:
            category = det["category"]
            summary[category] = summary.get(category, 0) + 1
        
        # Temps d'exécution
        execution_time = (time.time() - start_time) * 1000
        
        # Construire les résultats
        detection_results = [DetectionResult(**d) for d in detections]
        
        return AnalyzeResponse(
            success=True,
            text_length=len(request.text),
            detections_count=len(detections),
            detections=detection_results,
            summary=summary,
            execution_time_ms=round(execution_time, 2),
            anonymized_text=anonymized_text
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@app.get("/health")
async def health_check():
    """Vérifie l'état du service"""
    return {
        "status": "healthy",
        "engine": "ready",
        "taxonomy_loaded": detection_engine.taxonomy is not None,
        "patterns_count": sum(len(patterns) for patterns in detection_engine.compiled_patterns.values()),
        "keywords_count": len(detection_engine.keyword_matchers)
    }

@app.get("/categories")
async def get_categories():
    """Retourne la liste des catégories disponibles"""
    categories = []
    for category in detection_engine.taxonomy.get("categories", []):
        categories.append({
            "name": category["class"],
            "name_en": category.get("class_en", ""),
            "type": category.get("type", ""),
            "subclasses_count": len(category.get("subclasses", []))
        })
    return {"categories": categories}

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("MOTEUR DE DÉTECTION DE DONNÉES SENSIBLES - MAROC")
    print("=" * 60)
    print(f"Patterns compilés: {sum(len(p) for p in detection_engine.compiled_patterns.values())}")
    print(f"Mots-clés: {len(detection_engine.keyword_matchers)}")
    print("=" * 60)
    print("\nDémarrage du serveur sur http://127.0.0.1:8000")
    print("Documentation API: http://127.0.0.1:8000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000)