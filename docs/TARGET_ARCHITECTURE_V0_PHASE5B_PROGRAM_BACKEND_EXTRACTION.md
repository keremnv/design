# Target Architecture v0 — Phase 5B: ProgramBackend extraction

Status: draft for review. Phase 5A (merged) derived the minimum
backend-independent mechanical contract forced by the Phase 4 consumers.
Phase 5B extracts the smallest production boundary for that contract,
proves the native Program Spine conforms through a real adapter, and
migrates one end-to-end vertical consumer to it.

Governing question: what is the smallest production boundary that lets a
real Ontology Author consumer depend on the demonstrated mechanical
contract rather than native Program Spine storage details?

```text
before:  semantic consumer -> native spine storage details
after:   semantic consumer -> ProgramBackend -> native adapter -> native spine
```

## A. Merged Phase 5A starting point

Branch `phase5b/program-backend-extraction` starts at merged `main`
`8f296bbc` (Phase 5A squash-merge PR #5). No Phase 5A branch content is
used. R1–R7 are unchanged; the Phase 5A requirements document and its 22
executable conformance cases are the source of truth. No Glean, Code
Explorer, discovery-engine, or Semantic World redesign work is included.

## B. Selected forcing consumer

One real path: `construct_config_binding`
(`ontology_author/config_routes/binding.py`) through
`AuthorityConstructor` (`ontology_author/authority/construction.py`) and
`construct_authority_world` (`ontology_author/authority/lifecycle.py`),
exercised end-to-end by the Phase 4 vertical slice
(`W0 + P1 + E1 -> W1`, `W0 + P2 + E2 -> W2`). `binding.py` itself is
unchanged; its constructor read surface was migrated. No other consumer
was migrated.

## C. Pre-extraction native coupling audit

All program reads below were served from the candidate World, which
`construct_authority_world` seeds as a byte clone of the exact program
baseline. Classification:

| Native knowledge | Used by | Class |
| --- | --- | --- |
| `program_snapshot` row + `program_snapshot` assertion grounding extra (`snapshot_id`) | `_load_snapshot` | required mechanical (R2) |
| `program_entity_kind` enumeration | `program_entities()` unfiltered | required mechanical (R3) |
| `program_entity_kind` kind filter | `program_entities(kind=...)` | required mechanical (R3) |
| `_world_referents` labels | `program_entities(label=...)`, `call_site_invoking` | optional discovery |
| `program_identity_descriptor` | `program_entities(descriptor_contains=...)` | optional discovery |
| `structural_context` rows + hand walk | `structural_context` | required mechanical (R4) |
| `program_invokes` rows | `invoked_targets`, `call_site_invoking`, warrants | optional production (R4/R6) |
| `program_resolution` rows | `_default_warrant` | optional production (R4/R6) |
| `program_entity` membership/snapshot | `_is_program_entity`, `_entity_snapshot`, warrants | required mechanical (R2/R3) |
| `program_entity_kind` single kind | `_entity_kind`, relevance defaults | required mechanical (R3) |
| `ConstructionWorld.open` + `PublicationRef.from_world` + `verify_publication_ref` on the baseline | lifecycle basis recording | required occurrence mechanics (R1/R7); receipt shape stays native |
| whole-bundle byte clone | candidate seeding | retention, kept as-is (producer concern) |
| candidate `program_*` rows in admission validation | `validation.py` warrant/endpoint/scope/snapshot checks | retained-artifact verification, deliberately not migrated (see N) |
| `verify_retained_program_inputs` on the candidate | admission + publication verification | retention verification, kept native |

## D. Minimal production boundary

New package `ontology_author/program_backend/`. The boundary
(`__init__.py`) is one abstract class plus two tiny value types and
errors. No other production types were introduced.

```text
ProgramBackend (ABC, handle scoped to one exact opened occurrence)
  snapshot() -> str                      opaque observed-state token
  snapshot_id() -> str                   opaque recorded state identity
  members() -> tuple[str, ...]           opaque entity tokens
  is_member(entity) -> bool              concrete via members()
  kind(entity) -> str | None             mechanical kind, None if not member
  containment() -> tuple[{parent, child}]
  invocations() -> tuple[{call_site, target}]
  resolutions() -> tuple[{subject, status, capability}]
  capabilities() -> Mapping[str, Capability]
  observations(entity) -> tuple[dict, ...]   opaque qualified observations
  reconstruct(observation) -> (str, bool)    fail-closed retained material
  verify() -> tuple[str, ...]                retained-guarantee violations
  discover(label, kind, descriptor_contains) optional; raises if unsupported
  close() + context-manager protocol
```

`Capability` is a frozen `(status, scope, basis, gaps)` record;
`CapabilityStatus` enumerates the six production states. Errors are
`BackendError` with `NotAProgramOccurrence` (no program plane:
lifecycle maps to source-only mode), `OccurrenceQualificationError`
(malformed plane: fail closed), and `OptionalUnsupported` (optional
refusal). Fact rows are plain dicts keyed by role name; observations are
opaque mappings; both avoid new row/observation classes.

## E. Representation choices deliberately not made

No production `OpenedOccurrence`, `Descriptor`, `EntityView`,
`FactView`, `ProgramCapabilities`, `VerificationOutcome`, or `ProgramRef`
classes: qualification is handle scoping, rows are dicts, capability is
one record, verification is an error tuple, and occurrence addressing for
receipts stays with the native `PublicationRef` record. No universal kind
ontology (one opaque mechanical kind per member), no graph API (one edge
list per demonstrated family), no comparison on the core reader, no core
discovery, no producer/indexing surface, no universal error enum, and no
per-entity state accessor (`snapshot_of` was prototyped, found to have no
demonstrated consumer once handle scoping made the warrant cross-snapshot
check vacuous, and deleted).

## F. Native adapter mapping

`NativeProgramBackend` (`native.py`), opened with
`open_native_occurrence(address)`, projects a sealed native bundle:

| Boundary | Native source |
| --- | --- |
| open gates | `program_snapshot`/`program_entity` row presence; exact legacy messages preserved |
| `snapshot` / `snapshot_id` | snapshot row token; `program_snapshot` assertion grounding extra or token |
| `members` / `is_member` | `program_entity` rows filtered to the governed snapshot |
| `kind` | `program_entity_kind` rows (native kind; identical to identity kind in the current extractor) |
| `containment` / `invocations` / `resolutions` | same-named rows filtered to the snapshot, native order, role keys only |
| `observations` / `reconstruct` | `program_source_observations` / `reconstruct_program_observation`; `(text, status == "OK")` |
| `verify` | `validate_typescript_spine` + `verify_retained_program_inputs` over the bundle manifest |
| `discover` | kind rows + referent labels + identity descriptors |
| `capabilities` | receipt projection (see G), loaded lazily so `open` never depends on it |

Reads are cached at open; the underlying world is read-only. The adapter
invents no semantic information.

## G. Capability/completeness mapping

Neutral families map to native receipt ids exactly as in Phase 5A:
`containment -> spine.code_structure`, `invocation`/`resolution ->
spine.calls`. Each projects `(status, scope, completeness_basis,
known_gaps)`; receipt references, inputs, and losses are never exposed.
Further receipt capabilities are declared under their native ids
(e.g. `spine.component_usage`, which the R6 production case uses as its
honest `NOT_PRODUCED` witness). A missing receipt fails `capabilities()`
closed without affecting `open`; the migrated constructor never consults
capabilities, preserving its row-absence behavior while the boundary now
makes production state inspectable.

## H. Evidence mapping

Observations pass through as opaque dicts; `reconstruct` returns
`(material, verified)` with `("", False)` for every native `FAILED`
(missing/corrupt blob, revision mismatch, bad locator). No paths,
digests, offsets, coordinates, or observation classes cross the
boundary. `verify()` returns the combined native spine + retained-input
violations as plain strings.

## I. Historical identity mapping

Exact occurrence identity is the opened handle: all reads are filtered
to the opened snapshot, and equivalent retained copies are distinct
handles that never share state. `EntityToken != QualifiedEntityOccurrence`
holds: tokens are opaque strings, qualification is the handle. The native
`PublicationRef` remains the occurrence mechanism inside the adapter's
neighborhood (lifecycle basis recording and receipts keep their exact
shapes and values); the consumer no longer depends on it for program
content. Snapshot gates reproduce the legacy constructor messages
verbatim.

## J. Migrated consumer path

`construct_authority_world` now opens a native backend on a program
baseline (mapping "no program plane" to source-only mode and
qualification failures to construction failure), passes it to
`AuthorityConstructor(program_backend=...)`, and closes it after
admission validation. The constructor serves membership, kind, snapshot,
structural context, invocation, and resolution reads exclusively through
the boundary; `binding.py` is byte-identical. W1/W2 construction,
receipts, warrants, relevance scopes, evidence retention, and independent
histories are behaviorally unchanged, as the untouched Phase 4 slice
proves.

## K. Conformance results

Production conformance (`tests/test_program_backend_production.py`,
added to the default gate) re-runs all 22 Phase 5A cases through the
real adapter — content reads via the boundary, envelopes/metadata
test-side — plus two migration regression tests:

```text
Phase 5A conformance (unchanged file)          22 passed
production adapter conformance                 24 passed (22 + 2 migration)
default repository gate                        182 passed
Core v1 acceptance                              18 passed
Phase 4 vertical slice                          17 passed
phase3 boundary + authority construction        25 passed
authority maintenance + config routes 1-3      156 passed
checkout/design binding-adjacent suites         48 passed
spine + program evidence suites                 55 passed
npm run build / uv build / git diff --check    PASS
```

Disposable `/tmp` probes through the production path (not committed):
false-ancestor adapter mutant fails exactly
`test_typed_mechanical_facts_preserve_roles_and_snapshot` (1 failed, 23
passed); an invocation/resolution-`NOT_PRODUCED` backend passes core
history (3 conditional skips; only the native-behavior migration test
fails, as a native regression should); latest-substitution fails 8
cases including historical reads, wrong-snapshot qualification, and
evidence closure.

Pre-existing, unrelated: `test_maintenance_dependency_conformance.py`
reports 6 setup errors identically with and without this branch (verified
via stash); it is outside the default gate.

## L. Deleted direct coupling

From `AuthorityConstructor`: all `program_snapshot` / `program_entity` /
`program_entity_kind` / `program_identity_descriptor` /
`structural_context` / `program_invokes` / `program_resolution` reads,
the `_world_referents` label join, the `_world_assertions`
snapshot-grounding lookup, the now-dead `_labels` and `_grounding_extra`
helpers, and the vacuous cross-snapshot warrant check (with its
`_entity_snapshot` accessor). No `program_*` storage reads remain in the
constructor; `optional_program_rows` stays only as the generic helper
retained-artifact validation imports.

## M. Native extras left outside core

Comparison (`compare_spines` and friends), imports/types/extends
relations, resolution candidates, receipt/input/loss shapes, snapshot
grounding rules, display labels as anything but optional discovery
input, relevance-scope spine relation vocabulary, and all producer
machinery (extractor, `build_typescript_spine`, manifests) remain native
and unmigrated. No native implementation was deleted.

## N. Remaining extraction pressure

1. `validation.py` and `verify_construction_boundary` still read
   candidate `program_*` rows: deliberate retained-artifact
   verification, not decision coupling. A future backend-native
   retention format would revisit this.
2. Unmigrated native readers outside the binding path (`case.py`,
   `impact.py`, `maintenance.py`, `retrieval.py`, `evaluate.py`,
   `semantic_binding`, `governance`, relevance `COMPARABLE_RELATIONS`)
   keep working unchanged; each is a future forcing consumer, none was
   migrated for completeness.
3. `identityKind` vs `nativeKind`: identical in the current extractor;
   the boundary exposes one mechanical kind. A divergence would force an
   explicit contract choice.
4. Lifecycle still opens the baseline natively for `PublicationRef`
   basis recording; receipts require that native record shape.

## O. Glean questions now enabled

Can a Glean-backed occurrence supply: exact open + snapshot qualification;
opaque members + one mechanical kind; parent/child containment edges with
honest direction; optional invocation/resolution with declared
production; opaque observations with fail-closed reconstruction; a
`verify()` violation list; and a family capability table distinguishing
`NOT_PRODUCED` from supported-complete-empty? Any "no" is evidence about
Glean or the contract, to be settled in Phase 6.

## P. Deletion/minimality audit

| Introduced | Forced by | If removed | Foldable? |
| --- | --- | --- | --- |
| `ProgramBackend` ABC | migrated constructor reads | consumer reverts to native storage reads | no: the boundary is the phase |
| `Capability` + `CapabilityStatus` | R6 honesty through the adapter (production conformance) | `NOT_PRODUCED` vs complete becomes unrepresentable | no: one record, one enum |
| `BackendError` + 3 subclasses | lifecycle must distinguish absent plane / malformed plane / optional refusal | silent-empty vs fail-closed collapse | no: handling differs per case |
| `NativeProgramBackend` + `open_native_occurrence` | adapter over existing spine state | no production implementation | no |
| row dicts / opaque observation dicts | role-named facts without new classes | new row classes (worse) | n/a: already minimal |
| `discover` (optional) | existing filtered `program_entities` API + `call_site_invoking` | downstream discovery tests break | no: default raises |
| `verify()` | R7 retained-guarantee checks through the adapter | conformance cannot exercise retention honesty | no |

Net: the constructor lost ~40 lines of storage joins; the consumer's
program knowledge is now 13 boundary methods instead of 7 relation
schemas plus kernel tables. `snapshot_of`, `_entity_snapshot`, one
vacuous warrant check, and two dead helpers were prototyped or present
and deleted.

## Q. Final verdict

```text
YES — PRODUCTION PROGRAMBACKEND EXTRACTED; NATIVE BACKEND CONFORMS; READY FOR GLEAN CONFORMANCE
```
