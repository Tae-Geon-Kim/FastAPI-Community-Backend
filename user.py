# user 게시판에 관련된 router
import asyncpg
import asyncio
from pydantic import BaseModel
from fastapi import APIRouter
from database import connect_db
from encryption import hash_password, verify

router = APIRouter()

class userData(BaseModel):
    name: str
    pw: str

# 신규 회원가입 비밀번호를 입력했을 때, 해싱된 비밀번호 값을 DB에 저장 -> reg_date // 저장하기전에 전체적으로 다시 재검증 해야함.
@router.post("/uregister")
async def register(user : userData):

    # 비밀번호 공백 & 빈 문자열 검사
    if not user.pw.strip() or " " in user.pw:
        return {"Message" : "비밀번호에 공백을 사용할 수 없으며, 반드시 입력해야 합니다."}

    user.name = user.name.strip() # ID 앞 뒤 공백 삭제
    if not user.name:
        return {"Message" : "아이디로 빈 문자열을 사용할 수 없습니다."}

    conn = await connect_db()
    sql_push = 'INSERT INTO "user" (id, password) VALUES ($1, $2)'
    sql_pull = 'SELECT id FROM "user" WHERE id = $1'

    try:
        id_duplicate = await conn.fetchrow(sql_pull, user.name)

        if id_duplicate:
            return {"Message" : "중복되는 아이디입니다!"}

        hash_pw = hash_password(user.pw)
        await conn.execute(sql_push, user.name, hash_pw)

        return {"Message" : "회원가입이 성공적으로 완료되었습니다."}

    finally:
        await conn.close()

# 신규 회원 아이디 중복, not null 검사
@router.post("/ucheck")
async def check(user : userData):

    # ID not null 검사 
    user.name = user.name.strip() # ID 앞 뒤 공백 제거
    if not user.name:
        return {"Message" : "아이디로 빈 문자열을 사용할 수 없습니다."}

    conn = await connect_db()
    sql_get = 'SELECT id FROM "user" WHERE id = $1'

    # 아이디 중복 체크
    try:
        id_duplicate = await conn.fetchrow(sql_get, user.name)
        # DB에서 user.name이랑 중복되는 이름이 있는지 확인해서 있으면 그 user에 대한 정보 전체를 없으면 None을 

        if id_duplicate:
        # 만약 입력받은  ID가 DB 상에 있는 ID들과 일치하는게 있으면 예외처리 (ID 중복)
            return {"Message" : "중복되는 아이디입니다!"}
        else:
        # 만약 입력받은 ID가 DB 상에 있는 ID들과 일치하는게 없으면 (ID 중복 x)
            return  {"Message" : "사용 가능한 아이디 입니다!"}

    finally:
        await conn.close()

# 사용자 정보 조회
@router.post("/uinfo")
async def userInfo(user : userData):

    sql = 'SELECT * FROM "user" WHERE id = ($1)'

    if await login(user.name, user.pw) == 1:
        conn = await connect_db()
        try:
            user_info = await conn.fetchrow(sql, user.name) #if user_info: 해서 최종 검증 로직 만드는거 고민 (방어적 프로그래밍)
            return {
                "메세지" : "사용자 정보 조회 성공",
                "아이디" : user_info['id'],
                "회원 가입 일시" : user_info['reg_date'],
                "회원 정보 수정 일시" : user_info['update_date'] 
            }
        finally:
            await conn.close()
    else:
        return {"Message" : "로그인에 실패했습니다."}
