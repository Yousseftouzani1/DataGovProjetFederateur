from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    role: str   # "annotator", "labeler", "steward", "admin"


class UserInDB(User):
    id: Optional[str]
    hashed_password: Optional[str]
