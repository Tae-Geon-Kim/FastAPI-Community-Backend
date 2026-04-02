from asyncpg import Connection
from fastapi import HTTPException, status
from collections import defaultdict
from app.schemas.boards import *
from app.models.boards import *
from app.models.user import id_duplicate
from app.models.files import soft_delete_all_file, delete_files
from app.schemas.user import UserId, UserLogin
from app.services.auth import login

async def create_boards_services(conn: Connection, data: CreateBoard):

    # 게시판 제목이 빈 문자열인 경우
    if not data.title.strip():
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "게시판 제목에는 빈 문자열을 사용할 수 없습니다."
        )

    # 게시판 내용이 빈 문자열인 경우
    if not data.content.strip():
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "게시판 내용에는 빈 문자열을 사용할 수 없습니다."
        )
    
    user_num = await login(conn, data)
    # 로그인 성공 시 user_num 에는 사용자의 index 가
    # 로그인 실패 시 None

    # 로그인에 실패한 경우
    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    # 게시판을 저장할 때 user_num도 같이 저장
    await insert_boards_db(conn, data.title, data.content, user_num)
    
    return CommonResponse(message = "게시판이 생성되었습니다.")

# 특정 사용자의 게시판 목록을 출력 (사용자의 이름 입력 받아서 있음 출력 아님 에러 / 로그인 필요 없음)
async def certain_boards_info_services(conn: Connection, data: UserId):

    user_exist = await id_duplicate(conn, data)

    # 해당 사용자가 존재 x
    if not user_exist:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "해당 사용자가 존재하지않습니다."
        )

    # 해당 사용자가 존재 / 해당 사용자의 전체 게시글 fetch
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.
    rows = await certain_user_boards_info(conn, data.id)

    # 해당 사용자가 쓴 게시글이 없는 경우
    if not rows:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다."
        )
    
    board_list = [BoardInfo.model_validate(dict(row)) for row in rows]
    # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
    # DB에서 가져온 모든 Record 객체를 각각 dict로 변환하여 리스트 형태로 반환

    return CommonResponse(message = f"{data.id}님의 게시판을 출력합니다.", data = board_list)

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
async def title_modify_services(conn: Connection, data: ModiTitle):

    user_num = await login(conn, UserLogin(id = data.id, password = data.password))

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    boards_owner = await check_boards_owner(conn, data.board_index)
    # check_boards_owner()는 fetchrow() --> fetchrow()는 Record 객체 반환

    if not boards_owner:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다."
        )
    
    # boards_owner는 {'user_index': 5} 같은 모양의 객체 --> 이걸 user_num(정수 5)과 직접 비교하면 항상 다르다고 판단
    # boards_owner['user_index'] 라고 해야한다.
    if boards_owner['user_index'] != user_num:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "본인의 게시글만 수정할 수 있습니다."
        )

    if not data.new_title.strip():
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "게시판 제목에는 빈 문자열을 사용할 수 없습니다."
        )

    await title_modify(conn, data.new_title, data.board_index)

    return CommonResponse(message = f"{data.id}의 게시판 제목이 {data.new_title}로 변경되었습니다.")

# 게시판 내용 수정
async def content_modify_services(conn: Connection, data: ModiContent):
    
    user_num = await login(conn, UserLogin(id = data.id, password = data.password))

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    boards_owner = await check_boards_owner(conn, data.board_index)

    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다."
        )

    if boards_owner['user_index'] != user_num:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "본인의 게시글만 수정할 수 있습니다."
        )
    
    if not data.new_content.strip():
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "게시판 내용에는 빈 문자열을 사용할 수 없습니다."
        )
    
    await content_modify(conn, data.new_content, data.board_index)

    return CommonResponse(message = f"{data.id}님의 게시판 내용이 변경되었습니다.")

# 게시판 삭제 (soft delete)
async def boards_delete_services(conn: Connection, data: DeleteBoards):

    # 사용자 로그인
    user_num = await login(conn, UserLogin(id = data.id, password = data.password))

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )
    
    boards_owner = await check_boards_owner(conn, data.board_index)

    # 해당 User가 작성한 글이 존재하는지 확인
    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다."
        )
    
    # 삭제하려 하는 글의 User와 로그인한 User가 동일한 인물인지 확인
    if boards_owner['user_index'] != user_num:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "본인의 게시글만 삭제할 수 있습니다."
        )

    async with conn.transaction():
        #  soft delete
        await soft_delete_boards(conn, data.board_index)
        await soft_delete_all_file(conn, data.board_index)

    return CommonResponse(message = f"{data.id}님의 요청하신 삭제 요청이 성공적으로 처리되었습니다.")

# 게시판 삭제 (실제 삭제)
async def delete_boards_perman(pool):

    async with pool.acquire() as conn:
        await delete_boards(conn)
        await delete_files(conn)