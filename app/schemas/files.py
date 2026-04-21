from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from app.schemas.user import validate_password_format

# 응답 규격화
class CommonResponse(BaseModel):
    success: bool = True
    message: str = "사용자의 요청이 성공적으로 수행되었습니다."
    data: Optional[Any] = None

# 단일 파일 삭제
class DeleteFile(BaseModel):
    board_index: int = Field(..., gt = 0, description = "게시판 인덱스는 1이상이어야 합니다.")
    files_index: int = Field(..., gt = 0, description = "파일 인덱스는 1이상이어야 합니다.")
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 파일 전체 삭제
class DeleteAllFile(BaseModel):
    board_index: int = Field(..., gt = 0, description = "게시판 인덱스는 1이상이어야 합니다.")
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 단일 파일 복구 
class RestoreFile(BaseModel):
    board_index: int = Field(..., gt = 0, description = "게시판 인덱스는 1이상이어야 합니다.")
    files_index: int = Field(..., gt = 0, description = "파일 인덱스는 1이상이어야 합니다.")
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 전체 파일 복구
class RestoreAllFile(BaseModel):
    board_index: int = Field(..., gt = 0, description = "게시판 인덱스는 1이상이어야 합니다.")
    password: str = Field(..., min_length = 8, max_length = 30)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)
