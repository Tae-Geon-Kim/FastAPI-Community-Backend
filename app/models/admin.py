from asyncpg import Connection

# ========== 조회 ==========

# 관리자 전체 유저 조회
async def admin_get_all_users(conn: Connection):

    sql = """
        SELECT
            u.id, u.index, u.role, u.status, u.reg_date, u.update_date,
            u.deleted_at, u.deleted_by,
            COUNT(DISTINCT b.index) AS total_boards,
            COUNT(DISTINCT f.index) AS total_files
        FROM public."user" AS u
        LEFT JOIN public.boards AS b ON u.index  = b.user_index
        LEFT JOIN public.files AS f ON b.index = f.board_index
        GROUP BY u.index
        ORDER BY u.index ASC;
    """

    return await conn.fetch(sql)


# 관리자 특정 유저 정보 상세 조회
async def admin_get_specific_user(conn: Connection, user_index: int, limit: int, offset: int):

    sql = """
        SELECT
            u.id, u.index AS user_index, u.role, u.status, u.reg_date AS user_reg_date,
            u.deleted_at AS user_deleted_at, u.deleted_by AS user_deleted_by,
            b.index AS board_index, b.title, b.content, b.reg_date AS board_reg_date, b.update_date AS board_update_date, b.total_file_size,
            b.deleted_at AS board_deleted_at, b.deleted_by AS board_deleted_by
        FROM public."user" AS u
        LEFT JOIN public.boards AS b ON u.index = b.user_index
        WHERE u.index = $1
        ORDER BY b.index DESC 
        LIMIT $2 OFFSET $3;
    """

    return await conn.fetch(sql, user_index, limit, offset)


# 관리자 특정 게시판 상세 조회
async def admin_get_specific_board(conn: Connection, board_index: int):

    sql = """
        SELECT
            b.index, b.title, b.content, b.reg_date, b.update_date, b.total_file_size, 
            b.deleted_at, b.deleted_by,
            u.id AS user_id,
            COALESCE (
                (SELECT json_agg(json_build_object(
                    'index', f.index,
                    'original_name', f.original_name,
                    'file_size', f.file_size,
                    'reg_date', f.reg_date,
                    'deleted_at', f.deleted_at,
                    'deleted_by', f.deleted_by
                ))
                FROM public.files AS f
                WHERE f.board_index = b.index),
                '[]'::json 
            ) AS files
            
        FROM public.boards AS b
        LEFT JOIN public."user" AS u ON b.user_index = u.index
        WHERE b.index = $1;
    """

    return await conn.fetchrow(sql, board_index)


# ========== 삭제 (값 업데이트) ==========

# 관리자 특정 유저를 ban 처리
async def admin_ban(conn: Connection, user_index: int, ban_days: int):

    sql = """
        UPDATE public."user"
        SET status = 'BANNED',
            ban_count = ban_count + 1,
            ban_end_at = NOW() + $2::int * INTERVAL '1 day',
            update_date = NOW()
        WHERE index = $1
    """

    return await conn.execute(sql, user_index, ban_days)

# 관리자 특정 유저 ban 4회 됐을 때의 상태값 처리
async def admin_user_4ban_settings(conn: Connection, user_index: int):

    sql = """
        UPDATE public."user"
        SET status = 'WITHDRAWN',
            ban_end_at = NULL,
            ban_count = 4,
            update_date = NOW()
        WHERE index = $1
    """

    return await conn.execute(sql, user_index)

# 관리자 특정 유저를 unban 처리
async def admin_unban(conn: Connection, user_index: int):

    sql = """
        UPDATE public."user"
        SET status = 'ACTIVE',
            ban_count = 0,
            ban_end_at = NULL
        WHERE index = $1
        AND deleted_at IS NULL
    """

    return await conn.execute(sql, user_index)

# ========== 데이터 가져오기 ==========

# 관리자 특정 유저의 ban_count를 가쟈오는 쿼리
async def admin_get_banCount(conn: Connection, user_index: int):

    sql = 'SELECT ban_count FROM public."user" WHERE index = $1'

    return await conn.fetchval(sql, user_index)