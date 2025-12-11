"""
Moroccan CIN Recognizer for Microsoft Presidio
Detects Moroccan National ID Cards (Carte d'Identité Nationale)
Format: 1-2 letters + 5-8 digits (e.g., AB123456, J123456)
"""
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class MoroccanCINRecognizer(PatternRecognizer):
    """
    Recognizer for Moroccan CIN (Carte d'Identité Nationale)
    Formats supported:
    - AB123456 (2 letters + 6 digits)
    - A123456 (1 letter + 6 digits)
    - BE123456 (2 letters + 6 digits)
    """
    
    PATTERNS = [
        Pattern(
            "CIN_MAROC_FULL",
            r"\b[A-Z]{1,2}\d{5,8}\b",
            0.85
        ),
        Pattern(
            "CIN_MAROC_CONTEXT",
            r"(?:CIN|C\.I\.N|carte\s*d'identité|بطاقة\s*التعريف)[:\s]*([A-Z]{1,2}\d{5,8})",
            0.95
        ),
    ]
    
    CONTEXT = [
        "cin", "carte", "identité", "national", "بطاقة", "التعريف", "الوطنية"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "fr",
        supported_entity: str = "CIN_MAROC",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
