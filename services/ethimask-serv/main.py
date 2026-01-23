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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database.mongodb import db
from backend.score_calculator import MaskingPerceptron, UserRole, MaskingLevel
from backend.masking_techniques import ContextualMasker, MaskingTechnique

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

class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MaskingConfig(BaseModel):
    role: UserRole = UserRole.DATA_LABELER
    context: str = "default"  # Context: analysis, export, display, api
    purpose: str = "general"  # Purpose: research, compliance, marketing
    history_stats: Optional[Dict[str, float]] = {
        "conformity": 0.8, # Hc
        "frequency": 0.5,  # Hf
        "violations": 0.0  # Hv
    }

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
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Loss function balance: alpha * Privacy + (1-alpha) * Utility")

class ConfigManager:
    DEFAULT_CONFIG = {
        "weights": [0.35, -0.30, 0.20, 0.15],
        "bias": 0.4,
        "alpha": 0.5
    }

    async def get_config(self) -> Dict:
        if db is not None:
            doc = await db.ethimask_config.find_one({"_id": "global_config"})
            if doc:
                return {"weights": doc["weights"], "bias": doc["bias"], "alpha": doc.get("alpha", 0.5)}
        return self.DEFAULT_CONFIG

    async def update_config(self, config: ConfigUpdate):
        # Map frontend fields to perceptron weights order: [sensitivity, role, context, purpose]
        new_weights = [config.ws, config.wr, config.wc, config.wp]
        if db is not None:
            await db.ethimask_config.update_one(
                {"_id": "global_config"},
                {"$set": {"weights": new_weights, "bias": config.bias, "alpha": config.alpha}},
                upsert=True
            )
        # Update in-memory perceptron
        perceptron.update_weights(new_weights, config.bias)

# ====================================================================
# POLICY MANAGER (MONGO PERSISTED)
# ====================================================================

class PolicyManager:
    DEFAULT_POLICIES = [
        {"entity_type": "*", "role": "admin", "level": "none", "technique": "pseudonymization"},
        {"entity_type": "cin", "role": "steward", "level": "partial", "technique": "pseudonymization"},
        # Changed Labeler to Encrypted to demonstrate HE in Demo
        {"entity_type": "*", "role": "labeler", "level": "encrypted", "technique": "encryption"},
        # Annotator default
        {"entity_type": "*", "role": "annotator", "level": "partial", "technique": "generalization"},
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

        # Default fallback if no policy matches
        # return MaskingPolicy(entity_type=entity_type, role=role, level=MaskingLevel.FULL, technique=MaskingTechnique.SUPPRESSION)
        return None

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

@app.middleware("http")
async def set_root_path(request: Request, call_next):
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    return response

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
            detection.sensitivity_level, 
            request.config.role, 
            request.config.context, 
            request.config.purpose,
            history=request.config.history_stats
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
        "purpose_weight": config["weights"][3],
        "bias": config["bias"],
        "alpha": config["alpha"]
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

@app.get("/audit")
async def get_masking_audit_report(
    limit: int = 100, 
    role: Optional[str] = None, 
    entity_type: Optional[str] = None
):
    """
    US-MASK-04: Specialized Masking Audit Report
    Filterable by Role and Entity Type to analyze masking decisions.
    """
    if db is None:
        return {"logs": []}
    
    query = {}
    if role:
        query["role"] = role
    if entity_type:
        query["entity_type"] = entity_type
        
    cursor = db.audit_logs.find(query).sort("timestamp", -1).limit(limit)
    logs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)
    
    return {"count": len(logs), "filters": {"role": role, "entity_type": entity_type}, "logs": logs}

@app.post("/retrain")
async def retrain_on_audit_logs():
    """
    US-MASK-06: Automatic Pattern Learning
    Analyzes historical audit logs to refine weights.
    High violation counts -> Increase Sensitivity weight.
    High success rates -> Increase Role Trust.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    # 1. Fetch recent audit logs (last 500)
    cursor = db.audit_logs.find().sort("timestamp", -1).limit(500)
    logs = [doc async for doc in cursor]

    if not logs:
        return {"status": "skipped", "message": "No logs available for training"}

    # 2. Simple Heuristic Learning (Simulation of Perceptron update)
    # Feature influences
    sensitivity_shift = 0.0
    role_shift = 0.0
    
    for log in logs:
        level = log.get("masking_level")
        sens = log.get("sensitivity")
        
        # If we are masking a lot of HIGH sensitivity data, we might want to be more cautious
        if sens in ["high", "critical"] and level == "none":
            # Potential false negative (access allowed where it should be masked)
            sensitivity_shift += 0.01
        
        # If we are masking LOW sensitivity for ADMIN, we might be too restrictive
        if sens == "low" and log.get("role") == "admin" and level != "none":
            role_shift += 0.01

    # 3. Apply updates to current config
    config = await config_manager.get_config()
    weights = config["weights"]
    weights[0] = min(1.0, max(-1.0, weights[0] + sensitivity_shift)) # ws
    weights[1] = min(1.0, max(-1.0, weights[1] + role_shift))        # wr
    
    new_config = ConfigUpdate(ws=weights[0], wr=weights[1], wc=weights[2], wp=weights[3], bias=config["bias"])
    await config_manager.update_config(new_config)

    return {
        "status": "success", 
        "message": f"Retrained on {len(logs)} samples",
        "updates": {
            "sensitivity_weight": weights[0],
            "role_trust_weight": weights[1]
        }
    }

@app.post("/he/context")
async def initialize_he_context():
    """
    Initialize Homomorphic Encryption Context (TenSEAL)
    Mandatory Task for Admin to enable HE capabilities.
    """
    if not TENSEAL_AVAILABLE:
        # Mock success if TenSEAL is missing to prevent UI errors in dev
        return {"status": "mock_initialized", "scheme": "CKKS", "poly_modulus_degree": 8192}

    try:
        # Create a real TenSEAL context
        context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[60, 40, 40, 60]
        )
        context.global_scale = 2**40
        context.generate_galois_keys()
        
        # In a real app, we would persist this context (public keys) to DB or filesystem
        # For now, we simulate the setup success
        return {
            "status": "initialized",
            "scheme": "CKKS",
            "poly_modulus_degree": 8192,
            "security_level": "128-bit"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to init TenSEAL: {str(e)}")

if __name__ == "__main__":
    print(f"\\n" + "="*60)
    print(f"🔒 ETHIMASK SERVICE (MONGO) - Tâche 9")
    print(f"="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8009, reload=True)
