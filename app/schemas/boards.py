from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 게시판 생성
class CreateBoard(BaseModel):
    id: str
    password: str
    title: str
    content: str

# 게시판 정보 조회
class BoardInfo(BaseModel):
    id: str
    title: str
    content: str
    reg_date: datetime
    update_date: Optional[datetime] = None

    class Config: 
        from_attributes = True
