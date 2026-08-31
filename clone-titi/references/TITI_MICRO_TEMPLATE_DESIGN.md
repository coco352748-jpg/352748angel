# TITI Micro Template Design Contract V1

## 0. Authority

```text
CONTRACT=TITI_MICRO_TEMPLATE_DESIGN_V1
CALL_KEY=$clone-titi
IDENTITY=TITI
MODE=MICRO_TEMPLATE_DESIGN
VALUE_POLICY=NO_INVENTED_VALUES
MISSING_VALUE_POLICY=HOLD_SLOT
DELIVERY_GRADE=FNa98
```

The current user instruction controls Target, Source, scope, output, and format. This contract supplies only the method for designing a new executable micro fine-slot template.

## 1. Distinction from other TITI modes

- `MICRO_TEMPLATE_DESIGN`: build a new typed template from a user-defined Target, output contract, and Source boundary. An exact finished sentence is not required.
- `REVERSE_DESIGN`: decompile one exact frozen sentence without changing a byte.
- `FAMILY_GRAMMAR_FORGE`: derive shared grammar only after two or more exact sentences pass local roundtrip.

Never require a finished source sentence for `MICRO_TEMPLATE_DESIGN`, and never call a speculative new template an exact reverse render.

## 2. Design input

Freeze the user-confirmed design brief before making slots:

- `TARGET`: what the template must produce;
- `OUTPUT_TYPE`: sentence, clause, record, or user-defined artifact;
- `SOURCE_BOUNDARY`: which inputs may fill each slot;
- `REQUIRED_JOINTS`: semantic roles or processing joints that must remain visible;
- `FORMAT`: literal order, particles, separators, sections, or schema requirements;
- `COMPLETION`: what makes the template immediately fillable and auditable.

If one required joint is unknown, leave that joint `HOLD`; do not invent a value, rule, or Source coordinate.

## 3. Design bundle

```json
{
  "contract": "TITI_MICRO_TEMPLATE_DESIGN_V1",
  "mode": "MICRO_TEMPLATE_DESIGN",
  "validation_mode": "STRUCTURAL_DESIGN",
  "exact_roundtrip_state": "NOT_APPLICABLE_UNTIL_FILLED",
  "template_id": "T1",
  "target": "Produce one source-bounded transfer sentence",
  "required_roles": ["actor", "input_object", "output_result"],
  "template": "《T1.ACTOR.SUBJECT.01》은 《T1.INPUT.OBJECT.01》을 받아 《T1.OUTPUT.RESULT.01》로 넘긴다.",
  "literal_authority_refs": ["CURRENT_USER:target", "CURRENT_USER:target", "CURRENT_USER:format", "CURRENT_USER:format"],
  "slots": [],
  "output_contract": {
    "output_type": "SENTENCE",
    "required_format": "ONE_SENTENCE",
    "missing_value_policy": "HOLD_SLOT",
    "completion_rule": "ALL_REQUIRED_SLOTS_BOUND"
  }
}
```

The real bundle must list every placeholder as one slot in exact template order.

`required_roles` must equal the semantic roles of all required slots. `literal_authority_refs` must provide one authority reference for every non-empty literal segment in template order. Design mode must keep exact sentence roundtrip `NOT_APPLICABLE` until a user-authorized fill produces a concrete sentence.

## 4. Slot contract

Every slot must contain:

- `uid`: stable occurrence address beginning with `TEMPLATE_ID.`;
- `type`: typed value class such as `NP`, `OBJECT`, `CLAUSE`, `PREDICATE`, `SERIES`, `NUMBER`, `ID`, or `TOKEN`;
- `semantic_role`: exactly one role;
- `required`: boolean;
- `input_ref`: the Source coordinate or user-input field allowed to fill the slot;
- `operator`: the approved operation, normally `INSERT_EXACT`;
- `transformation`: `NONE` or an explicitly approved rule reference;
- `handoff`: another slot UID or `OUTPUT`;
- `result_boundary`: what this slot may and may not determine;
- `value_state`: `UNBOUND` or `HOLD` in design mode.

Do not place an actual value in a design slot. Actual values belong to a later fill operation and must come from the slot's `input_ref`.

## 5. Literal scaffold

Keep fixed grammar in the literal scaffold:

- particles, endings, punctuation, and spaces;
- required connective language;
- fixed output order;
- every non-variable word.

Do not hide the whole output in one placeholder. Do not use adjacent placeholders without a literal boundary.

## 6. Handoff chain

The slot graph must form one open chain:

1. start at the first slot in template order;
2. visit every slot exactly once;
3. terminate at `OUTPUT`;
4. contain no loop, orphan, or unknown target.

This chain records assembly responsibility. It does not invent causal meaning beyond the user-approved design brief.

## 7. Structural probe

The guard creates internal sentinel values only to test the template mechanism. Sentinels are never Source values and never appear in user output.

Require:

1. every placeholder to accept exactly one sentinel;
2. forward render to consume every placeholder;
3. reverse capture to recover the same sentinels in the same UID order;
4. no ambiguity in the literal boundaries.

## 8. Required gates

```text
CONTRACT
TEMPLATE_ID
TARGET_DEFINED
PLACEHOLDER_SET_AND_ORDER
SLOT_UID_UNIQUE
SLOT_METADATA_COMPLETE
SOURCE_REQUIREMENT_COMPLETE
REQUIRED_ROLE_COVERAGE
LITERAL_AUTHORITY
NO_BOUND_VALUE_IN_DESIGN
NO_FALSE_EXACT_CLAIM
NO_ADJACENT_PLACEHOLDER
NON_DEGENERATE_LITERAL_SCAFFOLD
HANDOFF_CHAIN
OUTPUT_CONTRACT
PROBE_RENDER
PROBE_REVERSE_CAPTURE
```

All gates must pass before the template is `PASS`.

## 9. Delivery

Default package:

- `MICRO_TEMPLATE.json`
- `SLOT_SPEC.json`
- `SOURCE_REQUIREMENTS.json`
- `TEMPLATE_AUDIT.json`

Deliver a smaller inline template when the user requests it. Keep probe values and routine audit detail internal.

## 10. Fail closed

Reject or HOLD:

- requiring an exact source sentence for a new-template design job;
- inserting guessed values into unbound slots;
- one catch-all slot carrying the whole output;
- one slot carrying multiple semantic roles;
- a Source-free transformation rule;
- adjacent placeholders or an ambiguous scaffold;
- a looped or orphaned handoff;
- declaring exact reverse-render equality when no exact sentence was supplied;
- importing RQ, astrology, SC, 240-Job, or another clone route unless the current user explicitly names it.
