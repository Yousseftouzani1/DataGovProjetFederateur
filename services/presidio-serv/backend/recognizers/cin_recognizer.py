import re
from typing import List, Optional
from presidio_analyzer import Pattern
from backend.recognizers.moroccan_base_recognizer import MoroccanPatternRecognizer


class MoroccanCINRecognizer(MoroccanPatternRecognizer):
    """
    Recognizer for Moroccan CIN (Carte d'Identité Nationale)
    Algorithm 3 Compliant (Weighted Scoring)
    """
    
    PATTERNS = [
        # CIN with spaces (e.g., "AB 123 456")
        Pattern(
            "CIN_MAROC_SPACED",
            r"\b[A-Z]{1,2}\s*\d{3}\s*\d{3,5}\b",
            0.40 # Lowered to require context for threshold 0.5
        ),
        # Standard CIN (requires 6-8 digits to ensure specificity)
        Pattern(
            "CIN_MAROC_FULL",
            r"\b[A-Z]{1,2}\d{6,8}\b",
            0.40 # Lowered to require context for threshold 0.5
        ),
    ]

    CONTEXT = [
        "cin", "carte", "identité", "national", "بطاقة", "التعريف", "الوطنية"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "CIN_MAROC",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        
        # Validator for Algorithm 3: check length 6-8 after letter prefix
        def cin_validator(text: str) -> bool:
            clean_text = re.sub(r"\s+", "", text).upper()
            digits_only = re.sub(r"[A-Z]", "", clean_text)
            return 6 <= len(digits_only) <= 8

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
            validator=cin_validator
        )
import re
