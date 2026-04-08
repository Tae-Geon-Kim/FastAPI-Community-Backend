from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from typing import List
from app.schemas.files import *
from app.services.files import *
from app.db.database import get_db
from app.core.security import verify_token

router = APIRouter()

# 파일 업로드
@router.post("/uploadFiles", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def upload_files(
    file: UploadFile = File(...),
    board_index: int = Form(...)
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await upload_files_services(file, board_index, conn, current_user_num)

# 단일 파일 삭제
@router.post("/deleteFiles", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_files(
    data: DeleteFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await delete_files_services(data, conn, current_user_num)

# 파일 전체를 삭제 (게시판은 삭제 x)
@router.post("/deleteAll", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def delete_all(
    data: DeleteAllFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await delete_all_services(data, conn, current_user_num)

# 특정 게시판 DB에 있는 soft delete 삭제된 단일 파일 복구 (게시판 전체 용량 재계산)
@router.post("/restoreFile", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def restore_file(
    data: RestoreFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await restore_file_services(data, conn, current_user_num)

# 특정 게시판 DB에 있는 soft delete 삭제된 파일들 일괄 복구 (게시판 전체 용량 재계산)
@router.post("/restoreAllFile", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def restore_all_file(
    data: RestoreAllFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):

    return await restore_all_file_services(data, conn, current_user_num)