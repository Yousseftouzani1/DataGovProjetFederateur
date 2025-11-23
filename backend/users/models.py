from pydantic import BaseModel

VALID_ROLES = ["Annotator", "Labeler", "Data Steward"]

class User(BaseModel):
    username: str
    password: str
    role: str
