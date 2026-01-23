import re
from typing import List, Optional
from presidio_analyzer import Pattern
from .moroccan_base_recognizer import MoroccanPatternRecognizer


class MoroccanCNSSRecognizer(MoroccanPatternRecognizer):
    """
    Recognizer for Moroccan CNSS (Caisse Nationale de Sécurité Sociale)
    Algorithm 3 Compliant (Weighted Scoring)
    """
    
    PATTERNS = [
        Pattern(
            "CNSS",
            r"\b\d{9,12}\b",
            0.05 # Aggressively lowered to MANDATE context (Score w/o context < 0.3)
        ),
    ]
    
    CONTEXT = [
        "cnss", "sécurité sociale", "caisse nationale", 
        "cotisation", "immatriculation", "الضمان", "الاجتماعي", "الصندوق"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "CNSS",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
