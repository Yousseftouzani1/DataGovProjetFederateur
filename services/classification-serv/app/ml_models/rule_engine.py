
import re

class RuleEngine:
    """
    Expert 1: Pattern Features (Regex)
    Detects standard formats with 100% certainty.
    """
    
    PATTERNS = {
        "EMAIL": r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
        "IBAN": r"^FR\d{2}[ ]\d{4}[ ]\d{4}[ ]\d{4}[ ]\d{4}[ ]\d{2}|MA\d{2}[ ]\d{24}$", # FR or MA format
        "PHONE_MA": r"^(?:\+212|0)[67]\d{8}$",
        "CIN": r"^[A-Z]{1,2}\d{6}$"
    }
    
    # Mapping Regex matches to Sensitivity Levels (0-5)
    # Public=0, Internal=1, Confidential=2, PII=3, SPI=4, Critical=5
    CLASS_MAP = {
        "EMAIL": 3,   # PII
        "IBAN": 5,    # CRITICAL (Banking)
        "PHONE_MA": 3,# PII
        "CIN": 3      # PII (could be 5 if critical content, but usually Strong ID)
    }

    def predict(self, sample_values: list) -> dict:
        """
        Returns {predicted_class: int/None, confidence: float}
        """
        if not sample_values:
            return {"class": None, "confidence": 0.0}
            
        matches = {k: 0 for k in self.PATTERNS.keys()}
        total_valid = 0
        
        for val in sample_values:
            val_str = str(val).strip()
            if not val_str: continue
            total_valid += 1
            
            for name, pattern in self.PATTERNS.items():
                if re.match(pattern, val_str):
                    matches[name] += 1
        
        if total_valid == 0:
             return {"class": None, "confidence": 0.0}

        # Check if any pattern dominates (> 80% matches)
        for name, count in matches.items():
            ratio = count / total_valid
            if ratio > 0.8:
                return {
                    "class": self.CLASS_MAP[name],
                    "confidence": 1.0, # Rule engines are very confident
                    "reason": f"Matched pattern {name}"
                }
                
        return {"class": None, "confidence": 0.0}
