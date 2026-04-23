import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기로 실행하도록 설정
pytestmark = pytest.mark.asyncio

"""
    - 아이디 제약 조건: 영문자, 숫자가 무조건 1개 이상은 포함된 5 ~ 30자 (특수문자는 선택사항)
	- 비밀번호 제약 조건: 영문자, 숫자, 특수문자가 무조건 1개 이상은 포함된 8 ~ 30자

    ( 허용되는 특수문자 :     @$!%*#?&._-     )
"""

# 테스트 데이터
TEST_USER_ID = "taegeon1111"
TEST_USER_PW = "Kim1234!!"

NEW_USER_ID = "newtaegeon11"
NEW_USER_PW = "Kim3276!!!"

# ==========================================
# 정상 작동 통합 테스트
# ==========================================
async def test_user_integration_scenario(client: AsyncClient):

    # 1. 아이디 중복 확인 (GET /users/check-id/{user_id})
    check_res = await client.get(f"/users/check-id/{TEST_USER_ID}")
    assert check_res.status_code == 200

    # 2. 회원가입 테스트 (POST /users)
    signup_res = await client.post("/users", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert signup_res.status_code == 201

    # 3. 로그인 및 토큰 발급 테스트 (POST /users/login)
    login_res = await client.post("/users/login", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert login_res.status_code == 201
    
    access_token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 4. 로그인한 사용자 정보 조회 (GET /users/me)
    info_res = await client.get("/users/me", headers=headers)
    assert info_res.status_code == 200
    assert info_res.json()["data"]["id"] == TEST_USER_ID

    # 5. 아이디 변경 테스트 (PATCH /users/me/id)
    id_mod_res = await client.patch("/users/me/id", headers=headers, json={"password": TEST_USER_PW, "new_id": NEW_USER_ID})
    assert id_mod_res.status_code == 200

    # 6. 비밀번호 변경 테스트 (PATCH /users/me/password)
    pw_mod_res = await client.patch("/users/me/password", headers=headers, json={"password": TEST_USER_PW, "new_password": NEW_USER_PW})
    assert pw_mod_res.status_code == 200

    # 7. 회원 탈퇴 테스트 (DELETE /users/me)
    withdraw_res = await client.request("DELETE", "/users/me", headers=headers, json={"password": NEW_USER_PW})
    
    assert withdraw_res.status_code == 200

    # 8. 회원 탈퇴 복구 테스트 (POST /users/me/restore)
    restore_res = await client.post("/users/me/restore", json={"id": NEW_USER_ID, "password": NEW_USER_PW})
    assert restore_res.status_code == 200
    
    print("\n[성공] 정상 라이프사이클(가입~복구) 테스트 완료")


# ==========================================
# 예외 테스트: 중복 아이디 가입 방어 - 409 ERROR
# ==========================================
async def test_duplicate_id_check(client: AsyncClient):

    DUP_ID = "rlaxorjs20905"
    DUP_PW = "Kim3276!?"

    # 최초 가입
    first_signup = await client.post("/users", json={"id": DUP_ID, "password": DUP_PW})
    assert first_signup.status_code == 201

    # 똑같은 아이디로 중복 확인 시도
    check_res = await client.get(f"/users/check-id/{DUP_ID}")
    assert check_res.status_code == 409
    assert "이미 사용중인 아이디입니다" in check_res.json()["detail"]

    # 똑같은 아이디로 회원가입 재시도
    second_signup = await client.post("/users", json={"id": DUP_ID, "password": DUP_PW})
    assert second_signup.status_code == 409
    
    print("\n[성공] 중복 가입 409 에러 방어 완료")


# ==========================================
# 예외 테스트: 잘못된 비밀번호 로그인 방어 - 401 ERROR
# ==========================================
async def test_login_wrong_password(client: AsyncClient):

    LOGIN_ID = "rlaxorjs20905"
    REAL_PW = "Kim3276!?"
    WRONG_PW = "Gim3276?!"

    # 정상 가입
    await client.post("/users", json={"id": LOGIN_ID, "password": REAL_PW})

    # 틀린 비밀번호로 로그인 시도
    login_res = await client.post("/users/login", json={"id": LOGIN_ID, "password": WRONG_PW})
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]
    
    print("\n[성공] 잘못된 비밀번호 로그인 401 에러 방어 완료")


# ==========================================
# 예외 테스트: 토큰 없이 보호된 API 접근
# ==========================================
async def test_access_without_token(client: AsyncClient):

    info_res = await client.get("/users/me")
    
    assert info_res.status_code == 401
    assert "Not authenticated" in info_res.json()["detail"]


# ==========================================
# 예외 테스트: 존재하지 않는 아이디 로그인
# ==========================================
async def test_login_nonexistent_user(client: AsyncClient):

    login_res = await client.post(
        "/users/login", 
        json={"id": "ghost_user123", "password": "Ghost1234!!"}
    )
    
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]


# ==========================================
# 예외 테스트: 남이 쓰는 아이디로 변경 시도 - 409 ERROR
# ==========================================
async def test_id_modify_duplicate_conflict(client: AsyncClient):
 
    USER1_ID, USER1_PW = "first_user11!!", "User1111!!"
    USER2_ID, USER2_PW = "second_user22!!", "User2222!!"

    # 유저 1, 2 모두 가입
    await client.post("/users", json={"id": USER1_ID, "password": USER1_PW})
    await client.post("/users", json={"id": USER2_ID, "password": USER2_PW})

    # 유저 1로 로그인하여 토큰 획득
    login_res = await client.post("/users/login", json={"id": USER1_ID, "password": USER1_PW})
    headers = {"Authorization": f"Bearer {login_res.json()['data']['access_token']}"}

    # 유저 1이 본인의 아이디를 유저 2의 아이디(second_user22!!)로 변경
    mod_res = await client.patch(
        "/users/me/id",
        headers=headers,
        json={"password": USER1_PW, "new_id": USER2_ID}
    )
    
    assert mod_res.status_code == 409
    assert "중복되는 아이디가 존재합니다" in mod_res.json()["detail"]

# ==========================================
# 예외 테스트: 회원탈퇴 시 비밀번호 불일치 - 401 ERROR
# ==========================================
async def test_withdraw_wrong_password(client: AsyncClient):

    TARGET_ID = "rlaxorjs20905"
    REAL_PW = "Kim9804!!"
    WRONG_PW = "Gim3276!?"

    # 가입 및 로그인
    await client.post("/users", json={"id": TARGET_ID, "password": REAL_PW})
    login_res = await client.post("/users/login", json={"id": TARGET_ID, "password": REAL_PW})
    headers = {"Authorization": f"Bearer {login_res.json()['data']['access_token']}"}

    # 틀린 비밀번호로 회원탈퇴 시도
    withdraw_res = await client.request(
        "DELETE",
        "/users/me",
        headers=headers,
        json={"password": WRONG_PW}
    )
    
    assert withdraw_res.status_code == 401
    assert "비밀번호가 일치하지 않습니다" in withdraw_res.json()["detail"]