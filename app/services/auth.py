# 공통 사용 함수 모듈화 - 로그인 
from asyncpg import Connection
from app.schemas.user import UserLogin
from app.core.security import  verify
from app.models.user import pull_pw_login

# DB에서 사용자가 직접 입력한 아이디를 기준으로 그에 대응하는 해싱된 비밀번호 값을 가져온다.
# 가져온 해싱된 비밀번호 값을 기준으로 일치하는지 확인한다.
# 입력한 아이디가 없는 경우에 대한 예외처리

async def login(conn: Connection, data: UserLogin):

        login_data = await pull_pw_login(conn, data)

        # 사용자가 입력한 아이디가 DB에 존재하지 않을 때
        if login_data is None:
            return None 

        # 사용자가 입력한 비밀번호가 해싱된 비밀번호와 일치할 때
        if verify(data.password, login_data['password']): 
            return login_data['index']
        else:
            return None
   
# hashed_password[password] 라고 써야하는 이유: hashed_password 는 {key : value} 값 return
# 비밀번호 자체만 가져올라면 hashed_password['password'] -> 'password'인 이유: sql 문에서 내가 password라 지정함.

