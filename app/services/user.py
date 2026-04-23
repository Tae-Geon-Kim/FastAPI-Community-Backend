from asyncpg import Connection
from fastapi import HTTPException, status
from app.schemas.user import *
from app.models.user import *
from app.models.boards import *
from app.core.security import *
from app.services.auth import *
from app.models.files import *

secret_key = jwt_auth.SECRET_KEY
algorithm = jwt_auth.ALGORITHM

credentials_exception = HTTPException(
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "유효하지 않은 인증 자격입니다.",
    headers = {"WWW-Authenticate": "Bearer"}
)

# JWT 토큰 재발급
async def refresh_access_token_services(conn: Connection, data: TokenRefreshRequest):
    
    try:
        payload = jwt.decode(data.refresh_token, secret_key, algorithms = [algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
           raise credentials_exception

        new_access = create_access_token(data = {"sub": str(user_id)})
        
        token_data = TokenResponse(
            access_token = new_access,
            refresh_token = data.refresh_token,
            token_type = "bearer"
        )

        return CommonResponse(
            message = "토큰이 성공적으로 재발급 되었습니다.",
            data = token_data
        )

    # 토큰 만료 에러
    except ExpiredSignatureError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "만료된 토큰입니다. 다시 로그인해주세요."
        )

    # 다른 모든 JWT error
    except JWTError:
        raise credentials_exception

# JWT Token 사용자 로그인
async def token_login_services(conn: Connection, data: UserLogin):

    user_num = await login(conn, data)

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    access_token = create_access_token(data = {"sub": str(user_num)})
    refresh_token = create_refresh_token(data = {"sub": str(user_num)})

    token_data = TokenResponse(
        access_token = access_token,
        refresh_token = refresh_token,
        token_type = "bearer"
    )

    return CommonResponse(
        message = "로그인에 성공하였습니다.",
        data = token_data
    )

# 사용자 비밀번호 검사 
async def user_pw_services(conn: Connection, data: UserLogin):

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
async def user_info_services(conn: Connection, current_user_num: str):
    
    user_data = await pull_user_info(conn, int(current_user_num))
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.

    return CommonResponse(
        message = "사용자 정보를 출력합니다.",
        data = UserInfo.model_validate(dict(user_data))
        # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
    )

# 시용자 회원탈퇴 (복구 기능 포함)
async def user_withdraw_services(data: UserPw, conn: Connection, current_user_num: str):
    
    user_info = await get_user_id_pw(conn, int(current_user_num))

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )
        
    async with conn.transaction():
        # soft delete
        await soft_withdraw_user(conn, int(current_user_num))
        await soft_withdraw_boards(conn, int(current_user_num))
        await soft_withdraw_files(conn, int(current_user_num))
    
    return CommonResponse(message = f"{user_info['id']}님의 회원탈퇴가 성공적으로 처리되었습니다.")

async def withdraw_user_perman(pool):
    async with pool.acquire() as conn:
        await withdraw_permanently(conn)

# 사용자 아이디 변경
async def userId_modify_services(data: ModiId, conn: Connection, current_user_num: str):
    
    user_info = await get_user_id_pw(conn, int(current_user_num))
    
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
    
    await userId_modify(conn, data.new_id, int(current_user_num))

    return CommonResponse(
        message = f"{user_info['id']}님의 아이디가 {data.new_id}로 수정되었습니다."
    )

# 사용자 비밀번호 변경
async def userPw_modify_services(data: ModiPw, conn: Connection, current_user_num: str):

    user_info = await get_user_id_pw(conn, int(current_user_num))
    
    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    # 새로운 비밀번호 해싱처리
    data.new_password = hash_password(data.new_password)

    # DB 저장
    await userPw_modify(conn, data.new_password, int(current_user_num))

    return CommonResponse(message = f"{user_info['id']}님의 비밀번호가 변경되었습니다.")

# 사용자 회원탈퇴 복구
async def restore_user_services(conn: Connection, data: UserLogin):

    # 회원 로그인 (권한 확인)
    user_num = await restore_login(conn, data)

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )
    
    # 사용자 데이터 복구
    async with conn.transaction():
        await restore_user_data(conn, data.id)
        await restore_user_boards(conn, user_num)
        await restore_user_file(conn, user_num)

    return CommonResponse(message = f"{data.id}님의 아이디가 복구되었습니다.")