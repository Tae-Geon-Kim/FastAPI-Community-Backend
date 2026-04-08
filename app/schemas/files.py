from pydantic import BaseModel
from typing import Optional, Any

# 응답 규격화
class CommonResponse(BaseModel):
    success: bool = True
    message: str = "사용자의 요청이 성공적으로 수행되었습니다."
    data: Optional[Any] = None

# 단일 파일 삭제
class DeleteFile(BaseModel):
    password: str
    board_index: int
    files_index: int

# 파일 전체 삭제
class DeleteAllFile(BaseModel):
    password: str
    board_index: int

# 단일 파일 복구 
class RestoreFile(BaseModel):
    password: str
    board_index: int
    files_index: int

# 전체 파일 복구
class RestoreAllFile(BaseModel):
    password: str
    board_index: int
