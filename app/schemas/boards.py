from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

# 응답 규격화
class CommonResponse(BaseModel):
    success: bool = True
    message: str = "사용자의 요청이 성공적으로 수행되었습니다."
    data: Optional[Any] = None

# 게시판 생성
class CreateBoard(BaseModel):
    id: str
    password: str
    title: str
    content: str

# 게시판 정보 조회 (certain)
class BoardInfo(BaseModel):
    id: str
    title: str
    content: str
    reg_date: datetime
    update_date: Optional[datetime] = None

    class Config: 
        from_attributes = True

# 게시판 정보 조회(all)
class AllBoardInfo(BaseModel):
    index: int
    title: str
    content: str
    reg_date: datetime
    update_date: Optional[datetime] = None

    class Config:
        from_attributes = True

# 게시판 정보 조회(all) 응답
class AllBoardInfoResponse(BaseModel):
    author: str
    posts : list[AllBoardInfo]

# 게시판 제목 변경
class ModiTitle(BaseModel):
    id: str
    password: str
    board_index: int
    new_title: str

# 게시판 내용 변경
class ModiContent(BaseModel):
    id: str
    password: str
    board_index: int
    new_content: str

# 게시판 삭제
class DeleteBoards(BaseModel):
    id: str
    password: str
    board_index: int