from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from app.schemas.user import validate_password_format

# 단일 파일 삭제
class DeleteFile(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 파일 전체 삭제
class DeleteAllFile(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 단일 파일 복구 
class RestoreFile(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 전체 파일 복구
class RestoreAllFile(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)
