from fastapi import APIRouter, Depends, status, Path
from fastapi_limiter.depends import RateLimiter
from asyncpg import Connection
from app.core.security import require_admin, get_current_user
from app.db.database import get_db
from app.schemas.common import CommonResponse
from app.schemas.admin import CreateNotice
from app.services.admin import (
    admin_get_all_users_services,
    admin_get_specific_user_services,
    admin_get_specific_board_services,
    admin_register_notice_services,
    admin_user_blacklist_services,
    admin_soft_delete_board_services,
    admin_IMT_hard_delete_board_services,
    admin_IMT_hard_delete_file_services,
    admin_soft_delete_file_services,
    admin_restore_board_services,
    admin_restore_file_services
)

router = APIRouter(dependencies = [Depends(require_admin)])

# 관리자 전체 유저 목록 조회
@router.get(
    "/users",
    dependencies = [Depends(RateLimiter(times = 100, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 전체 유저(정보) 조회",
    description = """
    현재 가입되어 있는 모든 유저의 정보를 출력

    - 삭제처리된 유저의 정보도 조회 가능
    - 관리자만 접근 가능
    """
)
async def get_all_users(
    conn: Connection = Depends(get_db)
):
    return await admin_get_all_users_services(conn)


# 관리자 전체 유저 중 특정 유저 상세 조회
@router.get(
    "/users/{user_index}",
    dependencies = [Depends(RateLimiter(times = 100, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 특정 유저(정보) 상세조회",
    description = """
    현재 가입되어 있는 모든 유저 중 특정 유저의 정보를 출력

    - 삭제처리된 유저의 정보도 조회 가능
    - 관리자만 접근 가능
    """
)
async def get_specific_user(
    user_index: int = Path(..., gt = 0, description = "상세 조회할 유저의 인덱스 (유저의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_get_specific_user_services(user_index, conn)


# 관리자 전체 유저 중 특정 게시판 상세 조회
@router.get(
    "/users/{user_index}/boards/{board_index}",
    dependencies = [Depends(RateLimiter(times = 100, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 특정 게시판(정보) 상세조회",
    description = """
    관리자가 모든 게시판중 특정 게시판의 정보를 상세조회

    - 삭제처리된 게시판의 정보도 조회 가능
    - 관리자만 접근 가능
    """
)
async def get_specific_board(
    user_index: int = Path(..., gt = 0, description = "상세 조회할 게시판 작성자의 인덱스 (작성자의 인덱스는 1이상이여야 합니다.)"),
    board_index: int = Path(..., gt = 0, description = "상세 조회할 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_get_specific_board_services(user_index, board_index, conn)


# 관리자 공지사항 작성
@router.post(
    "/boards",
    dependencies = [Depends(RateLimiter(times = 1, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_201_CREATED,
    summary = "[관리자] 공지사항 작성",
    description = """
    관리자가 공시사항이라는 태그가 있는 게시판을 작성

    - 게시판 목록 상단에 [공시사항]으로 고정되는 게시판을 작성
    - 관리자만 접근 가능
    """
)
async def register_notice(
    data: CreateNotice,
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_register_notice_services(data, conn, current_user)


# 관리자 유저 삭제 (블랙리스트 관리)
@router.delete(
    "/users/{user_index}",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 특정 유저를 관리자 권한으로 삭제 (soft delete)",
    description = """
    부적절한 행동을 한 유저 삭제

    - 블랙리스트를 만들어 부적절한 유저를 감시 및 관리자 권한으로 삭제
    - 1번 BANNED 처리되면 1일동안 정지 / 2번 BANNED 처리되면 3일 정지 / 3번 BANNED 처리되면 5일 정지
    - 4번째 BANNED 처리되면 자동으로 삭제 처리 (WITHDRAWN)
    - 관리자만 접근 가능
    """
)
async def user_blacklist(
    user_index: int = Path(..., gt = 0, description = "관리자 - 블랙리스트(삭제) 처리할 유저의 인덱스 (유저의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_user_blacklist_services(user_index, conn)


# 관리자 특정 게시판 삭제 처리 (soft delete)
@router.delete(
    "/boards/{board_index}/soft",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 부적절한 게시판을 관리자 권한으로 삭제 (soft delete)",
    description = """
    부적절한 게시판을 관리자 권한으로 삭제처리 (soft delete)
    
    - soft delete (삭제 처리 후 3일내 복구 가능)
    - 실제로 삭제 처리되는 것은 스케줄러를 통해서 자동으로 실행된다. (삭제 처리된지 3일이 지나면 hard delete)
    - 관리자만 접근 가능
    """
)
async def admin_soft_delete_board(
    board_index: int = Path(..., gt = 0, description = "관리자 - 삭제처리(soft delete) 할 게시판(공지사항) 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_soft_delete_board_services(board_index, conn)


# 관리자 특정 게시판 hard delete
@router.delete(
    "/boards/{board_index}/hard",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 부적절한 게시판을 관리자 권한으로 삭제",
    description = """
    부적절한 게시판을 관리자 권한으로 삭제 (hard delete)

    - hard delete이기 때문에 복구 불가능
    - 이미 삭제처리된 게시판도 바로 hard delete 가능
    - 관리자만 접근 가능
    """
)
async def admin_IMT_hard_delete_boards(
    board_index: int = Path(..., gt = 0, description = "관리자 - 삭제할 게시판의 인덱스 (게시판의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_IMT_hard_delete_board_services(board_index, conn)


# 관리자 특정 단일 파일 삭제 처리 (soft delete)
@router.delete(
    "/files/{file_index}/soft",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 부적절한 파일을 관리자 권한으로 삭제 (soft delete)",
    description = """
    부적절한 파일을 관리자 권한으로 삭제 (soft delete)

    - soft delete (삭제 처리 후 3일내 복구 가능)
    - 실제로 삭제 처리되는 것은 스케줄러를 통해서 자동으로 실행된다. (삭제 처리된지 3일이 지나면 hard delete)
    - 관리자만 접근 가능
    """
)
async def admin_soft_delete_file(
    file_index: int = Path(..., gt = 0, description = "관리자 - 삭제처리(soft delete) 할 파일의 인덱스 (파일의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_soft_delete_file_services(file_index, conn)


# 관리자 특정 단일 파일 hard delete
@router.delete(
    "/files/{file_index}/hard",
    dependencies = [Depends(RateLimiter(times = 10, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 부적절한 게시판을 관리자 권한으로 삭제",
    description = """
    부적절한 게시판을 관리자 권한으로 삭제 (hard delete)

    - 부적절한 파일을 관리자 권한으로 삭제 (hard delete - 복구 불가능)
    - 관리자만 접근 가능
    """
)
async def admin_IMT_hard_delete_files(
    file_index: int = Path(..., gt = 0, description = "관리자 - 삭제할 파일의 인덱스 (파일의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_IMT_hard_delete_file_services(file_index, conn)

# 관리자 한 게시판에 존재하는 모든 파일 soft delete
@router.delete(
    "/boards/{board_index}/files/soft",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 특정 게시판 모든 파일 삭제 처리",
    description = """
    한 게시판에 존재하는 모든 파일 삭제처리 (soft delete)

    - 관리자만 접근 가능
    """
)
async def admin_soft_delete_all_files(
    board_index: int = Path(..., gt = 0, description = "관리자 - 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_soft_delete_all_files_services(board_index, conn)

# 관리자 한 게시판에 존재하는 모든 파일 hard delete
@router.delete(
    "/boards/{board_index}/files/hard",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 특정 게시판 모든 파일 영구 삭제",
    description = """
    한 게시판에 존재하는 모든 파일 강제 삭제 (hard delete)

    - 관리자만 접근 가능
    """
)
async def admin_IMT_hard_delete_all_files(
    board_index: int = Path(..., gt = 0, description = "관리자 - 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_IMT_hard_delete_all_files_services(board_index, conn)


# 관리자 soft delete한 게시판 복구
@router.post(
    "/boards/{board_index}/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 게시판 복구",
    description = """
    삭제 처리된 게시판을 관리자 권한으로 복구

    - 삭제처리된지 3일내의 게시판만 복구 가능
    - 관리자만 접근 가능
    """
)
async def admin_restore_board(
    board_index: int = Path(..., gt = 0, description = "관리자 - 복구할 게시판 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_restore_board_services(board_index, conn)


# 관리자 soft delete한 파일 복구
@router.post(
    "/boards/{board_index}/files/{file_index}/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 파일 복구",
    description = """
    삭제 처리된 파일을 관리자 권한으로 복구

    - 삭제처리된지 3일내의 파일만 복구 가능
    - 관리자만 접근 가능
    """
)
async def admin_restore_file(
    board_index: int = Path(..., gt = 0, description = "관리자 - 복구할 파일이 속한 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    file_index: int = Path(..., gt = 0, description = "관리자 - 복구할 파일 인덱스 (파일의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_restore_file_services(board_index, file_index, conn)

# 관리자 한 게시판에 삭제처리된 모든 파일 복구
@router.post(
    "/boards/{board_index}/files/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 파일 일괄 복구",
    description = """
    특정 게시판에 삭제 처리된 모든 파일 일괄 복구

    - 관리자만 접근 가능
    """
)
async def admin_restore_all_files(
    board_index: int = Path(..., gt = 0, description = "관리자 - 파일 일괄 복구할 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await admin_restore_all_files_services(board_index, conn)