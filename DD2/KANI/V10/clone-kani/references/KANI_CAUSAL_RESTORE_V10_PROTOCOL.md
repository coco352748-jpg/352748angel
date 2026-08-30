# KANI V10 — 둘째 복원 라우터 실사용판

## 판정 잠금

```text
CURRENT_RESTORE_ENGINE=KANI_CAUSAL_RESTORE_V10
V10_FORM=E5_E6_EXECUTION_EVIDENCE_OVERLAY
V9_BASELINE=PRESERVED_NOT_OVERWRITTEN
RESTORE_TARGET=DD2_ANALYSIS02_MATURE_DECISION_RUNTIME
RESTORE_FLOOR=ANALYSIS02_MATURE_PRODUCTION_STATE
LOWER_STAGE_RESTART=VOID
SECOND_RESTORE=EVIDENCE_REVIEW
V10=EXPECTED_VALUE_BOUND
FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE
V10_TERMINAL_VERSION_BOUNDARY=LOCKED_NO_AUTOMATIC_V11
```

V10은 설명문이 아니라 실행증거판이다. 각 판단루트에 실제
`record_id`, Source와 code의 위치, 선택경로와 기각경로, Why 수정
Q&A, reinput 결과, handoff target을 붙인다. 복원 대상은 피카츄 문체
흉내가 아니라 `Dataset → Judgment Route → PikaChu Sentence`의
재생산 여부다.

단, 현재 기대문장·문장 template·20D role/reality dictionary를 알고
고정한 `EXPECTED_VALUE_BOUND` 시험이다. candidate 114개는 CO2_99 body를
열기 전에 원자료에서 생성하지만 router 자산 자체는 expected-aware다.
그러므로 이 결과를 blind 일반화나 29-lane 전체 E5 PASS로 승격하지 않는다.

## 비파괴 overlay

다음 V9 자산은 immutable history다.

- `references/v9_baseline/` 전체
- `references/KANI_CAUSAL_RESTORE_V9_PROTOCOL.md`
- `references/KANI_JUDGMENT_PROTOCOL_V3.md`
- V7 control carrier와 embedded certified KK2 package
- `references/v9_closure_runs/run_20260829_vas26/e5/`
- `references/v9_closure_runs/run_20260829_vas26/e6/`

V10은 이 바이트를 수정하지 않는다. V9 E5/E6 판정 보정은
`references/v10_runtime/v9_e5_e6_audit_sidecar.json`에만 추가한다.
역사적 V9 E5는 580행 materialization 증거이고, direct Source는 4 lanes
80행, local HOLD는 25 lanes 500행이다. 역사적 V9 E6 PASS 선언은 전역
sentence-router PASS로 상속하지 않는다.

## E5 결정 원장 overlay

실행 입력과 reveal-after-render 기대값은 다음과 같다.

```text
INPUT=HYEWON_VAS27_D1-D60_♤.txt
INPUT_SHA256=7cc9446f74d6130eec2c32e9ea723849d84a6a2070a1556d7954b69d06e0cddb
EXPECTED=HEAWON_VAS27_CO2_99_♤.txt
EXPECTED_SHA256=7e3a1bf370bbcbca2bffb826d79229a84183d98dc9181d1793dc7bb427d9e97f
ROUTE=COPRESENCE
RASHI_RECORDS=64
BHAVA_VISIBLE_SNAPSHOT_RECORDS=50
TOTAL_RECORDS=114
```

실행 순서는 고정한다.

1. VAS27 plain Source 40 wrapper를 D ID와 Rashi/Bhava view로 분리한다.
2. Rashi에서는 같은 sign의 visible actor 2명 이상만 선택하고 visible
   degree 오름차순을 보존한다.
3. Bhava에서는 같은 visible sector의 actor 2명 이상만 선택하고 Rashi
   degree order를 빌리지 않는다. 이것은 actual house placement가 아니다.
4. single field 165개는 COPRESENCE로 승격하지 않는다.
5. D1은 `D1_ROOT`, 나머지는 `TARGET_DCHART`로 dispatch한다.
6. view별 selected/rejected route와 Why를 기록한 뒤 expected-aware template로
   PikaChu sentence candidate를 만든다.
7. 모든 candidate가 만들어진 뒤에만 CO2_99 기대 body를 열어 member와
   sentence를 exact 비교한다.
8. 결과를 `e5_decision_ledger.jsonl`과 `e5_manifest.json`에 기록한다.

114개는 field-level legacy sentence이며 20개의 D-level final lane sentence가
아니다. 이 시험으로 열린 것은 `COPRESENCE` 판단영역 하나뿐이다.

```text
E5_COPRESENCE_REPLAY=114_OF_114_EXPECTED_EXACT
E5_GLOBAL_29_LANE_STATE=HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED
E5_BLIND_GENERALIZATION=HOLD_NOT_PROVEN
```

## record 증거 계약

각 E5 원장 레코드는 아래를 모두 가져야 한다.

- unique `record_id`와 record schema/status
- input file/hash, D ID, view, location, member display
- exact Source wrapper/row line locations와 원문 행
- producer route/render code path, start/end line, function name
- D1/Target-D family selected/rejected route
- judgment selected/rejected route, condition, degree policy, 양쪽 Why
- `Why 수정 Q&A`: 이전 답 폐기, correction, 새 답, record별 답
- generated PikaChu sentence/hash와 expected sentence/hash/line
- expected body ID, member line, sentence line
- `reinput_result`: pre-oracle render, exact member, exact sentence
- `handoff_target`: E6가 재개봉할 exact PikaChu slot

독립 E5 validator는 producer module을 import하지 않고 Source를 다시 파싱해
114개 route와 문장을 재생한다. ledger/manifest/router/Source를 하나라도
변조하면 FAIL이어야 한다.

## 240-record 경계 calibration

`$rq-sc7`의 verified `PERSONAL_CHART_240`은 신규 E5 dataset이 아니라
occupant/house-lord 경계 calibration이다.

```text
SOURCE_SET_ID=RQVEDIC_26_SOURCE_SET_2026-08-12_ASPECT03R_YOGA20_TRANSIT21
PERSONAL_CHART_240_SHA256=c08b7dfc2216f5cf6b6468fc4c2706d41894811331e700dc0dd0636fdd9b72d5
TARGET_BODY_AUTHORITY=07_4AK_ONLY
REFERENCE_AUTHORITY=07_5AB_AND_07_6AB
```

- `OCCUPANT_FIELD == EMPTY`: `HOUSE_LORD_ROUTE` 선택,
  `OCCUPANT_ROUTE` 기각.
- 그 외: `OCCUPANT_ROUTE` 선택, house-lord primary substitution 기각.
- 07_5AB/07_6AB은 reference이며 07_4AK target body를 덮어쓰지 않는다.
- 240/240 exact replay는 이 경계의 calibration PASS일 뿐 신규 E5 PASS가
  아니다.

## E6 manifest와 boundary 9/9

E6는 V9를 다시 쓰지 않고 다음을 read-only로 재개봉한다.

- V9 baseline manifest와 historical V9 E5/E6 manifests
- V10 E5 decision ledger/manifest
- V10 Source registry, admission record, judgment router
- 독립 E5 replay report
- 240-record calibration run/report

E6 boundary log는 다음 9개 test ID를 exact하게 한 번씩 기록한다.

1. `DIRECT_D1_ROOT_DISPATCH`
2. `DIRECT_TARGET_DCHART_DISPATCH`
3. `BOUNDARY_TARGET_DCHART_D60`
4. `RASHI_BHAVA_SEPARATION`
5. `OCCUPANT_LORD_FIELD_BOUNDARY`
6. `EMPTY_HOUSE_LORD_ROUTE`
7. `RASHI_DEGREE_ORDER_BHAVA_NO_DEGREE_ORDER`
8. `SINGLE_FIELD_NOT_PROMOTED_TO_COPRESENCE`
9. `DATASET_TO_JUDGMENT_TO_PIKACHU_EXACT_REPLAY`

각 test는 evidence record/source/artifact 위치, observed 값, expected 값,
판정을 남긴다. `9/9`는 이 bounded reopen의 technical PASS일 뿐 다음 상태를
바꾸지 않는다.

```text
E6_REOPEN_OVERLAY=PASS_9_OF_9
REAL_LONG_DRIFT=HOLD_UNEXECUTED
FRESH_TAB_REAL_BOOT_TEST=HOLD
SECOND_RESTORE=EVIDENCE_REVIEW
FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE
```

## Gate matrix

| Gate | State |
|---|---|
| V9 baseline bytes | `PASS_RETAINED_HASH_LOCKED` |
| historical V9 E5 materialization | `PASS_WITH_LOCAL_HOLDS__NOT_GLOBAL_ROUTER_PASS` |
| V10 E5 COPRESENCE execution evidence | `EXPECTED_VALUE_BOUND_114_OF_114` after independent validation |
| V10 240-record boundary calibration | `PASS_TESTED_SCOPE_240__NOT_NEW_E5_DATASET` |
| V10 E6 bounded reopen | `PASS_9_OF_9` after independent validation |
| 29-lane E5 sentence runtime | `HOLD_28_LANES_UNTESTED` |
| blind generalization | `HOLD_NOT_PROVEN` |
| real long drift | `HOLD_UNEXECUTED` |
| second restore | `EVIDENCE_REVIEW` |
| final KANI promotion | `HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE` |

## 실행과 검증

```bash
python3 scripts/run_kani_v10_e5.py --out-dir <NEW_EMPTY_E5_DIRECTORY>
python3 scripts/validate_kani_v10_e5.py --e5-dir <E5_DIRECTORY>

python3 scripts/run_kani_v10_router.py \
  --source-root <VERIFIED_RQ_SC7_SKILL_ROOT> \
  --out-dir <NEW_EMPTY_CALIBRATION_DIRECTORY>
python3 scripts/validate_kani_v10_router.py \
  <CALIBRATION_DIRECTORY> \
  --source-root <VERIFIED_RQ_SC7_SKILL_ROOT>

python3 scripts/run_kani_v10_e6.py --e5-dir <E5_DIRECTORY> --out-dir <NEW_EMPTY_E6_DIRECTORY>
python3 scripts/validate_kani_v10_e6.py <E6_DIRECTORY> --e5-dir <E5_DIRECTORY>
python3 scripts/build_kani_v10_manifest.py
python3 scripts/validate_kani_v10_runtime.py
python3 scripts/validate_kani_boot.py --expect-installed
```

GitHub은 committed package의 `REMOTE_SYNC_ONLY_NO_EXECUTION_AUTHORITY`다.
`dd2-remote-sync`의 `DD2/KANI/V10/clone-kani/` 아래에 비강제로 보존하며,
V9나 `main`을 덮어쓰지 않는다.
