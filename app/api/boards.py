from fastapi import APIRouter, Depends, status
from asyncpg import Connection
from app.schemas.boards import CreateBoard
from app.services.boards import *
from app.schemas.user import UserId, CommonResponse
from app.db.database import get_db

router = APIRouter()
# 파일별로 API를 나누기 위해 APIRouter를 사용

# 게시판 생성
@router.post("/bregister", response_model = CommonResponse, status_code = status.HTTP_201_CREATED)
async def bregister(data: CreateBoard, conn: Connection = Depends(get_db)):

    result = await create_boards_services(conn, data)

    return result

# 특정 유저의 게시판 조회
@router.post("/certain_binfo", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def certain_binfo(data: UserId, conn: Connection = Depends(get_db)):

    result = await certain_boards_info_services(conn, data)

    return result

# 모든 유저의 게시판 조회
@router.get("/all_binfo", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def all_binfo(conn: Connection = Depends(get_db)):

    result = await all_boards_info_services(conn)

    return result

# 게시판 제목 변경
@router.post("/modiTitle", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def modiTitle(data: ModiTitle, conn: Connection = Depends(get_db)):

    result = await title_modify_services(conn, data)

    return result