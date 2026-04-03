from asyncpg import Connection

# 파일 삽입
async def upload_files_db(conn: Connection, original_name: str, stored_name: str, file_path: str, file_size: int, board_index: int):

    sql = '''
        INSERT INTO "files" (original_name, stored_name, file_path, file_size, board_index)
        VALUES ($1, $2, $3, $4, $5)
    '''

    return await conn.execute(sql, original_name, stored_name, file_path, file_size, board_index)

# 파일이 해당 게시판에 소속되어있는지 확인
# files_index 와 boards index에 해당하는 파일이 있으면 1 없므면 None
async def check_files_belong(conn: Connection, files_index: int, board_index: int):

    sql = '''
        SELECT 1
        FROM files 
        WHERE index = $1 
        AND board_index = $2
        AND deleted_at IS NULL
    '''
    
    return await conn.fetchval(sql, files_index, board_index)

# 특정 게시판의 전체 파일 용량을 확인
async def get_total_fsize(conn: Connection, board_index: int):

    sql = '''
        SELECT SUM(file_size)
        FROM files
        WHERE board_index = $1
        AND deleted_at IS NULL
    '''

    result = await conn.fetchval(sql, board_index)

    return result if result else 0

# 단일 파일 삭제 (실제 삭제 x, deleted_at 상태값만 변경)
async def soft_delete_one_file(conn: Connection, files_index: int):

    sql = 'UPDATE files SET deleted_at = NOW() WHERE index = $1'

    return await conn.execute(sql, files_index)

# 한 게시판의 전체 파일 삭제 (실제 삭제 x, deleted_at 상태값만 변경)
async def soft_delete_all_file(conn: Connection, board_index: int):

    sql = 'UPDATE files SET deleted_at = NOW() WHERE board_index = $1'

    return await conn.execute(sql, board_index)

# 파일 삭제 (실제 삭제)
async def delete_files(conn: Connection):

    sql = """
        DELETE FROM files WHERE deleted_at IS NOT NULL
        AND deleted_at <= NOW() - INTERVAL '3 days'
    """

    return await conn.execute(sql)

# 파일 삭제로 인해 변동된 게시판의 총 파일 용량 업데이트
async def update_total_fsize(conn: Connection, total_file_size: int, board_index: int):

    sql = 'UPDATE boards SET total_file_size = $1 WHERE index = $2'
    
    return await conn.execute(sql, total_file_size, board_index)