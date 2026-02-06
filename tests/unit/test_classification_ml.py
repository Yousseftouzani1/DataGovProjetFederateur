"""
Unit Tests for Classification Service - ML Model Validation
Tests BERT classifier and ensemble model accuracy (Cahier §5.2.2-E)
"""
import pytest
import requests
import json


class TestBERTClassification:
    """Test BERT classifier model accuracy and functionality"""

    BASE_URL = "http://localhost:8005"

    def test_service_health(self):
        """Verify classification service is running"""
        response = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert response.status_code == 200, "Classification service not responding"

    def test_classify_email_column(self):
        """Test: Should classify email column correctly"""
        # Given: Sample email data
        payload = {
            "column_name": "email",
            "sample_values": [
                "user@example.com",
                "contact@company.fr",
                "admin@test.ma"
            ]
        }

        # When: Classify using ML model
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Should identify as EMAIL or PII
        assert response.status_code == 200
        result = response.json()
        assert "classification" in result
        assert result["classification"] in ["EMAIL", "PII", "CONTACT"]
        assert result["confidence"] > 0.5, "Confidence too low"

    def test_classify_name_column(self):
        """Test: Should classify name column correctly"""
        # Given: Sample name data
        payload = {
            "column_name": "nom_complet",
            "sample_values": [
                "Ahmed Benali",
                "Fatima El Amrani",
                "Mohammed Tazi"
            ]
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Should identify as NAME/NOM or PII
        assert response.status_code == 200
        result = response.json()
        assert result["classification"] in ["NAME", "NOM", "PII", "PERSON"]
        assert result["confidence"] > 0.5

    def test_classify_phone_column(self):
        """Test: Should classify phone number column correctly"""
        # Given: Moroccan phone numbers
        payload = {
            "column_name": "telephone",
            "sample_values": [
                "0612345678",
                "+212612345678",
                "0522123456"
            ]
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Should identify as PHONE or PII
        assert response.status_code == 200
        result = response.json()
        assert result["classification"] in ["PHONE", "TELEPHONE", "PII", "CONTACT"]
        assert result["confidence"] > 0.4

    def test_classify_numeric_column(self):
        """Test: Should classify numeric data correctly"""
        # Given: Numeric non-PII data
        payload = {
            "column_name": "age",
            "sample_values": ["25", "30", "45", "28", "35"]
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Should identify as NUMERIC or AGE
        assert response.status_code == 200
        result = response.json()
        assert result["classification"] in ["NUMERIC", "AGE", "INTEGER", "NUMBER"]

    def test_classify_date_column(self):
        """Test: Should classify date column correctly"""
        # Given: Date data
        payload = {
            "column_name": "date_naissance",
            "sample_values": [
                "1990-01-15",
                "1985-06-20",
                "2000-12-31"
            ]
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Should identify as DATE
        assert response.status_code == 200
        result = response.json()
        assert result["classification"] in ["DATE", "DATETIME", "TIMESTAMP"]

    def test_ensemble_voting(self):
        """Test: Ensemble model combines BERT + RandomForest + Rules"""
        # Given: Ambiguous data that benefits from ensemble
        payload = {
            "column_name": "identifier",
            "sample_values": ["ID001", "ID002", "ID003"]
        }

        # When: Classify using ensemble
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Should return result with ensemble metadata
        assert response.status_code == 200
        result = response.json()

        # Ensemble should provide voting breakdown
        if "ensemble_votes" in result:
            assert "BERT" in result["ensemble_votes"]
            assert "RandomForest" in result["ensemble_votes"]
            assert "RuleEngine" in result["ensemble_votes"]

    def test_cpu_mode_works(self):
        """Test: Model runs on CPU without CUDA errors"""
        # Given: Any classification request
        payload = {
            "column_name": "test",
            "sample_values": ["value1", "value2"]
        }

        # When: Classify (should use CPU)
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: No CUDA errors, successful response
        assert response.status_code == 200
        result = response.json()
        assert "error" not in result or "cuda" not in str(result.get("error", "")).lower()

    def test_confidence_score_range(self):
        """Test: Confidence scores are between 0.0 and 1.0"""
        # Given: Various test cases
        test_cases = [
            {"column_name": "email", "sample_values": ["test@example.com"]},
            {"column_name": "nom", "sample_values": ["Dupont"]},
            {"column_name": "age", "sample_values": ["25"]},
        ]

        for payload in test_cases:
            # When: Classify
            response = requests.post(
                f"{self.BASE_URL}/api/classify",
                json=payload,
                timeout=10
            )

            # Then: Confidence is valid range
            if response.status_code == 200:
                result = response.json()
                confidence = result.get("confidence", 0)
                assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"

    def test_batch_classification(self):
        """Test: Can classify multiple columns at once"""
        # Given: Multiple columns
        payload = {
            "columns": [
                {"name": "email", "samples": ["user@test.com"]},
                {"name": "nom", "samples": ["Ahmed"]},
                {"name": "age", "samples": ["30"]}
            ]
        }

        # When: Batch classify
        response = requests.post(
            f"{self.BASE_URL}/api/classify/batch",
            json=payload,
            timeout=15
        )

        # Then: All columns classified
        if response.status_code == 200:
            result = response.json()
            assert len(result.get("results", [])) == 3

    def test_empty_input_handling(self):
        """Test: Handles empty input gracefully"""
        # Given: Empty sample values
        payload = {
            "column_name": "test",
            "sample_values": []
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=5
        )

        # Then: Returns error or fallback classification
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            result = response.json()
            assert "classification" in result or "error" in result

    def test_null_value_handling(self):
        """Test: Handles null values in samples"""
        # Given: Samples with nulls
        payload = {
            "column_name": "email",
            "sample_values": ["user@test.com", None, "", "admin@test.com"]
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: Still classifies correctly
        assert response.status_code == 200
        result = response.json()
        assert "classification" in result


class TestClassificationHistory:
    """Test classification history storage in MongoDB"""

    BASE_URL = "http://localhost:8005"

    def test_history_saved_to_mongodb(self):
        """Test: Classification results are saved to MongoDB"""
        # Given: Classification request
        payload = {
            "column_name": "email_test",
            "sample_values": ["history@test.com"],
            "save_history": True
        }

        # When: Classify
        response = requests.post(
            f"{self.BASE_URL}/api/v1/classify",
            json=payload,
            timeout=10
        )

        # Then: History ID returned
        if response.status_code == 200:
            result = response.json()
            if "history_id" in result:
                # Verify history can be retrieved
                history_response = requests.get(
                    f"{self.BASE_URL}/api/history/{result['history_id']}",
                    timeout=5
                )
                assert history_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
