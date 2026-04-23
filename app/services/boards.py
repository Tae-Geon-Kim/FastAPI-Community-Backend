import json
from asyncpg import Connection
from fastapi import HTTPException, status
from collections import defaultdict
from app.schemas.boards import *
from app.models.boards import *
from app.models.user import id_duplicate, get_user_id_pw, get_user_index
from app.models.files import *
from app.schemas.user import UserId, UserLogin
from app.services.auth import login
from app.core.security import verify

def convert_mb(size_bytes: int) -> str:
    if size_bytes is None or size_bytes <= 0:
        return "0.00MB"
    return f"{(size_bytes / (1024 * 1024)):.2f}MB"

# 게시판 생성
async def create_boards_services(data: CreateBoard, conn: Connection, current_user_num: str):

    # 게시판을 저장할 때 user_num도 같이 저장
    await insert_boards_db(conn, data.title, data.content, int(current_user_num))
    
    return CommonResponse(message = "게시판이 생성되었습니다.")

# 특정 사용자의 게시판 목록을 출력 (로그인 필요 없이 user의 id를 입력받아서)
async def certain_boards_info_services(user_id: str, conn: Connection):
    
    # 입력받은 아이디로 유저의 인덱스 번호를 찾음
    target_user_index = await get_user_index(conn, user_id)

    # 해당 사용자가 존재하지 않거나 탈퇴한 경우
    if target_user_index is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"'{user_id}' 사용자가 존재하지 않거나 이미 탈퇴한 회원입니다."
        )

    # 해당 사용자가 존재 / 해당 사용자의 전체 게시글 fetch
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.
    rows = await certain_user_boards_info(conn, user_id)

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

    return CommonResponse(message = f"{user_id}님의 게시판을 출력합니다.", data = board_list)

# 전체 게시판을 출력 (사용자 별로 / 로그인 필요 없음)
async def all_boards_info_services(conn: Connection):

    rows = await all_user_boards_info(conn)
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
        author_id = row_dict['author']

        row_dict['total_file_size'] = convert_mb(row_dict.get('total_file_size', 0))

        if isinstance(row_dict.get('files'), str):
            row_dict['files'] = json.loads(row_dict['files'])

            for f in row_dict['files']:
                if 'file_size' in f:
                    f['file_size'] = convert_mb(f['file_size'])

        validate_post = AllBoardInfo.model_validate(row_dict)
        grouped_dict[author_id].append(validate_post)

    final_data = [
        AllBoardInfoResponse(author=name, posts=posts) 
        for name, posts in grouped_dict.items()
    ]
    
    return CommonResponse(
        message = "전체 게시글을 사용자별로 분류하여 출력합니다.",
        data = final_data
    )

# 게시판 제목 수정
async def title_modify_services(board_index: int, data: ModiTitle, conn: Connection, current_user_num: str):
    
    user_info = await get_user_id_pw(conn, int(current_user_num))

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    boards_owner = await check_boards_owner(conn, board_index)
    # check_boards_owner()는 fetchrow() --> fetchrow()는 Record 객체 반환

    if not boards_owner:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    # boards_owner는 {'user_index': 5} 같은 모양의 객체 --> 이걸 user_num(정수 5)과 직접 비교하면 항상 다르다고 판단
    # boards_owner['user_index'] 라고 해야한다.
    if boards_owner['user_index'] != int(current_user_num):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "본인의 게시글만 수정할 수 있습니다."
        )

    await title_modify(conn, data.new_title, board_index)

    return CommonResponse(message = f"{user_info['id']}의 게시판 제목이 {data.new_title}로 변경되었습니다.")

# 게시판 내용 수정
async def content_modify_services(board_index: int, data: ModiContent, conn: Connection, current_user_num: str):

    user_info = await get_user_id_pw(conn, int(current_user_num))

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

    if boards_owner['user_index'] != int(current_user_num):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "본인의 게시글만 수정할 수 있습니다."
        )
    
    await content_modify(conn, data.new_content, board_index)

    return CommonResponse(message = f"{user_info['id']}님의 게시판 내용이 변경되었습니다.")

# 게시판 삭제 (soft delete)
async def boards_delete_services(board_index: int, data: DeleteBoards, conn: Connection, current_user_num: str):
    
    user_info = await get_user_id_pw(conn, int(current_user_num))

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
    
    # 삭제하려 하는 글의 User와 로그인한 User가 동일한 인물인지 확인
    if boards_owner['user_index'] != int(current_user_num):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다. 본인의 게시글만 삭제할 수 있습니다."
        )

    async with conn.transaction():
        #  soft delete
        await soft_delete_boards(conn, board_index)
        await soft_delete_all_file(conn, board_index)

    return CommonResponse(message = f"{user_info['id']}님의 요청하신 삭제 요청이 성공적으로 처리되었습니다.")

# 게시판 삭제 (실제 삭제)
async def delete_boards_perman(pool):

    async with pool.acquire() as conn:
        await delete_boards(conn)
        await delete_files(conn)

# 게시판 삭제 데이터 복구 로직
async def restore_board_services(board_index: int, data: RestoreBoards, conn: Connection, current_user_num: str):

    user_info = await get_user_id_pw(conn, int(current_user_num))

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )
    
    restore_boards_owner = await check_restore_boards_owner(conn, board_index)

    if restore_boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"요청하신 {board_index}번 게시판은 존재하지않거나, 복구 대상(삭제 상태)이 아닙니다."
        )
    
    if restore_boards_owner != int(current_user_num):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail =  "권한이 없습니다. 본인의 게시글만 복구시킬 수 있습니다."
        )
    
    async with conn.transaction():
        await restore_board(conn, board_index) # 게시판 데이터 복구
        await restore_all_files(conn, board_index) # 게시판 내에 저장되어 있던 파일들이 있으면 파일들 일괄 복구
        new_total_fsize = await get_total_fsize(conn, board_index) # 파일들 복구되었으면 파일 용량 재계산
        await update_total_fsize(conn, new_total_fsize, board_index) # 재계산된 용량 DB 업로드

    return CommonResponse(message = f"{user_info['id']}님이 요청하신 게시판이 복구되었습니다.")