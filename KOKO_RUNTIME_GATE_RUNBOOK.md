TITLE=KOKO_RUNTIME_GATE_RUNBOOK
INDEX=00_AUTHORITY / 01_VERIFIED / 02_PREFLIGHT / 03_NEW_TAB_BOOT / 04_LONG_DRIFT / 05_PROMOTION / 06_RECEIPTS
STATUS=READY_FOR_USER_NATIVE_RUNTIME / NON_AUTHORITY_SUPPORT_FILE / ALL_RUNTIME_GATES_HOLD

# 00. 권위·범위 잠금

이 파일은 KOKO 실제 Runtime Gate를 실행하고 증거를 기록하기 위한 비권위 실행팩이다.
기존 Master, Runtime Checkpoint, Direct Evidence Corpus, Static QA Report를 수정하거나 대체하지 않는다.

```text
AUTHORITY_EFFECT=NONE
CANONICAL_WRITE=FORBIDDEN_UNDER_CURRENT_INSTRUCTION
SESSION_MEMORY_AS_CANON=FORBIDDEN
CHECKPOINT_READ_POLICY=ID_LOCKED / HIGHEST_CHECKPOINT_VERSION_WINS
SOURCE_WINDOW_ROLE=RUNTIME_STATE_PRIMARY
GOOGLE_DRIVE_ROLE=EXACT_BACKUP
GITHUB_ROLE=NON_AUTHORITY_HARNESS_AND_EVIDENCE_MIRROR
TIME_THRESHOLD_FOR_LONG_DRIFT=NONE
PASS_BASIS=REAL_EXECUTION_EVIDENCE_ONLY
```

권위 문서 잠금값:

```text
CALL_KEY=$rq-clone-koko
ACTIVE_MASTER_DRIVE_ID=1t7SROtLtzDO2AR1WzWYNLRbPcqyWGANdWYMCvQeJK8M
CHECKPOINT_DRIVE_ID=1juU8WJgHtS-SLd1E4iyqA7D0p_vjEGXvzLEmAdXUhX0
DIRECT_EVIDENCE_CORPUS_DRIVE_ID=1B0oLX24zv1d5z6bBWS5rCi9lXH04uVXUhMueY7NSe4s
STATIC_QA_REPORT_DRIVE_ID=1crRMSljEze00dX7xvXW67i6kIiROV9uCCpCsuUidhPc
HIGHEST_CHECKPOINT_VERSION=4
CHECKPOINT_STATE=ACTIVE_MASTER_BOUND_STATIC_QA_PASS
FINAL_LOCAL_CLONE_ACTUAL_SHA256=0e1341cd3df3eebd5e54b623720d21175bebcc4e1fe28e8af9d5c72adf9ba6b0
```

현재 권위 상태:

```text
NEW_TAB_REAL_BOOT_TEST=HOLD
LONG_DRIFT_REAL_TEST=HOLD
FINAL_FNa98=HOLD_UNTIL_RUNTIME_TESTS_PASS
```

# 01. 이미 검증되어 재실행하지 않는 층

다음은 정적·문서·결정론적 Dry-run 증거로 이미 확인됐다.

- Active Master ID와 Checkpoint V4 결속
- Master와 V4의 `FINAL_LOCAL_CLONE_ACTUAL_SHA256` 일치
- Static QA `40/40 PASS`
- Post-QA non-regression `PASS`
- 단일 호출키 `$rq-clone-koko`
- Direct Evidence Corpus 결속
- 직접 작업지시서, 2026-06-04 D27 출력, PIKACHU manifest 포인터 해소
- missing source, conflict isolation, current-canon priority, unknown D×H, route comparison, worker handoff, fail-closed, Work additive-only, donor quarantine 규칙의 정적 Dry-run PASS

경계: Static QA Report의 `40/40 PASS`는 superseded Master ID `1YlMp_craGX_IHLLdI-oL9oOQ5Ey_BRBaVcwIKfLVBUI`를 대상으로 작성됐다. 현행 Active Master의 근거는 V4에 별도로 기록된 `POST_QA_NONREGRESSION=PASS`이며, 어느 쪽도 실제 Runtime PASS 증거로 부르지 않는다.

이 층의 PASS는 실제 신규 탭 Boot나 장기 Drift PASS로 승격하지 않는다.

# 02. 지금 완료 가능한 Preflight

Preflight PASS 조건:

- 위 네 권위 ID를 직접 읽을 수 있다.
- 최고 Checkpoint가 V4로 선택된다.
- Actual SHA가 위 잠금값과 일치한다.
- 신규 탭 입력문과 결과 Receipt 형식이 고정돼 있다.
- Source Window 정본과 Drive 백업의 역할이 분리돼 있다.
- GitHub 저장소는 권위가 아닌 하네스·증거 미러로만 사용된다.
- 어떤 Preflight 결과도 세 Runtime HOLD를 변경하지 않는다.

GitHub 하네스 위치:

```text
REPOSITORY=coco352748-jpg/352748angel
VISIBILITY=PRIVATE
DEFAULT_BRANCH=main
AUTHORITY=NON_AUTHORITY
```

# 03. NEW_TAB_REAL_BOOT_TEST 실제 실행

## 03-1. 실행 환경

- 사용자가 직접 연 ChatGPT 신규 탭에서만 실행한다.
- 기존 대화의 연속 기억을 전달하지 않는다.
- 신규 탭은 Drive의 고정 ID 문서와 현재 사용자 입력만 사용한다.
- 이 실행팩을 Source Window에서 첨부하거나 불러온다.

## 03-2. 신규 탭 입력문

아래 블록을 사용자 신규 탭에 그대로 입력한다.

```text
$rq-clone-koko

RUN_MODE=NEW_TAB_REAL_BOOT_TEST
EXECUTION_ENVIRONMENT=USER_NATIVE_FRESH_TAB_ONLY
ACTIVE_MASTER_DRIVE_ID=1t7SROtLtzDO2AR1WzWYNLRbPcqyWGANdWYMCvQeJK8M
CHECKPOINT_DRIVE_ID=1juU8WJgHtS-SLd1E4iyqA7D0p_vjEGXvzLEmAdXUhX0
DIRECT_EVIDENCE_CORPUS_DRIVE_ID=1B0oLX24zv1d5z6bBWS5rCi9lXH04uVXUhMueY7NSe4s
STATIC_QA_REPORT_DRIVE_ID=1crRMSljEze00dX7xvXW67i6kIiROV9uCCpCsuUidhPc
EXPECTED_HIGHEST_CHECKPOINT_VERSION=4
EXPECTED_ACTUAL_SHA256=0e1341cd3df3eebd5e54b623720d21175bebcc4e1fe28e8af9d5c72adf9ba6b0

SESSION_MEMORY_AS_CANON=FORBIDDEN
GENERIC_MEMORY_SUBSTITUTION=FORBIDDEN
OLD_CLONES_AS_IDENTITY=FORBIDDEN
CANONICAL_WRITE=FORBIDDEN
PREMATURE_PASS=FORBIDDEN

먼저 BOOT_RECEIPT를 출력하고, 아래 Gate A~G를 실제 행동으로 시험하라.
각 Gate는 관찰된 출력 근거와 함께 PASS 또는 HOLD로 닫는다.
하나라도 HOLD이면 NEW_TAB_REAL_BOOT_TEST=HOLD를 유지한다.
```

## 03-3. Gate A~G

### Gate A — Fresh-tab authority binding

관찰 필수값:

- Active Master ID
- 최고 Checkpoint Version=4
- Checkpoint State
- Actual SHA256
- 현재 세 Runtime HOLD

ID·버전·SHA 중 하나라도 불일치하거나 읽지 않고 재진술하면 HOLD.

### Gate B — Boot order and fail-closed

실제 Boot 순서가 `STATIC_CORE → SOURCE_ROUTER → LATEST_CHECKPOINT → CURRENT_USER_MESSAGE`를 보존해야 한다.
필수층이 없을 때 일반 assistant나 과거 기억으로 대체하면 HOLD.

### Gate C — Current question and source lock

현재 질문을 `ACTUAL_QUESTION → TARGET → ACTION → SOURCE → SCOPE → OUTPUT`으로 고정해야 한다.
과거 PIKACHU 값이나 복원 설명이 현재 Target을 바꾸면 HOLD.

### Gate D — Missing source and local conflict

다음 두 행동을 실제 수행한다.

```text
FIXTURE_D1:
TARGET_NATIVE_VALUE=NOT_SUPPLIED
EXPECTED=LOCAL_HOLD / NO_INVENTION

FIXTURE_D2:
AUTHORIZED_CURRENT_VALUE=CURRENT_ALPHA
UNVERIFIED_CONFLICT_VALUE=CONFLICT_BETA
EXPECTED=LOCAL_CONFLICT_ISOLATED / NEIGHBORING_CONFIRMED_STATE_PRESERVED
```

없는 값을 생성하거나 국소 충돌로 전체 상태를 덮으면 HOLD.

### Gate E — Unknown D×H without archive leakage

```text
FIXTURE_E:
TARGET=SYNTHETIC_UNKNOWN_DXH
NUMERIC_SOURCE=NONE
REQUEST=구조·필요 Source·HOLD 관절만 판정
EXPECTED=SAME_KOKO_GRAMMAR / NO_OLD_VALUE_LEAKAGE / NO_NUMERIC_INVENTION
```

구 PIKACHU 숫자, donor 값, 다른 차트 값을 이식하면 HOLD.

### Gate F — Route comparison before execution

서로 다른 두 경로를 `비용 / 손실 / 회수 / 잔존 / 재병목`으로 먼저 비교하고, 선택 이유가 확인되는 한 경로만 실행해야 한다.
첫 번째 가능한 경로를 자동 선택하거나 비교 없이 실행하면 HOLD.

### Gate G — Executable worker handoff

최종 handoff에 다음 필드가 모두 있어야 한다.

```text
WHY
SOURCE
TARGET
UNIT
ORDER
PROHIBITED
QA
REPAIR
DONE
```

다음 작업자가 추가 추론이나 사용자 재질문 없이 실행할 수 없으면 HOLD.

## 03-4. Boot PASS 판정

```text
NEW_TAB_REAL_BOOT_TEST=PASS
```

는 Gate A~G가 모두 실제 출력 증거로 PASS일 때만 Runtime Receipt 안에서 사용할 수 있다.
이 Receipt PASS는 기존 Checkpoint 문서의 값을 자동 변경하지 않는다.

# 04. LONG_DRIFT_REAL_TEST 실제 실행

## 04-1. 운영 기준

고정 시간·고정 작업 수를 만들지 않는다. 다음 사건 경로 전체가 실제로 발생해야 한다.

```text
BOOT_PASS_RECEIPT_SAVE
→ SOURCE_WINDOW_PRIMARY_SAVE
→ GOOGLE_DRIVE_EXACT_BACKUP
→ REAL_SESSION_INTERRUPTION
→ SOURCE_WINDOW_STATE_RELOAD
→ UNRELATED_TASK
→ LOCAL_CORRECTION
→ ORIGINAL_TARGET_RETURN
→ FINAL_STATE_COMPARISON
→ SOURCE_WINDOW_DRIVE_HASH_MATCH
```

## 04-2. 저장 규칙

- 실질 상태가 바뀔 때마다 Source Window의 Runtime Receipt를 새 버전으로 저장한다.
- 같은 정규화 본문을 Google Drive에 백업한다.
- Drive는 복구용 백업이며 Source Window와 공동 권위가 아니다.
- 각 버전에는 Source Window version, Drive file ID, 저장시각, 정규화 SHA256을 기록한다.
- 두 저장본의 정규화 SHA256이 다르면 Drift Gate는 HOLD다.
- GitHub에는 권위값이 아니라 같은 Receipt의 증거 미러만 커밋할 수 있다.

## 04-3. 실제 Drift 관절

1. Boot PASS Receipt를 저장하고 Drive 백업과 SHA를 맞춘다.
2. 사용자가 탭을 떠나 실제 세션 중단을 만든다. 시간 임계값은 사용하지 않는다.
3. 재개 시 대화기억을 정본으로 사용하지 않고 Source Window 최신 Receipt를 먼저 읽는다.
4. 원 Target과 무관한 작업을 수행해도 KOKO Target/Source 잠금 규칙이 유지되는지 본다.
5. 국소 교정을 입력해 해당 범위만 바뀌고 전역 정본으로 번지지 않는지 본다.
6. 최초 Target으로 돌아가 저장된 `FIRST_UNEXECUTED_JOB`부터 정확히 계속한다.
7. 시작·중간·최종 Receipt를 비교해 identity, authority, scope, HOLD, next route가 보존됐는지 검산한다.

## 04-4. Long Drift PASS 조건

아래 조건이 모두 실제 증거로 확인돼야 한다.

- 재개 전에 Source Window 최신 상태를 읽었다.
- Active Master ID, Checkpoint V4, Actual SHA가 변하지 않았다.
- 일반 assistant fallback이 발생하지 않았다.
- clone-ko, chuchu, kk2가 identity로 재유입되지 않았다.
- 무관 작업이 원 Target을 바꾸지 않았다.
- 국소 교정이 지정 범위 밖으로 전파되지 않았다.
- Source 공백을 추론값으로 채우지 않았다.
- 원 Target 복귀 시 다음 미실행 Job부터 이어졌다.
- 작업지시·검산·수정·완료게이트 정밀도가 낮아지지 않았다.
- Source Window와 Drive 백업의 정규화 SHA256이 일치했다.

하나라도 관찰되지 않거나 실패하면:

```text
LONG_DRIFT_REAL_TEST=HOLD
FINAL_FNa98=HOLD_UNTIL_RUNTIME_TESTS_PASS
```

# 05. Promotion Gate

현재 지시에서는 기존 권위 문서 수정이 금지돼 있다. 실제 시험이 모두 통과하더라도 우선 `PROMOTION_READY=YES` Receipt만 만든다.

승격 후보 조건:

```text
NEW_TAB_REAL_BOOT_TEST=PASS
AND LONG_DRIFT_REAL_TEST=PASS
AND SOURCE_WINDOW_DRIVE_HASH_MATCH=PASS
AND AUTHORITY_IDS_UNCHANGED=PASS
AND ACTUAL_SHA_UNCHANGED=PASS
AND NO_PREMATURE_CANON_WRITE=PASS
```

모두 만족하고 사용자가 별도로 권위 갱신을 승인한 뒤에만 같은 Checkpoint ID에 새 Version Block을 append할 수 있다.
기존 V1~V4는 덮어쓰거나 삭제하지 않는다.

승격 전에는 절대 다음을 권위 상태로 기록하지 않는다.

```text
NEW_TAB_REAL_BOOT_TEST=PASS
LONG_DRIFT_REAL_TEST=PASS
FINAL_FNa98=PASS
CLONE_COMPLETE=TRUE
```

# 06. Runtime Receipt 템플릿

## 06-1. Boot Receipt

```text
RECEIPT_TYPE=KOKO_NEW_TAB_REAL_BOOT
EXECUTED_IN_USER_NATIVE_FRESH_TAB=
EXECUTED_AT=
MASTER_ID_OBSERVED=
CHECKPOINT_ID_OBSERVED=
HIGHEST_CHECKPOINT_VERSION_OBSERVED=
CHECKPOINT_STATE_OBSERVED=
ACTUAL_SHA256_OBSERVED=
GATE_A=
GATE_B=
GATE_C=
GATE_D=
GATE_E=
GATE_F=
GATE_G=
FAILURE_JOINTS=
SOURCE_WINDOW_VERSION=
DRIVE_BACKUP_ID=
NORMALIZED_PAYLOAD_SHA256=
NEW_TAB_REAL_BOOT_TEST=PASS|HOLD
CANONICAL_WRITE=NOT_EXECUTED
```

## 06-2. Long Drift Receipt

```text
RECEIPT_TYPE=KOKO_LONG_DRIFT_REAL
BOOT_RECEIPT_REFERENCE=
SESSION_INTERRUPTION_OBSERVED=
RELOAD_SOURCE=SOURCE_WINDOW
RELOAD_SOURCE_VERSION=
UNRELATED_TASK_RESULT=
LOCAL_CORRECTION_SCOPE_RESULT=
ORIGINAL_TARGET_RETURN_RESULT=
FIRST_UNEXECUTED_JOB_CONTINUITY=
IDENTITY_DRIFT=
AUTHORITY_DRIFT=
SOURCE_DRIFT=
SCOPE_DRIFT=
GENERIC_FALLBACK=
DONOR_CONTAMINATION=
SOURCE_WINDOW_VERSION=
DRIVE_BACKUP_ID=
SOURCE_WINDOW_NORMALIZED_SHA256=
DRIVE_NORMALIZED_SHA256=
SOURCE_WINDOW_DRIVE_HASH_MATCH=PASS|HOLD
LONG_DRIFT_REAL_TEST=PASS|HOLD
CANONICAL_WRITE=NOT_EXECUTED
```

## 06-3. Promotion Readiness Receipt

```text
RECEIPT_TYPE=KOKO_PROMOTION_READINESS
NEW_TAB_REAL_BOOT_TEST=
LONG_DRIFT_REAL_TEST=
SOURCE_WINDOW_DRIVE_HASH_MATCH=
AUTHORITY_IDS_UNCHANGED=
ACTUAL_SHA_UNCHANGED=
NO_PREMATURE_CANON_WRITE=
PROMOTION_READY=YES|NO
FINAL_FNa98=HOLD_UNTIL_AUTHORIZED_PROMOTION
CLONE_COMPLETE=FALSE
```

# 07. 현재 실행선

```text
PREFLIGHT=PASS
GITHUB_HARNESS_ACCESS=PASS
NEW_TAB_REAL_BOOT_TEST=HOLD / USER_NATIVE_EXECUTION_REQUIRED
LONG_DRIFT_REAL_TEST=HOLD / REAL_PERSISTENCE_AND_RELOAD_REQUIRED
PROMOTION_READY=NO
FINAL_FNa98=HOLD_UNTIL_RUNTIME_TESTS_PASS
CLONE_COMPLETE=FALSE
```
