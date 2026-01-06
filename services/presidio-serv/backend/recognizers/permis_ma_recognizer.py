import re
from typing import List, Optional
from presidio_analyzer import Pattern
from .moroccan_base_recognizer import MoroccanPatternRecognizer


class MoroccanPermisRecognizer(MoroccanPatternRecognizer):
    """
    Recognizer for Moroccan Driving License (Permis de Conduire)
    Algorithm 3 Compliant (Weighted Scoring)
    """
    
    PATTERNS = [
        # Permis code format (alphanumeric 6-12 chars, must contain at least one digit)
        Pattern(
            "PERMIS_MA",
            r"\b(?=[A-Z]*\d)[A-Z0-9]{6,12}\b",
            0.20 # Very specific context required
        ),
    ]
    
    CONTEXT = [
        "permis", "conduire", "conduite", "رخصة", "القيادة", "driving", "license"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "PERMIS_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        
        # Validator for Algorithm 3: check length and alphanumeric format
        def permis_validator(text: str) -> bool:
            return bool(re.match(r"^[A-Z0-9]{6,12}$", text.strip().upper()))

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
            validator=permis_validator
        )

