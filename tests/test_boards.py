import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기로 실행하도록 설정
pytestmark = pytest.mark.asyncio

"""
    - 제목 제약 조건: 2 ~ 50자
    - 내용 제약 조건: 30 ~ 2000자
"""

# 테스트 데이터
TEST_USER_ID = "taegeon_1111"
TEST_USER_PW = "Kim1234!!"
TEST_BOARDS_TITLE = "아스날 우승 실패" * 3
TEST_BOARDS_CONTENT = "아스날 우승 실패!!!" * 10
TEST_BOARDS_NEW_TITLE = "토트넘 강등" * 5
TEST_BOARDS_NEW_CONTENT = "토트넘 강등 위기!!!!!" * 100

# ==========================================
# 게시판 API 테스트를 위한 사용자 회원가입 헬퍼 함수
# ==========================================
async def setup_test_user(client: AsyncClient, test_userId, test_userPw):

    await client.post("/users", json={"id": test_userId, "password": test_userPw})

    await client.post("/users/login", json={"id": test_userId, "password": test_userPw})

# ==========================================
# 정상 작동 통합 테스트
# ==========================================
async def test_boards_valid_case(client: AsyncClient):

    await setup_test_user(client, TEST_USER_ID, TEST_USER_PW)

    # 1. 특정 유저의 게시판 생성 (POST /boards)
    create_res = await client.post(
        "/boards", 
        json={"title": TEST_BOARDS_TITLE, "content": TEST_BOARDS_CONTENT}
    )
    assert create_res.status_code == 201 
    print("\n[성공] 게시판 생성 완료")

    # 2. 모든 게시판 조회 (GET /boards)
    all_res = await client.get("/boards")
    assert all_res.status_code == 200
    
    # 그룹화된 데이터에서 글 번호 추출
    grouped_data = all_res.json().get("data", [])
    assert len(grouped_data) > 0
    first_author_posts = grouped_data[0]["posts"]
    target_board_index = first_author_posts[0]["index"]
    print(f"[성공] 조회된 게시글 번호: {target_board_index}")

    # 3. 특정 게시글 단건 조회 (GET /boards/{board_index})
    detail_res = await client.get(f"/boards/{target_board_index}")
    assert detail_res.status_code == 200
    print(f"[성공] 단건 게시글 상세 조회 완료: {detail_res.json()['data']['title']}")

    # 4. 특정 유저의 게시판 리스트 조회 (GET /boards/users/{user_id})
    certain_res = await client.get(f"/boards/users/{TEST_USER_ID}")
    assert certain_res.status_code == 200
    print(f"[성공] {TEST_USER_ID}님의 게시글 목록 출력 완료")

    # 5. 게시판 제목 변경 (PATCH /boards/{board_index}/title)
    modi_title_res = await client.patch(
        f"/boards/{target_board_index}/title",
        json={"password": TEST_USER_PW, "new_title": TEST_BOARDS_NEW_TITLE}
    )
    assert modi_title_res.status_code == 200

    # 6. 게시판 내용 변경 (PATCH /boards/{board_index}/content)
    modi_content_res = await client.patch(
        f"/boards/{target_board_index}/content",
        json={"password": TEST_USER_PW, "new_content": TEST_BOARDS_NEW_CONTENT}
    )
    assert modi_content_res.status_code == 200

    # 7. 게시판 삭제 (DELETE /boards/{board_index})
    del_res = await client.request(
        "DELETE",
        f"/boards/{target_board_index}",
        json={"password": TEST_USER_PW}
    )
    assert del_res.status_code == 200

    # 8. 게시판 복구 (POST /boards/{board_index}/restore)
    restore_res = await client.post(
        f"/boards/{target_board_index}/restore",
        json={"password": TEST_USER_PW}
    )
    assert restore_res.status_code == 200
    print("[성공] 게시판 CRUD 정상 라이프사이클 완료")


# ==========================================
# 예외 처리: 특정 유저 조회 시 유저가 없을 때 - 404 ERROR
# ==========================================
async def test_certainInfo_noUser_conflict(client: AsyncClient):

    GHOST_ID = "ghost_user_9999"

    res = await client.get(f"/boards/users/{GHOST_ID}")
    
    assert res.status_code == 404
    assert "존재하지 않거나" in res.json()["detail"]


# ==========================================
# 예외 처리: 모든 게시판 조회시 아무 글도 없을 때 - 404 ERROR
# ==========================================
async def test_allBInfo_noUser_conflict(client: AsyncClient):

    res = await client.get("/boards")
    assert res.status_code in [200, 404] 


# ==========================================
# 예외 처리: 타인의 게시판 수정 및 삭제 시도 - 403 ERROR
# ==========================================
async def test_boards_unauthorized_access(client: AsyncClient):

    # A로 가입 & 로그인
    await setup_test_user(client, "userA111", TEST_USER_PW)

    # A 글 작성
    await client.post(
        "/boards",
        json = {
            "title": "A가 작성하는 글 제목입니다.",
            "content": "이 글은 A가 작성하는 글의 내용입니다. 글의 최소 길이는 30자 입니다."
        } 
    )

    all_res = await client.get("/boards")
    target_index = all_res.json()["data"][-1]["posts"][-1]["index"] # 맨 마지막에 생성된 글 인덱스

    # B로 가입 & 로그인
    await setup_test_user(client, "userB222", TEST_USER_PW)

    # B가 A의 글 삭제 시도 -> 403 Forbidden
    del_res = await client.request(
        "DELETE",
        f"/boards/{target_index}",
        json={"password": TEST_USER_PW}
    )
    assert del_res.status_code == 403
    assert "본인의 게시글만" in del_res.json()["detail"]


# ==========================================
# 예외 처리: 존재하지 않는 게시판 접근 시도 - 404 ERROR
# ==========================================
async def test_boards_not_found(client: AsyncClient):

    await setup_test_user(client, TEST_USER_ID, TEST_USER_PW)
    GHOST_INDEX = 99999

    detail_res = await client.get(f"/boards/{GHOST_INDEX}")
    assert detail_res.status_code == 404
    assert "존재하지 않거나 삭제된" in detail_res.json()["detail"]

    modi_res = await client.patch(
        f"/boards/{GHOST_INDEX}/title",
        json={"password": TEST_USER_PW, "new_title": "유령 제목 길게 적어야 통과함"}
    )
    assert modi_res.status_code == 404
    assert "존재하지않습니다" in modi_res.json()["detail"]


# ==========================================
# 예외 처리: 게시판 삭제 시 비밀번호가 불일치 할 때 - 401 ERROR
# ==========================================
async def test_boards_wrong_password(client: AsyncClient):

    await setup_test_user(client, TEST_USER_ID, TEST_USER_PW)
    
    # 글 작성
    await client.post("/boards", json={"title": TEST_BOARDS_TITLE, "content": TEST_BOARDS_CONTENT})
    all_res = await client.get("/boards")
    target_index = all_res.json()["data"][-1]["posts"][-1]["index"] # 맨 마지막 글

    # 틀린 비밀번호로 삭제 시도
    del_res = await client.request(
        "DELETE",
        f"/boards/{target_index}",
        json={"password": "WrongPassword99!!"}
    )
    assert del_res.status_code == 401
    assert "비밀번호가 일치하지 않습니다" in del_res.json()["detail"]