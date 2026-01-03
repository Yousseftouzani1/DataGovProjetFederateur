"""
Moroccan Presidio Recognizers
Custom PII recognizers for Moroccan context
"""
from .cin_recognizer import MoroccanCINRecognizer
from .phone_ma_recognizer import MoroccanPhoneRecognizer
from .iban_ma_recognizer import MoroccanIBANRecognizer
from .cnss_recognizer import MoroccanCNSSRecognizer
from .arabic_recognizer import ArabicMoroccanRecognizer
from .passport_ma_recognizer import MoroccanPassportRecognizer
from .permis_ma_recognizer import MoroccanPermisRecognizer

__all__ = [
    "MoroccanCINRecognizer",
    "MoroccanPhoneRecognizer",
    "MoroccanIBANRecognizer",
    "MoroccanCNSSRecognizer",
    "ArabicMoroccanRecognizer",
    "MoroccanPassportRecognizer",
    "MoroccanPermisRecognizer",
]

