import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기(async)로 실행하도록 설정
pytestmark = pytest.mark.asyncio

# 테스트 데이터
TEST_USER_ID = "taegeon1111"
TEST_USER_PW = "Kim1234!!"

NEW_USER_ID = "newtaegeon11"

# ==========================================
# 정상 작동 통합 테스트
# ==========================================
async def test_user_integration_scenario(client: AsyncClient):
    """
    유저 생성부터 정보 변경, 탈퇴 및 복구까지의 전체 라이프사이클을 검증합니다.
    """
    # 1. 아이디 중복 확인 (/uCheck)
    check_res = await client.post("/uCheck", json={"id": TEST_USER_ID})
    assert check_res.status_code == 200

    # 2. 회원가입 테스트 (/uRegister)
    signup_res = await client.post("/uRegister", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert signup_res.status_code == 200

    # 3. 로그인 및 토큰 발급 테스트 (/login)
    login_res = await client.post("/login", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert login_res.status_code == 200
    
    access_token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 4. 로그인한 사용자 정보 조회 (/uInfo)
    info_res = await client.post("/uInfo", headers=headers)
    assert info_res.status_code == 200
    assert info_res.json()["data"]["id"] == TEST_USER_ID

    # 5. 아이디 변경 테스트 (/idModify)
    id_mod_res = await client.post("/idModify", headers=headers, json={"password": TEST_USER_PW, "new_id": NEW_USER_ID})
    assert id_mod_res.status_code == 200

    # 6. 회원 탈퇴 테스트 (/withdraw)
    withdraw_res = await client.post("/withdraw", headers=headers, json={"password": TEST_USER_PW})
    assert withdraw_res.status_code == 200

    # 7. 회원 탈퇴 복구 테스트 (/restoreUser)
    restore_res = await client.post("/restoreUser", json={"id": NEW_USER_ID, "password": TEST_USER_PW})
    assert restore_res.status_code == 200
    
    print("\n[성공] 정상 라이프사이클(가입~복구) 테스트 완료")


# ==========================================
# 예외 테스트: 중복 아이디 가입 방어
# ==========================================
async def test_duplicate_id_check(client: AsyncClient):
    """
    이미 가입된 아이디로 중복 확인 및 가입을 시도할 때 
    409 Conflict 에러를 잘 반환하는지 검증합니다.
    """
    DUP_ID = "duplicate123"
    DUP_PW = "Test1234!!"

    # 1. 최초 가입 진행 (성공해야 함)
    first_signup = await client.post("/uRegister", json={"id": DUP_ID, "password": DUP_PW})
    assert first_signup.status_code == 200

    # 2. 똑같은 아이디로 중복 확인 시도 -> 409 에러 발생 확인!
    check_res = await client.post("/uCheck", json={"id": DUP_ID})
    assert check_res.status_code == 409
    assert "이미 사용중인 아이디입니다" in check_res.json()["detail"]

    # 3. 똑같은 아이디로 회원가입 재시도 -> 409 에러 발생 확인!
    second_signup = await client.post("/uRegister", json={"id": DUP_ID, "password": DUP_PW})
    assert second_signup.status_code == 409
    
    print("\n[성공] 중복 가입 409 에러 방어 완료")


# ==========================================
# 예외 테스트: 잘못된 비밀번호 로그인 방어
# ==========================================
async def test_login_wrong_password(client: AsyncClient):
    """
    가입된 아이디에 대해 틀린 비밀번호로 로그인을 시도할 때 
    401 Unauthorized 에러를 잘 반환하는지 검증합니다.
    """
    LOGIN_ID = "wrongpwtest"
    REAL_PW = "RealPw123!!"
    WRONG_PW = "FakePw999!!"

    # 1. 정상 가입 진행
    await client.post("/uRegister", json={"id": LOGIN_ID, "password": REAL_PW})

    # 2. 틀린 비밀번호로 로그인 시도 -> 401 에러 발생 확인!
    login_res = await client.post("/login", json={"id": LOGIN_ID, "password": WRONG_PW})
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]
    
    print("\n[성공] 잘못된 비밀번호 로그인 401 에러 방어 완료")


# ==========================================
# 예외 테스트: 토큰 없이 보호된 API 접근
# ==========================================
async def test_access_without_token(client: AsyncClient):
    """
    토큰(Authorization 헤더) 없이 /uInfo에 접근할 때 
    401 에러를 반환하는지 검증합니다.
    """
    # 헤더 없이 바로 찌르기
    info_res = await client.post("/uInfo")
    
    assert info_res.status_code == 401
    assert "Not authenticated" in info_res.json()["detail"] # FastAPI 기본 에러 메시지


# ==========================================
# 예외 테스트: 존재하지 않는 아이디 로그인
# ==========================================
async def test_login_nonexistent_user(client: AsyncClient):
    """
    DB에 없는 아이디로 로그인을 시도할 때 
    401 에러를 반환하는지 검증합니다.
    """
    login_res = await client.post(
        "/login", 
        json={"id": "ghost_user123", "password": "Ghost1234!!"}
    )
    
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]


# ==========================================
# 예외 테스트: 남이 쓰는 아이디로 변경 시도
# ==========================================
async def test_id_modify_duplicate_conflict(client: AsyncClient):
    """
    아이디 변경 시, 이미 존재하는 다른 유저의 아이디로 
    변경을 시도할 때 409 에러를 반환하는지 검증합니다.
    """
    USER1_ID, USER1_PW = "firstuser11", "User1111!!"
    USER2_ID, USER2_PW = "seconduser22", "User2222!!"

    # 1. 유저 1, 2 모두 가입
    await client.post("/uRegister", json={"id": USER1_ID, "password": USER1_PW})
    await client.post("/uRegister", json={"id": USER2_ID, "password": USER2_PW})

    # 2. 유저 1로 로그인하여 토큰 획득
    login_res = await client.post("/login", json={"id": USER1_ID, "password": USER1_PW})
    headers = {"Authorization": f"Bearer {login_res.json()['data']['access_token']}"}

    # 3. 유저 1이 본인의 아이디를 유저 2의 아이디(seconduser22)로 변경 시도! -> 409 에러 발생
    mod_res = await client.post(
        "/idModify",
        headers=headers,
        json={"password": USER1_PW, "new_id": USER2_ID}
    )
    
    assert mod_res.status_code == 409
    assert "중복되는 아이디가 존재합니다" in mod_res.json()["detail"]

# ==========================================
# 예외 테스트: 회원탈퇴 시 비밀번호 불일치
# ==========================================
async def test_withdraw_wrong_password(client: AsyncClient):
    """
    회원 탈퇴 시, 현재 비밀번호를 틀리게 입력했을 때
    401 에러를 반환하는지 검증합니다.
    """
    TARGET_ID = "withdrawtest"
    REAL_PW = "RealPw123!!"
    WRONG_PW = "FakePw999!!"

    # 1. 가입 및 로그인
    await client.post("/uRegister", json={"id": TARGET_ID, "password": REAL_PW})
    login_res = await client.post("/login", json={"id": TARGET_ID, "password": REAL_PW})
    headers = {"Authorization": f"Bearer {login_res.json()['data']['access_token']}"}

    # 2. 틀린 비밀번호로 회원탈퇴 시도 -> 401 에러 발생
    withdraw_res = await client.post(
        "/withdraw",
        headers=headers,
        json={"password": WRONG_PW}
    )
    
    assert withdraw_res.status_code == 401
    assert "비밀번호가 일치하지 않습니다" in withdraw_res.json()["detail"]