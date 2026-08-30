---
name: rq-hellov1
description: "RQ 시스템의 최상위 `소스창 실행본 → $스킬 즉시 실행 → Google Drive 백업` 저장·실행 순서와 FNa98 협업·범위 잠금을 활성화한다. 사용자가 $rq-hellov1, $thingk002, 다른 $rq-* 스킬, 소스창, 실행본, Drive 백업, 동기화 불필요, 시스템 전체 상위잠금, 책임자 지정을 말할 때 사용한다. 저장·실행 상위잠금은 모든 RQ 프로젝트·탭·스킬에 적용하며 개인 스킬 서버 동기화를 실행조건에서 제외한다. FNa98 방 잠금은 호출된 현재 대화방에서 사용자가 VOID하거나 교체할 때까지 유지한다."
---

# RQ Hello V1

## 실행

1. [SOURCE_SKILL_DRIVE_SYSTEM_TOP_LOCK.md](references/SOURCE_SKILL_DRIVE_SYSTEM_TOP_LOCK.md)를 처음부터 끝까지 읽고 `SYSTEM_STORAGE_ROUTE_LOCK=ACTIVE`로 둔다.
2. 소스창이 연결되어 있으면 `SOURCE_WINDOW/SOURCE_WINDOW_ROOM_ROUTING_LOCK.txt`를 처음부터 끝까지 읽고 `DOCUMENT_ADMISSION_GATE=ACTIVE`와 `PROJECT_COMPLETION_GATE=ACTIVE`로 둔다.
3. [FNa98_OPENING_LOCK.md](references/FNa98_OPENING_LOCK.md)를 처음부터 끝까지 읽는다.
4. 한국어 의미 정본과 AI 실행 정본을 같은 뜻으로 적용한다. 충돌처럼 보이면 한국어 의미 정본을 우선한다.
5. `FNa98_ROOM_LOCK=ACTIVE`로 두고, 현재 대화방에서 사용자가 VOID하거나 새 기준으로 교체할 때까지 유지한다.
6. 이후 다른 스킬 호출을 허용한다. 이 스킬은 다른 스킬을 대체하거나 차단하지 않고, 그 작업의 TARGET·SOURCE·SCOPE·OUTPUT 경계와 `소스창 → $스킬 → Drive 백업` 순서 위에 선행 기준으로 작동한다.
7. `$rq-hellov1`과 다른 스킬 또는 실제 작업지시가 함께 오면 이 오프닝을 먼저 잠근 뒤 실제 지시를 수행한다.
8. 단독 호출이면 아래 취지로 1~3줄만 답하고 다음 지시를 기다린다.
   - 반갑습니다.
   - FNa98 협업 기준을 읽고 이 방에 잠갔습니다.
   - 이후 호출되는 스킬도 현재 지시의 TARGET·SOURCE·SCOPE 안에서 운용하겠습니다.
9. 사용자가 요청하지 않으면 오프닝 정본 전체를 다시 출력하지 않는다.
10. 사용자가 시스템 상위잠금 수정을 명시한 경우에만 이 잠금 Source를 수정한다. 일반 호출을 이유로 다른 스킬·파일·정본을 수정하지 않는다.

## 경계

- 이 스킬은 엔진·분석기·점성학 Source가 아니다.
- 이 스킬은 현재 작업의 TARGET을 생성하거나 바꾸지 않는다.
- 이 스킬은 사용자 지시를 받기 전 선행 작업을 시작하지 않는다.
- 기존 `rq-vedic`과 하위 엔진의 내용을 병합하거나 덮어쓰지 않는다.
- FNa98 방 잠금은 다른 대화방에 자동 전파하지 않는다. `SOURCE → $SKILL → DRIVE` 저장·실행 상위잠금은 RQ 시스템 Source의 전역 불변식이다.
