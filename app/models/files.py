from asyncpg import Connection

# 파일 삽입
async def upload_files_db(conn: Connection, original_name: str, stored_name: str, file_path: str, file_size: int, board_index: int):

    sql = '''
        INSERT INTO "files" (original_name, stored_name, file_path, file_size, board_index)
        VALUES ($1, $2, $3, $4, $5)
    '''

    return await conn.execute(sql, original_name, stored_name, file_path, file_size, board_index)