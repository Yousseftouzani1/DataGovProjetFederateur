import hashlib
import random
import uuid
from enum import Enum
from typing import Any, Tuple, Optional
from .score_calculator import MaskingLevel

class MaskingTechnique(str, Enum):
    PSEUDONYMIZATION = "pseudonymization"   # Replace with consistent fake value
    GENERALIZATION = "generalization"       # Generalize to category
    SUPPRESSION = "suppression"             # Remove entirely
    PERTURBATION = "perturbation"           # Add noise
    TOKENIZATION = "tokenization"           # Replace with token
    HASHING = "hashing"                     # One-way hash
    ENCRYPTION = "encryption"               # Encrypted value

class ContextualMasker:
    def __init__(self):
        self.pseudonym_cache = {}

    def mask(self, value: Any, entity_type: str, level: MaskingLevel, technique: MaskingTechnique = None) -> Tuple[Any, str]:
        if value is None or level == MaskingLevel.NONE: return value, "none"
        str_value = str(value)
        
        if technique is None:
            technique = self._select_technique(entity_type, level)

        if technique == MaskingTechnique.PSEUDONYMIZATION:
             return self._pseudonymize(str_value, entity_type), technique.value
        elif technique == MaskingTechnique.GENERALIZATION:
             return self._generalize(str_value, entity_type), technique.value
        elif technique == MaskingTechnique.SUPPRESSION:
             return f"[{entity_type.upper()}]", technique.value
        elif technique == MaskingTechnique.PERTURBATION:
             return self._perturb(str_value, entity_type), technique.value
        elif technique == MaskingTechnique.TOKENIZATION:
             return f"TKN_{hashlib.md5(str_value.encode()).hexdigest()[:12]}", technique.value
        elif technique == MaskingTechnique.HASHING:
             return hashlib.sha256(str_value.encode()).hexdigest()[:32], technique.value
        elif technique == MaskingTechnique.ENCRYPTION:
             return f"ENC_{hashlib.sha256(str_value.encode()).hexdigest()[:24]}", technique.value
        
        return self._partial_mask(str_value, entity_type), "partial"

    def _select_technique(self, entity_type: str, level: MaskingLevel) -> MaskingTechnique:
        if level == MaskingLevel.PARTIAL: return MaskingTechnique.PSEUDONYMIZATION
        elif level == MaskingLevel.FULL: return MaskingTechnique.SUPPRESSION
        elif level == MaskingLevel.ENCRYPTED: return MaskingTechnique.HASHING
        return MaskingTechnique.PSEUDONYMIZATION

    def _partial_mask(self, value: str, entity_type: str) -> str:
        if entity_type == "email":
             parts = value.split("@")
             return (parts[0][:2] + "***@" + parts[1]) if len(parts) == 2 else value
        return value[:2] + "*" * (len(value)-4) + value[-2:] if len(value) > 4 else "*"*len(value)

    def _pseudonymize(self, value: str, entity_type: str) -> str:
        key = f"{entity_type}:{value}"
        if key in self.pseudonym_cache: return self.pseudonym_cache[key]
        
        if entity_type == "name": result = random.choice(["Mohammed A.", "Fatima B.", "Ahmed C."])
        elif entity_type == "email": result = f"user_{random.randint(1000,9999)}@masked.com"
        else: result = f"[PSEUDO_{uuid.uuid4().hex[:6]}]"
        
        self.pseudonym_cache[key] = result
        return result

    def _generalize(self, value: str, entity_type: str) -> str:
        if entity_type == "age": return "30-49" # Simplification
        if entity_type == "salary": return "10K-20K MAD"
        return f"[{entity_type.upper()}_GEN]"

    def _perturb(self, value: str, entity_type: str) -> str:
        try:
             val = float(value)
             return str(round(val * random.uniform(0.9, 1.1), 2))
        except: return value
