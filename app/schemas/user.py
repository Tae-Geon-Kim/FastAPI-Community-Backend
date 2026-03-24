from pydantic import BaseModel

class UserCreate(BaseModel):
    id: str
    password: str

class UserIdCheck(BaseModel):
    id: str