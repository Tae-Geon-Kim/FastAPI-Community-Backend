from fastapi import APIRouter, Depends, status, Path
from asyncpg import Connection
from app.schemas.boards import CreateBoard, ModiTitle, ModiContent, DeleteBoards, RestoreBoards
from app.schemas.user import UserLogin
from app.db.database import get_db
from app.core.security import get_current_user
from app.schemas.common import CommonResponse
from app.services.boards import (
    create_boards_services,
    certain_boards_info_services,
    single_board_info_services,
    all_boards_info_services,
    title_modify_services,
    content_modify_services,
    boards_delete_services,
    restore_board_services
)

router = APIRouter()
# 파일별로 API를 나누기 위해 APIRouter를 사용

# 특정 유저의 게시판 생성
@router.post(
    "",
    response_model = CommonResponse,
    status_code = status.HTTP_201_CREATED,
    summary = "[게시판] 새로운 게시판 생성",
    description = """
    새로운 게시판을 생성

    - 사용자에게 글 제목, 글 내용을 입력받아 JWT 토큰 로그인한 유저의 게시판 목록에 새로운 글 생성
    - 제목 제약조건: 2 ~ 50 자
    - 내용 제약조건: 30 ~ 2000자
    """
)
async def register_boards(
    data: CreateBoard,
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await create_boards_services(data, conn, current_user_num)

# 특정 유저의 게시판 조회
@router.get(
    "/users/{user_id}",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 특정 유저의 게시판 목록을 출력",
    description = """
    특정 유저의 게시판 목록을 출력

    - 사용자의 아이디를 입력받아 해당 유저의 게시판 정보를 출력
    - 허용되는 id 형식: 영문자, 숫자가 무조건 포함된 5 ~ 30자 (특수문자 허용)
    - 로그인 필요하지 않음.
    """
)
async def get_user_boards(
    user_id: str = Path(..., min_length = 5, max_length = 30, description = "조회할 유저의 아이디"),
    conn: Connection = Depends(get_db)
):
    return await certain_boards_info_services(user_id, conn)

 # 단건 게시글 조회
@router.get(
    "/{board_index}",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 특정 게시글 상세 조회",
    description = """
    특정 게시글 하나만 상세하게 조회합니다.

    - 게시글의 인덱스(board_index)를 입력받아 해당 글만 출력합니다.
    - 로그인 필요하지 않음.
    """
 )
async def get_board_detail(
    board_index: int = Path(..., gt = 0, description = "조회할 게시판의 인덱스 (게시판의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db)
):
    return await single_board_info_services(board_index, conn)

# 모든 유저의 게시판 조회
@router.get(
    "",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 전체 게시판 목록을 출력",
    description = """
    전체 게시판 목록을 출력

    - 전체 게시판 목록을 사용자에 따라 분류하여 출력
    - 로그인 필요하지 않음.
    """
)
async def get_all_boards(
    conn: Connection = Depends(get_db)
):
    return await all_boards_info_services(conn)

# 게시판 제목 변경
@router.patch(
    "/{board_index}/title",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 게시판 제목을 수정",
    description = """
    게시판 제목을 수정

    - 특정 게시판의 게시판 제목을 수정
    - 변경하는 제목도 제약조건 검증에 통과해야한다. (2 ~ 50자)
    - 제목을 변경하기 위해서 비밀번호를 다시 입력해야한다.
    """
)
async def update_board_title(
    data: ModiTitle,
    board_index: int = Path(..., gt = 0, description = "수정할 게시판의 인덱스 (게시판의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await title_modify_services(board_index, data, conn, current_user_num)

# 게시판 내용 변경
@router.patch(
    "/{board_index}/content",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 게시판 내용을 수정",
    description = """
    게시판 내용을 수정

    - 특정 게시판의 게시판 내용을 수정
    - 변경하는 게시판의 내용도 제약조건 검증을 통과해야한다. (30 ~ 2000자)
    - 게시판 내용을 변경하기 위해서 비밀번호를 다시 입력해야한다.
    """
)
async def update_content(
    data: ModiContent,
    board_index: int = Path(..., gt = 0, description = "수정할 게시판의 인덱스 (게시판의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await content_modify_services(board_index, data, conn, current_user_num)

# 게시판 삭제
@router.delete(
    "/{board_index}",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 게시판 삭제",
    description = """
    특정 게시판을 삭제 처리

    - 삭제하려는 게시판의 board_index를 입력받아 해당 게시판을 삭제 처리 (soft delete)
    - 특정 게시판을 삭제하면 해당 게시판에 존재하던 파일 데이터도 같이 삭제된다.
    - 삭제하기 위해서는 비밀번호를 다시 입력해야한다. 
    - 실제로 삭제처리되는 것은 스케줄링을 통해 자동으로 실행된다. (삭제처리 상태가 된지 3일이 지났으면 hard delete 된다.)
    """
)
async def delete_boards(
    data: DeleteBoards,
    board_index: int = Path(..., gt = 0, description = "삭제할 게시판의 인덱스 (게시판의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await boards_delete_services(board_index, data, conn, current_user_num)

# 게시판 복구
@router.post(
    "/{board_index}/restore",
    response_model = CommonResponse,
    status_code = status.HTTP_200_OK,
    summary = "[게시판] 게시판 데이터 복구",
    description = """
    삭제 처리된 사용자 데이터를 복구
    
    - 복구를 하기 위해서는 사용자 정보 비밀번호 재확인이 필요하다.
    - 복구시 특정 게시판에 존재하던 파일 데이터들도 같이 복구된다.
    - 복구는 soft delete된지 3일이내의 데이터만 가능하다.
    """
)

async def restore_boards(
    data: RestoreBoards,
    board_index: int = Path(..., gt = 0, description = "복구할 게시판의 인덱스 (게시판의 인덱스는 1이상이어야 합니다.)"),
    conn: Connection = Depends(get_db),
    current_user_num: str = Depends(get_current_user)
):
    return await restore_board_services(board_index, data, conn, current_user_num)