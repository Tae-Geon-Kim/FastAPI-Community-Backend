from asyncpg import Connection
from app.schemas.user import UserLogin, UserId

# 로그인: 아이디에 맞는 비밀번호 확인
async def pull_pw_login(conn: Connection, data: UserLogin):
    sql = 'SELECT index, password FROM "user" WHERE id = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, data.id)

# 아이디, 비밀번호 저장
async def push_id_pw(conn: Connection, data: UserLogin):
    sql = 'INSERT INTO "user" (id, password) VALUES ($1, $2)'

    return await conn.execute(sql, data.id, data.password)

# 아이디 중복 확인
async def id_duplicate(conn: Connection, data: UserId):
    sql = 'SELECT id FROM "user" WHERE id = $1'

    return await conn.fetchrow(sql, data.id)

# 사용자 정보 조회
async def pull_user_info(conn: Connection, data: UserId):
    sql = 'SELECT id, reg_date, update_date FROM "user" WHERE id = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, data.id)

# 사용자 정보 삭제 (실제 삭제 x, 상태값만 변경)
async def soft_withdraw_user(conn: Connection, user_id: str):
    
    sql = 'UPDATE "user" SET deleted_at = NOW() WHERE id = $1'

    return await conn.execute(sql, user_id)

# 사용자 정보 삭제 (실제 삭제)
async def withdraw_permanently(conn: Connection):

    sql = """
        DELETE FROM "user"
        WHERE deleted_at IS NOT NULL
        AND deleted_at <= NOW() - INTERVAL '3 days'
        """
    
    return await conn.execute(sql)
