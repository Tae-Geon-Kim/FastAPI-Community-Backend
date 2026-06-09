from asyncpg import Connection

# ========== 확인 / 검증 ==========

# 특정 게시판에 삭제처리 안된 정상적인 파일이 존재하는지 확인 - 1이 반환되면 존재하는 것
async def check_board_files_exist(conn: Connection, board_index: int):

    sql = 'SELECT 1 FROM files WHERE board_index = $1 AND deleted_at IS NULL LIMIT 1'

    return await conn.fetchval(sql, board_index)

# 특정 게시판에 삭제된 파일이 하나라도 존재하는지 - 1이 반환되면 존재하는 것 
async def check_board_deleted_files_exist(conn: Connection, board_index: int):

    sql = 'SELECT 1 FROM files WHERE board_index = $1 AND deleted_at IS NOT NULL LIMIT 1'

    return await conn.fetchval(sql, board_index)

# 특정 파일이 속한 게시판의 인덱스를 확인
async def get_file_belong(conn: Connection, file_index: int):

    sql = 'SELECT board_index FROM files WHERE index = $1'

    return await conn.fetchval(sql, file_index)

# 삭제 처리된 단일 파일이 특정 게시판에 속한게 맞는지 확인
async def check_deleted_file_belong(conn: Connection, file_index: int, board_index: int):

    sql = '''
        SELECT 1
        FROM files WHERE index = $1
        AND board_index = $2
        AND deleted_at IS NOT NULL
    '''

    return await conn.fetchval(sql, file_index, board_index)

# 삭제 처리가 안된 단일 파일이 특정 게시판에 속한게 맞는지
async def check_undeleted_file_belong(conn: Connection, file_index: int, board_index: int):

    sql = """
        SELECT 1 
        FROM files WHERE index = $1
        AND board_index = $2
        AND deleted_at IS NULL
    """

    return await conn.fetchval(sql, file_index, board_index)

# 삭제 처리가 안된 파일 중에서 특정 파일이 존재하는지 확인
async def check_undeleted_files_exist(conn: Connection, file_index: int):

    sql = 'SELECT index FROM files WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, file_index)

# 삭제 처리와 무관하게 전체 파일 중 특정 파일이 존재하는지 확인
async def check_files_exist(conn: Connection, file_index: int):

    sql = 'SELECT index FROM files WHERE index = $1'

    return await conn.fetchval(sql, file_index)

# 특정 파일이 삭제 처리된 파일인지 확인
async def check_file_deleted(conn: Connection, file_index: int):

    sql = 'SELECT index FROM files WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchval(sql, file_index)

# 삭제 처리된 특정 파일의 정보를 가져온다.
async def get_deleted_file_info(conn: Connection, file_index: int):

    sql = """
        SELECT deleted_at, deleted_by FROM files
        WHERE index = $1 
        AND deleted_at IS NOT NULL
    """

    return await conn.fetchrow(sql, file_index)

# ========== 삽입 ==========
# 파일 삽입
async def upload_files_db(conn: Connection, original_name: str, stored_name: str, file_path: str, file_size: int, board_index: int):

    sql = '''
        INSERT INTO "files" (original_name, stored_name, file_path, file_size, board_index)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING index
    '''

    new_file_index = await conn.fetchval(sql, original_name, stored_name, file_path, file_size, board_index)

    return new_file_index

# ========== 용량 ==========

# 관리자용 - 복구 가능한 파일들의 용량 합을 반환 - 삭제된지 90일이내 (deleted_by 체크 x)
async def admin_get_restorable_fsize(conn: Connection, board_index: int):

    sql = """
        SELECT SUM(file_size) FROM files
        WHERE board_index = $1
        AND deleted_at IS NOT NULL
        AND deleted_at >= NOW() - INTERVAL '90 days'
    """

    return await conn.fetchval(sql, board_index)

# 유저용 - 복구 가능한 파일들의 용량 합을 반환 - 삭제된지 7일이내 (deleted_by: USER)
async def user_get_restorable_fsize(conn: Connection, board_index: int):

    sql = """
        SELECT SUM(file_size) FROM files
        WHERE board_index = $1
        AND deleted_by = 'USER'
        AND deleted_at IS NOT NULL
        AND deleted_at >= NOW() - INTERVAL '7 days'
    """

    return await conn.fetchval(sql, board_index)

# 파일의 인덱스로 해당 파일의 사이즈를 확인 (삭제처리된 파일 - deleted_at == NOT NULL)
async def get_softDelete_fsize(conn: Connection, files_index: int):

    sql = 'SELECT file_size FROM files WHERE index = $1'

    result = await conn.fetchval(sql, files_index)

    return result if result else 0

# 특정 게시판의 전체 파일 용량을 확인 (삭제되지 않은 파일 - delted_at == NULL)
async def get_total_fsize(conn: Connection, board_index: int):

    sql = '''
        SELECT SUM(file_size)
        FROM files
        WHERE board_index = $1
        AND deleted_at IS NULL
    '''

    result = await conn.fetchval(sql, board_index)

    return result if result else 0

# 특정 게시판에 삭제 처리된 파일들 용량의 총 합 - delted_at == NOT NULL
async def get_total_softDelete_fsize(conn: Connection, board_index: int):

    sql = '''
        SELECT SUM(file_size)
        FROM files
        WHERE board_index = $1
        AND deleted_at IS NOT NULL
    '''

    result = await conn.fetchval(sql, board_index)

    return result if result else 0

# 특정 유저 복구로 안한 파일 복구에서 복구시 용량이 초과되는 게시판이 있는지 확인 (USER_CASCADE)
async def check_restore_exceeding_boards_total_fsize(conn: Connection, user_index: int, allow_max_total_fsize: int):

    sql = """
        SELECT f.board_index, SUM(f.file_size) as future_total_size
        FROM files f
        INNER JOIN boards b ON f.board_index = b.index
        WHERE b.user_index = $1
        AND (f.deleted_at IS NULL OR f.deleted_by = 'USER_CASCADE')
        GROUP BY f.board_index
        HAVING SUM(f.file_size) > $2
        LIMIT 1;
    """

    return await conn.fetchrow(sql, user_index, allow_max_total_fsize)

# ========== 삭제 ==========

# 단일 파일 삭제 처리 (soft delete)
async def soft_delete_one_file(conn: Connection, deleted_by: str, file_index: int):

    sql = 'UPDATE files SET deleted_by = $1, deleted_at = NOW() WHERE index = $2'

    return await conn.execute(sql, deleted_by, file_index)

# 한 게시판의 전체 파일 삭제 처리 (soft delete)
async def soft_delete_all_board_files(conn: Connection, deleted_by: str, board_index: int):

    sql = 'UPDATE files SET deleted_by = $1, deleted_at = NOW() WHERE board_index = $2 AND deleted_at IS NULL'

    return await conn.execute(sql, deleted_by, board_index)

# 특정 유저가 올린 모든 파일을 삭제 처리 (soft delete)
async def soft_delete_all_user_files(conn: Connection, deleted_by: str, user_index: int):

    sql = '''
        UPDATE files
        SET deleted_by = $1, deleted_at = NOW()
        WHERE board_index IN (SELECT index FROM boards WHERE user_index = $2)
        AND deleted_at IS NULL
    '''

    return await conn.execute(sql, deleted_by, user_index)

# 삭제 처리된 파일들이 100일이 지나면 실제 삭제 (삭제 처리된 파일은 무조건 스케줄러 삭제 - deleted_by 상관없이)
async def delete_files(conn: Connection):

    sql = '''
        DELETE FROM files
        WHERE deleted_at IS NOT NULL
        AND (
            (deleted_by IN ('USER', 'USER_CASCADE', 'BOARD_CASCADE') AND deleted_at <= NOW() - INTERVAL '30 days')
            OR
            (deleted_by IN ('ADMIN_SCHEDULED', 'ADMIN_RETAIN') AND deleted_at <= NOW() - INTERVAL '100 days')
        )
    '''
    
    return await conn.execute(sql)

# 지워야 할 파일의 실제 파일의 경로를 가져온다.
async def get_delete_file_path(conn: Connection):

    sql = '''
        SELECT file_path FROM files
        WHERE deleted_at IS NOT NULL
        AND (
            (deleted_by IN ('USER', 'USER_CASCADE', 'BOARD_CASCADE') AND deleted_at <= NOW() - INTERVAL '30 days')
            OR
            (deleted_by IN ('ADMIN_SCHEDULED', 'ADMIN_RETAIN') AND deleted_at <= NOW() - INTERVAL '100 days')
        )
    '''

    return await conn.fetch(sql)

# 단일 파일 삭제 (hard delete)
async def hard_delete_one_file(conn: Connection, file_index: int):

    sql = 'DELETE FROM files WHERE index = $1'

    return await conn.execute(sql, file_index)

# 한 게시판의 전체 파일을 삭제 (hard delete)
async def hard_delete_all_board_files(conn: Connection, board_index: int):

    sql = 'DELETE FROM files WHERE board_index = $1'

    return await conn.execute(sql, board_index)

# 특정 유저의 모든 파일을 삭제 (hard delete)
async def hard_delete_all_user_files(conn: Connection, user_index: int):

    sql = '''
        DELETE FROM files
        WHERE board_index IN (SELECT index FROM boards WHERE user_index = $1)
    '''

    return await conn.execute(sql, user_index)

# ========== 복구 ==========

# 삭제 처리된 (soft deleted) 단일 파일을 복구 
async def restore_one_file(conn: Connection, file_index: int):

    sql = 'UPDATE files SET deleted_by = NULL, deleted_at = NULL WHERE index = $1'

    return await conn.execute(sql, file_index)

# 특정 게시판의 삭제 처리된 (soft deleted) 모든 파일을 일괄 복구
async def restore_all_board_files(conn: Connection, board_index: int):

    sql = 'UPDATE files SET deleted_by = NULL, deleted_at = NULL WHERE board_index = $1 AND deleted_at IS NOT NULL'

    return await conn.execute(sql, board_index)

# 특정 유저의 삭제로 인해 삭제처리된 파일들 일괄 복구
async def restore_all_user_files(conn: Connection, user_index: int, days: int):

    sql = '''
        UPDATE files
        SET deleted_by = NULL, deleted_at = NULL
        WHERE board_index IN  (SELECT index FROM boards WHERE user_index = $1)
        AND deleted_by = 'USER_CASCADE'
        AND deleted_at >= NOW()  -$2::int * INTERVAL '1 day'
    '''

    return await conn.execute(sql, user_index, days)

# 관리자용 - 복구 가능한 파일들 복구 (deleted_by 체크 x) - 삭제된지 90일 이내
async def admin_restore_all_restorable_files(conn: Connection, board_index: int):

    sql = """
        UPDATE files
        SET deleted_by = NULL, deleted_at = NULL
        WHERE board_index = $1
        AND deleted_at IS NOT NULL
        AND deleted_at >= NOW() - INTERVAL '90 days'
    """

    return await conn.execute(sql, board_index)

# 유저용 - 복구 가능한 파일들 복구 (deleted_by: USER) - 삭제된지 30일 이내
async def user_restore_all_restorable_files(conn: Connection, board_index: int):

    sql = """
        UPDATE files
        SET deleted_by = NULL, deleted_at = NULL
        WHERE board_index = $1
        AND deleted_by = 'USER'
        AND deleted_at IS NOT NULL
        AND deleted_at >= NOW() - INTERVAL '30 days'
    """

    return await conn.execute(sql, board_index)

# 게시판 삭제로 인해 같이 삭제된 파일들만 복구 (게시판 복구시 사용)
async def restore_cascade_board_files(conn: Connection, board_index: int, days: int):

    sql = f"""
        UPDATE files
        SET deleted_by = NULL, deleted_at = NULL
        WHERE board_index = $1
        AND deleted_by = 'BOARD_CASCADE'
        AND deleted_at IS NOT NULL
        AND deleted_at >= NOW() - $2::int * INTERVAL '1 day'
    """

    return await conn.execute(sql, board_index, days)