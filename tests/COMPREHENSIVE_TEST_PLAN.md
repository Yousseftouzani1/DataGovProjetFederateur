# 🧪 Comprehensive Testing Plan - Cahier des Charges Validation

## Overview

This plan defines **real functional tests** that validate compliance with the Cahier des Charges (technical specification).

**Goal**: Verify that all 9 services implement their specified functionality correctly.

---

## Test Coverage Matrix

| Requirement | Cahier Section | Test Type | Status |
|-------------|----------------|-----------|--------|
| **Authentication & RBAC** | §5.2.1-A | Integration | ✅ Planned |
| **PII Detection (Presidio)** | §5.2.2-C | Functional | ✅ Planned |
| **PII Detection (Taxonomie)** | §5.2.2-D | Functional | ✅ Planned |
| **ML Classification (BERT)** | §5.2.2-E | ML Model | ✅ Planned |
| **Text Correction (T5)** | §5.2.2-F | ML Model | ✅ Planned |
| **Data Quality (ISO 25012)** | §5.2.2-H | Functional | ✅ Planned |
| **Apache Atlas Integration** | §5.4.1 | Integration | ✅ Planned |
| **Apache Ranger Policies** | §5.4.2 | Integration | ✅ Planned |
| **MongoDB Persistence** | §5.6.1 | Integration | ✅ Planned |
| **Airflow Pipeline** | §5.3 | E2E | ✅ Planned |

---

## Test Suite Structure

```
tests/
├── unit/                           # Unit tests for individual functions
│   ├── test_auth_rbac.py           # Authentication & authorization
│   ├── test_classification_ml.py   # BERT model accuracy
│   ├── test_correction_ml.py       # T5 model accuracy
│   ├── test_quality_metrics.py     # ISO 25012 calculations
│   └── test_pii_detection.py       # PII detection logic
│
├── integration/                    # Integration tests for service communication
│   ├── test_services_health.py     # Basic health checks (DONE)
│   ├── test_atlas_integration.py   # Atlas metadata registration
│   ├── test_ranger_policies.py     # Ranger access control
│   ├── test_mongodb_persistence.py # Data persistence
│   └── test_service_communication.py # Inter-service calls
│
├── e2e/                            # End-to-end workflow tests
│   ├── test_full_pipeline.py       # Upload → Clean → Classify → Quality
│   ├── test_pii_workflow.py        # PII detection → Masking workflow
│   └── test_annotation_workflow.py # Annotation task creation → completion
│
├── performance/                    # Performance & scalability tests
│   ├── test_load_1000_rows.py      # Handle 1000 rows
│   ├── test_load_10000_rows.py     # Handle 10,000 rows
│   └── test_concurrent_requests.py # 10 simultaneous uploads
│
└── security/                       # Security validation tests
    ├── test_cors_restrictions.py   # CORS properly restricted
    ├── test_jwt_validation.py      # JWT authentication works
    └── test_input_validation.py    # Pydantic validation works
```

---

## Test Categories

### 1. ML Model Tests (Unit)

**Purpose**: Verify ML models produce correct predictions

#### 1.1 Classification Service (BERT)
- ✅ Test BERT model loads successfully
- ✅ Test classification accuracy on sample data
- ✅ Test ensemble voting (BERT + Random Forest + Rules)
- ✅ Test confidence scores are reasonable (0.0-1.0)
- ✅ Test CPU-only mode works (no CUDA errors)

**Example**:
```python
def test_bert_classification_accuracy():
    # Given: Sample data with known labels
    samples = [
        {"column": "email", "values": ["user@example.com"], "expected": "EMAIL"},
        {"column": "nom", "values": ["Dupont"], "expected": "NOM"},
    ]

    # When: Classify using BERT
    classifier = EnsembleClassifier()
    for sample in samples:
        result = classifier.predict(sample["values"])

        # Then: Prediction matches expected
        assert result["class"] == sample["expected"]
        assert result["confidence"] > 0.7
```

#### 1.2 Correction Service (T5)
- ✅ Test T5 model loads successfully
- ✅ Test text correction suggestions are reasonable
- ✅ Test confidence scoring
- ✅ Test context-aware corrections
- ✅ Test CPU-only mode works

**Example**:
```python
def test_t5_correction_quality():
    # Given: Incorrect values with context
    test_cases = [
        {"value": "2023-13-01", "context": "date_naissance", "expected": "2023-01-01"},
        {"value": "user@gmial.com", "context": "email", "expected": "user@gmail.com"},
    ]

    # When: Apply T5 correction
    corrector = TextCorrectionT5()
    for case in test_cases:
        corrected, confidence = corrector.correct(case["value"], case["context"])

        # Then: Correction improves the value
        assert corrected == case["expected"]
        assert confidence > 0.6
```

---

### 2. Integration Tests

**Purpose**: Verify services integrate with external systems correctly

#### 2.1 Atlas Integration
- ✅ Test metadata registration (dataset, columns)
- ✅ Test lineage tracking
- ✅ Test classification tagging (PII, SPI)
- ✅ Test GUID generation
- ✅ Test Atlas API connectivity

**Example**:
```python
@pytest.mark.asyncio
async def test_atlas_metadata_registration():
    # Given: A dataset to register
    dataset = {
        "name": "test_dataset",
        "columns": ["nom", "email", "telephone"]
    }

    # When: Register in Atlas
    atlas_client = AtlasClient.from_env()
    guid = await atlas_client.register_dataset_and_get_guid(dataset)

    # Then: GUID is returned
    assert guid is not None
    assert len(guid) > 0

    # And: Entity exists in Atlas
    entity = await atlas_client.get_entity(guid)
    assert entity["attributes"]["name"] == "test_dataset"
```

#### 2.2 Ranger Policy Enforcement
- ✅ Test access denied for unauthorized users
- ✅ Test access allowed for authorized users
- ✅ Test masking policies applied
- ✅ Test tag-based policies (PII, SPI)

**Example**:
```python
def test_ranger_denies_pii_access():
    # Given: User without PII access
    ranger_client = RangerClient()

    # When: Check access to PII-tagged resource
    decision = ranger_client.check_access(
        username="labeler_user",
        resource_tag="PII"
    )

    # Then: Access is denied
    assert decision.access == "DENIED"
    assert decision.reason == "No policy grants access"
```

#### 2.3 MongoDB Persistence
- ✅ Test data persists after service restart
- ✅ Test MongoDB collections exist
- ✅ Test CRUD operations work
- ✅ Test indexes are created

**Example**:
```python
@pytest.mark.asyncio
async def test_mongodb_data_persists():
    # Given: Create a task in annotation service
    task = {"title": "Label dataset", "status": "pending"}
    response = requests.post("http://localhost:8007/api/annotation/tasks", json=task)
    task_id = response.json()["id"]

    # When: Restart annotation service
    os.system("docker-compose restart annotation-service")
    time.sleep(10)  # Wait for restart

    # Then: Task still exists
    response = requests.get(f"http://localhost:8007/api/annotation/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Label dataset"
```

---

### 3. End-to-End Tests

**Purpose**: Verify complete workflows work end-to-end

#### 3.1 Full Data Pipeline
**Workflow**: Upload → Profile → Clean → Classify → Correct → Quality → Annotate

**Test Steps**:
1. Upload CSV file to cleaning service
2. Wait for Airflow DAG completion
3. Verify quality report generated
4. Verify classifications applied
5. Verify corrections suggested
6. Verify MongoDB has all data

**Example**:
```python
def test_full_data_pipeline():
    # Given: Sample CSV file with PII and errors
    csv_content = """nom,email,telephone,date_naissance
Dupont,user@gmial.com,0612345678,2023-13-01
Martin,invalid-email,invalid,1990-01-01"""

    # When: Upload to cleaning service
    files = {"file": ("test.csv", csv_content)}
    response = requests.post("http://localhost:8004/api/upload", files=files)
    dataset_id = response.json()["dataset_id"]

    # Wait for pipeline completion
    time.sleep(30)

    # Then: Quality report exists
    response = requests.get(f"http://localhost:8008/api/quality/reports/{dataset_id}")
    assert response.status_code == 200
    report = response.json()

    # And: PII detected
    assert "email" in report["pii_fields"]
    assert "telephone" in report["pii_fields"]

    # And: Errors corrected
    assert report["corrections_applied"] > 0

    # And: Classifications assigned
    assert len(report["classifications"]) > 0
```

#### 3.2 PII Detection & Masking Workflow
**Workflow**: Detect PII → Apply masking → Verify masked data

**Test Steps**:
1. Upload dataset with PII
2. Run Presidio + Taxonomie detection
3. Apply EthiMask masking
4. Verify original data preserved
5. Verify masked data doesn't contain PII

---

### 4. Performance Tests

**Purpose**: Verify system handles realistic data volumes

#### 4.1 Load Testing
- ✅ Handle 1,000 rows in < 10 seconds
- ✅ Handle 10,000 rows in < 60 seconds
- ✅ Handle 10 concurrent uploads

**Example**:
```python
def test_handle_10000_rows():
    # Given: Large CSV file (10,000 rows)
    rows = [f"row_{i},test{i}@example.com,0612345678" for i in range(10000)]
    csv_content = "nom,email,telephone\n" + "\n".join(rows)

    # When: Upload to cleaning service
    start_time = time.time()
    files = {"file": ("large.csv", csv_content)}
    response = requests.post("http://localhost:8004/api/upload", files=files)
    elapsed = time.time() - start_time

    # Then: Upload completes in reasonable time
    assert response.status_code == 200
    assert elapsed < 60  # Less than 1 minute
```

---

### 5. Security Tests

**Purpose**: Verify security measures are enforced

#### 5.1 CORS Restrictions
- ✅ Block requests from unauthorized origins
- ✅ Allow requests from localhost:8000 and localhost:3000

**Example**:
```python
def test_cors_blocks_unauthorized_origin():
    # Given: Request from unauthorized origin
    headers = {"Origin": "http://malicious.com"}

    # When: Try to access service
    response = requests.get("http://localhost:8001/api/auth/users", headers=headers)

    # Then: Request is blocked
    assert response.status_code == 403
    assert "CORS" in response.text
```

#### 5.2 JWT Authentication
- ✅ Reject requests without valid JWT
- ✅ Accept requests with valid JWT
- ✅ Reject expired JWTs

---

## Test Execution Plan

### Phase 1: Unit Tests (Day 1)
```bash
pytest tests/unit/ -v --cov
```

**Expected results**:
- ML models load successfully
- Predictions are accurate (>70% confidence)
- All unit tests pass

---

### Phase 2: Integration Tests (Day 2)
```bash
pytest tests/integration/ -v --cov
```

**Expected results**:
- Atlas integration works
- Ranger policies enforced
- MongoDB persistence confirmed
- Services communicate correctly

---

### Phase 3: E2E Tests (Day 3)
```bash
pytest tests/e2e/ -v --cov
```

**Expected results**:
- Full pipeline completes successfully
- Quality reports generated
- Data persists across restarts

---

### Phase 4: Performance Tests (Day 4)
```bash
pytest tests/performance/ -v
```

**Expected results**:
- Handles 10,000 rows
- No memory leaks
- Reasonable response times

---

## Success Criteria

To claim **Cahier des Charges compliance**, all tests must pass:

| Category | Tests | Pass Threshold |
|----------|-------|----------------|
| Unit Tests | 20+ tests | 100% pass |
| Integration Tests | 15+ tests | 100% pass |
| E2E Tests | 5+ tests | 100% pass |
| Performance Tests | 3+ tests | 100% pass |
| Security Tests | 5+ tests | 100% pass |

**Total**: 48+ comprehensive tests

---

## Next Steps

1. ✅ Create unit tests for ML models
2. ✅ Create integration tests for Atlas/Ranger
3. ✅ Create E2E pipeline test
4. ✅ Create performance tests
5. ✅ Run all tests and document results
6. ✅ Fix any failing tests
7. ✅ Generate coverage report

---

**Last updated**: 2026-02-06
**Test suite**: Comprehensive validation of Cahier des Charges requirements
