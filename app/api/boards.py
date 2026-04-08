from fastapi import APIRouter, Depends, status
from asyncpg import Connection
from app.schemas.boards import CreateBoard
from app.services.boards import *
from app.schemas.user import UserId, UserLogin
from app.db.database import get_db

router = APIRouter()
# 파일별로 API를 나누기 위해 APIRouter를 사용

# 특정 유저의 게시판 생성
@router.post("/bRegister", response_model = CommonResponse, status_code = status.HTTP_201_CREATED)
async def bregister(
    data: CreateBoard,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await create_boards_services(data, conn, current_user_num)

# 특정 유저의 게시판 조회
@router.post("/certainBInfo", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def certain_binfo(
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await certain_boards_info_services(conn, current_user_num)

# 모든 유저의 게시판 조회
@router.get("/allBInfo", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def all_binfo(conn: Connection = Depends(get_db)):

    return await all_boards_info_services(conn)

# 게시판 제목 변경
@router.post("/modiTitle", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def modi_title(
    data: ModiTitle,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await title_modify_services(data, conn, current_user_num)

# 게시판 내용 변경 
@router.post("/modiContent", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def modi_content(
    data: ModiContent,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await content_modify_services(data, conn, current_user_num)

# 게시판 삭제
@router.post("/deleteBoards", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_boards(
    data: DeleteBoards
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await boards_delete_services(data, conn, current_user_num)

# 게시판 복구
@router.post("/restoreBoards", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def restore_boards(
    data: RestoreBoards,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):

    return await restore_board_services(data, conn, current_user_num)