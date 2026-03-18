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