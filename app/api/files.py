from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from typing import List
from app.schemas.files import *
from app.services.files import *
from app.db.database import get_db
from app.core.security import get_current_user
from asyncpg import Connection

router = APIRouter()

# 파일 업로드
@router.post(
    "/uploadFiles",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 파일 업로드",
    description = """
    게시판의 인덱스를 입력받아 해당 게시판에 파일을 업로드 (파일 확장자, 단일 파일 최대 용량 제한있음)

    - 허용되는 파일 확장자: jpg, jpeg, png, gif, webp, pdf, docx, xlsx, pptx, txt, zip
    - 허용되는 단일 파일 최대 용량: 5MB
    - 한 게시판에 최대 허용 용량: 25MB
    """
)
async def upload_files(
    file: UploadFile = File(...),
    board_index: int = Form(..., gt = 0, description = "게시판 인덱스는 1 이상이어야 합니다."),
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await upload_files_services(file, board_index, conn, current_user_num)


# 단일 파일 삭제
@router.post(
    "/deleteFiles",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 단일 파일 삭제",
    description = """
    특정 게시판 (files_index)에 업로드된 단일 파일 삭제 (soft delete)

    - 삭제 처리를 진행하기 위해서 사용자 비밀번호 재입력 필요 
    - 실제로 삭제처리되는 것은 스케줄링을 통해 자동으로 실행된다. (삭제처리 상태가 된지 3일이 지났으면 hard delete 된다.)
    """
)
async def delete_files(
    data: DeleteFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await delete_files_services(data, conn, current_user_num)

# 파일 전체를 삭제 (게시판은 x)
@router.post(
    "/deleteAll",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 파일 전체 삭제",
    description = """
    특정 게시판 (files_index)에 업로드된 전체 파일을 삭제 (soft delete)

    - 삭제 처리를 진행하기 위헤서는 사용자 비밀번호 재입력 필요
    """
)
async def delete_all(
    data: DeleteAllFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await delete_all_services(data, conn, current_user_num)


# 특정 게시판 DB에 있는 soft delete 삭제된 단일 파일 복구 (게시판 전체 용량 재계산 로직 필요)
@router.post(
    "/restoreFile",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 단일 파일 하나 복구",
    description = """
    특정 게시판에 삭제 처리된 단일 파일 데이터 하나를 복구

    - 한 게시판에 최대 허용 용량: 25MB
    - boards_index, files_inedx를 입력받아 특정 게시판에 있었던 특정 파일을 복구
    - 복구를 하기 위해서 삭제 처리되었던 기존의 사용자 정보로 로그인 필요.
    - 복구는 soft delete된지 3일이내의 데이터만 가능하다.
    """
)
async def restore_file(
    data: RestoreFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await restore_file_services(data, conn, current_user_num)

# 특정 게시판 DB에 있는 soft delete 삭제된 파일들 일괄 복구 (게시판 전체 용량 재게산 로직 필요)
@router.post(
    "/restoreAllFile",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 전체 파일 복구",
    description = """
    특정 게시판에 삭제 처리된 전체 파일 데이터를 일괄 복구
    
    - 한 게시판에 최대 허용 용량: 25MB
    - boards_index를 입력받아 특정 게시판에 있었던 삭제된 파일 전체를 일괄 복구
    - 복구를 하기 위해서는 삭제 처리되었던 기존의 사용자 정보로 로그인 필요.
    - 복구는 soft delete된지 3일내의 데이터만 가능하다.
    """
)
async def restore_all_file(
    data: RestoreAllFile,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await restore_all_file_services(data, conn, current_user_num)