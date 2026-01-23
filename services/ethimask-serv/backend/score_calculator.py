import numpy as np
from enum import Enum
from typing import List, Dict, Tuple, Optional

class UserRole(str, Enum):
    ADMIN = "admin"                 # Full access
    DATA_STEWARD = "steward"        # Partial access
    DATA_ANNOTATOR = "annotator"    # Limited access
    DATA_LABELER = "labeler"        # Minimal access/HE

class MaskingLevel(str, Enum):
    NONE = "none"           # No masking (full access)
    PARTIAL = "partial"     # Partial masking (show some info)
    FULL = "full"           # Full masking (replace with placeholder)
    ENCRYPTED = "encrypted" # Homomorphic encryption
    DIFFERENTIAL_PRIVACY = "differential_privacy" # Differential Privacy

class MaskingPerceptron:
    def __init__(self):
        # Weights: [Sensitivity, Role, Context, Purpose, Hc, Hf, Hv]
        # Role and Sensitivity are dominant.
        # Positive score -> Open Access. Negative/Low score -> Masking.
        self.weights = np.array([0.4, 0.5, 0.1, 0.1, 0.1, -0.1, -0.2])
        self.bias = 0.2 # Positive bias to help low-tier roles reach > 0.15
        
        # Encoding: High value = High Trust/Safety
        self.sensitivity_encoding = {"low": 1.0, "medium": 0.5, "high": 0.2, "critical": 0.0}
        
        # CDC Roles Trust Hierarchy
        self.role_encoding = {
            UserRole.DATA_STEWARD: 1.0,     # Max Trust (Guardian of Governance)
            UserRole.ADMIN: 0.9,            # High Trust (System Admin)
            UserRole.DATA_ANNOTATOR: 0.5,   # Medium Trust (Validation)
            UserRole.DATA_LABELER: 0.1      # Low Trust (Entry Level, Restricted)
        }
        
        self.context_encoding = {"internal": 0.9, "analysis": 0.8, "display": 0.6, "export": 0.4, "api": 0.5, "external": 0.2, "default": 0.5}
        self.purpose_encoding = {"internal_research": 0.8, "compliance": 0.9, "research": 0.7, "general": 0.5, "marketing": 0.3, "third_party": 0.1}

    def update_weights(self, weights: List[float], bias: float):
        # Expecting complete weight vector
        if len(weights) == 7:
             self.weights = np.array(weights)
             self.bias = bias

    def encode_features(self, sensitivity, role, context, purpose, hc=0.8, hf=0.5, hv=0.0):
        # Hc: Conformity (0-1), Hf: Access Frequency (0-1), Hv: Violations (0-1)
        return np.array([
            self.sensitivity_encoding.get(sensitivity.lower(), 0.5),
            self.role_encoding.get(role, 0.5),
            self.context_encoding.get(context.lower(), 0.5),
            self.purpose_encoding.get(purpose.lower(), 0.5),
            hc, # Historic Conformity
            hf, # Access Frequency
            hv  # Violation History
        ])

    def decide_masking(self, sensitivity: str, role: UserRole, context: str = "default", purpose: str = "general", history: Dict = None) -> Tuple[MaskingLevel, float]:
        if history is None: history = {}
        hc = history.get("conformity", 0.9) # Assume good unless known
        hf = history.get("frequency", 0.2)
        hv = history.get("violations", 0.0)

        features = self.encode_features(sensitivity, role, context, purpose, hc, hf, hv)
        
        # Eq (11): Score T' = Sigmoid(W*X + b)
        logit = np.dot(features, self.weights) + self.bias
        score = 1 / (1 + np.exp(-logit))

        print(f"DEBUG: Role={role}, Sens={sensitivity}, Features={features}")
        print(f"DEBUG: Weights={self.weights}, Bias={self.bias}")
        print(f"DEBUG: Logit={logit}, Score={score}")
        
        # Mapping Score -> Level (CDC 11.4)
        # [0.85, 1.0] -> Full Access (Level 0)
        # [0.65, 0.85[ -> Anonymization (Level 1 - HE)
        # [0.45, 0.65[ -> Generalization (Level 2)
        # [0.25, 0.45[ -> Differential Privacy (Level 3)
        # [0, 0.25[    -> Suppression (Level 4)
        
        if score >= 0.80: return MaskingLevel.NONE, score
        elif score >= 0.60: return MaskingLevel.PARTIAL, score   # Level 2 (Generalization)
        elif score >= 0.40: return MaskingLevel.DIFFERENTIAL_PRIVACY, score # Level 3 (Annotator Range)
        elif score >= 0.15: return MaskingLevel.ENCRYPTED, score # Level 1 (Labeler Range - Security via HE)
        else: return MaskingLevel.FULL, score                    # Level 4 (Suppression)
        
        # Note: In our Enum, we need to map strictly:
        # Level 0 = MEANING.NONE
        # Level 1 = ENCRYPTED (HE)
        # Level 2 = PARTIAL (Generalization)
        # Level 3 = DP (We will reuse PARTIAL or add DP enum ?? Let's use PARTIAL+Technique)
        # Level 4 = FULL (Suppression)

    def get_decision_explanation(self, sensitivity: str, role: UserRole, context: str, purpose: str) -> Dict:
        features = self.encode_features(sensitivity, role, context, purpose)
        level, score = self.decide_masking(sensitivity, role, context, purpose)
        contributions = features * self.weights
        return {
            "decision": level.value, "score": round(score, 3),
            "feature_contributions": {
                "sensitivity": round(contributions[0], 3), "role": round(contributions[1], 3),
                "context": round(contributions[2], 3), "purpose": round(contributions[3], 3),
                "history": round(sum(contributions[4:]), 3)
            }
        }
