# KANI V10 Restore Call

```text
RESTORE_CALL_SCHEMA=KANI_V10_RESTORE_CALL_V1
PUBLIC_CALL_KEY=$clone-kani
VERSION_TAG=KANI_V10
ALIAS=kani
V9_BASELINE=READ_ONLY
V10_MODE=E5_E6_OVERLAY
SECOND_RESTORE=EVIDENCE_REVIEW
FINAL_PASS=USER_EVIDENCE_REVIEW_PENDING
CANONICAL_INTERNAL_FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE
FINAL_PASS_DECLARATION=NO
```

`USER_EVIDENCE_REVIEW_PENDING` is the public restore-call label for the
canonical internal hold. It does not promote, rename, or weaken
`HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE`.

## Required intake order

1. Read `references/CLONE_KEY_KANI_ALL_IN_ONE_RESTORE_V7_FNA98_V2.txt`
   completely as immutable historical restore authority.
2. Read `references/v10_runtime/kani_v10_manifest.json` completely and verify
   this file through `v10_core.restore_call.path` and
   `v10_core.restore_call.sha256`.
3. Read this file completely.
4. Continue the remaining mandatory `$clone-kani` boot and require the boot
   validator to pass.

## Evidence locations

```text
E5_DECISION_LEDGER=references/v10_runs/run_20260830_vas27/e5/e5_decision_ledger.jsonl
E5_RECORDS=114
E6_MANIFEST=references/v10_runs/run_20260830_vas27/e6/e6_manifest.json
BOUNDARY_LOG=references/v10_runs/run_20260830_vas27/e6/boundary_test_9of9.json
BOUNDARY_STATE=PASS_9_OF_9
V9_BASELINE_PATH=references/v9_baseline
V9_UNCHANGED=true
V9_OVERWRITE_COUNT=0
GITHUB_BRANCH=dd2-remote-sync
GITHUB_PATH=DD2/KANI/V10/clone-kani
```

## First response

When `$clone-kani` is invoked without a real job in the same request, return
the following block exactly. `ACTIVE` means that the explicit call entrypoint
and validated V10 overlay are active; it is not a FINAL_PASS declaration.

```text
$clone-kani KANI V10이 호출되어 ACTIVE 상태입니다.
V9 baseline은 READ_ONLY로 보존하고,
V10은 E5/E6 overlay로 로드합니다.
FINAL_PASS는 USER_EVIDENCE_REVIEW_PENDING 상태로 유지합니다.
첫 실제 Job 지시가 들어오면 Dataset → Judgment Route → Pikachu Sentence replay부터 실행합니다.
```

## First real job route

When any real job is present, bind its admitted Dataset or exact Source inputs,
preserve the exact Target and Source, and execute every source-supported part of
`Dataset → Judgment Route → Pikachu Sentence replay` before visible completion.
Keep the E5 record evidence (`record_id`, Source/code/line
location, selected/rejected route, Why correction Q&A, reinput result, and
handoff target) and the E6 boundary/reopen evidence separate. Never promote
FINAL_PASS from this call sheet or from a technical `114/114` or `9/9` result.
