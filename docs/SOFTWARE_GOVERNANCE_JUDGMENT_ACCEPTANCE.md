# Software Governance Judgment v0 acceptance record

Date: 2026-09-24. Specification:
[judgment contract](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md).

This record accepts Judgment v0 as an application layer over a sealed
[Construction v0](SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md) World.
It does not accept investigation, case expansion, change processing,
retrieval, maintenance, promotion, write-back, decision rights, execution,
or model-backed judgment. Investigation v0 is accepted separately in
[SOFTWARE_GOVERNANCE_INVESTIGATION_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_INVESTIGATION_ACCEPTANCE.md)
and is not part of this judgment baseline.

```text
SEALED CONSTRUCTION WORLD
        ↓
verified bounded case
        ↓
profile-owned judgment evaluator
        ↓
judgment artifact
        ↓
fresh-consumer reads
```

Judgment does not mutate the Construction World. Findings stay in the
artifact.

## Capability

`software_governance_judgment/v0`, implemented by
`ontology_author.software_governance.judgment`.

The generic package assembles a bounded case from a sealed World, verifies
each citation against that World, and reads a JSON artifact. It does not
decide applicability, a program finding, or conformance. Those decisions
belong to the profile evaluator that the caller invokes.

There is no evaluator registry, policy language, case database, workflow
engine, persistence abstraction, or promotion framework.

## Dependency

Judgment consumes a sealed Software Governance Construction v0 World.
Construction v0 stays the construction baseline. This acceptance does not
reopen it and does not change Core.

Assertion ids are external citations. `RoleType` has no `ASSERTION` value.
The case cites the id the sealed World already uses for a tuple and checks
that id, the values, and the support against that World.

## Frozen generic vocabulary

Applicability:

```text
APPLIES
DOES_NOT_APPLY
UNKNOWN
```

Program finding:

```text
ESTABLISHED
UNRESOLVED
```

Conformance, only when applicability is `APPLIES`:

```text
CONFORMS
CONFLICTS
UNKNOWN
```

`DOES_NOT_APPLY` and applicability `UNKNOWN` leave conformance absent.
`UNKNOWN` is not `CONFLICTS`. `NOT_APPLICABLE` is not a conformance value.
There is no generic boolean truth field and no `context_sufficiency` field.

A context request, when one is recorded, uses:

```text
gap: construction | judgment
proposition
subject
need
property
availability: ABSENT
```

The needs this version records are `established_binding`,
`mechanical_target_resolution`, and `subject_property`. They name missing
information. They are not a closed vocabulary for later investigation, and
a request is not an instruction to search a repository.

## Profile evaluators

Both profiles use the same generic package. Each evaluator records:

```text
method id
method version
reproducible implementation fingerprint
explicit rule parameters
```

The fingerprint is the sha256 of a canonical JSON record of the method id,
version, rule parameters, and the source of the functions defined in the
evaluator module. It does not include a filesystem path, a timestamp, or
environment-dependent formatting. The rule parameters are copied into
`method.rule`. They are not hidden constants.

| Profile | Module | Method | Positive applicability | Positive exclusion | Conformance |
| --- | --- | --- | --- | --- | --- |
| Mail | `profiles/software_governance_v0/judge.py` | `mail.outbound_mail_passes` `v0` | established binding and subject kind `call_site` | subject kind `callable`, `excludes_kind = callable` | established target compared with `notificationGatewaySend` |
| Config | `profiles/software_governance_config_v0/judge.py` | `config.customer_export_route` `v0` | established binding and subject kind `config:route` | handler other than `CustomerExport` under `required_handler = CustomerExport` | established path compared with `/customers/export` |

The generic package does not contain these terms and does not name a
Program Spine relation. It reconstructs observation text through the
existing evidence adapters. That reconstruction is not a spine schema.

## Case integrity

A case is not the World. It identifies the case, the judgment question, the
sealed World id, revision, and address, the selected proposition ids, the
selected SoftwareSubject ids, the relations inspected, and the cited
assertions.

Each citation is:

```text
assertion_id
relation
values
support
support_fingerprint
```

`support` keeps the warrant bases, construction origins, construction
methods, and reconstructed observation text required to inspect the
citation. Referent labels may be present. They are display text and are
not part of verification.

The verifier rejects:

- changed relation values
- changed reconstructed evidence
- changed construction origin
- changed construction method
- a removed grounding observation
- an invented grounding observation

A label-only change does not fail verification. There is no tuple-only
digest.

## Rule basis

Applicability `APPLIES` cites the established binding and the subject of
the ruled kind. An established binding is evidence used by applicability.
It is not itself applicability.

`DOES_NOT_APPLY` requires a positive exclusion in the case and in the
recorded rule. Failure to prove `APPLIES` is not `DOES_NOT_APPLY`.
Incomplete binding coverage is not a negative. The retained control is:
same generally relevant subject kind, no binding, coverage `INCOMPLETE`,
no explicit exclusion fact, applicability `UNKNOWN`, conformance absent,
no request.

## Findings and conformance

A program finding is separate from the raw producer assertion, the
governance proposition, applicability, and conformance. It records the
relevant value or status and the assertion ids whose support it used.
Findings are not written back into the Construction World.

```text
APPLIES + established sufficient finding
    → the profile may conclude CONFORMS or CONFLICTS

APPLIES + unresolved, non-unique, or missing required finding
    → UNKNOWN

DOES_NOT_APPLY
    → no conformance result

applicability UNKNOWN
    → no conformance result
```

## Four uncertainty classes

| Class | What the case shows | Result |
| --- | --- | --- |
| Missing judgment context | A fact the evaluator requires is absent from the case. The config acceptance omits `config_route` while the binding is present. | Applicability `APPLIES`. Conformance `UNKNOWN`. Judgment request, need `subject_property`, property `path`, availability `ABSENT`. |
| Construction gap | Candidate rows, an unresolved governance question, and no established `governance_binding`. Tested for the approved-mailer proposition and the status-route proposition. | Applicability `UNKNOWN`. Conformance absent. Construction request, need `established_binding`. No invented subject winner. |
| Mechanical indeterminacy | The producer supplied `MULTIPLE_CANDIDATES` and the candidate rows are in the case. | Finding `UNRESOLVED`. Conformance `UNKNOWN`. No request. |
| Semantic unknown | The available facts do not license either semantic conclusion. The retained control is an unbound subject of the relevant kind under incomplete coverage and no exclusion fact. | Applicability `UNKNOWN`. Conformance absent. No request. No invented negative. |

## Artifact and reads

The artifact is JSON outside the sealed World and outside the World
publication directory. After judgment, `world.sqlite` is byte-for-byte
unchanged.

```text
case identity
World id and revision
method record
applicability and its basis
program findings and their basis
conformance and its basis, or absent
context requests
```

The artifact has no chain-of-thought, decision right, execution result,
promotion state, or write-back state. It is not a World assertion.

`consumer_reads` answers, without SQL:

```text
What proposition was judged?
What software subject was judged?
Which sealed World and revision did this depend on?
Why was applicability APPLIES, DOES_NOT_APPLY, or UNKNOWN?
What program finding was established or left unresolved?
Which exact assertions and support paths justify it?
What conformance conclusion followed?
What remains unknown?
What bounded information was requested?
What exact judgment method, version, and rule parameters were used?
```

## Tests

Judgment v0 acceptance, 12 tests:

```sh
uv run --extra dev pytest -q tests/test_software_governance_judgment.py
```

| Suite | Tests |
| --- | --- |
| `tests/test_software_governance_judgment.py` | 12 |

The file exercises both profiles through the generic package: matching and
conflicting mail targets; `MULTIPLE_CANDIDATES`; callable exclusion;
unbound call site under incomplete coverage; matching and conflicting
route paths; omitted route property; handler exclusion; unbound route
under incomplete coverage; construction gaps for both families; six
citation mutations and a label-only change; unchanged `world.sqlite`;
fresh-consumer reads; and the architectural import and vocabulary bans.

Construction v0 acceptance remains the separate 30-test suite named in
[SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md).
The repository default gate in `pytest.ini` remains the Core list. This
file is application acceptance. It is not a claim that Judgment v0 is part
of Core.

Sealed worlds for these tests are built by
`tests/software_governance_judgment_fixtures.py`. That helper is acceptance
support. It is not a second judgment implementation.

## Architectural boundaries

- `ontology_author.software_governance.judgment` imports no profile module.
- It names no mail vocabulary and no config vocabulary.
- It names no Program Spine relation.
- Profile evaluator semantics stay in the two `judge.py` modules.
- Judgment does not mutate a sealed World.
- Citations fail closed under all six material mutation controls.
- Labels are display-only.
- The artifact does not become a World assertion.
- Production judgment code does not import historical `governance`,
  `authority`, `semantic_binding`, or `design_checkout`, and it does not
  depend on a GovernanceCase or checkout schema.
- The world layer still must not import `ontology_author.software_governance`,
  which includes this package.

## Experiment disposition

The Judgment v0 experiment was productionized. Duplicate experiment tests
were not kept.

| Former location | Disposition |
| --- | --- |
| `tests/judgment_v0_experiment/generic.py` | Productionized into `ontology_author/software_governance/judgment/`. Removed as redundant. |
| `tests/judgment_v0_experiment/mail.py` | Productionized into `profiles/software_governance_v0/judge.py`. Removed as redundant. |
| `tests/judgment_v0_experiment/config.py` | Productionized into `profiles/software_governance_config_v0/judge.py`. Removed as redundant. |
| `tests/test_software_governance_judgment_experiment.py` | Replaced by `tests/test_software_governance_judgment.py`. Removed as redundant. |
| `tests/judgment_v0_experiment/fixtures.py` | Moved to `tests/software_governance_judgment_fixtures.py`. Acceptance fixture support. |

The earlier construction experiments remain historical and excluded from
the default gate, as recorded in the construction acceptance. This pass
did not delete them.

## Explicit non-guarantees

Judgment v0 does not establish:

```text
autonomous investigation
case expansion
change impact
affected-governance retrieval
maintenance
cross-snapshot continuity
promotion
write-back
decision rights
execution
model-backed judgment
```

It also does not establish a bound call site with no resolution row as a
tested fixture. The mail evaluator can request `mechanical_target_resolution`
when that row is absent. No sealed acceptance world omits it. A program
finding that is not a value of an included mechanical tuple, a
multi-proposition rollup, and a profile rule stored as a construction-world
relation are also outside this version.
