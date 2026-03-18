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

# 신규 회원가입 비밀번호를 입력했을 때, 해싱된 비밀번호 값을 DB에 저장 -> reg_date
@router.post("/uregister")
async def register(user : userData):
    conn = await connect_db()
    sql = 'INSERT INTO "user" (id, password) VALUES ($1, $2)'

    try:
        hash_pw = hash_password(user.pw)
        await conn.execute(sql, user.name, hash_pw)

        return {"Message" : "회원가입이 성공적으로 완료되었습니다."}

    finally:
        await conn.close()

# 신규 회원 비밀번호 공백 검사 / 아이디 중복 검사 -> @router.post("/check")에 구현
@router.post("/ucheck")
async def check(user : userData):

    # 비밀번호 공백 검사
    if not user.pw.strip():
        return {"Message" : "비밀번호에 공백을 사용할 수 없습니다."}

    conn = await connect_db()
    sql_get = 'SELECT id FROM "user" WHERE id = $1'
    sql_put = 'INSERT INTO "user" (id) VALUES ($1)'

    # 아이디 중복 체크
    try:
        id_duplicate = await conn.fetchrow(sql_get, user.name)
        # DB에서 user.name이랑 중복되는 이름이 있는지 확인해서 있으면 그 user에 대한 정보 전체를 없으면 None을 

        if id_duplicate:
        # 만약 입력받은  ID가 DB 상에 있는 ID들과 일치하는게 있으면 예외처리 (ID 중복)
            return {"Message" : "중복되는아이디입니다!"}
        else:
        # 만약 입력받은 ID가 DB 상에 있는 ID들과 일치하는게 없으면 (ID 중복 x)
            await conn.execute(sql_put, user.name)

    finally:
        await conn.close()