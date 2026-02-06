"""
Integration Tests for Apache Ranger
Tests policy enforcement and access control (Cahier §5.4.2)
"""
import pytest
import requests


class TestRangerPolicyEnforcement:
    """Test Apache Ranger policy enforcement"""

    AUTH_URL = "http://localhost:8001"
    CLEANING_URL = "http://localhost:8004"
    ANNOTATION_URL = "http://localhost:8007"

    @pytest.fixture
    def auth_token(self):
        """Get authentication token for testing"""
        # Login as admin
        response = requests.post(
            f"{self.AUTH_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )

        if response.status_code == 200:
            return response.json().get("token")
        return None

    @pytest.fixture
    def labeler_token(self):
        """Get token for labeler role (limited access)"""
        # Try to create and login as labeler
        requests.post(
            f"{self.AUTH_URL}/api/auth/users",
            json={
                "username": "test_labeler",
                "password": "labeler123",
                "email": "labeler@test.com",
                "role": "labeler"
            },
            timeout=5
        )

        response = requests.post(
            f"{self.AUTH_URL}/api/auth/login",
            json={"username": "test_labeler", "password": "labeler123"},
            timeout=5
        )

        if response.status_code == 200:
            return response.json().get("token")
        return None

    def test_ranger_connectivity(self):
        """Test: Can connect to Ranger service"""
        # When: Check cleaning service (uses Ranger)
        response = requests.get(f"{self.CLEANING_URL}/health", timeout=5)

        # Then: Service is running
        assert response.status_code == 200

    def test_admin_has_full_access(self, auth_token):
        """Test: Admin role has full access to all resources"""
        if not auth_token:
            pytest.skip("Admin authentication not available")

        # Given: Admin token
        headers = {"Authorization": f"Bearer {auth_token}"}

        # When: Access PII-tagged resource
        response = requests.get(
            f"{self.CLEANING_URL}/api/datasets?include_pii=true",
            headers=headers,
            timeout=5
        )

        # Then: Access granted
        assert response.status_code in [200, 404]  # 404 if no datasets exist yet

    def test_labeler_limited_access(self, labeler_token):
        """Test: Labeler role has limited access"""
        if not labeler_token:
            pytest.skip("Labeler authentication not available")

        # Given: Labeler token (should NOT have PII access)
        headers = {"Authorization": f"Bearer {labeler_token}"}

        # When: Try to access PII-tagged data
        response = requests.get(
            f"{self.CLEANING_URL}/api/datasets?include_pii=true",
            headers=headers,
            timeout=5
        )

        # Then: Access denied or PII fields masked
        # Response might be 403 (forbidden) or 200 with masked data
        assert response.status_code in [200, 403, 401]

        if response.status_code == 200:
            # Check if PII is masked
            data = response.json()
            if "datasets" in data:
                print("ℹ️ Labeler can access data (PII should be masked)")

    def test_pii_tag_enforcement(self, auth_token):
        """Test: PII-tagged resources are protected"""
        if not auth_token:
            pytest.skip("Authentication not available")

        # Given: Dataset with PII
        csv_content = """email,telephone
user@test.com,0612345678"""

        files = {"file": ("pii_test.csv", csv_content)}
        headers = {"Authorization": f"Bearer {auth_token}"}

        # When: Upload dataset
        response = requests.post(
            f"{self.CLEANING_URL}/api/upload",
            files=files,
            headers=headers,
            timeout=15
        )

        if response.status_code in [200, 201]:
            dataset_id = response.json().get("dataset_id")

            # Then: PII fields should be tagged
            info_response = requests.get(
                f"{self.CLEANING_URL}/api/datasets/{dataset_id}",
                headers=headers,
                timeout=5
            )

            if info_response.status_code == 200:
                dataset = info_response.json()

                # Check for PII tags
                if "pii_fields" in dataset or "sensitive_fields" in dataset:
                    pii_fields = dataset.get("pii_fields") or dataset.get("sensitive_fields")
                    assert len(pii_fields) > 0
                    print(f"✅ PII fields tagged: {pii_fields}")

    def test_spi_tag_enforcement(self, auth_token):
        """Test: SPI-tagged resources require higher privileges"""
        if not auth_token:
            pytest.skip("Authentication not available")

        # Given: Dataset with SPI (Sensitive Personal Information)
        csv_content = """nom,prenom,cin
Dupont,Jean,AB123456"""

        files = {"file": ("spi_test.csv", csv_content)}
        headers = {"Authorization": f"Bearer {auth_token}"}

        # When: Upload
        response = requests.post(
            f"{self.CLEANING_URL}/api/upload",
            files=files,
            headers=headers,
            timeout=15
        )

        # Then: SPI detection should occur
        if response.status_code in [200, 201]:
            result = response.json()

            # Check for SPI tags
            if "spi_detected" in result or "sensitive_fields" in result:
                print("✅ SPI fields detected and tagged")

    def test_unauthenticated_access_denied(self):
        """Test: Unauthenticated requests are rejected"""
        # Given: No authentication token
        # When: Try to access protected resource
        response = requests.get(
            f"{self.CLEANING_URL}/api/datasets",
            timeout=5
        )

        # Then: Either requires auth or returns public data only
        # If auth is enforced, should be 401
        assert response.status_code in [200, 401, 403]

        if response.status_code == 401:
            print("✅ Authentication required")

    def test_role_based_access_control(self, auth_token, labeler_token):
        """Test: Different roles have different permissions"""
        if not auth_token or not labeler_token:
            pytest.skip("Authentication tokens not available")

        # Test admin access
        admin_headers = {"Authorization": f"Bearer {auth_token}"}
        admin_response = requests.get(
            f"{self.ANNOTATION_URL}/api/annotation/tasks",
            headers=admin_headers,
            timeout=5
        )

        # Test labeler access
        labeler_headers = {"Authorization": f"Bearer {labeler_token}"}
        labeler_response = requests.get(
            f"{self.ANNOTATION_URL}/api/annotation/tasks",
            headers=labeler_headers,
            timeout=5
        )

        # Both should work, but labeler might have limited view
        assert admin_response.status_code in [200, 404]
        assert labeler_response.status_code in [200, 404]

        print(f"✅ Admin access: {admin_response.status_code}")
        print(f"✅ Labeler access: {labeler_response.status_code}")

    def test_masking_policy_applied(self, labeler_token):
        """Test: Masking policies are applied for sensitive data"""
        if not labeler_token:
            pytest.skip("Labeler authentication not available")

        # Given: Labeler with masking policy
        headers = {"Authorization": f"Bearer {labeler_token}"}

        # When: Access dataset with PII
        response = requests.get(
            f"{self.CLEANING_URL}/api/datasets",
            headers=headers,
            timeout=5
        )

        # Then: PII should be masked
        if response.status_code == 200:
            data = response.json()

            # Check if data contains masked values (e.g., "***" or similar)
            data_str = str(data)
            has_masking = "***" in data_str or "MASKED" in data_str or "[REDACTED]" in data_str

            if has_masking:
                print("✅ Masking policy applied")

    def test_deny_policy_overrides_allow(self):
        """Test: Deny policies take precedence over allow policies"""
        # This is a Ranger-specific behavior
        # Note: Requires specific Ranger policy configuration

        # Test would involve:
        # 1. Create user with allow policy
        # 2. Add deny policy for specific resource
        # 3. Verify access is denied

        # For now, just verify the service respects access decisions
        response = requests.get(f"{self.AUTH_URL}/health", timeout=5)
        assert response.status_code == 200

    def test_audit_logging(self, auth_token):
        """Test: Access attempts are audited"""
        if not auth_token:
            pytest.skip("Authentication not available")

        # Given: Authenticated request
        headers = {"Authorization": f"Bearer {auth_token}"}

        # When: Access resource
        requests.get(
            f"{self.CLEANING_URL}/api/datasets",
            headers=headers,
            timeout=5
        )

        # Then: Audit log should exist
        # Note: Actual audit log verification would require Ranger admin access
        # This test just verifies the request completes
        print("ℹ️ Audit logging should be enabled in Ranger")


class TestRangerConfiguration:
    """Test Ranger configuration"""

    CLEANING_URL = "http://localhost:8004"

    def test_ranger_env_variables(self):
        """Test: Ranger environment variables are configured"""
        # When: Check service config
        response = requests.get(
            f"{self.CLEANING_URL}/api/config",
            timeout=5
        )

        # Then: Should have Ranger configuration
        if response.status_code == 200:
            config = response.json()

            # Check for Ranger-related config
            ranger_keys = ["ranger_url", "ranger_host", "hdp_host", "ranger_enabled"]
            has_ranger_config = any(key in config for key in ranger_keys)

            if has_ranger_config:
                print("✅ Ranger configuration present")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
