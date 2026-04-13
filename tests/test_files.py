import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기(async)로 실행하도록 설정
pytestmark = pytest.mark.asyncio

# 테스트에 사용할 가짜 데이터
TEST_USER_ID = "filetestuser"
TEST_USER_PW = "File1234!!"
TEST_TITLE = "파일 업로드 테스트 게시판"
TEST_CONTENT = "파일이 잘 올라가는지 확인합니다."

# ==========================================
# 유저 가입 / 로그인 및 테스트용 게시판 생성 헬퍼 함수
# ==========================================
async def setup_user_and_board(client: AsyncClient, user_id, user_pw):
# 유저 생성 & 해당 유저 이름으로 게시판 생성 & 헤더 / 게시판 번호 반환
  
    # 유저 가입 및 로그인
    await client.post("/uRegister", json={"id": user_id, "password": user_pw})
    login_res = await client.post("/login", json={"id": user_id, "password": user_pw})
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 게시판 생성
    await client.post("/bRegister", headers=headers, json={"title": TEST_TITLE, "content": TEST_CONTENT})
    
    # 방금 만든 게시판 번호 가져오기
    board_res = await client.get(f"/certainBInfo?user_id={user_id}")
    board_index = board_res.json()["data"][0]["board_index"]
    
    return headers, board_index

# ==========================================
# 파일 인덱스 조회 헬퍼 함수
# ==========================================
async def get_latest_file_index(client: AsyncClient, user_id):

    """가장 최근 게시물에 업로드된 첫 번째 파일의 인덱스를 가져옵니다."""
    board_res = await client.get(f"/certainBInfo?user_id={user_id}")
    files_list = board_res.json()["data"][0].get("files", [])
    if files_list:
        return files_list[0]["index"]
    return None

# ==========================================
# 정상 작동 통합 테스트
# ==========================================
async def test_files_valid_case(client: AsyncClient):

    headers, board_index = await setup_user_and_board(client, TEST_USER_ID, TEST_USER_PW)

    # 파일 업로드 (/uploadFiles)
    dummy_file = {"file": ("test_doc.txt", b"Hello, this is a test file content!", "text/plain")}
    form_data = {"board_index": str(board_index)}  # Form 데이터는 문자열로 줘야 안전함
    
    upload_res = await client.post(
        "/uploadFiles", 
        headers=headers, 
        data=form_data, 
        files=dummy_file
    )
    assert upload_res.status_code == 200
    print("\n[성공] 단일 파일 업로드 완료")

    # 방금 올린 파일의 인덱스 번호 조회
    files_index = await get_latest_file_index(client, TEST_USER_ID)
    assert files_index is not None

    # 단일 파일 삭제 (/deleteFiles)
    del_res = await client.post(
        "/deleteFiles",
        headers=headers,
        json={"board_index": board_index, "files_index": files_index, "password": TEST_USER_PW}
    )
    assert del_res.status_code == 200

    # 단일 파일 복구 (/restoreFile)
    res_res = await client.post(
        "/restoreFile",
        headers=headers,
        json={"board_index": board_index, "files_index": files_index, "password": TEST_USER_PW}
    )
    assert res_res.status_code == 200

    # 파일 전체 삭제 (/deleteAll)
    del_all_res = await client.post(
        "/deleteAll",
        headers=headers,
        json={"board_index": board_index, "password": TEST_USER_PW}
    )
    assert del_all_res.status_code == 200

    # 파일 전체 복구 (/restoreAllFile)
    res_all_res = await client.post(
        "/restoreAllFile",
        headers=headers,
        json={"board_index": board_index, "password": TEST_USER_PW}
    )
    assert res_all_res.status_code == 200
    print("[성공] 파일 CRUD 정상 라이프사이클 완료")

# ==========================================
# 예외 처리: 허용되지 않는 확장자 업로드 시도
# ==========================================
async def test_upload_invalid_extension(client: AsyncClient):

    headers, board_index = await setup_user_and_board(client, TEST_USER_ID, TEST_USER_PW)
    
    # 악성 실행 파일 모방
    bad_file = {"file": ("virus.exe", b"malicious code", "application/x-msdownload")}
    
    upload_res = await client.post(
        "/uploadFiles", 
        headers=headers, 
        data={"board_index": str(board_index)}, 
        files=bad_file
    )
    assert upload_res.status_code == 415
    assert "허용되는 확장자가 아닙니다" in upload_res.json()["detail"]

# ==========================================
# 예외 처리: 타인의 게시판에 파일 업로드 시도
# ==========================================
async def test_upload_unauthorized_board(client: AsyncClient):

    # 유저 A와 게시판 세팅
    _, board_index_A = await setup_user_and_board(client, "userA111", TEST_USER_PW)
    
    # 유저 B 세팅 (게시판은 만들지 않고 헤더만 가져옴)
    headers_B, _ = await setup_user_and_board(client, "userB222", TEST_USER_PW)

    # B가 A의 게시판(board_index_A)에 업로드 시도
    dummy_file = {"file": ("sneaky.txt", b"I am user B", "text/plain")}
    
    upload_res = await client.post(
        "/uploadFiles", 
        headers=headers_B,  # B의 토큰
        data={"board_index": str(board_index_A)}, 
        files=dummy_file
    )
    
    assert upload_res.status_code == 403
    assert "본인의 게시글에만" in upload_res.json()["detail"]

# ==========================================
# 예외 처리: 삭제 시 비밀번호 틀림
# ==========================================
async def test_delete_file_wrong_password(client: AsyncClient):
    headers, board_index = await setup_user_and_board(client, TEST_USER_ID, TEST_USER_PW)
    
    # 정상 업로드
    await client.post(
        "/uploadFiles", headers=headers, 
        data={"board_index": str(board_index)}, 
        files={"file": ("test.txt", b"hello", "text/plain")}
    )
    files_index = await get_latest_file_index(client, TEST_USER_ID)

    # 틀린 비밀번호로 삭제 시도
    del_res = await client.post(
        "/deleteFiles",
        headers=headers,
        json={"board_index": board_index, "files_index": files_index, "password": "WrongPassword99!!"}
    )
    
    assert del_res.status_code == 401
    assert "비밀번호" in del_res.json()["detail"]