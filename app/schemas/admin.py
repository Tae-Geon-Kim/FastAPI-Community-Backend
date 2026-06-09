from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from app.schemas.boards import validate_title_format, validate_content_format

# 관리자 공지사항 생성
class CreateNotice(BaseModel):
    title: str = Field(..., min_length = 2, max_length = 200)
    content: str = Field(..., min_length = 30, max_length = 2000)

    @field_validator('title')
    @classmethod
    def check_title(cls, v): return validate_title_format(v)

    @field_validator('content')
    @classmethod
    def check_content(cls, v): return validate_content_format(v)

# 관리자 유저, 게시판 삭제 옵션
class DeleteOption(str, Enum):
    SCHEDULED = "SCHEDULED"
    RETAIN = "RETAIN"
    IMMEDIATE = "IMMEDIATE"

# 관리자 파일 삭제 옵션
class FileDeleteOption(str, Enum):
    SCHEDULED = "SCHEDULED"
    IMMEDIATE = "IMMEDIATE"