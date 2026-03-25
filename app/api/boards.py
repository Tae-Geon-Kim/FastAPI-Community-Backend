from fastapi import APIRouter, Depends
from asyncpg import Connection
from app.schemas.boards import CreateBoard
from app.services.boards import create_boards_services, boards_info_services
from app.schemas.user import UserId
from app.db.database import get_db

router = APIRouter()
# 파일별로 API를 나누기 위해 APIRouter를 사용

# 게시판 생성
@router.post("/bregister")
async def bregister(data: CreateBoard, conn: Connection = Depends(get_db)):

    result = await create_boards_services(conn, data)

    return result

# 게시판 조회
@router.post("/binfo")
async def binfo(data: UserId, conn: Connection = Depends(get_db)):

    result = await boards_info_services(conn, data)

    return result