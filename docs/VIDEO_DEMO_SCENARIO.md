# 🎬 DataGov Federation Project - Ultimate Demo Script

## 🎯 Objective
Record a seamless end-to-end flow demonstrating:
1.  **Governance Initialization** (Syncing Taxonomy to Atlas)
2.  **Data Ingestion & Cataloging** (Atlas Registration)
3.  **PII Detection & Security** (Presidio + classifications)
4.  **Quality Assurance** (ISO 25012 check)
5.  **Forensic Audit** (System Ledger)

---

## 🎭 Cast & Roles
For the demo, you can stay logged in as **Admin** to show everything, or mention you are switching "hats".
*   **The Architect (Admin):** Sets up governance.
*   **The Data Engineer:** Ingests data.
*   **The Security Officer:** Scans for PII.
*   **The Quality Steward:** Checks data health.

---

## 🎬 Scene 1: The "Big Bang" - Governance Sync
**Goal:** Show that your local Python definitions drive the Enterprise Atlas Cluster.

1.  **Navigate:** Go to **"Settings"** (Click the Gear icon or "Configure Profile").
2.  **Action:** Scroll to the bottom card: "Governance Sync Required".
3.  **Click:** `[Sync Glossary to Atlas]`
4.  **Observe:**
    *   Wait for the Toast Notification: "✅ Synced X terms to Apache Atlas!"
5.  **External Validation (Apache Atlas):**
    *   Open Atlas UI: `http://100.91.176.196:21000` (User/Pass: `admin`/`admin`).
    *   Go to **"Principale"** (Search).
    *   In "Search By Type", select `_Glossary` or check the `Classifications` tab.
    *   **Show:** The `PII`, `SPI`, `Critical_Sensitivity` tags are present. This proves your system initialized the cluster.

---

## 🎬 Scene 2: High-Speed Ingestion
**Goal:** Ingest a file and prove it instantly syncs with the Catalog.

1.  **Navigate:** Go to **"Ingestion Engine"** (Database Icon / DataPipelinePage).
2.  **File Prep:**
    *   Use file: `services/cleaning-serv/tests/test_data/hr_data_dirty.csv` (or any CSV with PII like emails/phones).
    *   *Tip: Copy this file to your Desktop for easy access.*
3.  **Action:**
    *   Click `[Click to Select]` in the upload zone.
    *   Select your CSV file.
    *   Click `[Begin High-Speed Ingestion]`.
4.  **Observe:**
    *   See the list update with your new dataset.
    *   Note the "Atlas: Registered" status if visible.
5.  **External Validation (Apache Atlas):**
    *   Switch to Atlas UI.
    *   Search for the entity (Type: `DataSet` or just search "hr_data").
    *   **Show:** Click the entity. Show the "Relationship" graph or "Properties" to prove it's cataloged.

---

## 🎬 Scene 3: The Security Audit (PII Sentinel)
**Goal:** Detect sensitive Moroccan Data and generate a report.

1.  **Navigate:** Click **"PII Sentinel"** (Shield Icon).
2.  **Setup:**
    *   Switch tab to **"Volume Scan"** (Right tab).
    *   Select your uploaded dataset (e.g., `hr_data_dirty.csv`) from the dropdown.
3.  **Action:**
    *   Click `[Full Volume Audit]`.
4.  **Observe:**
    *   Watch the "Audit Results" populate.
    *   **Highlight:** Point out detected entities (CIN, PHONE_MA, IBAN).
    *   *Nice Touch:* Toggle the "Eye" icon to show/hide masked values (if you are Admin).
5.  **Export:**
    *   Click `[Export Report (CSV)]`.
    *   **Verify:** Open the downloaded CSV to show the rows of detected PII.
6.  **Handover:**
    *   Click `[Submit to Processing]`.
    *   Toast: "Pipeline triggered!"

---

## 🎬 Scene 4: Quality & Compliance (Quality Hub)
**Goal:** Evaluate ISO 25012 standards.

1.  **Navigate:** Click **"Quality Hub"** (Activity/Pulse Icon).
2.  **Action:**
    *   Select the dataset.
    *   Click `[Trigger Audit]`.
3.  **Observe:**
    *   The Radial Chart animates.
    *   The "ISO 25012 Grade" appears (e.g., "B - Acceptable").
    *   Review "Recommendations" list (e.g., "Fix broken emails").
4.  **Export (The New Feature):**
    *   Click the **Download Icon** (Arrow Down) next to the "Trigger Audit" button.
    *   **Show:** Open the PDF. Point out the professional grade and score.

---

## 🎬 Scene 5: Backend Logic (Airflow & Ranger)
**Goal:** Show the orchestration and security layers.

1.  **External Validation (Airflow):**
    *   Open Airflow: `http://localhost:8080` (User/Pass: `admin`/`admin`).
    *   Go to **DAGs**.
    *   **Show:** `daily_export_pipeline` or the triggered pipeline running green.
    *   Click into the Grid View to show tasks completing (`upload`, `clean`, `notify`).
2.  **External Validation (Ranger):**
    *   Open Ranger: `http://100.91.176.196:6080` (User/Pass: `admin`/`admin`).
    *   Go to **Access Manager** -> **Hadoop SQL** (or relevant policy).
    *   **Show:** A policy allows/denies access. *Note: You don't need to trigger a denial, just showing the Policy Manager proves security is configured.*

---

## 🎬 Scene 6: The Forensic Trail (System Ledger)
**Goal:** Prove that everything we just did was logged.

1.  **Navigate:** Click **"System Ledger"** (Clock/History Icon).
2.  **Observe:**
    *   The table is full of recent events:
        *   `TAXONOMY_SYNC`
        *   `DATASET_UPLOAD`
        *   `PII_SCAN`
        *   `QUALITY_EVALUATION`
3.  **The Grand Finale:**
    *   Click `[Export forensic PDF]`.
    *   **Show:** Open the PDF. It looks official ("System Forensic Ledger").
    *   Scroll through the events you just performed.

---

## 🏁 Ending
"And that is how the DataGov Federation Project unifies Governance, Security, and Quality in a single, automated platform."
