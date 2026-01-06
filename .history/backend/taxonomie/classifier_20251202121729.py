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
    detect_names: bool = Field(default=False, description="Activer la détection de noms (peut générer des faux positifs)")

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
        
        # Liste de mots français courants à exclure de la détection de noms
        self.french_stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais',
            'est', 'sont', 'était', 'été', 'être', 'avoir', 'avait', 'avons', 'ont',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'me', 'te', 'se',
            'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'votre',
            'ce', 'cet', 'cette', 'ces', 'qui', 'que', 'quoi', 'dont', 'où',
            'pour', 'par', 'dans', 'sur', 'sous', 'avec', 'sans', 'chez',
            'très', 'plus', 'moins', 'bien', 'mal', 'aussi', 'encore', 'déjà',
            'bonjour', 'merci', 'oui', 'non', 'si', 'comment', 'quand', 'pourquoi'
        }

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
                            "name": "CIN - Carte d'Identité Nationale",
                            "regex_patterns": ["\\b[A-Z]{1,2}\\d{5,8}\\b"],
                            "sensitivity_level": "critical"
                        },
                        {
                            "name": "Date de naissance",
                            "regex_patterns": [
                                "\\b(0[1-9]|[12][0-9]|3[01])[-/](0[1-9]|1[0-2])[-/](19|20)\\d{2}\\b",
                                "\\b(19|20)\\d{2}[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])\\b"
                            ],
                            "sensitivity_level": "high"
                        },
                        {
                            "name": "Numéro de passeport",
                            "regex_patterns": ["\\b[A-Z]{1,2}\\d{6,9}\\b"],
                            "sensitivity_level": "critical"
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
                            "regex_patterns": [
                                "\\b(\\+212|00212)[5-7]\\d{8}\\b",
                                "\\b0[5-7]\\d{8}\\b",
                                "\\b(\\+212|00212)\\s?[5-7]\\s?\\d{2}\\s?\\d{2}\\s?\\d{2}\\s?\\d{2}\\b",
                                "\\b0[5-7]\\s?\\d{2}\\s?\\d{2}\\s?\\d{2}\\s?\\d{2}\\b"
                            ],
                            "sensitivity_level": "high"
                        },
                        {
                            "name": "Adresse email",
                            "regex_patterns": ["\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b"],
                            "sensitivity_level": "high"
                        },
                        {
                            "name": "Adresse postale",
                            "regex_patterns": ["\\d+[,\\s]+(?:Rue|Avenue|Boulevard|Bd|Av)[\\s\\w-]+[,\\s]+\\d{5}"],
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
                            "regex_patterns": ["\\bMA\\d{2}[A-Z0-9]{22,24}\\b"],
                            "sensitivity_level": "critical"
                        },
                        {
                            "name": "Numéro de carte bancaire",
                            "regex_patterns": [
                                "\\b(?:\\d{4}[ -]?){3}\\d{4}\\b",
                                "\\b\\d{16}\\b"
                            ],
                            "sensitivity_level": "critical"
                        },
                        {
                            "name": "Identifiant fiscal (IF)",
                            "regex_patterns": ["\\b\\d{8,15}\\b"],
                            "sensitivity_level": "critical",
                            "context_required": ["fiscal", "IF", "impôt", "taxe"]
                        }
                    ]
                },
                {
                    "class": "SECURITE_SOCIALE",
                    "class_en": "SOCIAL_SECURITY",
                    "type": "PII",
                    "subclasses": [
                        {
                            "name": "Numéro CNSS",
                            "regex_patterns": ["\\bCNSS[:\\s]*\\d{9,10}\\b", "\\b\\d{9,10}\\b"],
                            "sensitivity_level": "critical",
                            "context_required": ["cnss", "sécurité sociale"]
                        }
                    ]
                },
                {
                    "class": "EDUCATION",
                    "class_en": "EDUCATION",
                    "type": "PII",
                    "subclasses": [
                        {
                            "name": "Code Massar",
                            "regex_patterns": ["\\b[MPTJ]\\d{9}\\b"],
                            "sensitivity_level": "high"
                        },
                        {
                            "name": "CNE - Code National Étudiant",
                            "regex_patterns": ["\\bCNE[:\\s]*[A-Z]\\d{9}\\b"],
                            "sensitivity_level": "high"
                        }
                    ]
                },
                {
                    "class": "DONNEES_SANTE",
                    "class_en": "HEALTH_DATA",
                    "type": "SPI",
                    "subclasses": [
                        {
                            "name": "Groupe sanguin",
                            "regex_patterns": ["\\b(A|B|AB|O)[+−-]\\b"],
                            "sensitivity_level": "high",
                            "context_required": ["sang", "sanguin", "groupe"]
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
                context_required = subclass.get("context_required", [])
                
                for pattern_str in patterns:
                    try:
                        compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
                        compiled[category_name].append((
                            compiled_pattern,
                            {
                                "entity_type": entity_name,
                                "category": category_name,
                                "sensitivity_level": sensitivity,
                                "type": category.get("type", "PII"),
                                "context_required": context_required
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
                
                # Utiliser uniquement les acronymes pour éviter les faux positifs
                all_keywords = acronyms
                
                for keyword in all_keywords:
                    if keyword and len(keyword) > 1:
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

    def _check_context_required(self, text: str, match_start: int, match_end: int, 
                                context_keywords: List[str], window_size: int = 50) -> bool:
        """Vérifie si les mots-clés de contexte requis sont présents"""
        if not context_keywords:
            return True
        
        # Extraire le contexte autour de la détection
        ctx_start = max(0, match_start - window_size)
        ctx_end = min(len(text), match_end + window_size)
        context = text[ctx_start:ctx_end].lower()
        
        # Vérifier si au moins un mot-clé est présent
        return any(keyword.lower() in context for keyword in context_keywords)

    def _is_valid_name(self, name: str) -> bool:
        """Vérifie si un nom détecté est valide"""
        words = name.lower().split()
        
        # Rejeter si contient des stopwords
        if any(word in self.french_stopwords for word in words):
            return False
        
        # Accepter uniquement si 2+ mots et chaque mot commence par une majuscule
        if len(words) >= 2 and all(w[0].isupper() for w in name.split()):
            return True
        
        return False

    def _detect_with_regex(self, text: str, detect_names: bool = False) -> List[Dict]:
        """Détection par expressions régulières"""
        detections = []
        
        for category_name, patterns in self.compiled_patterns.items():
            for pattern, metadata in patterns:
                # Skip les patterns de noms si detect_names est False
                if not detect_names and metadata["entity_type"] == "Nom complet":
                    continue
                
                for match in pattern.finditer(text):
                    matched_value = match.group(0)
                    
                    # Vérification de contexte si nécessaire
                    context_required = metadata.get("context_required", [])
                    if context_required:
                        if not self._check_context_required(text, match.start(), match.end(), context_required):
                            continue
                    
                    # Vérification spéciale pour les noms
                    if metadata["entity_type"] == "Nom complet" and not self._is_valid_name(matched_value):
                        continue
                    
                    # Filtrer les faux positifs pour identifiant fiscal
                    if metadata["entity_type"] == "Identifiant fiscal (IF)":
                        # Vérifier que ce n'est pas un numéro de téléphone
                        if matched_value.startswith(('06', '07', '05', '+212', '212')):
                            continue
                    
                    detection = {
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "value": matched_value,
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.9,  # Score plus élevé pour regex validées
                        "detection_method": "regex",
                        "context": self._get_context(text, match.start(), match.end())
                    }
                    detections.append(detection)
        
        return detections

    def _detect_with_keywords(self, text: str) -> List[Dict]:
        """Détection par mots-clés (acronymes uniquement)"""
        detections = []
        text_lower = text.lower()
        
        for keyword, metadata in self.keyword_matchers.items():
            # Recherche avec délimiteurs de mots
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, text_lower):
                pos = match.start()
                
                detection = {
                    "entity_type": metadata["entity_type"],
                    "category": metadata["category"],
                    "value": text[pos:pos + len(keyword)],
                    "start": pos,
                    "end": pos + len(keyword),
                    "sensitivity_level": metadata["sensitivity_level"],
                    "confidence_score": 0.75,
                    "detection_method": "keyword",
                    "context": self._get_context(text, pos, pos + len(keyword))
                }
                detections.append(detection)
        
        return detections

    def _merge_overlapping_detections(self, detections: List[Dict]) -> List[Dict]:
        """Fusionne les détections qui se chevauchent"""
        if not detections:
            return []
        
        # Trier par position de début puis par score décroissant
        sorted_detections = sorted(detections, key=lambda x: (x["start"], -x["confidence_score"]))
        merged = []
        
        for detection in sorted_detections:
            overlapping = False
            for i, existing in enumerate(merged):
                # Vérifier chevauchement
                if (detection["start"] < existing["end"] and detection["end"] > existing["start"]):
                    # Garder la détection avec le meilleur score
                    if detection["confidence_score"] > existing["confidence_score"]:
                        merged[i] = detection
                    overlapping = True
                    break
            
            if not overlapping:
                merged.append(detection)
        
        return sorted(merged, key=lambda x: x["start"])

    def analyze(self, text: str, language: str = "fr", 
                confidence_threshold: float = 0.5,
                detect_names: bool = False) -> List[Dict]:
        """Analyse le texte et détecte les données sensibles"""
        
        if not text or not text.strip():
            return []
        
        # Détection par regex
        regex_detections = self._detect_with_regex(text, detect_names=detect_names)
        
        # Détection par mots-clés (acronymes)
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
            placeholder = f"[{entity_type.upper().replace(' ', '_').replace('-', '_')}]"
            
            anonymized = anonymized[:start] + placeholder + anonymized[end:]
        
        return anonymized

# ====================================================================
# INITIALISATION DU MOTEUR
# ====================================================================

taxonomy_file = Path(__file__).parent / "taxonomie.json"
detection_engine = PIIDetectionEngine(taxonomy_path=str(taxonomy_file) if taxonomy_file.exists() else None)

# ====================================================================
# FASTAPI
# ====================================================================

app = FastAPI(
    title="Classification Engine API - Maroc",
    description="API de détection et classification de données personnelles et sensibles",
    version="2.0.0"
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
            confidence_threshold=request.confidence_threshold,
            detect_names=request.detect_names
        )
        
        # Anonymisation si demandée
        anonymized_text = None
        if request.anonymize and detections:
            anonymized_text = detection_engine.anonymize_text(request.text, detections)
            for det in detections:
                det["anonymized_value"] = f"[{det['entity_type'].upper().replace(' ', '_').replace('-', '_')}]"
        
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
        "version": "2.0.0",
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
    print("=" * 60)
    print("MOTEUR DE DÉTECTION DE DONNÉES SENSIBLES - MAROC v2.0")
    print("=" * 60)
    print(f"Patterns compilés: {sum(len(p) for p in detection_engine.compiled_patterns.values())}")
    print(f"Mots-clés: {len(detection_engine.keyword_matchers)}")
   
    print("=" * 60)
    print("\nDémarrage du serveur sur http://127.0.0.1:8001")

    print("=" * 60)

    uvicorn.run(app, host="127.0.0.1", port=8001)