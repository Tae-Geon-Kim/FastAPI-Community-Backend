import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기(async)로 실행하도록 설정
pytestmark = pytest.mark.asyncio

# 테스트 데이터
TEST_USER_ID = "taegeon1111"
TEST_USER_PW = "Kim1234!!"
TEST_BOARDS_TITLE = "아스날 우승 실패" * 3
TEST_BOARDS_CONTENT = "아스날 우승 실패!!!" * 10
TEST_BOARDS_NEW_TITLE = "토트넘 강등" * 5
TEST_BOARDS_NEW_CONTENT = "토트넘 강등 위기!!!!!" * 100

# ==========================================
# 게시판 API 테스트를 위한 사용자 회원가입 헬퍼 함수
# ==========================================
async def setup_test_user(client: AsyncClient, test_userId, test_userPw):
    await client.post("/uRegister", json={"id": test_userId, "password": test_userPw})

    login_res = await client.post("/login", json={"id": test_userId, "password": test_userPw})
    token = login_res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# 정상 작동 통합 테스트
# ==========================================
async def test_boards_valid_case(client: AsyncClient):
    # 0. 유저 세팅 및 헤더 가져오기
    headers = await setup_test_user(client, TEST_USER_ID, TEST_USER_PW)

    # 1. 특정 유저의 게시판 생성
    create_res = await client.post(
        "/bRegister", 
        headers=headers,
        json={"title": TEST_BOARDS_TITLE, "content": TEST_BOARDS_CONTENT}
    )
    assert create_res.status_code in [200, 201]
    print("\n[성공] 게시판 생성 완료")

    # 2. 모든 게시판 조회 (/allBInfo)
    all_res = await client.get("/allBInfo")
    assert all_res.status_code == 200
    
    # 💡 그룹화된 데이터에서 글 번호 추출
    grouped_data = all_res.json().get("data", [])
    assert len(grouped_data) > 0
    first_author_posts = grouped_data[0]["posts"]
    target_board_index = first_author_posts[0]["board_index"]
    print(f"[성공] 조회된 게시글 번호: {target_board_index}")

    # 3. 특정 유저(아이디 기반)의 게시판 상세 조회 (/certainBInfo)
    # 💡 수정된 로직 반영: 헤더 없이 user_id만 쿼리로 전송
    certain_res = await client.get(f"/certainBInfo?user_id={TEST_USER_ID}")
    assert certain_res.status_code == 200
    print(f"[성공] {TEST_USER_ID}님의 게시글 목록 출력 완료")

    # 4. 게시판 제목 변경
    modi_title_res = await client.post(
        "/modiTitle",
        headers=headers,
        json={"board_index": target_board_index, "password": TEST_USER_PW, "new_title": TEST_BOARDS_NEW_TITLE}
    )
    assert modi_title_res.status_code == 200

    # 5. 게시판 내용 변경
    modi_content_res = await client.post(
        "/modiContent",
        headers=headers,
        json={"board_index": target_board_index, "password": TEST_USER_PW, "new_content": TEST_BOARDS_NEW_CONTENT}
    )
    assert modi_content_res.status_code == 200

    # 6. 게시판 삭제 (Soft Delete)
    del_res = await client.post(
        "/deleteBoards",
        headers=headers,
        json={"board_index": target_board_index, "password": TEST_USER_PW}
    )
    assert del_res.status_code == 200

    # 7. 게시판 복구
    restore_res = await client.post(
        "/restoreBoards",
        headers=headers,
        json={"board_index": target_board_index, "password": TEST_USER_PW}
    )
    assert restore_res.status_code == 200
    print("[성공] 게시판 CRUD 정상 라이프사이클 완료")


# ==========================================
# 예외 처리: 특정 유저 조회 시 유저가 없을 때
# ==========================================
async def test_certainInfo_noUser_conflict(client: AsyncClient):
    """DB에 존재하지 않는 아이디로 조회를 시도하면 404를 반환해야 함"""
    GHOST_ID = "ghost_user_9999"
    res = await client.get(f"/certainBInfo?user_id={GHOST_ID}")
    
    assert res.status_code == 404
    assert "존재하지 않거나" in res.json()["detail"]


# ==========================================
# 예외 처리: 모든 게시판 조회시 아무 글도 없을 때
# ==========================================
async def test_allBInfo_noUser_conflict(client: AsyncClient):
    """
    이 테스트 함수가 시작될 때는 DB가 롤백되어 완전히 텅 빈 상태임.
    따라서 전체 조회를 하면 404 에러가 나야 정상!
    """
    res = await client.get("/allBInfo")
    assert res.status_code == 404
    assert "존재하지않습니다" in res.json()["detail"]


# ==========================================
# 예외 처리: 타인의 게시판 수정 및 삭제 시도
# ==========================================
async def test_boards_unauthorized_access(client: AsyncClient):
    """A가 쓴 글을 B가 삭제하려고 할 때 403 에러가 나야 함"""
    # 유저 A와 유저 B 가입 및 헤더 획득
    headers_A = await setup_test_user(client, "userA111", TEST_USER_PW)
    headers_B = await setup_test_user(client, "userB222", TEST_USER_PW)

    # A가 글 작성
    await client.post("/bRegister", headers=headers_A, json={"title": "A title", "content": "A content"})
    
    # 생성된 글 번호 가져오기
    all_res = await client.get("/allBInfo")
    target_index = all_res.json()["data"][0]["posts"][0]["board_index"]

    # 🚨 B가 A의 글 삭제 시도 -> 403 Forbidden
    del_res = await client.post(
        "/deleteBoards",
        headers=headers_B,  # B의 토큰 사용!
        json={"board_index": target_index, "password": TEST_USER_PW}
    )
    assert del_res.status_code == 403
    assert "본인의 게시글만" in del_res.json()["detail"]


# ==========================================
# 예외 처리: 존재하지 않는 게시판 접근 시도
# ==========================================
async def test_boards_not_found(client: AsyncClient):
    """없는 글 번호로 제목 수정을 시도하면 404 에러가 나야 함"""
    headers = await setup_test_user(client, TEST_USER_ID, TEST_USER_PW)
    GHOST_INDEX = 99999

    modi_res = await client.post(
        "/modiTitle",
        headers=headers,
        json={"board_index": GHOST_INDEX, "password": TEST_USER_PW, "new_title": "유령 제목"}
    )
    assert modi_res.status_code == 404
    assert "존재하지않습니다" in modi_res.json()["detail"]


# ==========================================
# 예외 처리: 게시판 삭제 시 비밀번호가 불일치 할 때
# ==========================================
async def test_boards_wrong_password(client: AsyncClient):
    """비밀번호를 틀리게 입력하여 삭제를 시도하면 401 에러가 나야 함"""
    headers = await setup_test_user(client, TEST_USER_ID, TEST_USER_PW)
    
    # 글 작성
    await client.post("/bRegister", headers=headers, json={"title": TEST_BOARDS_TITLE, "content": TEST_BOARDS_CONTENT})
    all_res = await client.get("/allBInfo")
    target_index = all_res.json()["data"][0]["posts"][0]["board_index"]

    # 틀린 비밀번호로 삭제 시도
    del_res = await client.post(
        "/deleteBoards",
        headers=headers,
        json={"board_index": target_index, "password": "WrongPassword99!!"}
    )
    assert del_res.status_code == 401
    assert "비밀번호가 일치하지 않습니다" in del_res.json()["detail"]