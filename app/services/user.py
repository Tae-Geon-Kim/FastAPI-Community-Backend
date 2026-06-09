from asyncpg import Connection
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta

from app.models.user import (
    push_id_pw, id_duplicate, pull_user_info, get_user_id_pw, 
    soft_delete_user, delete_soft_deleted_user, userId_modify, 
    userPw_modify, restore_user_data, get_deleted_user_info
)

from app.models.files import (
    soft_delete_all_user_files, delete_files, restore_all_user_files,
    check_restore_exceeding_boards_total_fsize
)

from app.models.boards import (
    soft_delete_all_user_boards, delete_boards, recalculate_all_user_boards_total_fsize,
    update_all_user_boards_total_fsize
)

from app.models.audit_log import insert_audit_log

from app.schemas.user import UserLogin, UserPw, ModiId, ModiPw, UserInfo
from app.schemas.common import CommonResponse

from app.core.security import hash_password, verify
from app.core.config import settings
from app.services.auth import restore_login

allow_max_total_fsize = settings.FILE_TOTAL_MAX_SIZE

# 사용자 회원가입 (사용자 비밀번호 검사)
async def register_user_services(conn: Connection, data: UserLogin):

    await user_name_services(conn, data.id)

    # 비밀번호 해싱 처리 후 저장
    data.password = hash_password(data.password)
    await push_id_pw(conn, data.id, data.password)

    return CommonResponse(message = "회원가입이 성공적으로 완료되었습니다.")

# 신규 회원 아이디 중복, 빈 문자열 검사
async def user_name_services(conn: Connection, user_id: str):

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, user_id):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "이미 사용중인 아이디입니다."
        )

    return CommonResponse(message = "사용 가능한 아이디입니다!")

# 사용자 정보조회
async def user_info_services(conn: Connection, current_user: dict):
    
    user_data = await pull_user_info(conn, current_user['index'])
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.

    if not user_data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "사용자 정보를 찾을 수 없거나 이미 탈퇴한 회원입니다."
        )

    return CommonResponse(
        message = "사용자 정보를 출력합니다.",
        data = UserInfo.model_validate(dict(user_data))
        # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
    )

# 시용자 회원탈퇴 - 사용자의 정보만 soft delete, 30 일 뒤 익명화 처리 / 게시판은 x / 파일은 즉시 soft delete (USER_CASCADE)
async def user_withdraw_services(data: UserPw, conn: Connection, current_user: dict):
    
    user_info = await get_user_id_pw(conn, current_user['index'])

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    async with conn.transaction():
        # soft delete
        await soft_delete_user(conn, "USER", current_user['index'])
        await soft_delete_all_user_files(conn, "USER_CASCADE", current_user['index'])
        await update_all_user_boards_total_fsize(conn, 0, current_user['index'])
        await insert_audit_log(
            conn = conn,
            action = "DELETE",
            target_type = "USER",
            target_index = current_user['index'],
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청에 의한 회원탈퇴 (soft delete)"
            }
        )
    
    return CommonResponse(message = f"{user_info['id']}님의 회원탈퇴가 성공적으로 처리되었습니다.")

# 영구 보관되는 데이터가 100일이 지난 경우 유저 데이터 익명화
async def anonymize_user(pool):
    async with pool.acquire() as conn:
        await delete_soft_deleted_user (conn)

# 유저 데이터 스케줄러 삭제 (ADMIN이 ADMIN_SCHEDULED 옵션으로 지운 데이터만 해당)
async def delete_user_perman(pool):

    async with pool.acquire() as conn:
        await delete_soft_deleted_user(conn)
        await delete_files(conn)

# 사용자 아이디 변경
async def userId_modify_services(data: ModiId, conn: Connection, current_user: dict):
    
    user_info = await get_user_id_pw(conn, current_user['index'])
    
    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, data.new_id):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "중복되는 아이디가 존재합니다."
        )
    
    async with conn.transaction():
        await userId_modify(conn, data.new_id, current_user['index'])
        await insert_audit_log(
            conn = conn,
            action = "MODIFY_ID",
            target_type = "USER",
            target_index = current_user['index'],
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "new_id": data.new_id
            }
        )

    return CommonResponse(
        message = f"{user_info['id']}님의 아이디가 {data.new_id}로 수정되었습니다."
    )

# 사용자 비밀번호 변경
async def userPw_modify_services(data: ModiPw, conn: Connection, current_user: dict):

    user_info = await get_user_id_pw(conn, current_user['index'])
    
    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    # 새로운 비밀번호 해싱처리
    data.new_password = hash_password(data.new_password)

    async with conn.transaction():
        await userPw_modify(conn, data.new_password, current_user['index'])
        await insert_audit_log(
            conn = conn,
            action = "MODIFY_PASSWORD",
            target_type = "USER",
            target_index = current_user['index'],
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청에 의한 비밀번호 변경"
            }
        )

    return CommonResponse(message = f"{user_info['id']}님의 비밀번호가 변경되었습니다.")

# 사용자 회원탈퇴 복구 (회원의 데이터 & 복구 가능한 회원의 파일 데이터)
async def restore_user_services(conn: Connection, data: UserLogin):

    # 삭제 처리된 유저의 로그인 (권한 확인) - user_num에는 유저의 index 값
    user_num = await restore_login(conn, data)

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )
    
    deleted_user_info = await get_deleted_user_info(conn, user_num)

    if deleted_user_info is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "삭제된 유저 정보를 찾을 수 없습니다."
        )

    time_diff = datetime.now(timezone.utc) - deleted_user_info['deleted_at'].replace(tzinfo = timezone.utc)

    if time_diff > timedelta(days = 7):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = f"삭제 처리를 한지 7일이 경과하여 {data.id} 유저를 복구 시킬 수 없습니다."
        )
    
    if deleted_user_info['deleted_by'] != "USER":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "관리자에 의해 삭제 처리된 유저 데이터를 일반 유저가 임의로 복구 시킬 수 없습니다."
        )

    # 유저 복구로 인해 파일 데이터들이 복구될 때 게시판의 허용 용량을 초과하는 게시판이 있는지 확인
    exceeding_boards = await check_restore_exceeding_boards_total_fsize(conn, user_num, allow_max_total_fsize)

    if exceeding_boards:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"유저 데이터 복구시 {exceeding_boards[board_index]}번 게시판은 업로드 가능한 파일 총 용량인 25MB를 초과합니다."
        )
    
    # 사용자 데이터 복구
    async with conn.transaction():
        await restore_user_data(conn, data.id) # 유저 데이터 복구
        await restore_all_user_files(conn, user_num, 30) # 해당 유저의 복구 가능한 파일 복구(USER_CASCADE 만 복구)
        await recalculate_all_user_boards_total_fsize(conn, user_num) # 용량 재계산 및 용량 업데이트
        
        await insert_audit_log(
            conn = conn,
            action = "RESTORE",
            target_type = "USER",
            target_index = user_num,
            actor_user_index = user_num,
            actor_user_id = data.id,
            detail = {
                "reason": "사용자 본인 요청에 의한 회원탈퇴 유저 아이디 복구"
            }
        )

    return CommonResponse(message = f"{data.id}님의 아이디가 복구되었습니다.") 