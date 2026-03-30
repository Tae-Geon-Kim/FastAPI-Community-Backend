from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class CommonResponse(BaseModel):
    success: bool = True
    message: str = "사용자의 요청이 성공적으로 수행되었습니다."
    data: Optional[Any] = None

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

class ModiId(BaseModel):
    id: str
    password: str
    new_id: str

class ModiPw(BaseModel):
    id: str
    password: str
    new_password: str
