# 랜덤으로 생성해야 하는 데이터는 게싷판의 제목 / 게시판의 내용 2개

# 게시판 제목 제약조건: 2 ~ 50 자

# 게시판 내용 제약조건: 30 ~ 2000자

import pytest
from faker import Faker

fake = Faker

test_boards = []

    for _ in range(50):

        test_title = fake.text(max_nb_chars = 50)
        test_content = fake.text(max_nb_chars = 2000)
        # fake.text() : max_nb_chars 길이 만큼의 text를 무작위로 생성해준다.

        test_boards.append({"title:": test_title, "content": test_content})

pytestmark = pytest.mark.asyncio

# =======================
# 1. 유저의 게시판 생성(/boards/bRegister)
# =======================

# 게시판 생성 성공
@pytest.mark.parametrize("boards", test_boards)
async def test_create_boards_success(async_client, boards):

    payload = {
        "title": boards["title"],
        "content": boards["content"]
    }

    response = await astnc_client.post("/boards/bRegister", json = payload)

    assert response.status_code = 200
    assert response.json()["message"] == "게시판이 생성되었습니다."

# =======================
# 2. 특정 유저의 게시판 조회 (/boards/certainBInfo)
# =======================

# 조회 성공
@pytest.mark.parametrize("boards", test_boards)
async def test_ceratin_boards_info_success("boards", test_boards):

    payload =

# 해당 유저가 쓴 게시판이 존재하지않을 때 - 이거는 게시판 성공 부분에서 게시판 하나씩 다 생성했는데

# =======================
# 3. 모든 유저의 게시판 조회 (/boards/allBInfo)
# =======================

# =======================
# 4. 게시판 제목 변경 (/boards/modiTitle)
# =======================

# =======================
# 5. 게시판 내용 변경 (/boards/modiContent)
# =======================

# =======================
# 6. 게시판 삭제 (/boards/deleteBoards)
# =======================

# =======================
# 7. 게시판 복구 (/boards/restoreBoards)
# =======================
