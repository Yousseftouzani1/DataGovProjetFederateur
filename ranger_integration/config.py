# ranger_integration/config.py

import os

RANGER_CONFIG = {
    # HDP Sandbox expose Ranger Admin sur 6080
    "BASE_URL": os.getenv("RANGER_BASE_URL", "http://localhost:6080"),

    "USERNAME": os.getenv("RANGER_USERNAME", "admin"),
    "PASSWORD": os.getenv("RANGER_PASSWORD", "admin"),

    # API REST publique Ranger
    "API_PREFIX": "/service/public/v2/api",

    # KPI < 150ms
    "TIMEOUT": int(os.getenv("RANGER_TIMEOUT", "5"))
}

# Rôles définis par le CDC
RANGER_ROLES = {
    "ADMIN": "admin",
    "DATA_STEWARD": "data_steward",
    "ANNOTATOR": "annotator",
    "LABELER": "data_labeler"
}
