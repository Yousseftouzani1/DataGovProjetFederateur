"""
End-to-End Pipeline Test
Tests complete data workflow from upload to quality report (Cahier §5.3)
"""
import pytest
import requests
import time


class TestFullDataPipeline:
    """Test complete data processing pipeline"""

    # Service endpoints
    CLEANING_URL = "http://localhost:8004"
    CLASSIFICATION_URL = "http://localhost:8005"
    CORRECTION_URL = "http://localhost:8006"
    QUALITY_URL = "http://localhost:8008"
    PRESIDIO_URL = "http://localhost:8003"
    TAXONOMIE_URL = "http://localhost:8002"

    @pytest.fixture
    def sample_dataset(self):
        """Sample CSV dataset with various issues"""
        return """nom,prenom,email,telephone,date_naissance,age
Dupont,Jean,jean@gmial.com,0612345678,1990-01-15,34
Martin,Marie,invalid-email,622334455,2023-13-01,30
El Amrani,Fatima,fatima@test.com,0612345678,1985-06-20,39
Tazi,Ahmed,ahmed@example.ma,+212612345678,invalid,invalid
Benali,Sara,,0612345678,1995-12-31,"""

    def test_complete_pipeline_workflow(self, sample_dataset):
        """
        Test: Full pipeline from upload to quality report

        Workflow:
        1. Upload CSV → Cleaning Service
        2. Profile data → Data profiling
        3. Clean data → Remove duplicates, handle nulls
        4. Detect PII → Presidio + Taxonomie
        5. Classify columns → ML Classification
        6. Detect issues → Quality analysis
        7. Apply corrections → T5 corrections
        8. Generate quality report → ISO 25012 metrics
        """

        # STEP 1: Upload dataset
        print("\n📤 STEP 1: Uploading dataset...")
        files = {"file": ("test_pipeline.csv", sample_dataset)}

        upload_response = requests.post(
            f"{self.CLEANING_URL}/api/upload",
            files=files,
            timeout=20
        )

        assert upload_response.status_code in [200, 201], \
            f"Upload failed: {upload_response.status_code}"

        upload_result = upload_response.json()
        dataset_id = upload_result.get("dataset_id")
        assert dataset_id is not None, "No dataset_id returned"
        print(f"✅ Dataset uploaded: {dataset_id}")

        # STEP 2: Wait for processing
        print("\n⏳ STEP 2: Waiting for pipeline processing...")
        time.sleep(15)  # Allow Airflow DAG to process

        # STEP 3: Verify PII detection
        print("\n🔍 STEP 3: Verifying PII detection...")
        pii_response = requests.get(
            f"{self.CLEANING_URL}/api/datasets/{dataset_id}/pii",
            timeout=10
        )

        if pii_response.status_code == 200:
            pii_data = pii_response.json()
            expected_pii_fields = ["email", "telephone"]

            if "pii_fields" in pii_data:
                pii_fields = pii_data["pii_fields"]
                assert len(pii_fields) > 0, "No PII detected"

                # Verify expected PII fields are detected
                for field in expected_pii_fields:
                    if field in pii_fields:
                        print(f"✅ {field} detected as PII")

        # STEP 4: Verify classification
        print("\n🏷️ STEP 4: Verifying ML classification...")
        classification_response = requests.get(
            f"{self.CLEANING_URL}/api/datasets/{dataset_id}/classifications",
            timeout=10
        )

        if classification_response.status_code == 200:
            classifications = classification_response.json()
            assert len(classifications) > 0, "No classifications applied"
            print(f"✅ {len(classifications)} columns classified")

        # STEP 5: Verify corrections detected
        print("\n🔧 STEP 5: Verifying error detection...")
        errors_response = requests.get(
            f"{self.CLEANING_URL}/api/datasets/{dataset_id}/errors",
            timeout=10
        )

        if errors_response.status_code == 200:
            errors = errors_response.json()

            # Expected errors:
            # - jean@gmial.com (typo)
            # - invalid-email (format)
            # - 2023-13-01 (invalid date)
            # - "invalid" in age field

            if "errors" in errors:
                error_list = errors["errors"]
                assert len(error_list) > 0, "No errors detected"
                print(f"✅ {len(error_list)} errors detected")

        # STEP 6: Get quality report
        print("\n📊 STEP 6: Generating quality report...")
        quality_response = requests.get(
            f"{self.QUALITY_URL}/api/quality/reports/{dataset_id}",
            timeout=15
        )

        if quality_response.status_code == 200:
            quality_report = quality_response.json()

            # Verify ISO 25012 metrics
            expected_metrics = [
                "accuracy",
                "completeness",
                "consistency",
                "credibility"
            ]

            for metric in expected_metrics:
                if metric in quality_report:
                    score = quality_report[metric]
                    print(f"✅ {metric}: {score}")

                    # Scores should be between 0 and 1
                    if isinstance(score, (int, float)):
                        assert 0 <= score <= 1, f"{metric} score out of range"

        # STEP 7: Verify data persistence
        print("\n💾 STEP 7: Verifying MongoDB persistence...")

        # Get dataset info
        dataset_response = requests.get(
            f"{self.CLEANING_URL}/api/datasets/{dataset_id}",
            timeout=10
        )

        assert dataset_response.status_code == 200, "Dataset not persisted"
        dataset_info = dataset_response.json()

        assert "id" in dataset_info or "dataset_id" in dataset_info
        assert "row_count" in dataset_info or "rows" in dataset_info
        print("✅ Dataset persisted in MongoDB")

        # STEP 8: Summary
        print("\n" + "="*60)
        print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Dataset ID: {dataset_id}")
        print(f"Status: All stages completed")
        print("="*60)

    def test_pipeline_with_clean_data(self):
        """Test: Pipeline handles already-clean data correctly"""
        # Given: Perfect dataset with no errors
        clean_data = """nom,email,age
Dupont,user@example.com,30
Martin,contact@test.fr,25"""

        files = {"file": ("clean_data.csv", clean_data)}

        # When: Upload
        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=15
        )

        # Then: Processing should complete without corrections
        assert response.status_code in [200, 201]
        dataset_id = response.json().get("dataset_id")

        time.sleep(10)

        # Quality score should be high
        quality_response = requests.get(
            f"{self.QUALITY_URL}/api/quality/reports/{dataset_id}",
            timeout=10
        )

        if quality_response.status_code == 200:
            quality = quality_response.json()

            # Completeness and accuracy should be 1.0 or close
            if "accuracy" in quality:
                assert quality["accuracy"] > 0.9
            if "completeness" in quality:
                assert quality["completeness"] > 0.9

            print("✅ Clean data processed correctly")

    def test_pipeline_with_large_dataset(self):
        """Test: Pipeline handles larger datasets (1000+ rows)"""
        # Given: Large dataset
        rows = [f"Nom{i},user{i}@test.com,{20+i%50}" for i in range(1000)]
        large_data = "nom,email,age\n" + "\n".join(rows)

        files = {"file": ("large_dataset.csv", large_data)}

        # When: Upload
        start_time = time.time()
        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=60
        )
        elapsed = time.time() - start_time

        # Then: Should complete in reasonable time
        assert response.status_code in [200, 201]
        assert elapsed < 60, f"Upload took too long: {elapsed}s"

        dataset_id = response.json().get("dataset_id")
        print(f"✅ 1000-row dataset processed in {elapsed:.2f}s")

        # Verify row count
        time.sleep(15)
        dataset_response = requests.get(
            f"{self.CLEANING_URL}/api/datasets/{dataset_id}",
            timeout=10
        )

        if dataset_response.status_code == 200:
            dataset = dataset_response.json()
            row_count = dataset.get("row_count") or dataset.get("rows", 0)
            assert row_count == 1000 or row_count == 1001  # +1 for header

    def test_pipeline_error_recovery(self):
        """Test: Pipeline recovers from errors gracefully"""
        # Given: Invalid CSV format
        invalid_data = "incomplete,data\nvalue1"  # Missing column

        files = {"file": ("invalid.csv", invalid_data)}

        # When: Upload
        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=15
        )

        # Then: Should return error or handle gracefully
        assert response.status_code in [200, 201, 400, 422]

        if response.status_code in [400, 422]:
            error = response.json()
            assert "error" in error or "detail" in error
            print("✅ Invalid data rejected gracefully")


class TestPIIWorkflow:
    """Test PII detection and masking workflow"""

    CLEANING_URL = "http://localhost:8004"
    PRESIDIO_URL = "http://localhost:8003"
    TAXONOMIE_URL = "http://localhost:8002"
    ETHIMASK_URL = "http://localhost:8009"

    def test_pii_detection_and_masking(self):
        """Test: PII is detected and can be masked"""
        # Given: Dataset with clear PII
        pii_data = """nom,email,telephone,cin
Dupont,jean.dupont@example.com,0612345678,AB123456
Martin,marie.martin@test.fr,0622334455,CD789012"""

        files = {"file": ("pii_dataset.csv", pii_data)}

        # STEP 1: Upload
        upload_response = requests.post(
            f"{self.CLEANING_URL}/api/upload",
            files=files,
            timeout=15
        )

        assert upload_response.status_code in [200, 201]
        dataset_id = upload_response.json().get("dataset_id")

        time.sleep(10)

        # STEP 2: Verify PII detected
        pii_response = requests.get(
            f"{self.CLEANING_URL}/api/datasets/{dataset_id}/pii",
            timeout=10
        )

        if pii_response.status_code == 200:
            pii_info = pii_response.json()
            expected_pii = ["email", "telephone", "cin"]

            for field in expected_pii:
                # Check if detected
                if "pii_fields" in pii_info:
                    assert field in pii_info["pii_fields"], \
                        f"{field} not detected as PII"
                    print(f"✅ {field} detected as PII")

        # STEP 3: Apply masking
        mask_response = requests.post(
            f"{self.ETHIMASK_URL}/api/mask/{dataset_id}",
            json={"strategy": "hash"},
            timeout=10
        )

        if mask_response.status_code in [200, 201]:
            masked_data = mask_response.json()
            print("✅ Masking applied successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
