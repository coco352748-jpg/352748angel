# TITI Family Grammar Forge V1

## Purpose

Extract a reusable grammar from two or more exact source sentences without flattening their differences.

```text
CONTRACT=TITI_FAMILY_GRAMMAR_V1
OWNER=$clone-titi
MODE=FAMILY_GRAMMAR_FORGE
INPUT=2_OR_MORE_EXACT_SENTENCES
OUTPUT=LOCAL_EXACT_PAIRS + FAMILY_SLOTS + STRUCTURAL_VARIANTS
EQUALITY=EXACT_SURFACE_PER_RECORD
```

## Execution order

1. Freeze every source sentence and assign a stable record ID.
2. Run TITI's ordinary sentence↔micro reverse design on each record.
3. Require every local record to pass exact bidirectional roundtrip.
4. Group only slots that have the same grammatical type and semantic role.
5. Map each local UID to exactly one Family slot.
6. Group records into variants by normalized literal scaffold and role/type placeholder order.
7. Recompile every local record to its own exact source sentence.

Family extraction never replaces the local exact templates. The local templates remain the executable ground truth.

## Family slot

```json
{
  "family_slot_id": "OCCUPANT_PLANET",
  "type": "NP",
  "semantic_role": "occupant_planet",
  "required_across_records": true,
  "members": {
    "S1": "S1.OCCUPANT.OCCUPANT_PLANET_NP.01",
    "S2": "S2.OCCUPANT.OCCUPANT_PLANET_NP.01"
  }
}
```

- `family_slot_id` is unique inside the Family.
- `type` and `semantic_role` must equal every mapped local slot.
- `members` maps record IDs to existing local UIDs.
- A required slot must cover every record.
- An optional slot may cover a subset, but every covered UID still has to match type and role.
- One local UID may belong to only one Family slot.

## Structural variant

A variant groups records whose templates become byte-identical after each local UID is replaced with its locked `type:semantic_role` token.

```json
{
  "variant_id": "V1",
  "record_ids": ["S1", "S2"]
}
```

Different particles, connectives, punctuation, literal words, or placeholder order require separate variants. Do not erase a difference merely to increase reuse.

## Required gates

```text
FAMILY_CONTRACT
EQUALITY_MODE
LOCAL_RECORD_ROUNDTRIP
FAMILY_SLOT_ID_UNIQUE
MEMBER_UID_VALID
MEMBER_UID_UNIQUE
ROLE_TYPE_STABLE
REQUIRED_COVERAGE
LOCAL_SLOT_COVERAGE
VARIANT_ID_UNIQUE
VARIANT_ASSIGNMENT
VARIANT_SKELETON_STABLE
```

All gates must pass. A local pair failure blocks only the affected Family bundle; it never authorizes rewriting the source sentence.

## Failure boundaries

Reject:

- grouping different semantic roles under one Family slot;
- grouping different slot types without an explicit new Family slot;
- mapping one local UID to multiple Family slots;
- leaving local slots unclassified;
- assigning a record to zero or multiple variants;
- forcing different literal scaffolds into one variant;
- claiming a shared grammar before every local record roundtrips exactly;
- replacing exact local templates with a lossy generalized template.

## Delivery

Default output:

1. exact local sentence-template records;
2. `family_slots` mapping;
3. `variants` mapping;
4. a short PASS audit.

Keep validation detail internal unless a gate fails or the user requests it. Output always follows the current user format and FNa98.
