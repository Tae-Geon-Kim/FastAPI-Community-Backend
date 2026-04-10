import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(transport = ASGITransport(app = app), base_url = "http://test_server") as client
        yield client

@pyetst.fixture
async def random_user_data():

    test_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    # string.ascii_lowercase: 영어 소문자 a-z를 모아둔 문자열
    # string.digits: 숫자 0-9를 모아둔 문자열
    # random.choices(string, k=8): string에 포함된 문자열 중에서 8개를 중복해서 무작위로 뽑는다.
    # ''.join(): 무작위로 뽑은 8개를 합친다. (''이랑 join이니까 그냥 합치는것)

    test_password = fake.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
    # 비밀번호 랜덤 생성 대/소문자, 숫자, 특수문자 포함 10자

    return {"id": test_id, "password": test_password}

@pytest.fixture
async def registerd_user(async_client, random_user_data):

    await async_client.post("/user/uRegister", json = payload)

    return random_user_data