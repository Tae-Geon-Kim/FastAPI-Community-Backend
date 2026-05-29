from asyncpg import Connection
from fastapi import HTTPException, status
from app.schemas.common import CommonResponse
from app.schemas.admin import CreateNotice, DeleteOption
from app.core.config import settings
from app.models.audit_log import insert_audit_log

from app.models.user import (
    get_user_id_pw,
    check_undeleted_user_exist,
    check_user_exist,
    pull_user_info,
    get_deleted_user_info
)

from app.models.boards import (
    check_boards_owner,
    check_undeleted_boards_exist,
    check_boards_exist,
    insert_boards_db
)

from app.models.files import (
    get_total_fsize,
    get_softDelete_fsize,
    update_total_fsize,
    soft_delete_all_board_files,
    restore_all_board_files,
    check_board_deleted_files_exist,
    get_total_softDelete_fsize,
    get_file_belong,
    check_undeleted_files_exist,
    check_files_exist,
    get_deleted_file_info,
    admin_get_restorable_fsize,
    admin_restore_all_restorable_files,
    restore_cascade_board_files
)

from app.models.admin import (
    admin_get_all_users,
    admin_get_specific_user,
    admin_get_specific_board,
    admin_blacklist,
    admin_get_banCount
)

allow_max_total_fsize = settings.FILE_TOTAL_MAX_SIZE # 20MB

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

    board_belong = await check_boards_owner(conn, board_index)

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

    async with conn.transaction():
        registered_notice_index = await insert_boards_db(
            conn,
            data.title,
            data.content,
            'NOTICE',
            current_user['index']
        )
        await insert_audit_log(
            conn = conn,
            action = "CREATE",
            target_type = "ADMIN",
            target_index = registered_notice_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "title": data.title
            }
        )

    return CommonResponse(
        message = "공지사항이 등록되었습니다.",
        data = f"notice_index: {registered_notice_index}"
    )

# 관리자 유저 블랙리스트 관리
async def admin_user_blacklist_services(user_index: int, conn: Connection, current_user: dict):

    ban_count = await admin_get_banCount(conn, user_index)

    if ban_count is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "해당 유저를 찾을 수 없습니다."
        )

    if ban_count >= 3:
        async with conn.transaction():
            await soft_delete_user(conn, "ADMIN_SCHEDULED", user_index) # soft delete 처리 (스케줄러) - ADMIN_SCHEDULER
            await insert_audit_log(
                conn = conn,
                action = "DELETE (ADMIN/SOFT)",
                target_type = "USER",
                target_index = user_index,
                actor_user_index = current_user['index'],
                actor_user_id = current_user['id'],
                detail = {
                    "reason": "누적 경고 3회 이상으로 관리자 권한으로 해당 사용자를 삭제 처리",
                    "total_ban_count": ban_count
                }
            )
            return CommonResponse(
                success = False,
                message = "이미 삭제처리된 유저입니다."
            )

    if ban_count == 0: ban_days = 1
    elif ban_count == 1: ban_days = 3
    else: ban_days = 5

    async with conn.transaction():
        await admin_blacklist(conn, user_index, ban_days)
        await insert_audit_log(
            conn = conn,
            action = "BAN (ADMIN)",
            target_type = "USER",
            target_index = user_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 해당 유저를 {ban_days}만큼 이용정지",
                "ban_days": ban_days,
                "current_ban_count": ban_count + 1
            }
        )

    return CommonResponse(message = f"해당 유저가 {ban_days}일 만큼 이용 정지처리 되었습니다.")

# 관리자 - 통합 유저 삭제
async def admin_delete_user_services(user_index: int, delete_option: DeleteOption, conn: Connection, current_user: dict):

    async with conn.transaction():
        if delete_option == DeleteOption.SCHEDULED:
            target_index = await check_undeleted_user_exist(conn, user_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 유저를 찾을 수 없습니다."
                )
            await soft_delete_user(conn, "ADMIN_SCHEDULED", user_index)
            action_type = "DELETE (ADMIN/SCHEDULED)"
        elif delete_option == DeleteOption.RETAIN:
            target_index = await check_undeleted_user_exist(conn, user_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 유저를 찾을 수 없습니다."
                )
            await soft_delete_user(conn, "ADMIN_RETAIN", user_index)
            action_type = "DELETE (ADMIN/RETAIN)"
        else:
            target_index = await check_user_exist(conn, user_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 유저를 찾을 수 없습니다."
                )
            await hard_delete_user(conn, "ADMIN_IMMEDIATE", user_index)
            action_type = "DELETE (ADMIN/IMMEDIATE)"

        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_index = user_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 유저를 삭제합니다. ({action_type})"
            }
        )

    return CommonResponse(message = f"관리자 권한으로 {user_index}번 유저를 삭제합니다. ({action_type})")


# 관리자 - 통합 단일 게시판 삭제
async def admin_delete_board_services(board_index: int, delete_option: DeleteOption, conn: Connection, current_user: dict):

    async with conn.transaction():
        if delete_option == DeleteOption.SCHEDULED:
            target_index = await check_undeleted_boards_exist(conn, board_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 게시판을 찾을 수 없습니다."
                )
            await soft_delete_board(conn, "ADMIN_SCHEDULED", board_index)
            await soft_delete_all_board_files(conn, "BOARD_CASCADE", board_index)
            action_type = "DELETE (ADMIN/SCHEDULED)"

        elif delete_option == DeleteOption.RETAIN:
            target_index = await check_undeleted_boards_exist(conn, board_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 게시판을 찾을 수 없습니다."
                )
            await soft_delete_board(conn, "ADMIN_RETAIN", board_index)
            await soft_delete_all_board_files(conn, "BOARD_CASCADE", board_index)
            action_type = "DELETE (ADMIN/RETAIN)"

        else: # IMMEDIATE
            target_index = await check_boards_exist(conn, board_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 게시판을 찾을 수 없습니다."
                )
            await hard_delete_board(conn, board_index)
            await hard_delete_all_board_files(conn, board_index)
            action_type = "DELETE (ADMIN/IMMEDIATE)"
        
        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 게시판을 삭제합니다. ({action_type})"
            }
        )

    return CommonResponse(message = f"관리자 권한으로 {board_index}번 게시판을 삭제합니다. ({action_type})")

# 관리자 - 통합 단일 파일 삭제 (용량 재계산 필요)
async def admin_delete_one_file_services(file_index: int, delete_option: DeleteOption, conn: Connection, current_user: dict):

    # 파일 인덱스를 통해서 해당 파일이 속한 board_index를 가져온다.
    board_index = await get_file_belong(conn, file_index)

    async with conn.transaction():
        if delete_option == DeleteOption.SCHEDULED:
            target_index = await check_undeleted_files_exist(conn, file_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 파일이 존재하지 않습니다."
                )
            await soft_delete_one_file(conn, "ADMIN_SCHEDULED", file_index)
            new_total_fsize = await get_total_fsize(conn, board_index)
            await update_total_fsize(conn, new_total_fsize, board_index)
            action_type = "DELETE (ADMIN/SCHEDULED)"
        elif delete_option == DeleteOption.RETAIN:
            target_index = await check_undeleted_files_exist(conn, file_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 파일이 존재하지 않습니다."
                )
            await soft_delete_one_file(conn, "ADMIN_RETAIN", file_index)
            new_total_fsize = await get_total_fsize(conn, board_index)
            await update_total_fsize(conn, new_total_fsize, board_index)
            action_type = "DELETE (ADMIN/RETAIN)"
        else: # IMMEDIATE
            target_index = await check_files_exist(conn, file_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 파일이 존재하지 않습니다."
                )
            await hard_delete_one_file(conn, "ADMIN_IMMEDIATE", file_index)
            new_total_fsize = await get_total_fsize(conn, board_index)
            await update_total_fsize(conn, new_total_fsize, board_index)
            action_type = "DELETE (ADMIN/IMMEDIATE)"
        
        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_index = file_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 단일 파일을 삭제합니다. ({action_type})",
                "new_board_size": int(new_total_fsize)
            }
        )
    
    return CommonResponse(message = f"관리자 권한으로 단일 파일 {file_index}번 파일을 삭제합니다. ({action_type})")

# 관리자 - 통합 특정 게시판의 전체 파일들 일괄 삭제 (파일은 RETAIN 옵션이랑 SCHEDULED 옵션이 동일함)
async def admin_delete_all_board_files_services(board_index: int, delete_option: DeleteOption, conn: Connection, current_user: dict):

    async with conn.transaction():
        target_index = await check_boards_exist(conn, board_index)
        is_restore_file = await check_board_deleted_files_exist(conn, board_index)

        if target_index is None or is_restore_file is None:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = f"{board_index}번 게시판이 존재하지 않거나 해당 게시판에 복구 가능한 (삭제 상태) 파일이 존재하지 않습니다."
            )

        if delete_option == DeleteOption.SCHEDULED:
            await soft_delete_all_board_files(conn, "ADMIN_SCHEDULED", board_index)
            action_type = "DELETE (ADMIN / SCHEDULED)"
        elif delete_option == DeleteOption.RETAIN:
            await soft_delete_all_board_files(conn, "ADMIN_RETAIN", board_index)
            action_type = "DELETE (ADMIN / RETAIN)"
        else: # IMMEDIATE
            await hard_delete_all_board_files(conn, "ADMIN_IMMEDIATE", board_index)
            action_type = "DELETE (ADMIN/IMMEDIATE)"
        
        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 {board_index}번 게시판의 파일을 일괄 삭제합니다. ({action_type})",
                "new_board_size": 0
            }
        )
    
    return CommonResponse(message = f"관리자 권한으로 {board_index}번 게시판 파일을 일괄 삭제합니다. ({action_type})")

# 관리자 삭제처리된 유저 복구 
async def admin_restore_user_services(user_index: int, conn: Connection, current_user: dict):

    # 삭제 처리된 유저 중에서 해당 유저의 id, deleted_by, deleted_at 을 가져온다.
    check_user = await get_deleted_user_info(conn, user_index)

    if check_user is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"요청하신 {user_index}번 유저의 {check_user['id']}는 존재하지 않거나, 복구 대상(삭제 상태)이 아닙니다."
        )
    
    time_diff = datetime.now(timezone.utc) - check_user['deleted_at'].replace(tzinfo = timezone.utc)

    if time_diff > timedelta(days = 90):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "삭제 처리를 한지 90일이 경과하여 유저를 복구 할 수 없습니다."
        )
    
    # 복구 로직
    async with conn.transaction():
        await restore_user_data(conn, check_user['id'])
        await restore_all_user_boards(conn, user_index)
        await restore_all_user_files(conn, user_index)

        await insert_audit_log(
            conn = conn,
            action = "RESTORE (ADMIN)",
            target_type = "USER",
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자의 권한으로 삭제 처리된 {check_user['id']} 유저를 복구합니다."
            }
        )

    return CommonResponse(message = f"관리자 권한으로 삭제 처리된 {check_user['id']} 유저를 복구하였습니다.")

# 관리자 삭제처리된 게시판 복구
async def admin_restore_board_services(board_index: int, conn: Connection, current_user: dict):

    # 삭제 처리된 게시물 중에서 해당 게시물의 index, deleted_by, deleted_at 을 가져온다.
    check_boards = await check_deleted_boards_owner(conn, board_index)

    if check_boards is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"요청하신 {board_index}번 게시판이 존재하지 않거나, 복구 대상(삭제 상태)이 아닙니다."
        )
    
    time_diff = datetime.now(timezone.utc) - check_boards['deleted_at'].replace(tzinfo = timezone.utc)

    if time_diff > timedelta(days = 90):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "삭제 처리를 한지 90일이 경과하여 파일을 복구할 수 없습니다."
        )
    
    # 복구 및 용량 재게산 로직
    async with conn.transaction():
        await restore_board(conn, board_index)
        await restore_cascade_board_files(conn, board_index, 90) # 게시판 삭제로 인해서 삭제된 파일들만 복구 - BOARD_CASCADE
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "RESTORE (ADMIN)",
            target_type = "BOARD",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "관리자 권한으로 삭제 처리된 게시판 복구",
                "new_board_size": int(new_total_fsize)
            }
        )
    
    return CommonResponse(message = f"{board_index}번의 게시판이 복구되었습니다.")


# 관리자 삭제처리된 파일복구
async def admin_restore_file_services(board_index: int, file_index: int, conn: Connection, current_user: dict):

    check_file = await get_deleted_file_info(conn, board_index, file_index)

    if check_file is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"복구하려는 {file_index}번 파일이 입력하신 {board_index}번 게시판에 속해있지 않습니다."
        )
    
    time_diff = datetime.now(timezone.utc) - check_file['deleted_at'].replace(tzinfo = timezone.utc)
    
    if time_diff > timedelta(days = 90):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "삭제 처리를 한지 90일이 경과하여 파일을 복구 할 수 없습니다."
        )

    # 해당 파일이 속한 게시판의 용량 재계산 로직 필요
    async with conn.transaction():
        await restore_one_file(conn, file_index, board_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "RESTORE (ADMIN)",
            target_type = "FILES",
            target_index = file_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "관리자 권한으로 삭제처리된 단일 파일 복구",
                "new_board_size": int(new_total_fsize)
            }
        )

    return CommonResponse(message = f"{file_index}번의 파일이 복구되었습니다.")

# 관리자 특정 게시판에 삭제처리된 모든 파일 일괄 복구
async def admin_restore_all_files_services(board_index: int, conn: Connection, current_user: dict):
    
    # 해당 board_index 번 게시판에 삭제 처리된 파일이 존재하는지
    check_deleted_file = await check_board_deleted_files_exist(conn, board_index)

    if check_deleted_file is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{board_index}번 게시판에는 복구 가능한 파일이 존재하지 않습니다."
        )
    
    # 현재 파일 총 용량
    cur_total_fsize = await get_total_fsize(conn, board_index)
    cur_total_fsize = cur_total_fsize or 0

    # ADMIN 권한으로 특정 게시판에서 복구 가능한 파일 용량의 총 합 (삭제 처리된지 90일 이내)
    admin_restorable_fsize = await admin_get_restorable_fsize(conn, board_index)
    admin_restorable_fsize = admin_restorable_fsize or 0

    if cur_total_fsize + admin_restorable_fsize > allow_max_total_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
             detail = f"복구를 진행할 시, 한 게시판에 업로드 할 수 있는 총 파일 용량을 초과합니다. (최대: {(allow_max_total_fsize / (1024 * 1024)):.2f}MB 현재: {(cur_total_fsize / (1024 * 1024)):.2f}MB 복구: {(admin_restorable_fsize / (1024 * 1024)):.2f}MB)"   
        )
    
    # 파일 복구 & 용량 재계산
    async with conn.transaction():
        await admin_restore_all_restorable_files(conn, board_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        new_total_fsize = new_total_fsize or 0
        await update_total_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "RESTORE_ALL (ADMIN)",
            target_type = "BOARD_FILES",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 {board_index}번 게시판의 삭제 처리된 모든 파일을 일괄 복구",
                "new_board_size": int(new_total_fsize)
            }
        )
    
    return CommonResponse(message = f"{board_index}번 게시판의 삭제 처리된 모든 파일을 일괄 복구하였습니다.")