"""
Moroccan Phone Number Recognizer for Microsoft Presidio
Detects Moroccan mobile and landline phone numbers
Formats: +212, 00212, 0 followed by 5/6/7 + 8 digits
"""
import re
from typing import List, Optional
from presidio_analyzer import Pattern
from backend.recognizers.moroccan_base_recognizer import MoroccanPatternRecognizer


class MoroccanPhoneRecognizer(MoroccanPatternRecognizer):
    """
    Recognizer for Moroccan Phone Numbers
    Algorithm 3 Compliant (Weighted Scoring)
    """
    
    PATTERNS = [
        Pattern(
            "PHONE_MA_INTERNATIONAL",
            r"\+212[5-7]\d{8}",
            0.40 # Lowered to require context
        ),
        Pattern(
            "PHONE_MA_INTERNATIONAL_00",
            r"00212[5-7]\d{8}",
            0.40 # Lowered to require context
        ),
        Pattern(
            "PHONE_MA_LOCAL",
            r"\b0[5-7]\d{8}\b",
            0.40 # Lowered to require context
        ),
        # Phone with spaces (e.g., "0612 345 678")
        Pattern(
            "PHONE_MA_LOCAL_SPACED", 
            r"\b0[5-7]\d{2}\s*\d{3}\s*\d{3}\b",
            0.40 # Lowered to require context
        ),
        Pattern(
            "PHONE_MA_SPACED",
            r"\+212[\s.-]?[5-7][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}",
            0.40 # Lowered to require context
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
        supported_language: str = "en",
        supported_entity: str = "PHONE_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        
        # Validator for Algorithm 3: check length and prefix
        def phone_validator(text: str) -> bool:
            clean_text = re.sub(r"[\s.+-]", "", text)
            # Remove 212 or 00212 or leading 0
            if clean_text.startswith("00212"): clean_text = clean_text[5:]
            elif clean_text.startswith("212"): clean_text = clean_text[3:]
            elif clean_text.startswith("0"): clean_text = clean_text[1:]
            
            return len(clean_text) == 9 and clean_text[0] in "567"

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
            validator=phone_validator
        )
import re

