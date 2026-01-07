# 📁 Correction Service V2 - Project Structure

## Overview
Professional Data Quality service with ML-based intelligent correction, human validation, and continuous learning.

---

## 📂 Directory Structure

```
correction-serv/
├── 📄 main.py                          # FastAPI Application (MAIN ENTRY POINT)
├── 📄 requirements.txt                  # Python Dependencies
├── 📄 Dockerfile                        # Container Configuration
├── 📄 .env                              # Environment Variables (create this)
│
├── 📚 Documentation/
│   ├── README.md                        # Feature Guide & API Reference
│   ├── DEPLOYMENT.md                    # Production Setup Guide
│   ├── PROJECT_STRUCTURE.md             # This file
│   └── IMPLEMENTATION_SUMMARY.md        # What Was Built
│
├── 🧪 tests/
│   └── test_comprehensive.py            # Complete Test Suite
│
├── 💡 Examples/
│   └── example_usage.py                 # End-to-End Workflow Demo
│
└── 🔧 backend/
    ├── database/
    │   └── mongodb.py                   # MongoDB Connection
    │
    ├── models/
    │   ├── detection_engine.py          # Inconsistency Detection (6 types)
    │   ├── correction_engine.py         # Algorithm 6 (Rule + ML)
    │   ├── validation_manager.py        # Human Validation Workflow
    │   ├── learning_engine.py           # Continuous Learning & Retraining
    │   ├── report_generator.py          # Comprehensive Reports
    │   ├── kpi_tracker.py               # KPI Monitoring
    │   ├── inconsistency.py             # Data Models
    │   ├── rules_loader.py              # YAML Rule Loading
    │   └── ml/
    │       ├── text_correction_t5.py    # T5 Model (ML Correction)
    │       └── numeric_regression.py    # Statistical Correction
    │
    └── rules/
        └── correction_rules.yaml        # Correction Rules (Data Steward managed)
```

---

## 🎯 File Responsibilities

### 🚀 Entry Point

#### `main.py` (640 lines)
**Purpose**: FastAPI application with all API endpoints

**What it does**:
- Initializes all engines (detection, correction, validation, learning, reporting, KPI)
- Loads T5 model on startup
- Provides 20+ REST API endpoints
- Handles request/response validation
- Background task processing
- CORS middleware

**Key Endpoints**:
- Detection: `POST /detect`
- Correction: `POST /correct`
- Validation: `GET /corrections/pending`, `POST /corrections/validate/{id}`
- Learning: `GET /learning/stats`, `POST /learning/retrain`
- Reporting: `POST /reports/corrections`
- KPIs: `GET /kpi/dashboard`

**Used by**: Everything (this is the main application)

---

### 🔍 Detection & Correction

#### `backend/models/detection_engine.py` (218 lines)
**Purpose**: Detect all 6 types of inconsistencies

**What it does**:
- FORMAT: Invalid dates, emails, phones using regex patterns
- DOMAIN: Out-of-range values (age, temperature, etc.)
- REFERENTIAL: Invalid field combinations (Paris + Morocco)
- TEMPORAL: Date ordering issues
- STATISTICAL: Outlier detection (IQR, Z-score)
- SEMANTIC: Type mismatches (phone in email field)

**Input**: Single data row (dict)
**Output**: List of `Inconsistency` objects with type, field, value, message

**Used by**: `main.py` (`/detect`, `/correct` endpoints)

---

#### `backend/models/correction_engine.py` (208 lines)
**Purpose**: Implement Algorithm 6 (Section 8.5) - Intelligent Correction

**What it does**:
1. Generate rule-based correction candidates from YAML rules
2. Generate ML-based candidates using T5 model
3. Rank candidates by confidence score
4. Select best candidate
5. Auto-apply if confidence >= 0.9, else queue for review
6. Log all decisions for traceability

**Input**: Row + list of inconsistencies
**Output**: Corrected row + list of correction logs

**Collaborates with**:
- `rules_loader.py` - Load correction rules
- `ml/text_correction_t5.py` - ML suggestions
- `ml/numeric_regression.py` - Numeric corrections

**Used by**: `main.py` (`/correct` endpoint)

---

### 🤖 Machine Learning

#### `backend/models/ml/text_correction_t5.py` (400+ lines)
**Purpose**: T5-based intelligent text correction

**What it does**:
- Loads pre-trained T5 model (t5-small or t5-base)
- Generates context-aware correction suggestions
- Format: `"correct: <value> context: <field>" → <corrected_value>`
- Batch processing for efficiency
- Confidence scoring based on model probabilities
- Fine-tuning capability for continuous learning

**Key Features**:
- Lazy loading (only loads when first used)
- GPU acceleration support
- Model caching
- Validation checks on outputs

**Used by**: `correction_engine.py` (ML candidate generation)

---

#### `backend/models/ml/numeric_regression.py` (173 lines)
**Purpose**: Statistical correction for numeric values

**What it does**:
- IQR (Interquartile Range) outlier detection
- Z-score outlier detection (threshold: 3.0)
- Domain-specific clamping (age, salary, percentage)
- NaN/Inf handling
- Median-based outlier correction

**Input**: Field name, value, optional context values
**Output**: Corrected value, confidence score

**Used by**: `correction_engine.py` (numeric field corrections)

---

### 👥 Human Validation

#### `backend/models/validation_manager.py` (390+ lines)
**Purpose**: Manage human validation workflow (US-CORR-04)

**What it does**:
- **ValidationQueue**: Priority queue for corrections needing review
- **validate_correction()**: Record accept/reject/modify decisions
- **batch_validate()**: Bulk validation support
- **Validator statistics**: Track performance by validator
- **Training example creation**: Convert validations to ML training format

**Data Flow**:
1. Low-confidence corrections added to queue
2. Data Annotator retrieves pending validations
3. Human makes decision (accept/reject/modify)
4. Decision recorded with timestamp, comments
5. Training example created for learning

**Used by**: `main.py` (validation endpoints), `learning_engine.py`

---

### 📚 Continuous Learning

#### `backend/models/learning_engine.py` (380+ lines)
**Purpose**: Learn from validations to improve accuracy (US-CORR-05)

**What it does**:
- Collect validated corrections as training examples
- Format for T5: `{"input": "correct: X context: Y", "output": "Z"}`
- Trigger retraining every 100 validations
- Model versioning (saves each trained version)
- Track accuracy improvement month-over-month
- Export training data for analysis

**Key Methods**:
- `record_validation()` - Add validation to training pool
- `retrain_model()` - Fine-tune T5 on validated examples
- `get_learning_stats()` - Learning progress metrics
- `get_accuracy_trend()` - Monthly improvement (+5% target)

**Used by**: `main.py` (learning endpoints), background tasks

---

### 📊 Reporting & KPIs

#### `backend/models/report_generator.py` (400+ lines)
**Purpose**: Generate comprehensive correction reports (US-CORR-06)

**What it does**:
- Summary statistics (total, auto, manual, acceptance rate)
- Breakdown by inconsistency type
-Breakdown by field
- Confidence score distributions(min, max, mean, percentiles)
- Timeline of corrections
- Validator contributions analysis
- KPI metrics calculation
- Export to JSON/Excel

**Report Structure**:
```json
{
  "summary": {...},
  "breakdown_by_type": {...},
  "breakdown_by_field": {...},
  "confidence_distribution": {...},
  "timeline": [...],
  "validator_contributions": {...},
  "correction_details": [...],
  "kpi_metrics": {...}
}
```

**Used by**: `main.py` (`/reports/corrections` endpoint)

---

#### `backend/models/kpi_tracker.py` (380+ lines)
**Purpose**: Track and monitor KPIs (Section 8.7)

**What it does**:
- Track 5 KPIs from specification:
  1. Detection rate > 95%
  2. Auto-correction precision > 90%
  3. Auto-correction rate > 70%
  4. Processing time < 5s per 1000 rows
  5. Monthly accuracy improvement +5%
- Record KPI snapshots over time
- Calculate trend analysis
- Generate compliance alerts
- Dashboard metrics with health score

**Used by**: `main.py` (`/kpi/*` endpoints), background tasks

---

### ⚙️ Configuration & Data

#### `backend/models/rules_loader.py` (100 lines)
**Purpose**: Load and cache correction rules from YAML

**What it does**:
- Load `correction_rules.yaml`
- Pre-compile regex patterns for performance
- Cache rules in memory
- Force reload capability

**Used by**: `detection_engine.py`, `correction_engine.py`

---

#### `backend/rules/correction_rules.yaml` (200+ lines)
**Purpose**: Define correction rules (managed by Data Stewards)

**Contains**:
- FORMAT patterns (email, phone, date, etc.)
- DOMAIN ranges (age, temperature, salary, etc.)
- REFERENTIAL constraints (valid city-country pairs)
- TEMPORAL rules (date ordering, age gaps)
- STATISTICAL thresholds (IQR, Z-score)
- SEMANTIC type definitions
- Correction strategies (CLAMP, NORMALIZE, ML_CORRECTION, etc.)
- Confidence thresholds (0.9 for auto-apply)
- KPI targets

**Edited by**: Data Stewards (US-CORR-02)
**Loaded by**: `rules_loader.py`

---

#### `backend/models/inconsistency.py` (11 lines)
**Purpose**: Data model for inconsistencies

**What it contains**:
```python
class Inconsistency:
    field: str       # Field name
    value: any       # Problematic value
    type: str        # FORMAT, DOMAIN, etc.
    message: str     # Human-readable description
```

**Used by**: Detection and correction engines

---

### 💾 Database

#### `backend/database/mongodb.py` (17 lines)
**Purpose**: MongoDB connection management

**What it does**:
- Connect to MongoDB using Motor (async)
- Load connection string from environment
- Provide `db` object for all services

**Collections used**:
- `correction_validations` - Corrections and validations
- `correction_training_data` - ML training examples
- `correction_kpi_history` - KPI snapshots
- `correction_performance` - Processing time tracking
- `correction_model_versions` - Fine-tuned model metadata

**Used by**: All engines that need persistence

---

## 🔄 Data Flow

### Complete Workflow

```
1. Request arrives at main.py
   ↓
2. Detection Engine - Finds inconsistencies (6 types)
   ↓
3. Correction Engine - Generates corrections (Algorithm 6)
   │  ├─ Rules Loader - Load YAML rules
   │  ├─ T5 Model - ML suggestions
   │  └─ Numeric Regressor - Statistical corrections
   ↓
4. Decision Point:
   ├─ Confidence >= 0.9 → Auto-apply ✅
   └─ Confidence < 0.9 → Queue for review ⏸
   ↓
5. (If queued) Validation Manager
   │  └─ Human validates (accept/reject/modify)
   ↓
6. Learning Engine - Records for training
   │  └─ Triggers retraining every 100 validations
   ↓
7. KPI Tracker - Records metrics
   ↓
8. Report Generator - Creates report (if requested)
```

---

## 🚀 Performance Optimizations

### Implemented

1. **T5 Model**:
   - Lazy loading (only when first correction requested)
   - Batch processing (up to 8 items at once)
   - Model caching in memory
   - Optional GPU acceleration

2. **Rules**:
   - YAML loaded once on startup
   - Regex patterns pre-compiled
   - Cached in memory with `force_reload` option

3. **Database**:
   - Async operations (Motor)
   - Connection pooling
   - Indexed queries (dataset_id, timestamp, status)

4. **Detection**:
   - Early termination on no inconsistencies
   - Parallel type checking where possible

5. **API**:
   - Background tasks for non-critical operations
   - Async endpoints
   - CORS pre-flight caching

### Latency Targets

- Detection: < 100ms per row
- Correction (rule-based): < 50ms
- Correction (ML-based): < 200ms per field
- Total: < 5s per 1000 rows ✅

---

## 📦 Dependencies

### Core (FastAPI)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

### Database
- `motor` - Async MongoDB driver
- `dnspython` - MongoDB DNS support

### Data Processing
- `pandas` - DataFrame operations
- `numpy` - Numerical computing
- `scikit-learn` - Statistical methods

### Machine Learning
- `transformers` - T5 model
- `torch` - PyTorch backend
- `sentencepiece` - Tokenizer

### Configuration
- `pyyaml` - YAML parsing
- `python-dotenv` - Environment variables

---

## 🧪 Testing

### `tests/test_comprehensive.py`

**Coverage**:
- ✅ All 6 inconsistency types (FORMAT, DOMAIN, REFERENTIAL, TEMPORAL, STATISTICAL, SEMANTIC)
- ✅ T5 model loading and correction
- ✅ Algorithm 6 implementation
- ✅ Validation workflow
- ✅ Learning system
- ✅ KPI calculations
- ✅ End-to-end workflow
- ✅ Performance (< 5s per 1000 rows)

**Run**: `pytest tests/test_comprehensive.py -v`

---

## 📖 Documentation

### User Guides
- `README.md` - Feature overview, API guide, user stories
- `DEPLOYMENT.md` - Installation, configuration, production setup
- `example_usage.py` - Complete workflow demonstration

### Developer Guides
- `PROJECT_STRUCTURE.md` - This file
- `IMPLEMENTATION_SUMMARY.md` - What was built, compliance checklist
- API Docs - http://localhost:8006/docs (auto-generated)

---

## 🎓 For Different Roles

### Data Stewards
- Edit: `backend/rules/correction_rules.yaml`
- Monitor: `GET /kpi/dashboard`
- Reload: `POST /rules/reload`

### Data Annotators
- Review: `GET /corrections/pending`
- Validate: `POST /corrections/validate/{id}`
- Batch: `POST /corrections/batch-validate`

### System Administrators
- Deploy: Follow `DEPLOYMENT.md`
- Monitor: KPI dashboard + logs
- Backup: MongoDB + fine-tuned models

### Developers
- API: http://localhost:8006/docs
- Test: `pytest tests/`
- Extend: Add patterns to YAML, implement new strategies

---

## 🔧 Customization Points

### Easy to Modify
1. **Correction Rules** (`correction_rules.yaml`)
   - Add new patterns
   - Adjust ranges
   - Define strategies

2. **T5 Model** (`main.py` startup)
   - Switch t5-small ↔ t5-base
   - Enable GPU
   - Adjust batch size

3. **Confidence Thresholds** (`correction_rules.yaml`)
   - Auto-apply threshold (default: 0.9)
   - Manual review threshold (default: 0.6)

4. **KPI Targets** (`kpi_tracker.py`)
   - Modify target values
   - Add custom metrics

5. **Retraining Frequency** (`learning_engine.py`)
   - Change from 100 to N validations

---

## 🏆 Code Quality

- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Error handling with logging
- ✅ Async/await for I/O
- ✅ Modular architecture
- ✅ Single responsibility principle
- ✅ Configuration over code
- ✅ Testable components

---

**Version**: 2.0.0  
**Status**: Production Ready ✅  
**Last Updated**: 2026-01-07
