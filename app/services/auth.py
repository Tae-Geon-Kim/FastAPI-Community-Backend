import hashlib 
from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from asyncpg import Connection
from app.schemas.user import UserLogin
from app.core.security import(
    verify_password,
    create_access_token,
    create_refresh_token,
    credentials_exception
)
from app.models.user import get_info_by_id, pull_pw_restore_login
from app.models.audit_log import insert_audit_log
from app.core.config import jwt_auth

secret_key = jwt_auth.SECRET_KEY
algorithm = jwt_auth.ALGORITHM

# JWT 토큰 재발급
async def refresh_access_token_services(conn: Connection, refresh_token: str, redis_client):

    try:
        payload = jwt.decode(refresh_token, secret_key, algorithms = [algorithm])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception
        
        # Redis DB에 저장된 해싱된 토큰 값이 stored_token에
        stored_token = await redis_client.get(f"refresh:user:{user_id}")

        # front에 받은 refresh_token을 해싱한 값
        received_token = hashlib.sha256(refresh_token.encode()).hexdigest()

        if not stored_token or stored_token != received_token:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "인증이 만료되었거나 유효하지 않은 토큰입니다. 다시 로그인해주세요."
            )
        
        new_access = create_access_token(data = {"sub": str(user_id)})

        return new_access
    
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
async def token_login_services(data: UserLogin, conn: Connection, redis_client):

    user_info = await login(conn, data) # user의 인덱스 값

    # 로그인에 실패한 경우
    if user_info is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    # 로그인은 성공했는데 is_verified는 False인 상황
    if user_info['is_verified'] == False:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "이메일 인증이 완료되지 않았습니다. 이메일 인증을 진행해주세요."
        )
    
    user_num = user_info['index']

    access_token = create_access_token(data = {"sub": str(user_num)})
    refresh_token = create_refresh_token(data = {"sub": str(user_num)})

    hashed_refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()

    expire_seconds = jwt_auth.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    await redis_client.set(
        f"refresh:user:{user_num}", 
        hashed_refresh_token,
        ex = expire_seconds
    )
    
    await insert_audit_log(
        conn = conn,
        action = "LOGIN",
        target_type = "USER",
        target_index = user_num,
        actor_user_index = user_num,
        actor_user_id = data.id,
        detail = {"status": "success"}
    )

    return access_token, refresh_token

# DB에서 사용자가 직접 입력한 아이디를 기준으로 그에 대응하는 해싱된 비밀번호 값을 가져온다.
# 가져온 해싱된 비밀번호 값을 기준으로 일치하는지 확인한다.
# 입력한 아이디가 없는 경우에 대한 예외처리
async def login(conn: Connection, data: UserLogin):

    login_data = await get_info_by_id(conn, data.id)

    # 사용자가 입력한 아이디가 DB에 존재하지 않을 때
    if login_data is None:
        return None

    # 비밀번호 일치
    if verify_password(data.password, login_data['password']):
        return login_data
    else: # 비밀번호가 틀린 경우
        return None

# hashed_password[password] 라고 써야하는 이유: hashed_password 는 {key : value} 값 return
# 비밀번호 자체만 가져올라면 hashed_password['password'] -> 'password'인 이유: sql 문에서 내가 password라 지정함.

# 회원탈퇴 아이디 복구시 로그인
async def restore_login(conn: Connection, data: UserLogin):

    login_data = await pull_pw_restore_login(conn, data.id)

    if login_data is None:
        return None
    
    if verify_password(data.password, login_data['password']):
        return login_data['index']
    else:
        return None