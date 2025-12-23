from pydantic import BaseModel, Field
from typing import Optional

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
