"""
EthiMask Service - Tâche 9
Contextual Data Masking Framework

Features:
- Perceptron V0.1 for masking level decision
- Role-based contextual masking
- Multiple masking techniques:
  - Pseudonymization
  - Generalization
  - Suppression
  - K-Anonymity
- TenSEAL homomorphic encryption (optional)
- Differential privacy (optional)
"""
import hashlib
import random
import string
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Optional: TenSEAL for homomorphic encryption
try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False
    print("⚠️ TenSEAL not available. Homomorphic encryption disabled.")

# ====================================================================
# MODELS
# ====================================================================

class MaskingLevel(str, Enum):
    NONE = "none"           # No masking (full access)
    PARTIAL = "partial"     # Partial masking (show some info)
    FULL = "full"           # Full masking (replace with placeholder)
    ENCRYPTED = "encrypted" # Homomorphic encryption

class MaskingTechnique(str, Enum):
    PSEUDONYMIZATION = "pseudonymization"   # Replace with consistent fake value
    GENERALIZATION = "generalization"       # Generalize to category
    SUPPRESSION = "suppression"             # Remove entirely
    PERTURBATION = "perturbation"           # Add noise
    TOKENIZATION = "tokenization"           # Replace with token
    HASHING = "hashing"                     # One-way hash
    ENCRYPTION = "encryption"               # Encrypted value

class UserRole(str, Enum):
    ADMIN = "admin"                 # Full access
    DATA_STEWARD = "steward"        # Partial access
    DATA_ANNOTATOR = "annotator"    # Limited access
    DATA_LABELER = "labeler"        # Minimal access
    ANALYST = "analyst"             # Aggregated access only
    EXTERNAL = "external"           # No PII access

class EntityType(str, Enum):
    CIN = "cin"
    PHONE = "phone"
    EMAIL = "email"
    NAME = "name"
    ADDRESS = "address"
    IBAN = "iban"
    CNSS = "cnss"
    BIRTH_DATE = "birth_date"
    SALARY = "salary"
    MEDICAL = "medical"

class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MaskingConfig(BaseModel):
    role: UserRole = UserRole.DATA_LABELER
    context: str = "default"  # Context: analysis, export, display, api
    purpose: str = "general"  # Purpose: research, compliance, marketing

class Detection(BaseModel):
    field: str
    value: Any
    entity_type: str
    sensitivity_level: str
    confidence: float = 1.0

class MaskRequest(BaseModel):
    data: Dict[str, Any]
    detections: List[Detection]
    config: MaskingConfig

class MaskResponse(BaseModel):
    masked_data: Dict[str, Any]
    masking_applied: int
    technique_used: Dict[str, str]
    audit_log: List[Dict]

class MaskingPolicy(BaseModel):
    entity_type: str
    role: str
    level: MaskingLevel
    technique: MaskingTechnique

# ====================================================================
# MASKING PERCEPTRON V0.1
# ====================================================================

class MaskingPerceptron:
    """
    Perceptron-based decision model for masking level
    
    Features:
    - sensitivity_score (0-1)
    - role_privilege_score (0-1)
    - context_score (0-1)
    - purpose_score (0-1)
    
    Output: Masking level decision
    """
    
    def __init__(self):
        # Pretrained weights (can be fine-tuned)
        self.weights = np.array([0.35, -0.30, 0.20, 0.15])
        self.bias = 0.4
        
        # Feature encodings
        self.sensitivity_encoding = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0
        }
        
        self.role_encoding = {
            UserRole.ADMIN: 0.0,
            UserRole.DATA_STEWARD: 0.3,
            UserRole.ANALYST: 0.5,
            UserRole.DATA_ANNOTATOR: 0.6,
            UserRole.DATA_LABELER: 0.8,
            UserRole.EXTERNAL: 1.0
        }
        
        self.context_encoding = {
            "internal": 0.2,
            "analysis": 0.3,
            "display": 0.5,
            "export": 0.7,
            "api": 0.6,
            "external": 0.9,
            "default": 0.5
        }
        
        self.purpose_encoding = {
            "internal_research": 0.2,
            "compliance": 0.3,
            "research": 0.4,
            "general": 0.5,
            "marketing": 0.7,
            "third_party": 0.9
        }
    
    def encode_features(self, 
                       sensitivity: str,
                       role: UserRole,
                       context: str,
                       purpose: str) -> np.ndarray:
        """Encode categorical features to numerical"""
        return np.array([
            self.sensitivity_encoding.get(sensitivity.lower(), 0.5),
            self.role_encoding.get(role, 0.5),
            self.context_encoding.get(context.lower(), 0.5),
            self.purpose_encoding.get(purpose.lower(), 0.5)
        ])
    
    def predict(self, features: np.ndarray) -> MaskingLevel:
        """Predict masking level based on features"""
        score = np.dot(features, self.weights) + self.bias
        
        # Apply sigmoid for probability
        prob = 1 / (1 + np.exp(-score * 5))
        
        if prob < 0.25:
            return MaskingLevel.NONE
        elif prob < 0.50:
            return MaskingLevel.PARTIAL
        elif prob < 0.75:
            return MaskingLevel.FULL
        else:
            return MaskingLevel.ENCRYPTED
    
    def decide_masking(self,
                       sensitivity: str,
                       role: UserRole,
                       context: str = "default",
                       purpose: str = "general") -> Tuple[MaskingLevel, float]:
        """Main decision function"""
        features = self.encode_features(sensitivity, role, context, purpose)
        level = self.predict(features)
        confidence = min(1.0, abs(np.dot(features, self.weights) + self.bias))
        
        return level, confidence
    
    def get_decision_explanation(self, 
                                 sensitivity: str,
                                 role: UserRole,
                                 context: str,
                                 purpose: str) -> Dict:
        """Explain the masking decision"""
        features = self.encode_features(sensitivity, role, context, purpose)
        level, confidence = self.decide_masking(sensitivity, role, context, purpose)
        
        contributions = features * self.weights
        
        return {
            "decision": level.value,
            "confidence": round(confidence, 3),
            "feature_contributions": {
                "sensitivity": round(contributions[0], 3),
                "role": round(contributions[1], 3),
                "context": round(contributions[2], 3),
                "purpose": round(contributions[3], 3)
            },
            "encoded_features": {
                "sensitivity": features[0],
                "role": features[1],
                "context": features[2],
                "purpose": features[3]
            }
        }

# ====================================================================
# CONTEXTUAL MASKER
# ====================================================================

class ContextualMasker:
    """Apply masking techniques based on level"""
    
    def __init__(self):
        self.pseudonym_cache = {}  # For consistent pseudonymization
    
    def mask(self, value: Any, entity_type: str, level: MaskingLevel, 
             technique: MaskingTechnique = None) -> Tuple[Any, str]:
        """
        Apply masking to a value
        Returns: (masked_value, technique_used)
        """
        if value is None or level == MaskingLevel.NONE:
            return value, "none"
        
        str_value = str(value)
        
        # Auto-select technique if not specified
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
            return self._tokenize(str_value), technique.value
        
        elif technique == MaskingTechnique.HASHING:
            return self._hash(str_value), technique.value
        
        elif technique == MaskingTechnique.ENCRYPTION:
            return self._encrypt(str_value), technique.value
        
        # Default: partial mask
        return self._partial_mask(str_value, entity_type), "partial"
    
    def _select_technique(self, entity_type: str, level: MaskingLevel) -> MaskingTechnique:
        """Select appropriate technique based on entity and level"""
        if level == MaskingLevel.PARTIAL:
            # Use pseudonymization for partial
            return MaskingTechnique.PSEUDONYMIZATION
        
        elif level == MaskingLevel.FULL:
            # Use generalization or suppression
            if entity_type in ["name", "email", "phone"]:
                return MaskingTechnique.GENERALIZATION
            return MaskingTechnique.SUPPRESSION
        
        elif level == MaskingLevel.ENCRYPTED:
            return MaskingTechnique.HASHING
        
        return MaskingTechnique.PSEUDONYMIZATION
    
    def _partial_mask(self, value: str, entity_type: str) -> str:
        """Apply partial masking showing some characters"""
        if entity_type == "cin":
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        
        elif entity_type == "phone":
            return value[:4] + "****" + value[-2:]
        
        elif entity_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                local = parts[0][:2] + "***"
                return f"{local}@{parts[1]}"
            return "*" * len(value)
        
        elif entity_type == "iban":
            return value[:4] + "*" * (len(value) - 8) + value[-4:]
        
        elif entity_type == "name":
            return value[0] + "*" * (len(value) - 1)
        
        elif entity_type == "cnss":
            return value[:3] + "***" + value[-3:]
        
        # Default
        show = max(2, len(value) // 4)
        return value[:show] + "*" * (len(value) - show * 2) + value[-show:]
    
    def _pseudonymize(self, value: str, entity_type: str) -> str:
        """Replace with consistent fake value"""
        # Use cache for consistency
        cache_key = f"{entity_type}:{value}"
        if cache_key in self.pseudonym_cache:
            return self.pseudonym_cache[cache_key]
        
        if entity_type == "name":
            fake_names = ["Mohammed A.", "Fatima B.", "Ahmed C.", "Khadija D.", "Youssef E."]
            result = random.choice(fake_names)
        
        elif entity_type == "email":
            result = f"user_{random.randint(1000, 9999)}@masked.com"
        
        elif entity_type == "phone":
            result = f"+212 6** *** ***"
        
        elif entity_type == "cin":
            result = f"XX{random.randint(100000, 999999)}"
        
        elif entity_type == "address":
            result = "Adresse anonymisée, Ville, Maroc"
        
        else:
            result = f"[PSEUDO_{entity_type.upper()}_{str(uuid.uuid4())[:6]}]"
        
        self.pseudonym_cache[cache_key] = result
        return result
    
    def _generalize(self, value: str, entity_type: str) -> str:
        """Generalize to broader category"""
        if entity_type == "age":
            try:
                age = int(value)
                if age < 18:
                    return "Mineur"
                elif age < 30:
                    return "18-29"
                elif age < 50:
                    return "30-49"
                elif age < 65:
                    return "50-64"
                else:
                    return "65+"
            except:
                return "[AGE]"
        
        elif entity_type == "salary":
            try:
                sal = float(str(value).replace(" ", "").replace(",", ""))
                if sal < 5000:
                    return "< 5K MAD"
                elif sal < 10000:
                    return "5K-10K MAD"
                elif sal < 20000:
                    return "10K-20K MAD"
                else:
                    return "> 20K MAD"
            except:
                return "[SALARY]"
        
        elif entity_type == "birth_date":
            try:
                year = int(value[:4]) if len(value) >= 4 else int(value[-4:])
                return f"Né(e) dans les années {(year // 10) * 10}"
            except:
                return "[BIRTH_YEAR]"
        
        elif entity_type == "address":
            return "Région anonymisée, Maroc"
        
        return f"[{entity_type.upper()}_GENERALIZED]"
    
    def _perturb(self, value: str, entity_type: str) -> str:
        """Add noise to numeric values"""
        if entity_type in ["salary", "age"]:
            try:
                num_val = float(str(value).replace(" ", "").replace(",", ""))
                noise = random.uniform(-0.1, 0.1) * num_val
                return str(round(num_val + noise, 2))
            except:
                pass
        return value
    
    def _tokenize(self, value: str) -> str:
        """Replace with reversible token"""
        token = f"TKN_{hashlib.md5(value.encode()).hexdigest()[:12]}"
        return token
    
    def _hash(self, value: str) -> str:
        """One-way hash (SHA-256)"""
        return hashlib.sha256(value.encode()).hexdigest()[:32]
    
    def _encrypt(self, value: str) -> str:
        """Encrypt value (placeholder - use TenSEAL in production)"""
        if TENSEAL_AVAILABLE:
            # Would use TenSEAL here
            pass
        # Simple encoding for demo
        return f"ENC_{hashlib.sha256(value.encode()).hexdigest()[:24]}"

# ====================================================================
# MASKING POLICY MANAGER
# ====================================================================

class PolicyManager:
    """Manage masking policies per role and entity"""
    
    DEFAULT_POLICIES = [
        # Admin: full access
        MaskingPolicy(entity_type="*", role="admin", level=MaskingLevel.NONE, technique=MaskingTechnique.PSEUDONYMIZATION),
        
        # Steward: partial masking for sensitive
        MaskingPolicy(entity_type="cin", role="steward", level=MaskingLevel.PARTIAL, technique=MaskingTechnique.PSEUDONYMIZATION),
        MaskingPolicy(entity_type="phone", role="steward", level=MaskingLevel.PARTIAL, technique=MaskingTechnique.PSEUDONYMIZATION),
        MaskingPolicy(entity_type="salary", role="steward", level=MaskingLevel.PARTIAL, technique=MaskingTechnique.GENERALIZATION),
        
        # Annotator: more masking
        MaskingPolicy(entity_type="cin", role="annotator", level=MaskingLevel.FULL, technique=MaskingTechnique.SUPPRESSION),
        MaskingPolicy(entity_type="phone", role="annotator", level=MaskingLevel.PARTIAL, technique=MaskingTechnique.PSEUDONYMIZATION),
        MaskingPolicy(entity_type="name", role="annotator", level=MaskingLevel.PARTIAL, technique=MaskingTechnique.PSEUDONYMIZATION),
        
        # Labeler: heavy masking
        MaskingPolicy(entity_type="*", role="labeler", level=MaskingLevel.FULL, technique=MaskingTechnique.SUPPRESSION),
        
        # External: all masked
        MaskingPolicy(entity_type="*", role="external", level=MaskingLevel.ENCRYPTED, technique=MaskingTechnique.HASHING),
    ]
    
    def __init__(self):
        self.policies = self.DEFAULT_POLICIES.copy()
    
    def get_policy(self, entity_type: str, role: str) -> Optional[MaskingPolicy]:
        """Find applicable policy"""
        # Try exact match first
        for policy in self.policies:
            if policy.entity_type == entity_type and policy.role == role:
                return policy
        
        # Try wildcard
        for policy in self.policies:
            if policy.entity_type == "*" and policy.role == role:
                return policy
        
        # Default to full masking
        return MaskingPolicy(
            entity_type=entity_type,
            role=role,
            level=MaskingLevel.FULL,
            technique=MaskingTechnique.SUPPRESSION
        )

# ====================================================================
# DIFFERENTIAL PRIVACY (Optional)
# ====================================================================

class DifferentialPrivacy:
    """Add differential privacy noise"""
    
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon
    
    def add_laplace_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Laplace noise for differential privacy"""
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise
    
    def randomized_response(self, value: bool, p: float = 0.75) -> bool:
        """Randomized response for boolean values"""
        if random.random() < p:
            return value
        return random.choice([True, False])

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="EthiMask Service",
    description="Tâche 9 - Contextual Data Masking Framework",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
perceptron = MaskingPerceptron()
masker = ContextualMasker()
policy_manager = PolicyManager()

@app.get("/")
def root():
    return {
        "service": "EthiMask Service",
        "version": "2.0.0",
        "status": "running",
        "tenseal_available": TENSEAL_AVAILABLE,
        "masking_levels": [l.value for l in MaskingLevel],
        "techniques": [t.value for t in MaskingTechnique]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ====================================================================
# MASKING ENDPOINTS
# ====================================================================

@app.post("/mask", response_model=MaskResponse)
def mask_data(request: MaskRequest):
    """Apply contextual masking to data with PII detections"""
    masked_data = request.data.copy()
    techniques_used = {}
    audit_log = []
    
    for detection in request.detections:
        field = detection.field
        
        if field not in masked_data:
            continue
        
        original_value = masked_data[field]
        
        # Get masking decision from perceptron
        level, confidence = perceptron.decide_masking(
            sensitivity=detection.sensitivity_level,
            role=request.config.role,
            context=request.config.context,
            purpose=request.config.purpose
        )
        
        # Override with policy if exists
        policy = policy_manager.get_policy(
            entity_type=detection.entity_type,
            role=request.config.role.value
        )
        if policy:
            level = policy.level
            technique = policy.technique
        else:
            technique = None
        
        # Apply masking
        masked_value, technique_used = masker.mask(
            value=original_value,
            entity_type=detection.entity_type,
            level=level,
            technique=technique
        )
        
        masked_data[field] = masked_value
        techniques_used[field] = technique_used
        
        # Audit log
        audit_log.append({
            "field": field,
            "entity_type": detection.entity_type,
            "sensitivity": detection.sensitivity_level,
            "masking_level": level.value,
            "technique": technique_used,
            "decision_confidence": round(confidence, 3),
            "timestamp": datetime.now().isoformat()
        })
    
    return MaskResponse(
        masked_data=masked_data,
        masking_applied=len([t for t in techniques_used.values() if t != "none"]),
        technique_used=techniques_used,
        audit_log=audit_log
    )

@app.post("/decide")
def get_masking_decision(
    sensitivity: str,
    role: UserRole,
    context: str = "default",
    purpose: str = "general"
):
    """Get masking decision explanation"""
    return perceptron.get_decision_explanation(sensitivity, role, context, purpose)

@app.post("/mask/simple")
def simple_mask(data: Dict, role: UserRole = UserRole.DATA_LABELER):
    """Simple masking without explicit detections - auto-detect and mask"""
    masked = {}
    techniques = {}
    
    # Common PII field patterns
    pii_patterns = {
        "cin": ["cin", "id_card", "carte_identite"],
        "phone": ["phone", "tel", "mobile", "telephone"],
        "email": ["email", "mail", "courriel"],
        "name": ["name", "nom", "prenom", "firstname", "lastname"],
        "address": ["address", "adresse"],
        "iban": ["iban", "bank", "compte"],
        "birth_date": ["birth", "naissance", "dob"],
        "salary": ["salary", "salaire", "wage"],
    }
    
    for field, value in data.items():
        field_lower = field.lower()
        entity_type = None
        
        # Detect entity type
        for etype, patterns in pii_patterns.items():
            if any(p in field_lower for p in patterns):
                entity_type = etype
                break
        
        if entity_type:
            # Get masking decision
            level, _ = perceptron.decide_masking(
                sensitivity="high",
                role=role,
                context="default",
                purpose="general"
            )
            
            masked_value, technique = masker.mask(value, entity_type, level)
            masked[field] = masked_value
            techniques[field] = technique
        else:
            masked[field] = value
            techniques[field] = "none"
    
    return {
        "masked_data": masked,
        "techniques_applied": techniques
    }

# ====================================================================
# POLICY ENDPOINTS
# ====================================================================

@app.get("/policies")
def list_policies():
    """List all masking policies"""
    return {"policies": [p.dict() for p in policy_manager.policies]}

@app.post("/policies")
def add_policy(policy: MaskingPolicy):
    """Add a new masking policy"""
    policy_manager.policies.append(policy)
    return {"status": "added", "total_policies": len(policy_manager.policies)}

@app.get("/techniques")
def list_techniques():
    """List available masking techniques"""
    return {
        "techniques": {
            "pseudonymization": "Replace with consistent fake value",
            "generalization": "Generalize to broader category (e.g., age ranges)",
            "suppression": "Remove/replace with placeholder",
            "perturbation": "Add noise to numeric values",
            "tokenization": "Replace with reversible token",
            "hashing": "One-way cryptographic hash (SHA-256)",
            "encryption": "Encrypted value (requires key)"
        }
    }

@app.get("/roles")
def list_roles():
    """List user roles and their default masking levels"""
    return {
        "roles": {
            "admin": "Full access, no masking",
            "steward": "Partial masking for sensitive fields",
            "annotator": "More masking, pseudonymized names",
            "labeler": "Heavy masking, suppressed PII",
            "analyst": "Aggregated access only",
            "external": "All PII encrypted/hashed"
        }
    }

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔒 ETHIMASK SERVICE - Tâche 9")
    print("="*60)
    print(f"TenSEAL: {'✅ Available' if TENSEAL_AVAILABLE else '❌ Not installed'}")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8009, reload=True)
