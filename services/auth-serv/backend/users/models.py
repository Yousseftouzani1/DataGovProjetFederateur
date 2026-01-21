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
    is_active: bool = Field(default=True)  # Algorithm 1: is_active check
    last_login: Optional[datetime] = None  # Algorithm 1: last_login tracking

