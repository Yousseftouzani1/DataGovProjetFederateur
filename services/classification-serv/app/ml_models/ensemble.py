
from .random_forest import RandomForestAdapter
from .bert_classifier import BertClassifierAdapter
from .rule_engine import RuleEngine
import numpy as np

class EnsembleClassifier:
    """
    Expert 4: The Judge (Algorithm 5)
    Combines votes from RF, BERT, and Rules.
    """
    
    def __init__(self):
        self.rf = RandomForestAdapter()
        self.bert = BertClassifierAdapter()
        self.rules = RuleEngine()
        
        # Weights (Tuned via manual feedback, US-CLASS-02)
        self.weights = {
            "RuleEngine": 3.0,     # Patterns are definitive (IBAN is IBAN)
            "BertClassifier": 2.0, # Semantic is strong
            "RandomForest": 1.0    # Statistical is weakest
        }
        
        # Threshold for manual review
        self.manual_review_threshold = 0.8

    def classify_column(self, col_name: str, values: list) -> dict:
        """
        Executes Algorithm 5: Weighted Voting.
        """
        # 1. Get Predictions
        # Rules need raw values
        p_rules = self.rules.predict(values)
        
        # RF needs raw values (extracts features internally)
        p_rf = self.rf.predict(values)
        
        # BERT needs text context (col name + values)
        # We prepend col_name to give context
        # e.g. "Phone 0661..."
        bert_input = [col_name] + [str(v) for v in values if v][:5]
        p_bert = self.bert.predict(bert_input)
        
        # 2. Weighted Vote
        # Votes for classes 0-5
        votes = np.zeros(6) 
        
        # Add votes if model is confident
        if p_rules["class"] is not None:
            votes[p_rules["class"]] += self.weights["RuleEngine"] * p_rules["confidence"]
            
        if p_rf["class"] is not None:
            votes[p_rf["class"]] += self.weights["RandomForest"] * p_rf["confidence"]
            
        if p_bert["class"] is not None:
            votes[p_bert["class"]] += self.weights["BertClassifier"] * p_bert["confidence"]
            
        # 3. Final Decision
        total_weight = sum([self.weights["RuleEngine"] if p_rules["class"] is not None else 0,
                            self.weights["RandomForest"] if p_rf["class"] is not None else 0,
                            self.weights["BertClassifier"] if p_bert["class"] is not None else 0])
        
        if total_weight == 0:
            # Fallback to PUBLIC if no one matched
            return {"level": 0, "code": "PUBLIC", "confidence": 0.0, "review": True}

        pred_class = int(np.argmax(votes))
        
        # Normalized confidence approx
        confidence = votes[pred_class] / total_weight if total_weight > 0 else 0.0
        
        # Label Map
        LABELS = {0: "PUBLIC", 1: "INTERNAL", 2: "CONFIDENTIAL", 3: "PII", 4: "SPI", 5: "CRITICAL"}
        
        result = {
            "level": int(pred_class),
            "code": str(LABELS.get(int(pred_class), "UNKNOWN")),
            "confidence": round(float(confidence), 2),
            "review": bool(confidence < self.manual_review_threshold),
            # "details": {
            #    "rules": p_rules,
            #    "rf": p_rf,
            #    "bert": p_bert
            # }
        }
        
        return result

    def fit(self):
        """
        US-CLASS-03: Placeholder for retraining logic.
        """
        print("🔄 Retraining Ensemble Classifier...")
        # In real scenario, would trigger rf.fit() and bert.fit()
        return True
