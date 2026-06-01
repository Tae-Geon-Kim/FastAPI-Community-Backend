from fastapi import APIRouter, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from asyncpg import Connection
from app.core.security import require_admin, get_current_user
from app.db.database import get_db
from app.schemas.common import CommonResponse
from app.schemas.admin import CreateNotice, DeleteOption

from app.services.admin import (
    admin_get_all_users_services,
    admin_get_specific_user_services,
    admin_get_specific_board_services,
    admin_register_notice_services,
    admin_user_ban_services,
    admin_user_unban_services,
    admin_delete_user_services,
    admin_delete_boards_services,
    admin_delete_one_file_services,
    admin_delete_all_board_files_services,
    admin_restore_user_services,
    admin_restore_board_services,
    admin_restore_file_services,
    admin_restore_all_files_services
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


# 관리자 유저 blacklist ban API
@router.post(
    "/users/{user_index}/ban",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 유저 블랙리스트 처리 (ban / delete)",
    description = """
    부적절한 행동을 한 유저를 벤

    - 블랙리스트를 만들어 부적절한 유저를 감시 및 관리자 권한으로 삭제
    - 1번 BANNED 처리되면 1일동안 정지 / 2번 BANNED 처리되면 3일 정지 / 3번 BANNED 처리되면 5일 정지
    - 4번째 BANNED 처리되면 자동으로 삭제 처리 (WITHDRAWN - soft delete)
    - 관리자만 접근 가능
    """
)
async def user_blacklist_ban(
    user_index: int = Path(..., gt = 0, description = "관리자 - 블랙리스트, ban 처리할 유저의 인덱스 (유저의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_user_ban_services(user_index, conn, current_user)

# 관리자 유저 blacklist unban API
@router.post(
    "/users/{user_index}/unban",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 유저 블랙리스트 처리 철회(unban)",
    description = """
    벤 당한 유저를 복구

    - 벤 당한 특정 유저의 벤 횟수를 초기화 및 즉시 활동 가능한 상태로 변경
    - 관리자만 접근 가능
    """
)
async def user_blacklist_unban(
    user_index: int = Path(..., gt = 0, description = "관리자 - 블랙리스트 처리 (ban)를 철회시킬 유저의 인덱스 (유저의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_user_unban_services(user_index, conn, current_user)

# admin user delete API
@router.delete(
    "/users/{user_index}",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 유저 삭제",
    description = """
    특정 유저를 삭제

    - soft delete 후 데이터 보관 / soft delete 후 데이터 스케줄러 삭제 / 즉시 hard delete 중 하나 선택해서 삭제
    - user 데이터가 삭제되면 해당 user의 boards, files 데이터도 같은 옵션으로 같이 삭제된다.
    - user 데이터 삭제 처리 후 보관될 때 유저를 특정할 수 있는 개인정보는 삭제되고 USER의 게시판 작성자, 파일 업로드자가 '알수없음' 으로 바뀐다.
    - soft delete된 데이터의 경우 90일 이내에 복구를 원할시 복구 가능 & 100일이 지나면 스케줄러를 통해 삭제
    - soft delete 후 데이터 보관 옵션을 선택해도 파일 데이터는 DB 과부하를 방지하기 위해 100일이 지나면 스케줄러를 통해 삭제
    - 관리자만 접근 가능
    """
)
async def admin_delete_user(
    user_index: int = Path(..., gt = 0, description = "관리자 - 삭제할 유저의 인덱스 (유저의 인덱스는 1이상이여야 합니다.)"),
    delete_option: DeleteOption = Query(..., description = "관리자 - 삭제할 옵션 (SCHEDULED, RETAIN, IMMEDIATE)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_delete_user_services(user_index, delete_option, conn, current_user)

# admin boards delete API 통합
@router.delete(
    "/boards/{board_index}",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 게시판 삭제",
    description = """
    특정 게시판을 삭제

    - soft delete 후 데이터 보관 / soft delete 후 데이터 스케줄러 삭제 / 즉시 hard delete 중 하나 선택해서 삭제
    - boards 데이터가 삭제되면 해당 boards의 files 데이터도 같은 옵션으로 같이 삭제된다.
    - soft delete된 데이터의 경우 90일 이내에 복구를 원할시 복구 가능 & 100일이 지나면 스케줄러를 통해 삭제
    - soft delete 후 데이터 보관 옵션을 선택해도 파일 데이터는 DB 과부하를 방지하기 위해 100일이 지나면 스케줄러를 통해 삭제
    - 관리자만 접근 가능
    """
)
async def admin_delete_boards(
    board_index: int = Path(..., gt = 0, description = "관리자 - 삭제할 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    delete_option: DeleteOption = Query(..., description = "관리자 - 삭제할 옵션 (SCHEDULED, RETAIN, IMMEDIATE)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_delete_boards_services(board_index, delete_option, conn, current_user)

# admin one file delete (단일 파일) API 통합
@router.delete(
    "/files/{file_index}",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 단일 파일 삭제",
    description = """
    특정 파일 하나를 삭제

    - soft delete (스케줄러 삭제) / 즉시 hard delete 중 하나 선택해서 삭제
    - soft delete된 데이터의 경우 90일 이내에 복구를 원할시 복구 가능 & 100일이 지나면 스케줄러를 통해 삭제
    - 관리자만 접근 가능
    """
)
async def admin_delete_one_file(
    file_index: int = Path(..., gt = 0, description = "관리자 - 삭제할 파일의 인덱스 (파일의 인덱스는 1이상이여야 합니다.)"),
    delete_option: DeleteOption = Query(..., description = "관리자 - 삭제할 옵션 (SCHEDULED, RETAIN, IMMEDIATE)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_delete_one_file_services(file_index, delete_option, conn, current_user)
   
# admin all boards files delete (한 게시판 파일 전체) API 통합
@router.delete(
    "/boards/{board_index}/files",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 파일 일괄 삭제",
    description = """
    특정 게시판의 파일 일괄 삭제

    - soft delete (스케줄러 삭제) / 즉시 hard delete 중 하나 선택해서 삭제
    - soft delete된 데이터의 경우 90일 이내에 복구를 원할시 복구 가능 & 100일이 지나면 스케줄러를 통해 삭제
    - 관리자만 접근 가능
    """
)
async def admin_delete_all_board_files(
    board_index: int = Path(..., gt = 0, description = "관리자 - 파일 일괄 삭제할 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    delete_option: DeleteOption = Query(..., description = "관리자 - 삭제할 옵션 (SCHEDULED, RETAIN, IMMEDIATE)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_delete_all_board_files_services(board_index, delete_option, conn, current_user)

# 관리자 soft delete한 유저 복구
@router.post(
    "/users/{user_index}/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 유저 복구",
    description = """
    삭제 처리된 유저를 관리자 권한으로 복구

    - 관리자는 삭제처리된지 90일이내의 유저만 복구 가능
    - 권한 상관없이 복구 가능
    - 관리자만 접근 가능
    """
)
async def admin_restore_user(
    user_index: int = Path(..., gt = 0, description = "관리자 - 복구할 유저의 인덱스 (유저의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_restore_user_services(user_index, conn, current_user)

# 관리자 soft delete한 게시판 복구
@router.post(
    "/boards/{board_index}/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 게시판 복구",
    description = """
    삭제 처리된 게시판을 관리자 권한으로 복구

    - 관리자는 삭제처리된지 90일이내의 게시판만 복구 가능
    - 권한 상관없이 복구 가능
    - 관리자만 접근 가능
    """
)
async def admin_restore_board(
    board_index: int = Path(..., gt = 0, description = "관리자 - 복구할 게시판 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_restore_board_services(board_index, conn, current_user)


# 관리자 soft delete한 단일 파일 복구
@router.post(
    "/boards/{board_index}/files/{file_index}/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 파일 복구",
    description = """
    삭제 처리된 파일을 관리자 권한으로 복구

    - 관리자는 삭제처리된지 90일이내의 파일만 복구 가능
    - 권한 상관없이 복구 가능
    - 관리자만 접근 가능
    """
)
async def admin_restore_file(
    board_index: int = Path(..., gt = 0, description = "관리자 - 복구할 파일이 속한 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    file_index: int = Path(..., gt = 0, description = "관리자 - 복구할 파일 인덱스 (파일의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_restore_file_services(board_index, file_index, conn, current_user)

# 관리자 한 게시판에 soft delete한 모든 파일 복구
@router.post(
    "/boards/{board_index}/files/restore",
    dependencies = [Depends(RateLimiter(times = 30, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[관리자] 파일 일괄 복구",
    description = """
    특정 게시판에 삭제 처리된 모든 파일 일괄 복구

    - 관리자는 삭제처리된지 90일이내의 파일들만 복구 가능
    - 권한 상관없이 복구 가능
    - 관리자만 접근 가능
    """
)
async def admin_restore_all_files(
    board_index: int = Path(..., gt = 0, description = "관리자 - 파일 일괄 복구할 게시판의 인덱스 (게시판의 인덱스는 1이상이여야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await admin_restore_all_files_services(board_index, conn, current_user)