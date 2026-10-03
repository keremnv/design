# Software Governance Investigation v0 acceptance record

Date: 2026-09-24. Specification:
[investigation contract](SOFTWARE_GOVERNANCE_INVESTIGATION_CONTRACT.md).

This record accepts Investigation v0 as an application layer around a
[Judgment v0](SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md) case. It does not
accept proposal admission, publication, write-back, change-impact retrieval,
maintenance, decision rights, or execution.

```text
SEALED CONSTRUCTION WORLD
        ↓
JUDGMENT CASE C0
        ↓
JUDGMENT J0
        ↓
investigation question
        ↓
CASE_EXPANDED | PROPOSAL | UNRESOLVED
        ↓
when expanded: JUDGMENT J1 of ordinary case C1
```

Judgment stays bounded. Investigation does not rewrite J0 or the sealed World.

## Capability

`software_governance_investigation/v0`, implemented by
`ontology_author.software_governance.investigation`.

The generic package builds a question, expands a case inside one sealed
publication, records a receipt, and records a proposal sidecar. It does not
decide what is worth finding. The config profile investigator does that for
route worlds. There is no investigator registry, capability registry, planner,
or admission service.

## Dependency

Investigation consumes an ordinary Judgment v0 case and the sealed
Construction v0 publication that case names. Expansion calls Judgment
`assemble_case` and `verify_case`. It does not reimplement citation checks.
C1 is an ordinary Judgment case: same fields as C0, no investigation lineage.

Judgment does not import Investigation. Construction does not import
Investigation. The world layer does not import this application.

## Question

```text
question_id
question
purpose
proposition
subject
origin
    case_id
    kind: judgment_request | open
    request?          optional copy of a Judgment request
structured_need?
    need
    property
```

`structured_need` is optional. An open question is valid. The question text
is not a World assertion.

## Outcomes

```text
CASE_EXPANDED
PROPOSAL
UNRESOLVED
```

`CASE_EXPANDED` means verified citations were added. It does not mean the
question was answered, the judgment changed, a construction gap closed, or
conformance became known.

```text
assertion already in this publication
    → eligible for verified case expansion

useful discovery with no assertion in this publication
    → proposal sidecar

neither
    → UNRESOLVED
```

Investigator confidence does not change these categories. Raw source text,
manifestation text, a hypothesis, an inferred tuple, or an assertion from
another publication does not become a case citation.

## Same-publication expansion

```text
same publication address
same world id
same revision
same selected proposition
same selected SoftwareSubject
citations(C1) ⊇ citations(C0)
```

These fixtures reuse the producer world id `config-routes` across
publications. Expansion binds the publication address stored on the case,
then the world id and revision, and rejects another directory before copying
a citation. An assertion from that other publication fails Judgment
verification even when the world id, the subject label, and the relation
shape match. v0 adds no cross-revision correspondence and no citation removal.

## Autonomy

A copied Judgment request is one missing fact, not a ceiling. The config
investigator may inspect every mechanical relation of the subject. Relations
it inspected, and citations the case includes, are not judgment support
unless a later judgment names those assertion ids.

The retained control: a path request still leaves `config_member` in the
case, and the conforming judgment does not cite that membership assertion.

## Proposal

```text
proposal_id
originating_case_id
originating_question_id
epistemic_class: mechanical | semantic | source/evidence | other
payload                  profile-owned
basis                    reconstructible source basis, profile-owned
method                   method id and capability
reason                   why this is not a citation in this case
```

No assertion id. The payload is not a universal relation schema. A proposal
is not World knowledge, construction admission, publication, a case-local
finding, or an existing World assertion.

The config profile treats source keys `id`, `path`, and `handler` as fields
its producer publishes. Another key that the question asks about, and that
reconstructed manifestation text contains, becomes a mechanical proposal.
The generic package does not know those keys.

## Receipt

Lineage stays on the receipt:

```text
question_id
parent_case_id
world_id
revision
world_address
method
    id
    capabilities used
outcome
resulting_case_id      only for CASE_EXPANDED
added_assertion_ids
proposal_id            only for PROPOSAL
inspected_relations
```

No chain-of-thought and no rejected-hypothesis log. `inspected_relations`
and the capability list are exploration provenance, not support. v0 does not
add a Judgment-style implementation fingerprint. Method id plus the supplied
capabilities are enough for the retrieval behavior this version demonstrates.
A later method that makes semantic selection choices may need more
provenance. This version does not define that record.

## Tests

Investigation v0 acceptance, 8 tests:

```sh
uv run --extra dev pytest -q tests/test_software_governance_investigation.py
```

| Suite | Tests |
| --- | --- |
| `tests/test_software_governance_investigation.py` | 8 |

The file covers same-publication expansion to `CONFORMS`, broader inspection
than the path request, an unasserted `approval` field kept as a proposal,
an open question with no `structured_need`, an unresolved billing-review
question, cross-publication rejection, a construction gap that survives
expansion, and the import and vocabulary boundaries.

Sealed worlds for these tests are built by
`tests/software_governance_investigation_fixtures.py`. That helper is
acceptance support. It is not a second investigation implementation.

Judgment v0 acceptance remains the separate 12-test suite. Construction v0
acceptance remains the separate 30-test suite. The repository default gate
in `pytest.ini` remains the Core list. This file is application acceptance.
It is not a claim that Investigation v0 is part of Core.

## Architectural boundaries

- The generic package imports no profile module.
- It names no mail vocabulary, no config vocabulary, and no Program Spine relation.
- It does not import historical `governance`, `authority`, `semantic_binding`, or `design_checkout`.
- It does not mutate a sealed World. Acceptance checks `world.sqlite` bytes.
- Judgment, construction, and the world layer do not import it.
- C1 has the same fields as an ordinary Judgment case.
- A proposal has no assertion id.
- Same-publication citation checks are `verify_case`.

## Experiment disposition

The Investigation v0 experiment was productionized. Duplicate experiment
tests were not kept.

| Former location | Disposition |
| --- | --- |
| `tests/investigation_v0_experiment/generic.py` | Productionized into `ontology_author/software_governance/investigation/`. Removed as redundant. |
| `tests/investigation_v0_experiment/config.py` | Productionized into `profiles/software_governance_config_v0/investigate.py`. Removed as redundant. |
| `tests/test_software_governance_investigation_experiment.py` | Replaced by `tests/test_software_governance_investigation.py`. Removed as redundant. |
| `tests/investigation_v0_experiment/fixtures.py` | Moved to `tests/software_governance_investigation_fixtures.py`. Acceptance fixture support. |

## Explicit non-guarantees

Investigation v0 does not establish:

```text
proposal admission
publication
World write-back
change-impact retrieval
maintenance
cross-World cases
cross-snapshot continuity
decision rights
execution
agent permission architecture
generic planning
tool registry
model-backed investigation guarantees
```

Discovery, proposal, admission, and publication stay distinct. This version
exercises discovery of an existing assertion and a proposal for a field the
producer did not assert. It stops before admission and publication.
