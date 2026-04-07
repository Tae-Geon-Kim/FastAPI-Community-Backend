from fastapi import APIRouter, Depends, status, UploadFile
from typing import List
from app.schemas.files import *
from app.services.files import *
from app.db.database import get_db

router = APIRouter()

# 파일 업로드
@router.post("/uploadFiles", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def upload_files(
    file: UploadFile,
    data: UserLogin,
    board_index: int,
    conn: Connection = Depends(get_db)
):
    result = await upload_files_service(conn, file, data, board_index)

    return result

# 단일 파일 삭제
@router.post("/deleteFiles", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_files(
    data: UserLogin,
    board_index: int,
    files_index: int,
    conn: Connection = Depends(get_db)
):

    result = await delete_files_service(conn, data, board_index, files_index) 

    return result

# 파일 전체를 삭제 (게시판은 삭제 x)
@router.post("/deleteAll", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_all(
    data: UserLogin,
    board_index: int,
    conn: Connection = Depends(get_db)
):

    result = await delete_all_services(conn, data, board_index)

    return result

# 특정 게시판 DB에 있는 soft delete 삭제된 단일 파일 복구 (게시판 전체 용량 재계산)
@router.post("/restoreFile", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def restore_file(
    data: UserLogin,
    files_index: int,
    board_index: int,
    conn: Connection = Depends(get_db)
):
    result = await restore_file_services(conn, data, files_index, board_index)

    return result

# 특정 게시판 DB에 있는 soft delete 삭제된 파일들 일괄 복구 (게시판 전체 용량 재계산)
@router.post("/restoreAllFile", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def restore_all_file(
    data: UserLogin,
    board_index: int,
    conn: Connection = Depends(get_db)
):

    result = await restore_all_file_services(conn, data, board_index)

    return result