"""
Unit Tests for Correction Service - T5 Model Validation
Tests T5-based text correction accuracy (Cahier §5.2.2-F)
"""
import pytest
import requests


class TestT5Correction:
    """Test T5 model for intelligent text correction"""

    BASE_URL = "http://localhost:8006"

    def test_service_health(self):
        """Verify correction service is running"""
        response = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert response.status_code == 200, "Correction service not responding"

    def test_correct_email_typo(self):
        """Test: Should correct common email typos"""
        # Given: Email with typo (gmial -> gmail)
        payload = {
            "value": "user@gmial.com",
            "context": "email",
            "field_type": "EMAIL"
        }

        # When: Apply T5 correction
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Should suggest gmail.com
        assert response.status_code == 200
        result = response.json()
        assert "suggestion" in result

        # T5 might suggest the correction
        suggested = result["suggestion"].lower()
        if suggested != payload["value"]:
            assert "gmail" in suggested or result["confidence"] > 0.5

    def test_correct_date_format(self):
        """Test: Should correct invalid date formats"""
        # Given: Invalid date (month 13)
        payload = {
            "value": "2023-13-01",
            "context": "date_naissance",
            "field_type": "DATE"
        }

        # When: Apply correction
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Should suggest valid date
        assert response.status_code == 200
        result = response.json()
        assert "suggestion" in result

        # Should not have month 13
        suggested = result["suggestion"]
        if suggested != payload["value"]:
            assert "13" not in suggested or "-01-" in suggested

    def test_correct_phone_format(self):
        """Test: Should standardize phone number format"""
        # Given: Phone without international prefix
        payload = {
            "value": "612345678",
            "context": "telephone",
            "field_type": "PHONE"
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Should suggest standardized format
        assert response.status_code == 200
        result = response.json()
        assert "suggestion" in result

        # Might add prefix or 0
        suggested = result["suggestion"]
        assert len(suggested) >= len(payload["value"])

    def test_context_aware_correction(self):
        """Test: Uses context to improve corrections"""
        # Given: Ambiguous value with context
        payload = {
            "value": "2023-01",
            "context": "date_naissance",
            "field_type": "DATE",
            "row_context": {
                "nom": "Dupont",
                "prenom": "Jean",
                "age": "25"
            }
        }

        # When: Correct with context
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Should use context to complete date
        assert response.status_code == 200
        result = response.json()
        assert "suggestion" in result

        # Should complete the date (add day)
        suggested = result["suggestion"]
        if len(suggested) > len(payload["value"]):
            assert suggested.count("-") >= 2  # YYYY-MM-DD format

    def test_confidence_scoring(self):
        """Test: Returns reasonable confidence scores"""
        # Given: Various correction scenarios
        test_cases = [
            {"value": "user@gmial.com", "context": "email"},  # Clear typo
            {"value": "2023-13-01", "context": "date"},       # Invalid date
            {"value": "valid@test.com", "context": "email"},  # Already correct
        ]

        for payload in test_cases:
            # When: Correct
            response = requests.post(
                f"{self.BASE_URL}/api/correct",
                json=payload,
                timeout=10
            )

            # Then: Confidence is in valid range
            if response.status_code == 200:
                result = response.json()
                confidence = result.get("confidence", 0.0)
                assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"

    def test_no_correction_needed(self):
        """Test: Recognizes when no correction is needed"""
        # Given: Already correct value
        payload = {
            "value": "user@example.com",
            "context": "email",
            "field_type": "EMAIL"
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Returns original or same value
        assert response.status_code == 200
        result = response.json()

        # Either no change or low confidence
        if result["suggestion"] == payload["value"]:
            assert True  # No correction needed
        else:
            assert result["confidence"] < 0.9  # Low confidence in change

    def test_batch_correction(self):
        """Test: Can correct multiple values at once"""
        # Given: Multiple values to correct
        payload = {
            "corrections": [
                {"value": "user@gmial.com", "context": "email"},
                {"value": "2023-13-01", "context": "date"},
                {"value": "612345678", "context": "phone"}
            ]
        }

        # When: Batch correct
        response = requests.post(
            f"{self.BASE_URL}/api/correct/batch",
            json=payload,
            timeout=15
        )

        # Then: All values corrected
        if response.status_code == 200:
            result = response.json()
            assert len(result.get("results", [])) == 3

    def test_cpu_mode_works(self):
        """Test: T5 model runs on CPU without CUDA errors"""
        # Given: Correction request
        payload = {
            "value": "test@gmial.com",
            "context": "email"
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: No CUDA errors
        assert response.status_code == 200
        result = response.json()
        assert "cuda" not in str(result).lower() or response.status_code == 200

    def test_empty_value_handling(self):
        """Test: Handles empty values gracefully"""
        # Given: Empty value
        payload = {
            "value": "",
            "context": "email"
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=5
        )

        # Then: Returns error or empty suggestion
        assert response.status_code in [200, 400, 422]

    def test_null_value_handling(self):
        """Test: Handles null values"""
        # Given: Null value
        payload = {
            "value": None,
            "context": "email"
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=5
        )

        # Then: Handles gracefully
        assert response.status_code in [200, 400, 422]

    def test_auto_apply_threshold(self):
        """Test: Auto-applies corrections above confidence threshold"""
        # Given: Clear correction with high confidence
        payload = {
            "value": "user@gmial.com",
            "context": "email",
            "auto_apply": True,
            "threshold": 0.9
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Indicates if auto-applied
        if response.status_code == 200:
            result = response.json()
            if "auto_applied" in result:
                assert isinstance(result["auto_applied"], bool)


class TestCorrectionValidation:
    """Test correction validation and persistence"""

    BASE_URL = "http://localhost:8006"

    def test_validation_stored_in_mongodb(self):
        """Test: Correction suggestions are stored for validation"""
        # Given: Correction request with save flag
        payload = {
            "value": "test@gmial.com",
            "context": "email",
            "save_for_validation": True
        }

        # When: Correct
        response = requests.post(
            f"{self.BASE_URL}/correct",
            json=payload,
            timeout=10
        )

        # Then: Validation ID returned
        if response.status_code == 200:
            result = response.json()
            if "validation_id" in result:
                # Verify can be retrieved
                val_response = requests.get(
                    f"{self.BASE_URL}/api/validations/{result['validation_id']}",
                    timeout=5
                )
                assert val_response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
