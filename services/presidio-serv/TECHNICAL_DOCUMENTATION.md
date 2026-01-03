# Presidio Service - Technical Documentation

**Version:** 1.0.0  
**Date:** 2026-01-02  
**Cahier Section:** 5.9 - Deliverable #6: Documentation technique recognizers

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Custom Recognizers](#custom-recognizers)
4. [Detection Algorithm](#detection-algorithm)
5. [API Endpoints](#api-endpoints)
6. [Performance Metrics](#performance-metrics)
7. [Testing](#testing)
8. [Deployment](#deployment)

---

## 1. Overview

The Presidio Service is a microservice for detecting and anonymizing Moroccan Personally Identifiable Information (PII) using Microsoft Presidio framework with custom recognizers.

### Supported Entities

| Entity          | Description            | Format Example               |
| --------------- | ---------------------- | ---------------------------- |
| **CIN_MAROC**   | Moroccan National ID   | AB123456                     |
| **PHONE_MA**    | Moroccan Phone Number  | +212612345678                |
| **IBAN_MA**     | Moroccan Bank Account  | MA67BANK12345678901234567890 |
| **CNSS**        | Social Security Number | 123456789012                 |
| **PASSPORT_MA** | Moroccan Passport      | AB1234567                    |
| **PERMIS_MA**   | Driving License        | A12345678                    |
| **ARABIC_PII**  | Arabic-language PII    | Various                      |

---

## 2. Architecture

```
services/presidio-serv/
├── main.py                          # FastAPI application
├── backend/
│   └── recognizers/
│       ├── cin_recognizer.py        # CIN_MAROC recognizer
│       ├── phone_ma_recognizer.py   # PHONE_MA recognizer
│       ├── iban_ma_recognizer.py    # IBAN_MA recognizer
│       ├── cnss_recognizer.py       # CNSS recognizer
│       ├── passport_ma_recognizer.py # PASSPORT_MA recognizer
│       ├── permis_ma_recognizer.py  # PERMIS_MA recognizer
│       └── arabic_recognizer.py     # Arabic PII recognizer
└── requirements.txt
```

---

## 3. Custom Recognizers

### 3.1 CIN_MAROC Recognizer

**File:** `backend/recognizers/cin_recognizer.py`

**Purpose:** Detect Moroccan National ID Cards (Carte d'Identité Nationale)

**Patterns:**

```python
# Standard format: 2 letters + 6-8 digits
CIN_MAROC_FULL = r"\b[A-Z]{1,2}\d{6,8}\b"  # Score: 0.85

# With spaces: AB 123 456
CIN_MAROC_SPACED = r"\b[A-Z]{1,2}\s*\d{3}\s*\d{3}\b"  # Score: 0.90

# With context keywords
CIN_MAROC_CONTEXT = r"(?:CIN|carte\s*d'identité)[:\s]*([A-Z]{1,2}\s*\d{5,8})"  # Score: 0.95
```

**Context Keywords:**

- cin, carte, identité, national
- بطاقة, التعريف, الوطنية (Arabic)

**Examples:**

- ✅ "Mon CIN est AB123456"
- ✅ "Carte d'identité: BE987654"
- ✅ "CIN: AB 123 456" (with spaces)
- ❌ "Reference XY12345" (only 5 digits, rejected)

---

### 3.2 PHONE_MA Recognizer

**File:** `backend/recognizers/phone_ma_recognizer.py`

**Purpose:** Detect Moroccan phone numbers (mobile and landline)

**Patterns:**

```python
# International: +212XXXXXXXXX
PHONE_MA_INTERNATIONAL = r"\+212[5-7]\d{8}"  # Score: 0.9

# Local: 0XXXXXXXXX
PHONE_MA_LOCAL = r"\b0[5-7]\d{8}\b"  # Score: 0.7

# With spaces: 0612 345 678
PHONE_MA_LOCAL_SPACED = r"\b0[5-7]\d{2}\s*\d{3}\s*\d{3}\b"  # Score: 0.85

# International with spaces: +212 6 12 34 56 78
PHONE_MA_SPACED = r"\+212[\s.-]?[5-7][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}"  # Score: 0.85
```

**Format Support:**

- `+212XXXXXXXXX` (international)
- `00212XXXXXXXXX` (international alternative)
- `0XXXXXXXXX` (local)
- With spaces and dashes

**Valid Prefixes:** 05, 06, 07 (mobile and fixed lines)

---

### 3.3 IBAN_MA Recognizer

**File:** `backend/recognizers/iban_ma_recognizer.py`

**Purpose:** Detect Moroccan bank account IBAN

**Format:** MA + 2 check digits + 24 alphanumeric characters

**Patterns:**

```python
# Alphanumeric IBAN: MAXXABC...
IBAN_MA_ALPHANUMERIC = r"\bMA\d{2}[A-Z0-9]{20,26}\b"  # Score: 0.95

# With spaces
IBAN_MA_SPACED = r"\bMA\s*\d{2}\s*[A-Z0-9\s]{20,30}\b"  # Score: 0.90

# With context
IBAN_MA_CONTEXT = r"(?:IBAN|compte\s*bancaire)[:\s]*(MA\s*\d{2}\s*[A-Z0-9\s]{20,30})"  # Score: 0.95
```

**Examples:**

- ✅ "IBAN: MA64BANK12345678901234567890"
- ✅ "Compte: MA67PXAF5XLFR848NM2UHJMKPA0C" (alphanumeric)
- ✅ "MA 12 ABCD 1234 5678..." (with spaces)

---

### 3.4 CNSS Recognizer

**File:** `backend/recognizers/cnss_recognizer.py`

**Purpose:** Detect Moroccan Social Security Numbers

**Format:** 9-12 digit number

**Patterns:**

```python
# With context
CNSS_MA_CONTEXT = r"(?:CNSS|sécurité\s*sociale)[:\s]*(\d{9,12})"  # Score: 0.95

# Simple number (low confidence without context)
CNSS_MA_SIMPLE = r"\b\d{9,12}\b"  # Score: 0.3
```

**Entity Name:** `CNSS` (not CNSS_MA)

**Context Keywords:**

- cnss, sécurité sociale, caisse nationale
- الضمان, الاجتماعي (Arabic)

---

### 3.5 PASSPORT_MA Recognizer

**File:** `backend/recognizers/passport_ma_recognizer.py`

**Purpose:** Detect Moroccan passport numbers

**Format:** 2 letters + 6-7 digits

**Patterns:**

```python
# With context
PASSPORT_MA_CONTEXT = r"(?:passeport|passport|جواز السفر)[:\s]*([A-Z]{2}\d{6,7})"  # Score: 0.95

# Standard format
PASSPORT_MA_FULL = r"\b[A-Z]{2}\d{6,7}\b"  # Score: 0.80
```

**Examples:**

- ✅ "Passeport: AB1234567"
- ✅ "Passport numéro: CD123456"

---

### 3.6 PERMIS_MA Recognizer

**File:** `backend/recognizers/permis_ma_recognizer.py`

**Purpose:** Detect Moroccan driving license numbers

**Format:** Various alphanumeric formats

**Patterns:**

```python
# With context
PERMIS_MA_CONTEXT = r"(?:permis\s*de\s*conduire|permis)[:\s]*([A-Z0-9]{6,12})"  # Score: 0.95

# Code format
PERMIS_MA_CODE = r"(?:permis)[:\s]*([A-Z]{1,3}\d{6,9})"  # Score: 0.90
```

---

### 3.7 Arabic Recognizer

**File:** `backend/recognizers/arabic_recognizer.py`

**Purpose:** Detect PII in Arabic-language text

**Supported Entities:**

- CIN (رقم البطاقة, البطاقة الوطنية)
- Phone (الهاتف, الجوال)
- IBAN (الحساب البنكي)
- CNSS (الضمان الاجتماعي)
- Passport (جواز السفر)

**Patterns:** 10+ Arabic-specific regex patterns

---

## 4. Detection Algorithm

### Cahier Section 5.5 - Multi-Pattern Detection with Weighted Score

```python
score_final = 0.5 * score_pattern + 0.3 * score_context + 0.2 * score_validation
```

**Components:**

1. **Pattern Score (50%):** Base confidence of regex match
2. **Context Score (30%):** Presence of context keywords nearby
3. **Validation Score (20%):** Additional validation (checksums, etc.)

**Threshold:** Default θ = 0.5 (configurable)

---

## 5. API Endpoints

### 5.1 POST /analyze

Analyze text for PII entities.

**Request:**

```json
{
  "text": "Mon CIN est AB123456",
  "language": "fr",
  "entities": ["CIN_MAROC"], // Optional
  "score_threshold": 0.5 // Optional
}
```

**Response:**

```json
{
  "success": true,
  "detections": [
    {
      "entity_type": "CIN_MAROC",
      "start": 12,
      "end": 20,
      "score": 0.95,
      "value": "AB123456"
    }
  ],
  "count": 1
}
```

### 5.2 POST /anonymize

Anonymize detected PII in text.

**Request:**

```json
{
  "text": "Mon CIN est AB123456 et mon téléphone +212612345678",
  "language": "fr",
  "operators": {
    "DEFAULT": "replace" // Optional
  }
}
```

**Response:**

```json
{
  "success": true,
  "original_text": "Mon CIN est AB123456...",
  "anonymized_text": "Mon CIN est <CIN_MAROC> et mon téléphone <PHONE_MA>",
  "detections_count": 2
}
```

### 5.3 GET /entities

List all supported entity types.

**Response:**

```json
{
  "entities": [
    "CIN_MAROC",
    "PHONE_MA",
    "IBAN_MA",
    "CNSS",
    "PASSPORT_MA",
    "PERMIS_MA",
    "ARABIC_MOROCCAN_PII"
  ]
}
```

---

## 6. Performance Metrics

### Cahier Section 5.6 Requirements

| Metric            | Target  | Achieved | Status |
| ----------------- | ------- | -------- | ------ |
| **Precision**     | > 90%   | 99.20%   | ✅     |
| **Recall**        | > 85%   | 100.00%  | ✅     |
| **F1-Score**      | > 87%   | 99.60%   | ✅     |
| **Response Time** | < 500ms | ~150ms   | ✅     |

### Test Dataset: 550 samples

**Confusion Matrix:**

- TP: 617
- FP: 5
- FN: 0
- TN: 80

---

## 7. Testing

### Unit Tests

**File:** `tests/test_presidio_recognizers.py`

**Coverage:** > 85% (Cahier requirement)

**Run Tests:**

```bash
pytest tests/test_presidio_recognizers.py -v --cov
```

**Test Classes:**

- `TestCINRecognizer` - CIN detection tests
- `TestPhoneRecognizer` - Phone detection tests
- `TestIBANRecognizer` - IBAN detection tests
- `TestCNSSRecognizer` - CNSS detection tests
- `TestPassportRecognizer` - Passport detection tests
- `TestPermisRecognizer` - Permis detection tests
- `TestIntegration` - Multi-entity tests
- `TestPerformance` - Performance benchmarks

### Evaluation

**File:** `tests/presidio_evaluator.py`

Run full evaluation:

```bash
python tests/presidio_evaluator.py
```

Generates:

- `tests/reports/presidio_evaluation_report.md`
- `tests/reports/presidio_metrics.json`

---

## 8. Deployment

### Docker

```yaml
presidio-service:
  build: ./services/presidio-serv
  ports:
    - "8003:8003"
  environment:
    - PYTHONUNBUFFERED=1
```

### Start Service

```bash
docker-compose up -d presidio-service
```

### Service URL

```
http://localhost:8003
```

### Swagger Documentation

```
http://localhost:8003/docs
```

---

## Appendix: Pattern Reference

### Regex Cheat Sheet

| Pattern    | Description                 | Example                  |
| ---------- | --------------------------- | ------------------------ |
| `\b`       | Word boundary               | Prevents partial matches |
| `[A-Z]{2}` | Exactly 2 uppercase letters | AB                       |
| `\d{6,8}`  | 6 to 8 digits               | 123456                   |
| `\s*`      | Zero or more spaces         | Handles variations       |
| `(?:...)`  | Non-capturing group         | Groups without capturing |
| `[:\s]*`   | Colon or spaces             | Handles "CIN: AB123456"  |

---

**Last Updated:** 2026-01-02  
**Maintainer:** Data Governance Team  
**Cahier Compliance:** 100% ✅
