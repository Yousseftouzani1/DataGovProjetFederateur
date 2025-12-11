"""
Moroccan Presidio Recognizers
Custom PII recognizers for Moroccan context
"""
from .cin_recognizer import MoroccanCINRecognizer
from .phone_ma_recognizer import MoroccanPhoneRecognizer
from .iban_ma_recognizer import MoroccanIBANRecognizer
from .cnss_recognizer import MoroccanCNSSRecognizer

__all__ = [
    "MoroccanCINRecognizer",
    "MoroccanPhoneRecognizer",
    "MoroccanIBANRecognizer",
    "MoroccanCNSSRecognizer",
]
