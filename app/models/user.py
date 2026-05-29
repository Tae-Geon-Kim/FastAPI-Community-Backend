from asyncpg import Connection

# ========== 확인 / 검증 / 데이터 받아오기 ==========

# 특정 유저의 인덱스에 대응하는 유저의 아이디와 비밀번호를 불러온다. (탈퇴하지 않은 회원의)
async def get_user_id_pw(conn: Connection, user_index: int):

    sql = 'SELECT id, password FROM "user" WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, user_index)

# 특정 유저의 아이디를 통해서 해당 유저의 인덱스 값을 불러온다. (탈퇴하지 않은 회원의)
async def get_user_index(conn: Connection, user_id: str):

    sql = 'SELECT index FROM "user" WHERE id = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, user_id)

# 특정 유저의 인덱스를 통해서 해당 유저의 index, id, role, deleted_at을 불러온다.
async def get_current_user_info(conn: Connection, user_index: int):

    sql = 'SELECT index, id, role, deleted_at FROM "user" WHERE index = $1'

    return await conn.fetchrow(sql, user_index)

# 아이디에 맞는 비밀번호 확인
async def pull_pw_login(conn: Connection, user_id: str):

    sql = 'SELECT index, password, role FROM "user" WHERE id = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, user_id)

# 아이디 중복 확인
async def id_duplicate(conn: Connection, user_id: str):

    sql = 'SELECT id FROM "user" WHERE id = $1'

    return await conn.fetchrow(sql, user_id)

# 삭제 처리되지 않은 유저 중 특정 유저가 존재하는지 확인
async def check_undeleted_user_exist(conn: Connection, user_index: int):

    sql = 'SELECT index FROM "user" WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, user_index)

# 삭제 처리와 무관하게 전체 유저 중에서 특정 유저가 존재하는지 확인
async def check_user_exist(conn: Connection, user_index: int):

    sql = 'SELECT index FROM "user" WHERE index = $1'

    return await conn.fetchval(sql, user_index)

# 아이디에 맞는 비밀번호를 확인 (삭제 처리된 유저의)
async def pull_pw_restore_login(conn: Connection, user_id: str):

    sql = 'SELECT index, password FROM "user" WHERE id = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchrow(sql, user_id)

# 삭제 처리된 유저의 id, deleted_by, deleted_at 을 가져온다
async def get_deleted_user_info(conn: Connection, user_index: int):

    sql = 'SELECT id, deleted_by, deleted_at FROM "user" WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchrow(sql, user_index)

# ========== 삽입 ==========

# 아이디, 비밀번호 저장
async def push_id_pw(conn: Connection, user_id: str, user_password: str):

    sql = 'INSERT INTO "user" (id, password) VALUES ($1, $2)'

    return await conn.execute(sql, user_id, user_password)

# ========== 조회 ==========

# 사용자 정보 조회
async def pull_user_info(conn: Connection, user_index: int):

    sql = 'SELECT id, reg_date, update_date FROM "user" WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchrow(sql, user_index)

# ========== 변경 ==========

# 사용자 아이디 변경
async def userId_modify(conn: Connection, new_id: str, user_index: int):

    sql = 'UPDATE "user" SET id = $1, update_date = NOW() WHERE index = $2'

    return await conn.execute(sql, new_id, user_index)

# 사용자 비밀번호 변경
async def userPw_modify(conn: Connection, new_password: str, user_index: int):

    sql = 'UPDATE "user" SET password = $1, update_date = NOW() WHERE index = $2'

    return await conn.execute(sql, new_password, user_index)

# ========== 삭제 ==========

# 사용자 삭제처리
async def soft_delete_user(conn: Connection, deleted_by: str, user_index: int):

    sql = """
        UPDATE "user" SET deleted_by = $1, deleted_at = NOW(), update_date = NOW()
        WHERE index = $2 AND deleted_at IS NULL
    """

    return await conn.execute(sql, deleted_by, user_index)

# 삭제 처리된 유저 100일 지난 경우 유저의 개인정보를 익명화 (id: UNKNOWN, password: DELETED)
async def anonymize_withdrawn_user(conn: Connection):

    sql = """
        UPDATE "user"
        SET id = 'UNKNOWN_' || index::text, password = 'DELETED_0000!', update_date = NOW()
        WHERE deleted_at IS NOT NULL 
        AND deleted_at <= NOW() - INTERVAL '100 days'
        AND id NOT LIKE 'UNKNOWN_%'
    """
    
    return await conn.execute(sql)
    # execute 성공 시 'UPDATE 5' (5줄이 업데이트 되었다) 같은 결과 문자열 반환

async def delete_user(conn: Connection):

    sql = """
        DELETE FROM "user"
        WHERE deleted_by = 'ADMIN_SCHEDULED'
        AND deleted_at IS NOT NULL
        AND deleted_at <= NOW() INTERVAL - '100 days'
    """

    return await conn.execute(sql)

# 사용자 실제 삭제
async def hard_delete_user(conn: Connection, user_index: int):

    sql = 'DELETE FROM "user" WHERE index = $1'

    return conn.execute(sql, user_index)

# ========== 복구 ==========

# 사용자 회원탈퇴 복구 (user 정보)
async def restore_user_data(conn: Connection, user_id: str):

    sql = """
        UPDATE "user" SET deleted_by = NULL, deleted_at = NULL, update_date = NOW()
        WHERE id = $1 AND deleted_at IS NOT NULL
    """

    return await conn.execute(sql, user_id)