
import re
import json
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from backend.services.sensitivity import SensitivityCalculator
from backend.db.loader import load_patterns_from_mongodb
from backend.core.patterns import MOROCCAN_PATTERNS, ARABIC_PATTERNS

class TaxonomyEngine:
    """Pure Regex-based Taxonomy Engine for Moroccan PII/SPI"""
    
    def __init__(self, domains_path: Optional[str] = None):
        # Adjusted path: services/../data/domains -> backend/data/domains
        self.domains_path = Path(domains_path) if domains_path else Path(__file__).parent.parent / "data" / "domains"
        self.taxonomy = {"categories": [], "domains": {}}
        
        # Load custom taxonomy from JSON files
        self._load_from_files()
        
        # Initialize Sensitivity Calculator (Cahier Section 4.4)
        self.sensitivity_calc = SensitivityCalculator()
        
        # Try loading patterns from MongoDB
        print("\n" + "="*60)
        print("🗄️  MONGODB PATTERN LOADING")
        print("="*60)
        
        try:
            mongodb_patterns = load_patterns_from_mongodb()
        except:
            mongodb_patterns = None
        
        # Helper to manage patterns state
        self.moroccan_patterns = MOROCCAN_PATTERNS.copy()
        
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
            print(f"⚠️ Domains path not found: {self.domains_path}")
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
        for entity_type, config in self.moroccan_patterns.items():
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
                        "context": self._get_context(text, match.start(), match.end()),
                        "analysis_explanation": f"Matches regex pattern for {metadata['entity_type']} in category {metadata['category']}"
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
                            "context": self._get_context(text, match.start(), match.end()),
                            "analysis_explanation": f"Matches Arabic pattern for {metadata['entity_type']} in category {metadata['category']}"
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
                                "context": self._get_context(text, match.start(), match.end()),
                                "analysis_explanation": f"Matches custom taxonomy pattern for {subclass.get('name', 'Unknown')}"
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

