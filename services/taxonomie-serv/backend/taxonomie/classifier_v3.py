"""
PII/SPI Detection Engine - Domain-Based Version
Loads taxonomies from domain JSON files or MongoDB
Compatible with Manal's original structure
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
    detect_names: bool = Field(default=False, description="Activer la détection de noms")
    domains: Optional[List[str]] = Field(default=None, description="Filtrer par domaines (ex: ['medical', 'financier'])")

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
    context: Optional[str] = None
    anonymized_value: Optional[str] = None

class AnalyzeResponse(BaseModel):
    success: bool
    text_length: int
    detections_count: int
    detections: List[DetectionResult]
    summary: Dict[str, int]
    domains_summary: Dict[str, int]
    execution_time_ms: float
    anonymized_text: Optional[str] = None

# ====================================================================
# CLASSE PRINCIPALE DE DÉTECTION
# ====================================================================

class PIIDetectionEngine:
    def __init__(self, domains_path: Optional[str] = None, use_mongodb: bool = False):
        """Initialise le moteur avec les taxonomies par domaine"""
        self.domains_path = Path(domains_path) if domains_path else Path(__file__).parent / "domains"
        self.use_mongodb = use_mongodb
        self.taxonomy = {"categories": [], "domains": {}}
        
        # Load taxonomies
        if use_mongodb:
            self._load_from_mongodb()
        else:
            self._load_from_files()
        
        self.compiled_patterns = self._compile_patterns()
        self.keyword_matchers = self._build_keyword_matchers()
        
        # French stopwords for filtering
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
        
        print(f"✅ Engine initialized with {len(self.taxonomy['domains'])} domains")
        print(f"   Patterns: {sum(len(p) for p in self.compiled_patterns.values())}")
        print(f"   Keywords: {len(self.keyword_matchers)}")

    def _load_from_files(self):
        """Load taxonomies from domain JSON files"""
        if not self.domains_path.exists():
            print(f"⚠️ Domains directory not found: {self.domains_path}")
            self._load_legacy_taxonomy()
            return
        
        json_files = list(self.domains_path.glob("*.json"))
        if not json_files:
            print(f"⚠️ No JSON files found in {self.domains_path}")
            self._load_legacy_taxonomy()
            return
        
        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    domain_tax = json.load(f)
                
                domain_id = domain_tax.get("metadata", {}).get("domain_id", filepath.stem)
                domain_name = domain_tax.get("metadata", {}).get("domain_name", filepath.stem)
                
                self.taxonomy["domains"][domain_id] = {
                    "name": domain_name,
                    "file": filepath.name,
                    "metadata": domain_tax.get("metadata", {})
                }
                
                # Add categories with domain reference
                for category in domain_tax.get("categories", []):
                    category["domain_id"] = domain_id
                    category["domain_name"] = domain_name
                    self.taxonomy["categories"].append(category)
                
                print(f"  ✅ Loaded {filepath.name}: {len(domain_tax.get('categories', []))} categories")
                
            except Exception as e:
                print(f"  ❌ Error loading {filepath.name}: {e}")

    def _load_from_mongodb(self):
        """Load taxonomies from MongoDB"""
        try:
            from backend.database.mongodb import sync_db, COLLECTIONS
            
            taxonomies_col = sync_db[COLLECTIONS["taxonomies"]]
            cursor = taxonomies_col.find({})
            
            for doc in cursor:
                domain_id = doc.get("metadata", {}).get("domain_id", "UNKNOWN")
                domain_name = doc.get("metadata", {}).get("domain_name", "UNKNOWN")
                
                self.taxonomy["domains"][domain_id] = {
                    "name": domain_name,
                    "metadata": doc.get("metadata", {})
                }
                
                for category in doc.get("categories", []):
                    category["domain_id"] = domain_id
                    category["domain_name"] = domain_name
                    self.taxonomy["categories"].append(category)
            
            print(f"  ✅ Loaded {len(self.taxonomy['domains'])} domains from MongoDB")
            
        except Exception as e:
            print(f"  ❌ MongoDB load failed: {e}")
            print("  📁 Falling back to JSON files...")
            self._load_from_files()

    def _load_legacy_taxonomy(self):
        """Fallback: Load Manal's original taxonomy file"""
        legacy_file = Path(__file__).parent / "taxonomie.json"
        if legacy_file.exists():
            try:
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    legacy_tax = json.load(f)
                
                for category in legacy_tax.get("categories", []):
                    category["domain_id"] = "DOM-LEGACY"
                    category["domain_name"] = "LEGACY"
                    self.taxonomy["categories"].append(category)
                
                self.taxonomy["domains"]["DOM-LEGACY"] = {
                    "name": "LEGACY",
                    "file": "taxonomie.json"
                }
                print(f"  ✅ Loaded legacy taxonomy: {len(legacy_tax.get('categories', []))} categories")
            except Exception as e:
                print(f"  ❌ Error loading legacy taxonomy: {e}")

    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Compile all regex patterns from taxonomies"""
        compiled = {}
        
        for category in self.taxonomy.get("categories", []):
            category_name = category.get("class", "UNKNOWN")
            domain_id = category.get("domain_id", "UNKNOWN")
            
            if category_name not in compiled:
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
                                "domain_id": domain_id,
                                "domain_name": category.get("domain_name", ""),
                                "sensitivity_level": sensitivity,
                                "type": category.get("type", "PII"),
                                "context_required": context_required
                            }
                        ))
                    except re.error as e:
                        print(f"  ⚠️ Regex error for {entity_name}: {e}")
        
        return compiled

    def _build_keyword_matchers(self) -> Dict[str, Dict]:
        """Build keyword matchers from acronyms"""
        matchers = {}
        
        for category in self.taxonomy.get("categories", []):
            for subclass in category.get("subclasses", []):
                entity_name = subclass.get("name", "")
                acronyms = subclass.get("acronyms_fr", []) + subclass.get("acronyms_en", [])
                
                for keyword in acronyms:
                    if keyword and len(keyword) > 1:
                        matchers[keyword.lower()] = {
                            "entity_type": entity_name,
                            "category": category.get("class", ""),
                            "domain_id": category.get("domain_id", ""),
                            "domain_name": category.get("domain_name", ""),
                            "sensitivity_level": subclass.get("sensitivity_level", "unknown")
                        }
        
        return matchers

    def _get_context(self, text: str, start: int, end: int, context_size: int = 30) -> str:
        """Extract context around a detection"""
        ctx_start = max(0, start - context_size)
        ctx_end = min(len(text), end + context_size)
        context = text[ctx_start:ctx_end]
        
        if ctx_start > 0:
            context = "..." + context
        if ctx_end < len(text):
            context = context + "..."
        
        return context

    def _check_context_required(self, text: str, match_start: int, match_end: int, 
                                context_keywords: List[str], window_size: int = 50) -> bool:
        """Check if required context keywords are present"""
        if not context_keywords:
            return True
        
        ctx_start = max(0, match_start - window_size)
        ctx_end = min(len(text), match_end + window_size)
        context = text[ctx_start:ctx_end].lower()
        
        return any(keyword.lower() in context for keyword in context_keywords)

    def _detect_with_regex(self, text: str, domains_filter: Optional[List[str]] = None, 
                           detect_names: bool = False) -> List[Dict]:
        """Detection using regex patterns"""
        detections = []
        
        for category_name, patterns in self.compiled_patterns.items():
            for pattern, metadata in patterns:
                # Apply domain filter
                if domains_filter:
                    domain_id = metadata.get("domain_id", "")
                    domain_name = metadata.get("domain_name", "").lower()
                    if not any(d.lower() in domain_id.lower() or d.lower() in domain_name 
                              for d in domains_filter):
                        continue
                
                # Skip name detection if not enabled
                if not detect_names and "Nom" in metadata.get("entity_type", ""):
                    continue
                
                for match in pattern.finditer(text):
                    matched_value = match.group(0)
                    
                    # Context validation
                    context_required = metadata.get("context_required", [])
                    if context_required:
                        if not self._check_context_required(text, match.start(), match.end(), context_required):
                            continue
                    
                    # Filter false positives for fiscal IDs
                    if "fiscal" in metadata.get("entity_type", "").lower():
                        if matched_value.startswith(('06', '07', '05', '+212', '212')):
                            continue
                    
                    detection = {
                        "entity_type": metadata["entity_type"],
                        "category": metadata["category"],
                        "domain": metadata.get("domain_name", ""),
                        "value": matched_value,
                        "start": match.start(),
                        "end": match.end(),
                        "sensitivity_level": metadata["sensitivity_level"],
                        "confidence_score": 0.9,
                        "detection_method": "regex",
                        "context": self._get_context(text, match.start(), match.end())
                    }
                    detections.append(detection)
        
        return detections

    def _detect_with_keywords(self, text: str, domains_filter: Optional[List[str]] = None) -> List[Dict]:
        """Detection using keyword matching"""
        detections = []
        text_lower = text.lower()
        
        for keyword, metadata in self.keyword_matchers.items():
            # Apply domain filter
            if domains_filter:
                domain_id = metadata.get("domain_id", "")
                domain_name = metadata.get("domain_name", "").lower()
                if not any(d.lower() in domain_id.lower() or d.lower() in domain_name 
                          for d in domains_filter):
                    continue
            
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, text_lower):
                pos = match.start()
                
                detection = {
                    "entity_type": metadata["entity_type"],
                    "category": metadata["category"],
                    "domain": metadata.get("domain_name", ""),
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
        """Merge overlapping detections, keeping highest confidence"""
        if not detections:
            return []
        
        sorted_detections = sorted(detections, key=lambda x: (x["start"], -x["confidence_score"]))
        merged = []
        
        for detection in sorted_detections:
            overlapping = False
            for i, existing in enumerate(merged):
                if (detection["start"] < existing["end"] and detection["end"] > existing["start"]):
                    if detection["confidence_score"] > existing["confidence_score"]:
                        merged[i] = detection
                    overlapping = True
                    break
            
            if not overlapping:
                merged.append(detection)
        
        return sorted(merged, key=lambda x: x["start"])

    def analyze(self, text: str, language: str = "fr", 
                confidence_threshold: float = 0.5,
                detect_names: bool = False,
                domains: Optional[List[str]] = None) -> List[Dict]:
        """Analyze text and detect sensitive data"""
        
        if not text or not text.strip():
            return []
        
        # Regex detection
        regex_detections = self._detect_with_regex(text, domains_filter=domains, detect_names=detect_names)
        
        # Keyword detection
        keyword_detections = self._detect_with_keywords(text, domains_filter=domains)
        
        # Combine and filter
        all_detections = regex_detections + keyword_detections
        all_detections = [d for d in all_detections if d["confidence_score"] >= confidence_threshold]
        
        # Merge overlaps
        merged_detections = self._merge_overlapping_detections(all_detections)
        
        return merged_detections

    def anonymize_text(self, text: str, detections: List[Dict]) -> str:
        """Anonymize text by replacing detected values"""
        if not detections:
            return text
        
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)
        
        anonymized = text
        for detection in sorted_detections:
            entity_type = detection["entity_type"]
            start = detection["start"]
            end = detection["end"]
            
            placeholder = f"[{entity_type.upper().replace(' ', '_').replace('-', '_')}]"
            anonymized = anonymized[:start] + placeholder + anonymized[end:]
        
        return anonymized

    def get_domains(self) -> List[Dict]:
        """Get list of available domains"""
        return [
            {
                "domain_id": did,
                "domain_name": info.get("name", ""),
                "metadata": info.get("metadata", {})
            }
            for did, info in self.taxonomy.get("domains", {}).items()
        ]

# ====================================================================
# INITIALISATION
# ====================================================================

domains_dir = Path(__file__).parent / "domains"
detection_engine = PIIDetectionEngine(
    domains_path=str(domains_dir),
    use_mongodb=False  # Set to True to load from MongoDB
)

# ====================================================================
# FASTAPI APPLICATION
# ====================================================================

app = FastAPI(
    title="Classification Engine API - Domain-Based",
    description="API de détection de données sensibles avec taxonomies par domaine",
    version="3.0.0"
)

# Enable CORS for frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text and detect sensitive data"""
    start_time = time.time()
    
    try:
        detections = detection_engine.analyze(
            text=request.text,
            language=request.language,
            confidence_threshold=request.confidence_threshold,
            detect_names=request.detect_names,
            domains=request.domains
        )
        
        # Anonymization
        anonymized_text = None
        if request.anonymize and detections:
            anonymized_text = detection_engine.anonymize_text(request.text, detections)
            for det in detections:
                det["anonymized_value"] = f"[{det['entity_type'].upper().replace(' ', '_').replace('-', '_')}]"
        
        # Summary by category
        summary = {}
        for det in detections:
            category = det["category"]
            summary[category] = summary.get(category, 0) + 1
        
        # Summary by domain
        domains_summary = {}
        for det in detections:
            domain = det.get("domain", "UNKNOWN")
            domains_summary[domain] = domains_summary.get(domain, 0) + 1
        
        execution_time = (time.time() - start_time) * 1000
        
        detection_results = [DetectionResult(**d) for d in detections]
        
        return AnalyzeResponse(
            success=True,
            text_length=len(request.text),
            detections_count=len(detections),
            detections=detection_results,
            summary=summary,
            domains_summary=domains_summary,
            execution_time_ms=round(execution_time, 2),
            anonymized_text=anonymized_text
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine": "ready",
        "version": "3.0.0",
        "domains_count": len(detection_engine.taxonomy.get("domains", {})),
        "patterns_count": sum(len(patterns) for patterns in detection_engine.compiled_patterns.values()),
        "keywords_count": len(detection_engine.keyword_matchers)
    }

@app.get("/domains")
async def get_domains():
    """Get available domains"""
    return {"domains": detection_engine.get_domains()}

@app.get("/categories")
async def get_categories():
    """Get all categories with domain info"""
    categories = []
    for category in detection_engine.taxonomy.get("categories", []):
        categories.append({
            "name": category.get("class", ""),
            "name_en": category.get("class_en", ""),
            "type": category.get("type", ""),
            "domain": category.get("domain_name", ""),
            "subclasses_count": len(category.get("subclasses", []))
        })
    return {"categories": categories}

@app.get("/statistics")
async def get_statistics():
    """Get engine statistics"""
    stats = {
        "domains": len(detection_engine.taxonomy.get("domains", {})),
        "categories": len(detection_engine.taxonomy.get("categories", [])),
        "patterns": sum(len(p) for p in detection_engine.compiled_patterns.values()),
        "keywords": len(detection_engine.keyword_matchers),
        "domains_detail": {}
    }
    
    for domain_id, info in detection_engine.taxonomy.get("domains", {}).items():
        domain_cats = [c for c in detection_engine.taxonomy["categories"] 
                       if c.get("domain_id") == domain_id]
        total_entities = sum(len(c.get("subclasses", [])) for c in domain_cats)
        stats["domains_detail"][domain_id] = {
            "name": info.get("name", ""),
            "categories": len(domain_cats),
            "entities": total_entities
        }
    
    return stats

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("MOTEUR DE DÉTECTION PII/SPI - DOMAIN-BASED v3.0")
    print("=" * 60)
    print(f"Domaines: {len(detection_engine.taxonomy.get('domains', {}))}")
    print(f"Patterns: {sum(len(p) for p in detection_engine.compiled_patterns.values())}")
    print(f"Keywords: {len(detection_engine.keyword_matchers)}")
    print("=" * 60)
    print("\nDémarrage du serveur sur http://127.0.0.1:8001")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
