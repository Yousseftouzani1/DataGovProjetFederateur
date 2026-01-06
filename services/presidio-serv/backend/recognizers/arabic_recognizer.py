import re
from typing import List, Optional
from presidio_analyzer import Pattern
from .moroccan_base_recognizer import MoroccanPatternRecognizer


class ArabicMoroccanRecognizer(MoroccanPatternRecognizer):
    """
    Comprehensive Arabic language recognizer for Moroccan PII entities
    Algorithm 3 Compliant (Weighted Scoring)
    Supports: CIN, Phone, IBAN, CNSS, Passport
    """
    
    PATTERNS = [
        # We only keep patterns that might be uniquely Arabic or have very high specificity
        # Redundant ones (CIN, Phone) are now handled by specialized recognizers in 'ar' mode.
        
        # ========== CNSS Patterns (Arabic specific if needed) ==========
        Pattern(name="cnss_arabic", regex=r"\b\d{9,12}\b", score=0.3),
    ]
    
    CONTEXT_WORDS = [
        "رقم", "البطاقة", "الوطنية", "الهاتف", "الجوال",
        "الحساب", "البنكي", "الضمان", "الاجتماعي",
        "جواز", "السفر", "الباسبور"
    ]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ar",
        supported_entity: str = "ARABIC_MOROCCAN_PII",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT_WORDS
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
    
    def analyze(self, text: str, entities: List[str], nlp_artifacts=None):
        """Override to add Arabic-specific logic and maintain Algorithm 3 scoring"""
        results = super().analyze(text, entities, nlp_artifacts)
        
        # Map to specific entity types and return
        for result in results:
            pos = result.start
            context_area = text[max(0, pos-50):min(len(text), pos+100)]
            
            # Identify entity type from context
            if any(keyword in context_area for keyword in ["البطاقة", "ب.و.ت"]):
                result.entity_type = "CIN_MAROC"
            elif any(keyword in context_area for keyword in ["الهاتف", "الجوال", "رقم"]):
                result.entity_type = "PHONE_MA"
            elif any(keyword in context_area for keyword in ["الحساب", "IBAN", "RIB"]):
                result.entity_type = "IBAN_MA"
            elif any(keyword in context_area for keyword in ["الضمان", "CNSS"]):
                result.entity_type = "CNSS"
            elif any(keyword in context_area for keyword in ["جواز", "الباسبور"]):
                result.entity_type = "PASSPORT_MA"
        
        return results

