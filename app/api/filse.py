from fastapi import APIRouter, Depends, status, UploadFile
from typing import List
from app.schemas.files import *
from app.services.files import *
from app.db.database import get_db

router = APIRouter()

# 파일 업로드
@router.post("/upload_files", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def upload_files(
    conn: Connection = Depends(get_db),
    file: UploadFile,
    data: UserLogin,
    board_index: int
):
    result = await upload_files_service(conn, file, data, board_index)

    return result

# 단일 파일 삭제
@router.post("/delete_files", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_files(
    conn: Connection = Depends(get_db),
    data: UserLogin,
    board_index: int,
    files_index: int
):

    result = await delete_files_service(conn, data, board_index, files_index) 

    return result

# 파일 전체를 삭제 (게시판은 삭제 x)
@router.post("/delete_all", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_all(
    conn: Connection = Depends(get_db),
    data: UserLogin,
    board_index: int,
):

    result = await delete_all_services(conn, data, board_index)

    return result

# 삭제된 파일 복구시 게시판 전체 용량 재계산
@router.post("/restore_file", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def restore_file(
    conn: Connection = Depends(get_db),
    data: UserLogin,
    files_index: int,
    board_index: int
):
    result = await restore_file_services(conn, data, files_index, board_index)

    return result