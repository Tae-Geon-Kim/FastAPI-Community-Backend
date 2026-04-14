import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import jwt_auth

secret_key = jwt_auth.SECRET_KEY
algorithm = jwt_auth.ALGORITHM
access_token_expire_minutes = jwt_auth.ACCESS_TOKEN_EXPIRE_MINUTES
refresh_token_expire_days = jwt_auth.REFRESH_TOKEN_EXPIRE_DAYS


# Swagger에서 Authorize 버튼 생성
security = HTTPBearer()

# 비밀번호를 해싱해서 암호화 후 반환 (return 값: string)
def hash_password(password: str):

    password = bytes(password, 'utf-8') # 암호화는 bytes에서 가능 -> bytes 변환
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()) # hashed에는 bytes가 

    return hashed_password.decode('utf-8') # string으로 -> DB 저장 필요

# DB에서 해싱처리된 비밀번호 값을 가져와 검증
def verify(plain_password: str, hashed_password: str):

    password = bytes(plain_password, 'utf-8')
    hashed_password = bytes(hashed_password, 'utf-8')

    # checkpw(password:bytes, hashed_password: bytes)

    return bcrypt.checkpw(password, hashed_password) # 반환 값: boolean

# access token 생성
def create_access_token(data: dict, expires_delta: timedelta | None = None):

    to_encode = data.copy()

    # 토큰 만료 시간 설정
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes = access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # JWT access token 생성
    encode_jwt = jwt.encode(to_encode, secret_key, algorithm = algorithm)
    return encode_jwt

# refresh token 생성
def create_refresh_token(data:dict, expires_delta: timedelta | None = None):

    to_encode = data.copy()

    # 토큰 만료 시간 설정
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days = refresh_token_expire_days)

    to_encode.update({"exp": expire})

    # JWT refresh token 생성
    encode_jwt = jwt.encode(to_encode, secret_key, algorithm = algorithm)
    return encode_jwt

# 토큰 확인
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
# Swagger에서 Authorize에 토큰을 넣으면 알아서 Credentials 변수에 토큰을 담아온다.

    try:
        payload = jwt.decode(credentials.credentials, secret_key, algorithms = [algorithm]) # 토큰 디코딩
        username: str = payload.get("sub") # 토큰 안의 유저 식별자 꺼내기
        if username is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "유효하지 않은 인증 자격입니다."
            )
        return username # 정상적인 토큰일시 반환
    except JWTError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "유효하지 않은 인증 자격입니다."
        )