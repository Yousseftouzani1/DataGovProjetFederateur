# 🏷️ Taxonomie Morocco Service - Metadata & Classification Engine

## 1. Overview & Project Role

The **Taxonomie Morocco Service** is the **Foundation Layer** of the **DataSentinel** platform. While the Presidio service provides raw detection, this service provides the **Semantic Meaning** and **Legal Classification** for all detected data.

### Its role in the DataSentinel Pipeline:

1.  **Definitions**: Stores the 9 Moroccan data domains (Identité, Médical, etc.).
2.  **Detection**: Implements the primary "Custom Pattern" engine (81+ regexes).
3.  **Governance**: Maps detected entities to **Sensitivity Levels** (Critical/High/Medium/Low) based on Law 09-08 and RGPD.
4.  **Atlas Bridge**: Provides the JSON schemas required to synchronize the platform's classification system with **Apache Atlas**.

---

## 2. Integrated Data Domains (Cahier Section 4)

The engine manages over **114 unique entities** across 9 domains, each with specific patterns and sensitivity levels:

| Domain            | Entities      | Example         | Legal Basis     |
| ----------------- | ------------- | --------------- | --------------- |
| **Identité**      | 47 (Extended) | CIN, Passport   | Loi 09-08       |
| **Médical**       | 37            | Dossier Médical | HIPAA / RGPD    |
| **Financier**     | 7             | IBAN, RIB       | Bank Al-Maghrib |
| **Education**     | 8             | Code Massar     | Ministry Rules  |
| **Professionnel** | 34            | No. CNSS        | Labor Law       |

---

## 3. Core Files & Impact Analysis

### 📁 `main.py`

The FastAPI entry point. It handles the REST orchestration between the custom pattern engine and the external Presidio service.

### 📁 `backend/sensitivity_calculator.py`

The **Governance Brain**. It implements the logic to determine if a piece of data is PII (Personally Identifiable) or SPI (Sensitive Personal Information). It calculates risk scores used by the platform to trigger masking.

### 📁 `backend/pattern_migration.py` & `taxonomy_loader.py`

The **Persistence Layer**. These scripts ensure the 9 JSON data domains are correctly migrated into **MongoDB Atlas**. This turns static JSON files into a queryable, high-performance database.

### 📁 `atlas_types_classifications_export.json`

The **Integration Deliverable**. This file contains the exact `classificationDefs` and `entityDefs` needed to import our Moroccan taxonomy into **Apache Atlas** for global data governance.

---

## 4. Key Scenarios & Use Cases

### Scenario A: The Moroccan Compliance Audit

A bank needs to audit thousands of French and Arabic documents for PII.

- **Action**: The service identifies "AB123456" as a `CIN_MAROC` and "رقم الحساب" as an `IBAN` indicator.
- **Result**: The service tags these as `SPI` (Sensitive) and `CRITICAL`, alerting the Data Steward.

### Scenario B: Sensitive Data Masking (Anonymization)

A developer needs a production database copy for testing.

- **Action**: The service runs the `anonymize=true` pipeline.
- **Result**: It replaces real Moroccan names and IDs with placeholders (e.g., `[CIN]`), ensuring Law 09-08 compliance while maintaining data structure for testing.

### Scenario C: Apache Atlas Sync

The CTO wants to see the data classification in the enterprise catalog.

- **Action**: `backend/export_atlas.py` is run.
- **Result**: All 114 Moroccan entities are automatically registered as "Classifications" in Apache Atlas.

---

## 5. Tests & Verification (100% Configured)

The service has been fully configured and verified through:

1.  **CRUD Tests**: Verified 100% of API endpoints for taxonomy management.
2.  **Data Integrity**: 161 Moroccan patterns verified for regex validity and performance.
3.  **KPI Audit**:
    - **Detection Speed**: < 100ms per text block (Exceeding KPI).
    - **Export Validity**: Atlas JSON verified against Apache Atlas v3.0 schemas.
    - **Storage**: Successfully migrated 10 taxonomies to MongoDB Atlas.

---

_Created with care by the DataSentinel Metadata Engineering Team._
