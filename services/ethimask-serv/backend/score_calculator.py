import numpy as np
from enum import Enum
from typing import List, Dict, Tuple, Optional

class UserRole(str, Enum):
    ADMIN = "admin"                 # Full access
    DATA_STEWARD = "steward"        # Partial access
    DATA_ANNOTATOR = "annotator"    # Limited access
    DATA_LABELER = "labeler"        # Minimal access
    ANALYST = "analyst"             # Aggregated access only
    EXTERNAL = "external"           # No PII access

class MaskingLevel(str, Enum):
    NONE = "none"           # No masking (full access)
    PARTIAL = "partial"     # Partial masking (show some info)
    FULL = "full"           # Full masking (replace with placeholder)
    ENCRYPTED = "encrypted" # Homomorphic encryption

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
