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
