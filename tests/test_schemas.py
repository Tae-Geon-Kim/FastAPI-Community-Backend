# test_schemas.py : 입력 데이터가 서버가 정한 규격에 맞는지만 확인
import pytest
from pydantic import ValidationError

from app.schemas.user import UserLogin, ModiId, ModiPw
from app.schemas.boards import CreateBoard, ModiTitle, ModiContent, DeleteBoards
from app.schemas.files import DeleteFile


'''
 -schemas/user.py 에서 test 해야되는 schema
    -UserLogin
    -ModiId
    -ModiPw
'''
# ==========================================
# 1. 유저(User) 스키마 테스트
# ==========================================

# 유저 아이디: 영문 소문자, 숫자 포함한 5 ~ 20자
# 유저 비밀번호: 영문자, 숫자, 특수문자를 포함한 8 ~ 16자

# 정상적인 아이디와 비밀번호 (성공)
def test_user_login_valid():
    data = UserLogin(id="taegeon1111", password="Kim1234!!")
    assert data.id == "taegeon1111"
    assert data.password == "Kim1234!!"

# 아이디에 대문자가 포함된 경우
def test_userId_upper_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "TAeGeOn1111", password = "Kim1234!!")

# 아이디의 길이가 5보다 작은 경우
def test_userId_short_lenght_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "  tae1  ", password = "Kim1234!!") # strip 후 실제 입력 값은 tae1

# 아이디의 길이가 20보다 큰 경우
def test_userId_long_length_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "mynameiskimtaegeon001010", password = "Kim1234!!")

# 아이디에 특수문자가 포함된 경우
def test_userId_special_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "kim001010!!", password = "Kim1234!!")

# 비밀번호에 특수문자가 없는 경우
def test_userPw_noSpecial_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "taegeon1111", password = "Kim20001010")

# 비밀번호에 숫자가 없는 경우
def test_userPw_noNum_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "taegeon1111", password = "Kimtaegeon!!")

# 비빌번호의 길이가 8보다 작은 경우
def test_userPw_short_length_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "taegeon1111", password = "Kim1!")

# 비밀번호 길이가 16보다 큰 경우
def test_userPw_long_length_invalid():
    with pytest.raises(ValidationError):
        UserLogin(id = "taegeon1111", password = "MynameisKimTaeGeon20001010!!!!!")

# 아이디 변경 실패 (새로운 아이디 형식이 잘못 됐을 때)
def test_modiId_invalid_newId():
    with pytest.raises(ValidationError):
        ModiId(password = "Kim1234!!", new_id = "TaEgEoN11!?")

# 비밀번호 변경 실패 (새로운 비밀번호 형식이 잘못됐을 때)
def test_modiPw_invalid_new_pw():
    with pytest.raises(ValidationError):
        ModiPw(password = "Kim1234!!", new_password = "rlaxorjs12215536")

# 아아디 변경 성공 (입력한 new_id & password의 형식이 맞는지만 확인)
def test_modiId_valid():
    data = ModiId(password = "Kim1234!!", new_id = "rlaxorjs1111")
    assert data.new_id == "rlaxorjs1111"

# 비밀번호 변경 성공 (입력한 new_password & password의 형식이 맞는지만 확인)
def test_modiPw_valid():
    data = ModiPw(password = "Kim1234!!", new_password = "Kim001010!?")
    assert data.new_password == "Kim001010!?"


'''
-schemas/boards.py 에서 test 해야되는 schema
    -CreateBoard
    -ModiTitle
    -ModiContent
    -DeleteBoards (RestoreBoards의 schema 데이터는 DeleteBoards와 동일하기 때문에 하나만)
'''
# ==========================================
# 2. Boards 스키마 테스트
# ==========================================

# 게시판 제목: 2 ~ 50자 이내
# 게시판 내용: 30 ~ 2000자 이내

# 정상적인 게시판 제목 & 게시판 내용 - CreateBoard 성공
def test_create_board_valid():
    data = CreateBoard(
        title = "아스날 우승 실패",
        content = "아스날 우승 실패!!!" * 10
    )
    
# 게시판의 제목이 2보다 작은 경우
def test_board_title_short_invalid():
    with pytest.raises(ValidationError):
        CreateBoard(
            title = "  ",
            content = "아스날 우승 실패!!" * 15
        )

# 게시판의 제목이 50보다 큰 경우
def test_board_title_long_invalid():
    with pytest.raises(ValidationError):
        CreateBoard(
            title = "아스날 우승 실패" * 3,
            content = "아스날 우승 실패!!!" * 10
        )

# 게시판 내용이 30보다 작은 경우
def test_board_content_short_invalid():
    with pytest.raises(ValidationError):
        CreateBoard(
            title = "아스날 우승 실패",
            content = "아스날 우승 실패!!!"
        )

# 게시판 내용이 2000보다 큰 경우
def test_board_content_long_invalid():
    with pytest.raises(ValidationError):
        CreateBoard(
            title = "아스날 우승 실패" * 4,
            content = "아스날 우승 실패" * 1000
        )

# 게시판 제목 변경 실패 (잘못된 board_index 형식)
def test_modi_title_invalid_bindex():
    with pytest.raises(ValidationError):
        ModiTitle(
            board_index = -1,
            password = "Kim1234!!",
            new_title = "아스날 우승 실패"
        )

# 게시판 제목 변경 실패 (잘못된 new_title 형식)
def test_modi_title_invalid_new_title():
    with pytest.raises(ValidationError):
        ModiTitle(
            board_index = 1,
            password = "Kim1234!!",
            new_title = " "
        )

# 게시판 내용 변경 실패 (잘못된 board_index 형태)
def test_modi_content_invalid_bindex():
    with pytest.raises(ValidationError):
        ModiContent(
            board_index = 0,
            password = "Kim1234!!",
            new_content = "아스날 우승 실패 실패" * 20
        )

# 게시판 내용 변경 실패 (잘못된 new_content 형태)
def test_modi_content_invalid_new_content():
    with pytest.raises(ValidationError):
        ModiContent(
            board_index = 1,
            password = "Kim1234!!",
            new_content = "아스날 우승 실패 실패" * 1000
        )

# 게시판 제목 변경 성공
def test_modi_title_valid():
    data = ModiTitle(
        board_index = 1,
        password = "Kim1234!!",
        new_title = "아스날 우승 실패 실패 실패" * 2
    )

# 게시판 내용 변경 성공
def test_modi_content_valid():
    data = ModiContent(
        board_index = 3,
        password = "Kim1234!!",
        new_content = "아스날 우승 실패 실패 실패" * 10
    )

'''
-schemas/files.py 에서 test 해야되는 schema
    - DeleteFile (RestoreFile과 구조 동일)
    - DeleteAllFile (RestoreAllFile과 구조 동일)
    - password 형식 검증은 User 스키마에서 완료했으므로 여기서는 index 제약(gt=0)만 확인합니다.
'''
# ==========================================
# 3. Files 스키마 테스트
# ==========================================

# 정상적인 단일 파일 삭제/복구 요청
def test_delete_file_valid():
    data = DeleteFile(board_index=5, files_index=10, password="Kim1234!!")
    assert data.board_index == 5
    assert data.files_index == 10

# 단일 파일 삭제/복구 실패 (board_index가 0 이하일 때)
def test_delete_file_invalid_board_index():
    with pytest.raises(ValidationError):
        DeleteFile(board_index=0, files_index=10, password="Kim1234!!")

# 단일 파일 삭제/복구 실패 (files_index가 음수일 때)
def test_delete_file_invalid_files_index():
    with pytest.raises(ValidationError):
        DeleteFile(board_index=5, files_index=-1, password="Kim1234!!")

# 정상적인 전체 파일 삭제/복구 요청
def test_delete_all_file_valid():
    data = DeleteAllFile(board_index=5, password="Kim1234!!")
    assert data.board_index == 5
    # DeleteAllFile에는 files_index 속성이 없어야 정상
    assert not hasattr(data, 'files_index') 

# 전체 파일 삭제/복구 실패 (board_index가 0 이하일 때)
def test_delete_all_file_invalid_board_index():
    with pytest.raises(ValidationError):
        DeleteAllFile(board_index=-3, password="Kim1234!!")
