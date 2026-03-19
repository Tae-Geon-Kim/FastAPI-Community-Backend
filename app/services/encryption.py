# main.py에서 입력받은 암호를 해싱해서 DB에 보관
# 로그인 할 때, DB에서 해싱값을 가져와 검증
import bcrypt

# 비밀번호를 해싱해서 암호화 후 반환 (return 값: string)
def hash_password(pw: str):

    pw = bytes(pw, 'utf-8') # 암호화는 bytes에서 가능 -> bytes 변환
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt()) # hashed에는 bytes가 

    return hashed.decode('utf-8') # string으로 -> DB 저장 필요
                                  # DB에 저장할 떄는 database.py SQL문 사용해서

# main.py에서 해싱된 값 가져와 검증
def verify(plain_password: str, hashed_password: str):

    pw = bytes(plain_password, 'utf-8')
    hashed_password = bytes(hashed_password, 'utf-8')

    # checkpw(password:bytes, hashed_password: bytes)

    return bcrypt.checkpw(plain_password, hashed_password) # 반환 값: boolean
