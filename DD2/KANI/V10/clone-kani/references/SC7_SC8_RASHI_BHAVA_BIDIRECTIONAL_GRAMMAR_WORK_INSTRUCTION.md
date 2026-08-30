# SC7 ↔ SC8 Rashi–Bhava 양방향 문법 역산 작업지시서

```text
WORK_INSTRUCTION_ID=KANI_SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR_V1
REGISTRATION_STATE=REGISTERED_FIRST_UNEXECUTED_JOB
EXECUTION_STATE=NOT_EXECUTED
V9_BASELINE=READ_ONLY
TARGET=SC7_TO_SC8_AND_SC8_TO_SC7_REPRODUCIBLE_GRAMMAR
LANE_SCOPE=RASHI_THEN_BHAVA_THEN_RASHI_BHAVA_BINDING
OCR_ROLE=VOID_AS_PRIMARY_TASK
ASTROLOGY_RECALCULATION=FORBIDDEN
PER_CHART_HARDCODING=FORBIDDEN
GRAMMAR_VALIDATOR_ROLE=FINAL_ACCEPTANCE_GATE_ONLY
```

## 1. 실제 질문

SC7 차트가 주어졌을 때 SC8 PIKACHU 차트를 만들고, SC8 PIKACHU 차트가
주어졌을 때 원래의 SC7 차트를 복원하는 **동일한 사고 문법**을 역산한다.
목표는 몇 개 샘플을 닮게 만드는 것이 아니라, 같은 입력에는 같은 판단을
내리는 한 개의 재사용 가능한 작업 프로토콜을 찾아 전체 corpus에 적용하는
것이다.

이 작업의 핵심 산출물은 OCR 결과나 점성 계산표가 아니다. SC7과 SC8은 이미
비교 가능한 Source artifact다. 해야 할 일은 두 표현 사이에서 DD2 작업자가
반복해서 사용한 선택·배치·문장화·생략·공동장 결합 규칙을 명시적 문법으로
복원하는 것이다.

## 2. 현재 등록 범위와 전체 프로그램 범위

### 현재 1단계: Rashi/Bhava

- D 차트 순서: `D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60`
- Lane 순서: `Rashi → Bhava → Rashi–Bhava binding`
- 20D × 2 lanes = **40 SC7–SC8 대응쌍**
- 20D × 12H × 2 lanes = **480 D×H 실행 단위**
- 원본 텍스트 파일 수: SC7 40 + SC8 40 = **80 files**

`40`, `480`, `80 files`는 단위가 다르다. 성공률 분모로 서로 바꾸어 쓰지
않는다.

### 전체 프로그램

- 물리적 PIKACHU corpus = **600 members**
- 각 archive의 `3P` 1개 × 20D = **20 physical members preserved / operationally VOID**
- 현재 KANI 활성 corpus = **580 non-3P members**

현재 작업 등록은 3P를 재활성화하지 않는다. 전체 600개 완전재현 PASS는
전수 forward/reverse round-trip을 실제 실행하기 전까지 `HOLD`다.

## 3. Source 잠금

실행 Source는 등록 manifest에 해시 잠금된 다음 두 master ZIP뿐이다.

1. `references/source_window_originals/sc7_sc8_rashi_bhava/HYEWON_SC7_RASHI_BHAVA_20D_ALL.zip`
2. `references/source_window_originals/sc7_sc8_rashi_bhava/HYEWON_SC8_RASHI_BHAVA_20D_ALL.zip`

SC7과 SC8의 파일명·D 순서·본문·빈칸·표기·단락을 Source evidence로 보존한다.
외부 지식이나 점성 재계산으로 누락을 메우지 않는다. 새 직접 Source가
입력되면 기존 Source를 덮어쓰지 말고 별도 후보로 등록하고 충돌 범위만
재개방한다.

## 4. 역산하는 브레인: 사고 프로토콜

각 D와 H를 독립 실행하되, 동일한 규칙 후보를 모든 대응쌍에 재사용한다.

### A. SC7 원자화

SC7 본문을 다음 입력 원자로 분해한다.

- D, lane, H 좌표
- Source Anchor와 원문 span
- Object / house / sign / lord / occupant / relation
- Rashi 상태와 Bhava 상태
- 공동장에 들어갈 참여자·역할·방향
- 문장 슬롯, 구분자, 순서, 반복, 생략, 빈칸
- 확정값, 파생값, `EMPTY`, `HOLD`, `VOID`

원자화는 의미를 새로 계산하는 단계가 아니다. SC7에 실제 존재하는 입력을
주소 가능한 최소 단위로 보존하는 단계다.

### B. SC8 구조 분해

SC8의 각 D×H 출력에서 다음 구조를 추출한다.

- 고정 프레임과 반복 슬롯
- 입력 원자가 들어간 정확한 출력 위치
- 선택된 원자와 거절된 후보
- 병합·정렬·중복 제거·이름 치환 규칙
- Rashi 단독 문장, Bhava 단독 문장, 결합 문장 사이의 경계
- 값이 없는 경우의 표기와 문장 생략 방식
- 동일 구조 안에서 바뀌는 variable과 고정되는 invariant

### C. 대응 정렬

각 SC8 span을 하나 이상의 SC7 Source Anchor에 연결한다. 연결되지 않는
SC8 span이나 사용되지 않은 SC7 원자는 즉시 예외문으로 덮지 말고
`UNEXPLAINED → HOLD`로 남긴다.

### D. 규칙 후보 생성

여러 D×H에서 반복되는 변환을 한 개의 일반 규칙 후보로 만든다. 규칙은
최소한 아래 질문에 답해야 한다.

1. 어떤 입력 원자를 본다?
2. 어떤 조건에서 이 규칙이 선택되는가?
3. 어떤 후보를 왜 버리는가?
4. 어떤 순서와 위치로 SC8을 만든다?
5. SC8만 보고 어떤 단서로 SC7 원자를 복원하는가?
6. 정보가 소실되거나 다의적인 경우 어떤 terminal state를 부여하는가?

### E. 최소 문법 선택

차트별 이름이나 D 번호를 조건으로 삼는 patch보다, 더 많은 대응쌍을 동일한
조건으로 설명하는 최소 규칙을 우선한다. 단, 더 짧다는 이유로 Source 차이를
지우지 않는다. 예외가 필요하면 먼저 다음을 증명한다.

- 일반 규칙으로 설명되지 않는 직접 Source 차이가 있다.
- 예외의 적용 범위가 명시되어 있다.
- forward와 inverse 모두에서 동일하게 판별할 수 있다.

이 세 조건을 충족하지 못하면 예외가 아니라 `HOLD`다.

### F. Rashi → Bhava → 결합 순서

1. Rashi lane의 forward/inverse 문법을 먼저 고정한다.
2. Bhava lane의 forward/inverse 문법을 별도로 고정한다.
3. 둘을 섞지 않은 상태에서 각각 round-trip한다.
4. 마지막에 Rashi–Bhava 이동·공동장·우선순위·충돌 해결 규칙을 결합한다.

Bhava를 Rashi의 단순 복사나 재계산 결과로 가정하지 않는다. 두 lane의
Source 경계와 역할을 유지한다.

## 5. 양방향 불변식

허용되는 최종 문법은 아래 두 식을 등록 범위 전체에서 만족해야 한다.

```text
Reverse(Forward(SC7)) = SC7
Forward(Reverse(SC8)) = SC8
```

비교는 단순 의미 유사도가 아니라, 등록된 canonicalization 규칙을 제외한
구조·슬롯·Source binding·terminal state의 재현으로 판정한다. canonicalization
규칙 자체도 명시적이고 양방향이어야 한다.

한 방향만 재현되는 규칙은 완성 규칙이 아니다. 역변환 시 원본을 하나로
결정할 수 없으면 `LOSSY_OR_AMBIGUOUS → HOLD`로 남긴다.

## 6. 규칙 레코드 문법

각 규칙은 다음 필드를 반드시 가진다.

```text
RULE_ID
RULE_VERSION
SC7_SOURCE_ANCHOR
INPUT_ATOMS
MATCH_CONDITION
SELECTED_ROUTE
REJECTED_ROUTES_AND_WHY
FORWARD_RULE
OUTPUT_POSITION
INVERSE_MATCH_CONDITION
INVERSE_RULE
CANONICALIZATION
EMPTY_RULE
HOLD_RULE
VOID_RULE
APPLICABLE_D
APPLICABLE_LANE
APPLICABLE_H
EXCEPTIONS
EVIDENCE_PAIRS
ROUND_TRIP_STATE
```

`MATCH_CONDITION`에는 특정 차트의 정답 문자열을 직접 넣지 않는다.
`EXCEPTIONS`는 일반 규칙의 실패 증거와 양방향 판별 기준을 함께 가진다.

## 7. Terminal state

- `PASS`: 직접 Source와 양방향 round-trip이 모두 일치한다.
- `EMPTY`: Source 구조상 값이 존재하지 않음이 확인된다.
- `HOLD`: Source 부족, 충돌, 다의성, 정보 소실, 미설명 차이가 있다.
- `VOID`: 현재 운영 대상이 아니다. 3P 20개는 물리적으로 보존하되 VOID다.
- `CONFLICT`: 직접 Source끼리 양립할 수 없는 값을 보인다.

`HOLD`, `VOID`, `CONFLICT`를 빈 문자열이나 임의 기본값으로 바꾸지 않는다.

## 8. 금지사항

- OCR을 주작업으로 다시 수행하지 않는다.
- SC8을 검증용 정답표로만 쓰고 SC7→SC8 생성 문법을 생략하지 않는다.
- 점성술 공식으로 SC7/SC8 값을 재계산해 Source를 덮어쓰지 않는다.
- 40개 대응쌍을 40개의 개별 템플릿으로 하드코딩하지 않는다.
- 파일명 변경·복사·이웃 D 재사용으로 새 D×H를 만들지 않는다.
- 단순 문자열 diff, 빈도, 파일 순서를 역사적 판단 인과로 단정하지 않는다.
- 검증기 제작을 문법 추출 완료로 보고하지 않는다.
- 실제 전수 실행 전 `600/600`, `580/580`, `480/480`을 주장하지 않는다.
- 별도 사용자 승인 없이 신규 공개 호출키를 활성화하지 않는다.

## 9. 실행 단계와 산출물

### Phase 0 — 등록 및 Source reopen

- 등록 manifest와 ZIP hash/CRC/D/lane inventory를 확인한다.
- 이 단계의 PASS는 **등록 무결성 PASS**일 뿐 문법 PASS가 아니다.

### Phase 1 — Rashi 문법

- 20D × 12H의 SC7↔SC8 대응을 정렬한다.
- forward와 inverse 규칙을 동시에 작성한다.
- Rashi round-trip coverage와 HOLD를 분리한다.

### Phase 2 — Bhava 문법

- Phase 1과 독립적으로 동일 절차를 수행한다.
- Bhava 고유 이동·house-function 규칙을 Rashi 규칙에 섞지 않는다.

### Phase 3 — Rashi–Bhava 결합

- 이동, 공동장, 우선순위, 중복 제거, 충돌 처리 문법을 고정한다.
- 독립 lane round-trip을 깨뜨리는 결합 규칙은 채택하지 않는다.

### Phase 4 — 480-unit 전수 왕복

- 20D × 12H × 2 lanes의 모든 단위를 실행한다.
- 단 하나라도 미설명 차이가 있으면 해당 규칙·의존 범위만 `HOLD`한다.

### Phase 5 — 전체 600/580 확장

- Rashi/Bhava에서 고정한 추론 프레임을 다른 PIKACHU lane으로 확장한다.
- 3P 20개는 별도 사용자 승인 전까지 실행하지 않는다.
- 580 active member 전수 round-trip 후에만 해당 분모의 PASS를 판단한다.

등록된 목표 산출물:

1. `SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR.md`
2. `sc7_sc8_rashi_bhava_grammar.yaml`
3. deterministic forward runner
4. deterministic reverse runner
5. `coverage_report.json`
6. `hold_registry.json`
7. 20D별 forward/reverse evidence ledger

현재 등록 시점에는 위 실행 산출물이 아직 생성되지 않았다.

## 10. 완료 기준

현재 등록 작업의 완료 기준:

- 작업지시서와 두 Source ZIP이 KANI V10 manifest에 해시 잠금된다.
- 등록 validator가 정확한 20D·40 pairs·80 files inventory를 PASS한다.
- KANI boot validator가 기존 V9/V10 상태를 손상 없이 PASS한다.
- 문법 실행 상태는 계속 `NOT_EXECUTED`로 정확히 남는다.

향후 문법 작업의 완료 기준:

- Rashi, Bhava, 결합 문법이 분리되어 명시된다.
- 모든 규칙이 forward와 inverse를 가진다.
- 480 D×H 단위의 round-trip 결과가 증거 ledger에 기록된다.
- 미설명 단위가 0이거나, 미설명 범위가 누락 없이 `HOLD` registry에 있다.
- 차트별 하드코딩 없이 같은 runner로 등록 범위를 재생한다.
- 실제 확장 실행 없이 전체 600/580 완료를 선포하지 않는다.

## 11. 현재 상태 잠금

```text
REGISTRATION=PASS_WHEN_HASH_LOCKED_AND_BOOT_VALIDATED
GRAMMAR_EXTRACTION=NOT_EXECUTED
FORWARD_RUNNER=NOT_CREATED
REVERSE_RUNNER=NOT_CREATED
ROUND_TRIP_480=HOLD_UNEXECUTED
FULL_PHYSICAL_600=HOLD_UNEXECUTED
ACTIVE_NON_3P_580=HOLD_UNEXECUTED_FOR_THIS_GRAMMAR
NEW_PUBLIC_CALL_KEY=HOLD_UNTIL_SEPARATE_USER_REQUEST
FINAL_FNA98_RUNTIME=HOLD_UNTIL_EXISTING_REAL_RUNTIME_GATES_PASS
```
