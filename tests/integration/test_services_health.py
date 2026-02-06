"""
Integration Test: Services Health Check
Tests that all 9 microservices are running and healthy
"""
import pytest
import requests
import time

class TestServicesHealth:
    """Test all services are running and responding"""

    def test_wait_for_services(self, services_urls):
        """Wait for all services to be ready (max 60 seconds)"""
        max_wait = 60
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                # Test one service to see if they're up
                response = requests.get(f"{services_urls['auth']}/health", timeout=2)
                if response.status_code == 200:
                    print("\n[OK] Services are ready!")
                    return
            except:
                time.sleep(2)
                print("[WAIT] Waiting for services to start...")

        pytest.fail("Services did not start within 60 seconds")

    def test_auth_service_health(self, services_urls):
        """Test auth service health"""
        response = requests.get(f"{services_urls['auth']}/health", timeout=5)
        assert response.status_code == 200
        print("[OK] Auth Service: HEALTHY")

    def test_taxonomie_service_health(self, services_urls):
        """Test taxonomie service health"""
        try:
            response = requests.get(f"{services_urls['taxonomie']}/health", timeout=5)
            assert response.status_code == 200
            print("[OK] Taxonomie Service: HEALTHY")
        except Exception as e:
            pytest.fail(f"Taxonomie service not healthy: {e}")

    def test_presidio_service_health(self, services_urls):
        """Test presidio service health"""
        response = requests.get(f"{services_urls['presidio']}/health", timeout=5)
        assert response.status_code == 200
        print("[OK] Presidio Service: HEALTHY")

    def test_cleaning_service_health(self, services_urls):
        """Test cleaning service health"""
        response = requests.get(f"{services_urls['cleaning']}/health", timeout=5)
        assert response.status_code == 200
        print("[OK] Cleaning Service: HEALTHY")

    def test_classification_service_health(self, services_urls):
        """Test classification service health"""
        response = requests.get(f"{services_urls['classification']}/health", timeout=5)
        assert response.status_code == 200
        print("[OK] Classification Service: HEALTHY")

    def test_all_services_summary(self, services_urls):
        """Summary of all services health"""
        results = {}
        for service_name, url in services_urls.items():
            if service_name == "nginx":
                continue
            try:
                response = requests.get(f"{url}/health", timeout=5)
                results[service_name] = "[OK] HEALTHY" if response.status_code == 200 else "[FAIL] UNHEALTHY"
            except Exception as e:
                results[service_name] = f"[FAIL] ERROR: {str(e)[:30]}"

        print("\n" + "="*50)
        print("SERVICES HEALTH SUMMARY")
        print("="*50)
        for service, status in results.items():
            print(f"{service:20} : {status}")
        print("="*50)

        # Assert all are healthy
        unhealthy = [s for s, status in results.items() if "[FAIL]" in status]
        assert len(unhealthy) == 0, f"Unhealthy services: {unhealthy}"
