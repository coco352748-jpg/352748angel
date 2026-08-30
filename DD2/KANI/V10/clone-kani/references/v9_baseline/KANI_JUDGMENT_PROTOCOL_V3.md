# KANI Judgment Protocol V3

## Authority and tested scope

This is the observable DD2 Analysis02 judgment protocol recovered from the
verified 20D × 29 active-lane PikaChu corpus, the direct Tab03 work-instruction
witness, and the sealed V3 replay. It is not private chain-of-thought and does
not claim identity or hidden-memory recovery.

```text
PROTOCOL_CORPUS=580_ACTIVE_PAIRS
PHYSICAL_CORPUS=600_MEMBERS
VOID_3P=20
DIRECT_TAB03_DECISION_EDGES=5
BLIND_REPLAY_CASES=D1,D27,D16,D24,D45
BLIND_REPLAY_ACTIVE_BODIES=145/145_HASH_VERIFIED
BLIND_REPLAY_CHECKS=2465/2465_PASS
EVIDENCE_LEVEL=E4_HELD_OUT_BLIND_REPLAY
```

The replay is a sealed-protocol-to-masked-body reconstruction check. It is not
the independent new-dataset production gate (E5).

## Decision pipeline

1. Bind the selected direct D-chart Source and preserve its hash.
2. Dispatch the grammar family before reading fields:
   - `D1_ROOT`: D1 uses its own Rashi, Bhava, and Shadbala source grammar.
   - `TARGET_DCHART`: D2–D60 use Target-D application grammar with D1 reference
     layers where the work instruction authorizes them.
3. Materialize exactly 29 active lanes. Preserve the physical 3P member as
   `VOID`; never count it as a thirtieth active judgment lane.
4. Keep Rashi original structure and Bhava reality placement separate. Bhava
   does not overwrite Rashi.
5. Parse `OCCUPANT_FIELD` and `HOUSE_LORD_FIELD` separately. A lord appended as
   `nL HouseLord` is not an occupant unless the direct occupant field also lists
   it.
6. Apply Source authority before similarity:
   - direct Bhava placement wins over a same-looking Rashi placement;
   - hidden or missing Bhava remains `NOT_SHOWN/HOLD`;
   - confirmed `EMPTY` means no occupant and routes to lord-only operation;
   - outer/support objects remain structural support unless the selected layer
     has a direct value.
7. Treat layer numbers as call order, not as permission to recalculate earlier
   layers. Run the current layer only and reference prior accepted artifacts by
   direct filename.
8. Treat `R` as source-applied, pre-work-instruction-QA material. Apply the
   executable instruction and QA to create `A`; do not treat `R` as final.
9. A work instruction must be executable: Source, role, target, output fields,
   rejection route, correction, QA, and direct handoff must be concrete.
10. Timing Gate intersects 016 Aspect activation with the 017 Dasha time window.
    It validates timing only and cannot write an event conclusion. Insufficient
    connection remains `HOLD`.
11. Close each lane with source/authority QA, structural QA, output/reopen QA,
    and the next direct handoff.
12. Repair only the failed route or field boundary. Preserve passed artifacts,
    hashes, and the Analysis02 mature floor; global restart is forbidden.

## Executable decision edges

| Trigger | Selected route | Rejected route | QA / handoff |
|---|---|---|---|
| D-chart selected | dispatch `D1_ROOT` or `TARGET_DCHART` | one grammar for every D | family-specific Source board |
| source board parsed | occupant and lord fields separated | append lord into occupants | direct object→house map |
| R stage ready | apply instruction and validate to A | treat R as final | 15-point QA / locked A filename |
| next layer | use prior A by direct filename; current role only | overwrite or recalculate prior layer | no-overwrite / direct preceding file |
| Source hidden, missing, or empty | `NOT_SHOWN`, `HOLD`, `NOT_APPLICABLE`, or lord-only | infer hidden value or treat empty as occupant | no sourceless value / local HOLD |
| work-instruction build | executable field-complete blueprint | vague prose or “after prior layers” | mandatory fields / next layer |
| Aspect03 A and Dasha A available | check activation×time-window intersection | write event conclusion | direct source match / 018 Timing Gate |

## Replay-discovered corrections

- V1 applied Target-D source and Shadbala probes to D1. All failures localized
  to D1, establishing the `D1_ROOT` / `TARGET_DCHART` dispatch boundary.
- V2 preserved the family dispatch but read the appended D1 house lord as an
  occupant. That localized failure established
  `OCCUPANT_FIELD != HOUSE_LORD_FIELD`.
- V3 sealed both corrections before reveal and passed all 2,465 assertions.

These are local protocol corrections. Neither failure reset the 580-pair
runtime or any previously passed gate.

## Current independent state axes

```text
REPLAY_BUNDLE=PASS
TAB_GENEALOGY=PASS
OUTPUT_CORPUS=PASS
INPUT_OUTPUT_BINDING=PASS
STRUCTURAL_LANE_RUNTIME=PASS
DIRECT_03_INSTRUCTION_BODY=PASS
CAUSAL_DECISION_RULES=PASS
BLIND_REPLAY=PASS
NEW_DATASET_PRODUCTION=HOLD_UNEXECUTED
LONG_DRIFT=HOLD_UNEXECUTED
FINAL_KANI_JUDGMENT_RUNTIME=HOLD_UNTIL_NEW_DATASET_LONG_DRIFT_AND_USER_PROMOTION
FIRST_UNEXECUTED_JOB=RUN_NEW_DATASET_PRODUCTION
LOWER_STAGE_RESTART=VOID
```

## Canonical artifacts

- Runner: `scripts/run_kani_v9_blind_replay.py`
- Sealed V3 execution: `references/v9_blind_replay/run_20260829_protocol_v3/`
- Result: `blind_replay_result.json`
- Full assertion ledger: `check_ledger.jsonl`
- Artifact hashes: `blind_replay_manifest.json`
