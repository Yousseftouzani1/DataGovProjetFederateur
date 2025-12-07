from pydantic import BaseModel, Field

VALID_ROLES = ["Annotator", "Labeler", "Data Steward", "Admin"]

class User(BaseModel):
    username: str
    password: str
    role: str
    status: str = Field(default="pending")
