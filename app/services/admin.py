import json

from asyncpg import Connection
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from app.schemas.common import CommonResponse
from app.schemas.admin import CreateNotice, DeleteOption, FileDeleteOption
from app.core.config import settings
from app.models.audit_log import insert_audit_log

from app.models.user import (
    get_user_id_pw, check_undeleted_user_exist, check_user_exist,
    pull_user_info, get_deleted_user_info, soft_delete_user,
    hard_delete_user, restore_user_data
)

from app.models.boards import (
    check_boards_owner, check_undeleted_boards_exist, check_boards_exist,
    insert_boards_db, soft_delete_board, hard_delete_board,
    check_deleted_boards_owner, restore_board, update_total_board_fsize,
    recalculate_all_user_boards_total_fsize, update_all_user_boards_total_fsize
)

from app.models.files import (
    get_total_fsize, get_softDelete_fsize, soft_delete_all_board_files,
    restore_all_board_files, check_board_deleted_files_exist, get_total_softDelete_fsize,
    get_file_belong, check_undeleted_files_exist, check_files_exist,
    get_deleted_file_info, admin_get_restorable_fsize, admin_restore_all_restorable_files,
    restore_cascade_board_files, restore_one_file, restore_all_user_files,
    soft_delete_one_file, soft_delete_all_user_files, hard_delete_one_file,
    hard_delete_all_board_files, hard_delete_all_user_files,
    check_restore_exceeding_boards_total_fsize
)

from app.models.admin import (
    admin_get_all_users, admin_get_specific_user, admin_get_specific_board,
    admin_ban, admin_unban,
    admin_get_banCount, admin_user_4ban_settings
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

    # 반복되는 유저 정보
    first_row = dict(user_data[0])
    user_info = {
        "id": first_row.get("id"),
        "user_index": first_row.get("user_index"),
        "role": first_row.get("role"),
        "status": first_row.get("status"),
        "reg_date": first_row.get("user_reg_date"),
        "deleted_at": first_row.get("user_deleted_at"),
        "deleted_by": first_row.get("user_deleted_by")
    }

    # 게시판 정보
    boards_list = []
    for row in user_data:
        row_dict = dict(row)
        if row_dict.get("board_index") is not None:
            boards_list.append({
                "board_index": row_dict.get("board_index"),
                "title": row_dict.get("title"),
                "content": row_dict.get("content"),
                "reg_date": row_dict.get("board_reg_date"),
                "update_date": row_dict.get("board_update_date"),
                "total_file_size": row_dict.get("total_file_size"),
                "deleted_at": row_dict.get("board_deleted_at"),
                "deleted_by": row_dict.get("board_deleted_by")
            })

    formatted_data = {
        "user_info": user_info,
        "boards": boards_list
    }

    return CommonResponse(
        message = f"관리자 권한으로 {user_index}번 유저를 상세 조회 합니다.",
        data = formatted_data
    )

# 관리자 특정 게시판 상세 조회
async def admin_get_specific_board_services(board_index: int, conn: Connection):
    
    board_belong = await check_boards_owner(conn, board_index)

    if board_belong is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"해당 {board_index}번 게시판이 존재하지 않습니다."
        )
    
    board_info = await admin_get_specific_board(conn, board_index)

    if not board_info:
        return CommonResponse(message=f"{board_index}번 게시판 상세 조회", data={})

    # 읽기 전용 Record를 마음대로 수정 가능한 파이썬 dict로 변환
    board_dict = dict(board_info)

    # 변환된 board_dict의 값을 파싱해서 덮어씌움
    if board_dict.get('files') and isinstance(board_dict['files'], str):
        board_dict['files'] = json.loads(board_dict['files'])

    return CommonResponse(
        message = f"{board_index}번 게시판의 상세 정보를 조회합니다.",
        data = board_dict 
    )


    return CommonResponse(
        message = f"{board_index}번 게시판의 상세 정보를 조회합니다.",
        data = dict(board_info) if board_info else {}
    )

# 관리자 공지사항 작성
async def admin_register_notice_services(data: CreateNotice, conn: Connection, current_user: dict):

    async with conn.transaction():
        registered_notice_index = await insert_boards_db(
            conn = conn,
            title = data.title,
            content = data.content,
            category = 'NOTICE',
            user_index = current_user['index']
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

# 관리자 - 유저 블랙리스트 ban 처리
async def admin_user_ban_services(user_index: int, conn: Connection, current_user: dict):

    ban_count = await admin_get_banCount(conn, user_index)

    if ban_count is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "해당 유저를 찾을 수 없습니다."
        )

    if ban_count == 3: # 이미 ban_count == 3 이면 경고 끝 삭제 (ban_count++ -> 4)
        async with conn.transaction():
            await soft_delete_user(conn, "ADMIN_SCHEDULED", user_index) # soft delete 처리 (스케줄러) - ADMIN_SCHEDULER
            await admin_user_4ban_settings(conn, user_index)
            await insert_audit_log(
                conn = conn,
                action = "DELETE (ADMIN/SOFT)",
                target_type = "USER",
                target_index = user_index,
                actor_user_index = current_user['index'],
                actor_user_id = current_user['id'],
                detail = {
                    "reason": f"누적 경고 4회로 관리자 권한으로 {user_index}번 사용자를 삭제 처리",
                    "total_ban_count": 4
                }
            )
        return CommonResponse(message = f"{user_index}번 유저가 누적 경고 4회로 삭제처리 되었습니다.")
    
    if ban_count > 3:
        return CommonResponse(
            success = False,
            message = "누적 경고 4회로 이미 삭제처리된 유저입니다."
        )
        
    if ban_count == 0: ban_days = 1
    elif ban_count == 1: ban_days = 3
    else: ban_days = 5

    async with conn.transaction():
        await admin_ban(conn, user_index, ban_days)
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
        return CommonResponse(message = f"{user_index}번 유저가 {ban_days}일 만큼 이용 정지처리 되었습니다.")

# 관리자 - 유저 블랙리스트 unban 처리
async def admin_user_unban_services(user_index: int, conn: Connection, current_user: dict):

    ban_count = await admin_get_banCount(conn, user_index)

    if ban_count is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 유저를 찾을 수 없습니다."
        )
    
    if ban_count == 0:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "해당 유저는 ban 상태가 아니며 ban 횟수는 0 입니다."
        )

    async with conn.transaction():
        await admin_unban(conn, user_index) # ban_count, ban_end_at, status 초기화 (0, NULL, ACTIVE)

        await insert_audit_log(
            conn = conn,
            action = "UNBAN (ADMIN)",
            target_type = "USER",
            target_index = user_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 {user_index}번 유저의 ban을 초기화"
            }
        )

    return CommonResponse(message = f"{user_index}번 유저의 ban 횟수가 초기화되어 정상활동이 가능합니다.")

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
            await soft_delete_all_user_files(conn, "USER_CASCADE", user_index)
            await update_all_user_boards_total_fsize(conn, 0, user_index)
            action_type = "DELETE (ADMIN/SCHEDULED)"

        elif delete_option == DeleteOption.RETAIN:
            target_index = await check_undeleted_user_exist(conn, user_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 유저를 찾을 수 없습니다."
                )
            await soft_delete_user(conn, "ADMIN_RETAIN", user_index)
            await soft_delete_all_user_files(conn, "USER_CASCADE", user_index)
            await update_all_user_boards_total_fsize(conn, 0, user_index)
            action_type = "DELETE (ADMIN/RETAIN)"
        else: # IMMEDIATE
            target_index = await check_user_exist(conn, user_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 유저를 찾을 수 없습니다."
                )
            await hard_delete_user(conn, user_index) # user 데이터를 즉시 익명화 처리
            await hard_delete_all_user_files(conn, user_index) # 해당 user의 모든 파일 데이터를 즉시 hard delete
            await update_all_user_boards_total_fsize(conn, 0, user_index) # 해당 user의 모든 게시판의 용량을 0으로 업데이트
            action_type = "DELETE (ADMIN/IMMEDIATE)"

        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_type = "USER",
            target_index = user_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 유저를 삭제합니다. ({action_type})"
            }
        )

    return CommonResponse(message = f"관리자 권한으로 {user_index}번 유저를 삭제합니다. ({action_type})")


# 관리자 - 통합 게시판 삭제
async def admin_delete_boards_services(board_index: int, delete_option: DeleteOption, conn: Connection, current_user: dict):

    async with conn.transaction():
        if delete_option == DeleteOption.SCHEDULED: # 게시판, 파일 데이터 모두 100일 후 hard delete
            target_index = await check_undeleted_boards_exist(conn, board_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 게시판을 찾을 수 없습니다."
                )
            await soft_delete_board(conn, "ADMIN_SCHEDULED", board_index)
            await soft_delete_all_board_files(conn, "BOARD_CASCADE", board_index)
            action_type = "DELETE (ADMIN/SCHEDULED)"

        elif delete_option == DeleteOption.RETAIN: # 게시판 자체는 영구적으로 hard delete x / 파일 데이터만 100일 후 hard delete
            target_index = await check_undeleted_boards_exist(conn, board_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 게시판을 찾을 수 없습니다."
                )
            await soft_delete_board(conn, "ADMIN_RETAIN", board_index)
            await soft_delete_all_board_files(conn, "BOARD_CASCADE", board_index)
            action_type = "DELETE (ADMIN/RETAIN)"

        else: # IMMEDIATE: 게시판, 파일 모두 즉시 hard delete
            target_index = await check_boards_exist(conn, board_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 게시판을 찾을 수 없습니다."
                )
            await hard_delete_all_board_files(conn, board_index)
            await hard_delete_board(conn, board_index)
            action_type = "DELETE (ADMIN/IMMEDIATE)"
        
        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_type = "BOARDS",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 게시판을 삭제합니다. ({action_type})"
            }
        )

    return CommonResponse(message = f"관리자 권한으로 {board_index}번 게시판을 삭제합니다. ({action_type})")

# 관리자 - 통합 단일 파일 삭제 (용량 재계산 필요 / 파일은 RETAIN, SCHEDULED 옵션 동일) - SCHEDULED, IMMEDIATE 
async def admin_delete_one_file_services(file_index: int, delete_option: FileDeleteOption, conn: Connection, current_user: dict):

    # 파일 인덱스를 통해서 해당 파일이 속한 board_index를 가져온다.
    board_index = await get_file_belong(conn, file_index)

    async with conn.transaction():
        if delete_option == FileDeleteOption.SCHEDULED:
            target_index = await check_undeleted_files_exist(conn, file_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 파일이 존재하지 않습니다."
                )
            await soft_delete_one_file(conn, "ADMIN_SCHEDULED", file_index)
            new_total_fsize = await get_total_fsize(conn, board_index)
            await update_total_board_fsize(conn, new_total_fsize, board_index)
            action_type = "DELETE (ADMIN/SCHEDULED)"
        elif delete_option == FileDeleteOption.IMMEDIATE:
            target_index = await check_files_exist(conn, file_index)
            if target_index is None:
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "해당 파일이 존재하지 않습니다."
                )
            await hard_delete_one_file(conn, file_index)
            new_total_fsize = await get_total_fsize(conn, board_index)
            await update_total_board_fsize(conn, new_total_fsize, board_index)
            action_type = "DELETE (ADMIN/IMMEDIATE)"
        
        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_type = "FILE",
            target_index = file_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": f"관리자 권한으로 단일 파일을 삭제합니다. ({action_type})",
                "new_board_size": int(new_total_fsize)
            }
        )
    
    return CommonResponse(message = f"관리자 권한으로 단일 파일 {file_index}번 파일을 삭제합니다. ({action_type})")

# 관리자 - 통합 특정 게시판의 전체 파일들 일괄 삭제 (파일은 RETAIN, SCHEDULED 옵션 동일함) - SCHEDULED, IMMEDIATE
async def admin_delete_all_board_files_services(board_index: int, delete_option: FileDeleteOption, conn: Connection, current_user: dict):

    async with conn.transaction():
        target_index = await check_boards_exist(conn, board_index) # 삭제처리와 무관하게 특정 게시판이 전체 게시판 리스트에 존재하는지 확인

        if target_index is None:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = f"{board_index}번 게시판이 존재하지 않습니다."
            )
        
        if delete_option == FileDeleteOption.SCHEDULED:
            await soft_delete_all_board_files(conn, "ADMIN_SCHEDULED", board_index)
            action_type = "DELETE (ADMIN / SCHEDULED)"
        elif delete_option == FileDeleteOption.IMMEDIATE:
            await hard_delete_all_board_files(conn, board_index)
            action_type = "DELETE (ADMIN / IMMEDIATE)"
        
        await insert_audit_log(
            conn = conn,
            action = action_type,
            target_type = "FILES",
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
            detail = f"요청하신 {user_index}번 유저는 존재하지 않거나, 복구 대상(삭제 상태)이 아닙니다."
        )
    
    time_diff = datetime.now(timezone.utc) - check_user['deleted_at'].replace(tzinfo = timezone.utc)

    if time_diff > timedelta(days = 90):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "삭제 처리를 한지 90일이 경과하여 유저를 복구 할 수 없습니다."
        )

    exceeding_boards = await check_restore_exceeding_boards_total_fsize(conn, user_index, allow_max_total_fsize)

    if exceeding_boards:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"유저 데이터 복구시 {exceeding_boards[board_index]}번 게시판은 업로드 가능한 파일 총 용량인 25MB를 초과합니다."
        )

    # 복구 로직 - 유저를 복구하면 복구 가능한 (삭제처리된지 90일이 안지난 데이터) 해당 유저의 파일 데이터도 같이 복구
    async with conn.transaction():
        await restore_user_data(conn, check_user['id']) # 유저 데이터 복구
        await restore_all_user_files(conn, user_index, 90) # 해당 유저의 복구 가능한 파일 복구 (USER_CASCADE 만 복구)
        await recalculate_all_user_boards_total_fsize(conn, user_index) # 용량 재계산 및 용량 업데이트

        await insert_audit_log(
            conn = conn,
            action = "RESTORE (ADMIN)",
            target_type = "USER",
            target_index = user_index,
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

    restorable_fsize = await admin_get_restorable_fsize(conn, board_index)

    if restorable_fsize > allow_max_total_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail = f"복구를 진행할 시, 한 게시판에 업로드 할 수 있는 총 파일 용량을 초과합니다. (최대 허용: {(allow_max_total_fsize / (1024 * 1024)):.2f}MB, 복구 가능 파일: {(restorable_fsize / (1024 * 1024)):.2f}MB)"
        )

    # 복구 및 용량 재게산 로직
    async with conn.transaction():
        await restore_board(conn, board_index)
        await restore_cascade_board_files(conn, board_index, 90) # 게시판 삭제로 인해서 삭제된 파일들만 복구 - BOARD_CASCADE
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_board_fsize(conn, new_total_fsize, board_index)
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


# 관리자 삭제처리된 단일 파일복구
async def admin_restore_file_services(file_index: int, conn: Connection, current_user: dict):

    check_file = await get_deleted_file_info(conn, file_index)

    if check_file is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{file_index}번 파일은 존재하지 않거나 복구 가능한 상태(삭제 상태)가 아닙니다."
        )
    
    time_diff = datetime.now(timezone.utc) - check_file['deleted_at'].replace(tzinfo = timezone.utc)
    
    if time_diff > timedelta(days = 90):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "삭제 처리를 한지 90일이 경과하여 파일을 복구 할 수 없습니다."
        )

    board_index = await get_file_belong(conn, file_index)

    # 해당 파일이 속한 게시판의 용량 재계산 로직 필요
    async with conn.transaction():
        await restore_one_file(conn, file_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_board_fsize(conn, new_total_fsize, board_index)
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

    board_belong = await check_boards_owner(conn, board_index)

    if board_belong is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{board_index}번 게시판이 존재하지 않습니다."
        )
    
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

    # ADMIN 권한으로 특정 게시판에서 복구 가능한 파일 용량의 총 합 (복구는 삭제처리된지 90일이내만 / 삭제처리 100일 후 스케줄러 hard delete)
    admin_restorable_fsize = await admin_get_restorable_fsize(conn, board_index)
    admin_restorable_fsize = admin_restorable_fsize or 0

    if admin_restorable_fsize == 0:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 게시판에는 복구 가능한 파일이 존재하지 않습니다."
        )

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
        await update_total_board_fsize(conn, new_total_fsize, board_index)
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