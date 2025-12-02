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
    """Moteur de détection hybride : Taxonomie + Presidio"""
    
    def __init__(self, taxonomy_path: str = "taxonomie_maroc_sans_gdpr.json"):
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        self.presidio_analyzer = self._init_presidio()
        self.presidio_anonymizer = AnonymizerEngine()
        self.compiled_patterns = self._compile_patterns()
        
    def _load_taxonomy(self, path: str) -> Dict:
        """Charge la taxonomie JSON"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Si le fichier n'existe pas, utiliser la taxonomie fournie
            return json.loads(TAXONOMY_JSON_FALLBACK)
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Précompile tous les patterns regex pour performance"""
        compiled = {}
        for category in self.taxonomy["categories"]:
            for subclass in category["subclasses"]:
                key = f"{category['class']}:{subclass['name']}"
                patterns = subclass.get("regex_patterns", [])
                compiled[key] = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns]
        return compiled
    
    def _init_presidio(self) -> AnalyzerEngine:
        """Initialise Presidio avec recognizers personnalisés pour le Maroc"""
        
        # Configuration NLP
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "fr", "model_name": "fr_core_news_sm"},
                {"lang_code": "en", "model_name": "en_core_web_sm"}
            ]
        }
        
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        
        # Ajout de recognizers personnalisés pour le Maroc
        self._add_moroccan_recognizers(registry)
        
        return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine)
    
    def _add_moroccan_recognizers(self, registry: RecognizerRegistry):
        """Ajoute des recognizers spécifiques au Maroc dans Presidio"""
        
        # CIN Marocaine
        cin_pattern = Pattern(
            name="cin_pattern",
            regex=r"\b[A-Z]{1,2}\d{5,8}\b",
            score=0.95
        )
        cin_recognizer = PatternRecognizer(
            supported_entity="MA_CIN",
            patterns=[cin_pattern],
            context=["CIN", "carte", "identité", "nationale"]
        )
        registry.add_recognizer(cin_recognizer)
        
        # Téléphone marocain
        phone_pattern = Pattern(
            name="ma_phone",
            regex=r"\b(\+212|0)[5-7]\d{8}\b",
            score=0.9
        )
        phone_recognizer = PatternRecognizer(
            supported_entity="MA_PHONE",
            patterns=[phone_pattern],
            context=["tél", "téléphone", "mobile", "portable", "GSM"]
        )
        registry.add_recognizer(phone_recognizer)
        
        # IBAN Marocain
        iban_pattern = Pattern(
            name="ma_iban",
            regex=r"\bMA\d{2}[A-Z0-9]{22}\b",
            score=0.95
        )
        iban_recognizer = PatternRecognizer(
            supported_entity="MA_IBAN",
            patterns=[iban_pattern],
            context=["IBAN", "RIB", "compte", "bancaire"]
        )
        registry.add_recognizer(iban_recognizer)
        
        # Code Massar
        massar_pattern = Pattern(
            name="code_massar",
            regex=r"\b[MPTJ]\d{9}\b",
            score=0.9
        )
        massar_recognizer = PatternRecognizer(
            supported_entity="MA_MASSAR",
            patterns=[massar_pattern],
            context=["Massar", "étudiant", "élève", "code"]
        )
        registry.add_recognizer(massar_recognizer)
        
        # CNSS
        cnss_pattern = Pattern(
            name="cnss_number",
            regex=r"\b\d{9,10}\b",
            score=0.7
        )
        cnss_recognizer = PatternRecognizer(
            supported_entity="MA_CNSS",
            patterns=[cnss_pattern],
            context=["CNSS", "sécurité", "sociale", "affiliation"]
        )
        registry.add_recognizer(cnss_recognizer)
    
    def detect_with_taxonomy(self, text: str) -> List[Dict]:
        """Détection basée sur la taxonomie (regex + keywords)"""
        results = []
        
        for category in self.taxonomy["categories"]:
            for subclass in category["subclasses"]:
                nom_fr = subclass["name"]
                nom_en = subclass.get("name_en", "")
                niveau = subclass.get("sensitivity_level", "unknown")
                key = f"{category['class']}:{nom_fr}"
                
                # 1. Détection par REGEX
                if key in self.compiled_patterns:
                    for pattern in self.compiled_patterns[key]:
                        for match in pattern.finditer(text):
                            results.append({
                                "entity_type": nom_fr,
                                "entity_type_en": nom_en,
                                "category": category["class"],
                                "value": match.group(0),
                                "start": match.start(),
                                "end": match.end(),
                                "sensitivity_level": niveau,
                                "confidence_score": 0.85,
                                "detection_method": "regex",
                                "context": self._extract_context(text, match.start(), match.end())
                            })
                
                # 2. Détection par KEYWORDS (pour données non structurées)
                else:
                    keywords = (
                        subclass.get("synonyms_fr", []) + 
                        subclass.get("synonyms_en", []) + 
                        [nom_fr.lower(), nom_en.lower()]
                    )
                    keywords = [k for k in keywords if k]  # Retire les vides
                    
                    for keyword in keywords:
                        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                        for match in pattern.finditer(text):
                            results.append({
                                "entity_type": nom_fr,
                                "entity_type_en": nom_en,
                                "category": category["class"],
                                "value": match.group(0),
                                "start": match.start(),
                                "end": match.end(),
                                "sensitivity_level": niveau,
                                "confidence_score": 0.6,
                                "detection_method": "keyword",
                                "context": self._extract_context(text, match.start(), match.end())
                            })
        
        return results
    
    def detect_with_presidio(self, text: str, language: str = "fr") -> List[Dict]:
        """Détection avec Presidio"""
        analyzer_results = self.presidio_analyzer.analyze(
            text=text,
            language=language,
            entities=None,  # Tous les types
            score_threshold=0.5
        )
        
        results = []
        for result in analyzer_results:
            results.append({
                "entity_type": result.entity_type,
                "entity_type_en": result.entity_type,
                "category": self._map_presidio_to_category(result.entity_type),
                "value": text[result.start:result.end],
                "start": result.start,
                "end": result.end,
                "sensitivity_level": self._infer_sensitivity(result.entity_type),
                "confidence_score": result.score,
                "detection_method": "presidio",
                "context": self._extract_context(text, result.start, result.end)
            })
        
        return results
    
    def analyze(
        self,
        text: str,
        language: str = "fr",
        use_presidio: bool = True,
        confidence_threshold: float = 0.5
    ) -> List[Dict]:
        """Analyse complète hybride"""
        
        # Détection taxonomie
        taxonomy_results = self.detect_with_taxonomy(text)
        
        # Détection Presidio
        presidio_results = []
        if use_presidio:
            try:
                presidio_results = self.detect_with_presidio(text, language)
            except Exception as e:
                print(f"Erreur Presidio: {e}")
        
        # Fusion et dédoublonnage
        all_results = taxonomy_results + presidio_results
        deduplicated = self._deduplicate_results(all_results)
        
        # Filtrage par seuil de confiance
        filtered = [r for r in deduplicated if r["confidence_score"] >= confidence_threshold]
        
        return sorted(filtered, key=lambda x: x["start"])
    
    def anonymize_text(self, text: str, detections: List[Dict]) -> str:
        """Anonymise le texte en remplaçant les valeurs sensibles"""
        anonymized = text
        offset = 0
        
        # Tri par position pour éviter les problèmes de décalage
        sorted_detections = sorted(detections, key=lambda x: x["start"])
        
        for detection in sorted_detections:
            start = detection["start"] + offset
            end = detection["end"] + offset
            original = detection["value"]
            
            # Stratégie d'anonymisation selon le type
            replacement = self._get_anonymization_replacement(detection)
            
            anonymized = anonymized[:start] + replacement + anonymized[end:]
            offset += len(replacement) - len(original)
            
            detection["anonymized_value"] = replacement
        
        return anonymized
    
    def _get_anonymization_replacement(self, detection: Dict) -> str:
        """Détermine le remplacement pour l'anonymisation"""
        entity_type = detection["entity_type"].lower()
        
        if "nom" in entity_type or "name" in entity_type:
            return "[NOM]"
        elif "cin" in entity_type or "passeport" in entity_type:
            return "[ID_DOCUMENT]"
        elif "téléphone" in entity_type or "phone" in entity_type:
            return "[TÉLÉPHONE]"
        elif "email" in entity_type:
            return "[EMAIL]"
        elif "iban" in entity_type or "rib" in entity_type:
            return "[COMPTE_BANCAIRE]"
        elif "adresse" in entity_type or "address" in entity_type:
            return "[ADRESSE]"
        elif "date" in entity_type and "naissance" in entity_type:
            return "[DATE_NAISSANCE]"
        else:
            return f"[{detection['category']}]"
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Supprime les détections en doublon (même position, même type)"""
        seen = set()
        unique = []
        
        for r in results:
            key = (r["entity_type"], r["start"], r["end"])
            if key not in seen:
                seen.add(key)
                unique.append(r)
            else:
                # Si doublon, garde celui avec le meilleur score
                existing = next((u for u in unique if (u["entity_type"], u["start"], u["end"]) == key), None)
                if existing and r["confidence_score"] > existing["confidence_score"]:
                    unique.remove(existing)
                    unique.append(r)
        
        return unique
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extrait le contexte autour d'une détection"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context = text[context_start:context_end]
        
        # Ajoute des ellipses si tronqué
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context.strip()
    
    def _map_presidio_to_category(self, entity_type: str) -> str:
        """Mappe les types Presidio aux catégories de la taxonomie"""
        mapping = {
            "PERSON": "IDENTITE_PERSONNELLE",
            "EMAIL_ADDRESS": "COORDONNEES",
            "PHONE_NUMBER": "COORDONNEES",
            "CREDIT_CARD": "DONNEES_FINANCIERES",
            "IBAN_CODE": "DONNEES_FINANCIERES",
            "LOCATION": "COORDONNEES",
            "DATE_TIME": "IDENTITE_PERSONNELLE",
            "MA_CIN": "IDENTITE_PERSONNELLE",
            "MA_PHONE": "COORDONNEES",
            "MA_IBAN": "DONNEES_FINANCIERES",
            "MA_MASSAR": "EDUCATION",
            "MA_CNSS": "SECURITE_SOCIALE"
        }
        return mapping.get(entity_type, "AUTRE")
    
    def _infer_sensitivity(self, entity_type: str) -> str:
        """Infère le niveau de sensibilité d'un type d'entité"""
        critical_types = ["CREDIT_CARD", "IBAN_CODE", "MA_CIN", "MA_IBAN", "MA_CNSS"]
        high_types = ["PHONE_NUMBER", "EMAIL_ADDRESS", "MA_PHONE", "PERSON"]
        
        if entity_type in critical_types:
            return "critical"
        elif entity_type in high_types:
            return "high"
        else:
            return "medium"

# ============================================================================
# INITIALISATION GLOBALE
# ============================================================================

# Taxonomie JSON en fallback (copie de votre document)
TAXONOMY_JSON_FALLBACK = """
{votre_json_taxonomie_complet}
"""

detection_engine = PIIDetectionEngine()

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