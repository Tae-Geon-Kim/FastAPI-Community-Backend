import re
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Any
from app.schemas.user import validate_password_format

# 응답 규격화
class CommonResponse(BaseModel):
    success: bool = True
    message: str = "사용자의 요청이 성공적으로 수행되었습니다."
    data: Optional[Any] = None

# 특정 유저 게시판 조회 / 전체 게시판 조회 모두에서 사용
class BoardFileResponse(BaseModel):
    index: int # 파일의 인덱스
    original_name: str
    file_size: int
    reg_date: datetime

# 게시판 정보 조회 (certain)
class BoardInfo(BaseModel):
    id: str
    index: int # 게시판의 인덱스
    title: str
    content: str
    reg_date: datetime
    update_date: Optional[datetime] = None
    files: list[BoardFileResponse] = []

    class Config: 
        from_attributes = True

# 게시판 정보 조회(all)
class AllBoardInfo(BaseModel):
    author: str
    index: int
    title: str
    content: str
    reg_date: datetime
    update_date: Optional[datetime] = None
    files: list[BoardFileResponse] = []

    class Config:
        from_attributes = True

# 게시판 정보 조회(all) 응답
class AllBoardInfoResponse(BaseModel):
    author: str
    posts : list[AllBoardInfo]

def validate_title_format(v:str)->str:

    # 양쪽 공백 제거 - 공백으로만 내용 채우는 것 방지
    v = v.strip()

    pattern = r'^.{2,50}$'

    if not re.match(pattern, v):
        raise ValueError("게시판 제목 형식이 올바르지 않습니다. (2 ~ 50자)")
    return v

def validate_content_format(v:str)->str:

    # 양쪽 공백 제거 - 공백으로만 내용 채우는 것 방지
    v = v.strip()

    pattern = r'^.{30,2000}$'

    if not re.match(pattern, v, flags = re.DOTALL):
        raise ValueError("게시판 내용 형식이 올바르지 않습니다. (30 ~ 2000자)")
    return v

# 게시판 생성
class CreateBoard(BaseModel):
    title: str = Field(..., min_length = 2, max_length = 50)
    content: str = Field(..., min_length = 30, max_length = 2000)

    @field_validator('title')
    @classmethod
    def check_title(cls, v): return validate_title_format(v)

    @field_validator('content')
    @classmethod
    def check_content(cls, v): return validate_content_format(v)

# 게시판 제목 변경
class ModiTitle(BaseModel):
    board_index: int
    password: str = Field(..., min_length = 8, max_length = 16)
    new_title: str = Field(..., min_length = 2, max_length = 50)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

    @field_validator('new_title')
    @classmethod
    def check_new_title(cls, v): return validate_title_format(v)

# 게시판 내용 변경
class ModiContent(BaseModel):
    board_index: int
    password: str = Field(..., min_length = 8, max_length = 16)
    new_content: str = Field(..., min_length = 30, max_length = 2000)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

    @field_validator('new_content')
    @classmethod
    def check_new_content(cls, v): return validate_content_format(v)

# 게시판 삭제
class DeleteBoards(BaseModel):
    board_index: int
    password: str = Field(..., min_length = 8, max_length = 16)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)

# 게시판 복구
class RestoreBoards(BaseModel):
    board_index: int
    password: str = Field(..., min_length = 8, max_length = 16)

    @field_validator('password')
    @classmethod
    def check_password(cls, v): return validate_password_format(v)