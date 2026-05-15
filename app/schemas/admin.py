from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.boards import validate_title_format, validate_content_format

# 공지사항 생성
class CreateNotice(BaseModel):
    title: str = Field(..., min_length = 2, max_length = 50)
    content: str = Field(..., min_length = 30, max_length = 2000)

    @field_validator('title')
    @classmethod
    def check_title(cls, v): return validate_title_format(v)

    @field_validator('content')
    @classmethod
    def check_content(cls, v): return validate_content_format(v)