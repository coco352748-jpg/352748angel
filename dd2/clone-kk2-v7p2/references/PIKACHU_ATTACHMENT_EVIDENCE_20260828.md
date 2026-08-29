# PikaChu attachment evidence — 2026-08-28 read-only audit

## Scope and verdict

The uploaded originals were inspected read-only. No `3P` body was admitted. The inspected evidence directly supports the June 4 PikaChu checkpoint, completed `04 CoPresence` structure, and a reproducible 20D×12H production topology. It does not by itself prove a hidden worker identity or an exact historical recognition quote.

## June 4 PikaChu subset

| D | ZIP SHA-256 | Bytes | Entries | Member time (timezone absent) |
|---|---|---:|---:|---|
| D1 | `b48a4236f993c83f4154847170f5864cf54ab8b642a263c21adf6ce6faa98ed0` | 312922 | 30 | `2026-06-04 18:59:40` |
| D2 | `3ee6d9581fc694f811670014f883a6c0c8a3cb559c7c35a1bca9d212e299be92` | 320395 | 30 | `2026-06-04 18:59:40` |
| D3 | `eb27eb9453df717dbd29187ed9c9ab2d9e3bc43634203b256b263753620cb076` | 325544 | 30 | `2026-06-04 18:59:38` |
| D4 | `289130ad388328428eb86316958960d1c4476d6a8a40aa724a3a524aef5489f1` | 326545 | 30 | `2026-06-04 18:59:38` |
| D5 | `a26c0a512b5fa459b64f60c00d5ab8232ed2619e67dc27cfe7792c0f9b4c6688` | 324212 | 30 | `2026-06-04 18:59:38` |

- ZIP integrity: `5/5 PASS`.
- Existing June 4 register match: hashes, sizes, entry counts, and member timestamps `5/5 MATCH`.
- Active non-3P members in the attached subset: `5 × 29 = 145`.
- The remaining fourteen PikaChu ZIPs and the historical `570/551` totals were not re-audited from this upload.

## `04 CoPresence`

| D | Member SHA-256 | Bytes |
|---|---|---:|
| D1 | `e640bc0a6fe7e1ddd6646ac77a65bf31c695379b382c99aa145375ba6e21e0bf` | 69646 |
| D2 | `af8a2c68c7994a2d9d3cc72c8cbbb1e32f793077f3d2330f710acf6c111fb8b3` | 81278 |
| D3 | `ea8c56f16d683866d2894bef02719eb18a94cfd2c860f5b7cbf5928a8d30d15b` | 78530 |
| D4 | `41262adca625ac808e836b61f6bacb9fcd4b4096ee66cb04520c373dfe56ab5a` | 79029 |
| D5 | `16481ba2af0ab023cee8de835e9d5dba9a31ec3b4a38def375a5ba0fd68fb712` | 80322 |

Each member contains exactly twelve Rashi houses, twelve Bhava houses, and twelve Rashi↔Bhava comparison houses. All three completion axes pass, the values are filled, and the status is `98_READY`. All five preserve the literal handoff from First Integration to CoPresence before Strength, Aspect, and Dasha.

Therefore:

```text
04_COMPLETED_BY_JUNE04_ARCHIVE_CHECKPOINT=PASS
EXACT_AUTHORING_TURN_TIME=NOT_PROVED
```

## 20D×12H production evidence

`02A_DChart_AppLieD_.zip`:

```text
SHA256=c7433d6d549b68282c6cd4f798b495f46364d7e64911222d31368a1119d78507
ENTRIES=40
INTEGRITY=40_OF_40_PASS
RASHI_FILES=20
BHAVA_FILES=20
RASHI_HOUSE_BLOCKS=240
BHAVA_HOUSE_BLOCKS=240
```

Every member contains exactly H1–H12. The D1–D5 Rashi/Bhava payloads are `10/10 byte-exact` with the corresponding copies inside the June 4 PikaChu ZIPs. This establishes physical source-to-package continuity, not merely similar wording.

The separate Drishti ZIP contains twenty members with twelve Receiver Cards and twelve Structure Joints each, all triple-checked. Its internal date is June 6, so it is transfer/reproducibility evidence and must not be relabeled as June 4 evidence.

## Status-aware navigator evidence

The five PikaChu indexes each describe a flat ZIP with preserved source filenames and thirty physical entries. Item `04` is the physically retained `3P` member, so the active runtime inventory per attached ZIP is:

```text
30 physical = 1 active index + 28 active content + 1 operationally VOID 3P
```

This permits a safe navigator that preserves history without attempting to open or route through `3P`.

The other attached sources add three navigation safeguards:

- `HYEWON_VeDic_CO2_99.txt`: the user's requested chart, layer, and house controls scope; file adjacency does not authorize cross-D expansion or Rashi/Bhava mixing.
- `HYEWON_VeDic_D1-D60_-1.txt`: stable `[D# SET]`, `[D# RASHI SOURCE]`, and `[D# BHAVA SOURCE]` find tags support deterministic addressing while preserving unaffected layers.
- `HYEWON_ASHTA_SAP_TKS_EKS_SPD_-.txt`: one D10 Shodhya Pinda block is `NEEDS_RECHECK`, and ten later blocks carry a D1 `INDEX` under a different D title. Therefore a navigator must prefer verified title/header and explicit status over an inconsistent index. The file is not blanket-promoted.

Coverage denominators remain independent: a `20/20` chart family, a `12H` house family, and mixed EKS/SPD counts are not averaged into one invented completion value. AL is not silently rewritten as A1, UL is not silently rewritten as A12, and tie/rank order is not silently normalized.

## Evidence lanes

- `ARCHIVE_DIRECT`: hashes, sizes, member counts, timestamps, H1–H12 topology, completion states, byte equality.
- `USER_DIRECT`: analysis03 is the third-worker tab and preserves later DD-second work instructions and QA.
- `RECORD_VERIFIED`: only a directly opened surviving record may support an exact historical quotation.
- `HOLD`: exact authoring-turn time and exact first/second recognition wording.
- `FORBIDDEN`: infer DD authorship from an internal `D_ENGINE` token; import historical PikaChu values as current values; use any `3P` body operationally.
