from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Lowercase roles matching frontend signup form
VALID_ROLES = ["admin", "steward", "annotator", "labeler", "analyst"]

class User(BaseModel):
    username: str
    password: str
    role: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str = Field(default="pending")
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    # Algorithm 7 additions
    skills: list[str] = Field(default_factory=list) # e.g. ["PII", "Finance"]
    performance_history: dict = Field(default_factory=dict) # e.g. {"accuracy": 0.9, "speed": 25}

