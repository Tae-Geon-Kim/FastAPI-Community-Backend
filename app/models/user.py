from asyncpg import Connection

# 아이디에 맞는 비밀번호 확인
async def pull_pw_login(conn: Connection, user_id: str):

    sql = 'SELECT index, password FROM "user" WHERE id = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, user_id)

# 아이디, 비밀번호 저장
async def push_id_pw(conn: Connection, user_id: str, user_password: str):

    sql = 'INSERT INTO "user" (id, password) VALUES ($1, $2)'

    return await conn.execute(sql, user_id, user_password)

# 아이디 중복 확인
async def id_duplicate(conn: Connection, user_id: str):

    sql = 'SELECT id FROM "user" WHERE id = $1'

    return await conn.fetchrow(sql, user_id)

# 사용자 정보 조회
async def pull_user_info(conn: Connection, user_id: str):

    sql = 'SELECT id, reg_date, update_date FROM "user" WHERE id = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, user_id)

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

# 사용자 아이디 변경
async def userId_modify(conn: Connection, new_id: str, user_id: str):

    sql = 'UPDATE "user" SET id = $1, update_date = NOW() WHERE id = $2'

    return await conn.execute(sql, new_id, user_id)

# 사용자 비밀번호 변경
async def userPw_modify(conn: Connection, new_password: str, user_id: str):

    sql = 'UPDATE "user" SET password = $1, update_date = NOW() WHERE id = $2'

    return await conn.execute(sql, new_password, user_id)

# 사용자 회원탈퇴 복구 (user 정보)
async def restore_user_data(conn: Connection, user_id: str):

    sql = 'UPDATE "user" SET deleted_at = NULL WHERE id = $1 AND deleted_at IS NOT NULL'

    return await conn.execute(sql, user_id)

# 아이디에 맞는 비밀번호를 확인
async def pull_pw_restore_login(conn: Connection, user_id: str):

    sql = 'SELECT index, password FROM "user" WHERE id = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchrow(sql, user_id)
