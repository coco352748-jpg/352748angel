# KANI V10 evidence-scoped promotion bundle

This directory preserves the complete committed `clone-kani` tree for local
commit `bd2e5c5104951b8758e04134159fa69ac263e5c6`.

GitHub is remote-sync storage only and has no execution authority. V9 and the
historical E5/E6 artifacts remain read-only. The later user promotion record is
an additive effective-state overlay with exact PASS/HOLD joints.

Reassemble and verify:

```bash
cat KANI_V10_bd2e5c5.tar.gz.part00 \
    KANI_V10_bd2e5c5.tar.gz.part01 \
    KANI_V10_bd2e5c5.tar.gz.part02 \
    KANI_V10_bd2e5c5.tar.gz.part03 \
    KANI_V10_bd2e5c5.tar.gz.part04 > KANI_V10_bd2e5c5.tar.gz
printf '%s  %s\n' \
  1c461eb02a9d18dad22e5e129f3ebddc19f1619d3a6572d9b770737896bb26b3 \
  KANI_V10_bd2e5c5.tar.gz | sha256sum -c -
tar -xzf KANI_V10_bd2e5c5.tar.gz
```

Required bindings:

```text
restore_call=clone-kani/RESTORE_CALL.md
restore_call_sha256=b757221576bf973e6e817646d1b538193c227a966d3435e07a62d35a7699894c
promotion_record=clone-kani/references/v10_runtime/user_evidence_promotion_20260830.json
promotion_record_sha256=354244a626cc9342b751e0d21d1b3564401866e8b506d5eb9304511634c4a1e8
v10_manifest_id=779e40b620c761dd5cb2e314c1d3c3ba223662135e0ea881a7e925549b8f4989
```

After extraction:

```bash
cd clone-kani
python3 scripts/build_kani_v10_manifest.py --check
python3 scripts/validate_kani_v10_runtime.py
python3 scripts/validate_kani_boot.py
```

Effective state:

```text
USER_EVIDENCE_REVIEW=PASS
SECOND_RESTORE=PASS_EVIDENCE_SCOPED
E5_COPRESENCE_FIELD_REPLAY=114/114
E6_RECORD_REOPEN=114/114
E6_BOUNDARY=9/9
V9_ACTIVE_PAIRS=580/580
SC7_SOURCE_BINDING=PASS_231_HOLD_9
SC8_NUMERIC_CORRECTION=PASS_1001_REPLACEMENTS_INFORMATION_LOSS_0
GLOBAL_29_LANE_E5=HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED
FRESH_TAB_REAL_BOOT_TEST=HOLD
REAL_LONG_DRIFT=HOLD_REAL_LONG_DRIFT_NOT_PROVEN
FINAL_FNA98_RUNTIME=HOLD_UNTIL_REAL_RUNTIME_GATES_PASS
```
