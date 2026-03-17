# user 게시판에 관련된 router
import asyncpg
import asyncio
from pydantic import BaseModel
from fastapi import APIRouter
from database import connect_db
from encryption import hash_password, verify

router = APIRouter()

# DB에서 사용자가 직접 입력한 아이디를 기준으로 그에 대응하는 해싱된 비밀번호 값을 가져온다.
# 가져온 해싱된 비밀번호 값을 기준으로 일치하는지 확인한다.
# 입력한 아이디가 없는 경우에 대한 예외처리
class userData(BaseModel):
    name: str
    pw: str

@router.post("/blogin")
async def login(user : userData):
    conn = await connect_db()
    sql = 'select password FROM "user" WHERE id = $1'

    try:
        hashed_pw = await conn.fetchrow(sql, user.name)
        # 지금 fetchrow() 에서 가지고 오는 정보는 사용자 아이디에 대응하는 해싱된 비밀번호 값

        if hashed_pw == None:
        # 사용자가 입력한 아이디가 DB에 존재하지 않을 때
            return {"Message" : "입력한 아이디는 존재하지 않는 아이디입니다."}
        # verify(plain_password: str, hashed_password: str)
        # 사용자가 입력한 비밀번호와 해싱된 비밀번호가 일치할 때
        if verify(user.pw, hashed_pw['password']): 
            # hashed_pw[password] 라고 써야하는 이유: hashed_pw 는 {key : value} 값 return
            # 비밀번호 자체만 가져올라면 hashed_pw['password'] -> 'password'인 이유: sql 문에서 내가 password라 지정함. 
            return {
                "Message" : "로그인에 성공했습니다.",
                "사용자 아이디" : user.name
            }
        
        else:
        # 일치하지 않을 때
            return {"Message" : "입력하신 비밀번호가 일치하지 않습니다."}
   
    finally:
        await conn.close()

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

# 비밀번호 공백 검사 / 아이디 중복 검사 -> @router.post("/check")에 구현
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

    