"""
Moroccan Phone Number Recognizer for Microsoft Presidio
Detects Moroccan mobile and landline phone numbers
Formats: +212, 00212, 0 followed by 5/6/7 + 8 digits
"""
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class MoroccanPhoneRecognizer(PatternRecognizer):
    """
    Recognizer for Moroccan Phone Numbers
    Formats supported:
    - +212 6XX XXX XXX (mobile)
    - +212 5XX XXX XXX (fixed)
    - 06XX XXX XXX (mobile local)
    - 05XX XXX XXX (fixed local)
    """
    
    PATTERNS = [
        Pattern(
            "PHONE_MA_INTERNATIONAL",
            r"\+212[5-7]\d{8}",
            0.9
        ),
        Pattern(
            "PHONE_MA_INTERNATIONAL_00",
            r"00212[5-7]\d{8}",
            0.9
        ),
        Pattern(
            "PHONE_MA_LOCAL",
            r"\b0[5-7]\d{8}\b",
            0.7
        ),
        Pattern(
            "PHONE_MA_SPACED",
            r"\+212[\s.-]?[5-7][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}",
            0.85
        ),
    ]
    
    CONTEXT = [
        "téléphone", "tel", "tél", "phone", "mobile", "gsm", 
        "appeler", "contact", "الهاتف", "رقم"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "fr",
        supported_entity: str = "PHONE_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
