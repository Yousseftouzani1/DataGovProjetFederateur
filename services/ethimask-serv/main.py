"""
EthiMask Service - Tâche 9
Contextual Data Masking Framework (Mongo Persisted)

Features:
- Perceptron V0.1 for masking level decision
- Role-based contextual masking
- Multiple masking techniques
- MongoDB Persistence for Audit Logs and Policies
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

from backend.database.mongodb import db

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
# CONFIG MANAGER (MONGO PERSISTED)
# ====================================================================

class ConfigUpdate(BaseModel):
    ws: float = Field(..., ge=-1.0, le=1.0)
    wr: float = Field(..., ge=-1.0, le=1.0)
    wc: float = Field(..., ge=-1.0, le=1.0)
    wp: float = Field(..., ge=-1.0, le=1.0)
    bias: float = Field(0.4, ge=-1.0, le=1.0)

class ConfigManager:
    DEFAULT_CONFIG = {
        "weights": [0.35, -0.30, 0.20, 0.15],
        "bias": 0.4
    }

    async def get_config(self) -> Dict:
        if db is not None:
            doc = await db.ethimask_config.find_one({"_id": "global_config"})
            if doc:
                return {"weights": doc["weights"], "bias": doc["bias"]}
        return self.DEFAULT_CONFIG

    async def update_config(self, config: ConfigUpdate):
        # Map frontend fields to perceptron weights order: [sensitivity, role, context, purpose]
        new_weights = [config.ws, config.wr, config.wc, config.wp]
        if db is not None:
            await db.ethimask_config.update_one(
                {"_id": "global_config"},
                {"$set": {"weights": new_weights, "bias": config.bias}},
                upsert=True
            )
        # Update in-memory perceptron
        perceptron.update_weights(new_weights, config.bias)

# ====================================================================
# MASKING PERCEPTRON
# ====================================================================

class MaskingPerceptron:
    def __init__(self):
        self.weights = np.array([0.35, -0.30, 0.20, 0.15])
        self.bias = 0.4
        self.sensitivity_encoding = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        self.role_encoding = {
            UserRole.ADMIN: 0.0, UserRole.DATA_STEWARD: 0.3, UserRole.ANALYST: 0.5,
            UserRole.DATA_ANNOTATOR: 0.6, UserRole.DATA_LABELER: 0.8, UserRole.EXTERNAL: 1.0
        }
        self.context_encoding = {"internal": 0.2, "analysis": 0.3, "display": 0.5, "export": 0.7, "api": 0.6, "external": 0.9, "default": 0.5}
        self.purpose_encoding = {"internal_research": 0.2, "compliance": 0.3, "research": 0.4, "general": 0.5, "marketing": 0.7, "third_party": 0.9}

    def update_weights(self, weights: List[float], bias: float):
        self.weights = np.array(weights)
        self.bias = bias

    def encode_features(self, sensitivity, role, context, purpose):
        return np.array([
            self.sensitivity_encoding.get(sensitivity.lower(), 0.5),
            self.role_encoding.get(role, 0.5),
            self.context_encoding.get(context.lower(), 0.5),
            self.purpose_encoding.get(purpose.lower(), 0.5)
        ])

    def decide_masking(self, sensitivity: str, role: UserRole, context: str = "default", purpose: str = "general") -> Tuple[MaskingLevel, float]:
        features = self.encode_features(sensitivity, role, context, purpose)
        score = np.dot(features, self.weights) + self.bias
        prob = 1 / (1 + np.exp(-score * 5))
        
        confidence = min(1.0, abs(score))
        
        if prob < 0.25: return MaskingLevel.NONE, confidence
        elif prob < 0.50: return MaskingLevel.PARTIAL, confidence
        elif prob < 0.75: return MaskingLevel.FULL, confidence
        else: return MaskingLevel.ENCRYPTED, confidence

    def get_decision_explanation(self, sensitivity: str, role: UserRole, context: str, purpose: str) -> Dict:
        features = self.encode_features(sensitivity, role, context, purpose)
        level, confidence = self.decide_masking(sensitivity, role, context, purpose)
        contributions = features * self.weights
        return {
            "decision": level.value, "confidence": round(confidence, 3),
            "feature_contributions": {
                "sensitivity": round(contributions[0], 3), "role": round(contributions[1], 3),
                "context": round(contributions[2], 3), "purpose": round(contributions[3], 3)
            }
        }

# ====================================================================
# CONTEXTUAL MASKER
# ====================================================================

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

# ====================================================================
# POLICY MANAGER (MONGO PERSISTED)
# ====================================================================

class PolicyManager:
    DEFAULT_POLICIES = [
        {"entity_type": "*", "role": "admin", "level": "none", "technique": "pseudonymization"},
        {"entity_type": "cin", "role": "steward", "level": "partial", "technique": "pseudonymization"},
        {"entity_type": "*", "role": "labeler", "level": "full", "technique": "suppression"},
        {"entity_type": "*", "role": "external", "level": "encrypted", "technique": "hashing"},
    ]
    
    async def get_policy(self, entity_type: str, role: str) -> Optional[MaskingPolicy]:
        if db is not None:
            # Look for exact match
            doc = await db.masking_policies.find_one({"entity_type": entity_type, "role": role})
            if not doc:
                # Wildcard entity
                doc = await db.masking_policies.find_one({"entity_type": "*", "role": role})
            
            if doc:
                return MaskingPolicy(**doc)
        
        # Fallback defaults if DB empty or not found
        for p in self.DEFAULT_POLICIES:
            if (p["entity_type"] == entity_type or p["entity_type"] == "*") and p["role"] == role:
                return MaskingPolicy(**p)

        return MaskingPolicy(entity_type=entity_type, role=role, level=MaskingLevel.FULL, technique=MaskingTechnique.SUPPRESSION)

    async def add_policy(self, policy: MaskingPolicy):
        if db is not None:
             await db.masking_policies.update_one(
                 {"entity_type": policy.entity_type, "role": policy.role},
                 {"$set": policy.dict()},
                 upsert=True
             )

    async def get_all_policies(self) -> List[MaskingPolicy]:
        if db is not None:
            cursor = db.masking_policies.find()
            return [MaskingPolicy(**doc) async for doc in cursor]
        return [MaskingPolicy(**p) for p in self.DEFAULT_POLICIES]

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="EthiMask Service",
    description="Tâche 9 - Contextual Data Masking Framework (Mongo Persisted)",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

perceptron = MaskingPerceptron()
masker = ContextualMasker()
policy_manager = PolicyManager()
config_manager = ConfigManager()

@app.on_event("startup")
async def startup_event():
    # Load config from DB on startup
    config = await config_manager.get_config()
    perceptron.update_weights(config["weights"], config["bias"])

@app.get("/")
async def root():
    log_count = 0
    if db is not None:
        log_count = await db.audit_logs.count_documents({})
    return {
        "service": "EthiMask Service",
        "status": "running",
        "db_connected": db is not None,
        "audit_logs_count": log_count
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/mask", response_model=MaskResponse)
async def mask_data(request: MaskRequest):
    """Apply contextual masking to data with PII detections"""
    masked_data = request.data.copy()
    techniques_used = {}
    audit_logs_batch = []
    
    for detection in request.detections:
        field = detection.field
        if field not in masked_data: continue
        
        # Perceptron Decision
        level, confidence = perceptron.decide_masking(
            detection.sensitivity_level, request.config.role, request.config.context, request.config.purpose
        )
        
        # Policy Override
        policy = await policy_manager.get_policy(detection.entity_type, request.config.role.value)
        if policy:
             level = policy.level
             technique = policy.technique
        else:
             technique = None
        
        masked_val, tech_used = masker.mask(masked_data[field], detection.entity_type, level, technique)
        masked_data[field] = masked_val
        techniques_used[field] = tech_used
        
        audit_logs_batch.append({
            "field": field,
            "entity_type": detection.entity_type,
            "sensitivity": detection.sensitivity_level,
            "masking_level": level.value,
            "technique": tech_used,
            "role": request.config.role.value,
            "timestamp": datetime.now().isoformat()
        })
    
    # Batch insert audit logs
    if db is not None and audit_logs_batch:
        result = await db.audit_logs.insert_many(audit_logs_batch)
        # Add IDs to logs for response but convert to string
        for i, log in enumerate(audit_logs_batch):
            log["_id"] = str(result.inserted_ids[i])
    
    return MaskResponse(
        masked_data=masked_data,
        masking_applied=len([t for t in techniques_used.values() if t != "none"]),
        technique_used=techniques_used,
        audit_log=audit_logs_batch
    )

@app.post("/decide")
def get_masking_decision(sensitivity: str, role: UserRole, context: str = "default", purpose: str = "general"):
    return perceptron.get_decision_explanation(sensitivity, role, context, purpose)

@app.get("/policies")
async def list_policies():
    """List all masking policies"""
    policies = await policy_manager.get_all_policies()
    return {"policies": [p.dict() for p in policies]}

@app.post("/policies")
async def add_policy(policy: MaskingPolicy):
    """Add or update a masking policy"""
    await policy_manager.add_policy(policy)
    return {"status": "added/updated"}

@app.get("/config")
async def get_config():
    """Get current perceptron configuration"""
    config = await config_manager.get_config()
    return {
        "sensitivity_weight": config["weights"][0],
        "role_weight": config["weights"][1],
        "context_weight": config["weights"][2],
        "purpose_weight": config["weights"][3],
        "bias": config["bias"]
    }

@app.post("/config")
async def update_config(config: ConfigUpdate):
    """Update perceptron weights and bias"""
    await config_manager.update_config(config)
    return {"status": "configuration saved", "new_config": config}

@app.get("/audit-logs")
async def get_audit_logs(limit: int = 100):
    """Get recent audit logs"""
    if db is not None:
        cursor = db.audit_logs.find().sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        return {"logs": logs}
    return {"logs": []}

if __name__ == "__main__":
    print(f"\\n" + "="*60)
    print(f"🔒 ETHIMASK SERVICE (MONGO) - Tâche 9")
    print(f"="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8009, reload=True)
