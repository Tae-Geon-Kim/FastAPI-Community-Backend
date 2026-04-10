import re
from pydantic import BaseModel, Field, field_validator
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

class UserInfo(BaseModel):
    id: str
    reg_date: datetime
    update_date: Optional[datetime] = None

    class Config:
        from_attributes = True

# 아이디 제약조건
def validate_id_format(v: str)->str:

    v = v.strip()

    pattern = r'^[a-z0-9]{5,20}$'

    if not re.match(pattern, v):
        raise ValueError("아이디 형식이 올바르지 않습니다. (영문 소문자, 숫자 포함한 5 ~ 20자)")
    return v

# 비밀번호 제약조건
def validate_password_format(v: str)->str:

    pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,16}$'

    if not re.match(pattern, v):
        raise ValueError("비밀번호 형식이 올바르지 않습니다. (영문자, 숫자, 특수문자를 포함한 8 ~ 16자)")
    return v


class UserLogin(BaseModel):
    id: str = Field(..., min_length = 5, max_length = 20)
    password: str = Field(..., min_length = 8, max_length = 16)

    @field_validator('id')
    @classmethod
    def check_id(cls, v): return validate_id_format(v)

    @field_validator('password')
    @classmethod
    def check_pw(cls, v): return validate_password_format(v)

class UserId(BaseModel):
    id: str = Field(..., min_length = 5, max_length = 20)

    @field_validator('id')
    @classmethod
    def check_id(cls, v): return validate_id_format(v)

class UserPw(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 16)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

class ModiId(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 16)
    new_id: str = Field(..., min_length = 5, max_length =20)

    @field_validator('password')
    @classmethod
    def check_id(cls, v): return validate_password_format(v)

    @field_validator('new_id')
    @classmethod
    def check_new_id(cls, v): return validate_id_format(v)

class ModiPw(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 16)
    new_password: str = Field(..., min_length = 8, max_length = 16)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

    @field_validator('new_password')
    @classmethod
    def check_new_password(cls, v): return validate_password_format(v)
