from asyncpg import Connection
from app.schemas.user import UserCreate, UserIdCheck
from app.models.user import id_duplicate, push_id_pw
from app.services.encryption import hash_password, verify
from app.services.util import login

# 사용자 비밀번호 검사 
async def user_pw_services(conn: Connection, data: UserCreate):

    name_check = await user_name_services(conn, data)

    # user_name_check 결과 False이면 해당 return 문을 출력
    if name_check["성공 여부"] == "False":
        return name_check

    # 비밀번호 공백 포함 or 빈 문자열인 경우
    if not data.password.strip() or " " in data.password:
        return {
            "성공 여부" : "False",
            "메시지" : "비밀번호에는 공백을 사용할 수 없으며 빈 문자열을 비밀번호로 사용할 수 없습니다."
        }
    
    # 비밀번호 해싱 처리 후 저장
    data.password = hash_password(data.password)
    await push_id_pw(conn, data)

    return {
        "성공 여부" : "True",
        "메시지" : "회원가입이 성공적으로 완료되었습니다."
    }


# 신규 회원 아이디 중복, 빈 문자열 검사
async def user_name_services(conn: Connection, data: UserIdCheck):
    
    data.id = data.id.strip()
    # 아이디가 빈 문자열인 경우
    if not data.id:
        return {
            "성공 여부" : "False",
            "메시지" : "빈 문자열을 아이디로 사용할 수 없습니다."
        }

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, data):
        return  {
            "성공 여부" : "False",
            "메시지" : "중복되는 아이디가 존재합니다."
        }
    
    # 아이디가 정상적인 경우

    return {
        "성공 여부" : "True",
        "메시지" : "사용 가능한 아이디입니다!"
    }


# 사용자 정보조회
async def user_info_services(conn: Connection, data: UserCreate):

    if await login(conn, data) != 1:
        return {
            "성공 여부" : "False",
            "메시지" : "로그인에 실패하였습니다. 로그인 정보를 다시 확인해주세요."
        }
    else:
        return {
            "성공 여부" : "True",
            "메시지" : "로그인에 성공하였습니다. 사용자 정보를 출력합니다.",
            "아이디" : data.id,
            "비밀번호" : data.password
        }
