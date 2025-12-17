# atlas_integration/config.py
"""
Apache Atlas configuration
Conforme au cahier de charges – HDP Sandbox (Docker / VM)
"""

import os

ATLAS_CONFIG = {
    # Adresse Atlas (HDP Sandbox expose Atlas sur 21000)
    # Cas Docker local : http://localhost:21000
    # Cas Docker VM : http://<VM_IP>:21000
    "BASE_URL": os.getenv("ATLAS_BASE_URL", "http://localhost:21000"),

    # Auth par défaut HDP Sandbox
    "USERNAME": os.getenv("ATLAS_USERNAME", "admin"),
    "PASSWORD": os.getenv("ATLAS_PASSWORD", "admin"),

    # API officielle Atlas v2 (CDC)
    "API_PREFIX": "/api/atlas/v2",

    # Performance KPI (< 200 ms)
    "TIMEOUT": int(os.getenv("ATLAS_TIMEOUT", "5")),

    # Fiabilité (sync 100 %)
    "RETRIES": int(os.getenv("ATLAS_RETRIES", "3"))
}

# Métadonnées par défaut exigées par la gouvernance
ATLAS_METADATA = {
    "OWNER": "DataGovernancePlatform",
    "SOURCE": "FastAPI-Microservices",
    "ENVIRONMENT": "HDP-Sandbox"
}
