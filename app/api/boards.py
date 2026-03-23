from fastapi import fastAPI, Depends
from asyncpg import Connection
from app.schemas.boards import CreateBoard
from app.services.boards import create_boards_services
from app.db.database import get_db

router = APIRouter()

# 파일별로 API를 나누기 위해 APIRouter를 사용
@router.post("/bregister")
async def bregister(data: CreateBoard, conn: Connection = Depends(get_db)):

    result = await create_boards_services(conn, data)

    return result