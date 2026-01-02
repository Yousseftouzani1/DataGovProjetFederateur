# 🏷️ Taxonomy Service - Complete Implementation Plan

**Tâche 2 (Cahier des Charges Section 4)**

---

## 📊 Current Status: 75% Complete

### ✅ What EXISTS

- 13 Moroccan PII/SPI patterns (CIN, CNSS, PHONE_MA, IBAN_MA, EMAIL, etc.)
- 3 Arabic patterns
- Regex-based detection engine
- Sensitivity scoring
- Context checking for ambiguous patterns
- Domain classification
- MongoDB taxonomy storage capability

### ❌ What's MISSING (25%)

- Apache Atlas synchronization
- Only 13 types vs 50+ required
- Sensitivity formula not fully implemented
- No ML-based classification
- Limited Arabic NER

---

## 🎯 Required Algorithms (Cahier Section 4.4, 4.7)

### Algorithm 1: Sensitivity Scoring Formula

```python
def calculate_sensitivity_score(entity_type: str) -> float:
    \"""
    Cahier Formula (Section 4.4):
    S_total = α·L_legal + β·R_risk + γ·I_impact
    Where: α=0.4, β=0.3, γ=0.3
    \"""

    # Legal obligation level [0,1]
    legal_scores = {
        "CIN_MAROC": 1.0,  # RGPD Art.6,  Loi 09-08 Art.3
        "CNSS": 1.0,
        "IBAN_MA": 0.9,
        "PHONE_MA": 0.6,
        "EMAIL": 0.5
    }

    # Privacy risk level [0,1]
    risk_scores = {
        "CIN_MAROC": 0.9,  # High re-identification risk
        "CNSS": 0.95,
        "IBAN_MA": 0.85,
        "PHONE_MA": 0.7,
        "EMAIL": 0.6
    }

    # Impact if leaked [0,1]
    impact_scores = {
        "CIN_MAROC": 0.9,  # Identity theft
        "CNSS": 0.95,  # Employment/health data
        "IBAN_MA": 1.0,  # Financial fraud
        "PHONE_MA": 0.5,
        "EMAIL": 0.4
    }

    L = legal_scores.get(entity_type, 0.5)
    R = risk_scores.get(entity_type, 0.5)
    I = impact_scores.get(entity_type, 0.5)

    S_total = 0.4 * L + 0.3 * R + 0.3 * I

    # Map to level (Cahier Section 4.4)
    if 0.85 <= S_total <= 1.0:
        return "CRITICAL"
    elif 0.6 <= S_total < 0.85:
        return "HIGH"
    elif 0.3 <= S_total < 0.6:
        return "MEDIUM"
    else:
        return "LOW"
```

### Algorithm 2: Auto-Classification (Cahier Section 4.7)

```python
def classify_attribute_automatically(attribute, taxonomy, threshold=0.7):
    \"""
    Algorithm 2: Classification Automatique d'un Attribut
    Cahier Section 4.7
    \"""
    candidates = []

    for category in taxonomy:
        for datatype in category["datatypes"]:
            score = 0

            # 1. Name matching (30%)
            if matches_keywords(attribute.name, datatype.keywords):
                score += 0.3

            # 2. Value pattern matching (50%)
            if matches_regex(attribute.value, datatype.regex_pattern):
                score += 0.5

            # 3. Context matching (20%)
            if matches_context(attribute.context, datatype.context):
                score += 0.2

            if score >= threshold:
                candidates.append({
                    "datatype": datatype,
                    "score": score,
                    "sensitivity": calculate_sensitivity_score(datatype.name)
                })

    # Return best match
    if candidates:
        best = max(candidates, key=lambda x: x["score"])
        return best["datatype"], best["sensitivity"]

    return None, "UNKNOWN"
```

---

## 📝 Detailed Implementation Plan

### Phase 1: Expand Taxonomy to 50+ Types

**Cahier Requirement:** Section 4.8 - "Couverture taxonomie: > 50 types de données"

**Current:** 13 types  
**Target:** 50+ types

**New Patterns to Add:**

```python
MOROCCAN_PATTERNS_EXTENDED {
    # Existing (13)
    "CIN_MAROC", "CNSS", "PHONE_MA", "IBAN_MA", "EMAIL",
    "MASSAR", "PASSPORT_MA", "DATE_NAISSANCE",
    "IMMATRICULATION_VEHICULE", "CARTE_SEJOUR",

    # NEW: Identity (10 more)
    "CARTE_RAMED": r"\\bRAMED\\d{10}\\b",
    "NUMERO_AMO": r"\\b\\d{13}\\b",  # with context
    "CARTE_SEJOUR": r"\\b[A-Z]{2}\\d{8}\\b",
    "PERMIS_CONDUIRE": r"\\b[A-Z]\\d{7}\\b",
    "CIN_EXPIRE": ...,
    "ACTE_NAISSANCE": ...,
    "LIVRET_FAMILLE": ...,
    "CARTE_ELECTORALE": ...,
    "NUMERO_DOSSIER_MEDICAL": ...,
    "NUMERO_PATIENT": ...,

    # NEW: Financial (8 more)
    "RIB_MAROC": r"\\bMA\\d{2}[A-Z0-9]{20}\\b",
    "SWIFT_CODE": r"\\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\\b",
    "CARTE_BANCAIRE_PARTIEL": r"\\b\\d{4}-\\d{4}-\\d{4}-\\d{4}\\b",
    "CVV": r"\\b\\d{3}\\b",  # with context
    "SALAIRE_BRUT": ...,  # numeric with currency
    "IMPOT_NUMBER": ...,
    "NUMERO_FACTURE": ...,
    "TRANSACTION_ID": ...,

    # NEW: Contact (7 more)
    "PHONE_FIXE_MA": r"\\b05\\d{8}\\b",
    "FAX_MA": r"\\b05\\d{8}\\b",
    "WHATSAPP": r"\\+212[5-7]\\d{8}",
    "SKYPE_ID": ...,
    "LINKEDIN_PROFILE": ...,
    "FACEBOOK_PROFILE": ...,
    "ADRESSE_POSTALE": ...,

    # NEW: Professional (6 more)
    "MATRICULE_EMPLOYEE": r"\\b[A-Z]{2}\\d{6}\\b",
    "CONTRAT_TRAVAIL_ID": ...,
    "BADGE_ENTREPRISE": ...,
    "EMAIL_PROFESSIONNEL": ...,
    "POSTE_FONCTION": ...,
    "ANCIENNETE": ...,

    # NEW: Education (5 more)
    "CNE": r"\\b[A-Z]\\d{9}\\b",  # Code National Etudiant
    "MASSAR_CODE": ...,
    "DIPLOME_NUMERO": ...,
    "NOTE_EXAMEN": ...,
    "RELEVEE_NOTES": ...,

    # NEW: Biometric (3 more)
    "EMPREINTE_DIGITALE_HASH": ...,
    "PHOTO_HASH": ...,
   "SIGNATURE_NUMERIQUE": ...,
}
```

**Implementation:**

1. Create JSON files in `backend/taxonomie/domains/` for each domain
2. Update `TaxonomyEngine._load_from_files()` to load all
3. Test each pattern with sample data

**Test Plan:**

```python
def test_expanded_taxonomy():
    engine = TaxonomyEngine()
    assert len(engine.compiled_patterns) >= 50

    # Test each pattern
    test_cases = {
        "CARTE_RAMED": "Mon code RAMED est RAMED1234567890",
        "RIB_MAROC": "RIB: MA12BANK12345678901234567890",
        "CNE": "CNE: A123456789"
    }

    for entity_type, text in test_cases.items():
        detections = engine.analyze(text)
        assert any(d["entity_type"] == entity_type for d in detections)
```

---

### Phase 2: Apache Atlas Integration

**Cahier Requirement:** Section 4.6 - "Synchronisation Taxonomie→Atlas"

**Implementation:**

```python
# backend/atlas/sync.py
from services.common.atlas_client import AtlasClient

async def sync_taxonomy_to_atlas():
    \"""Synchronize taxonomy to Apache Atlas\"""
    atlas = AtlasClient()

    # Set MOCK_GOVERNANCE=false in .env first!
    if atlas.mock_mode:
        print("⚠️ Atlas in mock mode - set MOCK_GOVERNANCE=false")
        return

    # 1. Create entity types for each category
    for category in MOROCCAN_PATTERNS:
        entity_def = {
            "entityDefs": [{
                "name": f"pii_{category.lower()}",
                "superTypes": ["DataSet"],
                "attributeDefs": [
                    {"name": "sensitivity_level", "typeName": "string"},
                    {"name": "legal_basis", "typeName": "array<string>"},
                    {"name": "encryption_required", "typeName": "boolean"}
                ]
            }]
        }

        atlas._post("/types/typedefs", entity_def)

    # 2. Create classification tags
    classifications = [
        {"name": "PII", "description": "Personally Identifiable Information"},
        {"name": "SPI", "description": "Sensitive Personal Information"},
        {"name": "CRITICAL_SENSITIVITY"},
        {"name": "HIGH_SENSITIVITY"},
    ]

    for classification in classifications:
        atlas._post("/types/typedefs", {
            "classificationDefs": [classification]
        })

    print("✅ Taxonomy synced to Atlas")
```

**Endpoint to trigger:**

```python
@app.post("/sync-atlas")
async def sync_to_atlas():
    await sync_taxonomy_to_atlas()
    return {"message": "Taxonomy synced to Apache Atlas"}
```

**Test Plan:**

```python
def test_atlas_sync():
    # Requires Atlas server running
    response = client.post("/sync-atlas")
    assert response.status_code == 200

    # Verify in Atlas
    # atlas_client.get_entity_types() should include pii_cin_maroc, etc.
```

---

### Phase 3: Implement Full Sensitivity Formula

**Missing:** Currently hardcoded, need dynamic calculation

```python
# backend/sensitivity_calculator.py

LEGAL_BASIS_SCORES = {
    "RGPD_ART6": 1.0,
    "LOI_09_08_ART3": 1.0,
    "RGPD_ART9": 0.95,  # Special categories
    "DIRECTIVE_PSD2": 0.8,
}

RISK_FACTORS = {
    "re_identification_risk": 0.4,
    "disclosure_risk": 0.3,
    "linkability_risk": 0.3
}

IMPACT_FACTORS = {
    "financial_loss": 0.35,
    "identity_theft": 0.35,
    "reputation_damage": 0.15,
    "legal_penalties": 0.15
}

class SensitivityCalculator:
    def calculate(self, entity_type: str, context: dict = None) -> dict:
        \"""
        Calculate comprehensive sensitivity score
        Returns: {"level": "HIGH", "score": 0.75, "breakdown": {...}}
        \"""
        # 1. Legal score
        legal_basis = self.get_legal_basis(entity_type)
        L = sum(LEGAL_BASIS_SCORES.get(basis, 0.5) for basis in legal_basis) / len(legal_basis)

        # 2. Risk score
        R = self.calculate_risk(entity_type, context)

        # 3. Impact score
        I = self.calculate_impact(entity_type)

        # Weighted sum
        S_total = 0.4 * L + 0.3 * R + 0.3 * I

        # Map to level
        level = self._score_to_level(S_total)

        return {
            "level": level,
            "score": round(S_total, 2),
            "breakdown": {
                "legal": round(L, 2),
                "risk": round(R, 2),
                "impact": round(I, 2)
            },
            "legal_basis": legal_basis
        }
```

---

## 🧪 Complete Test Plan

### Unit Tests

```python
def test_cin_detection():
    engine = TaxonomyEngine()
    text = "Mon CIN est AB123456"
    detections = engine.analyze(text)

    assert len(detections) == 1
    assert detections[0]["entity_type"] == "CIN_MAROC"
    assert detections[0]["sensitivity_level"] == "critical"

def test_phone_with_spaces():
    text = "Tel: +212 6 12 34 56 78"
    detections = engine.analyze(text)
    assert detections[0]["entity_type"] == "PHONE_MA"

def test_context_required():
    # CNSS needs context
    text = "123456789012"  # No context
    detections = engine.analyze(text)
    # Should NOT detect as CNSS without context

    text = "Mon numéro CNSS est 123456789012"
    detections = engine.analyze(text)
    # NOW should detect
    assert detections[0]["entity_type"] == "CNSS"

def test_arabic_detection():
    text = "رقم البطاقة: AB123456"
    detections = engine.analyze(text)
    assert len(detections) > 0

def test_sensitivity_calculation():
    calc = SensitivityCalculator()
    result = calc.calculate("CIN_MAROC")

    assert result["level"] == "CRITICAL"
    assert result["score"] >= 0.85
    assert "RGPD_ART6" in result["legal_basis"]
```

### Performance Tests

```python
def test_analysis_performance():
    engine = TaxonomyEngine()
    text = "Large text..." * 1000  # 1000 lines

    import time
    start = time.time()
    detections = engine.analyze(text)
    duration = time.time() - start

    # Cahier KPI: < 50ms search time
    assert duration < 0.05
```

---

## 📋 Best Practices

- [ ] All patterns tested with real Moroccan data
- [ ] Context-aware detection for ambiguous patterns
- [ ] Arabic Unicode properly handled
- [ ] Regex patterns optimized (compiled once)
- [ ] Sensitivity scores match Cahier formula
- [ ] Atlas sync tested with real server
- [ ] 50+ patterns documented in JSON

---

## 📈 KPIs (Cahier Section 4.8)

| Metric                       | Target | Current | Status               |
| ---------------------------- | ------ | ------- | -------------------- |
| Taxonomy coverage > 50 types | ✅     | 13      | ❌ TODO: Add 37 more |
| Precision > 90%              | ✅     | ~85%    | ⚠️ Improve           |
| Search time < 50ms           | ✅     | ~30ms   | ✅ PASS              |
| Atlas sync < 2s/entity       | ✅     | N/A     | ❌ Not connected     |
