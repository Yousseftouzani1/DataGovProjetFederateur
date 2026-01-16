# 🧪 DataGov Manual Test Laboratory: The "Full Integration" Scenario

This guide is your step-by-step manual to verify every single feature of the project. It follows a real data lifecycle based on the **Cahier des Charges**.

---

## 📂 Pre-Requisites: The Test Data
The platform now uses a central master dataset. You can find it at:
[**`MASTER_DATAGOV_TEST.csv`**](file:///c:/Users/ibnou/DataGovProjetFederateur/test_data/MASTER_DATAGOV_TEST.csv)

This file contains 20 rows of realistic Moroccan data (CIN, RIB, Phone) and some intentional errors to test Quality/Correction.

---

## 🎭 Step 1: The Ingestion (Role: Labeler)
**Goal**: Test Frontend Upload, Tokenization, and MongoDB Persistence.

1.  **Open Browser**: Go to `http://localhost:8080` (Frontend).
2.  **Login**: 
    *   **User**: `labeler_user`
    *   **Pass**: `Labeler123`
3.  **Navigate**: Click on **"Upload Data"** in the left sidebar.
4.  **Action**: 
    *   Select the file [**`MASTER_DATAGOV_TEST.csv`**](file:///c:/Users/ibnou/DataGovProjetFederateur/test_data/MASTER_DATAGOV_TEST.csv).
    *   Click **"Upload & Analyze"**.
5.  **Verify (What to see)**:
    *   A notification: *"Dataset uploaded successfully!"*.
    *   On the same page, scroll down to **"Detection Preview"**.
    *   **Crucial**: You should see the values for `cin`, `phone`, and `rib` as **`[CIN]`**, **`[PHONE]`**, and **`[IBAN]`**. 
    *   *Why?* Because as a Labeler, you are strictly forbidden from seeing raw sensitive data.

---

## 🔄 Step 2: The Logic (Service: Airflow)
**Goal**: Test Microservice Orchestration and ISO Quality Scoring.

1.  **Open Browser**: Go to `http://localhost:8081` (Airflow UI).
2.  **Login**: `admin` / `admin`.
3.  **Navigate**: Find the DAG named **`data_processing_pipeline`**.
4.  **Action**: Click the **"Play"** button (Trigger DAG).
5.  **Verify (What to see)**:
    *   Wait for the graph to turn green.
    *   Click on the **`evaluate_quality`** task -> Click **"Logs"**.
    *   **Proof**: Look for a line saying: `Quality Score: 95% (Grade A)`. This proves the ISO 25012 engine is running.

---

## ✅ Step 3: Human-in-the-loop (Role: Annotator)
**Goal**: Test Human Validation Workflow.

1.  **Open Browser**: Go back to the Frontend `http://localhost:8080`.
2.  **Login**: 
    *   **User**: `annotator_user`
    *   **Pass**: `Annotator123`
3.  **Navigate**: Click on **"Annotation Tasks"**.
4.  **Action**:
    *   Select the task for `test_maroc_bank.csv`.
    *   In the table, you will see the detected CIN `AB123456`. Click **"Confirm"**.
    *   Click **"Submit Validation"** at the bottom.
5.  **Verify**: The task status changes to "Completed".

---

## 🛡️ Step 4: Governance Approval (Role: Steward)
**Goal**: Trigger the synchronization to Apache Atlas.

1.  **Login**: 
    *   **User**: `steward_user`
    *   **Pass**: `Steward123`
2.  **Navigate**: Click on **"Approval Queue"**.
3.  **Action**:
    *   You will see the dataset verified by the annotator.
    *   Click **"View Quality Report"** (Check the PDF if it opens).
    *   Click **"Approve & Sync to Atlas"**.
4.  **Verify**: A success message aparece: *"Metadata synchronized with Apache Atlas"*.

---

## 🔍 Step 5: The Final Proof (Big Data Tools)
**Goal**: Check if the HDP Sandbox received the data.

### Part A: Apache Atlas (Metadata)
1.  **Goto**: `http://192.168.110.132:21000`
2.  **Login**: `admin` / `ensias2025`
3.  **Search**: In the search bar, type the name of your file or **`DataSet`**.
4.  **Proof**: You will see your columns listed. The columns `cin`, `phone`, and `rib` will have a **CLASSFICATIONS/TAG** entry named **`PII`**.

### Part B: Apache Ranger (Security)
1.  **Goto**: `http://192.168.110.132:6080`
2.  **Login**: `admin` / `hortonworks1`
3.  **Navigate**: **Access Manager** -> **Hive**.
4.  **Proof**: Look for a policy named something like `Masking_PII_Auto`. 
    *   **The Click**: Click the "Edit" (pencil) icon.
    *   **Observe**: You will see a rule that says: **"Role = LABELER -> Masking Type = REDACT"**.

---

## 🔒 Step 6: The "EthiMask" Magic (Role: Admin)
**Goal**: Prove real-time contextual masking.

1.  **Login**: `admin` / `ensias2025` (On the Frontend!)
2.  **Navigate**: Go to the **"Ethimask Preview"** or **"Datasets Overview"**.
3.  **Action**: Open `test_maroc_bank.csv`.
4.  **Verify**:
    *   As **Admin**: You see the real name **Mohammed Alami**.
    *   **Action**: Use the "Role Simulator" dropdown (if available) to switch to **Labeler**.
    *   **Result**: The name instantly changes to **`M*********`**.
    *   **Proof**: This proves the **Perceptron Model** in `ethimask-serv` is making decisions based on your role!
