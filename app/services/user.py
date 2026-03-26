from asyncpg import Connection
from fastapi import HTTPException
from app.schemas.user import UserLogin, UserId, UserInfo, CommonResponse
from app.models.user import id_duplicate, push_id_pw, pull_user_info
from app.core.security import hash_password, verify
from app.services.auth import login

# 사용자 비밀번호 검사 
async def user_pw_services(conn: Connection, data: UserLogin):

    await user_name_services(conn, UserId(id = data.id))

    # 비밀번호 공백 포함 or 빈 문자열인 경우
    if not data.password.strip() or " " in data.password:
        raise HTTPException(status_code = 400, detail = "비밀번호에는 공백을 사용할 수 없으며 빈 문자열은 비밀번호로 사용할 수 없습니다.")

    # 비밀번호 해싱 처리 후 저장
    data.password = hash_password(data.password)
    await push_id_pw(conn, data)

    return CommonResponse(message = "회원가입이 성공적으로 완료되었습니다.")

# 신규 회원 아이디 중복, 빈 문자열 검사
async def user_name_services(conn: Connection, data: UserId):
    
    data.id = data.id.strip()
    # 아이디가 빈 문자열인 경우
    if not data.id:
        raise HTTPException(status_code = 400, detail = "빈 문자열을 아이디로 사용할 수 없습니다.")

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, data):
        raise HTTPException(status_code = 409, detail = "이미 사용중인 아이디입니다")
    
    return CommonResponse(message = "사용 가능한 아이디입니다!")

# 사용자 정보조회
async def user_info_services(conn: Connection, data: UserLogin):

    user_num = await login(conn, data)

    # 로그인 실패
    if user_num is None:
        raise HTTPException(status_code = 401, detail = "로그인 정보를 다시 확인해주세요.")
    
    user_data = await pull_user_info(conn, UserId(id = data.id))
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.

    return CommonResponse(
        message = "사용자 정보를 출력합니다.",
        data = UserInfo.model_validate(dict(user_data))
        # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
    )