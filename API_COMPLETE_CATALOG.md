# 📔 DataGov Pro: Complete API Microservices Catalog

This document provides a comprehensive technical reference for all microservices in the DataGov Projet Fédérateur.

## 🏗️ Architecture Overview

The platform follows a microservices architecture coordinated through an **Nginx Gateway** (Port 8000). Persistent storage is managed via **MongoDB Atlas** and orchestration via **Apache Airflow**.

| Service | Port | Primary Responsibility |
| :--- | :--- | :--- |
| **Auth Service** | 8001 | RBAC, JWT tokens, Ranger/Atlas Audit Sync. |
| **Taxonomy Service** | 8002 | Moroccan PII/SPI definition and regex-based detection. |
| **Presidio Service** | 8003 | AI-based PII detection & anonymization (Moroccan + Intl). |
| **Cleaning Service** | 8004 | Data profiling (YData) and cleaning pipelines (IQR). |
| **Classification Service**| 8005 | ML Ensemble (RF/BERT) for column sensitivity tagging. |
| **Correction Service** | 8006 | Automatic inconsistency detection and T5 learning. |
| **Annotation Service** | 8007 | Human-in-the-loop validation & quality metrics (Kappa). |
| **Quality Service** | 8008 | ISO 25012 compliance scoring and PDF reports. |
| **EthiMask Service** | 8009 | Contextual masking framework via Perceptron logic. |

---

## 🔐 1. Auth Service (Port 8001)
*Module d'Authentification et Gestion des Rôles*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/login` | `POST` | Authenticate and get JWT Bearer token. |
| `/users` | `GET` | (Admin) List all users and role distribution. |
| `/create` | `POST` | (Steward) Create a new user account. |
| `/approve/{user}` | `POST` | (Admin) Activate a pending user. |
| `/reject/{user}` | `POST` | (Admin) Reject/Deactivate a pending user. |
| `/users/{username}/role`| `PUT` | **US-AUTH-03**: Update user role (Manage Permissions). |
| `/ranger/check-access`| `GET` | Verify resource access against Ranger policies. |
| `/audit-logs` | `GET` | Consult system audit trials (Steward view). |

**Login Request:** `username`, `password` (OAuth2 Form).

---

## 🇲🇦 2. Taxonomy Service (Port 8002)
*Moroccan PII/SPI Taxonomy Manager*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/analyze` | `POST` | Regex scan for CIN, Phone, CNSS, and Arabic PII. |
| `/patterns` | `POST` | **US-TAX-02**: Add new PII Categories & Patterns dynamically. |
| `/domains` | `GET` | List available taxonomy domains (Health, Finance, etc). |
| `/patterns` | `GET` | View all compiled regex patterns for Morocco. |
| `/sync-atlas` | `POST` | Push taxonomy definitions to Apache Atlas tags. |

---

## 🔒 3. Presidio Service (Port 8003)
*AI PII Detection & Anonymization Engine*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/analyze` | `POST` | Deep NLP scan for 20+ entities. |
| `/anonymize` | `POST` | Redact, Mask, or Encrypt text using Presidio Operators. |
| `/recognizers` | `POST` | **US-PRES-02**: Register custom PII recognizers (Patterns). |
| `/entities` | `GET` | List all supported entity types. |
| `/execute` | `POST` | Trigger Airflow batch anonymization task. |

---

## 🧹 4. Cleaning Service (Port 8004)
*Data Profiling & Pipeline Orchestration*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/cleaning/upload` | `POST` | Upload CSV/Excel for processing. |
| `/api/v1/cleaning/datasets` | `GET` | **US-CLEAN-05**: List all active datasets (Discovery). |
| `/api/v1/cleaning/profile/{id}` | `GET` | Generate Interactive HTML Profiling Report. |
| `/api/v1/cleaning/clean/{id}` | `POST` | Run cleaning: Duplicates, Outliers (IQR), Normalization. |
| `/api/v1/cleaning/download/{id}` | `GET` | Retrieve the cleaned CSV file. |

---

## 🏷️ 5. Classification Service (Port 8005)
*Fine-Grained Column Sensitivity Tagging*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/classification/classify` | `POST` | Use Ensemble ML to classify column sensitivity levels. |
| `/api/v1/classification/retrain` | `POST` | **US-CLASS-03**: Trigger ensemble model retraining. |
| `/api/v1/classification/stats` | `GET`| Global distribution of PII/SPI classes. |
| `/api/v1/classification/config` | `POST`| (Steward) Adjust ML weights and review thresholds. |

---

## 🔧 6. Correction Service (Port 8006)
*Automatic Data Quality Remediation*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/detect` | `POST` | Detect 6 types of inconsistencies (Domain, Temporal, etc). |
| `/correct` | `POST` | Generate T5-ML suggestions for detected errors. |
| `/config/rules` | `POST` | **US-CORR-02**: Define custom correction rules dynamically. |
| `/corrections/validate` | `POST` | (Annotator) Accept/Modify/Reject ML suggestions. |
| `/kpi/dashboard` | `GET` | Monitor Auto-Correction rate and Precision KPIs. |

---

## 👤 7. Annotation Service (Port 8007)
*Human-in-the-loop Validation Workflow*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/tasks` | `POST` | Create a new validation task for row/dataset. |
| `/tasks/my-queue` | `GET` | **US-VALID-04**: Annotator-specific pending task queue. |
| `/assign` | `POST` | **Algorithm 7**: Smart skill-based workload assignment. |
| `/tasks/{id}/submit` | `POST` | Submit human validation results. |
| `/users/{id}/stats` | `GET` | View **Algorithm 6**: Cohen's Kappa & Accuracy metrics. |

---

## 📊 8. Quality Service (Port 8008)
*ISO 25012 Compliance and Reporting*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/evaluate/{id}` | `POST` | Calculate 6-Dimension Score (Completeness, Uniqueness...). |
| `/thresholds` | `POST` | **US-QUAL-04**: Configure ISO 25012 dimension weights. |
| `/report/{id}` | `GET` | Retrieve structured quality assessment. |
| `/report/{id}/pdf` | `GET` | Download official ISO 25012 PDF Quality Certificate. |

---

## 🎭 9. EthiMask Service (Port 8009)
*Contextual Data De-identification Framework*

### Endpoints
| Path | Method | Description |
| :--- | :--- | :--- |
| `/mask` | `POST` | **Perceptron Logic**: Mask data based on Role/Context/Purpose. |
| `/policies` | `POST` | (Steward) Define granular masking rules per entity. |
| `/retrain` | `POST` | **Pattern Learning**: Adjust Perceptron weights via Audit Logs. |

---

## 🚦 Common Data Models

### 💎 Standard Response Wrapper
All services return a common success format:
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-01-22T..."
}
```

### 🚨 Service Errors
```json
{
  "detail": "Error message description",
  "error_code": "ERR_SERVICE_TYPE"
}
```
