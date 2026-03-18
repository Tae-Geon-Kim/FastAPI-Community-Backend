# 공통 사용 함수 모듈화 - 로그인 
import asyncpg
import asyncio
from encryption import verify
from database import connect_db

# DB에서 사용자가 직접 입력한 아이디를 기준으로 그에 대응하는 해싱된 비밀번호 값을 가져온다.
# 가져온 해싱된 비밀번호 값을 기준으로 일치하는지 확인한다.
# 입력한 아이디가 없는 경우에 대한 예외처리

async def login(name: str, pw: str):
    conn = await connect_db()
    sql = 'select password FROM "user" WHERE id = $1'

    try:
        hashed_pw = await conn.fetchrow(sql, name)
        # 지금 fetchrow() 에서 가지고 오는 정보는 사용자 아이디에 대응하는 해싱된 비밀번호 값

        if hashed_pw == None:
        # 사용자가 입력한 아이디가 DB에 존재하지 않을 때
            return 0 

        if verify(pw, hashed_pw['password']): 
        # 사용자가 입력한 비밀번호와 해싱된 비밀번호가 일치할 때 
            return 1   
        else:
        # 일치하지 않을 때
            return 0
   
    finally:
        await conn.close()

# hashed_pw[password] 라고 써야하는 이유: hashed_pw 는 {key : value} 값 return
# 비밀번호 자체만 가져올라면 hashed_pw['password'] -> 'password'인 이유: sql 문에서 내가 password라 지정함.

