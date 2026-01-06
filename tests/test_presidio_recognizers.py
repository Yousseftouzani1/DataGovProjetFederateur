"""
Pytest Unit Tests for Presidio Recognizers
Cahier Section 5.9 - Deliverable #4: Tests unitaires pytest (coverage > 85%)

Tests all Moroccan custom recognizers:
- CIN_MAROC
- PHONE_MA
- IBAN_MA
- CNSS
- PASSPORT_MA
- PERMIS_MA
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'presidio-serv'))

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from backend.recognizers.cin_recognizer import MoroccanCINRecognizer
from backend.recognizers.phone_ma_recognizer import MoroccanPhoneRecognizer
from backend.recognizers.iban_ma_recognizer import MoroccanIBANRecognizer
from backend.recognizers.cnss_recognizer import MoroccanCNSSRecognizer
from backend.recognizers.passport_ma_recognizer import MoroccanPassportRecognizer
from backend.recognizers.permis_ma_recognizer import MoroccanPermisRecognizer


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def analyzer():
    """Create analyzer with all Moroccan recognizers"""
    registry = RecognizerRegistry()
    registry.add_recognizer(MoroccanCINRecognizer())
    registry.add_recognizer(MoroccanPhoneRecognizer())
    registry.add_recognizer(MoroccanIBANRecognizer())
    registry.add_recognizer(MoroccanCNSSRecognizer())
    registry.add_recognizer(MoroccanPassportRecognizer())
    registry.add_recognizer(MoroccanPermisRecognizer())
    
    # Use 'en' to match registry default (recognizers are pattern-based, language-agnostic)
    analyzer = AnalyzerEngine(registry=registry, supported_languages=["en"])
    return analyzer


# ============================================================================
# CIN_MAROC TESTS
# ============================================================================

class TestCINRecognizer:
    """Test Moroccan CIN recognizer"""
    
    def test_cin_basic(self, analyzer):
        """Test basic CIN detection"""
        text = "Mon CIN est AB123456"
        results = analyzer.analyze(text, language='en', entities=["CIN_MAROC"])
        
        assert len(results) == 1
        assert results[0].entity_type == "CIN_MAROC"
        assert results[0].start == 12
        assert results[0].end == 20
        assert text[results[0].start:results[0].end] == "AB123456"
    
    def test_cin_with_context(self, analyzer):
        """Test CIN with context keywords"""
        text = "Carte d'identité: BE987654"
        results = analyzer.analyze(text, language='en', entities=["CIN_MAROC"])
        
        assert len(results) == 1
        assert results[0].entity_type == "CIN_MAROC"
        assert results[0].score >= 0.85
    
    def test_cin_with_spaces(self, analyzer):
        """Test CIN with spaces (AB 123 456)"""
        text = "CIN: AB 123 456"
        results = analyzer.analyze(text, language='en', entities=["CIN_MAROC"])
        
        assert len(results) >= 1
        assert any(r.entity_type == "CIN_MAROC" for r in results)
    
    def test_cin_false_positive_prevention(self, analyzer):
        """Test that short codes don't match"""
        text = "Reference XY12345"  # Only 5 digits, should not match
        results = analyzer.analyze(text, language='en', entities=["CIN_MAROC"])
        
        # Should have 0 or very low confidence
        high_confidence = [r for r in results if r.score >= 0.7]
        assert len(high_confidence) == 0


# ============================================================================
# PHONE_MA TESTS
# ============================================================================

class TestPhoneRecognizer:
    """Test Moroccan phone number recognizer"""
    
    def test_phone_international(self, analyzer):
        """Test international format +212"""
        text = "Téléphone: +212612345678"
        results = analyzer.analyze(text, language='en', entities=["PHONE_MA"])
        
        assert len(results) == 1
        assert results[0].entity_type == "PHONE_MA"
        assert "+212612345678" in text[results[0].start:results[0].end]
    
    def test_phone_local(self, analyzer):
        """Test local format 06"""
        text = "Appelez-moi au 0612345678"
        results = analyzer.analyze(text, language='en', entities=["PHONE_MA"])
        
        assert len(results) == 1
        assert results[0].entity_type == "PHONE_MA"
    
    def test_phone_with_spaces(self, analyzer):
        """Test phone with spaces"""
        text = "Tel: 0612 345 678"
        results = analyzer.analyze(text, language='en', entities=["PHONE_MA"])
        
        assert len(results) >= 1
        assert any(r.entity_type == "PHONE_MA" for r in results)
    
    def test_phone_multiple_formats(self, analyzer):
        """Test various phone formats"""
        formats = [
            "+212612345678",
            "0612345678",
            "00212612345678",
        ]
        
        for phone in formats:
            text = f"Contact: {phone}"
            results = analyzer.analyze(text, language='en', entities=["PHONE_MA"])
            assert len(results) >= 1, f"Failed for format: {phone}"


# ============================================================================
# IBAN_MA TESTS
# ============================================================================

class TestIBANRecognizer:
    """Test Moroccan IBAN recognizer"""
    
    def test_iban_alphanumeric(self, analyzer):
        """Test IBAN with alphanumeric characters"""
        # Valid MOD-97 IBAN for PXAF5XLFR848NM2UHJMKPA0C
        text = "IBAN: MA56PXAF5XLFR848NM2UHJMKPA0C"
        results = analyzer.analyze(text, language='en', entities=["IBAN_MA"])
        
        assert len(results) == 1
        assert results[0].entity_type == "IBAN_MA"
        assert results[0].score >= 0.85
    
    def test_iban_numeric(self, analyzer):
        """Test IBAN with numbers only"""
        # Valid MOD-97 numeric IBAN
        text = "Compte: MA64123456789012345678901234"
        results = analyzer.analyze(text, language='en', entities=["IBAN_MA"])
        
        assert len(results) >= 1
    
    def test_iban_with_context(self, analyzer):
        """Test IBAN with context keywords"""
        # Valid MOD-97 numeric IBAN
        text = "Mon compte bancaire: MA64123456789012345678901234"
        results = analyzer.analyze(text, language='en', entities=["IBAN_MA"])
        
        assert len(results) >= 1
        assert any(r.score >= 0.90 for r in results)


# ============================================================================
# CNSS TESTS
# ============================================================================

class TestCNSSRecognizer:
    """Test Moroccan CNSS recognizer"""
    
    def test_cnss_basic(self, analyzer):
        """Test basic CNSS detection"""
        text = "CNSS: 123456789012"
        results = analyzer.analyze(text, language='en', entities=["CNSS"])
        
        assert len(results) == 1
        assert results[0].entity_type == "CNSS"
        assert "123456789012" in text[results[0].start:results[0].end]
    
    def test_cnss_with_context(self, analyzer):
        """Test CNSS with context"""
        text = "Numéro de sécurité sociale: 987654321098"
        results = analyzer.analyze(text, language='en', entities=["CNSS"])
        
        assert len(results) == 1
        assert results[0].score >= 0.85
    
    def test_cnss_entity_name(self, analyzer):
        """Test that entity type is CNSS not CNSS_MA"""
        text = "Mon numéro CNSS est 111222333444"
        results = analyzer.analyze(text, language='en', entities=["CNSS"])
        
        assert len(results) == 1
        assert results[0].entity_type == "CNSS"  # Not CNSS_MA


# ============================================================================
# PASSPORT_MA TESTS
# ============================================================================

class TestPassportRecognizer:
    """Test Moroccan Passport recognizer"""
    
    def test_passport_basic(self, analyzer):
        """Test basic passport detection"""
        text = "Passeport: AB1234567"
        results = analyzer.analyze(text, language='en', entities=["PASSPORT_MA"])
        
        assert len(results) == 1
        assert results[0].entity_type == "PASSPORT_MA"
        assert "AB1234567" in text[results[0].start:results[0].end]
    
    def test_passport_6_digits(self, analyzer):
        """Test passport with 6 digits"""
        text = "Passport numéro: CD123456"
        results = analyzer.analyze(text, language='en', entities=["PASSPORT_MA"])
        
        assert len(results) >= 1
        assert any(r.entity_type == "PASSPORT_MA" for r in results)


# ============================================================================
# PERMIS_MA TESTS
# ============================================================================

class TestPermisRecognizer:
    """Test Moroccan Driving License recognizer"""
    
    def test_permis_basic(self, analyzer):
        """Test basic permis detection"""
        text = "Permis de conduire: A12345678"
        results = analyzer.analyze(text, language='en', entities=["PERMIS_MA"])
        
        assert len(results) >= 1
        assert any(r.entity_type == "PERMIS_MA" for r in results)
    
    def test_permis_with_context(self, analyzer):
        """Test permis with context"""
        text = "Mon permis: ABC123456"
        results = analyzer.analyze(text, language='en', entities=["PERMIS_MA"])
        
        assert len(results) >= 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for multiple entities"""
    
    def test_multiple_entities(self, analyzer):
        """Test detection of multiple entities in one text"""
        text = """
        Informations personnelles:
        CIN: AB123456
        Téléphone: +212612345678
        IBAN: MA12BANK12345678901234567890
        CNSS: 123456789012
        """
        results = analyzer.analyze(text, language='en')
        
        entity_types = [r.entity_type for r in results]
        assert "CIN_MAROC" in entity_types
        assert "PHONE_MA" in entity_types
        assert "IBAN_MA" in entity_types
        assert "CNSS" in entity_types
    
    def test_no_false_positives(self, analyzer):
        """Test that normal text doesn't trigger detections"""
        text = "Bonjour, comment allez-vous? Le temps est agréable aujourd'hui."
        results = analyzer.analyze(text, language='en')
        
        # Should be empty or very low confidence
        assert len(results) == 0 or all(r.score < 0.5 for r in results)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance requirements (Cahier Section 5.6)"""
    
    def test_response_time(self, analyzer):
        """Test that analysis completes in < 500ms (Cahier requirement)"""
        import time
        
        text = "CIN: AB123456, Tel: +212612345678, IBAN: MA12BANK12345678901234567890" * 10
        
        start = time.time()
        results = analyzer.analyze(text, language='en')
        duration = time.time() - start
        
        # Cahier requirement: < 500ms
        assert duration < 0.5, f"Analysis took {duration:.3f}s, should be < 0.5s"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services/presidio-serv/backend/recognizers", "--cov-report=term-missing", "--cov-report=html"])

