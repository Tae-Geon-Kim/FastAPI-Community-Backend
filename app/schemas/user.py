from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserLogin(BaseModel):
    id: str
    password: str

class UserId(BaseModel):
    id: str

class UserInfo(BaseModel):
    id: str
    reg_date: datetime
    update_date: Optional[datetime] = None

    class Config:
        from_attributes = True