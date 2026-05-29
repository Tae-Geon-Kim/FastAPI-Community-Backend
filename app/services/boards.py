import json
import math
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from asyncpg import Connection
from fastapi import HTTPException, status
from app.models.user import get_user_id_pw, get_user_index
from app.models.audit_log import insert_audit_log
from app.core.security import verify
from app.db.redis_config import redis_db
from app.schemas.common import CommonResponse
from app.schemas.boards import (
    CreateBoard, BoardInfo, AllBoardInfo, AllBoardInfoResponse,
    ModiTitle, ModiContent, DeleteBoards, RestoreBoards
)
from app.models.boards import (
    insert_boards_db, pull_board_info_by_index, certain_user_boards_info,
    all_user_boards_info, check_boards_owner, title_modify, content_modify,
    soft_delete_board, delete_boards, check_deleted_boards_owner,
    restore_board, search_in_title_content, total_search_in_title_content,
    total_certain_user_boards_info, get_total_boards_num, update_view_count,
    get_popular_top5_board, insert_boards_view_info
)
from app.models.files import (
    soft_delete_all_board_files, delete_files, restore_all_board_files,
    get_total_fsize, update_total_fsize, restore_cascade_board_files,
)

def convert_mb(size_bytes: int) -> str:
    if size_bytes is None or size_bytes <= 0:
        return "0.00MB"
    return f"{(size_bytes / (1024 * 1024)):.2f}MB"

# 게시판 생성 - DB에 저장을 하고 게시판의 인덱스를 다시 받아온다.
async def create_boards_services(data: CreateBoard, conn: Connection, current_user: dict):

    async with conn.transaction():
        new_board_index = await insert_boards_db(conn, data.title, data.content, current_user['index'])
        await insert_audit_log(
            conn = conn,
            action = "CREATE",
            target_type = "BOARD",
            target_index = new_board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "title": data.title,
            }
        )

    return CommonResponse(
        message = "게시판이 생성되었습니다.",
        data = {"board_index": new_board_index}
    )

# 특정 게시글 1개 상세 조회 (조회수 로직 포함)
async def single_board_info_services(board_index: int, viewer_info: dict, conn: Connection, redis_client):

    board_data = await pull_board_info_by_index(conn, board_index)

    # 게시글이 존재하는지 먼저 확인
    if not board_data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "존재하지 않거나 삭제된 게시글입니다."
        )

    # redis key 생성
    if viewer_info.get("user_index"): # 로그인 유저
        redis_key = f"board_view:{board_index}:user:{viewer_info['user_index']}"
    else: # 비로그인 유저
        redis_key = f"board_view:{board_index}:anon:{viewer_info['anonymous_id']}"

    # 5분 안에 본 적 있는지 검사
    is_viewed = await redis_client.get(redis_key)

    # 처음 보거나 5분이 지난경우 (캐시에 없음)
    if not is_viewed:
        await insert_boards_view_info(conn, board_index, viewer_info['user_index'], viewer_info['anonymous_id'])

        # redis에 해당 IP가 viewed 라고 표시
        # 300초 지나면 자동으로 표시 초기화
        await redis_client.setex(redis_key, 300, "viewed")

    board_dict = dict(board_data)
    
    board_dict['total_file_size'] = convert_mb(board_dict.get("total_file_size", 0))

    if isinstance(board_dict.get('files'), str):
        board_dict['files'] = json.loads(board_dict['files'])
        for f in board_dict['files']:
            if 'file_size' in f:
                f['file_size'] = convert_mb(f['file_size'])

    return CommonResponse(
        message = "게시글 상세 조회에 성공하였습니다.",
        data = board_dict
    )

# 특정 사용자의 게시판 목록을 출력 (로그인 필요 없이 user의 id를 입력받아서)
async def certain_boards_info_services(user_id: str, page: int, limit: int, conn: Connection):

    offset = (page - 1) * limit

    # 입력받은 아이디로 유저의 인덱스 번호를 찾음
    target_user_index = await get_user_index(conn, user_id)

    # 해당 사용자가 존재하지 않거나 탈퇴한 경우
    if target_user_index is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"'{user_id}' 사용자가 존재하지 않거나 이미 탈퇴한 회원입니다."
        )
    
    total_boards = await total_certain_user_boards_info(conn, user_id)
    total_pages = math.ceil(total_boards / limit) if total_boards > 0 else 0

    # 해당 사용자가 존재 / 해당 사용자의 전체 게시글 fetch
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.
    rows = await certain_user_boards_info(conn, user_id, limit, offset)

    # 해당 사용자가 쓴 게시글이 없는 경우
    if not rows:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_id}님의 등록된 게시글이 존재하지않습니다."
        )
    
    board_list = []
    for row in rows:
        row_dict = dict(row)

        row_dict['total_file_size'] = convert_mb(row_dict.get("total_file_size", 0))

        if isinstance(row_dict.get('files'), str):
            row_dict['files'] = json.loads(row_dict['files'])

            for f in row_dict['files']:
                if 'file_size' in f:
                    f['file_size'] = convert_mb(f['file_size'])

        board_list.append(BoardInfo.model_validate(row_dict))
        # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
        # DB에서 가져온 모든 Record 객체를 각각 dict로 변환하여 리스트 형태로 반환

    return CommonResponse(
        message = f"{user_id}님의 게시판을 출력합니다.",
        data = {
            "result": board_list,
            "meta": {
                "total_boards": total_boards,
                "total_pages": total_pages,
                "current_page": page,
                "limit": limit
            }
        }
    )

# 전체 게시판을 출력 (사용자 별로 / 로그인 필요 없음)
async def all_boards_info_services(conn: Connection, page: int, limit: int):

    offset = (page - 1) * limit

    total_boards = await get_total_boards_num(conn)
    total_pages = math.ceil(total_boards / limit) if total_boards > 0 else 0

    rows = await all_user_boards_info(conn, limit, offset)
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.

    # boards 테이블에 게시판이 아예 하나도 존재하지 않을 때
    if not rows:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "등록된 게시글이 존재하지않습니다."
        )
    
    grouped_dict =defaultdict(list)
    # 빈 딕셔너리 생성

    for row in rows:
        row_dict = dict(row)
        author_id = row_dict['id']

        row_dict['total_file_size'] = convert_mb(row_dict.get('total_file_size', 0))

        if isinstance(row_dict.get('files'), str):
            row_dict['files'] = json.loads(row_dict['files'])

            for f in row_dict['files']:
                if 'file_size' in f:
                    f['file_size'] = convert_mb(f['file_size'])

        validate_post = AllBoardInfo.model_validate(row_dict)
        grouped_dict[author_id].append(validate_post)

    final_data = [
        AllBoardInfoResponse(id = name, posts = posts) 
        for name, posts in grouped_dict.items()
    ]

    return CommonResponse(
        message = "전체 게시글을 사용자별로 분류하여 출력합니다.",
        data = {
            "result": final_data,
            "meta": {
                "total_boards": total_boards,
                "total_pages": total_pages,
                "current_page": page,
                "limit": limit
            }
        }
    )

# 게시판 제목 수정
async def title_modify_services(board_index: int, data: ModiTitle, conn: Connection, current_user: dict):
    
    user_info = await get_user_id_pw(conn, current_user['index'])

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    boards_owner = await check_boards_owner(conn, board_index)

    if not boards_owner:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    if boards_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    async with conn.transaction():
        await title_modify(conn, data.new_title, board_index)
        await insert_audit_log(
            conn = conn,
            action = "MODIFY_TITLE",
            target_type = "BOARD",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "new_title": data.new_title,
            }
        )


    return CommonResponse(message = f"{user_info['id']}의 게시판 제목이 {data.new_title}로 변경되었습니다.")

# 게시판 내용 수정
async def content_modify_services(board_index: int, data: ModiContent, conn: Connection, current_user: dict):

    user_info = await get_user_id_pw(conn, current_user['index'])

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    boards_owner = await check_boards_owner(conn, board_index)

    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    if boards_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    async with conn.transaction():
        await content_modify(conn, data.new_content, board_index)
        await insert_audit_log(
            conn = conn,
            action = "MODIFY_CONTENT",
            target_type = "BOARD",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "new_content_preview": data.new_content[:50] + "..." 
            }
        )


    return CommonResponse(message = f"{user_info['id']}님의 게시판 내용이 변경되었습니다.")

# 게시판 삭제 (soft delete)
async def boards_delete_services(board_index: int, data: DeleteBoards, conn: Connection, current_user: dict):
    
    user_info = await get_user_id_pw(conn, current_user['index'])

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )
    
    boards_owner = await check_boards_owner(conn, board_index)

    # 해당 User가 작성한 글이 존재하는지 확인
    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    # 삭제할려는 글의 User와 로그인한 User가 동일한 인물인지 확인
    if boards_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    # soft delete
    async with conn.transaction():
        await soft_delete_board(conn, "USER", board_index)
        await soft_delete_all_board_files(conn, "BOARD_CASCADE", board_index) 
        # board가 삭제 때문에 file이 삭제되는 경우는 BOARD_CASCADE 로 표시
        await insert_audit_log(
            conn = conn,
            action = "DELETE",
            target_type = "BOARD",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청에 의한 삭제 (soft delete)"
            }
        )

    return CommonResponse(message = f"{user_info['id']}님의 요청하신 삭제 요청이 성공적으로 처리되었습니다.")

# 게시판 스케줄러 삭제 (ADMIN이 ADMIN_SCHEDULED 옵션으로 지운 데이터만 해당)
async def delete_boards_perman(pool):

    async with pool.acquire() as conn:
        await delete_boards(conn)
        await delete_files(conn)

# 게시판 삭제 데이터 복구 로직
async def restore_board_services(board_index: int, data: RestoreBoards, conn: Connection, current_user: dict):

    user_info = await get_user_id_pw(conn, current_user['index'])

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    restore_boards_owner = await check_deleted_boards_owner(conn, board_index)

    if restore_boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"요청하신 {board_index}번 게시판은 존재하지않거나, 복구 대상(삭제 상태)이 아닙니다."
        )
    
    if restore_boards_owner['user_index'] != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    time_diff = datetime.now(timezone.utc) - restore_boards_owner['deleted_at'].replace(tzinfo = timezone.utc)

    if time_diff > timedelta(days = 30):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = f"삭제 처리를 한지 30일이 경과하여 {board_index}번 게시물을 복구 시킬 수 없습니다."
        )

    if restore_boards_owner['deleted_by'] != "USER":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "관리자에 의해 삭제 처리된 게시판을 일반 유저가 임의로 복구시킬 수 없습니다."
        )
    
    async with conn.transaction():
        await restore_board(conn, board_index) # 게시판 데이터 복구
        await restore_cascade_board_files(conn, board_index, 30) # 게시판 삭제로 인해서 삭제된 파일들만 복구 - BOARD_CASCADE
        new_total_fsize = await get_total_fsize(conn, board_index) # 파일들 복구되었으면 파일 용량 재계산
        await update_total_fsize(conn, new_total_fsize, board_index) # 재계산된 용량 DB 업로드
        await insert_audit_log(
            conn = conn,
            action = "RESTORE",
            target_type = "BOARD",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청에 의한 복구"
            }
        )

    return CommonResponse(message = f"{user_info['id']}님이 요청하신 게시판이 복구되었습니다.")


# 게시판 검색 (제목 + 내용)
async def search_in_title_content_services(search_keyword: str, page: int, limit: int, conn: Connection):

    offset = (page - 1) * limit

    total_boards = await total_search_in_title_content(conn, search_keyword) 
    total_pages = math.ceil(total_boards / limit) if total_boards > 0 else 0

    search_result = await search_in_title_content(conn, search_keyword, limit, offset)

    if not search_result:
        return CommonResponse(
            message = f"{search_keyword}에 대한 검색결과가 존재하지않습니다.",
            data = {
                "result": [],
                "meta": {
                    "total_boards": 0,
                    "total_pages": 0,
                    "current_page": page,
                    "limit": limit
                }
            }
        )

    formatted_search_result = [dict(row) for row in search_result]

    return CommonResponse(
        message = f"{search_keyword}에 대한 검색이 성공적으로 조회되었습니다.",
        data = {
            "result": formatted_search_result,
            "meta": {
                "total_boards": total_boards,
                "total_pages": total_pages,
                "current_page": page,
                "limit": limit
            }
        }
    )

# 인기게시글 설정
async def get_popular_board_services(period: str, conn: Connection, redis_client):

    if period == "all":
        time_condition = ""
        period_output = "전체기간"
    elif period == "weekly":
        time_condition = "AND reg_date >= NOW() - INTERVAL '7 days'"
        period_output = "주간"
    elif period == "month":
        time_condition = "AND reg_date >= NOW() - INTERVAL '30 days'"
        period_output = "월간"
    else:
        return CommonResponse(
            success = False,
            message = "잘못된 입력입니다. period(조회기간)는 all, weekly, month만 가능합니다."
        )
    
    redis_key = f"popular_boards: {period}"

    cache_data = await redis_client.get(redis_key)

    if cache_data:
        result = json.loads(cahce_data)
        return CommonResponse(
            message = f"{period_output} 인기글 조회에 성공하였습니다.",
            data = result
        )

    rows = await get_popular_top5_board(conn, time_condition)
    result = [dict(row) for row in rows]

    # 전체 게시글이 단 한개도 존재하지 않는 경우
    if not result:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "전체 게시판에 등록된 게시글이 존재하지 않습니다."
        )

    await redis_client.setex(redis_key, 600, json.dumps(result))

    return CommonResponse(
        message = f"{period_output} 인기글 조회에 성공하였습니다.",
        data = result
    )