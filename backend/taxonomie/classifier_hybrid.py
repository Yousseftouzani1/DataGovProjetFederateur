"""
Hybrid PII/SPI Detection Engine
Combines:
- Custom Moroccan taxonomy patterns (CIN, CNSS, Massar, etc.)
- Microsoft Presidio for international PII (NER-based)
- Arabic language support
"""
import re
import json
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ====================================================================
# CONFIGURATION
# ====================================================================

# Try to import Presidio (optional)
PRESIDIO_AVAILABLE = False
try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    print("⚠️ Presidio not installed. Using regex-only mode.")
    print("   To enable Presidio: pip install presidio-analyzer presidio-anonymizer spacy")

# ====================================================================
# MODÈLES DE DONNÉES
# ====================================================================

class SensitivityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Texte à analyser", min_length=1)
    language: str = Field(default="fr", description="Langue du texte (fr/en/ar)")
    anonymize: bool = Field(default=False, description="Anonymiser les résultats")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    detect_names: bool = Field(default=True, description="Activer la détection de noms")
    use_presidio: bool = Field(default=True, description="Utiliser Presidio (si disponible)")
    domains: Optional[List[str]] = Field(default=None, description="Filtrer par domaines")

class DetectionResult(BaseModel):
    entity_type: str
    category: str
    domain: Optional[str] = None
    value: str
    start: int
    end: int
    sensitivity_level: str
    confidence_score: float
    detection_method: str
    source: str = "custom"  # "custom", "presidio", "arabic"
    context: Optional[str] = None
    anonymized_value: Optional[str] = None

class AnalyzeResponse(BaseModel):
    success: bool
    text_length: int
    detections_count: int
    detections: List[DetectionResult]
    summary: Dict[str, int]
    domains_summary: Dict[str, int]
    sources_summary: Dict[str, int]
    execution_time_ms: float
    anonymized_text: Optional[str] = None
    presidio_available: bool = False
    engine_mode: str = "regex"

# ====================================================================
# ARABIC PATTERNS
# ====================================================================

ARABIC_PATTERNS = {
    "الرقم الوطني": {  # National ID
        "patterns": [
            r"[A-Za-z]{1,2}\d{5,8}",
            r"رقم البطاقة[:\s]*[A-Za-z]{1,2}\d{5,8}"
        ],
        "category": "هوية شخصية",
        "category_en": "PERSONAL_IDENTITY",
        "sensitivity": "critical",
        "type": "SPI"
    },
    "رقم الهاتف": {  # Phone number
        "patterns": [
            r"(?:\+212|00212|0)[5-7]\d{8}",
            r"الهاتف[:\s]*(?:\+212|00212|0)[5-7]\d{8}"
        ],
        "category": "معلومات الاتصال",
        "category_en": "CONTACT_INFO",
        "sensitivity": "high",
        "type": "PII"
    },
    "البريد الإلكتروني": {  # Email
        "patterns": [
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        ],
        "category": "معلومات الاتصال",
        "category_en": "CONTACT_INFO",
        "sensitivity": "high",
        "type": "PII"
    },
    "رقم الضمان الاجتماعي": {  # CNSS
        "patterns": [
            r"\d{9,12}",
            r"(?:CNSS|الصندوق الوطني)[:\s]*\d{9,12}"
        ],
        "category": "معلومات مهنية",
        "category_en": "PROFESSIONAL_INFO",
        "sensitivity": "critical",
        "type": "SPI",
        "context_required": ["cnss", "ضمان", "اجتماعي", "صندوق"]
    },
    "رقم الحساب البنكي": {  # Bank account
        "patterns": [
            r"MA\d{2}[A-Z0-9]{22,24}",
            r"(?:IBAN|الحساب البنكي)[:\s]*MA\d{2}[A-Z0-9]{22,24}"
        ],
        "category": "معلومات مالية",
        "category_en": "FINANCIAL_INFO",
        "sensitivity": "critical",
        "type": "SPI"
    },
    "تاريخ الميلاد": {  # Date of birth
        "patterns": [
            r"(?:0[1-9]|[12][0-9]|3[01])[-/](?:0[1-9]|1[0-2])[-/](?:19|20)\d{2}",
            r"(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12][0-9]|3[01])"
        ],
        "category": "هوية شخصية",
        "category_en": "PERSONAL_IDENTITY",
        "sensitivity": "high",
        "type": "PII"
    },
    "الاسم الكامل": {  # Full name (Arabic)
        "patterns": [
            r"[\u0600-\u06FF]+\s+[\u0600-\u06FF]+(?:\s+[\u0600-\u06FF]+)?",
        ],
        "category": "هوية شخصية",
        "category_en": "PERSONAL_IDENTITY",
        "sensitivity": "high",
        "type": "PII",
        "context_required": ["اسم", "السيد", "السيدة", "الأستاذ"]
    },
    "رقم جواز السفر": {  # Passport
        "patterns": [
            r"[A-Z]{1,2}\d{6,9}",
            r"(?:جواز|passport)[:\s]*[A-Z]{1,2}\d{6,9}"
        ],
        "category": "هوية شخصية",
        "category_en": "PERSONAL_IDENTITY",
        "sensitivity": "critical",
        "type": "SPI"
    },
    "العنوان": {  # Address
        "patterns": [
            r"\d+[,\s]+[\u0600-\u06FF\s]+[,\s]+[\u0600-\u06FF\s]+"
        ],
        "category": "معلومات الاتصال",
        "category_en": "CONTACT_INFO",
        "sensitivity": "medium",
        "type": "PII"
    },
    "رقم السيارة": {  # License plate
        "patterns": [
            r"\d{1,6}\s?[\u0600-\u06FF]\s?\d{1,4}",
            r"WW\s?\d{1,6}"
        ],
        "category": "معلومات المركبات",
        "category_en": "VEHICLE_INFO",
        "sensitivity": "medium",
        "type": "PII"
    }
}

# ====================================================================
# PRESIDIO ENTITY MAPPING
# ====================================================================

PRESIDIO_ENTITY_MAP = {
    "PERSON": {"sensitivity": "high", "category": "IDENTITE_PERSONNELLE", "domain": "IDENTITE"},
    "EMAIL_ADDRESS": {"sensitivity": "high", "category": "COORDONNEES", "domain": "CONTACT"},
    "PHONE_NUMBER": {"sensitivity": "high", "category": "COORDONNEES", "domain": "CONTACT"},
    "CREDIT_CARD": {"sensitivity": "critical", "category": "DONNEES_FINANCIERES", "domain": "FINANCIER"},
    "IBAN_CODE": {"sensitivity": "critical", "category": "DONNEES_FINANCIERES", "domain": "FINANCIER"},
    "DATE_TIME": {"sensitivity": "medium", "category": "IDENTITE_PERSONNELLE", "domain": "IDENTITE"},
    "LOCATION": {"sensitivity": "medium", "category": "COORDONNEES", "domain": "CONTACT"},
    "NRP": {"sensitivity": "critical", "category": "IDENTITE_PERSONNELLE", "domain": "IDENTITE"},
    "MEDICAL_LICENSE": {"sensitivity": "high", "category": "DONNEES_MEDICALES", "domain": "MEDICAL"},
    "URL": {"sensitivity": "low", "category": "COORDONNEES", "domain": "CONTACT"},
    "IP_ADDRESS": {"sensitivity": "medium", "category": "DONNEES_TECHNIQUES", "domain": "TECHNIQUE"},
    "US_SSN": {"sensitivity": "critical", "category": "IDENTITE_PERSONNELLE", "domain": "IDENTITE"},
    "US_PASSPORT": {"sensitivity": "critical", "category": "IDENTITE_PERSONNELLE", "domain": "IDENTITE"},
    "UK_NHS": {"sensitivity": "critical", "category": "DONNEES_MEDICALES", "domain": "MEDICAL"},
}

# ====================================================================
# HYBRID DETECTION ENGINE
# ====================================================================

class HybridDetectionEngine:
    def __init__(self, domains_path: Optional[str] = None):
        """Initialize hybrid engine with custom patterns, Presidio, and Arabic support"""
        self.domains_path = Path(domains_path) if domains_path else Path(__file__).parent / "domains"
        self.taxonomy = {"categories": [], "domains": {}}
        
        # Load custom Moroccan taxonomy
        self._load_from_files()
        self.compiled_patterns = self._compile_patterns()
        self.keyword_matchers = self._build_keyword_matchers()
        
        # Compile Arabic patterns
        self.arabic_patterns = self._compile_arabic_patterns()
        
        # Initialize Presidio if available
        self.presidio_analyzer = None
        self.presidio_anonymizer = None
        if PRESIDIO_AVAILABLE:
            self._init_presidio()
        
        print(f"\n{'='*60}")
        print("🚀 HYBRID PII/SPI DETECTION ENGINE")
        print(f"{'='*60}")
        print(f"✅ Custom Moroccan patterns: {sum(len(p) for p in self.compiled_patterns.values())}")
        print(f"✅ Keywords: {len(self.keyword_matchers)}")
        print(f"✅ Arabic patterns: {len(self.arabic_patterns)}")
        print(f"{'✅' if PRESIDIO_AVAILABLE else '❌'} Presidio NER: {'Enabled' if PRESIDIO_AVAILABLE else 'Disabled'}")
        print(f"{'='*60}\n")

    def _init_presidio(self):
        """Initialize Presidio analyzer with French support"""
        try:
            # Create NLP engine configuration
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "en", "model_name": "en_core_web_sm"},
                    {"lang_code": "fr", "model_name": "fr_core_news_sm"},
                ]
            }
            
            try:
                provider = NlpEngineProvider(nlp_configuration=configuration)
                nlp_engine = provider.create_engine()
                self.presidio_analyzer = AnalyzerEngine(
                    nlp_engine=nlp_engine,
                    supported_languages=["en", "fr"]
                )
            except Exception:
                # Fallback to default English-only
                self.presidio_analyzer = AnalyzerEngine()
            
            self.presidio_anonymizer = AnonymizerEngine()
            print("  ✅ Presidio initialized successfully")
        except Exception as e:
            print(f"  ⚠️ Presidio initialization failed: {e}")
            self.presidio_analyzer = None

    def _load_from_files(self):
        """Load custom Moroccan taxonomies"""
        if not self.domains_path.exists():
            return
        
        for filepath in self.domains_path.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    domain_tax = json.load(f)
                
                domain_id = domain_tax.get("metadata", {}).get("domain_id", filepath.stem)
                domain_name = domain_tax.get("metadata", {}).get("domain_name", filepath.stem)
                
                self.taxonomy["domains"][domain_id] = {
                    "name": domain_name,
                    "metadata": domain_tax.get("metadata", {})
                }
                
                for category in domain_tax.get("categories", []):
                    category["domain_id"] = domain_id
                    category["domain_name"] = domain_name
                    self.taxonomy["categories"].append(category)
                    
            except Exception as e:
                print(f"  ⚠️ Error loading {filepath.name}: {e}")

    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Compile custom Moroccan patterns"""
        compiled = {}
        for category in self.taxonomy.get("categories", []):
            category_name = category.get("class", "UNKNOWN")
            if category_name not in compiled:
                compiled[category_name] = []
            
            for subclass in category.get("subclasses", []):
                for pattern_str in subclass.get("regex_patterns", []):
                    try:
                        compiled[category_name].append((
                            re.compile(pattern_str, re.IGNORECASE | re.UNICODE),
                            {
                                "entity_type": subclass.get("name", "Unknown"),
                                "category": category_name,
                                "domain_name": category.get("domain_name", ""),
                                "sensitivity_level": subclass.get("sensitivity_level", "unknown"),
                                "context_required": subclass.get("context_required", [])
                            }
                        ))
                    except re.error:
                        pass
        return compiled

    def _build_keyword_matchers(self) -> Dict[str, Dict]:
        """Build keyword matchers"""
        matchers = {}
        for category in self.taxonomy.get("categories", []):
            for subclass in category.get("subclasses", []):
                for keyword in subclass.get("acronyms_fr", []) + subclass.get("acronyms_en", []):
                    if keyword and len(keyword) > 1:
                        matchers[keyword.lower()] = {
                            "entity_type": subclass.get("name", ""),
                            "category": category.get("class", ""),
                            "domain_name": category.get("domain_name", ""),
                            "sensitivity_level": subclass.get("sensitivity_level", "unknown")
                        }
        return matchers

    def _compile_arabic_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Compile Arabic patterns"""
        compiled = {}
        for entity_name, config in ARABIC_PATTERNS.items():
            compiled[entity_name] = []
            for pattern_str in config.get("patterns", []):
                try:
                    compiled[entity_name].append((
                        re.compile(pattern_str, re.UNICODE),
                        {
                            "entity_type": entity_name,
                            "entity_type_en": config.get("category_en", entity_name),
                            "category": config.get("category", ""),
                            "category_en": config.get("category_en", ""),
                            "sensitivity_level": config.get("sensitivity", "medium"),
                            "context_required": config.get("context_required", [])
                        }
                    ))
                except re.error:
                    pass
        return compiled

    def _get_context(self, text: str, start: int, end: int, size: int = 30) -> str:
        """Extract context around detection"""
        ctx_start = max(0, start - size)
        ctx_end = min(len(text), end + size)
        context = text[ctx_start:ctx_end]
        if ctx_start > 0:
            context = "..." + context
        if ctx_end < len(text):
            context = context + "..."
        return context

    def _check_context(self, text: str, start: int, end: int, keywords: List[str]) -> bool:
        """Check if context keywords are present"""
        if not keywords:
            return True
        ctx = text[max(0, start-50):min(len(text), end+50)].lower()
        return any(kw.lower() in ctx for kw in keywords)

    def _detect_custom(self, text: str, detect_names: bool = True) -> List[Dict]:
        """Detect using custom Moroccan patterns"""
        detections = []
        
        for category_name, patterns in self.compiled_patterns.items():
            for pattern, metadata in patterns:
                if not detect_names and "Nom" in metadata.get("entity_type", ""):
                    continue
                
                for match in pattern.finditer(text):
                    ctx_required = metadata.get("context_required", [])
                    if ctx_required and not self._check_context(text, match.start(), match.end(), ctx_required):
                        continue
                    
                    detections.append({
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "domain": metadata.get("domain_name", ""),
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.9,
                        "detection_method": "regex",
                        "source": "custom",
                        "context": self._get_context(text, match.start(), match.end())
                    })
        
        return detections

    def _detect_arabic(self, text: str) -> List[Dict]:
        """Detect using Arabic patterns"""
        detections = []
        
        # Check if text contains Arabic characters
        if not any('\u0600' <= char <= '\u06FF' for char in text):
            return detections
        
        for entity_name, patterns in self.arabic_patterns.items():
            for pattern, metadata in patterns:
                for match in pattern.finditer(text):
                    ctx_required = metadata.get("context_required", [])
                    if ctx_required and not self._check_context(text, match.start(), match.end(), ctx_required):
                        continue
                    
                    detections.append({
                        "entity_type": entity_name,
                        "entity_type_en": metadata.get("entity_type_en", entity_name),
                        "category": metadata.get("category_en", metadata["category"]),
                        "domain": metadata.get("category_en", "").split("_")[0] if metadata.get("category_en") else "",
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.85,
                        "detection_method": "regex",
                        "source": "arabic",
                        "context": self._get_context(text, match.start(), match.end())
                    })
        
        return detections

    def _detect_presidio(self, text: str, language: str = "en") -> List[Dict]:
        """Detect using Presidio NER"""
        if not self.presidio_analyzer:
            return []
        
        detections = []
        try:
            lang = "fr" if language in ["fr", "ar"] else "en"
            results = self.presidio_analyzer.analyze(text=text, language=lang)
            
            for result in results:
                entity_info = PRESIDIO_ENTITY_MAP.get(result.entity_type, {
                    "sensitivity": "medium",
                    "category": "OTHER",
                    "domain": "OTHER"
                })
                
                detections.append({
                    "entity_type": result.entity_type,
                    "category": entity_info["category"],
                    "domain": entity_info["domain"],
                    "value": text[result.start:result.end],
                    "start": result.start,
                    "end": result.end,
                    "sensitivity_level": entity_info["sensitivity"],
                    "confidence_score": result.score,
                    "detection_method": "ner",
                    "source": "presidio",
                    "context": self._get_context(text, result.start, result.end)
                })
        except Exception as e:
            print(f"Presidio error: {e}")
        
        return detections

    def _merge_detections(self, detections: List[Dict]) -> List[Dict]:
        """Merge overlapping detections, prioritizing custom over Presidio"""
        if not detections:
            return []
        
        # Sort by start position and confidence
        sorted_dets = sorted(detections, key=lambda x: (x["start"], -x["confidence_score"]))
        merged = []
        
        for det in sorted_dets:
            overlap = False
            for i, existing in enumerate(merged):
                if det["start"] < existing["end"] and det["end"] > existing["start"]:
                    # Custom patterns take priority
                    if det["source"] == "custom" and existing["source"] != "custom":
                        merged[i] = det
                    elif det["confidence_score"] > existing["confidence_score"]:
                        merged[i] = det
                    overlap = True
                    break
            
            if not overlap:
                merged.append(det)
        
        return sorted(merged, key=lambda x: x["start"])

    def analyze(self, text: str, language: str = "fr", 
                confidence_threshold: float = 0.5,
                detect_names: bool = True,
                use_presidio: bool = True,
                domains: Optional[List[str]] = None) -> List[Dict]:
        """Analyze text using all detection methods"""
        
        if not text or not text.strip():
            return []
        
        all_detections = []
        
        # 1. Custom Moroccan patterns (always)
        custom_dets = self._detect_custom(text, detect_names=detect_names)
        all_detections.extend(custom_dets)
        
        # 2. Arabic patterns (if Arabic text detected)
        arabic_dets = self._detect_arabic(text)
        all_detections.extend(arabic_dets)
        
        # 3. Presidio NER (if enabled and available)
        if use_presidio and PRESIDIO_AVAILABLE:
            presidio_dets = self._detect_presidio(text, language)
            all_detections.extend(presidio_dets)
        
        # Filter by confidence
        all_detections = [d for d in all_detections if d["confidence_score"] >= confidence_threshold]
        
        # Filter by domain if specified
        if domains:
            all_detections = [d for d in all_detections 
                           if any(dom.lower() in d.get("domain", "").lower() for dom in domains)]
        
        # Merge overlapping
        merged = self._merge_detections(all_detections)
        
        return merged

    def anonymize_text(self, text: str, detections: List[Dict]) -> str:
        """Anonymize detected values"""
        if not detections:
            return text
        
        sorted_dets = sorted(detections, key=lambda x: x["start"], reverse=True)
        anonymized = text
        
        for det in sorted_dets:
            entity = det["entity_type"].upper().replace(" ", "_").replace("-", "_")
            placeholder = f"[{entity}]"
            anonymized = anonymized[:det["start"]] + placeholder + anonymized[det["end"]:]
        
        return anonymized

    def get_domains(self) -> List[Dict]:
        """Get available domains"""
        return [
            {"domain_id": did, "domain_name": info.get("name", ""), "metadata": info.get("metadata", {})}
            for did, info in self.taxonomy.get("domains", {}).items()
        ]

# ====================================================================
# INITIALIZE ENGINE
# ====================================================================

domains_dir = Path(__file__).parent / "domains"
detection_engine = HybridDetectionEngine(domains_path=str(domains_dir))

# ====================================================================
# FASTAPI APPLICATION
# ====================================================================

app = FastAPI(
    title="Hybrid PII/SPI Detection API",
    description="Détection hybride: Taxonomie Marocaine + Presidio NER + Arabe",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text with hybrid detection"""
    start_time = time.time()
    
    try:
        detections = detection_engine.analyze(
            text=request.text,
            language=request.language,
            confidence_threshold=request.confidence_threshold,
            detect_names=request.detect_names,
            use_presidio=request.use_presidio,
            domains=request.domains
        )
        
        anonymized_text = None
        if request.anonymize and detections:
            anonymized_text = detection_engine.anonymize_text(request.text, detections)
            for det in detections:
                det["anonymized_value"] = f"[{det['entity_type'].upper().replace(' ', '_')}]"
        
        # Summaries
        summary = {}
        domains_summary = {}
        sources_summary = {}
        
        for det in detections:
            summary[det["category"]] = summary.get(det["category"], 0) + 1
            domains_summary[det.get("domain", "OTHER")] = domains_summary.get(det.get("domain", "OTHER"), 0) + 1
            sources_summary[det.get("source", "unknown")] = sources_summary.get(det.get("source", "unknown"), 0) + 1
        
        execution_time = (time.time() - start_time) * 1000
        
        # Determine engine mode
        engine_mode = "hybrid" if PRESIDIO_AVAILABLE and request.use_presidio else "regex"
        
        return AnalyzeResponse(
            success=True,
            text_length=len(request.text),
            detections_count=len(detections),
            detections=[DetectionResult(**d) for d in detections],
            summary=summary,
            domains_summary=domains_summary,
            sources_summary=sources_summary,
            execution_time_ms=round(execution_time, 2),
            anonymized_text=anonymized_text,
            presidio_available=PRESIDIO_AVAILABLE,
            engine_mode=engine_mode
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": "4.0.0 (Hybrid)",
        "presidio_available": PRESIDIO_AVAILABLE,
        "domains_count": len(detection_engine.taxonomy.get("domains", {})),
        "custom_patterns": sum(len(p) for p in detection_engine.compiled_patterns.values()),
        "arabic_patterns": len(detection_engine.arabic_patterns),
        "languages": ["fr", "en", "ar"]
    }

@app.get("/domains")
async def get_domains():
    """Get available domains"""
    return {"domains": detection_engine.get_domains()}

@app.get("/statistics")
async def get_statistics():
    """Get engine statistics"""
    return {
        "engine": "hybrid",
        "presidio_enabled": PRESIDIO_AVAILABLE,
        "custom_patterns": sum(len(p) for p in detection_engine.compiled_patterns.values()),
        "keywords": len(detection_engine.keyword_matchers),
        "arabic_patterns": sum(len(p) for p in detection_engine.arabic_patterns.values()),
        "domains": len(detection_engine.taxonomy.get("domains", {})),
        "languages_supported": ["fr", "en", "ar"]
    }

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 HYBRID PII/SPI DETECTION ENGINE v4.0")
    print("="*60)
    print("Démarrage du serveur sur http://127.0.0.1:8001")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
