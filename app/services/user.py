from asyncpg import Connection
from fastapi import HTTPException, status
from app.schemas.user import *
from app.models.user import *
from app.models.boards import soft_withdraw_boards
from app.core.security import *
from app.services.auth import *

# 사용자 비밀번호 검사 
async def user_pw_services(conn: Connection, data: UserLogin):

    await user_name_services(conn, UserId(id = data.id))

    # 비밀번호 공백 포함 or 빈 문자열인 경우
    if not data.password.strip() or " " in data.password:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "비밀번호에는 공백을 사용할 수 없으며 빈 문자열은 비밀번호로 사용할 수 없습니다."
        )

    # 비밀번호 해싱 처리 후 저장
    data.password = hash_password(data.password)
    await push_id_pw(conn, data)

    return CommonResponse(message = "회원가입이 성공적으로 완료되었습니다.")

# 신규 회원 아이디 중복, 빈 문자열 검사
async def user_name_services(conn: Connection, data: UserId):

    # 아이디가 공백 or 빈 문자열인 경우
    data.id = data.id.strip()
    if not data.id or " " in data.id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQEUST,
            detail = "아이디에는 공백을 사용할 수 없으며 빈 문자열은 아이디로 사용할 수 없습니다."
        )

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, data):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "이미 사용중인 아이디입니다."
        )

    return CommonResponse(message = "사용 가능한 아이디입니다!")

# 사용자 정보조회
async def user_info_services(conn: Connection, data: UserLogin):

    user_num = await login(conn, data)

    # 로그인 실패
    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )
    
    user_data = await pull_user_info(conn, UserId(id = data.id))
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.

    return CommonResponse(
        message = "사용자 정보를 출력합니다.",
        data = UserInfo.model_validate(dict(user_data))
        # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
    )

# 시용자 회원탈퇴 (복구 기능 포함)
async def user_withdraw_services(conn: Connection, data: UserLogin):

    user_num = await login(conn, data)
       
    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )
        
    async with conn.transaction():
        # soft delete
        await soft_withdraw_user(conn, data.id)
        await soft_withdraw_boards(conn, user_num)
    
    return CommonResponse(message = f"{data.id}님의 회원탈퇴가 성공적으로 처리되었습니다.")

async def withdraw_perman(pool):
    async with pool.acquire() as conn:
        await withdraw_permanently(conn)

# 사용자 아이디 변경
async def userId_modify_services(conn: Connection, data: ModiId):

    user_num = await login(conn, UserLogin(id = data.id, password = data.password))

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    # 아이디 공백 포함 빈 문자열 검사
    data.new_id = data.new_id.strip() # 아이디 양쪽 공백 제거
    if not data.new_id or " " in data.new_id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "아이디에는 공백을 사용할 수 없으며 빈 문자열은 아이디로 사용할 수 없습니다."
        )

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, UserId(id = data.new_id)):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "중복되는 아이디가 존재합니다."
        )
    
    await userId_modify(conn, data.new_id, data.id)

    return CommonResponse(
        message = f"{data.id}님의 아이디가 {data.new_id}로 수정되었습니다."
    )

# 사용자 비밀번호 변경
async def userPw_modify_services(conn: Connection, data: ModiPw):

    user_num = await login(conn, UserLogin(id = data.id, password = data.password))

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

     # 비밀번호 검사 (비밀번호 공백 포함 or 빈 문자열 여부)
    if not data.new_password or " " in data.new_password:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "비밀번호에는 공백을 사용할 수 없으며 빈 문자열은 비밀번호로 사용할 수 없습니다."
        )
    
    # 새로운 비밀번호 해싱처리
    data.new_password = hash_password(data.new_password)

    # DB 저장
    await userPw_modify(conn, data.new_password, data.id)

    return CommonResponse(message = f"{data.id}님의 비밀번호가 변경되었습니다.")