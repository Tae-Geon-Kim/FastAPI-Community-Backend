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