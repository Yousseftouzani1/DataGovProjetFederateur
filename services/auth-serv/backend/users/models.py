from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

# Lowercase roles matching frontend signup form
VALID_ROLES = ["admin", "steward", "annotator", "labeler", "analyst"]


class AdminCreate(BaseModel):
    """Model for admin creation - password in request body, not query param."""
    admin_password: str = Field(..., min_length=8)

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


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

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

