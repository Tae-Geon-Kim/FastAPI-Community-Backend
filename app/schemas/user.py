from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

# 응답 규격화
class CommonResponse(BaseModel):
    success: bool = True
    message: str = "사용자의 요청이 성공적으로 수행되었습니다."
    data: Optional[Any] = None

# CommonResponse JWT 토큰 인증 data 
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# JWT 토큰 
class TokenRefreshRequest(BaseModel):
    refresh_token: str

class UserLogin(BaseModel):
    id: str
    password: str

class UserId(BaseModel):
    id: str

class UserPw(BaseModel):
    password: str

class UserInfo(BaseModel):
    id: str
    reg_date: datetime
    update_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModiId(BaseModel):
    password: str
    new_id: str

class ModiPw(BaseModel):
    password: str
    new_password: str
