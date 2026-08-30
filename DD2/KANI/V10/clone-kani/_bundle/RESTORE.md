# KANI V10 remote-sync bundle

This directory preserves the complete committed `clone-kani` tree for local
commit `cc85d1961f07217062930288bbc381de7a07973f`.

GitHub is remote-sync storage only and has no execution authority. V9 is
preserved read-only; V10 is the additive E5/E6 execution-evidence overlay.

Reassemble, verify, and inspect the restore call:

```bash
cat KANI_V10_cc85d19.tar.gz.part00 \
    KANI_V10_cc85d19.tar.gz.part01 \
    KANI_V10_cc85d19.tar.gz.part02 \
    KANI_V10_cc85d19.tar.gz.part03 \
    KANI_V10_cc85d19.tar.gz.part04 > KANI_V10_cc85d19.tar.gz
printf '%s  %s\n' \
  808ac483869ec45b7485495d899f887adf945525cf1dde24ab0bb08d6fd639be \
  KANI_V10_cc85d19.tar.gz | sha256sum -c -
tar -tzf KANI_V10_cc85d19.tar.gz | grep -x 'clone-kani/RESTORE_CALL.md'
tar -xzf KANI_V10_cc85d19.tar.gz
```

The archive expands under `clone-kani/`. The required restore-call binding is:

```text
path=clone-kani/RESTORE_CALL.md
sha256=903a9e2509752ec2e3dc186f37e3a4f3b8d6dd998d89d5796c27d4b8a8979d08
```

After extraction, run:

```bash
cd clone-kani
python3 scripts/build_kani_v10_manifest.py --check
python3 scripts/validate_kani_v10_runtime.py
python3 scripts/validate_kani_boot.py
```

Evidence state at sync:

```text
E5_COPRESENCE_REPLAY=114/114
E6_BOUNDARY_REOPEN=9/9
SC7_CALIBRATION=240/240
SECOND_RESTORE=EVIDENCE_REVIEW
V10=EXPECTED_VALUE_BOUND
FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE
PUBLIC_FINAL_PASS=USER_EVIDENCE_REVIEW_PENDING
GLOBAL_29_LANE_E5=HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED
REAL_LONG_DRIFT=HOLD_REAL_LONG_DRIFT_NOT_PROVEN
```
