# 🗺️ DataGov - Project Services Map

This document centralizes all internal and external service links, ports, and default credentials used in the **DataSentinel** project.

## 🚀 Main Entry Points

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Dashboard** | [http://localhost:8000](http://localhost:8000) | Main user interface (Nginx Gateway) |
| **API Gateway** | [http://localhost:8000/api/v1](http://localhost:8000/api/v1) | Single entry point for all microservices |
| **Airflow UI** | [http://localhost:8081](http://localhost:8081) | Pipeline orchestration |
| **Apache Ambari** | [http://localhost:8080](http://localhost:8080) | HDP Cluster Management (Docker) |
| **Apache Atlas** | [http://localhost:21000](http://localhost:21000) | Metadata and Governance (Docker) |
| **Apache Ranger** | [http://localhost:6080](http://localhost:6080) | Access Control and Security (Docker) |

---

## 🔧 Internal Microservices (FastAPI)

| # | Service Name | Internal Port | API Route Prefix |
| :--- | :--- | :--- | :--- |
| 1 | `auth-serv` | 8001 | `/api/auth/` |
| 2 | `taxonomie-serv` | 8002 | `/api/taxonomie/` |
| 3 | `presidio-serv` | 8003 | `/api/presidio/` |
| 4 | `cleaning-serv` | 8004 | `/api/cleaning/` |
| 5 | `classification-serv` | 8005 | `/api/classification/` |
| 6 | `correction-serv` | 8006 | `/api/correction/` |
| 7 | `annotation-serv` | 8007 | `/api/annotation/` |
| 8 | `quality-serv` | 8008 | `/api/quality/` |
| 9 | `ethimask-serv` | 8009 | `/api/ethimask/` |

---

## 📦 Infrastructure & Databases

| Component | Port / Location | Description |
| :--- | :--- | :--- |
| **MongoDB Atlas** | Cloud (URI in .env) | Cloud-hosted MongoDB cluster |
| **Nginx** | 8000 (Local Docker) | Reverse proxy and frontend host |
| **HDP Sandbox** | Docker Container | HDP Sandbox in Docker (localhost) |
| **NameNode UI** | [http://localhost:50070](http://localhost:50070) | Hadoop DFS Management |
| **SSH (Web Shell)** | [http://localhost:4200](http://localhost:4200) | Shell-in-a-box access |
| **HDP SSH** | ssh root@localhost -p 2222 | Direct SSH access to HDP container |

---

## 🔐 Credential Master Table

| Service / Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **HDP SSH (Root)** | `root` | `hadoop` | SSH/Web Shell Access (Docker) |
| **Apache Ambari** | `raj_ops` | `raj_ops` | Cluster Mgmt |
| **Apache Atlas** | `admin` | `ensias2025` | Metadata API/UI |
| **Apache Ranger** | `admin` | `hortonworks1` | Security API/UI |
| **Airflow UI** | `admin` | `admin` | Local Orchestration |
| **Admin (App)** | `admin` | `admin123` | Full Web Access |
| **Steward (App)** | `steward_user` | `Steward123` | Quality/Approval |
| **Annotator (App)**| `annotator_user` | `Annotator123` | Validation Tasks |
| **Labeler (App)** | `labeler_user` | `Labeler123` | Basic Uploads |

---

## 🌐 Connectivity Notes
- **Local Docker:** All services including HDP run in Docker on `localhost` with fixed ports.
- **HDP Services:** Running in **Docker container** - no more IP address changes!
- **MOCK Mode:** If `MOCK_GOVERNANCE=true` in `.env`, the system will use simulated responses instead of calling Atlas/Ranger.
- **Network Access:** Services in `datagov-network` can access HDP by container name or via localhost from host machine.
