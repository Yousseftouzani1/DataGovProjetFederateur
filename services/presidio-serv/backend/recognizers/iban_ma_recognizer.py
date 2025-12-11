"""
Moroccan IBAN Recognizer for Microsoft Presidio
Detects Moroccan bank account IBAN numbers
Format: MA + 24 alphanumeric characters
"""
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class MoroccanIBANRecognizer(PatternRecognizer):
    """
    Recognizer for Moroccan IBAN
    Format: MA + 2 check digits + 24 characters
    Example: MA64 0110 0785 0001 2300 0000 0001
    """
    
    PATTERNS = [
        Pattern(
            "IBAN_MA_FULL",
            r"\bMA\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}\b",
            0.95
        ),
        Pattern(
            "IBAN_MA_COMPACT",
            r"\bMA\d{24}\b",
            0.9
        ),
        Pattern(
            "IBAN_MA_CONTEXT",
            r"(?:IBAN|compte\s*bancaire|الحساب\s*البنكي)[:\s]*(MA\d{2}[A-Z0-9\s]{20,26})",
            0.95
        ),
    ]
    
    CONTEXT = [
        "iban", "compte", "bancaire", "banque", "virement", 
        "rib", "bank", "الحساب", "البنك"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "fr",
        supported_entity: str = "IBAN_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
