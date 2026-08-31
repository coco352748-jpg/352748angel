# KANI 21-Layer Vedic Academic–Life Forge

```text
CONTRACT_ID=KANI_21_LAYER_VEDIC_ACADEMIC_LIFE_FORGE_V2
EXECUTION_OWNER=KANI_ONLY
USER_VISIBLE_ROUTE=ALL_21_VISIBLE_LAYERS
CANONICAL_UNIT_COUNT=19
ROLES_PER_UNIT=3
ROLE_PACKET_COUNT=57
TERMINAL_UNIT=21
REGISTRATION_AND_ANALYSIS_STATES=SEPARATE
CONFLICT_POLICY=LOCAL_HOLD_NO_SILENT_RESOLUTION
PUBLICATION_STATE=FORBIDDEN
ANALYSIS_VALIDATION=NOT_RUN_NO_RUN_BUNDLE
ACADEMIC_GATE=HOLD_UNEXECUTED
LIFE_CONGRUENCE_GATE=HOLD_UNEXECUTED
MACHINE_EXECUTION_AUTHORITY=HASH_LOCKED_REGISTRATION_AND_RUN_BUNDLE
CONTRACT_CONFLICT=HOLD
ROUTE_AUTHORITY=RQ_VEDIC_19_LAYER_V1_PROJECT_PROTOCOL_NOT_CLASSICAL_JYOTISH_CANON
METHOD_CORPUS_LOCK=BEFORE_INTERPRETATION
LIFE_EXPOSURE_LOG=MANDATORY
READINESS_AUTHORITY=ACTUAL_RUN_VALIDATOR_ONLY
USER_VISIBLE_STAGE_SEQUENCE=V3_V4_V5
V3=PIKACHU_FIRST_ANALYSIS_BASELINE
V4=UNIVERSITY_THESIS_DEPTH
V5=CONFERENCE_PRESENTATION_REVIEW_DEPTH
V4_DOMAIN_BENCHMARK=BHU_DEPARTMENT_OF_JYOTISH
V4_WRITING_BENCHMARK=OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_RUBRIC_TARGET
INTERNAL_ENGINE_ALIAS_V4=RQ_R5_V5
INTERNAL_ENGINE_ALIAS_V5=RQ_R5_V7
INSTITUTIONAL_ENDORSEMENT=NOT_CLAIMED
```

This reference registers a KANI-only forge for deepening the completed first
PikaChu V3 analysis into the explicitly named user-visible V4 and V5 products and, only
after the chart-native analysis is frozen, comparing the frozen claims with
admitted life evidence. It is an execution and evidence contract. It is not a
claim that a university, conference, editor, reviewer, or scholarly society has
accepted, reviewed, endorsed, or published any output.

The user-visible phrase “all 21 layers” names the route that reaches the
source-defined terminal unit `21`. The canonical source map contains nineteen
top-level units. Do not invent two filler units, renumber the route, or turn the
label into an unsupported count. The exact unit roster is:

```text
1, 2, 3, 4, D-1, 5-4, 6, 7, 8, 9, 10, 12, 13, 14, 17, 18, 19, 20, 21
```

This route is the project protocol
`RQ_VEDIC_19_LAYER_V1_PROJECT_PROTOCOL_NOT_CLASSICAL_JYOTISH_CANON`. Its unit
names and order are authoritative for this KANI project; do not misrepresent
the route itself as a universally recognized classical Jyotish canon.

## 1. Exact user authority

The four normalized authority strings are immutable inputs to this contract.
They must appear byte-for-byte and in this order in the registration record:

1. `피카츄 파일을 보면 1차분석을 해놧잖아 그보다 높은 학문적 깊이가 필요한거지`
2. `베딕 학문적으로 4 5 단계를 얘기한거임 5단계는 학회발표 4단계는 대학생논문수준 정도가 되지 않을까요?`
3. `21단계 모두사용해서 말입니다`
4. `내가 받은 분석이 학문적 근거가 있고 사회적으로 내놓아도 흠잡히지 않을 수준 학회발표정도는 되야 가능할것 같고 또 실제 내 삶과도 일치하게 설명할수 있을거 같아서요`

```text
AUTHORITY_PROVENANCE=IN_TURN_DIRECT_USER_MESSAGES_GIT_COMMITTED_REGISTRATION
AUTHORITY_SCOPE=KANI_ONLY_FORGE_DESIGN_AND_REGISTRATION
CONTRACT_AUTHORITY_MACHINE=HASH_LOCKED_REGISTRATION_AND_RUN_BUNDLE
CONTRACT_AUTHORITY_HUMAN_GUIDANCE=references/KANI_21_LAYER_VEDIC_ACADEMIC_LIFE_FORGE.md
CONTRACT_AUTHORITY_CONFLICT=HOLD
REGISTRATION_SCOPE=INSTALLATION_ONLY
ANALYSIS_VALIDATION=NOT_RUN_NO_RUN_BUNDLE
```

Do not invent a session ID, transcript timestamp, or external authority marker.

These strings authorize the requested depth, route, and life-comparison design.
They do not authorize fabricated chart values, invented scholarship, hidden
life inference, automatic publication, a claim of peer review, or a claim of
conference acceptance.

## 2. Stage names and non-claims

The public stage names are exactly `V3 → V4 → V5`. Internal RQ-R5 namespaces
are implementation aliases only and never replace the public labels:

| Public stage | User-visible contract | Internal RQ-R5 engine alias |
|---|---|---|
| `V3` | `PIKACHU_FIRST_ANALYSIS_BASELINE`; completed comparison baseline and default entry depth | `RQ_R5_V3` |
| `V4` | `UNIVERSITY_THESIS_DEPTH`; dual-benchmark undergraduate thesis rigor target | `RQ_R5_V5` |
| `V5` | `CONFERENCE_PRESENTATION_REVIEW_DEPTH`; internally reviewable conference-presentation form | `RQ_R5_V7` |

The V4 dual benchmark has two non-interchangeable roles:

1. `BHU_DEPARTMENT_OF_JYOTISH` is the Jyotish-domain anchor. The official BHU
   department describes Jyotishshastra through Siddhanta, Samhita, and Hora.
2. `OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_RUBRIC_TARGET` is the academic-writing
   target: research question, primary/secondary literature, coherent critical
   argument, source criticism, structure, citation, limitations, and sustained
   dissertation-quality discussion. Oxford is not used as a Jyotish-domain
   authority.

Official benchmark locators, checked for this registration on 2026-08-31:

- BHU Department of Jyotish:
  `https://www.bhu.ac.in/site/UnitHomeTemplate/1_131_653_Faculty-of-Sanskrit-Vidya-Dharma-Vijnan-Jyotish`
- BHU Department of Jyotish programmes:
  `https://www.bhu.ac.in/site/Programme/0_131_664_Department-of-Jyotish-Programmes`
- Oxford Sanskrit BA (Hons):
  `https://www.ames.ox.ac.uk/sanskrit-ba-hons`
- Oxford BA Sanskrit FHS handbook target:
  `https://www.ames.ox.ac.uk/sites/default/files/orinst/documents/media/ba_sanskrit_handbook_2025-26.pdf`

These are internal reference benchmarks, not institutional participation.
Neither BHU nor Oxford has reviewed, certified, endorsed, accepted, awarded,
or approved any KANI output. Oxford has no role here as a Jyotish department,
and BHU's official existence does not prove KANI's claims. A future benchmark
refresh may update locators or rubric details only through a new hash-locked
registration revision; it may not silently alter an executed run.

Public `V5` never means `ACCEPTED`, `PEER_REVIEWED`, `PUBLISHED`, `ENDORSED`, or
`CONFERENCE_PRESENTED`. Those states remain `NOT_CLAIMED` unless independent
external evidence is later supplied and explicitly admitted for that separate
purpose. “학회발표 수준” may be rendered only as
“conference-presentation review depth,” never as a completed institutional
outcome. It has no named conference or society benchmark in this registration.

V3 is a completed baseline, not a disposable draft. Public V4 and V5 must deepen it
through an exhaustive delta ledger. They may correct a baseline item only with
an exact reason and source trail; they may not silently rewrite the baseline.

### Public V4/V5 and internal RQ-R5 joint records

Stage readiness is based on concrete joint records, not a count or a polished
summary. `15_user_v4_r5_v5_joint_records.jsonl` contains exactly one addressable
record for each of these seven internal RQ-R5 V5 joints that implement public
V4, in order:

```text
V5.STRUCTURE_VERDICT
V5.INPUT_SELECTION
V5.OPERATION_TRANSFER
V5.COMMON_ROOT
V5.CAPABILITY_DISTORTION_BRANCH
V5.MINIMUM_TRANSITION
V5.FINAL_STRUCTURE_LOCK
```

`16_user_v5_r5_v7_joint_records.jsonl` contains exactly one addressable record
for each of these eight internal RQ-R5 V7 joints that implement public V5, in
order:

```text
V7.JURISDICTION
V7.REPEATED_EVIDENCE_INVARIANT
V7.SUPERORDINATE_RULE
V7.APPLICATION_GATE
V7.JUDGMENT_PRIORITY
V7.OPERATING_ORDER
V7.EXCEPTION_COUNTEREXAMPLE_PROHIBITION
V7.TERMINATION_CODE_LOCK
```

Every joint record binds the exact joint ID, input claim IDs, previous-output
hash, grammatical/structural operator, direct object, method and source refs,
pre-state, transformation, post-state, Why, handoff value and hash, result
boundary, state, and holds. The output hash of one joint must equal the next
joint's previous-input hash. A missing, duplicated, renamed, summary-only, or
count-only joint is `ACADEMIC_GATE=HOLD_UNEXECUTED` or `ANALYSIS_HOLD`.

Public V5 additionally requires `17_lower_structure_independence_graph.json`. The
graph names each lower structure and binds its separate input/source ancestry,
claim set, operation path, and hash. At least two lower structures must be
independent at the asserted invariant: copying one claim tree, renaming a
coordinate, or sharing the decisive unsupported ancestor does not satisfy
independence. If fewer than two independently traceable lower structures remain,
internal `V7.REPEATED_EVIDENCE_INVARIANT` and every dependent internal V7 joint
are `HOLD`.

## 3. Registration state is not analysis state

Registration and execution use independent state machines.

Registration states:

```text
UNREGISTERED
INSTALLED_LOCAL_CONTRACT
VALIDATED_LOCAL_CONTRACT
REGISTRATION_HOLD
```

Per-run analysis states:

```text
NOT_RUN
SOURCE_LOCKED
METHOD_CORPUS_LOCKED
ROUTE_RUNNING
CHART_NATIVE_FROZEN
LIFE_COMPARISON_RUNNING
RUN_VALIDATED
ANALYSIS_HOLD
```

The presence or validation of this reference proves only the registration
state. It does not prove that any target analysis ran, that any public V4/V5 product
passed, or that a life comparison occurred. The registration record therefore
starts with `analysis_state=NOT_RUN` even while it records V3 as the completed
historical baseline.

Its exact initial execution gates are:

```text
ANALYSIS_VALIDATION=NOT_RUN_NO_RUN_BUNDLE
ACADEMIC_GATE=HOLD_UNEXECUTED
LIFE_CONGRUENCE_GATE=HOLD_UNEXECUTED
```

The registration validator can validate contract paths, bytes, hashes, enums,
and registration shape only. It has no authority to change those three gates.
Readiness is derived only by the actual run validator after it reopens a
complete coordinate run bundle and its review record.

No state may be promoted from prose, file presence, self-report, or a nearby
run. Promotion requires the exact target's run bundle, manifest, reopen hashes,
and declared validators.

## 4. Canonical 19-unit route and 57 role packets

Every unit materializes exactly three role packets in this fixed order:

1. `ELIVEDIC` — `SOURCE_FACT_OBSERVATION`: preserve the admitted chart fact,
   source locator, authority, state, and boundary without interpretation.
2. `ELICOLLEGE` — `METHOD_PATTERN_COMPARISON`: state the admitted scholarly or
   source-defined method, comparison pattern, applicability, limits, and
   citation trail without altering the fact packet.
3. `ELIPHD` — `DERIVED_CLAIM_DEEP_STRUCTURE`: derive the bounded mechanism,
   causal/processing structure, qualification, and claim state from the first
   two packets. It cannot promote a held fact or method.

The role names are authoritative. The semantic labels explain their duties but
may not replace the names. All 57 packets are mandatory roster entries, even
when an entry's truthful state is `NOT_APPLICABLE`, `NOT_SUPPLIED`, `HOLD`, or
`CONFLICT`.

| Order | Unit | Three required role packet IDs | Source-defined unit boundary |
|---:|---|---|---|
| 01 | `1` | `U01_ELIVEDIC`, `U01_ELICOLLEGE`, `U01_ELIPHD` | Rashi baseline; preserve sign, graha, degree, nakshatra, and pada values |
| 02 | `2` | `U02_ELIVEDIC`, `U02_ELICOLLEGE`, `U02_ELIPHD` | Bhava reality position; do not overwrite it with Rashi |
| 03 | `3` | `U03_ELIVEDIC`, `U03_ELICOLLEGE`, `U03_ELIPHD` | Rashi–Bhava move judgment; preserve both pre-move values |
| 04 | `4` | `U04_ELIVEDIC`, `U04_ELICOLLEGE`, `U04_ELIPHD` | Co-presence field; co-presence and degree order are not causality or time order |
| 05 | `D-1` | `U05_ELIVEDIC`, `U05_ELICOLLEGE`, `U05_ELIPHD` | Background group: `5-1` Pushkara, `5-2` Upagraha, `5-3` Chalit; `METHOD_SPECIFIC` |
| 06 | `5-4` | `U06_ELIVEDIC`, `U06_ELICOLLEGE`, `U06_ELIPHD` | Moon/Chandra-Lagna reference; `METHOD_SPECIFIC_UNLESS_SOURCE_BOUND` |
| 07 | `6` | `U07_ELIVEDIC`, `U07_ELICOLLEGE`, `U07_ELIPHD` | Arudha surface representation; do not promote appearance into native ownership |
| 08 | `7` | `U08_ELIVEDIC`, `U08_ELICOLLEGE`, `U08_ELIPHD` | Strength + aspect combination; non-additive, no double count, target-native and D1-reference separated |
| 09 | `8` | `U09_ELIVEDIC`, `U09_ELICOLLEGE`, `U09_ELIPHD` | Mrityu/SPother limitation and special-point group; auxiliary only |
| 10 | `9` | `U10_ELIVEDIC`, `U10_ELICOLLEGE`, `U10_ELIPHD` | `AVA` planet-relationship reference; keep distinct from unit `19` Ava |
| 11 | `10` | `U11_ELIVEDIC`, `U11_ELICOLLEGE`, `U11_ELIPHD` | Bhinna raw matrix; never collapse raw rows into an event conclusion |
| 12 | `12` | `U12_ELIVEDIC`, `U12_ELICOLLEGE`, `U12_ELIPHD` | SAP/TKS/EKS/SDP completion stages; preserve each non-interchangeable stage |
| 13 | `13` | `U13_ELIVEDIC`, `U13_ELICOLLEGE`, `U13_ELIPHD` | Varga Mini candidate link; candidate only until full confirmation |
| 14 | `14` | `U14_ELIVEDIC`, `U14_ELICOLLEGE`, `U14_ELIPHD` | Varga Full repeat confirmation; repetition is not automatic strength or event proof |
| 15 | `17` | `U15_ELIVEDIC`, `U15_ELICOLLEGE`, `U15_ELIPHD` | Dasha time window; a window does not itself prove occurrence |
| 16 | `18` | `U16_ELIVEDIC`, `U16_ELICOLLEGE`, `U16_ELIPHD` | Trimming/Timing Gate; match candidates only, no independent event conclusion |
| 17 | `19` | `U17_ELIVEDIC`, `U17_ELICOLLEGE`, `U17_ELIPHD` | Post-timing Ava condition; state, contamination, recovery, or relocation after a match |
| 18 | `20` | `U18_ELIVEDIC`, `U18_ELICOLLEGE`, `U18_ELIPHD` | Yoga condition check; existence does not prove manifestation |
| 19 | `21` | `U19_ELIVEDIC`, `U19_ELICOLLEGE`, `U19_ELIPHD` | Transit context with timestamp and canonical-state lock; terminal handoff only |

Each role packet must contain at least:

```text
role_packet_id
unit
role_type
semantic_duty
state
source_refs[]
method_refs[]
claim_refs[]
boundaries[]
holds[]
handoff_hash
```

The unit order and role order are hash-relevant. A later stage may add detail
inside a packet but may not add a twentieth unit, omit a packet, rename a role,
or reorder the 57-packet roster.

## 5. PikaChu exhaustive delta ledger

V3 is admitted through an exact PikaChu baseline roster. Before public V4 or V5
writing, enumerate every physical baseline member and every atomic baseline
claim. If the current KANI V10 promotion corpus is selected, the expected
physical denominator is twenty archives × thirty members = 600, including the
twenty physical `3P` members whose operational state remains `VOID`, leaving
580 active non-`3P` members. If the selected exact source disagrees with that
roster, preserve the discrepancy as `CONFLICT`; do not force the denominator.

The baseline roster binds the exact baseline path, bytes, SHA-256, sorted unique
`complete_claim_ids`, and `complete_claim_id_set_sha256`. Delta completeness is
exact set equality, not a matching count:

```text
set(delta.baseline_claim_ids) = set(baseline.complete_claim_ids)
missing_claim_ids = []
extra_claim_ids = []
duplicate_claim_ids = []
```

Two different claim-ID sets with the same cardinality fail. A baseline item
without an atomic claim ID remains visible and `HOLD`; it cannot disappear from
the denominator.

`03_pikachu_delta_ledger.jsonl` must have at least one classified record for
every baseline roster item. It must also record every new public V4/V5 claim. Allowed
delta operations are:

```text
UNCHANGED
DEEPENED
CORRECTED
SPLIT
MERGED_WITH_PROVENANCE
HELD
REMOVED_WITH_REASON
NEW
```

Each delta record contains the baseline ID and hash, new claim IDs, operation,
before and after text or hashes, reason, source refs, method refs, affected role
packet IDs, authorizing state, and downstream impact. `CORRECTED`, `MERGED`, or
`REMOVED` without a source-bound reason fails the run. The ledger closes only
when:

```text
baseline_roster_items = classified_baseline_items
unclassified_baseline_items = 0
new_claims = classified_new_claims
dangling_delta_refs = 0
```

SC8 numeric correction history, PikaChu structural authorship, method claims,
and the current chart analysis remain separate authorities. A preserved or
corrected sentence does not, by itself, prove its hidden judgment method.

## 6. Academic method corpus and search lock

The method corpus is a per-run, hash-locked evidence set. Search expands only
the academic method corpus; it may not supply or alter the user's chart facts,
search for the user's identity or life history, or target a desired conclusion.
`METHOD_CORPUS_LOCK=BEFORE_INTERPRETATION`: no chart interpretation or derived
claim may begin until the declared method corpus and search log are frozen.

Required sequence:

1. Hash-lock the admitted chart sources and V3 baseline.
2. Declare the method question for each applicable unit.
3. Search scholarly catalogues, databases, or publisher/primary text sources
   with exact logged queries.
4. Record every included and materially relevant excluded result with reason.
5. Freeze the corpus manifest and its aggregate hash.
6. Apply only the frozen corpus to the chart-native analysis.
7. Reopening search after life exposure creates a new run revision; it may not
   silently mutate the frozen run.

Every search-log entry records `query_exact`, provider/database, URL or stable
identifier when available, UTC time, result metadata, admission decision,
exclusion reason, and content hash or exact locator. Secondary exposition may
orient the search, but a claim presented as textual, historical, empirical, or
traditional authority requires the strongest available directly inspectable
source. No citation may be invented from title memory, a search snippet, or a
nearby bibliography.

The method corpus cannot prove that a chart claim is empirically true, and a
life match cannot retroactively validate the scholarly method corpus. Those
tracks remain separate.

## 7. Claim and citation contract

Every substantive sentence is segmented into claim IDs before final prose.
Each claim ledger record includes:

```text
claim_id
claim_type
claim_text
unit
role_packet_ids[]
source_fact_ids[]
method_rule_ids[]
citation_ids[]
delta_ids[]
life_evidence_ids[]
inference_steps[]
qualifiers[]
state
hold_reason
```

Allowed claim types are `PRIOR_ANALYSIS`, `CHART_FACT`, `METHOD_CLAIM`,
`DERIVED_INFERENCE`, `LIFE_ALIGNMENT`, and `LIMITATION`. `PRIOR_ANALYSIS`
identifies an exact V3/PikaChu baseline claim and binds its baseline path, hash,
and delta record; it is not silently recast as a current fact or method claim.
A chart fact needs an exact chart source locator, not a scholarly citation. A
method claim needs claim-level scholarly support and locator. A derived
inference must bind both its fact and method parents. A life-alignment claim
must bind a previously frozen chart claim and an admitted life-evidence event.
A limitation identifies the affected scope and may remain valid when the
related positive claim is held.

Citation records preserve author/editor, title, edition or version, year,
publisher or venue, page/section/verse locator, stable identifier or URL,
access date when applicable, source class, content hash when locally retained,
and exactly which claim IDs they support. One citation attached to a paragraph
does not automatically support every sentence in it.

Unsupported, overbroad, disputed, unavailable, or conflicting support is
`HOLD` or `CONFLICT`. Citation quantity never substitutes for claim fit.

## 8. Chart-native analysis must precede life exposure

The forge executes in this irreversible order:

```text
SOURCE_LOCK
→ PIKACHU_DELTA_CLASSIFICATION
→ METHOD_CORPUS_FREEZE
→ 19_UNITS_X_3_ROLES
→ CHART_NATIVE_CLAIMS
→ CHART_NATIVE_FREEZE_HASH
→ LIFE_EXPOSURE
→ LIFE_ALIGNMENT_LEDGER
→ PUBLIC_V4_OR_V5_RENDER
→ EXACT_REVERSE_AND_FNA98
```

The chart-native freeze contains the exact claims, states, role-packet hashes,
method-corpus hash, delta-ledger hash, and a UTC freeze event. Life evidence
cannot edit that frozen object. A material chart or method correction after the
freeze forks a new revision and retains the old freeze.

This order limits hindsight fitting. It does not turn the eventual comparison
into a blinded scientific experiment unless the selected life-exposure mode
actually satisfies the blind boundary.

## 9. Life-exposure modes, log, hash chain, and append-only roster

One mode is declared before the first life event. Each mode maps to one of the
three authoritative exposure classifications:

| Mode | Exposure classification | Meaning | Permitted claim |
|---|---|---|---|
| `L0_CLOSED` | `PROSPECTIVE` | no life evidence exposed; frozen claims may be preserved for a future test | chart-native claim only; no life-congruence result yet |
| `L1_POST_FREEZE_BLIND_COMPARE` | `BLIND_CONFIRMATORY` | chart-native freeze predates independently held life evidence | bounded post-freeze confirmation/nonconfirmation; record holder and reveal |
| `L2_POST_FREEZE_USER_CONTEXT` | `RETROSPECTIVE_EXPLANATORY` | the user supplies life context after freeze | contextual fit/non-fit, `PASS_SCOPED` at most |
| `L3_PREEXPOSED_CONTEXT` | `RETROSPECTIVE_EXPLANATORY` | the runtime or analyst had prior access to relevant life context | explanation only, `PASS_SCOPED` at most |

`RETROSPECTIVE_EXPLANATORY` never authorizes validation, prediction, or causal
language. Its strongest positive state is `PASS_SCOPED`, meaning only that the
frozen or explicitly pre-exposed structure explains the admitted life record
within the declared scope. `BLIND_CONFIRMATORY` requires a demonstrable
pre-reveal freeze and independent evidence holder. `PROSPECTIVE` requires a
time-ordered freeze, later outcome event, and no backfill; until the later event
exists, `LIFE_CONGRUENCE_GATE=HOLD_UNEXECUTED`.

If pre-exposure is discovered, downgrade the mode to `L3_PREEXPOSED_CONTEXT` by
appending a mode-change event. Never backdate `L1`. A mode switch that changes
the validation meaning requires a new run revision or a visible downgrade.

`LIFE_EXPOSURE_LOG=MANDATORY`. `12_life_exposure_log.jsonl` is append-only and records every reveal, access,
mode change, correction, and withdrawal request. `13_life_evidence_roster.jsonl`
is also append-only and records each exact statement or content-addressed
attachment, speaker/source authority, date known versus date disclosed, scope,
reliability note, and affected life claims. Corrections append a new item with
`supersedes`; they do not overwrite history. A withdrawal appends a tombstone
that blocks future use while preserving audit continuity.

The roster deduplicates by exact evidence ID plus payload hash. Repeated access
to the same payload appends an access event but not a second evidence identity.
If two records claim the same evidence ID with different payload hashes, both
remain visible as `CONFLICT`. Tombstones, superseding records, and dedup links
are themselves hash-chained events and never delete earlier bytes.

Both files use an event hash chain. The first event's
`previous_event_sha256` is sixty-four zeroes. For every later event:

```text
event_sha256 = SHA256(
  previous_event_sha256 + "\n" + UTF8_JCS(event_without_event_sha256)
)
```

The run manifest binds each chain head, line count, and exact file hash. Chain
break, deletion, reordering, duplicate event ID, unlogged life access, or a
roster item without an exposure event is a hard `ANALYSIS_HOLD`.

`14_life_alignment_ledger.jsonl` compares frozen chart claims with roster items
using `MATCH`, `PARTIAL_MATCH`, `NONMATCH`, `UNKNOWN`, or `CONFLICT`. It records
the comparison rule and both hashes. Nonmatches and contradictions are retained;
they may not be edited into matches. Life agreement may support explanatory fit
for this person. It does not prove causation, general validity, or scholarly
acceptance.

## 10. Exact target coordinates and prototype firewall

The registered forge targets are exact and independent:

| Coordinate | Source section token | Prototype rule |
|---|---|---|
| `D5_8H` | `07_7AB_D5_8H_FINAL_SYNTHESIS_PACKET` | no cross-coordinate prototype |
| `D4_10H` | `07_7AB_D4_10H_FINAL_SYNTHESIS_PACKET` | no cross-coordinate prototype |
| `D6_5H` | `07_7AB_D6_5H_FINAL_SYNTHESIS_PACKET` | `D5_5H` shape only |

For `D6_5H`, `D5_5H` may transfer only section order, field order, record
schema, and QA positions. It may not transfer values, chart facts, house facts,
interpretation, claims, citations, or life evidence. The prototype is
`D5_5H`, not `D5_8H`. Every substantive `D6_5H` cell must resolve from exact
`D6_5H` sources or remain `HOLD`.

Each coordinate receives its own source lock, 57-packet route, chart-native
freeze, life chain, reverse index, QA report, and run manifest. Cross-coordinate
comparison is a separate derived product and cannot replace the three runs.

## 11. KANI-only ownership and KK2 no-publish lock

KANI owns registration, source admission, method admission, analysis-state
promotion, user-visible rendering, and final handoff. The embedded certified
KK2 runtime may be used only as an execution substrate for permitted structural
materialization, dependency preflight, reopen checks, or existing KANI-delegated
mechanics.

```text
KANI_EXECUTION_AUTHORITY=PRIMARY_AND_ONLY
MACHINE_EXECUTION_AUTHORITY=HASH_LOCKED_REGISTRATION_AND_RUN_BUNDLE
KK2_ROLE=EMBEDDED_EXECUTION_SUBSTRATE_ONLY
KK2_REGISTRATION_AUTHORITY=NONE
KK2_ANALYSIS_PROMOTION_AUTHORITY=NONE
KK2_PUBLICATION_AUTHORITY=NONE
AUTOMATIC_EXTERNAL_PUBLICATION=FORBIDDEN
CONTRACT_CONFLICT=HOLD
```

Do not register this forge under `$clone-kk2`, publish it from KK2, claim a
standalone KK2 product, or let KK2 overwrite KANI's Source, stage, life, or
conflict states. KANI may deliver a user-requested artifact to the user. Any
later institutional submission or external publication is a separate,
explicitly authorized action and is not performed or claimed by this contract.

## 12. Per-coordinate run bundle contract

Each run directory contains exactly these required artifacts in this order:

```text
00_run_manifest.json
01_source_lock.json
02_pikachu_baseline_roster.json
03_pikachu_delta_ledger.jsonl
04_method_corpus_manifest.json
05_method_search_log.jsonl
06_claim_ledger.jsonl
07_citation_ledger.jsonl
08_route_19_units_57_roles.json
09_chart_native_analysis.md
10_chart_native_freeze.json
11_life_exposure_mode.json
12_life_exposure_log.jsonl
13_life_evidence_roster.jsonl
14_life_alignment_ledger.jsonl
15_user_v4_r5_v5_joint_records.jsonl
16_user_v5_r5_v7_joint_records.jsonl
17_lower_structure_independence_graph.json
18_stage_output_v3_v4_v5.md
19_exact_reverse_index.json
20_fna98_report.json
21_review_record.json
22_run_bundle_manifest.json
```

`00_run_manifest.json` declares run ID, coordinate, requested stage, revision,
registration-reference binding, V3 baseline binding, source scope, method-search
policy, life mode, initial states, and tool/runtime versions. It is written
before analysis and never rewritten; corrections fork a revision.

`22_run_bundle_manifest.json` binds the exact path, bytes, SHA-256, media type,
state, and dependency hashes of every required artifact. It also records all
chain heads, the chart-native freeze hash, the registration binding, validator
commands and results, reopen evidence, holds, conflicts, and final analysis
state. Missing files, undeclared extras presented as evidence, hash mismatch,
or a target mismatch fails closure.

The closure manifest must bind, as concrete records rather than counts alone:

```text
target coordinate and target hash
all admitted input paths, bytes, and SHA-256 values
method-corpus and search-log hashes frozen before interpretation
V3 baseline path, bytes, SHA-256, complete claim-ID set, and set hash
the ordered 19-unit route and all 57 role-packet hashes
PikaChu delta, claim, citation, life-exposure, roster, and alignment ledgers
all seven named internal RQ-R5 V5 joint records for public V4 and all eight
named internal RQ-R5 V7 joint records for public V5
the public V3→V4→V5 stage map and exact V4/V5 benchmark contract
the lower-structure independence graph and its ancestry hashes
chart-native freeze and life hash-chain heads
stage render, exact reverse index, and independent FNa98 report
the internal review record and actual run-validator result
```

`21_review_record.json` is an internal KANI run review, not academic peer
review. It binds reviewer/runtime identity, review authority, reviewed manifest
hash, exact validator invocation and result, reopen evidence, issue roster,
holds, conflicts, and disposition. Its label is
`INTERNAL_RUNTIME_REVIEW_NOT_PEER_REVIEW`.

Only the actual run validator may derive `ACADEMIC_GATE`,
`LIFE_CONGRUENCE_GATE`, or stage readiness from these records. The registration
validator must leave them unexecuted. A run report that asserts readiness
without the complete physical bundle and review record is invalid.

Empty life artifacts are still materialized for `L0_CLOSED` with a declared
empty-chain state. Empty search results are permitted only with the exact
queries and search failure/coverage limits logged; they do not authorize an
unsupported method claim.

## 13. FNa98 exact reverse

The independent FNa98 report retains the existing eight axes:

```text
TARGET_CHECK
FACTCHECK
SOURCE_CHECK
WHY_CHECK
LOGIC_CHECK
CONDITION_EXCEPTION_CHECK
FORMAT_CHECK
PRACTICAL_USABILITY
```

Each axis carries evidence, validator state, holds, and conflicts. `FNa98` is
not a decorative completion word. Until the physical bundle is reopened and
all eight axes have independent evidence, the report remains `RECHECK` or
`HOLD`.

`19_exact_reverse_index.json` maps every final output span exactly backward:

```text
final_span_id
→ claim_id
→ role_packet_id
→ canonical_unit
→ source_fact_id + method_rule_id
→ source/citation locator
→ PikaChu delta record
→ chart-native freeze hash
→ life event and roster item hashes, when used
```

The reverse index must also reproduce the original final span from its bound
claim text and render map. Closure requires 100% final-span coverage, all 57
role packets accounted for, zero dangling IDs, zero unsupported citations,
zero unlogged life dependencies, zero cross-coordinate source leakage, and
exact agreement with the reopened artifact hashes.

A truthful `HOLD`, `CONFLICT`, limitation, or nonmatch can pass the format and
provenance checks. Deleting or smoothing it cannot.

## 14. Conflict and HOLD propagation

Conflicts are local first and dependent second:

1. Preserve both conflicting values, sources, locators, and hashes.
2. Mark the affected fact, method, citation, life event, or role packet
   `CONFLICT`.
3. Mark every claim that depends on the unresolved joint `HOLD`.
4. Continue independent units and claims whose dependencies remain intact.
5. Surface the conflict and its exact impact in public V4/V5 prose and the bundle
   manifest.
6. Require direct source resolution or explicit user authority before a later
   revision promotes one branch.

Source absence, method-source absence, citation mismatch, chart/life mismatch,
prototype leakage, life-chain break, and state disagreement are never silently
resolved. Registration remains valid when a particular analysis is held;
analysis quality remains truthful when it exposes a hold. Neither condition
permits a false final `PASS`.

## 15. Completion conditions

The actual run validator, and no registration check, may mark public V4 ready only
when the exact coordinate's source lock, exhaustive
PikaChu delta, method corpus, 57 role packets, claim/citation ledgers,
chart-native freeze, declared life mode, seven concrete internal RQ-R5 V5 joint
records, V4 dual-benchmark trace, exact reverse index, review record, bundle
manifest, and all applicable FNa98 axes
pass or expose bounded holds without false promotion.

Public V5 requires all public V4 evidence plus eight concrete internal RQ-R5 V7
joint records, the lower-structure independence graph, and a
conference-presentation-review-depth argument structure: explicit question,
literature/method boundary, chart-native
analysis, counter-readings, limitations, claim-level citations, life-comparison
mode and results, conclusion, and reproducible reverse appendix. It still does
not claim acceptance, peer review, presentation, publication, or empirical
validation.

The forge closes one coordinate and one requested stage at a time. If a
required dependency remains unresolved, return the completed independent work
and the smallest exact `HOLD`; never substitute confidence, eloquence, or life
fit for missing evidence.
