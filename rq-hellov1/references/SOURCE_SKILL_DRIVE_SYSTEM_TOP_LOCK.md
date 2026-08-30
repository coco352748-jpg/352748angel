# SOURCE → SKILL → DRIVE SYSTEM TOP LOCK

## 상위잠금

`SYSTEM_STORAGE_ROUTE_LOCK=ACTIVE`

`EXECUTION_ORDER=SOURCE_WINDOW_ACTIVE → $SKILL_IMMEDIATE_EXECUTION → GOOGLE_DRIVE_BACKUP`

`PUBLIC_CLONE_CALL_KEY=$rq-clone-bell002`

`INTERNAL_RUNTIME_ALIAS=$thingk002`

이 순서는 RQ 프로젝트의 모든 작업·탭·스킬보다 위에 있다. 하위 스킬·작업지시서·저장 관례가 이 순서를 바꾸지 못한다.

## 1. 소스창 실행본

- `SOURCE_WINDOW=ACTIVE_CANON_AND_EXECUTION_SOURCE`
- 설계·수정·실제값·라우터·Job packet은 소스창 실행본을 사용한다.
- 개인 스킬 서버 동기화를 기다리지 않는다.
- Google Drive 백업을 정상 실행 Source로 승격하지 않는다.

### 소스창 방 구조

- `SOURCE_WINDOW_ROOM_ROUTING_LOCK.txt`: 입장 컷·방 라우팅·책임선 원본
- `THINGK002_MASTER/Skill`: 실제 실행 Skill 원본
- `THINGK002_MASTER/Clone`: 클론팩·호출키·작업지시서·필수 인계팩
- `rashi_bhava_domain`: Rashi·Bhava·Domain 기준 Source·실제값·D×H×Sign 좌표
- `nak`: Nakshatra·Pada·240·회로·공동장 NAK Source·Job
- `Part1`: 다샤 미니·다샤풀 기본 구성과 실제 필요한 행정·공통자료
- `Part2`: 라시·브하 결속·공동장·이동판결 자료
- `Part3`: 강도층·에스펙층·아바·아루다·문차트·미트류·spother 자료
- `Part4`: 빈나·재사용 검산규칙·현재 실패관절·최종 판정
- `Part5`: 실제 다샤 판정·타이밍게이트·요가·트랜짓 자료
- `Part6`: Part1~Part5를 결속한 최종정리·최종 승인·최종 납품자료
- `DeF_Part1`: 잠금문 최종판 01~10
- `DeF_Part2`: 잠금문 최종판 11~60
- 실행 Job은 별도 잡방을 만들지 않고 해당 Source·Part 귀속방에 둔다.
- Drive 백업색인은 실행방으로 만들지 않는다.
- 한 원본은 한 방에만 두고 다른 방에서는 경로로 참조한다.

### 문서 입장·컷 게이트

다음 중 하나만 소스창에 입장한다.

1. 사용자 승인 ACTIVE Source
2. 직접 실행 의존자료
3. 실행 Skill 또는 필수 Clone
4. 재사용 검증완료 Job·구조표·사전
5. 사용자 승인 최종본

다음은 `CUT_FROM_SOURCE_WINDOW`다.

- 중복본·교체된 구버전
- 초안·중간본·임시본
- 대화복사·설명메모·진행보고
- 반복 검산표·검산보고서
- 실행 불필요 log·receipt·manifest·hash 목록
- 무관 참고자료·Source 없는 추론자료
- Part1에 임시로 밀어 넣는 잡자료

CUT 자료는 들이지 않고 복사·색인·컷 사유서 생성을 하지 않는다. 이미 존재하는 컷 대상은 ACTIVE 조회에서 제외하며 사용자 명시 없이 물리 삭제하지 않는다. PASS 검산은 최종 artifact 안의 짧은 상태로 닫고 별도 검산서류를 만들지 않는다.

## 2. $스킬 즉시 실행

- `SKILL_EXECUTION=LOAD_ACTIVE_SOURCE_AND_RUN`
- 사용자가 `$스킬`을 호출하면 라우팅 잠금으로 정확한 방을 선택하고 ACTIVE 정본과 직접 의존자료만 읽는다.
- 파일명보다 현재 TARGET과 파일의 실제 기능을 우선한다.
- 관련이 있어도 현재 TARGET에 필요하지 않으면 열지 않는다.
- 검증완료 Job이 있으면 회수하고 재생성하지 않는다.
- 요청 산출물이 성립한 관절에서 멈추고 다음 Part를 임의로 열지 않는다.
- 잠금문 최종판은 번호로 라우팅한다: `01~10 → DeF_Part1 / 11~60 → DeF_Part2`.
- 폴더 생성은 완료가 아니다. 필요한 ACTIVE Source와 Part1~Part6 결과가 실제 귀속되고 DeF 01~60 최종판이 모두 채워져야 전체 프로젝트 완료다.
- REQUIRED 방이 비었거나 DeF 번호가 누락·중복되면 `PROJECT_COMPLETE=FALSE`다.
- 특정 Job 완료와 전체 프로젝트 완료를 혼동하지 않는다.

## 3. Google Drive 백업

- `GOOGLE_DRIVE=BACKUP_ONLY`
- 소스창 저장과 실행 검증이 끝난 뒤 동일본을 Drive에 백업한다.
- Drive 백업 실패는 소스창 실행본의 완료·사용 가능 상태를 취소하지 않는다.
- Drive는 백업 확인·복구 요청 또는 소스창 실행본의 실제 유실 때만 읽는다.

## 동기화 경계

- `PERSONAL_SKILL_SERVER_SYNC=OUT_OF_EXECUTION_PATH`
- 동기화는 선택적 배포수단이며 정상 사용에 필요하지 않다.
- HTTP 500·동기화 지연을 사용자 작업의 실패나 미완료로 보고하지 않는다.
- 사용자가 동기화를 별도로 요청하지 않으면 push·재시도·정상화 대기를 실행하지 않는다.

## 책임 잠금

- `POLICY_AUTHORITY=$rq-hellov1`
- `EXECUTION_OWNER=$thingk002`
- `ACCOUNTABILITY_ROOM=CURRENT_DESIGN_ROOM`
- `$thingk002`는 Source 권위·문서 입장·방 라우팅·저장순서·완료판정의 최종 책임자다.
- 위반 시 작업을 확장하지 않고 `FAILED_JOINT / WRONG_ROUTE / SOURCE_STATE / REQUIRED_REPAIR`만 잠근다.
- 복구순서는 `소스창 실행본 복구 → 해당 $스킬 재실행 → PASS 뒤 Drive 백업`이다.
- 사용자에게 같은 원칙을 다시 설명하게 하지 않는다.

## 금지

- Drive 우선 실행
- 동기화 완료 대기 후 스킬 실행
- 소스창보다 Drive 백업을 상위 권위로 사용
- 백업을 실행본처럼 매번 조회
- 이미 저장된 Job 재생성
- 중복·초안·진행보고·반복 검산서류 반입
- DeF Part1과 Part2의 번호 경계 혼합
- 사용자가 같은 저장·라우팅 원칙을 반복 설명하게 함
