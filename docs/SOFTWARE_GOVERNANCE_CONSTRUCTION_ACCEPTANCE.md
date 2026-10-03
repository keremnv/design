# Software Governance Construction v0 acceptance record

Date: 2026-09-23. Specification:
[construction contract](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md).

This record accepts Construction v0 only. It does not accept judgment,
change processing, retrieval, maintenance, or an agent workflow.

```text
Construction v0 establishes A–C:
software observation consumption
governance knowledge
knowledge ↔ software binding

It does not establish:
judgment
change processing
retrieval
maintenance
agent workflow
```

## Capability

`software_governance_construction/v0`, implemented by
`ontology_author.software_governance`.

From authoritative evidence and a mechanically trustworthy software World,
construction records propositions, established bindings, candidates, explicit
unresolved questions, and a scoped completeness claim, then seals a fresh
address. A fresh consumer reopens that World through `GovernanceView`.

Commands:

```sh
uv run python profiles/software_governance_v0/build.py /path/to/fresh-world
uv run python profiles/software_governance_config_v0/build.py /path/to/fresh-world
```

The output path must not already exist.

## Profiles

Both profiles matter because they use different producers and the same
generic relations.

| Profile | Producer | What it contributes |
| --- | --- | --- |
| [Mail](../profiles/software_governance_v0/README.md) | TypeScript Program Spine | Snapshot-local call-site subjects, mechanical invocation and resolution rows, `source-token-range` manifestations. One call site is bound; a sibling call and another caller of the same target are not. |
| [Config routes](../profiles/software_governance_config_v0/README.md) | Deterministic JSON parse | `config:route` subjects, `config_member` and `config_route` facts, `canonical-json-record` manifestations, no Program Spine tables and no invocation graph. One route is bound; an under-specified sentence stays a candidate pair. |

The generic package does not know either subject vocabulary. Program Spine is
one producer. It is not the interchange schema.

## Producer-neutral boundary

```text
software_subject(subject, snapshot, kind, capability, version)
software_manifestation(subject, scheme, location, capability)    optional
producer-owned mechanical relations and observations
```

`software_subject` recovers snapshot-local identity, kind, producing
capability and version, snapshot membership, and mechanical grounding.
`software_manifestation`, when present, names the scheme, the coordinate,
and the capability, and grounds the bytes from which the content digest is
recovered. A grounded subject with no manifestation row stays valid; the
read reports `NOT_PRODUCED`.

Tested manifestation schemes, not a required vocabulary:

```text
source-token-range
canonical-json-record
```

## Generic durable vocabulary

```text
software_subject
software_manifestation

governance_proposition
governance_binding
governance_candidate
governance_question

governance_completeness
governance_known_gap
```

Producer relation names such as `program_invokes`, `config_route`, and
`config_member` are not in this vocabulary. The generic consumer discovers
mechanical facts that name a subject by ordinary World relations and does
not interpret them.

## Guarantees demonstrated

- A proposition referent is not a semantic subject, a software subject, or an assertion id.
- Proposition evidence and binding correspondence grounding are separate.
- One proposition can bind one subject while other subjects that share an owner, a target, or a document stay unbound.
- An ambiguous correspondence is candidate rows plus an explicit `UNRESOLVED` question, and it does not create `governance_binding`.
- `AMBIGUOUS` and `UNRESOLVED` are not positive endpoint resolutions. `DETERMINISTIC` is not the only positive class the generic validator accepts.
- `SOURCE_EXPLICIT` is a profile support class, not the only one generic validation accepts.
- Semantic interpretation of propositions, bindings, candidates, and questions is `SEMANTIC`.
- Construction-coverage rows in both profiles are `MECHANICAL` because the run only stored the correspondences it was given. The relation names do not force that origin; a semantic coverage claim remains admissible.
- Known gaps are identifier rows. Absence of a binding is not “ungoverned” while coverage is `INCOMPLETE`.
- Local manifestation content, location, and subject identity are distinct. A whole-file digest is not the subject manifestation.
- Mechanical producer facts stay `MECHANICAL`.
- The package does not import historical `authority`, `semantic_binding`, `governance`, or `design_checkout` application packages, and it does not import either profile or the TypeScript producer.

## Intentionally not demonstrated

- Adjudication workflow, GovernanceCase, or a policy engine. Judgment v0 is accepted separately in [SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md) and is not part of this baseline.
- Change processing, diff ingestion, cross-snapshot correspondence, maintenance, affected-binding retrieval, or re-resolution.
- A persistent semantic identity. The cross-replacement experiment remains historical evidence. Neither acceptance profile mints one.
- A universal subject kind, manifestation scheme, or mechanical relation vocabulary.
- A non-content coordinate that cannot be reconstructed as bytes.
- Core SQL derivation completeness as the binding-coverage record.
- User interface.

## Read surface

`open_governance_world` returns a `GovernanceView`. Both sealed profiles
answer through the same methods:

```text
propositions_for_subject
subjects_for_proposition
inspect_governance_proposition
inspect_governance_binding
binding_candidates_for_proposition
local_manifestation_for_subject
mechanical_facts_for_subject
program_relations_for_subject    empty when the producer emitted no spine call rows
completeness
absence_is_negative
```

`program_relations_for_subject` is a convenience for worlds that contain the
spine call relations. It is not a second interchange schema.

## Tests

Construction v0 acceptance, 30 tests:

```sh
uv run --extra dev pytest -q \
  tests/test_software_governance_construction.py \
  tests/test_software_governance_config_profile.py \
  tests/test_architecture_boundaries.py
```

| Suite | Tests |
| --- | --- |
| `tests/test_software_governance_construction.py` | 20 |
| `tests/test_software_governance_config_profile.py` | 7 |
| `tests/test_architecture_boundaries.py` | 3 |

The construction file includes the mail profile. The config file is the
non-spine profile. Architecture boundaries keep the world layer from
importing this application. The repository default gate in `pytest.ini`
remains the Core list. These three files are the application acceptance
suite; they are not a claim that Construction v0 is part of Core.

Historical experiments, retained and excluded from the default gate
(`pytest -m historical` selects them):

| Suite | Tests | Disposition |
| --- | --- | --- |
| `tests/test_manifestation_granularity.py` | 1 | Historical. Token-range versus file digest, and the comparison limits, are encoded in the contract. Not acceptance. |
| `tests/test_semantic_identity_persistence.py` | 1 | Historical. The optional cross-replacement use is encoded in the contract. Not used by either acceptance profile. |
| `tests/test_governance_binding_target.py` | 1 | Historical. Call-site grain for one invocation is encoded in the contract and the mail profile. |
| `tests/test_governance_binding_representation.py` | 5 | Historical. The proposition-referent plus `governance_binding` shape is the frozen representation. |

None of those four files is disposable. None is part of Construction v0
acceptance. No temporary fixture was removed.
