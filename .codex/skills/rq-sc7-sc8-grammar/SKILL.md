---
name: rq-sc7-sc8-grammar
description: Run the source-locked SC7 ↔ SC8 PIKACHU Rashi/Bhava bidirectional grammar audit and fail-closed executors. Use when the user invokes $rq-sc7-sc8-grammar or asks to resume, validate, or extend the 20D SC7/SC8 grammar extraction without OCR, astrology supplementation, chart-ID exceptions, or manual correction.
---

# RQ SC7 SC8 Grammar

Operate as a lossless bidirectional compiler designer. Do not describe a core-field comparison as full roundtrip completion.

## Source

- Repository: `coco352748-jpg/352748angel`
- Branch: `exports/sc7-sc8-rashi-bhava-20d`
- Source root: `exports/hyewon-sc7-sc8-rashi-bhava-20d/`
- Grammar root: `exports/hyewon-sc7-sc8-rashi-bhava-20d/grammar/`
- Active D order: `D1,D9,D2,D3,D4,D5,D6,D7,D8,D10,D11,D12,D16,D20,D24,D27,D30,D40,D45,D60`

Before acting, read these files from the grammar root:

1. `SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR.md`
2. `sc7_sc8_rashi_bhava_grammar.yaml`
3. `grammar_hold_registry.json`
4. `roundtrip_600_coverage.json`

## Protocol

1. Verify the ALL ZIP hashes recorded in the YAML before parsing.
2. Parse only supplied text. Never run OCR.
3. Keep Rashi and Bhava as independent typed lanes.
4. Decompose each pair as `D → lane → house → section → block → row → field → token`.
5. Apply only rules with an explicit `SC7_SOURCE_ANCHOR` and satisfied `MATCH_CONDITION`.
6. Preserve `EMPTY`, `NOT_SHOWN`, `HOLD`, `VOID`, `N.A.`, and `SUPPORT_ONLY` as distinct states.
7. Do not use D/chart identifiers to choose a historical formatting exception.
8. On mismatch, return to the grammar condition; never patch the generated chart.
9. Claim PASS only after exact file-byte forward, reverse, and both roundtrips pass for every contract unit.

## Commands

Run forward core extraction and paired validation:

```bash
exports/hyewon-sc7-sc8-rashi-bhava-20d/grammar/forward_sc7_to_sc8 \
  --sc7-root <SC7_ALL_ZIP_OR_ROOT> \
  --sc8-reference-root <SC8_ALL_ZIP_OR_ROOT> \
  --output <RESULT_JSON>
```

Run reverse recoverability validation:

```bash
exports/hyewon-sc7-sc8-rashi-bhava-20d/grammar/reverse_sc8_to_sc7 \
  --sc7-root <SC7_ALL_ZIP_OR_ROOT> \
  --sc8-reference-root <SC8_ALL_ZIP_OR_ROOT> \
  --output <RESULT_JSON>
```

Exit code 2 and `status: HOLD` are expected while blocking holds remain. `--allow-hold` may be used only for CI/report generation; it does not change the JSON status.

## Release gate

Do not emit target-looking TXT when `no_output_txt_emitted` is true. Release exact rendering only after:

- the contract contains all 600 source/target units;
- a non-ID Bhava long/short profile selector exists or one canonical profile is selected;
- every reverse-required SC7 token has a carrier or the inverse target is formally narrowed;
- the D1 target profile is version-locked;
- all SHA-256 byte comparisons pass with zero manual correction and zero chart-ID exception.

Record unresolved items only in `grammar_hold_registry.json`.
