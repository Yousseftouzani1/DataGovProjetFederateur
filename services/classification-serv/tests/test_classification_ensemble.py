import pytest
import requests
import json

BASE_URL = "http://localhost:8005"

def test_health():
    """Verify service is healthy and models are loaded"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "models" in data

def test_classify_english():
    """Test English classification with statistical model"""
    payload = {
        "text": "My CIN is AB123456",
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["classification"] == "PERSONAL_IDENTITY"
    assert data["sensitivity_level"] == "critical"

def test_classify_french_semantic():
    """Test French classification (should trigger transformer init)"""
    payload = {
        "text": "Ceci est un dossier médical confidentiel",
        "language": "fr"
    }
    response = requests.post(f"{BASE_URL}/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Even if transformer fails, it should fallback safely
    assert "classification" in data

def test_classify_arabic_semantic():
    """Test Arabic classification"""
    payload = {
        "text": "الرقم الوطني الخاص بي هو AB123456",
        "language": "ar"
    }
    response = requests.post(f"{BASE_URL}/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_mongodb_workflow():
    """Test adding to pending queue (requires MongoDB)"""
    payload = {
        "text": "A generic message that is not sensitive but needs review",
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/add-pending", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "classification_id" in data

if __name__ == "__main__":
    # This allows running the test script directly
    try:
        test_health()
        print("✅ Health check passed")
        test_classify_english()
        print("✅ English classification passed")
        test_classify_french_semantic()
        print("✅ French semantic classification passed")
        test_classify_arabic_semantic()
        print("✅ Arabic semantic classification passed")
        test_mongodb_workflow()
        print("✅ MongoDB workflow passed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
