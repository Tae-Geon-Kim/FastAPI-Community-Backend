from fastapi import APIRouter, Depends, status, UploadFile, File, Path
from fastapi_limiter.depends import RateLimiter
from asyncpg import Connection
from app.schemas.common import CommonResponse
from app.schemas.files import DeleteFile, DeleteAllFile, RestoreFile, RestoreAllFile
from app.db.database import get_db
from app.core.security import get_current_user  
from app.services.files import (
    upload_files_services,
    delete_files_services,
    delete_all_services,
    restore_file_services,
    restore_all_file_services
)

router = APIRouter()

# 파일 업로드
@router.post(
    "/boards/{board_index}",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_201_CREATED,
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
    board_index: int = Path(..., gt = 0, description = "파일을 업로드할 게시판 인덱스 (게시판 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await upload_files_services(file, board_index, conn, current_user)


# 단일 파일 삭제
@router.delete(
    "/{file_index}",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 단일 파일 삭제",
    description = """
    특정 단일 파일의 인덱스를 입력받아 해당 파일을 삭제 (soft delete)

    - 삭제 처리를 진행하기 위해서 사용자 비밀번호 재입력 필요
    - 삭제 처리 후 7일이 지나면 복구가 불가하며 100일 후 스케줄러를 통해 hard delete 된다.
    """
)
async def delete_single_file(
    data: DeleteFile,
    file_index: int = Path(..., gt = 0, description = "삭제할 파일의 인덱스 (파일의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await delete_files_services(file_index, data, conn, current_user)

# 특정 게시판의 모든 파일을 일괄 삭제 (게시판은 삭제 x)
@router.delete(
    "/boards/{board_index}",
    dependencies = [Depends(RateLimiter(times = 1, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 파일 전체 삭제",
    description = """
    특정 게시판의 인덱스를 입력받아 해당 게시판에 업로드된 전체 파일을 삭제 (soft delete)

    - 삭제 처리를 진행하기 위헤서는 사용자 비밀번호 재입력 필요
    - 삭제 처리 후 7일이 지나면 복구가 불가하며 100일 후 스케줄러를 통해 hard delete 된다.
    """
)
async def delete_all_files(
    data: DeleteAllFile,
    board_index: int = Path(..., gt = 0, description = "파일을 전체 삭제할 게시판의 인덱스 (게시판 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await delete_all_services(board_index, data, conn, current_user)


# 특정 게시판 DB에 있는 soft delete 삭제된 단일 파일 복구 (게시판 전체 용량 재계산 로직 필요)
@router.post(
    "/{file_index}/restore",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 단일 파일 하나 복구",
    description = """
    특정 단일 파일 데이터를 복구

    - 한 게시판에 최대 허용 용량: 25MB
    - file_index를 입력받아 해당 파일을 복구
    - 복구를 하기 위해서 삭제 처리되었던 기존의 사용자 정보로 로그인 필요.
    - 복구는 soft delete된지 3일이내의 데이터만 가능하다.
    """
)
async def restore_file(
    data: RestoreFile,
    file_index: int = Path(..., gt = 0, description = "복구할 파일의 인덱스 (파일의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await restore_file_services(file_index, data, conn, current_user)

# 특정 게시판 DB에 있는 soft delete 삭제된 파일들 일괄 복구 (게시판 전체 용량 재게산 로직 필요)
@router.post(
    "/boards/{board_index}/restore",
    dependencies = [Depends(RateLimiter(times = 1, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[파일] 전체 파일 복구",
    description = """
    특정 게시판에 삭제 처리된 전체 파일 데이터를 일괄 복구
    
    - 한 게시판에 최대 허용 용량: 25MB
    - boards_index를 입력받아 특정 게시판에 있었던 삭제된 파일 전체를 일괄 복구
    - 복구를 진행 했을 때 한 게시판에 최대 허용 용량인 25MB를 초과하면 복구는 불가능하다.
    - 복구를 하기 위해서는 삭제 처리되었던 기존의 사용자 정보로 로그인 필요.
    - 복구는 soft delete된지 3일내의 데이터만 가능하다.
    """
)
async def restore_all_file(
    data: RestoreAllFile,
    board_index: int = Path(..., gt = 0, description = "전체 파일을 복구할 게시판 인덱스 (게시판 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await restore_all_file_services(board_index, data, conn, current_user)