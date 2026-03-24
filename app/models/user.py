from asyncpg import Connection
from app.schemas.user import UserCreate

# 로그인: 아이디에 맞는 비밀번호 확인
async def pull_pw_login(conn: Connection, data: UserCreate):
    sql = 'SELECT pw FROM "user" WHERE name = $1'

    return await conn.fetchrow(sql, data.name)

# 아이디, 비밀번호 저장
async def push_id_pw(conn: Connection, data: UserCreate):
    sql = 'INSERT INTO "user" (name, pw) VALUES ($1, $2)'

    return await conn.execute(sql, data.name, data.pw)

# 아이디 중복 확인
async def id_duplicate(conn: Connection, data: UserCreate):
    sql = 'SELECT name FROM "user" WHERE name = $1'

    return await conn.fetchrow(sql, data.name)
