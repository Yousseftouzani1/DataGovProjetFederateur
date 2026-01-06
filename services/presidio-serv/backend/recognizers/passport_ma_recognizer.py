import re
from typing import List, Optional
from presidio_analyzer import Pattern
from .moroccan_base_recognizer import MoroccanPatternRecognizer


class MoroccanPassportRecognizer(MoroccanPatternRecognizer):
    """
    Recognizer for Moroccan Passport Numbers
    Algorithm 3 Compliant (Weighted Scoring)
    """
    
    PATTERNS = [
        # Standard passport format
        Pattern(
            "PASSPORT_MA",
            r"\b[A-Z]{2}\d{6,7}\b",
            0.30 # Lowered to require context
        ),
    ]
    
    CONTEXT = [
        "passeport", "passport", "جواز", "السفر", "voyage", "travel"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "PASSPORT_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        
        # Validator: check length and prefix
        def passport_validator(text: str) -> bool:
            return bool(re.match(r"^[A-Z]{2}\d{6,7}$", text.strip().upper()))

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
            validator=passport_validator
        )

