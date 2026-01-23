import hashlib
import random
import uuid
from enum import Enum
from typing import Any, Tuple, Optional
import numpy as np
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
        # Initialize TenSEAL Context for HE (Level 1)
        try:
             import tenseal as ts
             self.ctx = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus_degree=8192, coeff_mod_bit_sizes=[60, 40, 40, 60])
             self.ctx.global_scale = 2**40
             self.ctx.generate_galois_keys()
             self.he_available = True
        except ImportError:
             self.he_available = False
             print("⚠️ TenSEAL not available. HE will fall back to Hashing.")

    def mask(self, value: Any, entity_type: str, level: MaskingLevel, technique: MaskingTechnique = None) -> Tuple[Any, str]:
        if value is None or level == MaskingLevel.NONE: return value, "none"
        str_value = str(value)
        
        # Mapping Level to Technique (if not forced)
        if technique is None:
            if level == MaskingLevel.ENCRYPTED: technique = MaskingTechnique.ENCRYPTION
            elif level == MaskingLevel.FULL: technique = MaskingTechnique.SUPPRESSION
            elif level == MaskingLevel.PARTIAL: technique = MaskingTechnique.GENERALIZATION
            elif level == MaskingLevel.DIFFERENTIAL_PRIVACY: technique = MaskingTechnique.PERTURBATION
            else: technique = MaskingTechnique.PSEUDONYMIZATION

        # Ensure technique is treated as string for comparison
        technique_str = technique.value if isinstance(technique, MaskingTechnique) else str(technique)

        # --- LEVEL 1: Homomorphic Encryption ---
        if technique_str == MaskingTechnique.ENCRYPTION.value:
             if self.he_available:
                 try:
                     # Attempt numeric encryption
                     val = float(value)
                     # Vector encryption
                     import tenseal as ts
                     enc_vec = ts.ckks_vector(self.ctx, [val])
                     # Return base64 serialization for transport
                     return enc_vec.serialize().hex()[:50] + "...(HE)", "homomorphic_encryption"
                 except ValueError:
                     # Fallback for strings
                     return f"HEX_{hashlib.sha256(str_value.encode()).hexdigest()}", "hashing_fallback"
             else:
                 return f"ENC_{hashlib.sha256(str_value.encode()).hexdigest()}", "hashing_fallback"

        # --- LEVEL 3: Differential Privacy (Laplace) ---
        elif technique_str == MaskingTechnique.PERTURBATION.value:
             # Epsilon-DP
             return self._apply_laplace_mechanism(value), "differential_privacy_laplace"

        elif technique_str == MaskingTechnique.PSEUDONYMIZATION.value:
             return self._pseudonymize(str_value, entity_type), "pseudonymization"
        elif technique_str == MaskingTechnique.GENERALIZATION.value:
             return self._generalize(str_value, entity_type), "generalization"
        elif technique_str == MaskingTechnique.SUPPRESSION.value:
             return None, "suppression" # Return None/Null for suppression
        
        return self._partial_mask(str_value, entity_type), "partial_masking"

    def _apply_laplace_mechanism(self, value: Any, epsilon: float = 1.0, sensitivity: float = 1.0) -> Any:
        try:
             val = float(value)
             # Laplace Noise: scale = sensitivity / epsilon
             scale = sensitivity / epsilon
             noise = np.random.laplace(0, scale)
             return round(val + noise, 2)
        except:
             return value # Cannot noise non-numeric

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

    def _partial_mask(self, value: str, entity_type: str) -> str:
        if entity_type == "email":
             parts = value.split("@")
             return (parts[0][:2] + "***@" + parts[1]) if len(parts) == 2 else value
        return value[:2] + "*" * (max(0, len(value)-4)) + value[-2:] if len(value) > 4 else "*"*len(value)
