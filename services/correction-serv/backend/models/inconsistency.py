from typing import Any
from pydantic import BaseModel

class Inconsistency(BaseModel):
    """
    Représente une incohérence détectée dans une ligne de données
    """
    field: str
    value: Any
    type: str        # FORMAT, DOMAIN, REFERENTIAL, TEMPORAL, SEMANTIC
    message: str
