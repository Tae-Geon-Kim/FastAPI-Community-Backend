import pytest
from httpx import AsyncClient
from app.db.redis_config import redis_db

# 현재 파일의 모든 테스트 함수를 비동기로 실행하도록 설정
pytestmark = pytest.mark.asyncio

"""
    - 아이디 제약 조건: 영문자, 숫자가 무조건 1개 이상은 포함된 5 ~ 30자 (선택적으로 특수문자 사용 가능:    $!%*#?&._-     )
	- 비밀번호 제약 조건: 영문자, 숫자, 특수문자가 무조건 1개 이상은 포함된 8 ~ 30자 (허용되는 특수문자:    @$!%*#?&._-    )
"""

# 테스트 데이터
TEST_USER_ID = "taegeon1111"
TEST_USER_PW = "Kim1234!!"
TEST_USER_NAME = "김태건"
TEST_USER_EMAIL = "test123@test.com"

NEW_USER_ID = "newtaegeon11"
NEW_USER_PW = "Kim3276!!!"

# ==========================================
# 정상 작동 통합 테스트
# ==========================================
async def test_user_integration_scenario(client: AsyncClient):

    # 아이디 중복 확인 (POST /users/check-id)
    check_res = await client.post(
        "/users/check-id",
        json={"id": TEST_USER_ID}
    )
    assert check_res.status_code == 200

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{TEST_USER_EMAIL}", 300, "true")

    # 회원가입 테스트 (POST /users)
    signup_res = await client.post(
        "/users",
        json={"id": TEST_USER_ID, "password": TEST_USER_PW, "name": TEST_USER_NAME, "email": TEST_USER_EMAIL}
    )
    assert signup_res.status_code == 201

    # 로그인 및 토큰 발급 테스트 (POST /auth/login)
    login_res = await client.post("/auth/login", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert login_res.status_code == 201
    assert "access_token" in login_res.cookies

    # 로그인한 사용자 정보 조회 (GET /users/me)
    info_res = await client.get("/users/me")
    assert info_res.status_code == 200
    assert info_res.json()["data"]["id"] == TEST_USER_ID

    # 아이디 변경 테스트 (PATCH /users/me/id)
    id_mod_res = await client.patch("/users/me/id", json={"password": TEST_USER_PW, "new_id": NEW_USER_ID})
    assert id_mod_res.status_code == 200

    # 비밀번호 변경 테스트 (PATCH /users/me/password)
    pw_mod_res = await client.patch("/users/me/password", json={"password": TEST_USER_PW, "new_password": NEW_USER_PW})
    assert pw_mod_res.status_code == 200

    # 회원 탈퇴 테스트 (DELETE /users/me)
    withdraw_res = await client.request("DELETE", "/users/me", json={"password": NEW_USER_PW})
    
    assert withdraw_res.status_code == 200

    # 회원 탈퇴 복구 테스트 (POST /users/me/restore)
    restore_res = await client.post("/users/me/restore", json={"id": NEW_USER_ID, "password": NEW_USER_PW})
    assert restore_res.status_code == 200
    
    print("\n[성공] 정상 라이프사이클(가입~복구) 테스트 완료")


# ==========================================
# 예외 테스트: 중복 아이디 가입 방어 - 409 ERROR
# ==========================================
async def test_duplicate_id_check(client: AsyncClient):

    DUP_ID = "rlaxorjs20905"
    DUP_EMAIL_1 = "duptest1@test.com"
    DUP_EMAIL_2 = "duptest2@test.com"

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{DUP_EMAIL_1}", 300, "true")
    
    # 최초 가입
    first_signup = await client.post(
        "/users",
        json={"id": DUP_ID, "password": TEST_USER_PW, "name": TEST_USER_NAME, "email": DUP_EMAIL_1}
    )
    assert first_signup.status_code == 201

    # 똑같은 아이디로 중복 확인 시도
    check_res = await client.post("/users/check-id", json={"id": DUP_ID})
    assert check_res.status_code == 409
    assert "이미 사용중인 아이디입니다" in check_res.json()["detail"]

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{DUP_EMAIL_2}", 300, "true")

    # 똑같은 아이디로 회원가입 재시도
    second_signup = await client.post(
        "/users",
        json={"id": DUP_ID, "password": TEST_USER_PW, "name": TEST_USER_NAME, "email": DUP_EMAIL_2}
    )
    assert second_signup.status_code == 409
    
    print("\n[성공] 아이디 중복 가입 409 에러 방어 완료")

# ==========================================
# 예외 테스트: 중복 이메일 가입 방어 - 409 ERROR
# ==========================================
async def test_duplicate_email_Check(client: AsyncClient):

    DUP_ID_1 = "rlaxorjs20905"
    DUP_ID_2 = "rlaxorjs30305"
    DUP_EMAIL = "dupemail@test.com"

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{DUP_EMAIL}", 300, "true")

    # 최초 가입
    first_signup = await client.post(
        "/users",
        json={"id": DUP_ID_1, "password": TEST_USER_PW, "name": TEST_USER_NAME, "email": DUP_EMAIL}
    )
    assert first_signup.status_code == 201

    # 똑같은 이메일로 중복 확인 시도
    check_res = await client.post("/users/check-email", json={"email": DUP_EMAIL})
    assert check_res.status_code == 409
    assert "이미 사용중인 이메일입니다." in check_res.json()["detail"]

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{DUP_EMAIL}", 300, "true")

    # 똑같은 이메일로 회원가입 재시도
    second_signup = await client.post(
        "/users",
        json={"id": DUP_ID_2, "password": TEST_USER_PW, "name": TEST_USER_NAME, "email": DUP_EMAIL}
    )
    assert second_signup.status_code == 409
    
    print("\n[성공] 이메일 중복 가입 409 에러 방어 완료")

# ==========================================
# 예외 테스트: 잘못된 비밀번호 로그인 방어 - 401 ERROR
# ==========================================
async def test_login_wrong_password(client: AsyncClient):

    REAL_PW = "Kim3276!?"
    WRONG_PW = "Gim3276?!"

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{TEST_USER_EMAIL}", 300, "true")

    # 정상 가입
    await client.post(
        "/users",
        json={"id": TEST_USER_ID, "password": REAL_PW, "name": TEST_USER_NAME, "email": TEST_USER_EMAIL}
    )

    # 틀린 비밀번호로 로그인 시도
    login_res = await client.post("/auth/login", json={"id": TEST_USER_ID, "password": WRONG_PW})
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]
    
    print("\n[성공] 잘못된 비밀번호 로그인 401 에러 방어 완료")


# ==========================================
# 예외 테스트: 토큰 없이 보호된 API 접근
# ==========================================
async def test_access_without_token(client: AsyncClient):

    info_res = await client.get("/users/me")
    
    assert info_res.status_code == 401
    assert "유효하지 않은 인증 자격입니다." in info_res.json()["detail"]


# ==========================================
# 예외 테스트: 존재하지 않는 아이디 로그인
# ==========================================
async def test_login_nonexistent_user(client: AsyncClient):

    login_res = await client.post(
        "/auth/login", 
        json={"id": "ghost_user123", "password": "Ghost1234!!"}
    )
    
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]


# ==========================================
# 예외 테스트: 남이 쓰는 아이디로 변경 시도 - 409 ERROR
# ==========================================
async def test_id_modify_duplicate_conflict(client: AsyncClient):
 
    USER1_ID, USER1_PW, USER1_EMAIL = "first_user11!!", "User1111!!", "USER1@email.com"
    USER2_ID, USER2_PW, USER2_EMAIL = "second_user22!!", "User2222!!", "USER2@emai.com"


    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{USER1_EMAIL}", 300, "true")

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{USER2_EMAIL}", 300, "true")

    # 유저 1, 2 모두 가입
    await client.post(
        "/users",
        json={"id": USER1_ID, "password": USER1_PW, "name": TEST_USER_NAME, "email": USER1_EMAIL}
    )

    await client.post(
        "/users",
        json={"id": USER2_ID, "password": USER2_PW, "name": TEST_USER_NAME, "email": USER2_EMAIL}
    )

    # 유저 1로 로그인하여 토큰 획득
    login_res = await client.post("/auth/login", json={"id": USER1_ID, "password": USER1_PW})

    # 유저 1이 본인의 아이디를 유저 2의 아이디(second_user22!!)로 변경
    mod_res = await client.patch(
        "/users/me/id",
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
    TARGET_EMAIL = "wrongpw@test.com"

    # Redis에 이메일 인증 완료 등록
    await redis_db.setex(f"email_verified:{TARGET_EMAIL}", 300, "true")

    # 가입 및 로그인
    await client.post(
        "/users",
        json={"id": TARGET_ID, "password": REAL_PW, "email": TARGET_EMAIL, "name": TEST_USER_NAME}
    )

    login_res = await client.post("/auth/login", json={"id": TARGET_ID, "password": REAL_PW})

    # 틀린 비밀번호로 회원탈퇴 시도
    withdraw_res = await client.request(
        "DELETE",
        "/users/me",
        json={"password": WRONG_PW}
    )
    
    assert withdraw_res.status_code == 401
    assert "비밀번호가 일치하지 않습니다" in withdraw_res.json()["detail"]