# design_checkout construction contract experiment

This note records a bounded experiment on the existing mobile-checkout
profile. It is not a generic contract framework, schema language, or
stable-view product.

## Principle

```text
Construction code is the executable implementation.

Generic integrity/admission rules constrain what may
be published.

Application adequacy tests constrain what semantic
capability the resulting World must provide.

The sealed World and generated receipt expose what
was actually produced and how.
```

```text
Questions define demand.
Construction code constructs.
Tests define adequacy.
The sealed World explains itself.
```

`PURPOSE.md` remains in the fixture as historical rationale and human-readable
context. Tests do not treat its wording as the decisive adequacy criterion.

## Normative construction inputs

1. selected evidence
2. generated governed questions / obligations
3. `construction.py` and helpers
4. generic integrity/admission rules
5. executable adequacy tests

## Existing tests classified

`CONSTRUCTION_INTEGRITY`

- `test_design_contract_rejects_unlisted_semantic_decisions`
- `test_design_contract_keeps_nonsemantic_world_facts_source_grounded`
- `test_resolution_failure_preserves_previous_sealed_world`
- `test_adjudication_must_reference_an_existing_candidate`
- constructor-claimed authority cannot create sufficient evidence
- unauthorized adjudication does not break conflict
- selected law source / unselected source / adoption-required governance tests

`CONSTRUCTION_ADEQUACY`

- generated obligations are published and have an inspectable resolution state
- availability may resolve; priority and goal-support may remain unresolved
- read-surface joins of question → candidate → warrant / grounding
- governed obligations remain readable without Purpose
- law/structure changes change the obligation set
- evidence-authority unbinding changes resolution without erasing the question
- `tests/test_design_checkout_adequacy.py` (explicit adequacy invariant)

`FIXTURE_GOLDEN_ASSERTION`

- exact `DESIGN_REFERENTS` set
- exact `relative_prominence` / `remains_available_during` / `supports` rows
- exact contract/law/evidence identity strings
- exact structural node ids and parser kind
- exact obligation count `3` in several older tests

Golden assertions remain as useful regressions. They are not the adequacy
contract.

## Adequacy invariant

For every applicable `GeneratedObligation` produced by the adopted checkout
governance law over the current structure, the sealed World must account for
that obligation, inspectably `RESOLVED` (selected commitment and warrant) or
`UNRESOLVED` (machine-readable reason).

`ADEQUATE != COMPLETE SEMANTIC KNOWLEDGE`. Honest unresolvedness is adequate.

## Raw schema versus stable consumer surfaces

`RAW ONTOLOGY SCHEMA` (`relative_prominence`, `supports`, SQL tables) is
inspectable and may evolve with construction. It is not automatically a
compatibility API.

Current surfaces that are already compatibility-sensitive for this profile:

- governed obligations / selected-obligation read
- resolutions and candidate assessments
- assertion inspection, warrant, grounding, construction origin
- schema inspection (roles/types/mode, not exact relation names)
- governance identity and law provenance
- evidence/adjudication authority identity
- structure inspection
- construction receipt

Do not assume raw relation names are stable unless a consumer already depends
on them. The golden profile tests do; the adequacy tests do not.

## Construction receipt

Generated sidecar: `world/world.construction-receipt.json`

```text
contract            world_construction_receipt/v0
entrypoint          construction.py
source_digest       sha256 of that file
runtime_world_id    World runtime id (currently v0)
contract_identity   admitted Contract identity
```

## Claim-level material support

Source standing (`APPROVED_REQUIREMENT` on `file://checkout-requirements.md`)
is not claim support. The availability candidate records a reconstructible
Markdown line range (`lines:3-6`) plus a content digest. Deterministic
maintenance reproduces that region from the current file:

```text
PRESERVED | CHANGED | MISSING | UNKNOWN
```

Unrelated edits outside the range keep support. An extra space inside the
range is `CHANGED` under this exact-text contract; the experiment does not
treat whitespace as semantically inert. Wording change and removal also
invalidate automatic reuse. The sealed historical resolution may remain
`RESOLVED`; `current_resolution(..., source_root=...)` reports current
sufficiency. Rebuild after a source change is new construction, not automatic
reuse of the old basis.

Inspection: `claim_support(assertion_id, source_root=...)` separates authority
bindings from recorded/current material support. Construction receipt remains
the constructor identity, not the claim evidence basis.

See `tests/test_design_checkout_claim_support.py`.
