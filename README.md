# 📌 프로젝트 소개
---
본 프로젝트는 **회원관리 및 게시판 기능을 포함한 백엔드 시스템**을 구현한 프로젝트입니다.  

사용자는 회원가입 및 로그인 후 게시글을 작성하고, 회원정보 및 게시글을 수정, 삭제할 수 있습니다.

또한 FastAPI 기반으로 설계하여 비동기 처리 성능과 확장성, 유지보수성을 고려하였습니다.

---

# ⚙️ 개발 스펙 및 개발 환경
## 🧩 Backend
- **Language**: Python 3.12.3
- **Framework**: FastAPI
- **Security**: Bcrypt (Password Hashing), JWT (Token Auth)

## 🗄️ Database & Storage
- **DBMS**: PostgreSQL
- **Driver**: Asyncpg (Asynchronous Python driver)

## 🛠️ Tools
- **IDE**: VS Code
- **Version Control**: Git, GitHub
- **API Test**: Swagger UI (Built-in), Postman
---

# 🚀 주요 기능

## 👤 회원 관리
- 회원가입 / 로그인 / 로그아웃
- 🔐 비밀번호 암호화 저장 (BCrypt)
- 사용자 정보 조회, 수정, 삭제

---

## 📝 게시판 기능
- 게시글 작성 / 조회 / 수정 / 삭제 (CRUD)
- 📋 게시글 목록 조회 (페이징 처리)
- 🔍 게시글 수정 및 삭제

---

# 🧱 프로젝트 구조
여기에 파일 구조 

---

# 🏗️ 시스템 아키텍처
여기에 mermaid로 그린 시퀀스 다이어그램 

```mermaid
sequenceDiagram

autonumber

actor U as User

participant A as API

participant D as DB



Note over U, A: [공통 단계] 아이디 유효성 검사

U->>A: ID 입력 (로그인/회원가입 시도)

activate A

A->>A: ID 공백/빈 문자열 체크

A->>D: ID 중복 여부 조회

activate D

D-->>A: 조회 결과 반환

deactivate D



alt [Case 1] ID가 존재하지 않는 경우 (회원가입 진행)

A-->>U: "아이디 사용 가능 (회원가입 진행)"

U->>A: 비밀번호 입력

A->>A: 비밀번호 공백/해싱(bcrypt)

A->>D: 신규 유저 정보 저장 (reg_date)

D-->>U: 회원가입 완료 성공


else [Case 2] ID가 존재하는 경우 (로그인 진행)

A-->>U: "아이디 확인됨 (비밀번호 입력)"

U->>A: 비밀번호 입력

A->>D: 저장된 Hashed PW 호출

D-->>A: hashed_pw 반환

A->>A: bcrypt.checkpw() 검증


alt 비밀번호 일치 (로그인 성공)

A-->>U: 로그인 성공 (인증 완료)

else 비밀번호 불일치 (실패)

A-->>U: error (비밀번호를 확인하세요)

end

end

deactivate A 
```

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant A as API
    participant D as DB

    Note over U, D: [로그인 성공 상태 (Authenticated)]

    Note over U, D: 1. 사용자 정보 조회 (Read)
    U->>A: 사용자 정보 조회 요청
    activate A
    A->>D: user_index를 통한 정보 조회 요청
    activate D
    D-->>A: 사용자 데이터 반환 (ID, 가입일 등)
    deactivate D
    A-->>U: 사용자 정보 화면 출력
    deactivate A

    Note over U, D: 2. 사용자 정보 수정 (Update)
    U->>A: 변경할 정보 입력 (ID 혹은 PW)
    activate A
    A->>A: 입력값 공백 및 빈 문자열 확인
    
    alt [Case 1] 아이디(ID) 변경 시
        A->>D: 신규 아이디 중복 여부 확인
        activate D
        D-->>A: 중복 결과 반환
        deactivate D
        alt 중복 없음
            A->>D: 신규 ID 저장 및 update_date 갱신
            A-->>U: 아이디 변경 성공 알림
        else 중복 있음
            A-->>U: error (이미 사용 중인 아이디입니다)
        end
        
    else [Case 2] 비밀번호(PW) 변경 시
        A->>A: 신규 비밀번호 해싱 (bcrypt)
        A->>D: 해싱된 PW 저장 및 update_date 갱신
        A-->>U: 비밀번호 변경 성공 알림
    end
    deactivate A

    Note over U, D: 3. 사용자 정보 삭제 (Delete / 회원 탈퇴)
    U->>A: 회원 탈퇴 요청
    activate A
    A->>D: 해당 user_index 관련 데이터 전체 삭제
    activate D
    D-->>A: 삭제 완료 응답 (DELETE Success)
    deactivate D
    A-->>U: 탈퇴 처리 성공 (로그아웃 처리)
    deactivate A

    
```

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant A as API
    participant D as DB

    Note over U, A: [게시판 작업 전 본인 확인]
    U->>A: 아이디 / 비밀번호 전송
    activate A
    A->>D: ID 존재 확인 및 hashed_pw 조회
    activate D
    alt 아이디 미존재 혹은 검증 실패
        D-->>A: Error/Fail
        A-->>U: 인증 에러 (로그인 실패)
    else 인증 성공
        D-->>A: hashed_pw 반환
        deactivate D
        A->>A: bcrypt.checkpw() 검증 성공
        
        Note over U, D: [게시판 등록]
        alt
            U->>A: Title 입력
            A->>A: 빈 문자열 여부 확인
            alt 빈 문자열인 경우
                A-->>U: error (제목을 입력하세요)
            else 정상 입력
                U->>A: Content 입력
                A->>D: Title, Content, user_index 저장 (reg_date)
                A-->>U: 등록 완료
            end

        Note over U, D: [게시판 조회]
        else
            A->>D: 해당 User의 게시글 리스트 조회
            activate D
            D-->>A: 게시판 목록 반환
            deactivate D
            A-->>U: 목록 출력

        Note over U, D: [게시판 수정]
        else
            A->>D: 수정할 게시판 데이터 로드
            U->>A: 수정할 내용 입력
            A->>A: Title/Content 빈 문자열 체크
            alt 빈 문자열 포함
                A-->>U: error (내용을 비워둘 수 없습니다)
            else 정상 수정
                A->>D: 수정사항 저장 (update_date 갱신)
                A-->>U: 수정 완료
            end

        Note over U, D: [게시판 삭제]
        else
            A->>D: 삭제할 게시판 선택 요청
            A-->>U: "삭제를 위해 비밀번호를 다시 입력하세요"
            U->>A: 비밀번호 재입력
            A->>A: bcrypt.checkpw() 최종 검증
            alt 비밀번호 불일치
                A-->>U: 삭제 실패 (권한 없음)
            else 비밀번호 일치
                A->>D: 해당 게시글 삭제 (DELETE)
                A-->>U: 삭제 완료 성공
            end
        end
    end
    deactivate A
```

---

# 📡 API 예시

## 🔐 회원가입
POST /

## 🔑 로그인
POST /

## 📝 게시글 작성
POST /

## 📋 게시글 목록 조회
GET /

---

# 🧪 테스트 방법

- Swagger을 활용한 API 테스트
---


# ✨ 향후 개선 사항

- 🔍 게시글 검색 고도화 (Full Text Search)
- 📷 이미지 업로드 기능 추가
- 👍 좋아요 기능
- 🧾 API 문서화 (Swagger)
