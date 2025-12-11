"""
Moroccan CNSS Recognizer for Microsoft Presidio
Detects Moroccan Social Security Numbers (CNSS)
Format: 9-12 digit number
"""
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class MoroccanCNSSRecognizer(PatternRecognizer):
    """
    Recognizer for Moroccan CNSS (Caisse Nationale de Sécurité Sociale)
    Format: 9-12 digit number
    """
    
    PATTERNS = [
        Pattern(
            "CNSS_MA_CONTEXT",
            r"(?:CNSS|sécurité\s*sociale|الضمان\s*الاجتماعي|الصندوق\s*الوطني)[:\s]*(\d{9,12})",
            0.95
        ),
        Pattern(
            "CNSS_MA_SIMPLE",
            r"\b\d{9,12}\b",
            0.3  # Low confidence without context
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
        supported_language: str = "fr",
        supported_entity: str = "CNSS_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
