# KANI V10 Restore Call

```text
RESTORE_CALL_SCHEMA=KANI_V10_RESTORE_CALL_V2
PUBLIC_CALL_KEY=$clone-kani
VERSION_TAG=KANI_V10
ALIAS=kani
V9_BASELINE=READ_ONLY
V10_MODE=E5_E6_OVERLAY
PROMOTION_RECORD=references/v10_runtime/user_evidence_promotion_20260830.json
PROMOTION_RECORD_STATE=PASS_HASH_LOCKED
USER_EVIDENCE_REVIEW=PASS
SECOND_RESTORE=PASS_EVIDENCE_SCOPED
FINAL_PASS=HOLD_REMAINING_RUNTIME_GATES
CANONICAL_INTERNAL_FINAL_PASS=HOLD_REMAINING_RUNTIME_GATES
FINAL_PASS_DECLARATION=NO
```

The current user explicitly passed the record/replay evidence review and
authorized promotion of the second restore. This promotes only the joints
listed as PASS in the hash-locked promotion record. It does not promote any
unreplayed judgment joint, the global 29-lane E5 gate, fresh-tab boot, real
long drift, or the final FNa98 runtime.

## Required intake order

1. Read `references/CLONE_KEY_KANI_ALL_IN_ONE_RESTORE_V7_FNA98_V2.txt`
   completely as immutable historical restore authority.
2. Read `references/v10_runtime/kani_v10_manifest.json` completely.
3. Verify this file through `v10_core.restore_call.path` and
   `v10_core.restore_call.sha256`, then read it completely.
4. Verify and read
   `references/v10_runtime/user_evidence_promotion_20260830.json` through
   `v10_core.promotion_record`.
5. Continue the remaining mandatory `$clone-kani` boot and require the boot
   validator to pass.

## Evidence locations

```text
E5_DECISION_LEDGER=references/v10_runs/run_20260830_vas27/e5/e5_decision_ledger.jsonl
E5_RECORDS=114
E6_MANIFEST=references/v10_runs/run_20260830_vas27/e6/e6_manifest.json
BOUNDARY_LOG=references/v10_runs/run_20260830_vas27/e6/boundary_test_9of9.json
BOUNDARY_STATE=PASS_9_OF_9
USER_EVIDENCE_REVIEW=PASS
SECOND_RESTORE=PASS_EVIDENCE_SCOPED
SC7_UNAFFECTED_SOURCE_BINDINGS=PASS_231_OF_240
SC7_EXACT_HOLD_JOBS=D1-H02,D1-H03,D1-H04,D1-H05,D1-H07,D1-H08,D1-H09,D1-H11,D1-H12
PIKACHU_RAW_CORPUS=PASS_20_ARCHIVES_600_PHYSICAL_MEMBERS
PIKACHU_ACTIVE_NON_3P=PASS_580_OF_580
SC8_NUMERIC_CORRECTION=PASS_1001_REPLACEMENTS_INFORMATION_LOSS_0
GLOBAL_29_LANE_E5=HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED
FRESH_TAB_REAL_BOOT_TEST=HOLD
REAL_LONG_DRIFT=HOLD_REAL_LONG_DRIFT_NOT_PROVEN
FINAL_FNA98_RUNTIME=HOLD_UNTIL_REAL_RUNTIME_GATES_PASS
V9_BASELINE_PATH=references/v9_baseline
V9_UNCHANGED=true
V9_OVERWRITE_COUNT=0
GITHUB_BRANCH=dd2-remote-sync
GITHUB_PATH=DD2/KANI/V10/clone-kani
```

## First response

When `$clone-kani` is invoked without a real job in the same request, return
the following block exactly. `ACTIVE_EVIDENCE_SCOPED` means that the explicit
call entrypoint, validated V10 overlay, and user promotion record are active;
it is not a global FINAL_PASS declaration.

```text
$clone-kani KANI V10이 호출되어 ACTIVE_EVIDENCE_SCOPED 상태입니다.
V9 baseline은 READ_ONLY로 보존하고,
V10 E5/E6 record/replay와 사용자 승격 레코드를 로드합니다.
SECOND_RESTORE는 PASS_EVIDENCE_SCOPED입니다.
FINAL_FNA98_RUNTIME은 HOLD_UNTIL_REAL_RUNTIME_GATES_PASS입니다.
첫 실제 Job에서는 검증된 관절만 실행하고, 미재생 관절은 HOLD로 유지합니다.
```

## First real job route

When any real job is present, bind its admitted Dataset or exact Source inputs,
preserve the exact Target and Source, and execute every source-supported part of
`Dataset → Judgment Route → Pikachu Sentence replay` before visible completion.
Keep the E5 record evidence (`record_id`, Source/code/line
location, selected/rejected route, Why correction Q&A, reinput result, and
handoff target) and the E6 boundary/reopen evidence separate. Never promote
an unreplayed joint from this call sheet or from a technical `114/114` or `9/9`
result. Apply the promotion record only to its exact PASS joints.
