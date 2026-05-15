from asyncpg import Connection

# 관리자 정보 조회 부분에서는 deleted_at IS NULL / NOT NULL 상관없이 모두 조회

# 관리자 전체 유저 조회 (deleted_at IS NOT NULL / NULL 전체)
# 해당 유저의 아이디, 인덱스 / 생성 일자 / 수정 일자 / 역할 / 상대 + 작성한 게시판 수, 작성한 파일 수
async def admin_get_all_users(conn: Connection):

    sql = """
        SELECT
            u.id, u.index, u.role, u.status, u.reg_date, u.update_date,
            COUNT(DISTINCT b.index) AS total_boards,
            COUNT(DISTINCT f.index) AS total_files
        FROM public."user" AS u
        LEFT JOIN public.boards AS b ON u.index  = b.user_index
        LEFT JOIN public.files AS f ON b.index = f.board_index
        GROUP BY u.index
        ORDER BY u.index ASC;
    """

    return await conn.fetch(sql)

# 관리자 특정 유저 정보 상세 조회 (관리자 전체 유저 목록에서 특정 유저 아이디 클릭했을 때)
# 해당 유저가 쓴 글들이 페이지네이션되서 나오도록 (파일 목록은 관리자 특정 게시판 상세 조회에서)
async def admin_get_specific_user(conn: Connection, user_index: int, limit: int, offset: int):

    sql = """
        SELECT
            b.index AS board_index, b.title, b.content, b.reg_date AS board_reg_date, b.update_date AS board_update_date, b.total_file_size,
            u.id, u.index AS user_index, u.role, u.status, u.reg_date AS user_reg_date
        FROM public.boards AS b
        INNER JOIN public."user" AS u ON b.user_index = u.index
        WHERE u.index = $1
        ORDER BY b.index DESC 
        LIMIT $2 OFFSET $3;
    """

    return await conn.fetch(sql, user_index, limit, offset)

# 관리자 특정 게시판 상세 조회 (관리자 유저 상세 조회에서 특정 게시판 클릭했을 때)
# 이 때 글 작성자의 아이디 및 인덱스, 작성자의 역할 및 상태, 게시글 제목 및 내용, 게시글의 생성일자 및 수정 일자
# 파일 정보(파일의 인덱스, 파일의 original_name, 파일 사이즈, 파일 생성 일자)
async def admin_get_specific_board(conn: Connection, board_index: int):

    sql = """
        SELECT
            b.index, b.title, b.content, b.reg_date, b.update_date, b.total_file_size, u.id AS user_id,
            COALESCE (
                (SELECT json_agg(json_build_object(
                    'index', f.index,
                    'original_name', f.original_name,
                    'file_size', f.file_size,
                    'reg_date', f.reg_date
                ))
                FROM public.files AS f
                WHERE f.board_index = b.index),
                '[]'::json 
            ) AS files
        FROM public.boards AS b
        INNER JOIN public."user" AS u ON b.user_index = u.index
        WHERE b.index = $1;
    """

    return await conn.fetchrow(sql, board_index)

# 관리자 특정 게시판의 작성자 인덱스를 확인 (board_index -> user_index 확인)
async def admin_check_board_belong(conn: Connection, board_index: int):

    sql = 'SELECT user_index FROM boards WHERE index = $1'

    return await conn.fetchval(sql, board_index)

# 관리자 특정 파일 인덱스가 어떤 게시판의 인덱스에 속하는지 확인 (file_index -> board_index)
async def admin_get_file_board_index(conn: Connection, file_index: int):

    sql = 'SELECT board_index FROM files WHERE index = $1'

    return await conn.fetchval(sql, file_index)

# 관리자 공지사항 글 작성 (DB에 넣고 다시 해당 게시글 (공지사항)의 인덱스를 반환)
async def admin_register_notice(conn: Connection, title: str, content: str, category: str, user_index: int):

    sql = 'INSERT INTO boards (title, content, category, user_index) VALUES ($1, $2, $3, $4) RETURNING index'

    return await conn.fetchval(sql, title, content, category, user_index)

# 관리자 특정 유저를 블랙리스트 처리 
async def admin_blacklist(conn: Connection, user_index: int, ban_days: int):

    sql = """
        UPDATE public."user"
        SET status = 'BANNED',
            ban_count = ban_count + 1,
            ban_end_at = NOW() + $2::int * INTERVAL '1 day'
        WHERE index = $1
    """

    return await conn.execute(sql, user_index, ban_days)

# 관리자 특정 유저의 ban_count를 가쟈오는 쿼리
async def admin_get_banCount(conn: Connection, user_index: int):

    sql = 'SELECT ban_count FROM public."user" WHERE index = $1'

    return await conn.fetchval(sql, user_index)

# 관리자 특정 유저를 삭제
async def admin_delete_user(conn: Connection, user_index: int):

    sql = 'DELETE FROM "user" WHERE index = $1'

    return await conn.execute(sql, user_index)

# 삭제를 하려는 게시판이 존재하는지 확인 (삭제처리 안된 것 중에서 - deleted_at == NULL)
async def admin_check_soft_delete_board(conn: Connection, board_index: int):

    sql = 'SELECT index FROM boards WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, board_index)

# 삭제를 하려는 게시판이 존재하는지 확인 (삭제 처리 상관 x)
async def admin_check_hard_delete_board(conn: Connection, board_index: int):
    
    sql = 'SELECT index FROM boards WHERE index = $1'

    return await conn.fetchval(sql, board_index)

# 관리자 특정 게시판을 삭제 (soft delete - 관리자는 3일)
async def admin_soft_delete_board(conn: Connection, board_index: int):

    sql = 'UPDATE boards SET deleted_at = NOW() WHERE index = $1 AND deleted_at IS NULL'

    return await conn.execute(sql, board_index)

# 관리자 특정 게시판을 삭제 (hard delete - soft delete 처리 된 것 아닌 것 모두 포함)
async def admin_hard_delete_board(conn: Connection, board_index: int):

    sql = 'DELETE FROM boards WHERE index = $1'

    return await conn.execute(sql, board_index)

# 삭제하려는 파일이 존재하는지 확인 (삭제처리 안된 것 중에서 - deleted_at == NULL)
async def admin_check_soft_delete_file(conn: Connection, file_index: int):

    sql = 'SELECT index FROM files WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, file_index)

# 삭제하려는 파일이 존재하는지 확인 (삭제처리 상관 x)
async def admin_check_hard_delete_file(conn: Connection, file_index: int):

    sql = 'SELECT index FROM files WHERE index = $1'

    return await conn.fetchval(sql, file_index)

# 관리자 특정 파일을 삭제 (soft delete - 관리자는 3일)
async def admin_soft_delete_file(conn: Connection, file_index: int):

    sql = 'UPDATE files SET deleted_at = NOW() WHERE index = $1 AND deleted_at IS NULL'

    return await conn.execute(sql, file_index)

# 관리자 특정 파일을 삭제 (hard delete - 삭제처리 상관 x)
async def admin_hard_delete_file(conn: Connection, file_index: int):

    sql = 'DELETE FROM files WHERE index = $1'

    return await conn.execute(sql, file_index)

# 관리자 복구하려는 게시판이 삭제처리된 게시판인지
async def admin_check_restore_board(conn: Connection, board_index: int):

    sql = 'SELECT index FROM boards WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchval(sql, board_index)

# 관리자 게시판 복구 (soft delete된 파일들만)
async def admin_restore_board(conn: Connection, board_index: int):

    sql = 'UPDATE boards SET deleted_at = NULL WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.execute(sql, board_index)

# 특정 게시판에 있는 삭제 처리된 (soft deleted된) 모든 파일을 복구
async def admin_restore_all_files(conn: Connection, board_index: int):

    sql = 'UPDATE files SET deleted_at = NULL WHERE board_index = $1 AND deleted_at IS NOT NULL'

    return await conn.execute(sql, board_index)

# 관리자 복구하려는 파일이 삭제처리된 파일인지
async def admin_check_restore_file(conn: Connection, file_index: int):

    sql = 'SELECT index FROM files WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchval(sql, file_index)

# 관리자 복구하려는 파일 (file_index / deleted_at IS NOT NULL) 이 해당 게시판 (board_index)에 속한게 맞는지
async def admin_check_file_belong(conn: Connection, board_index: int, file_index: int):

    sql = 'SELECT board_index FROM files WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.fetchval(sql, board_index, file_index)

# 관리자 파일 복구 (soft delete된 파일들만)
async def admin_restore_file(conn: Connection, file_index: int):

    sql = 'UPDATE files SET deleted_at = NULL WHERE index = $1 AND deleted_at IS NOT NULL'

    return await conn.execute(sql, file_index)