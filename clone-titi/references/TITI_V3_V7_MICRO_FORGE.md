# TITI V3–V7 Micro Forge Contract V1

## 0. Authority and route

```text
CONTRACT=TITI_V3_V7_MICRO_FORGE_V1
CALL_KEY=$clone-titi
PUBLIC_CALL_KEY_ADDED=false
IDENTITY=TITI
INTERNAL_MODE=V3_V7_MICRO_FORGE
OPERATIONS=DESIGN_STAGE | EXACT_STAGE_REVERSE
EXACT_INPUT_STATE=REQUIRES_EXECUTED_AUDIT
R5_REGISTRY_CONTRACT=RQ_R5_V3_V7_SENTENCE_JOINT_REGISTRY_V1
R5_OUTPUT_STYLE=NON_COMPRESSED_ACADEMIC_EXPLANATORY
VALUE_POLICY=SOURCE_BOUND_NO_INVENTION
DELIVERY_GRADE=FNa98
```

This is an internal `$clone-titi` capability. It does not create another public call key, clone identity, or fallback route. Activate it only when the current user instruction explicitly requests an R5/V3–V7 sentence stage, its micro fine-slot design, or its exact reverse rendering. Target and routing remain exactly bound to the user's current instruction.

For lock-sentence work with no explicit Version, V3 is the default. For a V3 design or new V3 sentence with no user-selected sentence standard, read `TITI_V3_DEFAULT_LOCK_CALIBRATION.md` and apply the ordered `D5-H08 → D4-H10 → D6-H05` prose/micro-structure calibration. Its values are always void. `D6-H05` uses `D5-H05` as a sentence/micro archetype only and binds actual values from current D6 Source. The calibration never applies to V4–V7 or `EXACT_STAGE_REVERSE`.

Before either operation, read the current R5 canon, registry, and exact-roundtrip contract completely. R5 controls stage meaning, joint identity, registry order, paragraph function, evidence boundary, and sentence authority. TITI controls only the micro-template design, occurrence addressing, structural audit, and exact sentence↔slot inversion. TITI must not reinterpret, summarize, merge, or silently extend an R5 formula.

## 1. Frozen stage mapping

The version-to-stage mapping is exact and immutable:

| Version | Stage | R5 stage name |
|---|---:|---|
| `V3` | `3` | `3단계 심층작동결` |
| `V4` | `3.5` | `3.5단계 심층촘촘결` |
| `V5` | `4` | `4단계 구조통찰결` |
| `V6` | `4.5` | `4.5단계 심층통찰결` |
| `V7` | `5` | `5단계 법전결` |

Changing a label, borrowing a function from another version, or treating later versions as longer rewrites of earlier versions is forbidden.

## 2. Exact R5 registry

The requested version must open every joint below exactly once and in exactly this order. The full registry contains `39` joints.

### V3 — 6 joints

1. `V3.CENTER_OPERATION` — 중심 작동판정
2. `V3.FIELD_INPUT` — 작동장과 입력
3. `V3.OPERATOR_OBJECT` — 작동주어와 처리대상
4. `V3.STATE_TRANSFORMATION` — 상태변환
5. `V3.TRANSFER_CHECKPOINT` — 전달경로와 검문관절
6. `V3.RESULT_BOUNDARY` — 결과경계

### V4 — 7 joints

1. `V4.SOURCE_ALLOWED_ANSWER` — 표면질문 교정과 Source 허용 선행답변
2. `V4.EVIDENCE_PRECONDITION` — 직접근거와 성립전제
3. `V4.DEPENDENCY_AUTHORITY` — 의존관계와 권한방향
4. `V4.ROLE_LAYER_STATE_SEPARATION` — 배역·층위·상태 분리
5. `V4.MECHANISM_RECONNECTION` — 작동기제 재결속
6. `V4.MINIMUM_COUNTEREXAMPLE` — 최소반례
7. `V4.CONCLUSION_BOUNDARY` — 결론과 경계 봉합

### V5 — 7 joints

1. `V5.STRUCTURE_VERDICT` — 구조판정
2. `V5.INPUT_SELECTION` — 입력과 선별
3. `V5.OPERATION_TRANSFER` — 작동과 전달
4. `V5.COMMON_ROOT` — 공통뿌리
5. `V5.CAPABILITY_DISTORTION_BRANCH` — 능력과 왜곡의 분기조건
6. `V5.MINIMUM_TRANSITION` — 최소 전환관절
7. `V5.FINAL_STRUCTURE_LOCK` — 최종 잠금

### V6 — 11 joints

1. `V6.OUTER_STRUCTURE` — 바깥 구조판정 고정
2. `V6.INNER_GENERATIVE_MECHANISM` — 첫째 내측 생성기제
3. `V6.DEEPEST_CORE_JOINT` — 둘째 최심층 핵심관절
4. `V6.UPWARD_GENERATION_ORDER` — 최심층에서 바깥으로 올라오는 생성순서
5. `V6.REALITY_TRIGGER` — 현실 촉발조건
6. `V6.OBSERVABLE_SIGNAL` — 관찰 가능한 징후
7. `V6.ACTUAL_CHOICE_ACTION` — 실제 선택과 행동
8. `V6.REALITY_BRANCH` — 능력과 왜곡의 현실분기
9. `V6.CONTROL_POINTS_ORDER` — 두 통제점과 검문순서
10. `V6.REALITY_AUDIT_COUNTEREXAMPLE` — 현실 검산과 최소반례
11. `V6.DEEPEST_BOUNDARY` — 최심층 확정경계

### V7 — 8 joints

1. `V7.JURISDICTION` — 법의 관할
2. `V7.REPEATED_EVIDENCE_INVARIANT` — 반복근거와 불변식
3. `V7.SUPERORDINATE_RULE` — 상위법칙 선언
4. `V7.APPLICATION_GATE` — 적용게이트
5. `V7.JUDGMENT_PRIORITY` — 판정우선순위
6. `V7.OPERATING_ORDER` — 운영순서
7. `V7.EXCEPTION_COUNTEREXAMPLE_PROHIBITION` — 예외·반례·금지선
8. `V7.TERMINATION_CODE_LOCK` — 종료선과 법전 잠금

Joint omission, duplication, reordering, or substitution fails the stage. A requested subset may be inspected, but it cannot be labeled a completed R5 stage.

## 3. Work unit and record envelope

```text
ONE_RECORD = ONE_VIEW × ONE_ROLE × ONE_VERSION × ONE_SEMANTIC_JOINT
ONE_JOINT = ONE_ACADEMIC_PARAGRAPH_RECORD
SLOT_UID = VIEW.ROLE.VERSION.JOINT_UID.SENTENCE_UID.SLOT_NAME.OCCURRENCE
```

Each occurrence has its own stable UID. Repeated surface text or repeated semantic values never share an occurrence address by assumption. A slot carries exactly one semantic role. A whole joint paragraph, sentence, or stage must not be hidden inside a catch-all placeholder.

Every paragraph record has the envelope fields `JOINT_UID / VIEW / ROLE / VERSION / STAGE`, followed by all nineteen R5 cells below, plus `SLOT_ORDER / LITERAL_ORDER / PARAGRAPH_FUNCTION_ORDER / SOURCE_BACKMAP`.

## 4. All 19 R5 cells

Every joint record contains all nineteen cells exactly once as named fields:

1. `INPUT_REF`
2. `PREVIOUS_OUTPUT`
3. `GRAMMATICAL_SUBJECT`
4. `SUBJECT_ROLE`
5. `PREDICATE`
6. `DIRECT_OBJECT`
7. `ADVERBIAL_METHOD`
8. `CONDITION_GATE`
9. `PRE_STATE`
10. `TRANSFORMATION`
11. `POST_STATE`
12. `WHY_LINK`
13. `HANDOFF_VALUE`
14. `NEXT_SUBJECT_OR_FIELD`
15. `RESULT_STAGE`
16. `RESULT_BOUNDARY`
17. `EVIDENCE_GRADE`
18. `STATUS`
19. `SURFACE_SCAFFOLD`

The cells may contain typed micro-slots, source-bound literals, or an explicit `HOLD`, but they may not be omitted or replaced with a generic paragraph field. `GRAMMATICAL_SUBJECT`, `PREDICATE`, and `DIRECT_OBJECT` remain distinct. `PRE_STATE`, `TRANSFORMATION`, and `POST_STATE` remain directionally distinct. `RESULT_STAGE` separates occurrence, transfer, arrival, attribution, ownership, retention, recovery, and timing rather than collapsing them.

## 5. Four paragraph functions

Every one-joint paragraph record preserves these four functions in this exact order:

1. `QUESTION_AND_PREVIOUS_OUTPUT`
2. `SUBJECT_VERB_OBJECT_OPERATION`
3. `STATE_TRANSFORMATION_AND_WHY`
4. `HANDOFF_AND_RESULT_BOUNDARY`

The functions may occupy multiple sentences or clause records, but none may be compressed into a keyword line or absorbed into another joint. The paragraph first fixes its question and received value, then exposes the actual subject–verb–object operation, then explains the source-backed state change and WHY, and finally hands off the processed value while closing the confirmed and unconfirmed result boundary.

## 6. Stage handoff identity

Within one version, the registry is an identity-locked open chain.

For every adjacent pair `A → B`:

```text
A.NEXT_SUBJECT_OR_FIELD addresses B
A.HANDOFF_VALUE.VALUE_ID == B.PREVIOUS_OUTPUT.VALUE_ID
```

For `DESIGN_STAGE`, prove the unbound lineage with a separate test token. For `EXACT_STAGE_REVERSE`, require the actual semantic and surface values too:

```text
DESIGN_STAGE:
A.HANDOFF_VALUE.HANDOFF_TEST_TOKEN == B.PREVIOUS_OUTPUT.HANDOFF_TEST_TOKEN

EXACT_STAGE_REVERSE:
A.HANDOFF_VALUE.SEMANTIC_VALUE == B.PREVIOUS_OUTPUT.SEMANTIC_VALUE
A.HANDOFF_VALUE.SURFACE_VALUE == B.PREVIOUS_OUTPUT.SURFACE_VALUE
```

If a value changes between joints, the change must be completed inside the preceding joint's `TRANSFORMATION`, producing the exact value that the next joint receives. A connective such as “따라서” or an unrecorded paraphrase cannot perform a handoff transformation.

The first joint receives only its registry-defined initial input (`SOURCE_INPUT`, `V5_CONFIRMED_STRUCTURE_OR_SOURCE_INPUT`, or `SOURCE_GROUP_INPUT` as applicable). The last joint hands off to `STAGE_OUTPUT`. The chain must visit every registered joint exactly once, contain no loop or orphan, and never cross into another version.

```text
HANDOFF_IDENTITY_PASS = AND(
  FIRST_JOINT.PREVIOUS_ADDRESS == REGISTRY_INITIAL_INPUT[VERSION],
  FOR_EVERY_ADJACENT_A_B:
    A.NEXT_ADDRESS == B.JOINT_UID
    AND A.HANDOFF_VALUE.VALUE_ID == B.PREVIOUS_OUTPUT.VALUE_ID
    AND (
      OPERATION == DESIGN_STAGE
        ? A.HANDOFF_VALUE.HANDOFF_TEST_TOKEN == B.PREVIOUS_OUTPUT.HANDOFF_TEST_TOKEN
        : A.HANDOFF_VALUE.SEMANTIC_VALUE == B.PREVIOUS_OUTPUT.SEMANTIC_VALUE
          AND A.HANDOFF_VALUE.SURFACE_VALUE == B.PREVIOUS_OUTPUT.SURFACE_VALUE
    ),
  LAST_JOINT.NEXT_ADDRESS == STAGE_OUTPUT,
  VISITED_JOINT_UID_ARRAY == REGISTRY_JOINT_UID_ARRAY[VERSION]
)
```

## 7. Operation A — DESIGN_STAGE

`DESIGN_STAGE` creates a fillable micro fine-slot system for one requested R5 version without requiring a finished approved sentence.

1. Freeze `ACTUAL_QUESTION / TARGET / VIEW / ROLE / VERSION / STAGE / SOURCE_BOUNDARY / OUTPUT / FORMAT / COMPLETION`.
2. Load the exact registry for that version and create one paragraph record per joint in registry order.
3. Allocate all nineteen cells and all four paragraph functions for every joint.
4. Create typed occurrence slots and literal scaffolds. Fixed particles, endings, spaces, punctuation, connective language, and order stay in the literal scaffold; variable semantic atoms stay in slots.
5. Give each slot one `semantic_role`, `input_ref`, approved operator, transformation boundary, handoff, result boundary, and `UNBOUND` or `HOLD` value state.
6. Keep all real values unbound. Missing data stays `HOLD_SLOT`; contextual plausibility is never a Source.
7. Build the stage handoff chain and order ledgers without borrowing a conclusion from another version.
8. Run the structural sentinel audit described below.

Design completion means the requested version has a structurally executable, source-bounded schema. It does not mean a source sentence exists or that exact equality has passed.

```text
PRE_FNA98_AUDIT_STATE=STRUCTURAL_DESIGN_BUILT
ALLOWED_SUCCESS_STATUS_AFTER_AUDIT=FNA98_DESIGN_READY
EXACT_SOURCE_ROUNDTRIP=NOT_APPLICABLE_UNTIL_FILLED
```

## 8. DESIGN_STAGE structural sentinel audit

Sentinels are internal mechanism probes, never Source values and never user output.

For every joint paragraph and for the complete stage packet:

1. assign a unique `OCCURRENCE_SENTINEL` to every slot UID and a separate `HANDOFF_TEST_TOKEN` to each stage-value lineage;
2. render through the literal scaffold in locked slot, sentence, paragraph, joint, and stage order;
3. parse the rendered probe through literal anchors;
4. recover the same occurrence sentinels, UIDs, and occurrence order;
5. confirm all nineteen cells and four functions remain addressable;
6. confirm `A.HANDOFF_VALUE.HANDOFF_TEST_TOKEN == B.PREVIOUS_OUTPUT.HANDOFF_TEST_TOKEN` for every adjacent joint while keeping the two occurrence sentinels unique;
7. confirm every non-empty literal segment has user-format, R5-canon, or explicitly approved grammar authority;
8. confirm no catch-all, adjacent placeholder, ambiguous capture, loop, orphan, or cross-version address exists.

A sentinel PASS proves structural fillability and inverse address order only. It must never be reported as exact source-sentence roundtrip PASS.

```text
STRUCTURAL_SENTINEL_ROUNDTRIP_PASS = AND(
  ROUNDTRIP_AUDIT.checks.OCCURRENCE_SENTINEL_UID_UNIQUE,
  ROUNDTRIP_AUDIT.checks.SENTINEL_RENDER,
  ROUNDTRIP_AUDIT.checks.SENTINEL_PARSE,
  ROUNDTRIP_AUDIT.checks.SENTINEL_RERENDER,
  ROUNDTRIP_AUDIT.checks.SENTINEL_VALUES_UIDS_ORDER_IDENTICAL,
  ROUNDTRIP_AUDIT.checks.HANDOFF_TEST_TOKEN_IDENTITY,
  ROUNDTRIP_AUDIT.checks.ALL_19_CELLS_ADDRESSABLE,
  ROUNDTRIP_AUDIT.checks.ALL_4_FUNCTIONS_ADDRESSABLE,
  ROUNDTRIP_AUDIT.checks.LITERAL_AUTHORITY,
  ROUNDTRIP_AUDIT.checks.NON_DEGENERATE
)
```

## 9. Operation B — EXACT_STAGE_REVERSE

`EXACT_STAGE_REVERSE` decompiles an approved R5 stage text into exact paragraph, sentence, clause, literal, and typed occurrence records, and then proves both directions without changing a byte.

```text
PRE_FNA98_AUDIT_STATE=REQUIRES_EXECUTED_AUDIT
ALLOWED_SUCCESS_STATUS_AFTER_AUDIT=FNA98_SENTENCE_PASS
```

1. Freeze the exact approved UTF-8 text and normalize only CRLF or CR to LF for comparison.
2. Require an explicit paragraph-to-`JOINT_UID` map covering every joint of the requested version exactly once and in registry order.
3. Require one joint to equal one paragraph record. Do not merge two joints into a paragraph or split one joint across unrelated paragraph records.
4. Bind the seventeen semantic value cells and four paragraph functions to exact text spans when surfaced and to Source coordinates; validate `SURFACE_SCAFFOLD` against the exact template/literal-authority ledger and bind `STATUS` only to the executed audit result.
5. Separate `SEMANTIC_VALUE` from `SURFACE_VALUE` for every slot, even when they look identical.
6. Preserve particles, endings, spacing, punctuation, quotation marks, symbols, sentence order, paragraph order, and line breaks in the literal scaffold and ledgers.
7. Issue a separate occurrence UID for every repeated appearance.
8. Verify the stage handoff identity and Source backmap before claiming semantic completion.
9. Execute both exact roundtrip directions.

Required invariants:

```text
RENDER(SLOT_PACKET + LITERAL_SCAFFOLD + ORDER_LEDGERS) == APPROVED_STAGE_TEXT
PARSE(APPROVED_STAGE_TEXT) == ORIGINAL_SLOT_PACKET
RERENDER(PARSED_PACKET) == APPROVED_STAGE_TEXT
KEY_SET == ORIGINAL_KEY_SET
SLOT_SET_AND_ORDER == ORIGINAL_SLOT_SET_AND_ORDER
INVERSE_VALUES == ORIGINAL_SEMANTIC_AND_SURFACE_VALUES
HANDOFF_IDENTITY == TRUE
ONE_SLOT_ONE_ROLE == TRUE
NON_DEGENERATE == TRUE
SOURCE_ROLE_VIEW_VERSION == PRESERVED
```

Roundtrip equality does not certify that the sentence has valid R5 meaning. R5 stage, Source, joint, and evidence gates must pass first; then TITI may certify exact inversion.

```text
EXACT_RENDER_PASS = ROUNDTRIP_AUDIT.checks.EXACT_RENDER == true
EXACT_PARSE_PASS = ROUNDTRIP_AUDIT.checks.EXACT_PARSE_AND_INVERSE_VALUES_ORDER == true
EXACT_RERENDER_PASS = ROUNDTRIP_AUDIT.checks.EXACT_RERENDER == true

APPROVED_TEXT_EXACT_ROUNDTRIP_PASS = AND(
  EXACT_RENDER_PASS,
  EXACT_PARSE_PASS,
  EXACT_RERENDER_PASS,
  ROUNDTRIP_AUDIT.checks.KEY_SET,
  ROUNDTRIP_AUDIT.checks.SLOT_SET_AND_ORDER,
  ROUNDTRIP_AUDIT.checks.HANDOFF_IDENTITY,
  ROUNDTRIP_AUDIT.checks.ONE_SLOT_ONE_ROLE,
  ROUNDTRIP_AUDIT.checks.NON_DEGENERATE,
  ROUNDTRIP_AUDIT.checks.SOURCE_ROLE_VIEW_VERSION
)
```

## 10. Source binding and no invention

Every semantic value, transformation, WHY, handoff, result stage, and result boundary must backmap to a direct Source or an explicitly approved derived rule inside the frozen Target.

- `DIRECT_SOURCE` is used only for a value directly present in the allowed Source.
- `DERIVED` requires the exact approved derivation rule and its inputs.
- `INFERENCE` never silently becomes Source and cannot fill a direct-evidence requirement.
- Missing, VOID, NOT_PARSED, conflicting, or unauthorized data remains `HOLD` at the exact cell and all dependent downstream cells.

Do not invent an actor, intent, event, coordinate, comparison, counterexample, opposite branch, transition, timing, ownership, retention, or outcome. Do not turn a field, sign, house, location, or EMPTY state into an acting subject unless Source grants that role. Do not polish a frozen sentence to improve its grammar or templating.

## 11. V7 elevation lock

V7 cannot open from one case, one lower structure restated twice, or two outputs that only look similar.

Before any V7 paragraph becomes `PASS`, require:

```text
INDEPENDENT_LOWER_STRUCTURE_COUNT >= 2
SOURCE_BACKMAP_COUNT >= 2
EACH_LOWER_STRUCTURE = INPUT + OPERATION + TRANSFORMATION + HANDOFF + RESULT
EACH_INVARIANT_COMPONENT -> ITS_OWN_LOWER_STRUCTURE_SOURCE_BACKMAP
```

The lower structures must have independently addressable structure IDs, operating paths, and Source coordinates. The repeated value must be the same source-backed operation joint, sequence, and transformation—not merely the same label or result. If fewer than two independent lower structures exist, if either Source backmap breaks, or if the invariant is wider than its evidence, set the whole V7 stage to `HOLD`; do not partially populate later joints to make a law-like output.

## 12. Multiple-version isolation

When the user requests more than one version, create a separate stage packet, template namespace, paragraph array, slot ledger, Source backmap, handoff chain, and audit for each version.

```text
V3 != V4 != V5 != V6 != V7
NO_CROSS_VERSION_UID
NO_CROSS_VERSION_HANDOFF
NO_CROSS_VERSION_CONCLUSION_INHERITANCE
NO_AVERAGED_V3_V7_TEMPLATE
```

Versions may cite the same authorized Source coordinate, but they do not share conclusions, missing cells, values, or completion status. A PASS in one version cannot repair a HOLD in another. A revision creates a new versioned artifact; it never mutates a frozen exact artifact in place.

## 13. Executable FNa98 three-axis gate

FNa98 is an executed result, not a prose label. The evaluator must consume the stage packet, frozen R5 registry, Source or Source-requirement backmaps, handoff ledger, mode-native audit, and visibility manifest. A writer or caller cannot set an FNa98 status manually.

For this gate, the nineteen R5 cells are divided into seventeen semantic value cells, one structural surface cell, and one audit-control cell:

```text
FNA98_VALUE_CELL_SET = ALL_19_R5_CELLS - {SURFACE_SCAFFOLD, STATUS}
FNA98_VALUE_CELL_COUNT = 17
FNA98_STRUCTURAL_CELL = SURFACE_SCAFFOLD
FNA98_CONTENT_CELL_SET = FNA98_VALUE_CELL_SET + {SURFACE_SCAFFOLD}
FNA98_CONTENT_CELL_COUNT = 18
FNA98_CONTROL_CELL = STATUS
```

The evaluator accepts one frozen audit input bundle with the same `ARTIFACT_ID / ARTIFACT_VERSION / VERSION / OPERATION` on every component:

```text
STAGE_PACKET
R5_REGISTRY_SNAPSHOT
SOURCE_BINDING_OR_REQUIREMENT_LEDGER
PARAGRAPH_FUNCTION_LEDGER
SEMANTIC_CLAIM_LEDGER
RESOLUTION_SEPARATION_LEDGER
HANDOFF_LEDGER
MODE_NATIVE_AUDIT
ROUNDTRIP_AUDIT
OUTPUT_VISIBILITY_MANIFEST
```

A component with a different artifact identity, a missing referenced UID, or a bare declared status without its check map is invalid. Each axis emits `per_joint[joint_uid].checks`, `stage_checks`, `failures`, and a computed boolean. The audit runs on every one-joint paragraph record and then on the complete version packet. Stage success is the logical AND of every expected record check and every stage check; averaging, sampling, or compensating one weak joint with another strong joint is forbidden.

### 13.1 Density execution gate

For every registered joint, execute and record:

```text
D01_PARAGRAPH_COUNT_FOR_JOINT == 1
D02_CONTENT_CELL_NAME_SET == FNA98_CONTENT_CELL_SET
D03_CONTENT_CELL_COUNT == 18
D04_FUNCTION_NAME_ORDER == [
  QUESTION_AND_PREVIOUS_OUTPUT,
  SUBJECT_VERB_OBJECT_OPERATION,
  STATE_TRANSFORMATION_AND_WHY,
  HANDOFF_AND_RESULT_BOUNDARY
]
D05_FUNCTION_CELL_MAP == REQUIRED_FUNCTION_CELL_MAP
D06_UNMAPPED_SENTENCE_OR_CLAUSE_COUNT == 0
D07_UNAUTHORIZED_DUPLICATE_CLAIM_COUNT == 0
D08_WHY_LINK_SOURCE_GATE == true
D09_HANDOFF_IDENTITY_GATE == true
D10_RESULT_BOUNDARY_SEPARATION_GATE == true
```

The exact content-cell name set is the seventeen names listed in section 4 except `SURFACE_SCAFFOLD` and `STATUS`, plus `SURFACE_SCAFFOLD`; set equality and count are tested separately. The seventeen value cells must be partitioned exactly once by this map:

```text
REQUIRED_FUNCTION_CELL_MAP = {
  QUESTION_AND_PREVIOUS_OUTPUT: [
    INPUT_REF, PREVIOUS_OUTPUT, CONDITION_GATE
  ],
  SUBJECT_VERB_OBJECT_OPERATION: [
    GRAMMATICAL_SUBJECT, SUBJECT_ROLE, PREDICATE,
    DIRECT_OBJECT, ADVERBIAL_METHOD
  ],
  STATE_TRANSFORMATION_AND_WHY: [
    PRE_STATE, TRANSFORMATION, POST_STATE, WHY_LINK, EVIDENCE_GRADE
  ],
  HANDOFF_AND_RESULT_BOUNDARY: [
    HANDOFF_VALUE, NEXT_SUBJECT_OR_FIELD, RESULT_STAGE,
    RESULT_BOUNDARY
  ]
}
```

No value cell may be absent from the map or assigned to two primary functions. `SURFACE_SCAFFOLD` is a structural overlay whose literal-span ledger may cover all four functions; `STATUS` is excluded from the function map. Listing names without typed slots, exact spans, or Source requirements is not coverage. Every sentence or clause span must map to at least one of the four function IDs, and all four functions must have non-empty coverage.

The semantic claim ledger deterministically forms:

```text
CLAIM_KEY = (
  SUBJECT_ROLE.VALUE_ID,
  PREDICATE.VALUE_ID,
  DIRECT_OBJECT.VALUE_ID,
  CONDITION_GATE.VALUE_ID,
  PRE_STATE.VALUE_ID,
  POST_STATE.VALUE_ID,
  RESULT_STAGE.VALUE_ID,
  RESULT_BOUNDARY.VALUE_ID
)
```

The executable signature uses each listed cell's `input_ref` in `DESIGN_STAGE` and its exact `value` in `EXACT_STAGE_REVERSE`. When all eight members are non-empty, a second identical signature anywhere in the requested bundle is unauthorized duplicate-claim padding. Surface repetition is still preserved with separate occurrence probes, but it does not exempt a duplicated eight-field claim signature. WHY, handoff, and boundary remain independently required by their binding and completeness gates.

These checks normalize into the machine gates `JOINT_COUNT / REQUIRED_CELL_SET / PARAGRAPH_FUNCTIONS / FUNCTION_CELL_PARTITION / NO_DUPLICATE_CLAIM_PADDING` used by `FNA98_DENSITY` in section 13.4.

### 13.2 Resolution execution gate

Resolution requires both the exact version registry depth and the version-specific separation below:

| Version | Executed resolution proof |
|---|---|
| `V3` | Six-joint route separately proves center, field/input qualification, actual operator/object, directional pre→transformation→post state, transfer/checkpoint, and last confirmed result boundary. |
| `V4` | Seven-joint route separately proves Source-allowed answer, direct evidence/precondition, dependency authority, role/layer/state separation, mechanism reconnection, minimum counterexample, and conditional conclusion boundary. |
| `V5` | Seven-joint route separately proves structure, selection, operation/transfer, Source-backmapped common root, capability/distortion branch conditions, minimum transition joint, and overinterpretation boundary. |
| `V6` | Eleven-joint route proves two non-synonymous inner layers, their upward generation order, reality trigger, observable signal, actual choice/action, reality branch, two ordered control points, re-entry audit/counterexample, and deepest boundary. |
| `V7` | Eight-joint route proves jurisdiction, at least two independent lower structures, per-structure Source backmaps, repeated operational invariant, superordinate rule, application gate, priority, operating order, exception/counterexample/prohibition, and termination lock. |

Each resolution-ledger entry has `requirement_id / joint_uid_set / semantic_role_entries / state_entries / result_stage_entries / source_backmap_refs / evidence_paths`. The evaluator resolves those paths into the stage packet and recomputes:

```text
R01_REQUIRED_JOINT_UID_SET == REGISTRY_JOINT_UID_SET[VERSION]
R02_EACH_JOINT_HAS_17_VALUE_CELLS_AND_SCAFFOLD == true
R03_EACH_JOINT_HAS_OPERATION_APPROPRIATE_BINDING == true
R04_ROLE_LAYER_STATE_RESULT_SEPARATION == true
R05_VERSION_SPECIFIC_DEPTH == true
R06_EACH_PROOF_SOURCE_OR_REQUIREMENT_REF_RESOLVES == true
R07_STAGE_HANDOFF_IDENTITY == true
```

`R03` means every value cell has a typed slot and Source-requirement ref in `DESIGN_STAGE`, and a non-HOLD Source-backed semantic value plus its exact surfaced span or explicit `IMPLICIT` realization record in `EXACT_STAGE_REVERSE`. An `IMPLICIT` record must cite the approved derivation and Source input; it cannot be inferred from fluency.

`R04` is computed from occurrence UIDs and semantic-role enums. Any simultaneously present `BODY / OPERATOR / DIRECT_OBJECT / FIELD` roles have distinct occurrence UIDs. `PRE_STATE / TRANSFORMATION / POST_STATE` have distinct addresses and directional value lineage. `STRUCTURE / OCCURRENCE / TRANSFER / ARRIVAL / ATTRIBUTION / OWNERSHIP / RETENTION / RECOVERY / TIMING` result categories use distinct result-stage addresses; one slot cannot certify two categories.

`R05` first requires the exact joint set shown in the table and then applies the additional version checks below:

- V3: `PRE_STATE.VALUE_ID != POST_STATE.VALUE_ID`, the transformation connects them, and transfer/arrival/result-boundary records remain separately addressed.
- V4: direct evidence and precondition use different addresses; preceding, dependent, and support authority roles remain ordered; the blocked leap and conditional conclusion boundary are separate values.
- V5: common-root, capability branch, distortion branch, minimum transition, and final boundary have separate addresses and Source backmaps; neither branch may be mirrored from the other without Source.
- V6: compute the two layer signatures below and require `V6_LAYER_DISTINCT_PASS=true`.
- V7: compute the independent lower-structure paths and Source bindings below and require `V7_TWO_LOWER_STRUCTURES_PASS=true`; the invariant joint itself remains covered by the normal R5 cell-binding gates.

For V6, compare `V6.INNER_GENERATIVE_MECHANISM` and `V6.DEEPEST_CORE_JOINT` with the guard's exact computed signature:

```text
V6_DISTINCT_FIELD_SET = {
  GRAMMATICAL_SUBJECT,
  DIRECT_OBJECT,
  TRANSFORMATION,
  HANDOFF_VALUE
}

V6_FIELD_SIGNATURE(cell) =
  IF OPERATION == DESIGN_STAGE: cell.input_ref
  IF OPERATION == EXACT_STAGE_REVERSE: (cell.source_ref, cell.value)

V6_LAYER_DISTINCT_PASS = NOT AND(
  V6_FIELD_SIGNATURE(INNER[field]) == V6_FIELD_SIGNATURE(DEEPEST[field])
  for every field in V6_DISTINCT_FIELD_SET
)
```

Thus the two layers fail when all four computed signatures are clones. Their upward continuity is not inferred from this distinctness check; it must separately pass `HANDOFF_CHAIN`, `HANDOFF_TEST_TOKEN`, and `HANDOFF_SEMANTIC_LEDGER`.

For V7, every lower-structure record must have this exact five-part path and field order:

```text
LOWER_PATH_PART_SET = {INPUT, OPERATION, TRANSFORMATION, HANDOFF, RESULT}
LOWER_PATH(structure_id) = ordered five non-empty VALUE_ID records
```

Every record has a non-empty unique `structure_id` and non-empty `independence_basis`. Every part has its own binding ref, and all refs across all selected lower structures and all five parts are unique.

```text
V7_PART_BINDING_PASS(part) =
  IF OPERATION == DESIGN_STAGE:
    part.input_ref starts with one of {
      SOURCE_REQUIREMENT:, USER_INPUT:, CURRENT_USER:, SOURCE:
    }
    AND part.value_state in {UNBOUND, HOLD}
    AND part.value in {null, ""}
  IF OPERATION == EXACT_STAGE_REVERSE:
    part.source_ref starts with one of {
      SOURCE:, USER_EXACT:, CURRENT_USER:
    }
    AND part.value is a non-empty exact string
    AND part.binding_authority == SOURCE_EXACT

V7_TWO_LOWER_STRUCTURES_PASS =
  LOWER_STRUCTURE_COUNT >= 2
  AND EVERY_LOWER_STRUCTURE.FIELD_KEY_ARRAY == [
    input, operation, transformation, handoff, result
  ]
  AND EVERY_STRUCTURE_ID_NONEMPTY_AND_UNIQUE
  AND EVERY_INDEPENDENCE_BASIS_NONEMPTY
  AND V7_PART_BINDING_PASS(every part)
  AND BINDING_REF_COUNT == LOWER_STRUCTURE_COUNT * 5
  AND UNIQUE_BINDING_REF_COUNT == BINDING_REF_COUNT
```

These checks normalize into `REGISTRY_CANON / VERSION_SET_AND_ORDER / VERSION_SEPARATION / JOINT_ORDER / OCCURRENCE_SENTINEL_UNIQUE / DIRECTED_TRANSFORMATION / V6_LAYER_DISTINCT / V7_TWO_LOWER_STRUCTURES` used by `FNA98_RESOLUTION` in section 13.4.

### 13.3 Completeness execution gate

Completeness is the executed conjunction of handoff continuity, binding authority, native child audit, visibility, and operation-native proof. The guard uses these exact input states:

```text
DESIGN_STAGE = {
  stage.binding_authority: SOURCE_REQUIREMENTS_ONLY,
  stage.exact_roundtrip_state: NOT_APPLICABLE_UNTIL_FILLED,
  STATUS.control_state: HOLD,
  semantic_cell.binding_authority: SOURCE_REQUIREMENT_ONLY,
  semantic_cell.value_state: UNBOUND | HOLD,
  semantic_cell.value: null | "",
  semantic_cell.input_ref_prefix: SOURCE_REQUIREMENT: | USER_INPUT: | CURRENT_USER: | SOURCE:
}

EXACT_STAGE_REVERSE = {
  stage.binding_authority: SOURCE_EXACT,
  stage.exact_roundtrip_state: REQUIRES_EXECUTED_AUDIT,
  STATUS.control_state: REQUIRES_EXECUTED_AUDIT,
  semantic_cell.binding_authority: SOURCE_EXACT,
  semantic_cell.value: NONEMPTY_EXACT_STRING,
  semantic_cell.source_ref_prefix: SOURCE: | USER_EXACT: | CURRENT_USER:
}

SURFACE_SCAFFOLD = {
  template_ref: NONEMPTY,
  literal_authority: NONEMPTY_AUTHORIZED_REF_ARRAY
}
```

`HANDOFF_CHAIN` validates the registry links and, in exact mode, actual handoff-value continuity. `HANDOFF_TEST_TOKEN` validates a token per edge that never collides with an occurrence probe. `HANDOFF_SEMANTIC_LEDGER` requires the derived producer/consumer ledger exactly. `CELL_BINDING_BOUNDARY` and `NO_INVENTED_BINDINGS` enforce the operation-specific schemas above. `CHILD_NATIVE_AUDIT` requires every joint's TITI design or exact reverse child guard to pass; `EXACT_NATIVE_ROUNDTRIP` is additionally mandatory only for `EXACT_STAGE_REVERSE`. `DESIGN_NO_FALSE_EXACT` is mandatory only for `DESIGN_STAGE`. A declared top-level PASS cannot replace a child audit.

The visibility gate compares exactly:

```text
OUTPUT_VISIBILITY = {
  show_internal_ids: false,
  show_numbers: false,
  show_validation_table: false,
  render_academic_paragraphs: true
}
```

Registry closure, all nineteen cells, the seventeen-cell function partition, Source binding, and version-specific depth remain mandatory through the Density and Resolution primitive gates. Completeness cannot compensate for a failure in either axis.

### 13.4 Allowed FNa98 statuses

The machine-authoritative three-axis formulas use the guard's exact gate names:

```text
FNA98_DENSITY = AND(
  JOINT_COUNT,
  REQUIRED_CELL_SET,
  PARAGRAPH_FUNCTIONS,
  FUNCTION_CELL_PARTITION,
  NO_DUPLICATE_CLAIM_PADDING
)

FNA98_RESOLUTION = AND(
  REGISTRY_CANON,
  VERSION_SET_AND_ORDER,
  VERSION_SEPARATION,
  JOINT_ORDER,
  OCCURRENCE_SENTINEL_UNIQUE,
  DIRECTED_TRANSFORMATION,
  V6_LAYER_DISTINCT,
  V7_TWO_LOWER_STRUCTURES
)

OPERATION_NATIVE_GATE =
  IF OPERATION == DESIGN_STAGE: DESIGN_NO_FALSE_EXACT
  IF OPERATION == EXACT_STAGE_REVERSE: EXACT_NATIVE_ROUNDTRIP

FNA98_COMPLETENESS = AND(
  CONTRACT,
  MODE,
  OPERATION,
  HANDOFF_CHAIN,
  HANDOFF_TEST_TOKEN,
  HANDOFF_SEMANTIC_LEDGER,
  CELL_BINDING_BOUNDARY,
  NO_INVENTED_BINDINGS,
  CHILD_NATIVE_AUDIT,
  OUTPUT_VISIBILITY,
  NO_FALSE_EXACT_CLAIM,
  OPERATION_NATIVE_GATE
)

FNA98_DESIGN_READY =
  OPERATION == DESIGN_STAGE
  AND FNA98_DENSITY
  AND FNA98_RESOLUTION
  AND FNA98_COMPLETENESS

FNA98_SENTENCE_PASS =
  OPERATION == EXACT_STAGE_REVERSE
  AND FNA98_DENSITY
  AND FNA98_RESOLUTION
  AND FNA98_COMPLETENESS
```

`FNA98_DENSITY`, `FNA98_RESOLUTION`, and `FNA98_COMPLETENESS` are derived from the named primitive gates; declared incoming quality values are ignored. `DESIGN_STAGE` may emit only `FNA98_DESIGN_READY`; it can never emit `FNA98_SENTENCE_PASS`. Only `EXACT_STAGE_REVERSE` may emit `FNA98_SENTENCE_PASS`. If any primitive gate in any axis fails, both success labels are forbidden and the guard returns `FNA98_REVISE`; missing or unauthorized Source and V7 lower-structure evidence remain semantically `HOLD` at the blocked records.

## 14. Required gates

The executable guard owns this exact primitive gate set:

```text
CONTRACT
MODE
OPERATION
REGISTRY_CANON
VERSION_SET_AND_ORDER
VERSION_SEPARATION
JOINT_COUNT
JOINT_ORDER
REQUIRED_CELL_SET
PARAGRAPH_FUNCTIONS
FUNCTION_CELL_PARTITION
NO_DUPLICATE_CLAIM_PADDING
DIRECTED_TRANSFORMATION
HANDOFF_CHAIN
OCCURRENCE_SENTINEL_UNIQUE
HANDOFF_SEMANTIC_LEDGER
HANDOFF_TEST_TOKEN
V6_LAYER_DISTINCT
CELL_BINDING_BOUNDARY
NO_INVENTED_BINDINGS
DESIGN_NO_FALSE_EXACT
NO_FALSE_EXACT_CLAIM
CHILD_NATIVE_AUDIT
EXACT_NATIVE_ROUNDTRIP
V7_TWO_LOWER_STRUCTURES
OUTPUT_VISIBILITY
FNA98_DENSITY
FNA98_RESOLUTION
FNA98_COMPLETENESS
```

`VERSION_ISOLATION` in the conceptual contract is executed as `VERSION_SET_AND_ORDER + VERSION_SEPARATION + JOINT_ORDER`. `DESIGN_NO_FALSE_EXACT` is the design-native operation gate; `EXACT_NATIVE_ROUNDTRIP` is the exact-native operation gate. `V7_TWO_LOWER_STRUCTURES` implements the five-part independent lower-path and distinct Source-binding test above.

## 15. Status and fail-closed behavior

- `FNA98_DESIGN_READY`: every design, Density, Resolution, Completeness-design, and sentinel gate passes; exact source equality remains not applicable.
- `FNA98_SENTENCE_PASS`: the R5 stage and Source gates, all three FNa98 axes, and every exact reverse-render invariant pass.
- `REVISE`: authorized Source exists, but a repairable scaffold, capture, UID, order, map, or handoff defect remains.
- `HOLD`: a required Source, approved sentence, stage joint, semantic value, evidence authority, or V7 lower structure/backmap is unavailable.

Fail closed on any of the following:

- wrong version mapping, joint count, registry order, or paragraph count;
- one joint merged with another or replaced by a summary sentence;
- any missing one of the nineteen cells or four paragraph functions;
- a paragraph, sentence, or stage hidden in a catch-all slot;
- adjacent placeholders, ambiguous reverse capture, duplicated UID, or reused occurrence;
- invented or context-inferred values, transformations, WHY links, handoffs, or Source coordinates;
- mismatched `HANDOFF_VALUE` and next `PREVIOUS_OUTPUT`;
- a loop, orphan, unknown handoff, or cross-version handoff;
- exact PASS claimed from a design sentinel;
- paraphrase, Unicode normalization, spacing repair, particle change, punctuation change, or line-order change before exact comparison;
- a V7 law built from fewer than two independent lower structures or incomplete Source backmaps;
- a partial-stage output labeled a complete R5 version;
- one version used to fill, repair, promote, or overwrite another version.
- any FNa98 label asserted without the three-axis audit evidence, or any one axis failing at one joint.

No failed gate may be hidden with fluent prose. Report the first blocked joint and the exact missing or broken dependency, preserve all verified upstream records, and stop downstream certification at that boundary.

## 16. FNa98 delivery lock

Every user-facing result must comply with FNa98 and the user's requested format. Lead with the outcome. For final prose, hide internal joint IDs, slot UIDs, numbers, and validation tables unless the user explicitly requests the engineering bundle. For a template or audit request, expose only the requested technical artifacts and keep internal sentinels private.

Never label a structurally designed packet as an exact reverse-rendered sentence. Never label a byte-perfect roundtrip as semantically valid unless the R5 and Source gates also pass.
