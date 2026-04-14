from fastapi import APIRouter, Depends, status
from asyncpg import Connection
from app.schemas.user import *
from app.services.user import *
from app.db.database import get_db
from app.core.security import verify_token

router = APIRouter()

# JWT 토큰 재발급
@router.post(
    "/refresh",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[인증] 만료된 JWT Access 토큰 재발급",
    description = """
    만료된 Access Token을 갱신하기 위해서 새로운 토큰을 발급받는다.
    - 로그인시 발급받았던 refresh token을 request body에 담아서 요청을 보내야 한다.
    """

)
async def refresh_access_token(
    data: TokenRefreshRequest,
    conn: Connection = Depends(get_db)
):
    return await refresh_access_token_services(conn, data)

# JWT 사용자 로그인
@router.post(
    "/login", 
    response_model = CommonResponse, 
    status_code = status.HTTP_200_OK,
    summary  = "[인증] 사용자 로그인", 
    description = """
    사용자의 아이디와 비밀번호를 검증하고 JWT Access, Refresh 토큰을 발급합니다.
     - id: 영문 소문자, 숫자를 포함한 5 ~ 20자
     - password: 영문자, 숫자, 특수문자를 포함한 8 ~ 16자
    """
)
async def token_login(
    data: UserLogin,
    conn: Connection = Depends(get_db)
):
    return await token_login_services(conn, data)


# 신규 회원가입 비밀번호를 입력했을 때, 해싱된 비밀번호 값을 DB에 저장
@router.post(
    "/uRegister",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 신규 회원가입",
    description = """
    사용자에게 아이디와 비밀번호를 입력받아 최종적으로 신규 User 가입을 완료
    - 허용되는 id 형식: 영문 소문자, 숫자를 포함한 5 ~ 20자
    - 허용되는 password 형식: 영문자, 숫자, 특수문자를 포함한 8 ~ 16자
    """
)
async def uregister(
    data: UserLogin,
    conn: Connection = Depends(get_db)
):
    return await user_pw_services(conn, data)

# 신규 회원의 아이디 중복, not null 검사
@router.post(
    "/uCheck",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 신규 아이디 중복 확인",
    description = """
    회원가입 전 아이디 사용 가능 여부를 확인.
     - 입력된 아이디가 DB에 존재하는 지 확인 (중복 확인)
     - 허용되는 id 형식: 영문 소문자, 숫자를 포함하는 5 ~ 20자 이내 (유효성 검증)
    """
)
async def ucheck(
    data: UserId,
    conn: Connection = Depends(get_db)
):
    return await user_name_services(conn, data)

# 사용자 정보 조회
@router.post(
    "/uInfo",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 정보 조회",
    description = """
    사용자 본인의 정보를 조회
    - 정보를 조회하기 위해서 로그인 필요
    """
)
async def uinfo(
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await user_info_services(conn, current_user_num)

# 사용자 회원탈퇴
@router.post(
    "/withdraw",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 회원탈퇴",
    description = """
    사용자의 모든 회원정보 (사용자 정보, 게시판, 게시판에 업로드된 파일)를 삭제 처리 (soft delete)
    - 삭제 처리를 진행하기 위해서 사용자 비밀번호 재입력 필요.
    """
)
async def withdraw(
    data: UserPw,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await user_withdraw_services(data, conn, current_user_num)

# 사용자 아이디 변경
@router.post(
    "/idModify",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 아이디 변경",
    description = """
    사용자 아아디 변경
    - 변경하는 새로운 아이디 중복 검사 & 유효성 검증 필요
    - 제약조건: 영문 소문자, 숫자 포함한 5 ~ 20자
    - 아이디를 변경하기 위해서 사용자 비밀번호 재입력 필요.
    """
)
async def id_modify(
    data: ModiId,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await userId_modify_services(data, conn, current_user_num)

# 사용자 비밀번호 변경
@router.post(
    "/pwModify",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 비밀번호 변경",
    description = """
    사용자 비밀번호 변경
    - 변경하는 새로운 비밀번호 유효성 검증 필요
    - 제약조건: 영문자, 숫자, 특수문자를 포함한 8 ~ 16자
    - 비밀번호를 변경하기 위헤서 사용자 비밀번호 재입력 필요.
    """
)
async def pw_modify(
    data: ModiPw,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(verify_token)
):
    return await userPw_modify_services(data, conn, current_user_num)


# 사용자 회원탈퇴 복구 - JWT 기반 로그인 
# JWT 기반 로그인 방식을 도입해도 여기서 로그인 부분은 기존의 아이디, 비밀번호 입력받는 방식을 사용해야한다.
# why? : 이미 삭제 처리된 데이터이기 때문에 삭제 처리가 된 순간 발급 된 (되어있던) access / refresh은 삭제된다.
@router.post(
    "/restoreUser",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[유저] 사용자 데이터 복구",
    description = """
    삭제 처리된 사용자 데이터를 복구
    - 복구를 하기 위해서 삭제 처리되었던 기존의 사용자 정보로 로그인 필요.
    - 복구시 삭제 처리된 모든 데이터 (사용자 정보, 게시판 정보, 해당 게시판에 업로드된 파일 정보)가 복구된다.
    """
)
async def restore_user(
    data: UserLogin,
    conn: Connection = Depends(get_db)
):
    return await restore_user_services(conn, data)