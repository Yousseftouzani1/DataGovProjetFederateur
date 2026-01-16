# 🏆 The Ultimate DataGov End-to-End Test Scenario

This document outlines the **"Golden Path"** to test every aspect of your project, from the frontend microservices to the Big Data governance tools (Atlas/Ranger/Airflow).

---

## 🎭 The 4 Personas (Your Test Users)

| Role | Username | Password | Mission |
| :--- | :--- | :--- | :--- |
| **Labeler** | `labeler_user` | `Labeler123` | **The Scout**: Uploads raw data and does basic tagging. |
| **Annotator** | `annotator_user` | `Annotator123` | **The Expert**: Validates PII detections and fixes errors. |
| **Steward** | `steward_user` | `Steward123` | **The Judge**: Approves work and analyzes ISO Quality. |
| **Admin** | `admin` | `ensias2025` | **The Master**: Manages users and checks the Big Data Logs. |

---

## 🚀 The Scenario: "The Sensitive Bank Export"

### Step 1: Data Ingestion (Labeler Persona)
1.  **Login** as `labeler_user`.
2.  **Action**: Go to **"Upload Data"**. 
3.  **Test File**: Use a CSV containing Moroccan CINs (e.g., `AB123456`) and Phone numbers.
4.  **Service Hook**: This triggers the `cleaning-service` (Port 8004).
5.  **Visibility**: You should see your PII detected but **Masked** (e.g., `[CIN]`).

### Step 2: The Orchestration (Airflow Check)
1.  **Login** to Airflow ([http://localhost:8080](http://localhost:8080)).
2.  **Action**: Trigger the DAG `data_processing_pipeline`.
3.  **Observation**: Watch the tasks turn green in order: `detect_pii` -> `classify_sensitivity` -> `evaluate_quality`.
4.  **Verification**: This proves that your services are talking to each other through the "Nginx Gateway".

### Step 3: Human Validation (Annotator Persona)
1.  **Login** as `annotator_user`.
2.  **Action**: Go to **"Classification Validation"**.
3.  **Choice**: You will see a detection: *"Is AB123456 a CIN?"*. Click **Confirm**.
4.  **Service Hook**: This updates the `annotation-service` (Port 8007).

### Step 4: Governance Approval (Steward Persona)
1.  **Login** as `steward_user`.
2.  **Action**: Go to **"Quality Analysis"**.
3.  **Result**: You should see an **ISO 25012 Grade** (e.g., "Grade A").
4.  **The "Big Move"**: Go to **"Approval Queue"** and approve the dataset for "Atlas Sync".

### Step 5: Metadata Proof (Atlas UI Check)
1.  **Login** to Atlas ([http://192.168.110.132:21000](http://192.168.110.132:21000)).
2.  **Search**: Type the name of the dataset you just uploaded.
3.  **Proof**: You will see the dataset with a **Tag** (Classification) called `PII`. 
4.  **Meaning**: Your project successfully updated the enterprise metadata map.

### Step 6: Security Enforcement (Ranger UI Check)
1.  **Login** to Ranger ([http://192.168.110.132:6080](http://192.168.110.132:6080)).
2.  **Action**: Go to **"Hive"** -> **"Policies"**.
3.  **Discovery**: Search for a policy created by the `ranger_integration`.
4.  **The Test**: Try to access the data as a `labeler` vs `admin`.
    *   `labeler` -> Should see `****` (Masking).
    *   `admin` -> Should see clear text.

---

## 🛠️ Verification Checklist for Success

| Component | Port | Proof of Life |
| :--- | :--- | :--- |
| **Frontend UI** | 8001 | Modern Glassmorphism dashboard appears. |
| **Nginx Gateway**| 8000 | `/api/auth/login` returns a real JWT token. |
| **MongoDB** | 27017 | Collections `users` and `datasets` are populated. |
| **Apache Atlas** | 21000 | New entities appear with `qualifiedName`. |
| **Apache Ranger**| 6080 | New policies appear in the "Access Manager". |
| **EthiMask** | 8009 | Data changes dynamically when switching roles. |

---

## 💡 Pro Tip for your Jury
> *"Our platform doesn't just 'show' data; it orchestrates a complete lifecycle from raw ingestion to enforced security policies in a Big Data environment (HDP Sandbox), making it compliant with Law 09-08."*
