"""
Tests for Cleaning Service - Tâche 4
Run with: pytest tests/test_cleaning/ -v
"""
import pytest
from fastapi.testclient import TestClient
import pandas as pd
import io
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'cleaning-serv'))

from main import app, DataProfiler, OutlierDetector, DataCleaner

client = TestClient(app)


# ====================================================================
# FIXTURES
# ====================================================================

@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing"""
    return b"name,age,salary,city\nAlice,25,50000,Casablanca\nBob,30,60000,Rabat\nCharlie,25,55000,Marrakech\nAlice,25,50000,Casablanca\nDavid,,70000,Fes\n"


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing"""
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, None, 28],
        "salary": [50000, 60000, 55000, 70000, 1000000],  # Eve is outlier
        "city": ["Casablanca", "Rabat", "Marrakech", "Fes", "Tanger"]
    })


# ====================================================================
# API TESTS
# ====================================================================

class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()


class TestUploadEndpoint:
    def test_upload_csv(self, sample_csv_content):
        files = {"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")}
        response = client.post("/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
        assert data["rows"] == 5
        assert data["columns"] == 4
    
    def test_upload_invalid_format(self):
        files = {"file": ("test.txt", io.BytesIO(b"invalid content"), "text/plain")}
        response = client.post("/upload", files=files)
        assert response.status_code == 400


class TestProfilingEndpoint:
    def test_profile_stats(self, sample_csv_content):
        # First upload
        files = {"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")}
        upload_response = client.post("/upload", files=files)
        dataset_id = upload_response.json()["dataset_id"]
        
        # Then profile
        response = client.get(f"/profile/{dataset_id}")
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "rows" in data["profile"]
        assert "missing_values" in data["profile"]
    
    def test_profile_not_found(self):
        response = client.get("/profile/nonexistent-id")
        assert response.status_code == 404


class TestOutlierEndpoint:
    def test_detect_outliers(self, sample_csv_content):
        # Upload
        files = {"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")}
        upload_response = client.post("/upload", files=files)
        dataset_id = upload_response.json()["dataset_id"]
        
        # Detect outliers
        response = client.post(f"/outliers/{dataset_id}", json={"method": "iqr"})
        assert response.status_code == 200
        data = response.json()
        assert "total_outliers" in data


class TestCleaningEndpoint:
    def test_clean_remove_duplicates(self, sample_csv_content):
        # Upload
        files = {"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")}
        upload_response = client.post("/upload", files=files)
        dataset_id = upload_response.json()["dataset_id"]
        
        # Clean
        response = client.post(f"/clean/{dataset_id}", json={
            "operations": [{"operation": "remove_duplicates"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["rows_removed"] >= 0
    
    def test_auto_clean(self, sample_csv_content):
        # Upload
        files = {"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")}
        upload_response = client.post("/upload", files=files)
        dataset_id = upload_response.json()["dataset_id"]
        
        # Auto clean
        response = client.post(f"/clean/{dataset_id}/auto")
        assert response.status_code == 200
        assert response.json()["success"] == True


# ====================================================================
# UNIT TESTS
# ====================================================================

class TestDataProfiler:
    def test_basic_stats(self, sample_dataframe):
        profiler = DataProfiler(sample_dataframe)
        stats = profiler.get_basic_stats()
        
        assert stats["rows"] == 5
        assert stats["columns"] == 4
        assert "missing_values" in stats
        assert "numeric_stats" in stats
    
    def test_missing_detection(self, sample_dataframe):
        profiler = DataProfiler(sample_dataframe)
        stats = profiler.get_basic_stats()
        
        assert stats["missing_values"]["age"] == 1  # David has no age


class TestOutlierDetector:
    def test_iqr_detection(self, sample_dataframe):
        detector = OutlierDetector(sample_dataframe)
        outliers = detector.detect_iqr("salary", multiplier=1.5)
        
        assert outliers.sum() >= 1  # Eve's salary is outlier
    
    def test_zscore_detection(self, sample_dataframe):
        detector = OutlierDetector(sample_dataframe)
        outliers = detector.detect_zscore("salary", threshold=2.0)
        
        assert isinstance(outliers, pd.Series)


class TestDataCleaner:
    def test_remove_duplicates(self):
        df = pd.DataFrame({
            "a": [1, 1, 2, 3],
            "b": ["x", "x", "y", "z"]
        })
        cleaner = DataCleaner(df)
        cleaner.remove_duplicates()
        result = cleaner.get_result()
        
        assert len(result) == 3
    
    def test_fill_missing_mean(self, sample_dataframe):
        cleaner = DataCleaner(sample_dataframe)
        cleaner.fill_missing(column="age", strategy="mean")
        result = cleaner.get_result()
        
        assert result["age"].isnull().sum() == 0
    
    def test_standardize_column(self):
        df = pd.DataFrame({"name": ["Alice", "BOB", "Charlie"]})
        cleaner = DataCleaner(df)
        cleaner.standardize_column("name", "lowercase")
        result = cleaner.get_result()
        
        assert result["name"].tolist() == ["alice", "bob", "charlie"]
    
    def test_changes_log(self):
        df = pd.DataFrame({"a": [1, 1, 2]})
        cleaner = DataCleaner(df)
        cleaner.remove_duplicates()
        
        changes = cleaner.get_changes()
        assert len(changes) > 0
        assert "duplicate" in changes[0].lower()
