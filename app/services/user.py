from asyncpg import Connection
from app.schemas.user import UserCreate
from app.models.user import id_duplicate
from app.services.encryption import hash_password, verify
from app.services.util import login

# 사용자 회원가입
async def user_create_services(conn: Connection, data: UserCreate):

    # 비밀번호 공백 포함 or 빈 문자열인 경우
    if not data.pw.strip() or " " in data.pw:
        return {
            "성공 여부" : "False",
            "메시지" : "비밀번호에는 공백을 사용할 수 없으며 빈 문자열을 비밀번호로 사용할 수 없습니다."
        }
    
    data.name = data.name.strip()
    # 아이디가 빈 문자열인 경우
    if not data.name:
        return {
            "성공 여부" : "False"
            "메시지" : "빈 문자열을 아이디로 사용할 수 없습니다."
        }

    # 아이디가 중복되는 경우
    if await id_duplicate(conn, data):
        return  {
            "성공 여부" : "False"
            "메시지" : "중복되는 아이디가 존재합니다."
        }
    
    # 비밀번호 해싱 처리 후 저장
    data.pw = hash_password(data.pw)
    await push_id_pw(conn, data)

    return {
        "성공 여부" : "True"
        "메시지" : "회원가입이 성공적으로 완료되었습니다."
    }


# 사용자 정보조회
async def user_info_services(conn: Connection, data: UserCreate):


    if await login(conn, data) != 1:
        return {
            "성공 여부" : "False"
            "메시지" : "로그인에 실패하였습니다. 로그인 정보를 다시 확인해주세요."
        }
    else:
        return {
            "성공 여부" : "True"
            "메시지" : "로그인에 성공하였습니다. 사용자 정보를 출력합니다."
            "아이디" : "data.name"
            "비밀번호" : "data.pw"
        }    
