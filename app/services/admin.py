from asyncpg import Connection
from fastapi import HTTPException, status
from app.schemas.common import CommonResponse
from app.models.user import pull_user_info
from app.models.files import get_total_fsize, get_softDelete_fsize, update_total_fsize
from app.schemas.admin import CreateNotice
from app.models.admin import (
    admin_get_all_users,
    admin_get_specific_user,
    admin_get_specific_board,
    admin_check_board_belong,
    admin_get_file_board_index
    admin_register_notice,
    admin_blacklist,
    admin_get_banCount,
    admin_delete_user,
    admin_soft_delete_board,
    admin_soft_delete_file,
    admin_hard_delete_board,
    admin_hard_delete_file,
    admin_check_soft_delete_board,
    admin_check_soft_delete_file,
    admin_check_hard_delete_board,
    admin_check_hard_delete_file,
    admin_check_restore_board,
    admin_check_restore_file,
    admin_check_file_belong,
    admin_restore_all_files
)

# 관리자 전체 유저 목록 조회
async def admin_get_all_users_services(conn: Connection):

    users = await admin_get_all_users(conn)
    user_list = [dict(u) for u in users] if users else []

    return CommonResponse(
        message = "관리자 권한으로 전체 유저 목록을 조회합니다.",
        data = {"users": user_list}
    )

# 관리자 전체 유저 중 특정 유저 상세 조회 (페이지네이션 포함)
async def admin_get_specific_user_services(user_index: int, conn: Connection):

    user_data = await admin_get_specific_user(conn, user_index, limit=50, offset=0)

    if not user_data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 유저 또는 해당 유저가 작성한 게시글을 찾을 수 없습니다."
        )
    
    specific_user_data = [dict(record) for record in user_data] if user_data else []

    return CommonResponse(
        message = f"관리자 권한으로 {user_index}번 유저를 상세 조회 합니다.",
        data = {"specific_user": specific_user_data}
    )

# 관리자 특정 게시판 상세 조회
async def admin_get_specific_board_services(user_index: int, board_index: int, conn: Connection):

    board_belong = await admin_check_board_belong(conn, board_index)

    if board_belong != user_index:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "해당 게시판은 요청하신 유저가 작성한 글이 아닙니다."
        )
    
    board_info = await admin_get_specific_board(conn, board_index)

    return CommonResponse(
        message = f"{board_index}번 게시판의 상세 정보를 조회합니다.",
        data = dict(board_info) if board_info else {}
    )
    
# 관리자 공지사항 작성
async def admin_register_notice_services(data: CreateNotice, conn: Connection, current_user: dict):

    registerd_notice_index = await admin_register_notice(conn, data.title, data.content, 'NOTICE', current_user['index'])

    return CommonResponse(
        message = "공지사항이 등록되었습니다.",
        data = f"notice_index: {registerd_notice_index}"
    )

# 관리자 유저 블랙리스트 관리
async def admin_user_blacklist_services(user_index: int, conn: Connection):

    ban_count = await admin_get_banCount(conn, user_index)

    if ban_count is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "해당 유저를 찾을 수 없습니다."
        )
    
    if ban_count >= 3:
        await admin_delete_user(conn, user_index)
        return CommonResponse(
            success = False,
            message = "이미 삭제처리된 유저입니다."
        )
    
    if ban_count == 0: ban_days = 1
    elif ban_count == 1: ban_days = 3
    else: ban_days = 5
 
    # 특정 유저를 블랙리스트 처리
    await admin_blacklist(conn, user_index, ban_days)

    return CommonResponse(message = f"해당 유저가 {ban_days}일 만큼 이용 정지처리 되었습니다.")

# 관리자 게시판 삭제 (soft delete)
async def admin_soft_delete_board_services(board_index: int, conn: Connection):

    target_index = await admin_check_soft_delete_board(conn, board_index)

    if target_index is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 게시판을 찾을 수 없습니다."
        )
    
    await admin_soft_delete_board(conn, board_index)

    return CommonResponse(message = f"{board_index}번의 게시판이 삭제 처리되었습니다.")


# 관리자가 직접 게시판 hard delete (hard delete 경우는 용량 재계산 로직 필요 x)
async def admin_IMT_hard_delete_board_services(board_index: int, conn: Connection):

    target_index = await admin_check_hard_delete_board(conn, board_index)

    if target_index is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 게시판을 찾을 수 없습니다"
        )
    
    await admin_hard_delete_board(conn, board_index)

    return CommonResponse(message = f"{board_index}번의 게시판이 영구적으로 삭제되었습니다.")

# 관리자 파일 삭제 (soft delete)
async def admin_soft_delete_file_services(file_index: int, conn: Connection):

    target_index = await admin_check_soft_delete_file(conn, file_index)

    if target_index is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 파일을 찾을 수 없습니다."
        )
    
    board_index = await admin_get_file_board_index(conn, file_index)

    async with conn.transaction():
        await admin_soft_delete_file(conn, file_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_fsize(conn, new_total_fsize, board_index)

    return CommonResponse(message = f"{file_index}번의 파일이 삭제 처리되었습니다.")

# 관리자가 직접 파일 hard delete (hard delete 경우는 용량 재계산 로직 필요 x)
async def admin_IMT_hard_delete_file_services(file_index: int, conn: Connection):

    target_index = await admin_check_hard_delete_file(conn, file_index)

    if target_index is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 파일을 찾을 수 없습니다."
        )
   
    await admin_hard_delete_file(conn, file_index)

    return CommonResponse(message = f"{file_index}번의 파일이 영구적으로 삭제되었습니다.")

# 관리자 삭제처리된 게시판 복구
async def admin_restore_board_services(board_index: int, conn: Connection):

    check_boards = await admin_check_restore_board(conn, board_index)

    if check_boards is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"요청하신 {board_index}번 게시판이 존재하지 않거나, 복구 대상(삭제 상태)이 아닙니다."
        )
    
    # 용량 재게산 로직
    async with conn.transaction():
        await admin_restore_board(conn, board_index)
        await admin_restore_all_files(conn, board_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_fsize(conn, new_total_fsize, board_index)
    
    return CommonResponse(message = f"{board_index}번의 게시판이 복구되었습니다.")


# 관리자 삭제처리된 파일복구
async def admin_restore_file_services(board_index: int, file_index: int, conn: Connection):

    check_file_belong = await admin_check_file_belong(conn, board_index, file_index)

    if check_file_belong is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "복구하려는 파일의 인덱스가 입력하신 게시판 인덱스에 속해있지 않습니다."
        )

    check_files = await admin_check_restore_file(conn, file_index)

    if check_files is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"요청하신 {file_index}번 파일이 존재하지 않거나, 복구 대상(삭제 처리)이 아닙니다."
        )
    
    # 해당 파일이 속한 게시판의 용량 재계산 로직 필요
    async with conn.transaction():
        await admin_restore_file(conn, file_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_fsize(conn, new_total_fsize, board_index)

    return CommonResponse(message = f"{file_index}번의 파일이 복구되었습니다.")