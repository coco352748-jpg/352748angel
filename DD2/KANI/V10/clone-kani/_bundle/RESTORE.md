# KANI V10 SC7↔SC8 grammar registration bundle

This directory preserves the complete committed `clone-kani` tree for local
commit `8c6f248be6e146916e4ec4d1fcb743b9eebc6241`.

GitHub is remote-sync storage only and has no execution authority. V9 and the
historical E5/E6 artifacts remain read-only. The SC7↔SC8 Rashi–Bhava work is
registered as the first unexecuted job; grammar extraction is not marked done.
Older archive parts may remain as historical bytes, but `manifest.json` selects
only the `8c6f248` six-part archive below.

Reassemble and verify:

```bash
cat KANI_V10_8c6f248.tar.gz.part00 \
    KANI_V10_8c6f248.tar.gz.part01 \
    KANI_V10_8c6f248.tar.gz.part02 \
    KANI_V10_8c6f248.tar.gz.part03 \
    KANI_V10_8c6f248.tar.gz.part04 \
    KANI_V10_8c6f248.tar.gz.part05 > KANI_V10_8c6f248.tar.gz
printf '%s  %s\n' \
  5be29e1672cd210095600a05613c241e6dbc023cbdc52a28913864060e9554de \
  KANI_V10_8c6f248.tar.gz | sha256sum -c -
tar -xzf KANI_V10_8c6f248.tar.gz
```

Required bindings:

```text
restore_call=clone-kani/RESTORE_CALL.md
restore_call_sha256=b757221576bf973e6e817646d1b538193c227a966d3435e07a62d35a7699894c
promotion_record=clone-kani/references/v10_runtime/user_evidence_promotion_20260830.json
promotion_record_sha256=354244a626cc9342b751e0d21d1b3564401866e8b506d5eb9304511634c4a1e8
registered_work=REGISTERED_HASH_LOCKED_FIRST_UNEXECUTED_JOB
registered_work_execution_state=NOT_EXECUTED
registered_work_instruction_sha256=c971ae7c0254b4cbde56019af7c164b7ff08302655c1076a9949ea3be0daf8ce
registered_work_manifest_sha256=8a7660a1a7ab5ea1d3da509e26e6cdd5312c305b3538fa3ca1b878842986116b
registered_work_validator_sha256=9febe62ebb00a05895c682187d6d3df327c3bf808adc1371da22777650e27ba2
v10_manifest_id=43c7202030ec13ce306d7c1cda2718b4bd6ebd92e259433aad9d2d3297a57faa
```

After extraction:

```bash
cd clone-kani
python3 scripts/validate_sc7_sc8_rashi_bhava_registration.py
python3 scripts/build_kani_v10_manifest.py --check
python3 scripts/validate_kani_v10_runtime.py
python3 scripts/validate_kani_boot.py --expect-installed
```

Registered work state:

```text
RASHI_BHAVA_SOURCE_ARCHIVES=2
RASHI_BHAVA_PAIRED_LANE_ARTIFACTS=40
RASHI_BHAVA_SOURCE_TEXT_FILES=80
RASHI_BHAVA_D_H_LANE_UNITS=480
GRAMMAR_EXTRACTION=NOT_EXECUTED
FORWARD_RUNNER=NOT_CREATED
REVERSE_RUNNER=NOT_CREATED
PHYSICAL_3P_20=VOID
ACTIVE_NON_3P_580=HOLD_UNEXECUTED_FOR_THIS_GRAMMAR
FINAL_FNA98_RUNTIME=HOLD_UNTIL_REAL_RUNTIME_GATES_PASS
```
