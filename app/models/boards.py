from asyncpg import Connection

# ========== 확인 / 검증 ==========

# 삭제처리가 안된 게시물 중 특정 게시판이 존재하는지 확인
async def check_undeleted_boards_exist(conn: Connection, board_index: int):
    
    sql = 'SELECT index FROM boards WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, board_index)

# 삭제처리와 무관하게 전체 게시물 중 특정 게시판이 존재하는지 확인
async def check_boards_exist(conn: Connection, board_index: int):

    sql = 'SELECT index FROM boards WHERE index = $1'

    return await conn.fetchval(sql, board_index)

# 삭제처리되지 않은 게시판 중에서 게시판의 작성자를 확인
async def check_boards_owner(conn: Connection, board_index: int):

    sql = 'SELECT user_index FROM boards WHERE index = $1 AND deleted_at IS NULL'

    return await conn.fetchval(sql, board_index)

# 삭제처리된 게시판의 user_index, deleted_at, deleted_by 값을 가져온디.
async def check_deleted_boards_owner(conn: Connection, board_index: int):

    sql = 'SELECT user_index, deleted_at, deleted_by FROM boards WHERE index = $1 AND deleted_at IS NOT NULL'
    
    return await conn.fetchrow(sql, board_index)


# ========== 삽입 ==========

# 게시글 저장 및 해당 게시글의 인덱스를 반환
async def insert_boards_db(
    conn: Connection,
    title: str,
    content: str,
    user_index: int,
    category: str = 'GENERAL'
):
    sql = 'INSERT INTO boards (title, content, category, user_index) VALUES ($1, $2, $3, $4) RETURNING index;'

    return await conn.fetchval(sql, title, content, category, user_index)


# ========== 조회 ==========

# 모든 유저의 게시판 정보 조회
async def all_user_boards_info(conn: Connection, limit: int, offset: int):

    sql = """
        WITH TargetBoards AS (
            SELECT b.index
            FROM boards b
            INNER JOIN "user" u ON b.user_index = u.index
            WHERE b.deleted_at IS NULL
            ORDER BY u.id ASC, b.index DESC
            LIMIT $1 OFFSET $2
        )
        SELECT
            b.index,
            b.category,
            b.title,
            b.reg_date,
            b.update_date,
            b.total_file_size,

            CASE WHEN u.deleted_at IS NOT NULL THEN '탈퇴한 사용자' ELSE u.id END AS id,

            COALESCE(
                (SELECT json_agg(json_build_object(
                    'index', f.index,
                    'original_name', f.original_name,
                    'file_size', f.file_size,
                    'reg_date', f.reg_date
                ))
                FROM files as f
                WHERE f.board_index = b.index
                AND f.deleted_at IS NULL),
                '[]'::json
            ) AS files
            
        FROM TargetBoards tb
        INNER JOIN boards b ON tb.index = b.index
        INNER JOIN "user" u ON b.user_index = u.index
        ORDER BY u.id ASC, b.index DESC
    """ 
    # ORDER BY u.id ASC : 사용자 아이디를 가나나 / ABC 순으로
    # ORDER BY b.index DESC : 게시글 중 가장 번호가 큰 글 (최신) 위로 정렬
    # ASC: 오름차순
    # DESC: 내림차순

    return await conn.fetch(sql, limit, offset)

# 특정 유저의 게시판 정보 조회 (INNER JOIN)
async def certain_user_boards_info(conn: Connection, user_id: str, limit: int, offset: int):

    sql = """
        SELECT
            b.index,
            b.category,
            b.title,
            b.content,
            b.reg_date,
            b.update_date,
            b.total_file_size,

            CASE WHEN u.deleted_at IS NOT NULL THEN '탈퇴한 사용자' ELSE u.id END AS id,

            COALESCE(
            (SELECT json_agg(json_build_object (
                'index', f.index,
                'original_name', f.original_name,
                'file_size', f.file_size,
                'reg_date', f.reg_date
                ))
                FROM files as f
                WHERE f.board_index = b.index
                AND f.deleted_at IS NULL),
                '[]'::json
                ) AS files
            FROM boards AS b
            INNER JOIN "user" AS u ON b.user_index = u.index
            WHERE u.id = $1
                AND b.deleted_at IS NULL
            ORDER BY b.index DESC
            LIMIT $2 OFFSET $3
    """
    # ORDER BY b.index DESC : 가장 최근에 쓴 글 (가장 큰 번호)이 가장 위로 

    return await conn.fetch(sql, user_id, limit, offset)

# 특정 게시글 1개 상세 조회
async def pull_board_info_by_index(conn: Connection, board_index: int):
    sql = """
        SELECT
            b.index,
            b.category,
            b.title,
            b.content,
            b.reg_date,
            b.update_date,
            b.total_file_size,
            b.view_count,

            CASE WHEN u.deleted_at IS NOT NULL THEN '탈퇴한 사용자' ELSE u.id END AS id,

            COALESCE(
                (SELECT json_agg(json_build_object (
                    'index', f.index,
                    'original_name', f.original_name,
                    'file_size', f.file_size,
                    'reg_date', f.reg_date,
                    'deleted_at', f.deleted_at
                ))
                FROM files as f
                WHERE f.board_index = b.index),
                '[]'::json
            ) AS files
        FROM boards AS b
        INNER JOIN "user" AS u ON b.user_index = u.index
        WHERE b.index = $1 
            AND b.deleted_at IS NULL 
    """
    return await conn.fetchrow(sql, board_index)

# 게시판 제목 + 게시판 내용 통합 검색 조회 (content 는 가져올 때 다 가져오지말고 처음의 100자만)
async def search_in_title_content(conn: Connection, search_keyword: str, limit: int, offset: int):

    sql = """
        SELECT index, category, title, view_count, reg_date, 
               LEFT(content, 100) || '...' AS content_preview
        FROM boards 
        WHERE (title ILIKE '%' || $1 || '%' OR content ILIKE '%' || $1 || '%')
        AND deleted_at IS NULL
        ORDER BY reg_date DESC
        LIMIT $2 OFFSET $3;
    """

    return await conn.fetch(sql, search_keyword, limit, offset)

# 게시글에서 조회수를 기준으로 TOP5 가져오기 (전체 기간 / 최근 7일 / 최근 30일 기준) - 공지사항 게시글은 제외
async def get_popular_top5_board(conn: Connection, time_condition: str):

    sql = f"""
        WITH Top5_List AS (
            SELECT
                index, title, content, view_count, category, reg_date,
                ROW_NUMBER() OVER (ORDER BY view_count DESC, index DESC) as ranking
            FROM boards
            WHERE deleted_at IS NULL
            AND category != 'NOTICE' 
            {time_condition}
        )
        SELECT * FROM Top5_List
        WHERE ranking <= 5;
    """

    return await conn.fetch(sql)


# ========== 개수 확인 ==========

# 전체 게시판 숫자
async def get_total_boards_num(conn: Connection):

    sql = 'SELECT COUNT(*) from boards WHERE deleted_at IS NULL'
    
    return await conn.fetchval(sql)

# 특정 유저의 게시판 조회로 조회된 총 게시물 개수
async def total_certain_user_boards_info(conn: Connection, user_id: str):

    sql = """
        SELECT COUNT(*)
        FROM boards AS b
        INNER JOIN "user" AS u ON b.user_index = u.index
        WHERE u.id = $1
            AND b.deleted_at IS NULL
    """

    return await conn.fetchval(sql, user_id)

# 게시판 제목 + 내용 통합 검색으로 조회된 총 게시물 개수
async def total_search_in_title_content(conn: Connection, search_keyword: str):

    sql = """
        SELECT COUNT(*) from boards
        WHERE (title ILIKE '%' || $1 || '%' OR content ILIKE '%' || $1 || '%')
        AND deleted_at IS NULL
    """

    return await conn.fetchval(sql, search_keyword)

# ========== 수정 ==========

# 게시판 제목 변경
async def title_modify(conn: Connection, new_title: str, board_index: int):

    sql = 'UPDATE boards SET title = $1, update_date = NOW() WHERE index = $2'

    return await conn.execute(sql, new_title, board_index)

# 게시판 내용 변경
async def content_modify(conn: Connection, new_content: str, board_index: int):

    sql = 'UPDATE boards SET content = $1, update_date = NOW() WHERE index = $2'

    return await conn.execute(sql, new_content, board_index)


# ========== 삭제 ==========

# 게시판 하나 삭제 처리 (soft delete)
async def soft_delete_board(conn: Connection, deleted_by: str, boards_index: int):

    sql = 'UPDATE boards SET deleted_by = $1, deleted_at = NOW(), update_date = NOW() WHERE index = $2'

    return await conn.execute(sql, deleted_by, boards_index)

# 특정 유저의 게시판 전체를 삭제 처리 (soft delete)
async def soft_delete_all_user_boards(conn: Connection, deleted_by: str, user_index: int):
    
    sql = """
        UPDATE boards
            SET deleted_by = $1, deleted_at = NOW(), update_date = NOW()
            WHERE user_index = $2 AND deleted_at IS NULL
    """

    return await conn.execute(sql, deleted_by, user_index)

# 삭제 처리된 게시물 100일 지난 경우 실제 삭제 (ADMIN인 경우에만 허용)
async def delete_boards(conn: Connection):

    sql = """
        DELETE FROM boards
        WHERE deleted_by = 'ADMIN_SCHEDULED' AND deleted_at IS NOT NULL
        AND deleted_at <= NOW() - INTERVAL '100 days'
    """

    return await conn.execute(sql)

# 게시판 하나 실제 삭제 (hard delete)
async def hard_delete_board(conn: Connection, board_index: int):

    sql = 'DELETE FROM boards WHERE index = $1'

    return await conn.execute(sql, board_index)

# 특정 유저의 게시판 전체를 실제 삭제 (hard delete)
async def hard_delete_all_user_boards(conn: Connection, user_index: int):

    sql = 'DELETE FROM boards WHERE user_index = $1'

    return await conn.execute(sql, user_index)


# ========== 복구 ==========

# soft delete된 게시판 하나의 데이터를 복구
async def restore_board(conn: Connection, board_index: int):

    sql = 'UPDATE boards SET deleted_at = NULL, deleted_by = NULL, update_date = NOW() WHERE index =  $1'

    return await conn.execute(sql, board_index)

# 사용자 회원탈퇴 복구 (해당 유저의 모든 게시판)
async def restore_all_user_boards(conn: Connection, user_index: int):

    sql = """
        UPDATE boards SET deleted_at = NULL, deleted_by = NULL, update_date = NOW()
        WHERE user_index = $1 AND deleted_at IS NOT NULL
    """

    return await conn.execute(sql, user_index)


# ========== 조회수 / 용량 ==========

# 게시글 조회수 1 증가
async def update_view_count(conn: Connection, board_index: int):

    sql = 'UPDATE boards SET view_count = view_count + 1 WHERE index = $1'

    return await conn.execute(sql, board_index)

# boards_view 테이블에 누가 특정 게시물을 봤는지 기록
async def insert_boards_view_info(conn: Connection, board_index: int, user_index: int, anonymous_id: str):

    sql = 'INSERT INTO boards_view(board_index, user_index, anonymous_id) VALUES ($1, $2, $3);'

    return await conn.execute(sql, board_index, user_index, anonymous_id)

# 파일 추가, 삭제로 인해 변동된 특정 게시판의 총 파일 용량 업데이트
async def update_total_board_fsize(conn: Connection, total_file_size: int, board_index: int):

    sql = 'UPDATE boards SET total_file_size = $1, update_date = NOW() WHERE index = $2'
    
    return await conn.execute(sql, total_file_size, board_index)

# 특정 유저의 모든 게시판의 용량을 특정 값으로 업데이트
async def update_all_user_boards_total_fsize(conn: Connection, total_file_size: int, user_index: int):

    sql = """
        UPDATE boards 
        SET total_file_size = $1, update_date = NOW() 
        WHERE user_index = $2
        AND deleted_at IS NULL
    """

    return await conn.execute(sql, total_file_size, user_index)

# 특정 유저의 모든 게시판의 총 용량을 재계산하여 업데이트
async def recalculate_all_user_boards_total_fsize(conn: Connection, user_index: int):

    sql = """
        UPDATE boards
        SET total_file_size = COALESCE((
            SELECT SUM(file_size)
            FROM files
            WHERE files.board_index = boards.index 
            AND files.deleted_at IS NULL
        ), 0)
        WHERE user_index = $1;
    """

    return await conn.execute(sql, user_index)