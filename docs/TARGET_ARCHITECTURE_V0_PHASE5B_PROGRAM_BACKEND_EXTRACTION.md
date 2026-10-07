# Target Architecture v0 — Phase 5B: ProgramBackend extraction

Status: corrected draft for one final Phase 5B closure review. PR #6 started
at merged Phase 5A `8f296bbc`; the reviewed pre-correction head was
`1a152b71`. Phase 5A R1–R7 and its behavioral cases are unchanged. No Glean
inspection/integration, kernel change, publication redesign, or merge occurs.

The extraction remains:

```text
AuthorityConstructor -> ProgramBackend -> native adapter -> native Program Spine
```

The adversarial review confirmed real constructor decoupling, but rejected
mandatory whole-universe/family enumeration, six native capability spellings,
string-valued evidence, and two public state representations. It also found
nonmember evidence access and adapter regressions hidden by test qualification.
This correction changes those demonstrated issues without reopening Phase 5A.

## A. Forcing consumer and deletion

The forcing production path is `construct_config_binding` through
`AuthorityConstructor` and `construct_authority_world`, exercised by the
Phase 4 W1/W2 vertical slice. The caller supplies E explicitly. Binding now
uses `constructor.is_program_entity(E)`, not enumeration followed by membership.
Filtered/unfiltered `program_entities()` remains optional discovery behavior.

Constructor program-content reads still use only ProgramBackend. Removed native
knowledge remains removed: program membership/kind tables, label/descriptor
joins, snapshot grounding, relation storage and snapshot filters, the entity
snapshot accessor, and its redundant cross-snapshot check. Generic candidate
World writes and semantic referent integrity reads remain application work.

Two durable migration regressions discriminate the source of decisions:

- Candidate has no program rows: backend reads still work.
- Candidate has correct native rows: differing backend membership, kind,
  context, invocation, and resolution answers control the constructor/default
  warrant. Native candidate rows do not repair backend answers.

## B. Corrected production API choice

`ontology_author/program_backend/__init__.py` has seven core reader operations
plus a convenient composed verification operation. Entity tokens are opaque
hashable local values; native tokens remain strings, while the lazy fake uses
integers. Qualification is the opened handle plus token, not token spelling.

```text
snapshot() -> str                         one observed-state token
is_member(E) -> bool                      exact local membership
kind(E) -> str | None                     declared mechanical kind
containment(E) -> parent/child rows       E's ancestor edges only
capability(family) -> Capability          requested-family qualification
observations(E) -> tuple[object, ...]     opaque backend-owned evidence handles
reconstruct(handle) -> (material, verified)
verify() -> tuple[str, ...]               convenient composed guarantee checks

optional invocations(C) -> call_site/target rows
optional resolutions(S) -> subject/status/capability rows
optional discover(label, kind, descriptor_contains) -> local candidates
close() and context-manager protocol
```

There is no `members()`, `snapshot_id()`, or capability inventory operation.
No core relation read dumps a full family. Fixed role names preserve the
Phase 5A entity/literal distinction without a graph engine or query language.
Parent/child/call_site/target/subject values are local entity tokens;
resolution status and capability attribution are text.

`containment(E)` returns relevant ancestor edges, sufficient for the demonstrated
chain and preserving parent/child direction. The constructor still performs its
ordinary ancestor walk. Its default warrant requests outgoing invocations for
one endpoint and resolution outcomes for that subject. The optional
`call_site_invoking(label)` compatibility helper discovers candidate sites and
queries each site; reverse whole-family enumeration is not added to core.

Invocation/resolution production is optional. The base implementations return
empty results with NOT_PRODUCED; a backend declaring production without
implementing the read fails explicitly. A backend can implement membership,
kind, containment, and evidence without extracting calls. Qualified empty rows
never imply unsupported analysis was complete.

## C. Capability normalization

`Capability` remains one frozen `(status, scope, basis, gaps)` record. The
normalized states have demonstrated consequences:

| Production state | Meaning |
| --- | --- |
| COMPLETE | Supported complete within its declared scope/basis, not universal program behavior |
| INCOMPLETE | Supported but incomplete/partial, or completeness uncertain; no exhaustive absence conclusion |
| NOT_PRODUCED | Family not produced; no absence conclusion |

The native mapping is explicit:

| Native receipt state | Production state | Preserved qualification |
| --- | --- | --- |
| COMPLETE | COMPLETE | Original scope, basis, known gaps |
| STATIC_COMPLETE | COMPLETE | Original static scope/basis plus native qualification in basis |
| INCOMPLETE | INCOMPLETE | Original scope, basis, known gaps |
| PARTIAL | INCOMPLETE | Original metadata plus native qualification in basis |
| UNKNOWN | INCOMPLETE | Original metadata plus native qualification in basis |
| NOT_PRODUCED | NOT_PRODUCED | Original metadata; never closure |

Native spellings in explanatory basis text are adapter metadata, not required
enum values for another backend. Static coverage of resolution outcomes is not
proof that unresolved sites invoke nobody. Resolution outcomes retain their
own RESOLVED/UNRESOLVED semantics.

`capability(family)` maps containment to `spine.code_structure` and invocation /
resolution to `spine.calls`; other native ids are optional native vocabulary.
The native component-usage NOT_PRODUCED declaration is a test witness, not a
required core family. A missing/unreadable receipt or omitted requested native
declaration fails qualification. Mechanical content reads may still work with
no receipt, but cannot establish capability-qualified completeness.

The migrated constructor does not infer exhaustive absence or consult the
capability operation. Its existing empty-warrant behavior is preserved; it is
not claimed to persist an additional capability-qualified negative conclusion.

## D. Evidence and source revision ownership

The boundary passes opaque `object` handles unchanged into `reconstruct`.
It requires neither a mapping nor string-valued metadata, a source-coordinate
format, an evidence class, paths, digest algorithms, nor descriptor objects.
Native handles remain dictionaries; the native adapter alone validates and
interprets their provider/handle/revision/location fields.

Native observations check membership before grounding lookup. The snapshot
referent and arbitrary program-looking nonmembers return no observations.
Member observations reconstruct from retained digest-checked program inputs.
Native reconstruction verifies `source_revision` against the opened native
snapshot's `source_state`, validates the locator, and reads retained bytes;
wrong revision, damaged retention, or live-source substitution cannot verify.
Thus source revision qualification lives in the opaque evidence handle plus
backend reconstruction verification, not a universal descriptor accessor.

`(material, verified)` is the retained simple API choice. Native failure returns
`("", False)`; a valid empty extent returns `("", True)`. Consumers must check
verification. Suppressing all unverified material is not claimed as a universal
security primitive or evidence class requirement.

## E. One state token; native basis adaptation

`snapshot()` now returns the native recorded snapshot id (grounding extra,
legacy referent fallback if no recorded id), not a second public referent token.
The native opener rejects absent source-state qualification and disagreement
between the recorded state and an available receipt. Direct tests compare the
state with the producer manifest, not the constructor or another backend getter.

The constructor uses this single token for warrant/receipt observed-state
qualification. The native lifecycle separately supplies `candidate_snapshot_ref`
from its already-open native baseline for the existing copied-artifact basis and
validation fields. That is native publication adaptation, not another backend
state obligation. Existing native basis/receipt layouts and values are retained.

Exact occurrence identity is different from observed-state qualification.
Native `PublicationRef`, exact address opening, and reference verification live
at composition. Copies may share local tokens and state tokens while retaining
distinct exact references. Direct raw-token membership in an equivalent copy
is true; a qualified entity from the original is not the copy's qualified
entity. A future non-filesystem factory can supply a different exact reference
and the same scoped reader behavior without a universal ProgramOccurrenceRef.

## F. What production conformance actually covers

The 22 Phase 5A functions are reused without edits. `ProductionRead` remains a
test projection: optional native discovery aggregates scoped reads when old
test views request an unscoped family. This does not require production core
enumeration. Native receipt descriptors, labels/boundaries, occurrence envelopes,
and comparison remain explicitly test-side/native composition.

| Requirement | ProgramBackend-owned behavior | Surrounding composition / fixture |
| --- | --- | --- |
| R1 exact occurrence | Scoped reads from the opened handle | Exact reference/factory, serialization, PublicationRef qualification |
| R2 observed state | One state token; evidence revision verified on reconstruction; requested scope/basis | Native descriptor inputs/losses/boundary; copied-artifact snapshot referent adaptation |
| R3 membership/kind | Direct local membership and mechanical kind; nonmember reads/evidence empty | Qualified-entity envelope rejects contradictory occurrence/state context |
| R4 context/facts | Scoped ancestor/site/subject reads with fixed roles and capability access | Test role-schema projection; optional discovery aggregation for old global test views |
| R5 evidence | Member-only opaque handles, retained reconstruction, explicit verification failure | Native producer supplies evidence; test fixture damages retained inputs |
| R6 honesty | Requested-family status/scope/basis/gaps; optional production distinguished from complete-empty | Native test witness family, optional descriptor/boundary disclosures |
| R7 history/verification | Stable reopened scoped facts, capabilities, observations; reconstruction and verify | Exact reopening/retention, publication qualification, fingerprints, optional native comparison |

These are conformance of the reader plus its declared composition, not a claim
that the ABC wholly implements R1–R7. Direct adapter tests bypass inherited
`NativeRead.inspect` and check foreign/fabricated tokens, equivalent-copy local
membership, producer-recorded state, invalid state qualification, nonmember
evidence, historical scoped reads, requested capability, wrong revision,
retained corruption, and missing-receipt qualification.

Eight durable dishonest-adapter controls require behavioral assertions to
reject occurrence-insensitive membership, incorrect state identity, nonmember
evidence leakage, signature-as-module ancestor, unsupported-as-complete,
latest substitution, ignored revision, and mutable-live evidence fallback.

## G. Alternative-backend falsifier

`tests/program_backend_lazy_fixture.py` supplies exact non-filesystem occurrence
handles, integer local IDs, keyed-only member/context indexes, per-family
qualification, and structured evidence containing integer revisions, nested
source ids, extents, and binary content handles. Index enumeration raises.
There is no discovery or comparison. Both the core-only version (default
NOT_PRODUCED call reads) and optional produced scoped-call version pass the
core tests. Closure verification checks its declared retained source directly;
it does not enumerate a repository. This proves representational freedom,
not real Glean conformance, scalability, or a new production implementation.

## H. Mandatory deletion audit

| Remaining production method/type | Demonstrated forcing consumer / behavior | Further scope/fold? | Alternative backend |
| --- | --- | --- | --- |
| ProgramBackend | Constructor mechanical read dependency | Keep handle-scoped boundary; no producer/export API | Natural opened query handle |
| snapshot | Warrant/basis observed-state qualification | Second accessor removed | One stable state token |
| is_member | Explicit config selection, endpoints, warrant/relevance checks | Already one entity; enumeration deleted | Keyed membership |
| kind | Selected-entity relevance defaults | Already one entity; no universal kind ontology | Declared adequate category |
| containment | Constructor ancestor context | Already E's ancestors; roles cannot fold away without losing direction | Scoped ancestor query |
| invocations | Default warrant/invoked_targets; optional call-site helper | Optional production; site-scoped | Scoped outgoing query or NOT_PRODUCED |
| resolutions | Default warrant subject outcomes | Optional production; subject-scoped | Scoped outcome query or NOT_PRODUCED |
| capability | R4/R6 qualification of requested facts | Already one family; inventory deleted | Per-family declaration |
| Capability | R6 status/scope/basis/gaps | One compact record; no receipt hierarchy | Natural metadata |
| CapabilityStatus | Complete/incomplete/not-produced falsifiers | Six native states folded to three | No native spellings required |
| observations | R5 selected-entity evidence | Already one member; object handle | Native structured/opaque handle |
| reconstruct | R5 exact qualified material or failure | Single handle; no coordinates exposed | Provider-owned reconstruction |
| verify | R7 mechanical verification, production conformance | Convenient composed operation retained; not forced by constructor; no subsystem | Provider closure/consistency checks |
| discover | Existing program_entities/call_site_invoking compatibility | Optional extension; descriptor_contains is native-compatible only | May refuse entirely |
| close / context manager | Lifecycle owns an opened resource | No-op close allowed; no new lifecycle objects | Natural or no-op |
| BackendError | Common native adapter failure handling | Convenience superclass, not an epistemic requirement | Ordinary explicit failure |
| NotAProgramOccurrence | Source-only lifecycle differs from malformed program state | Distinction cannot collapse into generic empty program | Factory-specific absence signal |
| OccurrenceQualificationError | Malformed/missing requested qualification must fail | Named subclass retained for current compatibility; no extra recovery policy | Ordinary qualification failure |
| OptionalUnsupported | Discovery/read service refusal differs from successful empty lookup | Optional extension/default-read signaling only | Explicit refusal |
| NativeProgramBackend / __init__ | Production native implementation and opening gates | Native caches/eagerness remain local, not contract | Different adapter/factory |
| open_native_occurrence | Native lifecycle exact opener | Filesystem reference deliberately localized | Different exact-reference factory |
| _rows / _recorded_snapshot_id / _project_capability | Native tables, grounding, receipt normalization | Private native implementation, no universal obligation | Not required |
| candidate_snapshot_ref | Existing native copied-artifact basis/validation | Composition input; not reader state/accessor | Different basis adapter later |

## I. Remaining extraction pressure

The native lifecycle still takes paths, opens `world.sqlite`, records
PublicationRef bases, clones the full program bundle, and admits/verifies the
candidate's native program rows and retained blobs. Other program readers,
comparison, maintenance, and native relevance relation vocabulary are not
migrated. These are explicit composition/application dependencies, not fallback
program-content reads in AuthorityConstructor. A fully non-native end-to-end
publication needs separate basis/retention/validation adaptation later.

The future simplification remains semantic publication plus an exact external
program occurrence/evidence basis, rather than necessarily cloning a full
Program World. No such publication change occurs here. The reader now requires
neither universe nor full relation enumeration, making that future deletion
possible without satisfying a new export obligation.

## J. Validation and verdict

Correction validation (counts overlap; this is not the entire historical suite):

| Check | Result |
| --- | --- |
| Production backend conformance | 45 passed: unchanged 22-case replay, 2 original migration cases, 21 corrective/direct/fake/mutant cases |
| Phase 5A behavioral conformance | 22 passed, file unchanged |
| Phase 4 vertical slice | 17 passed |
| Combined reader / Phase 5A / Phase 4 command | 84 passed |
| Authority/config, native spine/comparison, program/evidence regressions below | 225 passed |
| Default gate | 203 passed, no skips |
| Core acceptance separately | 18 passed |
| Honest lazy core-only / produced-call variants | Both passed, with enumeration unavailable and discovery refused |
| Dishonest adapter controls | All 8 rejected by direct behavioral assertions |
| Frontend build / package build / diff whitespace | PASS; frontend build produced no tracked asset diff |

Reproduction:

```sh
uv sync --locked --extra dev
npm ci --prefix frontend
uv run --extra dev pytest -q tests/test_program_backend_production.py \
  tests/test_program_backend_conformance.py tests/test_phase4_vertical_slice.py
uv run --extra dev pytest -q tests/test_authority_construction.py \
  tests/test_authority_maintenance.py tests/test_config_routes_phase1.py \
  tests/test_config_routes_phase2.py tests/test_config_routes_phase3.py \
  tests/test_phase3_construction_boundary.py tests/test_typescript_program_spine.py \
  tests/test_program_spine_comparison.py tests/test_phase1_program_observation_conformance.py \
  tests/test_phase1_program_capture_conformance.py tests/test_phase1_evidence_conformance.py
uv run --extra dev pytest
uv run --extra dev pytest -q tests/test_core_v1_acceptance.py
npm run build --prefix frontend
uv build
git diff --check
```

Implementation verdict supported by this corrected surface, direct negative
controls, and the honest alternative fixture:

```text
YES — MINIMAL PRODUCTION PROGRAMBACKEND EXTRACTED;
NATIVE BACKEND CONFORMS;
READY FOR GLEAN CONFORMANCE
```

This is readiness to test another backend, not a claim about Glean's architecture
or conformance. The PR remains draft and unmerged for one final independent
Phase 5B closure review. Native end-to-end composition debt in §I remains.
