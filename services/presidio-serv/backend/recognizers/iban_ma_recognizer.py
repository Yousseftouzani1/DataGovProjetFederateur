"""
Moroccan IBAN Recognizer for Microsoft Presidio
Detects Moroccan bank account IBAN numbers
Format: MA + 24 alphanumeric characters
"""
import re
from typing import List, Optional
from presidio_analyzer import Pattern
from backend.recognizers.moroccan_base_recognizer import MoroccanPatternRecognizer


class MoroccanIBANRecognizer(MoroccanPatternRecognizer):
    """
    Recognizer for Moroccan IBAN
    Algorithm 3 Compliant (Weighted Scoring)
    """
    
    PATTERNS = [
        # IBAN with alphanumeric characters (MA + 2 digits + 24 alphanumeric)
        Pattern(
            "IBAN_MA",
            r"\bMA\d{2}[A-Z0-9]{20,30}\b",
            0.60 # Lowered to increase safety
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
        supported_language: str = "en",
        supported_entity: str = "IBAN_MA",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        
        def iban_validator(text: str) -> bool:
            """
            Standard IBAN Validation (MOD-97)
            """
            clean_text = re.sub(r"\s+", "", text).upper()
            if not clean_text.startswith("MA") or len(clean_text) < 24:
                return False
            
            # 1. Move first 4 characters to the end
            # 2. Convert letters to digits (A=10, B=11, ..., Z=35)
            # 3. Compute mod 97
            rearranged = clean_text[4:] + clean_text[:4]
            digits = ""
            for char in rearranged:
                if char.isdigit():
                    digits += char
                else:
                    digits += str(ord(char) - ord('A') + 10)
            
            try:
                # Standard IBAN mod-97: digits % 97 == 1
                return int(digits) % 97 == 1
            except ValueError:
                return False

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
            validator=iban_validator
        )
import re

