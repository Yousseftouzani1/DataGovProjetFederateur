# 🧪 Comprehensive Testing Guide - Real Functional Tests

## Overview

This test suite provides **real functional validation** of the DataGov platform against the Cahier des Charges requirements.

**Unlike basic health checks**, these tests verify:
✅ ML models actually work (BERT, T5)
✅ Atlas metadata registration
✅ Ranger policy enforcement
✅ Data quality metrics (ISO 25012)
✅ PII detection accuracy
✅ End-to-end pipeline functionality

---

## Test Structure

```
tests/
├── unit/                                    # ML Model Tests
│   ├── test_classification_ml.py            # BERT classifier tests (§5.2.2-E)
│   └── test_correction_ml.py                # T5 correction tests (§5.2.2-F)
│
├── integration/                             # Service Integration Tests
│   ├── test_services_health.py              # Basic health checks
│   ├── test_atlas_integration.py            # Atlas metadata tests (§5.4.1)
│   └── test_ranger_policies.py              # Ranger RBAC tests (§5.4.2)
│
├── e2e/                                     # End-to-End Workflow Tests
│   └── test_full_pipeline.py                # Complete pipeline test (§5.3)
│
└── results/                                 # Test reports (HTML)
```

---

## Quick Start

### Option 1: Run All Tests (Recommended)

```bash
# 1. Start services
docker-compose up -d

# 2. Wait 30 seconds for initialization
timeout /t 30

# 3. Run all comprehensive tests
RUN_COMPREHENSIVE_TESTS.bat
```

This will:
- ✅ Run 48+ functional tests
- ✅ Generate HTML reports
- ✅ Validate Cahier des Charges compliance

---

### Option 2: Run Specific Test Suites

#### Unit Tests Only (ML Models)
```bash
pytest tests/unit/ -v -s
```

**Tests**:
- BERT classification accuracy
- T5 correction quality
- Confidence scoring
- CPU-only mode verification

**Expected time**: 2-3 minutes

---

#### Integration Tests Only (Atlas/Ranger)
```bash
pytest tests/integration/ -v -s
```

**Tests**:
- Atlas metadata registration
- Ranger policy enforcement
- RBAC verification
- MongoDB persistence

**Expected time**: 3-5 minutes

---

#### E2E Tests Only (Full Pipeline)
```bash
pytest tests/e2e/ -v -s
```

**Tests**:
- Complete data workflow
- PII detection → Classification → Correction → Quality
- Large dataset handling (1000+ rows)

**Expected time**: 5-10 minutes

---

## Test Coverage

### 1. ML Model Tests (Unit)

#### Classification Service (BERT)
| Test | Validates | Expected Result |
|------|-----------|-----------------|
| `test_classify_email_column` | Email detection | Classification: EMAIL/PII, Confidence >0.5 |
| `test_classify_name_column` | Name detection | Classification: NOM/NAME/PII |
| `test_classify_phone_column` | Phone detection | Classification: PHONE/TELEPHONE |
| `test_ensemble_voting` | BERT+RF+Rules | Ensemble votes from all 3 models |
| `test_cpu_mode_works` | No CUDA errors | Runs on CPU successfully |
| `test_confidence_score_range` | Valid scores | 0.0 ≤ confidence ≤ 1.0 |

#### Correction Service (T5)
| Test | Validates | Expected Result |
|------|-----------|-----------------|
| `test_correct_email_typo` | Email corrections | gmial.com → gmail.com |
| `test_correct_date_format` | Date validation | 2023-13-01 → 2023-01-01 |
| `test_correct_phone_format` | Phone standardization | Adds prefix, standardizes format |
| `test_context_aware_correction` | Uses row context | Better suggestions with context |
| `test_confidence_scoring` | Valid confidence | 0.0 ≤ confidence ≤ 1.0 |

---

### 2. Integration Tests

#### Atlas Integration
| Test | Validates | Expected Result |
|------|-----------|-----------------|
| `test_dataset_metadata_registration` | Atlas GUID generation | Dataset registered with GUID |
| `test_column_metadata_registration` | Column registration | Columns registered in Atlas |
| `test_pii_classification_tagging` | PII tags applied | PII columns tagged in Atlas |
| `test_lineage_tracking` | Data lineage | Lineage tracked through pipeline |
| `test_taxonomy_sync_to_atlas` | Taxonomy sync | Taxonomies synced on startup |

#### Ranger Policies
| Test | Validates | Expected Result |
|------|-----------|-----------------|
| `test_admin_has_full_access` | Admin RBAC | Admin can access PII |
| `test_labeler_limited_access` | Labeler restrictions | Labeler cannot access PII |
| `test_pii_tag_enforcement` | Tag-based policies | PII-tagged resources protected |
| `test_spi_tag_enforcement` | SPI enforcement | SPI requires higher privileges |
| `test_masking_policy_applied` | Data masking | PII masked for unauthorized users |

---

### 3. End-to-End Tests

#### Full Pipeline Workflow
**Test**: `test_complete_pipeline_workflow`

**Steps**:
1. Upload CSV → Cleaning Service
2. Profile data → ydata-profiling
3. Clean data → Remove duplicates, nulls
4. Detect PII → Presidio + Taxonomie
5. Classify columns → BERT ensemble
6. Detect errors → Quality analysis
7. Apply corrections → T5 model
8. Generate quality report → ISO 25012

**Expected Results**:
- ✅ Dataset uploaded successfully
- ✅ PII fields detected (email, telephone)
- ✅ Columns classified correctly
- ✅ Errors detected (typos, invalid dates)
- ✅ Quality report generated (accuracy, completeness, consistency)
- ✅ Data persisted in MongoDB

---

#### PII Detection & Masking
**Test**: `test_pii_detection_and_masking`

**Steps**:
1. Upload dataset with PII (email, phone, CIN)
2. Verify PII detected by both Presidio and Taxonomie
3. Apply EthiMask masking
4. Verify masked data

**Expected Results**:
- ✅ Email, telephone, CIN detected as PII
- ✅ Masking applied (hash/redaction)
- ✅ Original data preserved for authorized users

---

## Interpreting Results

### Success Criteria

**✅ PASS** - All tests must pass to claim Cahier des Charges compliance:

| Category | Tests | Threshold |
|----------|-------|-----------|
| Unit Tests (ML) | 15+ tests | 100% pass |
| Integration (Atlas/Ranger) | 15+ tests | 100% pass |
| E2E (Pipeline) | 5+ tests | 100% pass |
| **TOTAL** | **35+ tests** | **100% pass** |

---

### Test Output Examples

#### ✅ Successful Test
```
tests/unit/test_classification_ml.py::TestBERTClassification::test_classify_email_column PASSED
✅ email detected as PII
Confidence: 0.87
```

#### ❌ Failed Test
```
tests/integration/test_atlas_integration.py::test_dataset_metadata_registration FAILED
AssertionError: No atlas_guid returned
Expected: GUID string
Got: None
```

---

## HTML Reports

After running tests, HTML reports are generated in `tests/results/`:

```
tests/results/
├── unit_tests_20260206_012345.html
├── integration_tests_20260206_012345.html
└── e2e_tests_20260206_012345.html
```

**To view**:
```bash
start tests\results\unit_tests_20260206_012345.html
```

Reports include:
- ✅ Pass/fail status
- ⏱️ Execution time
- 📊 Stack traces for failures
- 📝 Test coverage stats

---

## Troubleshooting

### "Services not running" Error
```bash
# Start services
docker-compose up -d

# Wait for initialization
timeout /t 30

# Verify services are up
docker-compose ps
```

### "Connection refused" Error
```bash
# Services might still be starting
# Wait 30 more seconds
timeout /t 30

# Check specific service logs
docker-compose logs classification-service
```

### "CUDA not available" Warning
This is **expected and correct**! We use CPU-only PyTorch.
```python
# Tests verify CPU mode works:
assert "cuda" not in error_message or response.status_code == 200
```

### "Atlas/Ranger not responding" Error
```bash
# Check if HDP is configured
cat .env | grep HDP_HOST

# Verify mock mode setting
cat .env | grep MOCK_GOVERNANCE

# If HDP is not available, tests will skip or use mock mode
```

---

## Adding New Tests

### Create Unit Test
```python
# tests/unit/test_my_feature.py
import pytest
import requests

class TestMyFeature:
    BASE_URL = "http://localhost:8005"

    def test_feature_works(self):
        """Test: My feature does X"""
        # Given: Input data
        payload = {"test": "data"}

        # When: Call service
        response = requests.post(
            f"{self.BASE_URL}/api/my-endpoint",
            json=payload
        )

        # Then: Verify result
        assert response.status_code == 200
        assert response.json()["result"] == "expected"
```

### Run Your New Test
```bash
pytest tests/unit/test_my_feature.py -v -s
```

---

## Test Data

### Sample Datasets

#### Clean Dataset (No Errors)
```csv
nom,email,age
Dupont,user@example.com,30
Martin,contact@test.fr,25
```

#### Dataset with Issues (For Testing)
```csv
nom,email,telephone,date_naissance
Dupont,jean@gmial.com,0612345678,2023-13-01
Martin,invalid-email,622334455,invalid
El Amrani,,0612345678,1990-01-15
```

---

## Performance Benchmarks

Expected test execution times:

| Test Suite | Tests | Time | Notes |
|------------|-------|------|-------|
| Unit (ML) | 15 tests | 2-3 min | CPU-only PyTorch |
| Integration | 15 tests | 3-5 min | Requires services running |
| E2E Pipeline | 5 tests | 5-10 min | Includes 30s wait for Airflow |
| **Total** | **35+ tests** | **10-18 min** | Full validation |

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 30
      - name: Run tests
        run: |
          pip install pytest pytest-cov pytest-html requests
          pytest tests/ -v --cov --html=report.html
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: report.html
```

---

## Next Steps

1. ✅ **Run basic health check first**: `RUN_TESTS.bat`
2. ✅ **Run comprehensive tests**: `RUN_COMPREHENSIVE_TESTS.bat`
3. ✅ **Review HTML reports** in `tests/results/`
4. ✅ **Fix any failing tests**
5. ✅ **Add custom tests** for your specific requirements
6. ✅ **Integrate into CI/CD** pipeline

---

## Support

If tests fail:
1. Check `tests/results/*.html` for detailed error messages
2. Verify services are running: `docker-compose ps`
3. Check service logs: `docker-compose logs [service-name]`
4. Review test code in `tests/` directory
5. Ensure .env variables are configured (HDP_HOST, etc.)

---

**Last updated**: 2026-02-06
**Test suite version**: 1.0
**Coverage**: 48+ comprehensive tests validating Cahier des Charges compliance
