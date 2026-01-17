"""
International PII Recognizers
Supports: Chinese, Japanese, Korean, Russian, Hindi, Hebrew, German, French
"""
import re
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class ChineseIDRecognizer(PatternRecognizer):
    """
    Recognizes Chinese National ID (身份证号码)
    Format: 18 digits, last can be X
    Example: 110101199001011234
    """
    PATTERNS = [
        Pattern(
            "CHINESE_ID_18",
            r"\b[1-6]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
            0.85,
        ),
        Pattern(
            "CHINESE_ID_15",
            r"\b[1-6]\d{5}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}\b",
            0.7,
        ),
    ]
    CONTEXT = ["身份证", "id", "身份", "证号", "chinese id", "national id"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="CHINESE_NATIONAL_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class ChinesePhoneRecognizer(PatternRecognizer):
    """
    Recognizes Chinese Phone Numbers
    Format: +86 followed by 11 digits, or 11 digits starting with 1
    """
    PATTERNS = [
        Pattern(
            "CHINESE_MOBILE",
            r"\b(?:\+86)?1[3-9]\d{9}\b",
            0.7,
        ),
        Pattern(
            "CHINESE_MOBILE_SPACED",
            r"\b(?:\+86[\s-]?)?1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}\b",
            0.65,
        ),
    ]
    CONTEXT = ["电话", "手机", "phone", "mobile", "联系"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="CHINESE_PHONE",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class ChineseBankAccountRecognizer(PatternRecognizer):
    """
    Recognizes Chinese Bank Account Numbers
    Format: 16-19 digits, often starting with 62
    """
    PATTERNS = [
        Pattern(
            "CHINESE_BANK_UNIONPAY",
            r"\b62\d{14,17}\b",
            0.7,
        ),
        Pattern(
            "CHINESE_BANK_GENERIC",
            r"\b\d{16,19}\b",
            0.4,
        ),
    ]
    CONTEXT = ["银行", "账户", "卡号", "bank", "account", "card"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="CHINESE_BANK_ACCOUNT",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class JapaneseMyNumberRecognizer(PatternRecognizer):
    """
    Recognizes Japanese My Number (マイナンバー)
    Format: 12 digits
    """
    PATTERNS = [
        Pattern(
            "JAPAN_MY_NUMBER",
            r"\b\d{12}\b",
            0.5,
        ),
        Pattern(
            "JAPAN_MY_NUMBER_FORMATTED",
            r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b",
            0.7,
        ),
    ]
    CONTEXT = ["マイナンバー", "個人番号", "my number", "mynumber", "個人"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="JAPAN_MY_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class JapanesePhoneRecognizer(PatternRecognizer):
    """
    Recognizes Japanese Phone Numbers
    Format: +81 followed by 10 digits, or 0X-XXXX-XXXX
    """
    PATTERNS = [
        Pattern(
            "JAPAN_PHONE",
            r"\b(?:\+81|0)\d{1,4}[\s-]?\d{1,4}[\s-]?\d{4}\b",
            0.7,
        ),
    ]
    CONTEXT = ["電話", "携帯", "phone", "tel", "連絡"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="JAPAN_PHONE",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class KoreanRRNRecognizer(PatternRecognizer):
    """
    Recognizes Korean Resident Registration Number (주민등록번호)
    Format: YYMMDD-XXXXXXX (13 digits with hyphen)
    """
    PATTERNS = [
        Pattern(
            "KOREAN_RRN",
            r"\b\d{6}[\s-]?[1-4]\d{6}\b",
            0.85,
        ),
    ]
    CONTEXT = ["주민등록", "주민번호", "resident", "registration", "RRN"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="KOREAN_RRN",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class KoreanPhoneRecognizer(PatternRecognizer):
    """
    Recognizes Korean Phone Numbers
    Format: +82-10-XXXX-XXXX or 010-XXXX-XXXX
    """
    PATTERNS = [
        Pattern(
            "KOREAN_MOBILE",
            r"\b(?:\+82[\s-]?)?0?1[016789][\s-]?\d{3,4}[\s-]?\d{4}\b",
            0.7,
        ),
    ]
    CONTEXT = ["전화", "휴대폰", "phone", "mobile", "연락처"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="KOREAN_PHONE",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class RussianPassportRecognizer(PatternRecognizer):
    """
    Recognizes Russian Passport Numbers
    Format: 10 digits (series + number)
    """
    PATTERNS = [
        Pattern(
            "RUSSIAN_PASSPORT",
            r"\b\d{2}[\s]?\d{2}[\s]?\d{6}\b",
            0.7,
        ),
    ]
    CONTEXT = ["паспорт", "passport", "серия", "номер"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="RUSSIAN_PASSPORT",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class RussianPhoneRecognizer(PatternRecognizer):
    """
    Recognizes Russian Phone Numbers
    Format: +7-XXX-XXX-XX-XX
    """
    PATTERNS = [
        Pattern(
            "RUSSIAN_PHONE",
            r"\b(?:\+7|8)[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b",
            0.7,
        ),
    ]
    CONTEXT = ["телефон", "мобильный", "phone", "mobile"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="RUSSIAN_PHONE",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class IndianAadhaarRecognizer(PatternRecognizer):
    """
    Recognizes Indian Aadhaar Number
    Format: 12 digits (XXXX XXXX XXXX)
    """
    PATTERNS = [
        Pattern(
            "INDIAN_AADHAAR",
            r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b",
            0.8,
        ),
    ]
    CONTEXT = ["आधार", "aadhaar", "aadhar", "UID", "unique id"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="INDIAN_AADHAAR",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class IndianPANRecognizer(PatternRecognizer):
    """
    Recognizes Indian PAN (Permanent Account Number)
    Format: XXXXX0000X (5 letters, 4 digits, 1 letter)
    """
    PATTERNS = [
        Pattern(
            "INDIAN_PAN",
            r"\b[A-Z]{5}\d{4}[A-Z]\b",
            0.9,
        ),
    ]
    CONTEXT = ["PAN", "permanent account", "tax", "income tax"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="INDIAN_PAN",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class HebrewIDRecognizer(PatternRecognizer):
    """
    Recognizes Israeli ID Number (תעודת זהות)
    Format: 9 digits
    """
    PATTERNS = [
        Pattern(
            "ISRAELI_ID",
            r"\b\d{9}\b",
            0.5,
        ),
    ]
    CONTEXT = ["תעודת זהות", "ת.ז", "ID", "israeli id", "identity"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="ISRAELI_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class GermanIDRecognizer(PatternRecognizer):
    """
    Recognizes German National ID (Personalausweis)
    Format: 9 characters (letters and digits)
    """
    PATTERNS = [
        Pattern(
            "GERMAN_ID",
            r"\b[CFGHJKLMNPRTVWXYZ0-9]{9}\b",
            0.6,
        ),
    ]
    CONTEXT = ["Personalausweis", "Ausweis", "ID", "german id", "identity"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="GERMAN_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


class FrenchNIRRecognizer(PatternRecognizer):
    """
    Recognizes French NIR (Numéro INSEE / Sécurité sociale)
    Format: 15 digits (1 + 2 + 2 + 2 + 3 + 3 + 2)
    """
    PATTERNS = [
        Pattern(
            "FRENCH_NIR",
            r"\b[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}\b",
            0.85,
        ),
        Pattern(
            "FRENCH_NIR_SPACED",
            r"\b[12]\s?\d{2}\s?(0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b",
            0.8,
        ),
    ]
    CONTEXT = ["NIR", "sécurité sociale", "INSEE", "numéro social"]

    def __init__(self, supported_language: str = "en"):
        super().__init__(
            supported_entity="FRENCH_NIR",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )


# Export all recognizers
INTERNATIONAL_RECOGNIZERS = [
    ChineseIDRecognizer,
    ChinesePhoneRecognizer,
    ChineseBankAccountRecognizer,
    JapaneseMyNumberRecognizer,
    JapanesePhoneRecognizer,
    KoreanRRNRecognizer,
    KoreanPhoneRecognizer,
    RussianPassportRecognizer,
    RussianPhoneRecognizer,
    IndianAadhaarRecognizer,
    IndianPANRecognizer,
    HebrewIDRecognizer,
    GermanIDRecognizer,
    FrenchNIRRecognizer,
]


def register_all_international(registry, languages=None):
    """Register all international recognizers for the given languages"""
    if languages is None:
        languages = ["en", "fr"]  # Default languages
    
    count = 0
    for lang in languages:
        for RecognizerClass in INTERNATIONAL_RECOGNIZERS:
            try:
                recognizer = RecognizerClass(supported_language=lang)
                registry.add_recognizer(recognizer)
                count += 1
            except Exception as e:
                print(f"⚠️ Failed to register {RecognizerClass.__name__}: {e}")
    
    print(f"✅ Registered {count} international recognizers")
    return count
