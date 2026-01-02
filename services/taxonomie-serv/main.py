"""
Taxonomy Service - Tâche 2
Pure Moroccan PII/SPI Taxonomy with Regex Patterns

According to Cahier des Charges:
- Custom taxonomy for Moroccan PII/SPI
- Regex-based detection
- Arabic support
- MongoDB integration for taxonomy storage

Note: Presidio integration moved to presidio-serv
Note: ML classification moved to classification-serv
"""
import re
import json
import time
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import Sensitivity Calculator (Cahier Section 4.4)
from backend.sensitivity_calculator import SensitivityCalculator
from backend.pattern_loader import load_patterns_from_mongodb

# ====================================================================
# DATA MODELS
# ====================================================================

class SensitivityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Texte à analyser", min_length=1)
    language: str = Field(default="fr", description="Langue (fr/en/ar)")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    detect_names: bool = Field(default=True)
    domains: Optional[List[str]] = Field(default=None)

class DetectionResult(BaseModel):
    entity_type: str
    category: str
    domain: Optional[str] = None
    value: str
    start: int
    end: int
    sensitivity_level: str
    sensitivity_score: Optional[float] = None  # NEW: Cahier formula score
    sensitivity_breakdown: Optional[Dict] = None  # NEW: {legal, risk, impact}
    confidence_score: float
    detection_method: str = "regex"
    context: Optional[str] = None

class AnalyzeResponse(BaseModel):
    success: bool
    text_length: int
    detections_count: int
    detections: List[DetectionResult]
    summary: Dict[str, int]
    domains_summary: Dict[str, int]
    execution_time_ms: float

# ====================================================================
# MOROCCAN PATTERNS (CORE OF TÂCHE 2)
# ====================================================================

MOROCCAN_PATTERNS = {
    "CIN_MAROC": {
        "patterns": [r"\b[A-Z]{1,2}\d{5,8}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IDENTITE"
    },
    "CNSS": {
        "patterns": [r"\b\d{9,12}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "critical",
        "domain": "PROFESSIONNEL",
        "context_required": ["cnss", "sécurité sociale", "الضمان"]
    },
    "PHONE_MA": {
        "patterns": [
            r"(?:\+212|00212|0)[5-7]\d{8}",
            r"\+212[\s.-]?[5-7][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}"
        ],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "IBAN_MA": {
        "patterns": [r"\bMA\d{2}[A-Z0-9\s]{20,26}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER"
    },
    "EMAIL": {
        "patterns": [r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "MASSAR": {
        "patterns": [r"\b[A-Z]\d{9}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "EDUCATION",
        "context_required": ["massar", "élève", "scolaire"]
    },
    "PASSPORT_MA": {
        "patterns": [r"\b[A-Z]{1,2}\d{6,9}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IDENTITE",
        "context_required": ["passeport", "passport", "جواز"]
    },
    "DATE_NAISSANCE": {
        "patterns": [
            r"(?:0[1-9]|[12][0-9]|3[01])[-/](?:0[1-9]|1[0-2])[-/](?:19|20)\d{2}",
            r"(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12][0-9]|3[01])"
        ],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "IDENTITE"
    },
    "IMMATRICULATION_VEHICULE": {
        "patterns": [r"\d{1,6}[\s-]?[A-Zأ-ي][\s-]?\d{1,4}"],
        "category": "DONNEES_VEHICULE",
        "sensitivity": "medium",
        "domain": "VEHICULE"
    },
    "CARTE_SEJOUR": {
        "patterns": [r"\b[A-Z]{2}\d{6,10}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IMMIGRATION",
        "context_required": ["séjour", "residence", "إقامة"]
    },
    
    # ======= NEW PATTERNS (37 total) =======
    # Added per Cahier Section 4.8 - Target: 50+ types
    
    # === IDENTITY & HEALTH (10 more) ===
    "CARTE_RAMED": {
        "patterns": [r"\bRAMED\d{10}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "SANTE",
        "context_required": ["ramed", "santé", "الصحة"]
    },
    "NUMERO_AMO": {
        "patterns": [r"\b\d{13}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "SANTE",
        "context_required": ["amo", "assurance", "التأمين"]
    },
    "PERMIS_CONDUIRE": {
        "patterns": [r"\b[A-Z]\d{7}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "medium",
        "domain": "IDENTITE",
        "context_required": ["permis", "conduire", "رخصة"]
    },
    "NUMERO_DOSSIER_MEDICAL": {
        "patterns": [r"\bDM\d{8}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "critical",
        "domain": "SANTE"
    },
    "CARTE_ELECTORALE": {
        "patterns": [r"\bCE[A-Z]\d{7}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "medium",
        "domain": "POLITIQUE"
    },
    "NUMERO_MUTUELLE": {
        "patterns": [r"\bMUT\d{8,12}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "high",
        "domain": "SANTE"
    },
    "CARTE_HANDICAP": {
        "patterns": [r"\bCH\d{8}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "critical",
        "domain": "SANTE",
        "context_required": ["handicap", "invalidité"]
    },
    "NUMERO_PATIENT": {
        "patterns": [r"\bPAT\d{8,10}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "critical",
        "domain": "SANTE"
    },
    "CNE": {
        "patterns": [r"\b[A-Z]\d{9}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "EDUCATION",
        "context_required": ["cne", "étudiant", "طالب", "élève"]
    },
    "NUMERO_SECURITE_SOCIALE": {
        "patterns": [r"\b[12]\d{14}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "critical",
        "domain": "PROFESSIONNEL"
    },
    
    # === FINANCIAL (8 more) ===
    "RIB_MAROC": {
        "patterns": [r"\b\d{24}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER",
        "context_required": ["rib", "relevé", "bancaire"]
    },
    "SWIFT_CODE": {
        "patterns": [r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "high",
        "domain": "FINANCIER"
    },
    "CARTE_BANCAIRE": {
        "patterns": [r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER"
    },
    "CVV": {
        "patterns": [r"\b\d{3,4}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER",
        "context_required": ["cvv", "code", "sécurité"]
    },
    "NUMERO_FACTURE": {
        "patterns": [r"\bFAC\d{8}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "low",
        "domain": "COMMERCIAL"
    },
    "SALAIRE": {
        "patterns": [r"\d+\s?(?:DH|MAD|dirhams?)"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "PROFESSIONNEL",
        "context_required": ["salaire", "rémunération", "الأجر", "paie"]
    },
    "NUMERO_COMPTE_BANCAIRE": {
        "patterns": [r"\b\d{10,16}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER",
        "context_required": ["compte", "bancaire", "account"]
    },
    "MONTANT_TRANSACTION": {
        "patterns": [r"\b\d{1,}[.,]\d{2}\s?(?:DH|MAD)\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "medium",
        "domain": "FINANCIER"
    },
    
    # === CONTACT & ADDRESS (7 more) ===
    "PHONE_FIXE_MA": {
        "patterns": [r"\b05\d{8}\b"],
        "category": "COORDONNEES",
        "sensitivity": "medium",
        "domain": "CONTACT"
    },
    "FAX_MA": {
        "patterns": [r"\b(?:fax|télécopie)[:\s]*05\d{8}\b"],
        "category": "COORDONNEES",
        "sensitivity": "low",
        "domain": "CONTACT"
    },
    "ADRESSE_COMPLETE": {
        "patterns": [r"\b\d+,?\s+(?:rue|avenue|boulevard|av\.)\s+[\w\s]+,\s*\d{5}"],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "CODE_POSTAL_MA": {
        "patterns": [r"\b\d{5}\b"],
        "category": "COORDONNEES",
        "sensitivity": "low",
        "domain": "CONTACT",
        "context_required": ["code postal", "cp", "ville"]
    },
    "ADRESSE_IP": {
        "patterns": [r"\b(?:\d{1,3}\.){3}\d{1,3}\b"],
        "category": "DONNEES_TECHNIQUES",
        "sensitivity": "medium",
        "domain": "INFORMATIQUE"
    },
    "URL_PERSONNEL": {
        "patterns": [r"https?://[\w\.-]+\.[a-z]{2,}"],
        "category": "COORDONNEES",
        "sensitivity": "low",
        "domain": "CONTACT"
    },
    "EMAIL_PROFESSIONNEL": {
        "patterns": [r"[a-zA-Z0-9._%+-]+@(?:entreprise|company|corp|inc|org)\.(?:ma|com)"],
        "category": "COORDONNEES",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL"
    },
    
    # === PROFESSIONAL (6 more) ===
    "MATRICULE_EMPLOYEE": {
        "patterns": [r"\bEMP[A-Z]{2}\d{6}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL"
    },
    "CONTRAT_TRAVAIL_ID": {
        "patterns": [r"\bCT\d{8}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "high",
        "domain": "PROFESSIONNEL"
    },
    "NUMERO_BADGE": {
        "patterns": [r"\bBDG\d{6}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "low",
        "domain": "PROFESSIONNEL"
    },
    "ICE": {
        "patterns": [r"\b\d{15}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL",
        "context_required": ["ice", "entreprise", "société"]
    },
    "NUMERO_RC": {
        "patterns": [r"\bRC\d{6,8}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL",
        "context_required": ["rc", "registre", "commerce"]
    },
    "PATENTE": {
        "patterns": [r"\bPAT\d{8}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL",
        "context_required": ["patente", "taxe"]
    },
    
    # === EDUCATION (3 more) ===
    "DIPLOME_NUMERO": {
        "patterns": [r"\bDIP\d{8}\b"],
        "category": "DONNEES_EDUCATION",
        "sensitivity": "medium",
        "domain": "EDUCATION"
    },
    "NOTE_EXAMEN": {
        "patterns": [r"\b\d{1,2}[.,]\d{2}\s*/\s*20\b"],
        "category": "DONNEES_EDUCATION",
        "sensitivity": "medium",
        "domain": "EDUCATION"
    },
    "NUMERO_ETUDIANT": {
        "patterns": [r"\bETU\d{8}\b"],
        "category": "DONNEES_EDUCATION",
        "sensitivity": "medium",
        "domain": "EDUCATION"
    },
    
    # === BIOMETRIC & SENSITIVE (3 more) ===
    "PHOTO_HASH": {
        "patterns": [r"\bPH[A-F0-9]{64}\b"],
        "category": "DONNEES_BIOMETRIQUES",
        "sensitivity": "critical",
        "domain": "BIOMETRIQUE"
    },
    "EMPREINTE_DIGITALE_ID": {
        "patterns": [r"\bFP[A-F0-9]{32}\b"],
        "category": "DONNEES_BIOMETRIQUES",
        "sensitivity": "critical",
        "domain": "BIOMETRIQUE"
    },
    "NUMERO_DNA": {
        "patterns": [r"\bDNA[A-F0-9]{16}\b"],
        "category": "DONNEES_BIOMETRIQUES",
        "sensitivity": "critical",
        "domain": "BIOMETRIQUE"
    }
}

# Arabic patterns
ARABIC_PATTERNS = {
    "الرقم_الوطني": {
        "patterns": [r"رقم البطاقة[:\s]*[A-Za-z]{1,2}\d{5,8}"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IDENTITE"
    },
    "رقم_الهاتف": {
        "patterns": [r"الهاتف[:\s]*(?:\+212|00212|0)[5-7]\d{8}"],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "الحساب_البنكي": {
        "patterns": [r"(?:IBAN|الحساب البنكي)[:\s]*MA\d{2}[A-Z0-9\s]{20,26}"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER"
    }
}

# ====================================================================
# TAXONOMY ENGINE
# ====================================================================

class TaxonomyEngine:
    """Pure Regex-based Taxonomy Engine for Moroccan PII/SPI"""
    
    def __init__(self, domains_path: Optional[str] = None):
        self.domains_path = Path(domains_path) if domains_path else Path(__file__).parent / "taxonomie" / "domains"
        self.taxonomy = {"categories": [], "domains": {}}
        
        # Load custom taxonomy from JSON files
        self._load_from_files()
        
        # Initialize Sensitivity Calculator (Cahier Section 4.4)
        self.sensitivity_calc = SensitivityCalculator()
        
        # Try loading patterns from MongoDB
        print("\n" + "="*60)
        print("🗄️  MONGODB PATTERN LOADING")
        print("="*60)
        
        mongodb_patterns = load_patterns_from_mongodb()
        
        if mongodb_patterns and len(mongodb_patterns) >= 47:
            print(f"✅ Using MongoDB patterns ({len(mongodb_patterns)} loaded)")
            self.moroccan_patterns = mongodb_patterns
        else:
            print(f"⚠️  MongoDB load failed or incomplete, using hardcoded fallback")
            print(f"✅ Using hardcoded patterns ({len(self.moroccan_patterns)} patterns)")
        
        # Compile patterns (after potentially loading from MongoDB)
        self.compiled_patterns = self._compile_moroccan_patterns()
        self.compiled_arabic = self._compile_arabic_patterns()
        
        print(f"\n{'='*60}")
        print("🇲🇦 MOROCCAN TAXONOMY ENGINE - Tâche 2")
        print(f"{'='*60}")
        print(f"✅ Moroccan patterns: {len(self.compiled_patterns)}")
        print(f"✅ Arabic patterns: {len(self.compiled_arabic)}")
        print(f"✅ Custom domains: {len(self.taxonomy.get('domains', {}))}")
        print(f"{'='*60}\n")
    
    def _load_from_files(self):
        """Load custom taxonomy from domain JSON files"""
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
    
    def _compile_moroccan_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Compile Moroccan patterns"""
        compiled = {}
        for entity_type, config in MOROCCAN_PATTERNS.items():
            compiled[entity_type] = []
            for pattern_str in config.get("patterns", []):
                try:
                    compiled[entity_type].append((
                        re.compile(pattern_str, re.IGNORECASE | re.UNICODE),
                        {
                            "entity_type": entity_type,
                            "category": config["category"],
                            "domain": config.get("domain", ""),
                            "sensitivity_level": config["sensitivity"],
                            "context_required": config.get("context_required", [])
                        }
                    ))
                except re.error:
                    pass
        return compiled
    
    def _compile_arabic_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Compile Arabic patterns"""
        compiled = {}
        for entity_type, config in ARABIC_PATTERNS.items():
            compiled[entity_type] = []
            for pattern_str in config.get("patterns", []):
                try:
                    compiled[entity_type].append((
                        re.compile(pattern_str, re.UNICODE),
                        {
                            "entity_type": entity_type,
                            "category": config["category"],
                            "domain": config.get("domain", ""),
                            "sensitivity_level": config["sensitivity"],
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
    
    def analyze(self, text: str, language: str = "fr",
                confidence_threshold: float = 0.5,
                detect_names: bool = True,
                domains: Optional[List[str]] = None) -> List[Dict]:
        """Analyze text using Moroccan taxonomy"""
        
        if not text or not text.strip():
            return []
        
        detections = []
        
        # Moroccan patterns
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern, metadata in patterns:
                for match in pattern.finditer(text):
                    ctx_required = metadata.get("context_required", [])
                    if ctx_required and not self._check_context(text, match.start(), match.end(), ctx_required):
                        continue
                    
                    # Calculate sensitivity using Cahier formula (Section 4.4)
                    sensitivity = self.sensitivity_calc.calculate(metadata["entity_type"])
                    
                    detections.append({
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "domain": metadata.get("domain", ""),
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": sensitivity["level"],
                        "sensitivity_score": sensitivity["score"],
                        "sensitivity_breakdown": sensitivity["breakdown"],
                        "confidence_score": 0.9,
                        "detection_method": "regex",
                        "context": self._get_context(text, match.start(), match.end())
                    })
        
        # Arabic patterns (if Arabic text detected)
        if any('\u0600' <= char <= '\u06FF' for char in text):
            for entity_type, patterns in self.compiled_arabic.items():
                for pattern, metadata in patterns:
                    for match in pattern.finditer(text):
                        # Calculate sensitivity using Cahier formula
                        sensitivity = self.sensitivity_calc.calculate(metadata["entity_type"])
                        
                        detections.append({
                            "entity_type": metadata["entity_type"],
                            "category": metadata["category"],
                            "domain": metadata.get("domain", ""),
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end(),
                            "sensitivity_level": sensitivity["level"],
                            "sensitivity_score": sensitivity["score"],
                            "sensitivity_breakdown": sensitivity["breakdown"],
                            "confidence_score": 0.85,
                            "detection_method": "regex_arabic",
                            "context": self._get_context(text, match.start(), match.end())
                        })
        
        # Also check custom taxonomy from files
        for category in self.taxonomy.get("categories", []):
            for subclass in category.get("subclasses", []):
                for pattern_str in subclass.get("regex_patterns", []):
                    try:
                        pattern = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
                        for match in pattern.finditer(text):
                            detections.append({
                                "entity_type": subclass.get("name", "Unknown"),
                                "category": category.get("class", ""),
                                "domain": category.get("domain_name", ""),
                                "value": match.group(0),
                                "start": match.start(),
                                "end": match.end(),
                                "sensitivity_level": subclass.get("sensitivity_level", "unknown"),
                                "confidence_score": 0.85,
                                "detection_method": "regex",
                                "context": self._get_context(text, match.start(), match.end())
                            })
                    except re.error:
                        pass
        
        # Filter by threshold and domains
        detections = [d for d in detections if d["confidence_score"] >= confidence_threshold]
        if domains:
            detections = [d for d in detections 
                         if any(dom.lower() in d.get("domain", "").lower() for dom in domains)]
        
        # Remove duplicates based on position
        seen = set()
        unique = []
        for d in detections:
            key = (d["start"], d["end"])
            if key not in seen:
                seen.add(key)
                unique.append(d)
        
        return sorted(unique, key=lambda x: x["start"])
    
    def get_domains(self) -> List[Dict]:
        """Get available domains"""
        return [
            {"domain_id": did, "domain_name": info.get("name", ""), "metadata": info.get("metadata", {})}
            for did, info in self.taxonomy.get("domains", {}).items()
        ]

# Initialize engine
domains_dir = Path(__file__).parent / "backend" / "taxonomie" / "domains"
taxonomy_engine = TaxonomyEngine(domains_path=str(domains_dir))

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Taxonomy Service",
    description="Moroccan PII/SPI Taxonomy - Tâche 2",
    version="2.0.0"
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
    return {"service": "Taxonomy Service", "status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "patterns": len(taxonomy_engine.compiled_patterns),
        "arabic_patterns": len(taxonomy_engine.compiled_arabic),
        "domains": len(taxonomy_engine.taxonomy.get("domains", {}))
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text with Moroccan taxonomy"""
    start_time = time.time()
    
    try:
        detections = taxonomy_engine.analyze(
            text=request.text,
            language=request.language,
            confidence_threshold=request.confidence_threshold,
            detect_names=request.detect_names,
            domains=request.domains
        )
        
        # Build summaries
        summary = {}
        domains_summary = {}
        for det in detections:
            summary[det["category"]] = summary.get(det["category"], 0) + 1
            domains_summary[det.get("domain", "OTHER")] = domains_summary.get(det.get("domain", "OTHER"), 0) + 1
        
        execution_time = (time.time() - start_time) * 1000
        
        return AnalyzeResponse(
            success=True,
            text_length=len(request.text),
            detections_count=len(detections),
            detections=[DetectionResult(**d) for d in detections],
            summary=summary,
            domains_summary=domains_summary,
            execution_time_ms=round(execution_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/domains")
def get_domains():
    """Get available taxonomy domains"""
    return {"domains": taxonomy_engine.get_domains()}

@app.get("/patterns")
def get_patterns():
    """Get available pattern types"""
    return {
        "moroccan": list(MOROCCAN_PATTERNS.keys()),
        "arabic": list(ARABIC_PATTERNS.keys())
    }

@app.post("/sync-atlas")
async def sync_taxonomy_to_atlas():
    """
    Sync taxonomy to Apache Atlas (Cahier Section 4.6)
    Creates entity type definitions for all 47+ Moroccan PII/SPI patterns
    """
    try:
        # Import Atlas client
        import sys
        sys.path.insert(0, '../common')
        from atlas_client import AtlasClient
        
        atlas = AtlasClient()
        
        if atlas.mock_mode:
            return {
                "warning": "Atlas in MOCK mode. Set MOCK_GOVERNANCE=false to sync to real Atlas",
                "mock_mode": True,
                "total_patterns": len(MOROCCAN_PATTERNS) + len(ARABIC_PATTERNS)
            }
        
        synced = 0
        errors = []
        
        # Sync all Moroccan patterns as entity types
        for entity_type, config in MOROCCAN_PATTERNS.items():
            try:
                # Calculate sensitivity
                sensitivity = taxonomy_engine.sensitivity_calc.calculate(entity_type)
                
                # Create entity definition
                entity_def = {
                    "entityDefs": [{
                        "name": f"pii_{entity_type.lower()}",
                        "superTypes": ["DataSet"],
                        "description": f"Moroccan PII/SPI: {entity_type}",
                        "attributeDefs": [
                            {"name": "sensitivity_level", "typeName": "string"},
                            {"name": "sensitivity_score", "typeName": "float"},
                            {"name": "category", "typeName": "string"},
                            {"name": "domain", "typeName": "string"},
                            {
                                "name": "legal_score",
                                "typeName": "float",
                                "defaultValue": str(sensitivity["breakdown"]["legal"])
                            },
                            {
                                "name": "risk_score",
                                "typeName": "float",
                                "defaultValue": str(sensitivity["breakdown"]["risk"])
                            },
                            {
                                "name": "impact_score",
                                "typeName": "float",
                                "defaultValue": str(sensitivity["breakdown"]["impact"])
                            }
                        ],
                        "options": {
                            "sensitivity": sensitivity["level"],
                            "category": config["category"],
                            "domain": config.get("domain", ""),
                            "cahier_section": "4.8"
                        }
                    }]
                }
                
                # Submit to Atlas
                result = atlas._post("/types/typedefs", entity_def)
                if result:
                    synced += 1
            except Exception as e:
                errors.append({"entity": entity_type, "error": str(e)})
        
        # Sync Arabic patterns
        for entity_type, config in ARABIC_PATTERNS.items():
            try:
                sensitivity = taxonomy_engine.sensitivity_calc.calculate(entity_type)
                
                entity_def = {
                    "entityDefs": [{
                        "name": f"pii_arabic_{entity_type.lower()}",
                        "superTypes": ["DataSet"],
                        "description": f"Arabic PII: {entity_type}",
                        "attributeDefs": [
                            {"name": "sensitivity_level", "typeName": "string"},
                            {"name": "category", "typeName": "string"}
                        ],
                        "options": {
                            "sensitivity": sensitivity["level"],
                            "language": "ar"
                        }
                    }]
                }
                
                result = atlas._post("/types/typedefs", entity_def)
                if result:
                    synced += 1
            except Exception as e:
                errors.append({"entity": entity_type, "error": str(e)})
        
        total = len(MOROCCAN_PATTERNS) + len(ARABIC_PATTERNS)
        
        return {
            "message": f"Synced {synced}/{total} entities to Apache Atlas",
            "synced": synced,
            "total": total,
            "errors": errors,
            "mock_mode": False
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Atlas client not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Atlas sync failed: {str(e)}"
        )

# ====================================================================
# MONGODB MANAGEMENT ENDPOINTS
# ====================================================================

@app.get("/patterns/mongodb/status")
def get_mongodb_status():
    """Check MongoDB connection and pattern status"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
        from mongodb_client import test_connection
        from backend.pattern_loader import get_pattern_count
        
        if not test_connection():
            return {
                "status": "disconnected",
                "using": "hardcoded_fallback",
                "pattern_count": len(MOROCCAN_PATTERNS),
                "database": "N/A"
            }
        
        pattern_count = get_pattern_count()
        
        return {
            "status": "connected",
            "using": "mongodb" if pattern_count >= 47 else "hardcoded",
            "pattern_count": pattern_count,
            "database": "DataGovDB",
            "collection": "taxonomies",
            "atlas_cloud": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "using": "hardcoded_fallback"
        }

@app.post("/patterns/reload")
def reload_patterns_from_db():
    """Reload patterns from MongoDB without restarting service"""
    global taxonomy_engine
    
    try:
        from backend.pattern_loader import load_patterns_from_mongodb
        
        new_patterns = load_patterns_from_mongodb()
        
        if new_patterns and len(new_patterns) >= 47:
            # Update engine patterns
            taxonomy_engine.moroccan_patterns = new_patterns
            # Recompile patterns
            taxonomy_engine.compiled_patterns = taxonomy_engine._compile_moroccan_patterns()
            
            return {
                "success": True,
                "message": f"Reloaded {len(new_patterns)} patterns from MongoDB",
                "pattern_count": len(new_patterns),
                "source": "mongodb"
            }
        else:
            return {
                "success": False,
                "message": "Failed to reload from MongoDB, keeping existing patterns",
                "pattern_count": len(taxonomy_engine.moroccan_patterns),
                "source": "unchanged"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Pattern reload failed"
        }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🇲🇦 TAXONOMY SERVICE - Tâche 2")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
