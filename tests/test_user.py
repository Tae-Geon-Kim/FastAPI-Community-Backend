import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기(async)로 실행하도록 설정
pytestmark = pytest.mark.asyncio

"""
    - 아이디 제약 조건: 영문자, 숫자가 무조건 1개 이상은 포함된 5 ~ 30자 (특수문자는 선택사항)
    		pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&._-]{5,30}$’

	- 비밀번호 제약 조건: 영문자, 숫자, 특수문자가 무조건 1개 이상은 포함된 8 ~ 30자
    		pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&._-])[A-Za-z\d@$!%*#?&._-]{8,30}$'

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

    # 아이디 중복 확인 (/uCheck)
    check_res = await client.post("/user/uCheck", json={"id": TEST_USER_ID})
    assert check_res.status_code == 200

    # 회원가입 테스트 (/uRegister)
    signup_res = await client.post("/user/uRegister", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert signup_res.status_code == 200

    # 로그인 및 토큰 발급 테스트 (/login)
    login_res = await client.post("/user/login", json={"id": TEST_USER_ID, "password": TEST_USER_PW})
    assert login_res.status_code == 200
    
    access_token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 로그인한 사용자 정보 조회 (/uInfo)
    info_res = await client.post("/user/uInfo", headers=headers)
    assert info_res.status_code == 200
    assert info_res.json()["data"]["id"] == TEST_USER_ID

    # 아이디 변경 테스트 (/idModify)
    id_mod_res = await client.patch("/user/idModify", headers=headers, json={"password": TEST_USER_PW, "new_id": NEW_USER_ID})
    assert id_mod_res.status_code == 200

    # 비밀번호 변경 테스트 (/pwModify)
    pw_mod_res = await client.patch("/user/pwModify", headers=headers, json={"password": TEST_USER_PW, "new_password": NEW_USER_PW})
    assert pw_mod_res.status_code == 200

    # 비밀번호 변경 테스트에서 비밀번호르 변경한 후에 진행하는 테스트에서는 새롭게 변경된 비밀번호를 사용해야된다.

    # 회원 탈퇴 테스트 (/withdraw)
    withdraw_res = await client.post("/user/withdraw", headers=headers, json={"password": NEW_USER_PW})
    assert withdraw_res.status_code == 200

    # 회원 탈퇴 복구 테스트 (/restoreUser)
    restore_res = await client.post("/user/restoreUser", json={"id": NEW_USER_ID, "password": NEW_USER_PW})
    assert restore_res.status_code == 200
    
    print("\n[성공] 정상 라이프사이클(가입~복구) 테스트 완료")


# ==========================================
# 예외 테스트: 중복 아이디 가입 방어 - 409 ERROR
# ==========================================
async def test_duplicate_id_check(client: AsyncClient):

    DUP_ID = "rlaxorjs20905"
    DUP_PW = "Kim3276!?"

    # 최초 가입 진행
    first_signup = await client.post("/user/uRegister", json={"id": DUP_ID, "password": DUP_PW})
    assert first_signup.status_code == 200

    # 똑같은 아이디로 중복 확인 시도
    check_res = await client.post("/user/uCheck", json={"id": DUP_ID})
    assert check_res.status_code == 409
    assert "이미 사용중인 아이디입니다" in check_res.json()["detail"]

    # 똑같은 아이디로 회원가입 재시도
    second_signup = await client.post("/user/uRegister", json={"id": DUP_ID, "password": DUP_PW})
    assert second_signup.status_code == 409
    
    print("\n[성공] 중복 가입 409 에러 방어 완료")


# ==========================================
# 예외 테스트: 잘못된 비밀번호 로그인 방어 - 401 ERROR
# ==========================================
async def test_login_wrong_password(client: AsyncClient):

    LOGIN_ID = "rlaxorjs20905"
    REAL_PW = "Kim3276!?"
    WRONG_PW = "Gim3276?!"

    # 정상 가입 진행
    await client.post("/user/uRegister", json={"id": LOGIN_ID, "password": REAL_PW})

    # 틀린 비밀번호로 로그인 시도
    login_res = await client.post("/user/login", json={"id": LOGIN_ID, "password": WRONG_PW})
    assert login_res.status_code == 401
    assert "로그인 정보를 다시 확인해주세요" in login_res.json()["detail"]
    
    print("\n[성공] 잘못된 비밀번호 로그인 401 에러 방어 완료")


# ==========================================
# 예외 테스트: 토큰 없이 보호된 API 접근
# ==========================================
async def test_access_without_token(client: AsyncClient):

    # 헤더 없이 바로 찌르기
    info_res = await client.post("/user/uInfo")
    
    assert info_res.status_code == 401
    assert "Not authenticated" in info_res.json()["detail"]


# ==========================================
# 예외 테스트: 존재하지 않는 아이디 로그인
# ==========================================
async def test_login_nonexistent_user(client: AsyncClient):

    login_res = await client.post(
        "/user/login", 
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
    await client.post("/user/uRegister", json={"id": USER1_ID, "password": USER1_PW})
    await client.post("/user/uRegister", json={"id": USER2_ID, "password": USER2_PW})

    # 유저 1로 로그인하여 토큰 획득
    login_res = await client.post("/user/login", json={"id": USER1_ID, "password": USER1_PW})
    headers = {"Authorization": f"Bearer {login_res.json()['data']['access_token']}"}

    # 유저 1이 본인의 아이디를 유저 2의 아이디(seconduser22)로 변경 시도
    mod_res = await client.patch(
        "/user/idModify",
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
    await client.post("/user/uRegister", json={"id": TARGET_ID, "password": REAL_PW})
    login_res = await client.post("/user/login", json={"id": TARGET_ID, "password": REAL_PW})
    headers = {"Authorization": f"Bearer {login_res.json()['data']['access_token']}"}

    # 틀린 비밀번호로 회원탈퇴 시도
    withdraw_res = await client.post(
        "/user/withdraw",
        headers=headers,
        json={"password": WRONG_PW}
    )
    
    assert withdraw_res.status_code == 401
    assert "비밀번호가 일치하지 않습니다" in withdraw_res.json()["detail"]