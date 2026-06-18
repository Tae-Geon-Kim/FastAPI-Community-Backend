from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from fastapi_limiter.depends import RateLimiter
from asyncpg import Connection

from app.schemas.user import (
    UserRegister, UserLogin, UserId, UserPw, 
    ModiId, ModiPw, EmailRequest, EmailVerification
)

from app.schemas.common import CommonResponse

from app.services.user import (
    register_user_services, user_id_duplicate_services,
    user_email_duplicate_services, send_verification_email_services,
    check_verification_code_services, user_info_services, user_withdraw_services, 
    userId_modify_services, userPw_modify_services, restore_user_services,
)

from app.db.database import get_db
from app.db.redis_config import get_redis, redis_db
from app.core.security import get_current_user

router = APIRouter()

# 신규 회원가입
@router.post(
    "",
    dependencies = [Depends(RateLimiter(times = 1, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_201_CREATED,
    summary = "[유저] 신규 회원가입",
    description = """
    사용자에게 아이디와 비밀번호를 입력받아 최종적으로 신규 User 가입을 시킨다.

    - 허용되는 id 형식: 영문자, 숫자가 무조건 포함된 5 ~ 30자 (선택적 특수문자 사용 가능: $!%*#?&._-)
    - 허용되는 password 형식: 영문자, 숫자, 특수문자가 무조건 포함된 8 ~ 30자 (허용 특수문자: @$!%*#?&._-)
    - 허용되는 name 형식: 한글 혹은 영어로 이루어진 2 ~ 50자
    - 허용되는 email 형식: user@exaplme.com의 형태
    """
)
async def register_user(
    data: UserRegister,
    redis_client = Depends(get_redis),
    conn: Connection = Depends(get_db)
):
    return await register_user_services(data, conn, redis_client)

# 신규 회원의 아이디 중복 검사
@router.post(
    "/check-id",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 신규 아이디 중복 확인",
    description = """
    신규 유저 아이디의 중복 검사
    
    - 신규 유저 아이디의 중복 확인 및 유효성 검증
    - 허용되는 id 형식: 영문자, 숫자가 무조건 포함된 5 ~ 30자 (특수문자 허용)
    - 허용되는 특수문자: $!%*#?&._-
    """
)
async def check_user_id(
    data: UserId,
    conn: Connection = Depends(get_db)
):
    return await user_id_duplicate_services(conn, data.id)

# 신규 회원의 이메일 중복 검사
@router.post(
    "/check-email",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 10))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 신규 회원의 이메일 중복 확인",
    description = """
    신규 유저 이메일의 중복 검사

    - 신규 유저 이메일의 중복 확인 및 유효성 검증
    - 허용되는 이메일 형식: user@example.com
    """
)
async def check_user_email(
    data: EmailRequest,
    conn: Connection = Depends(get_db)
):
    return await user_email_duplicate_services(conn, data.email)

# 인증번호 생성 및 전송
@router.post(
    "/send-verification-code",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 인증 이메일 발송",
    description = """
    인증번호 이메일 전송

    - 인증번호는 6자리의 난수를 생성하여 유저의 이메일로 전송한다.
    - 인증번호의 유효시간은 5분이다. 
    """
)
async def send_verification_code(
    data: EmailRequest,
    redis_client = Depends(get_redis),
    conn: Connection = Depends(get_db)
):
    return await send_verification_email_services(data.email, conn, redis_client)

# 인증번호 검증
@router.post(
    "/check-verification_code",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 인증번호 검증",
    description = """
    이메일 인증번호 검증

    - 인증번호는 임의의 6자리 숫자이다.
    - 인증번호의 유효시간은 5분이다.
    """
)
async def check_verification_code(
    data: EmailVerification,
    redis_client = Depends(get_redis),
    conn: Connection = Depends(get_db)
):
    return await check_verification_code_services(data, conn, redis_client)


# 사용자 정보 조회
@router.get(
    "/me",
    dependencies = [Depends(RateLimiter(times = 20, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 정보 조회",
    description = """
    사용자 본인의 정보를 조회

    - 정보를 조회하기 위해서 로그인 필요
    """
)
async def get_my_info(
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await user_info_services(conn, current_user)

# 사용자 회원탈퇴
@router.delete(
    "/me",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 회원탈퇴",
    description = """
    사용자의 모든 회원정보 (사용자 정보, 업로드 파일)를 삭제 처리 (soft delete)

    - 삭제 처리를 진행하기 위해서 사용자 비밀번호 재입력 필요.
    - 사용자의 정보와 업로드된 파일만 삭제처리되며 게시판은 삭제처리되지 않는다.
    - 삭제처리 상태가 된지 7일이 지났으면 복구가 불가능하다.
    - 삭제처리가 된지 30일이 지나면 스케줄러를 통해서 사용자 데이터는 익명화처리 된다.
    - 삭제처리가 된지 100일이 지나면 스케줄러를 통해 사용자가 업로드한 파일 데이터는 hard delete 된다.
    """
)
async def withdraw_user(
    data: UserPw,
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await redis_db.delete(f"refresh:user:{current_user['index']}")

    return await user_withdraw_services(data, conn, current_user)

# 사용자 아이디 변경
@router.patch(
    "/me/id",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 아이디 변경",
    description = """
    사용자 아아디 변경

    - 변경하는 새로운 아이디 중복 검사 & 유효성 검증 필요
    - 제약조건: 영문자, 숫자가 무조건 포함된 5 ~ 30자 (특수문자 허용)
    - 허용되는 특수문자: $!%*#?&._-
    - 아이디를 변경하기 위해서 사용자 비밀번호 재입력 필요.
    """
)
async def update_my_id(
    data: ModiId,
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await userId_modify_services(data, conn, current_user)

# 사용자 비밀번호 변경
@router.patch(
    "/me/password",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 비밀번호 변경",
    description = """
    사용자 비밀번호 변경

    - 변경하는 새로운 비밀번호 유효성 검증 필요
    - 제약조건: 영문자, 숫자, 특수문자가 무조건 포함된 8 ~ 30자
    - 허용되는 특수문자: @$!%*#?&._-
    - 비밀번호를 변경하기 위헤서 사용자 비밀번호 재입력 필요.
    """
)
async def update_my_password(
    data: ModiPw,
    conn: Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await redis_db.delete(f"refresh:user:{current_user['index']}")

    return await userPw_modify_services(data, conn, current_user)


# 사용자 회원탈퇴 복구 - JWT 기반 로그인 
# JWT 기반 로그인 방식을 도입해도 여기서 로그인 부분은 기존의 아이디, 비밀번호 입력받는 방식을 사용해야한다.
# why? : 이미 삭제 처리된 데이터이기 때문에 삭제 처리가 된 순간 발급 된 (되어있던) access / refresh은 삭제된다.
@router.post(
    "/me/restore",
    dependencies = [Depends(RateLimiter(times = 5, seconds = 60))],
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 데이터 복구",
    description = """
    삭제 처리된 사용자 데이터를 복구
    
    - 복구를 하기 위해서 삭제 처리되었던 기존의 사용자 정보로 로그인 필요.
    - 복구시 삭제 처리된 모든 데이터 (사용자의 정보, 사용자가 업로드한 파일)가 복구된다.
    - 삭제된 파일을 복구할 때, 복구 후 한 게시판에 업로드 가능한 파일 총 용량 (25MB)을 초과하면 복구는 불가하다.
    - 복구는 삭제처리된지 7일이내에만 가능하다.
    """
)
async def restore_my_account(
    data: UserLogin,
    conn: Connection = Depends(get_db)
):
    return await restore_user_services(conn, data)