# DataGov Projet Fédérateur

## Système de Gouvernance et Protection des Données Sensibles

Architecture Microservices avec FastAPI + MongoDB

### Services

| Port | Service | Description |
|------|---------|-------------|
| 8001 | auth-serv | Authentication & Roles |
| 8002 | taxonomie-serv | Taxonomy & Classification |
| 8003 | presidio-serv | PII Detection (Moroccan) |
| 8004 | cleaning-serv | Data Cleaning & Profiling |
| 8005 | classification-serv | ML/NLP Classification |
| 8006 | correction-serv | Auto Correction |
| 8007 | annotation-serv | Human Validation |
| 8008 | quality-serv | ISO Quality Metrics |
| 8009 | ethimask-serv | Contextual Masking |

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run a service
cd services/taxonomie-serv
python main.py
```

### Documentation

See `/docs` for detailed documentation.
