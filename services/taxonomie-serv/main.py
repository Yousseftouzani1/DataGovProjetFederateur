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
        
        # Compile patterns
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
                    
                    detections.append({
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "domain": metadata.get("domain", ""),
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.9,
                        "detection_method": "regex",
                        "context": self._get_context(text, match.start(), match.end())
                    })
        
        # Arabic patterns (if Arabic text detected)
        if any('\u0600' <= char <= '\u06FF' for char in text):
            for entity_type, patterns in self.compiled_arabic.items():
                for pattern, metadata in patterns:
                    for match in pattern.finditer(text):
                        detections.append({
                            "entity_type": metadata["entity_type"],
                            "category": metadata["category"],
                            "domain": metadata.get("domain", ""),
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end(),
                            "sensitivity_level": metadata["sensitivity_level"],
                            "confidence_score": 0.85,
                            "detection_method": "regex",
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

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🇲🇦 TAXONOMY SERVICE - Tâche 2")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
