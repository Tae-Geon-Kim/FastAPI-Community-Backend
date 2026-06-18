import random
import aiosmtplib

from email.mime.text import MIMEText
from asyncpg import Connection
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta

from app.models.user import (
    insert_user_basic_info, id_duplicate, email_duplicate, pull_user_info, 
    get_user_id_pw, soft_delete_user, delete_soft_deleted_user, userId_modify, 
    userPw_modify, restore_user_data, get_deleted_user_info, update_is_verified_true
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

from app.schemas.user import (
    UserRegister, EmailVerification, UserLogin,
    UserId, UserPw, ModiId, ModiPw, UserInfo
)

from app.schemas.common import CommonResponse

from app.core.security import hash_password, verify_password
from app.core.config import settings, smtp_settings
from app.services.auth import restore_login

allow_max_total_fsize = settings.FILE_TOTAL_MAX_SIZE

sender_email = smtp_settings.SMTP_SENDER
sender_password = smtp_settings.SMTP_PASSWORD
smtp_server = smtp_settings.SMTP_SERVER
smtp_port = smtp_settings.SMTP_PORT

# 사용자 회원가입 (사용자 비밀번호 검사 및 이메일 검증 - 인증번호)
async def register_user_services(data: UserRegister, conn: Connection, redis_client):

    verified_key = f"email_verified:{data.email}"
    is_verified = await redis_client.get(verified_key)

    if not is_verified:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "이메일 인증이 완료되지 않았습니다."
        )
    
    # 위의 예외처리가 필요한 이유 - API 호출 로직 순서
    # 유저가 이메일을 입력하고 '인증번호 받기' 버튼: send-verification-code API
    # 유저가 인증 코드를 입력하고 '인증번호 확인' 버튼: check-verification-code API
    # 여기까지 완료하면 Redis에 email_verified:test@test.com 이라고 하는 30분 유지되는 표식
    # 유저가 나머지 아이디, 비밀번호 등의 정보를 입력하고 최종 회원가입 버튼: register API (이미 인증번호는 완료한 상태여야한다.)

    # 아이디 중복, 빈 문자열 검사
    await user_id_duplicate_services(conn, data.id)

    # 이메일 중복 검사
    await user_email_duplicate_services(conn, data.email)

    # 비밀번호 해싱 처리 후 저장
    data.password = hash_password(data.password)
    await insert_user_basic_info(conn, data.id, data.password, data.name, data.email)

    await redis_client.delete(verified_key)

    # is_verified 값을 true로 업데이트
    await update_is_verified_true(conn, data.email)  

    return CommonResponse(message = "회원가입이 성공적으로 완료되었습니다.")

# 신규 회원의 아이디 중복 검사
async def user_id_duplicate_services(conn: Connection, user_id: str):

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, user_id):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "이미 사용중인 아이디입니다."
        )

    return CommonResponse(message = "사용 가능한 아이디입니다!")

# 신규 회원의 이메일 중복 검사
async def user_email_duplicate_services(conn: Connection, user_email: str):

    # 이메일이 중복되는 경우
    if await email_duplicate(conn, user_email):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "이미 사용중인 이메일입니다."
        )
    
    return CommonResponse(message = "사용 가능한 이메일입니다!")

# 이메일 인증번호 전송 
async def send_verification_email_services(receiver_email:str, conn: Connection, redis_client):

    # 6자리 난수 생성 (0 ~999999)
    verification_code = f"{random.randint(0, 999999):06d}"

    # Redis에 저장
    # {user_email:인증번호} {key:value} 형태로 redis에 저장
    redis_key = f"email_auth:{receiver_email}"
    await redis_client.setex(redis_key, 300, verification_code)

    # 이메일을 보내는 코드
    msg_text = f"인증번호는 {verification_code}입니다. 5분 이내에 입력해주세요."
    msg = MIMEText(msg_text, 'plain', 'utf-8')

    msg['Subject'] = "[FastApi-Community-Backend] 인증번호"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # 비동기 메일 발송
    try:
        await aiosmtplib.send(
            msg,
            hostname = smtp_server,
            port = smtp_port,
            username = sender_email,
            password = sender_password
        )
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"이메일을 보내는 과정에서 에러가 발생하였습니다. : {str(e)}"
        )

# 인증번호 검증
async def check_verification_code_services(data: EmailVerification, conn: Connection, redis_client):

    redis_key = f"email_auth:{data.email}"
    verification_code = await redis_client.get(redis_key)

    # redis에서 값이 존재하지 않을 때
    if not verification_code:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "인증번호가 만료되었거나 발송되지 않았습니다."
        )
    
    if isinstance(verification_code, bytes):
        verification_code = verification_code.decode('utf-8')
    
    if verification_code != data.code:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "일치하지 않는 인증번호입니다."
        )

    await redis_client.delete(redis_key)
    verified_key = f"email_verified:{data.email}"
    await redis_client.setex(verified_key, 1800, "true")

    return CommonResponse(message = "인증이 완료되었습니다.")

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

    if not verify_password(data.password, user_info['password']):
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
    
    if not verify_password(data.password, user_info['password']):
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
    
    if not verify_password(data.password, user_info['password']):
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
            detail = f"유저 데이터 복구시 {exceeding_boards['board_index']}번 게시판은 업로드 가능한 파일 총 용량인 25MB를 초과합니다."
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