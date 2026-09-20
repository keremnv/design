# Spine comparison contract

This document defines the native contract for comparing two independently
constructed program-spine snapshots. It is subordinate to
[PROGRAM_SPINE_CONTRACT.md](PROGRAM_SPINE_CONTRACT.md),
[SPINE_EXTRACTOR_CONTRACT.md](SPINE_EXTRACTOR_CONTRACT.md), and the
language-specific profiles that declare the snapshot capabilities being
compared.

The comparison layer is a mechanical comparison of durable spine output. It
does not construct a spine, parse source directly, infer semantic meaning, or
migrate governance claims. It produces an inspectable account of candidate
continuity and mechanical change.

The normative architecture has no external program ontology. A comparison
mechanism consumes the native core contract, declared capability contracts,
snapshot-local identities, structural context, evidence, completeness records,
and disclosed losses.

## Architectural boundary

Three operations remain distinct:

~~~text
SOURCE DIFF
  textual/file/range changes between source states

PROGRAM CORRESPONDENCE
  mechanically supported claims about which snapshot manifestations continue

PROGRAM DELTA
  identity, manifestation, and relation changes after correspondence is considered
~~~

A source diff may supply evidence for correspondence and localization. It is
not lineage by itself. A program delta may report a relation change that is not
represented by a simple changed-line containment test, such as a continued call
site whose invocation target changed.

The snapshots remain independently valid sealed World artifacts even when no
correspondence can be established. Cross-snapshot continuity is never implied
by an ID, name, source path, or source-location equality.

## Inputs and comparison identity

A comparison consumes:

~~~text
spine A
spine B
construction receipts/manifests for A and B
~~~

It MAY also consume:

~~~text
source-diff observations
snapshot-local source-range localization results
extractor-provided comparison hints
~~~

Optional inputs are evidence, not authority over the native spine facts. A
comparison mechanism MUST record which optional evidence it used.

The comparison itself has a comparison-local identity and version. That ID is
not a program identity and is not a lineage identity. A conceptual comparison
manifest contains:

~~~text
comparison ID
old snapshot identity
new snapshot identity
comparison mechanism identity/version
core contract compatibility result
capability compatibility results
optional source-diff identity
comparison configuration
~~~

The source-state identities of the snapshots are retained separately from the
extractor and capability versions that interpreted them.

## Compatibility before comparison

Comparison MUST establish compatibility before treating facts as comparable.
The minimum rules are:

1. The two spines MUST identify compatible major versions of "spine_core".
2. A standard capability relation is comparable only when both snapshots
   declare the same compatible capability semantics and version. A missing,
   incompatible, or "NOT_PRODUCED" capability is reported as not comparable
   for that capability.
3. A project or framework extension is comparable only when its ID, version,
   endpoint kinds, relation meaning, evidence rules, uncertainty semantics,
   and completeness basis are explicitly declared compatible.
4. Extractor implementation versions MAY differ only when their receipts and
   profile declarations establish compatible durable semantics. Matching
   extractor names alone is insufficient.
5. Different source-coordinate conventions, identity descriptor rules, or
   boundary policies MUST be treated as comparison limitations until an
   explicit compatibility declaration covers them.

The preferred construction path is to reconstruct both source states with the
same compatible core, capability/profile, extractor contract, and relevant
configuration. This keeps extractor evolution separate from software change.

When compatibility is absent, the comparison may still report snapshot and
manifest differences, but it MUST NOT silently emit ordinary identity or
relation deltas as though the semantic representations were equivalent.

Compatibility is capability-scoped. For example, compatible code structure may
be compared while a framework-specific UI capability is "NOT_COMPARABLE".

## Snapshot-local manifestations

Every program identity in a correspondence claim belongs to exactly one
immutable snapshot. The comparison uses the IDs emitted by those snapshots:

~~~text
program:ts:S1:callable:...
program:ts:S2:callable:...
~~~

These illustrative IDs do not claim permanence. Correspondence relates two
snapshot-local manifestations:

~~~text
S1:A != S2:B
correspondence(S1:A, S2:B)
~~~

Equal program referent IDs across two Worlds occur only when the snapshots
share the same snapshot identity, as in identical-input reconstruction. A
later comparison may support the claim that two manifestations continue the
same mechanically identifiable program object, but it does not rewrite either
snapshot ID into a global identity.

Names, qualified names, source paths, source coordinates, and serialization
IDs are comparison signals or evidence. None is a definition of continuity.

The comparison mechanism should prefer comparable identity kinds. It MUST NOT
claim a callable-to-component correspondence merely because both objects have
similar labels, and it MUST disclose when one profile has no equivalent
attachment surface.

## Correspondence model

Correspondence is represented as comparison-local claims between old and new
snapshot manifestations. It must support one-to-one, one-to-many,
many-to-one, and unmatched manifestations without manufacturing a permanent
lineage object.

A useful conceptual record is:

~~~yaml
correspondence_claim:
  comparison_id: ...
  old_entity: optional snapshot-A program ID
  new_entity: optional snapshot-B program ID
  group_id: optional comparison-local cardinality group
  continuity: CONTINUED | AMBIGUOUS | UNRESOLVED | NO_MATCH
  manifestation_changes: [RENAME, MOVE, MODIFIED]
  basis_class: DETERMINISTIC | HEURISTIC | OBSERVATIONAL
  evidence:
    - kind: ...
      description: ...
      source: ...
  limitations: [...]
~~~

This is a conceptual contract, not a required physical World schema. If
claims are persisted in the World, they remain ordinary application-level
facts with evidence and comparison scope. A comparison-local group ID is only
a way to inspect one comparison's cardinality event; it is not an identity
that survives comparisons.

The model deliberately separates dimensions:

~~~text
continuity
  whether a safe continuation claim was established

manifestation changes
  name, source/module placement, or implementation changes observed

cardinality event
  split, merge, new, or deleted membership in the comparison
~~~

The required human-facing outcome vocabulary is expressed across these
dimensions rather than overloaded into one enum:

| Outcome | Meaning |
| --- | --- |
| UNCHANGED_OR_CONTINUED | A one-to-one continuation was established and no compared manifestation change was observed. It may still have unexamined changes in an unproduced capability. |
| RENAME | Continuity was established and the relevant native name changed. |
| MOVE | Continuity was established and source/module or structural placement changed. |
| RENAME_AND_MOVE | Continuity was established and both changes were observed. |
| SPLIT | One old manifestation participates in a comparison-local one-to-many transformation group. |
| MERGE | Many old manifestations participate in a comparison-local many-to-one transformation group. |
| DELETED | An old manifestation has no safe new counterpart under the comparable scope. |
| NEW | A new manifestation has no safe old counterpart under the comparable scope. |
| AMBIGUOUS | Multiple plausible correspondences remain and no one continuation is selected. |
| UNRESOLVED | The available evidence or compatibility is insufficient to establish correspondence. |

MODIFIED is a separate manifestation/property annotation. A continued
callable can therefore be UNCHANGED_OR_CONTINUED as an identity outcome and
also have a body or signature modification in its delta. DELETED and NEW are
delta classifications for unmatched sides, not pairwise claims with a missing
endpoint.

### One-to-one

A one-to-one claim may have continuity CONTINUED. Its manifestation change
annotations then distinguish unchanged, rename, move, rename-plus-move, and
other modifications.

RENAME, MOVE, and RENAME_AND_MOVE MUST NOT be emitted when the mechanism cannot
establish continuity with sufficient evidence. A name or path match by itself
is insufficient.

### Split and merge

A split or merge is a comparison-local cardinality event over sets of
snapshot-local manifestations:

~~~text
split: {old A} -> {new B, new C}
merge: {old B, old C} -> {new A}
~~~

The group records its members, event kind, basis, and evidence. It does not
assert that every pair in the Cartesian product is a one-to-one continuation.
The mechanism MAY retain pairwise candidate claims inside the group, but those
claims must carry the group event and must not be presented as independent
unqualified identity continuity.

### New and deleted

An old identity is DELETED only when its side is sufficiently complete for the
relevant identity universe and no safe new counterpart exists. If the new
spine is partial, an absent counterpart is UNRESOLVED or NOT_COMPARABLE, not
automatically deleted. The same rule applies to NEW on the other side.

### Ambiguous and unresolved

AMBIGUOUS means the mechanism found multiple plausible candidates supported by
evidence. Candidate claims and their evidence may be retained, but no one
candidate is silently selected.

UNRESOLVED means the mechanism cannot establish a safe candidate or cannot
compare the relevant representation. Dynamic or missing evidence, incompatible
capabilities, and incomplete universes can all lead to this result.

Neither state is a negative assertion. Intelligent lineage adjudication, if
introduced later, must be a separate explicitly grounded resolution step.

## Mechanical correspondence evidence

The comparison mechanism MUST retain an inspectable basis for each established,
ambiguous, or unresolved claim. It MUST NOT make one opaque numeric similarity
score durable truth. A temporary ranking score MAY be used internally if it is
not presented as the warrant for continuity and the retained result explains
the actual evidence.

Potential evidence, ordered from stronger to weaker, includes:

1. An exact match of compatible identity descriptors, and only when the
   descriptor contract for those snapshots explicitly licenses continuation
   from descriptor equality. Descriptor stability for identical inputs is not
   by itself a continuation license. The current TypeScript
   `program_identity_descriptor` is a snapshot-local construction key, not a
   declared continuation rule, so equality is heuristic evidence.
2. Matching identity kind and compatible declaration or occurrence role.
3. Corresponding structural context, such as a continuing module or owning
   callable, with the context correspondence itself supported.
4. Preserved signature shape, parameter roles, member kind, or other declared
   native properties.
5. Source-diff evidence for a move or rename, including a mechanically
   recoverable old/new manifestation relationship.
6. Preserved neighboring native relations, such as imports, type relations,
   or invocation neighborhoods, when those capabilities are comparable.
7. Body or declaration similarity, where the comparison mechanism explicitly
   labels it heuristic.
8. Extractor-provided comparison hints, which are accepted only with their
   declared provenance and semantics.

Names alone, source-location equality alone, and graph proximity alone cannot
establish entailed continuity. Unique structural agreement can still be
useful heuristic correspondence. Relation neighborhoods are supporting
evidence; they do not turn a semantic or governance attachment into a program
identity.

Each evidence item is classified as one of:

~~~text
DETERMINISTIC
  exact/entailed support: the declared comparison/descriptor contract
  mechanically licenses correspondence from the available identity evidence.
  This is not a statement that the matching algorithm is deterministic.

HEURISTIC
  deterministic, reproducible structural evidence proposes correspondence
  but does not entail that the old and new manifestations are the same
  continuing program thing. HEURISTIC does not mean fuzzy, scored, or
  model-judged.

OBSERVATIONAL
  records supplied or externally observed comparison evidence, such as a
  source diff or a caller-supplied cardinality group, without itself proving
  continuity
~~~

Deterministic computation does not imply mechanically entailed
correspondence. A unique heuristic mapping may be continuity CONTINUED with
basis_class HEURISTIC. Ambiguous heuristic candidates remain AMBIGUOUS; extra
heuristic signals must not break that tie.

An established correspondence may use several evidence items, but a
heuristically supported claim MUST remain visibly heuristic. If deterministic
and heuristic evidence conflict, the result is ambiguous or unresolved unless
the contract explicitly defines a mechanical resolution rule.

## Program delta

ProgramDelta is a comparison-local derived report constructed from:

~~~text
spine A + spine B + correspondence claims/groups
~~~

It is not a new snapshot, a permanent identity system, or a semantic claim
migration record. Every delta record retains its old/new snapshot IDs and the
correspondence or compatibility basis that produced it.

### Identity delta

The identity section reports:

~~~text
continued
added
removed
split
merged
ambiguous
unresolved
~~~

continued is a safe one-to-one identity correspondence. added and removed are
unmatched identities under a stated comparable universe. split and merged are
cardinality groups. ambiguous and unresolved retain candidate or limitation
information rather than forcing an identity classification.

### Property and manifestation delta

For continued comparable identities, the delta MAY report only properties owned
by the declared native capabilities. The initial useful set is:

~~~text
name changed
source manifestation changed
structural owner/context changed
signature changed
boundary classification changed
identity kind changed, when the profiles define kind comparison
~~~

Source manifestation changes include a moved range, changed declaration
occurrence, or changed source module. They do not by themselves mean that the
program identity changed. A whitespace-only edit may move a range while
leaving descriptors, structure, signatures, and relations unchanged.

MODIFIED is an observation about changed comparable program facts. It does not
imply that every implementation change was detected when the relevant
capability is partial or unproduced.

### Relation delta

For each comparable relation capability, compare relation tuples only after
endpoint correspondence and capability completeness have been assessed. The
delta can report:

~~~text
relation preserved
relation added
relation removed
relation endpoint retargeted
relation not comparable
relation change unresolved
~~~

For the current TypeScript spine, a call-site relationship is compared in its
native shape:

~~~text
old call_site -> old target
new call_site -> new target
~~~

If the call site continues and the target changes from a corresponding
submitOrder manifestation to a corresponding saveDraft manifestation, the
delta reports an endpoint retargeting. It does not flatten the call into a
callable-only fact before comparison.

An added or removed relation is reportable only within the comparable scope of
its capability. If a call outcome is unresolved in one snapshot, the absence
of program_invokes is not a removed invocation. If either endpoint is
ambiguous, the relation change may be relation change unresolved even when the
raw tuples differ.

## Completeness and negative reasoning

Comparison consumes construction-time capability records; it does not replace
them. The comparison receipt references or summarizes the records that justify
each comparison scope. It MUST preserve the distinction between:

~~~text
capability not produced
capability produced but partial
capability complete over a stated universe
capability not comparable across snapshots
~~~

The following negative conclusions are permitted only under the stated basis:

| Basis | Permitted conclusion |
| --- | --- |
| program-universe membership complete for both compatible declared universes | an in-scope identity absent on the other side is eligible for NEW or DELETED, subject to correspondence evidence |
| code structure complete over both admitted inputs | supported declaration/context additions and removals may be reported within that structural profile |
| imports complete under the same static resolver contract | recognized static import tuple changes may be reported; dynamic loading remains outside the conclusion |
| calls statically complete under the same analyzer basis | recognized call-site outcomes and resolved invocation tuples may be compared; runtime targets remain outside the conclusion |
| capability partial, unknown, or not produced | no general absence or removal conclusion for that capability |
| profile or boundary incompatible | no ordinary semantic delta for the affected capability |

The mechanism MUST distinguish “no comparable edge is present” from “the
capability proved that no such edge exists.”

## Attachment preservation and maintenance hooks

Correspondence provides inputs for later maintenance of source, semantic, and
governance attachments. It does not copy or validate those claims.

The comparison output SHOULD expose, for each continued identity and affected
relation, a maintenance context containing:

~~~text
identity continuity result and basis
old/new source manifestations
structural context preserved/changed
signature preserved/changed
native relation additions/removals/retargets
resolution outcome changes
boundary/input/configuration changes
capability completeness and compatibility limitations
old and new evidence references
known losses relevant to the comparison
~~~

This lets a later claim-maintenance step ask whether the identity and the
grounds for a claim survived. It does not answer that question for every
claim.

For example:

~~~text
Figma/design correspondence -> component usage
  may survive a callable rename if its supported identity/context remains
  suitable, subject to a later purpose-specific maintenance decision.

call site -> PurchaseAction
  must be reconsidered when the call site's invocation target changes or its
  source grounding moves in a way that affects the claim's warrant.
~~~

Identity continuity evidence is not claim-validity continuity. Old grounds
must not be silently attached to a new manifestation. In particular,
`CONTINUED + HEURISTIC` must never silently renew a source, semantic, or
program attachment. Attachment warrant context belongs to
[AUTHORITY_CONSTRUCTION_CONTRACT.md](AUTHORITY_CONSTRUCTION_CONTRACT.md).
Program-side maintenance assessments and governance-case assembly belong to
[AUTHORITY_MAINTENANCE_CONTRACT.md](AUTHORITY_MAINTENANCE_CONTRACT.md) and
[GOVERNANCE_CASE_CONTRACT.md](GOVERNANCE_CASE_CONTRACT.md).
`ProgramDelta.maintenance` is an entity-scoped input to those stages, not an
attachment assessment and not a compliance verdict.

## Source diff and localization

The intended path is:

~~~text
source diff
  -> changed old/new source ranges
  -> snapshot-local program localization
  -> candidate changed identities
  -> cross-snapshot correspondence
  -> ProgramDelta
~~~

The localizer uses each snapshot's own canonical evidence and identity
surfaces. It may return several enclosing identities for a range. A changed
range is a candidate localization, not a governance impact decision.

Comparison MUST also permit changes that simple containment misses:

~~~text
file/module moves or renames
changed configuration or boundary
descriptor changes without directly changed body lines
relation endpoint retargeting
split/merge transformations
external endpoint or dependency identity changes
~~~

The source diff remains recorded as observational evidence. It cannot force a
continuation or force a deletion when the spine facts are incomplete.

## SpineComparisonReceipt

Construction and comparison have separate receipts. A
SpineComparisonReceipt is an inspection and admission artifact, not a second
truth system. It summarizes the comparison-local claims and delta and points
to the source spines and their authoritative construction/completeness
records.

The v1 conceptual shape is:

~~~yaml
receipt_version: spine_comparison_receipt/v1
comparison_id: ...
conformance:
  status: PASS | CONTRACT_FAILURE
  diagnostics: [...]
snapshots:
  old:
    id: ...
    construction_receipt: ...
  new:
    id: ...
    construction_receipt: ...
compatibility:
  core: COMPATIBLE | INCOMPATIBLE
  capabilities:
    - id: ...
      old_version: ...
      new_version: ...
      status: COMPARABLE | PARTIAL | NOT_COMPARABLE | NOT_PRODUCED
      basis: ...
      limitations: [...]
comparison_mechanism:
  id: ...
  version: ...
  configuration: ...
  optional_inputs: [...]
correspondence_summary:
  outcomes:
    unchanged_or_continued: 0
    rename: 0
    move: 0
    rename_and_move: 0
    split: 0
    merge: 0
    deleted: 0
    new: 0
    ambiguous: 0
    unresolved: 0
  basis_classes:
    deterministic: 0
    heuristic: 0
delta_summary:
  identity: {...}
  properties: {...}
  relations:
    - capability: ...
      status: COMPARABLE | PARTIAL | NOT_COMPARABLE
      added: 0
      removed: 0
      preserved: 0
      endpoint_retargeted: 0
      unresolved: 0
      completeness_receipt_refs: [...]
unresolved_comparisons: [...]
known_losses: [...]
representative_examples: [...]
adequacy_probes: optional [...]
acceptance: optional
~~~

The receipt MUST NOT contain an opaque lineage-quality score or imply that all
future correspondence uses have been solved. Counts are inspection aids.
Representative examples should show old/new identities, evidence, context,
correspondence basis, and the resulting delta.

The comparison receipt may summarize World completeness receipts, but it may
not widen their universes, statuses, or bases. If a comparison mechanism
introduces comparison-specific completeness records later, those records must
remain separately identifiable and capability-scoped.

## Comparison adequacy

A comparison can conform honestly and still be inadequate for a purpose. For
example, two snapshots may compare their enclosing callables successfully
while neither spine represents component usages. That is a purpose limitation,
not a comparison contract failure.

An optional purpose-specific probe records:

~~~yaml
question: ...
input_or_test: ...
observed_result: ...
relevant_capability_or_surface: ...
implication: ...
receipt_ref: ...
~~~

Examples include:

~~~text
Can two Button uses in one page be distinguished across snapshots?
Can a changed handler range localize to a call site and its enclosing usage?
Can an invocation retarget be observed when the surrounding callable continues?
Can a helper be followed through when it has no semantic attachment?
~~~

Probe results are evidence for a user's construction purpose. They are not
universal conformance tests and must not be collapsed into a quality score.

## Diff and lineage readiness

Lineage matching remains deferred. A conforming extractor is required only to
expose the material it actually has:

~~~text
deterministic snapshot-local descriptors
identity kinds
structural context
declaration and occurrence roles
source/configuration evidence
capability relations and outcomes
known loss declarations
~~~

The comparison receipt MAY report observed behavior, such as identical-input
rebuilds producing identical descriptors or whitespace edits preserving
descriptors. It MUST NOT claim universal lineage adequacy, promise that a
rename or move will be recognized, or replace observations with an opaque
readiness score.

Comparison should be able to use richer or poorer extractor output. A coarse
extractor may leave component-instance or fine-grained correspondence
unresolved while remaining core-conformant. That loss must be visible and may
make the output inadequate for a purpose.

## Relationship to current TypeScript output

The current TypeScript profile exposes the material a comparison mechanism
needs without making its implementation mandatory:

~~~text
snapshot-local program IDs
program_entity and program_entity_kind membership/kind facts
structural_context
program_imports
program_invokes with call-site endpoints
program_has_type / program_extends / program_implements
program_resolution outcomes and candidates
exact UTF-8 byte-range evidence
declared/effective input manifests
capability-scoped completeness records
construction receipt losses and comparison-readiness observations
~~~

The comparison contract does not require TypeScript checker symbols, UTF-16
conversion, Node, package-resolution implementation details, or the current
relation storage layout. Another extractor may provide a different internal
construction and still compare at any capability/kind intersection for which
it declares compatible semantics.

The current receipt's statement that lineage is deferred remains correct. Its
known losses, especially the absence of component instances and unresolved
dynamic targets, are inputs to comparison adequacy and must not be hidden by a
successful mechanical match of enclosing callables.

## Kernel relationship and deliberate non-changes

The existing World kernel is sufficient to store the inputs, comparison-local
claims, evidence, ordinary typed relations, and derived delta records as
application-level artifacts. It already provides thin referents, typed n-ary
relations, content-addressed assertion identity, multiple grounds, source
observations, deterministic derivation, scoped completeness, explicit
unresolvedness, and candidate-to-sealed lifecycle.

The kernel does not provide a cross-World join, a lineage primitive, a
comparison-local cardinality-group primitive, relation-aware claim-maintenance
semantics, or comparison-receipt validation. These are application-level
comparison concerns. This design deliberately does not add generic kernel
primitives, permanent lineage IDs, a universal matcher, a fuzzy score schema,
or semantic claim migration.

## Deliberately deferred

This contract does not choose or implement:

- a source-diff parser or change format;
- a matching or tree-differencing algorithm;
- thresholds for heuristic candidate ranking;
- a persistent World schema for comparison claims and delta records;
- whether comparison artifacts are sealed Worlds, sidecars, or another
  application-level artifact (the v0 implementation stores
  `spine.comparison.json` as an application sidecar and does not add kernel
  lineage primitives);
- cross-language or cross-profile identity matching;
- cross-version lineage persistence;
- runtime behavior comparison;
- claim retention, invalidation, or semantic adjudication (see
  [AUTHORITY_MAINTENANCE_CONTRACT.md](AUTHORITY_MAINTENANCE_CONTRACT.md) and
  [GOVERNANCE_CASE_CONTRACT.md](GOVERNANCE_CASE_CONTRACT.md) for the design of
  maintenance assessments and case assembly; those remain outside this
  comparison contract);
- mandatory user acceptance of a comparison receipt;
- UI/component-instance, routing, state, Reads/Writes, or other deferred
  extractor capabilities.

Future implementation must preserve the distinction between valid snapshots,
correspondence evidence, program delta, and later semantic claim maintenance.

