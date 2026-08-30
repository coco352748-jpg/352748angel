# KANI V10 remote-sync bundle

This directory preserves the complete committed `clone-kani` tree for local
commit `cbd6ea19149378d66e022127027158d0f070706e`.

GitHub is remote-sync storage only and has no execution authority. V9 is
preserved; V10 is the additive E5/E6 execution-evidence overlay.

Reassemble and verify:

```bash
cat KANI_V10_cbd6ea1.tar.gz.part* > KANI_V10_cbd6ea1.tar.gz
printf '%s  %s\n' \
  d9a7c9692e92baeb375946b155a20f785e0f1f1abbf32be62a3c107bb15b7fbe \
  KANI_V10_cbd6ea1.tar.gz | sha256sum -c -
tar -xzf KANI_V10_cbd6ea1.tar.gz
```

The archive expands under `clone-kani/`. After extraction, run:

```bash
cd clone-kani
python3 scripts/build_kani_v10_manifest.py --check
python3 scripts/validate_kani_v10_runtime.py
python3 scripts/validate_kani_boot.py --expect-installed
```

Evidence state at sync:

```text
E5_COPRESENCE_REPLAY=114/114
E6_BOUNDARY_REOPEN=9/9
SC7_CALIBRATION=240/240
SECOND_RESTORE=EVIDENCE_REVIEW
V10=EXPECTED_VALUE_BOUND
FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE
GLOBAL_29_LANE_E5=HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED
REAL_LONG_DRIFT=HOLD_REAL_LONG_DRIFT_NOT_PROVEN
```
