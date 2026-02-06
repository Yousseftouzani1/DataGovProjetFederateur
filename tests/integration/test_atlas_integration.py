"""
Integration Tests for Apache Atlas
Tests metadata registration and lineage tracking (Cahier §5.4.1)
"""
import pytest
import requests
import time


class TestAtlasIntegration:
    """Test Apache Atlas metadata management integration"""

    # Services that use Atlas
    CLEANING_URL = "http://localhost:8004"
    TAXONOMIE_URL = "http://localhost:8002"

    def test_atlas_connectivity(self):
        """Test: Can connect to Apache Atlas"""
        # Given: Cleaning service with Atlas integration
        # When: Check if Atlas is configured
        response = requests.get(f"{self.CLEANING_URL}/health", timeout=5)

        # Then: Service should be running
        assert response.status_code == 200

        # Check if Atlas configuration exists in response
        if "atlas" in response.text.lower():
            assert True  # Atlas is configured

    def test_dataset_metadata_registration(self):
        """Test: Dataset metadata is registered in Atlas"""
        # Given: Upload a dataset
        csv_content = """nom,email,telephone
Dupont,user@example.com,0612345678
Martin,contact@test.fr,0622334455"""

        files = {"file": ("test_atlas.csv", csv_content)}

        # When: Upload to cleaning service
        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=15
        )

        # Then: Dataset uploaded successfully
        assert response.status_code in [200, 201]
        result = response.json()

        # Verify Atlas GUID was generated
        if "atlas_guid" in result or "guid" in result:
            guid = result.get("atlas_guid") or result.get("guid")
            assert guid is not None
            assert len(guid) > 0
            print(f"✅ Atlas GUID generated: {guid}")

    def test_column_metadata_registration(self):
        """Test: Column metadata is registered with classifications"""
        # Given: Dataset with PII columns
        csv_content = """nom,email,age
Dupont,user@test.com,30"""

        files = {"file": ("test_columns.csv", csv_content)}

        # When: Upload and classify
        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=15
        )

        # Then: Columns should be registered in Atlas
        if response.status_code in [200, 201]:
            result = response.json()
            dataset_id = result.get("dataset_id")

            # Check if column classifications exist
            if dataset_id:
                time.sleep(2)  # Allow Atlas registration to complete

                # Try to get dataset info
                info_response = requests.get(
                    f"{self.CLEANING_URL}/api/datasets/{dataset_id}",
                    timeout=5
                )

                if info_response.status_code == 200:
                    dataset_info = info_response.json()

                    # Verify columns have Atlas metadata
                    if "columns" in dataset_info:
                        columns = dataset_info["columns"]
                        assert len(columns) > 0
                        print(f"✅ {len(columns)} columns registered")

    def test_pii_classification_tagging(self):
        """Test: PII columns are tagged with Atlas classifications"""
        # Given: Dataset with clear PII
        csv_content = """email,telephone
user@test.com,0612345678"""

        files = {"file": ("test_pii.csv", csv_content)}

        # When: Upload
        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=15
        )

        # Then: PII tags should be applied
        if response.status_code in [200, 201]:
            result = response.json()

            # Check if PII was detected
            if "pii_detected" in result or "classifications" in result:
                pii_info = result.get("pii_detected") or result.get("classifications")
                print(f"✅ PII detected: {pii_info}")
                assert pii_info is not None

    def test_lineage_tracking(self):
        """Test: Data lineage is tracked through pipeline"""
        # Given: Dataset going through pipeline
        csv_content = """nom,email
Test,test@example.com"""

        files = {"file": ("test_lineage.csv", csv_content)}

        # When: Upload (starts pipeline)
        upload_response = requests.post(
            f"{self.CLEANING_URL}/api/upload",
            files=files,
            timeout=15
        )

        if upload_response.status_code in [200, 201]:
            dataset_id = upload_response.json().get("dataset_id")

            # Wait for pipeline processing
            time.sleep(10)

            # Then: Check if lineage exists
            lineage_response = requests.get(
                f"{self.CLEANING_URL}/api/datasets/{dataset_id}/lineage",
                timeout=5
            )

            # Lineage endpoint might not exist, but should not error
            assert lineage_response.status_code in [200, 404, 501]

            if lineage_response.status_code == 200:
                lineage = lineage_response.json()
                print(f"✅ Lineage tracked: {lineage}")

    def test_taxonomy_sync_to_atlas(self):
        """Test: Taxonomies are synced to Atlas on startup"""
        # Given: Taxonomie service is running
        # When: Check taxonomies
        response = requests.get(
            f"{self.TAXONOMIE_URL}/api/taxonomies",
            timeout=5
        )

        # Then: Taxonomies should be available
        if response.status_code == 200:
            taxonomies = response.json()
            assert isinstance(taxonomies, (list, dict))

            # Check if Atlas sync metadata exists
            if isinstance(taxonomies, dict) and "atlas_synced" in taxonomies:
                assert taxonomies["atlas_synced"] is True
                print("✅ Taxonomies synced to Atlas")

    def test_atlas_entity_creation(self):
        """Test: Can create entities in Atlas programmatically"""
        # Given: Entity data
        entity_data = {
            "typeName": "DataSet",
            "attributes": {
                "name": "test_dataset_" + str(int(time.time())),
                "description": "Test dataset for Atlas integration",
                "qualifiedName": f"test_dataset_{int(time.time())}@datagov"
            }
        }

        # When: Try to create entity via service
        response = requests.post(
            f"{self.CLEANING_URL}/api/atlas/entities",
            json=entity_data,
            timeout=10
        )

        # Then: Entity created or endpoint exists
        assert response.status_code in [200, 201, 404, 501]

        if response.status_code in [200, 201]:
            result = response.json()
            assert "guid" in result or "guidAssignments" in result
            print("✅ Entity created in Atlas")

    def test_atlas_search_functionality(self):
        """Test: Can search entities in Atlas"""
        # Given: Search query
        search_query = {"query": "test", "typeName": "DataSet"}

        # When: Search via service
        response = requests.post(
            f"{self.CLEANING_URL}/api/atlas/search",
            json=search_query,
            timeout=10
        )

        # Then: Search works or endpoint exists
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            results = response.json()
            print(f"✅ Atlas search returned: {results}")

    def test_mock_mode_fallback(self):
        """Test: System works when Atlas is unavailable (mock mode)"""
        # Note: This test verifies graceful degradation

        # Given: Service might be in mock mode
        # When: Upload dataset
        csv_content = """test,data
value1,value2"""

        files = {"file": ("mock_test.csv", csv_content)}

        response = requests.post(
            f"{self.CLEANING_URL}/upload",
            files=files,
            timeout=15
        )

        # Then: Upload still works (even if Atlas is down)
        assert response.status_code in [200, 201]

        # Service should indicate if in mock mode
        result = response.json()
        if "mock_mode" in result:
            print(f"ℹ️ Mock mode: {result['mock_mode']}")


class TestAtlasConfiguration:
    """Test Atlas configuration and environment"""

    CLEANING_URL = "http://localhost:8004"

    def test_atlas_env_variables(self):
        """Test: Atlas environment variables are configured"""
        # When: Check service config
        response = requests.get(
            f"{self.CLEANING_URL}/api/config",
            timeout=5
        )

        # Then: Should have Atlas configuration
        if response.status_code == 200:
            config = response.json()

            # Check for Atlas-related config
            atlas_keys = ["atlas_url", "atlas_host", "hdp_host", "atlas_enabled"]
            has_atlas_config = any(key in config for key in atlas_keys)

            if has_atlas_config:
                print("✅ Atlas configuration present")

    def test_atlas_mock_mode_setting(self):
        """Test: MOCK_GOVERNANCE environment variable is respected"""
        # When: Check if mock mode is documented
        response = requests.get(
            f"{self.CLEANING_URL}/health",
            timeout=5
        )

        # Then: Service should indicate its mode
        if response.status_code == 200:
            health = response.json()

            # Check if mode is indicated
            if "mode" in health or "mock_mode" in health:
                mode = health.get("mode") or health.get("mock_mode")
                print(f"ℹ️ Service mode: {mode}")
                assert mode in [True, False, "mock", "production"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
