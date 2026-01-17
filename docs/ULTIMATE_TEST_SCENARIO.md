# 🏆 The Ultimate DataGov End-to-End Test Scenario

> **Version:** 2.0 (Role-Based & User Story Aligned)  
> **Reference:** `docs/ROLE_BASED_ACCESS_GUIDE.md`

This document outlines the **End-to-End Verification Path** for the DataGov Platform. It validates the system against **Law 09-08**, **ISO 25012**, and the **Micros-Services Architecture**.

---

## 🏗️ PART 1: The "Golden Thread" Production Workflow

**Scenario:** A bank needs to onboard a sensitive client file (`customers_sensitive.csv`) while ensuring strict governance, privacy, and quality control.

### 🔄 The Lifecycle Flow
1.  **Ingestion & Sanitation (The Labeler)**
    *   **Context**: A branch manager uploads a CSV of new clients.
    *   **Action**: Upload -> EthiMask checks -> Cleaning.
    *   **System Event**: `cleaning-service` normalizes names, dates, and removes duplicates.
    *   **Result**: Valid, raw data enters the "Lake".

2.  **Automated Intelligence (The Orchestrator)**
    *   **Context**: Airflow wakes up (Scheduled DAG).
    *   **Action**: Scans the new file.
    *   **System Event**: 
        *   `presidio-service` scans for PII (CIN, Phones).
        *   `classification-service` (ML) predicts column types.
    *   **Result**: Dataset tagged with *candidate* metadata.

3.  **Human Validation (The Annotator)**
    *   **Context**: The ML model is only 95% sure.
    *   **Role Constraint**: The **Steward** *cannot* certify data until 5% uncertainty is resolved.
    *   **Action**: Annotator logs in -> Sees "Pending Validations" -> Confirms/Rejects predictions.
    *   **Result**: High-quality, human-verified metadata.

4.  **Governance Certification (The Steward)**
    *   **Context**: Data is clean, but is it safe for executive dashboards?
    *   **Action**: Steward checks **Quality Report** (ISO 25012 scores).
    *   **Decision**: If Grade is A/B, click **"Approve for Atlas"**.
    *   **Result**: Metadata published to Enterprise Catalog (Atlas).

5.  **Security Enforcement (The Guard)**
    *   **Context**: A Data Scientist queries Hive via Ranger.
    *   **System Event**: **Ranger** intercepts request -> Checks Atlas tags.
    *   **Enforcement**: "Column `CIN` has tag `PII_SENSITIVE`. Access Denied."

---

## 👥 PART 2: Role-Based Acceptance Testing (RBAC)

Use the credentials below to verify strict access control.

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Labeler** | `labeler_user` | `Labeler123` | **Level 1 (Basic)**: Upload, View My Stats. |
| **Annotator** | `annotator_user` | `Annotator123` | **Level 2 (Validation)**: + Corrections, Cleaning. |
| **Steward** | `steward_user` | `Steward123` | **Level 3 (Governance)**: + Taxonomy, Approval, Quality. |
| **Admin** | `admin` | `ensias2025` | **Level 4 (Root)**: + User Mgmt, Config, Logs. |

### 🧪 Test 1: The Forbidden Menu Check
*Goal: Ensure users CANNOT see what they are not supposed to see.*

| Actor | Action | Expected Result |
| :--- | :--- | :--- |
| **Labeler** | Look for "Data Cleaning" sidebar item | ❌ **HIDDEN** |
| **Labeler** | Look for "EthiMask" sidebar item | ❌ **HIDDEN** |
| **Annotator** | Look for "Taxonomy Manager" | ❌ **HIDDEN** |
| **Steward** | Look for "User Management" | ❌ **HIDDEN** |

---

## 📝 PART 3: Detailed User Stories & Step-by-Step

### 🧑‍💻 User Story 1: "Agile Ingestion" (Labeler)
> **As a Labeler**, I want to upload raw data and verify recognized PII so that the cleaning process can begin.

**Steps:**
1.  **Login** as `labeler_user` / `Labeler123`.
2.  **Upload**: Navigate to **"Importer un Dataset"**.
3.  **Action**: Upload `MASTER_DATAGOV_TEST.csv`.
4.  **Verify**:
    *   Toast message: "Upload Successful".
    *   Go to **"PII Detection"**. Select file.
    *   **Check**: Are CINs masked (e.g., `AB******`)?
    *   **Check**: Are Names visible but flagged?

### 🕵️ User Story 2: "Intelligent Correction" (Annotator)
> **As an Annotator**, I want to receive assigned tasks to validate uncertain classifications and fix quality issues.

**Steps:**
1.  **Logout** and Login as `annotator_user` / `Annotator123`.
2.  **Cleaning**: Go to **"Data Cleaning"**.
    *   Select the file uploaded by Labeler.
    *   **Action**: Click **"Run Cleaning"**.
    *   Wait for "Cleaning Completed" status.
3.  **Validation**: Go to **"Classification Validation"**.
    *   You should see rows like "Column: `cin_ma` -> Predicted: `CIN` (Conf: 0.92)".
    *   **Action**: Click **"Confirm"** (Green Check).
4.  **Correction**: Go to **"Corrections"**.
    *   Find a row with a negative salary (`-9200`).
    *   **Action**: Edit value to `9200`. Click **"Save"**.

### ⚖️ User Story 3: "Quality Certification" (Steward)
> **As a Data Steward**, I want to review the ISO 25012 quality score and approve the dataset for enterprise usage.

**Steps:**
1.  **Logout** and Login as `steward_user` / `Steward123`.
2.  **Dashboard**: Go to **"Quality Metrics"**.
    *   Select the file.
    *   **Verify**: Look for the "Accuracy" and "Completeness" gauges.
3.  **Approval Queue**: Go to **"Approval Queue"**.
    *   See the correction made by the **Annotator** (Salary change).
    *   **Action**: Click **"Approve"**.
    *   *System Effect*: The change is permanently committed to the Master Data.

### 🛡️ User Story 4: "Adaptive Security" (EthiMask)
> **As a Compliance Officer**, I want to ensure that different roles see different levels of data exposure based on their trust score.

**Steps:**
1.  **Comparison Test**:
    *   **Login as Labeler**: View file in "PII Detection". CIN = `AB******`. Phone = `0661******`.
    *   **Login as Steward**: View file in "PII Detection". CIN = `AB123456` (Full? Or partially masked?). Phone = `0661234567`.
    *   *Note*: Stewards have a higher Trust Score (0.85) than Labelers (0.50), revealing more data.

---

## 🛠️ Verification Checklist

- [ ] **Docker Services**: All 9 containers + Nginx running.
- [ ] **Login**: All 4 users can login.
- [ ] **Menu Security**: Labeler cannot see Admin menus.
- [ ] **Flow**: Upload -> Clean -> Validate -> Approve works without error.
- [ ] **EthiMask**: Masking changes based on the logged-in user.
- [ ] **Airflow**: DAG `data_processing_pipeline` completes successfully.
