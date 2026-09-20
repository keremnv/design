# Authority attachment maintenance contract

This document defines program-side maintenance of existing
authority/program attachments. It is subordinate to
[`FOUNDATIONS.md`](FOUNDATIONS.md),
[`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md), and
[`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md). It consumes
the program spine, comparison, and authority-construction contracts:

- [`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md)
- [`SPINE_COMPARISON_CONTRACT.md`](SPINE_COMPARISON_CONTRACT.md)
- [`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md)

Markdown reconstruction, when needed by a later case, follows
[`MARKDOWN_SOURCE_PROFILE.md`](MARKDOWN_SOURCE_PROFILE.md).

This contract governs durable *assessment* output. It does not prescribe an
implementation, a matcher, a model, or a domain vocabulary.

The normative words **MUST**, **MAY**, and **DEFERRED** have their usual
contract meaning. Changing the meaning of a named maintenance dimension,
dependency kind, or persistence implication requires a new contract version.

v0 identity:

```text
contract:   authority_maintenance/v0
artifact:   AttachmentMaintenanceAssessment
sidecar:    authority.maintenance.json   (application sidecar; not a World)
API:        ontology_author.authority.assess_attachment_maintenance
```

The v0 writer lives in `ontology_author.authority.maintenance`.

## Architectural position

Keep these stages distinct:

```text
PROGRAM DELTA
    mechanical description of program change

        ↓

ATTACHMENT MAINTENANCE
    does the persisted mapping still have mechanical support?
    → AttachmentMaintenanceAssessment (this contract)

        ↓

CHANGE IMPACT / RELEVANCE
    did the program change touch the surface this authority governs?
    → AuthorityChangeImpact
    → GOVERNANCE_CASE_CONTRACT.md

        ↓

CASE ASSEMBLY
    should the original authority be presented for this change?

        ↓

ADJUDICATION
    what the authority implies for the changed program
    → GOVERNANCE_ADJUDICATION_CONTRACT.md
```

Maintenance answers:

> Given an old authority/program attachment, its warrant, and ProgramDelta,
> what mechanically happened to the grounds that justified this attachment?

It MUST NOT decide whether the changed program complies with authority.

It MUST NOT decide whether the authority is relevant to this ProgramDelta.

It MUST NOT persist a new source/program assertion.

It MUST NOT mutate either World.

## Explicit non-goals

This contract does not implement or require:

- attachment migration or automatic reattachment;
- silent renewal from correspondence;
- LLM re-resolution;
- source-document lineage or `AuthorityDelta`;
- adjudication, policy enforcement, or PASS/FAIL/COMPLIANT/VIOLATION;
- agent prompting, semantic search, RAG, or corpus grep;
- Git diff ingestion or UI;
- new spine capabilities or domain predicates;
- kernel lineage, cross-World joins, or case tables;
- case selection, relevance scoring, or a watch/policy engine over program
  changes.

ProgramDelta `maintenance` hooks from comparison remain **inputs**, not this
artifact. They are entity-scoped convenience records. Authority maintenance
MUST inspect warrant dependencies against correspondence and relation delta.
It MUST NOT treat `ProgramDelta.maintenance.relations_changed` as proof that
a warrant dependency changed.

## Inputs

A maintenance run consumes:

```text
old governed World          sealed; contains spine S_old plus authority facts
new program-spine World     sealed; spine S_new; need not contain authority
spine.comparison.json       correspondence, ProgramDelta, comparison receipt
AuthorityConstructionReceipt of the old World
authorized source universe  standing and revisions used at construction
```

Authoritative source revisions used by the existing attachments are assumed
**unchanged** for this milestone. Original evidence MUST remain recoverable.
Maintenance MUST NOT reinterpret newer source text.

Optional comparison evidence (source diffs, localization) is already folded
into correspondence/ProgramDelta. Maintenance MUST NOT invent a second
source-diff pass.

## Output

One sidecar bundle per comparison:

```text
authority.maintenance.json
```

It contains:

```text
maintenance_id
contract / mechanism identity / version
old_world / old_snapshot
new_world / new_snapshot
comparison_id
purpose / constructor_profile references from the old receipt
assessments[]               one AttachmentMaintenanceAssessment per warrant
known_omissions
```

The sidecar is not a sealed World, not a second truth system, and not a
lineage primitive. The two input Worlds remain independently valid.

## Critical invariants

Frozen:

```text
program correspondence
    ≠
attachment renewal
    ≠
claim-validity continuation
```

Especially:

```text
CONTINUED + HEURISTIC
```

MUST never migrate, renew, or validate an attachment.

A later `DETERMINISTIC` correspondence basis, if comparison ever emits it,
still MUST NOT copy claims. It only strengthens input to later
revalidation/re-resolution construction, which this contract does not
implement.

Identity continuity and claim-validity continuity remain separate.

Also frozen:

```text
maintenance assessment
    ≠
new source/program assertion
```

A candidate new target MAY be recorded. That is not a durable attachment in
the new snapshot.

## Maintenance is not relevance

Keep these questions distinct:

```text
attachment maintenance
    validity/support of the persisted mapping

change impact / relevance
    applicability of that authority to this ProgramDelta

case selection
    whether original authority belongs in the assembled case

adjudication
    what the authority implies for the changed program
```

An attachment MAY remain mechanically supported (`HOLD`) while the program
surface it governs changes. That is not a maintenance failure. It is often
exactly why the authority must enter a GovernanceCase.

Do not implement case selection as:

```text
maintenance_action ≠ HOLD
```

Warrant dependencies justify *why the attachment points here*. They are not
the full set of mechanical facts whose change should surface the authority.
Relevance scope is a separate, inspectable surface. It MUST NOT be overloaded
onto `authority_attachment_warrant`.

`AuthorityChangeImpact` and case selection are specified in
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md). Construction
persists `authority_relevance_scope` as specified in
[`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md).

## Existing attachment and warrant

Attachments target explicit snapshot-local program manifestations in the old
World. Both topologies remain valid:

```text
source evidence -> program          SOURCE_PROGRAM
source evidence -> semantic -> program
                                    SOURCE_SEMANTIC + SEMANTIC_PROGRAM
```

Every program-involving attachment has one or more
`authority_attachment_warrant` rows. Each warrant is a separate maintenance
subject. One claim MAY have several warrants (for example an importer module
and an imported module).

v0 warrant content, already constructed:

```text
assertion_id
program_snapshot_id
program_entity
structural_context                 JSON list of enclosing program IDs
justifying_program_relations       JSON list of native relation tuples
justifying_resolution_outcomes     JSON list of spine resolution rows
constructor_profile
relation_support
endpoint_resolution
```

plus SOURCE grounding on the warrant assertion (evidence pointers, not
source-text bodies).

Do not rediscover the original attachment from scratch during normal
maintenance. The warrant is the dependency surface.

## AttachmentMaintenanceAssessment

Tentative name retained. It is an application-level record, not a kernel
type.

It MUST refer to:

```text
old_world_id / old_snapshot_id
new_world_id / new_snapshot_id
comparison_id
attachment_assertion_id            the program-involving claim
claim_kind                         SOURCE_PROGRAM | SEMANTIC_PROGRAM
warrant_assertion_id
old_program_entity
candidate_new_manifestations[]     0..n snapshot-local new IDs
```

It MUST NOT mutate Worlds.

### Dimensions, not one enum

Do not collapse maintenance into valid/invalid, STALE, or PASS/FAIL.

Record three independent dimensions, then a derived action. Names below are
normative for v0.

#### 1. Continuation

Cardinality of candidate new manifestations for the warrant’s
`program_entity`, after comparison:

| `continuation` | Meaning |
| --- | --- |
| `UNIQUE` | Exactly one new manifestation is the comparison’s continuation candidate. |
| `AMBIGUOUS` | Two or more plausible new manifestations remain. No winner. |
| `NONE` | No represented continuation candidate (orphaned / deleted under a comparable universe, or `NO_MATCH`). |
| `NOT_COMPARABLE` | The relevant identity kind or capability cannot be compared. |

`UNIQUE` does **not** mean the attachment may be copied. Pair it with
`correspondence_basis`.

Do not encode HEURISTIC into the continuation value. A unique heuristic map
is `continuation=UNIQUE` and `correspondence_basis=HEURISTIC`.

Split groups are `AMBIGUOUS` (one-to-many). Merge groups MAY be `UNIQUE` to
the merged new entity while other dimensions show changed/lost grounds.

#### 2. Correspondence support

Copied from the comparison claim that produced the continuation, or
`ABSENT` when there is no claim:

| Field | Values |
| --- | --- |
| `correspondence_continuity` | `CONTINUED` \| `AMBIGUOUS` \| `UNRESOLVED` \| `NO_MATCH` \| `ABSENT` |
| `correspondence_basis` | `DETERMINISTIC` \| `HEURISTIC` \| `OBSERVATIONAL` \| `ABSENT` |

v0 automatic comparison is HEURISTIC. Assessments MUST leave that visible.

#### 3. Per-dependency change

Each recorded warrant dependency gets:

| `dependency_change` | Meaning |
| --- | --- |
| `PRESERVED` | The same mechanical fact is present on the candidate new side after endpoint correspondence. |
| `CHANGED` | The fact is present but an endpoint or recorded value was retargeted or replaced. |
| `LOST` | The required fact is absent (removed relation, missing identity, missing resolution). |
| `UNKNOWN` | Comparison left this fact unresolved. |
| `NOT_COMPARABLE` | The capability/profile cannot compare this fact. |

`CHANGED` includes relation endpoint retarget. `LOST` includes a required
tuple with no new counterpart. Do not call every `CHANGED` “stale”; `LOST`
is the closer analogue of disappearance.

#### Derived rollups

These are inspection aids. They MUST remain consistent with the dimensions
above and MUST NOT replace them.

```text
grounds_summary:
  GROUNDS_PRESERVED     every recorded dependency is PRESERVED
  GROUNDS_CHANGED       at least one CHANGED; none LOST / UNKNOWN / NOT_COMPARABLE
  GROUNDS_LOST          at least one LOST; none UNKNOWN / NOT_COMPARABLE
  GROUNDS_UNKNOWN       at least one UNKNOWN; none NOT_COMPARABLE
  GROUNDS_INCOMPARABLE  at least one NOT_COMPARABLE
```

```text
orphaned: continuation = NONE
```

Avoid a single `STALE` / `RE_RESOLUTION_REQUIRED` / `UNRESOLVED` enum as the
primary result. Those English words MAY appear only in commentary that
points at the dimensions (`LOST` ≈ stale grounds; `RERESOLVE` below ≈
re-resolution required).

#### 4. Maintenance action

What a **later** construction or adjudication step is invited to do. Not a
compliance verdict. Not a persist instruction for a new attachment.

| `maintenance_action` | Meaning |
| --- | --- |
| `HOLD` | Recorded grounds are preserved. Correspondence, if unique, is still not renewal. Later revalidation MAY consider the candidate; this stage MUST NOT copy. |
| `RERESOLVE` | Grounds changed, were lost, are ambiguous, or the old target is orphaned. The relationship must be resolved again if it is to exist on the new snapshot. |
| `CANNOT_ASSESS` | Comparison cannot establish enough continuity or comparable facts. |

Every assessment also carries:

```text
persistence_implication: NO_RENEWAL
```

v0 MUST NOT emit any other persistence implication. There is no `RENEW`.

Derivation (worst-case; evaluate in order):

```text
continuation in {NOT_COMPARABLE}
    or any dependency NOT_COMPARABLE
    or correspondence_continuity = UNRESOLVED
        → CANNOT_ASSESS

continuation in {AMBIGUOUS, NONE}
    or any dependency in {CHANGED, LOST, UNKNOWN}
        → RERESOLVE

otherwise UNIQUE + all dependencies PRESERVED
        → HOLD
```

`HOLD` with `correspondence_basis=HEURISTIC` is the conservative default
happy path. It is not silent preservation of the claim. It is not a
statement that the authority is irrelevant to this ProgramDelta.

## Warrant-dependency model

A warrant mixes **dependencies** (mechanical facts the attachment used) with
**provenance** (how construction labeled that use). Only dependencies are
inspected against ProgramDelta.

### Dependency kinds

| Kind | Source on the warrant | Compared using |
| --- | --- | --- |
| `entity_identity` | `program_entity` | correspondence of that ID |
| `structural_context` | each ID in `structural_context` | correspondence of that ID, and whether it remains an enclosing context of the candidate |
| `program_relation` | each object in `justifying_program_relations` | `ProgramDelta.relations[relation]` preserved / retargeted / removed / unresolved / not comparable |
| `resolution_outcome` | each object in `justifying_resolution_outcomes` | old vs new `program_resolution` for that subject/capability after correspondence |
| `boundary` | only if the warrant recorded boundary as a justifying fact | manifestation `boundary` change |
| `source_manifestation` | only if the warrant recorded source range/module as a justifying fact | manifestation `source_manifestation` / `source_location` change |
| `capability_assumption` | capability that produced a justifying relation | comparison compatibility for that capability |
| `completeness_assumption` | completeness receipt that licensed the justifying relation’s existence | comparison completeness limitations for that capability |

### Not dependencies by default

Do not treat as mechanical dependencies unless a future warrant schema
explicitly lists them:

- `constructor_profile`, `relation_support`, `endpoint_resolution` labels;
- exploration provenance;
- World revision counters;
- human labels and identity descriptors except as already used by comparison;
- SOURCE grounding pointers (source assumed unchanged this milestone);
- “same file changed” or “same module contains another changed function”;
- byte-offset shifts;
- every native relation that happens to mention the attached entity.

v0 default warrants record entity, structural context, `program_invokes`
tuples when present, and resolution outcomes. They do **not** record source
manifestation or boundary as justifying facts. A source-location-only move
therefore MUST NOT, by itself, mark those warrants `CHANGED`.

A construction profile MAY add `source_manifestation` or `boundary` to a
warrant. Then those facts become dependencies for that attachment only.

### Program-relation matching

For a justifying tuple such as:

```text
{ relation: program_invokes, call_site: C_old, target: T_old }
```

inspect `ProgramDelta.relations.program_invokes`:

| Delta bucket containing the old tuple | `dependency_change` |
| --- | --- |
| `preserved` | `PRESERVED` |
| `retargeted` | `CHANGED` |
| `removed` | `LOST` |
| `unresolved` | `UNKNOWN` |
| capability `NOT_COMPARABLE` / `NOT_PRODUCED` | `NOT_COMPARABLE` |
| old tuple absent from the delta and from the old spine | warrant/World inconsistency → `UNKNOWN` plus a known omission |

Match on the old tuple’s recorded roles, not on “any relation involving C”.
A retarget of an unrelated invocation on the same owner MUST NOT affect this
dependency.

`structural_context` is preserved when each listed old ID has a unique
continuation and remains in the new entity’s enclosing context chain. If the
owner ID continues but is no longer a parent of the candidate, that
dependency is `CHANGED`. If a listed owner is `NONE`, it is `LOST`.

## Treatment of HEURISTIC correspondence

v0 comparison’s automatic continuity is HEURISTIC. Therefore v0 maintenance
is conservative.

A unique heuristic continuation MAY fill `candidate_new_manifestations` with
that one new ID. The assessment MUST still say:

```text
continuation = UNIQUE
correspondence_continuity = CONTINUED
correspondence_basis = HEURISTIC
persistence_implication = NO_RENEWAL
```

If justifying relations are preserved: `maintenance_action = HOLD`.

If a justifying relation retargeted: `maintenance_action = RERESOLVE`.

In both cases, maintenance MUST NOT create:

```text
semantic:… -> program:S_new:…
```

or copy `authority_attachment_warrant` onto the new snapshot.

`OBSERVATIONAL` basis is treated like HEURISTIC for persistence: never
renew. `DETERMINISTIC` basis, if present later, still yields `NO_RENEWAL` in
this contract version; it may only change how a later revalidation step
weighs the candidate.

## Candidate continuation semantics

`candidate_new_manifestations` is an ordered, inspectable list of new
snapshot-local program IDs. It is not an attachment.

| Continuation | List contents |
| --- | --- |
| `UNIQUE` | The single new ID from the correspondence claim. |
| `AMBIGUOUS` | All comparison candidates; no distinguished winner. |
| `NONE` | Empty. |
| `NOT_COMPARABLE` | Empty; limitations recorded. |

Do not rank, score, or drop candidates. Do not use numeric confidence.

For `UNIQUE` + `CHANGED` program_relation, still record the unique new
entity **and** the new relation tuple from the retarget record. The new
tuple is context for later re-resolution, not a new claim.

## Provenance

Every assessment MUST be inspectable. No private chain-of-thought. No
numeric confidence.

Required fields:

```text
old attachment assertion_id / claim_kind / relation_name
old warrant assertion_id / program_entity / snapshot
comparison_id / comparison mechanism version
correspondence claim reference (or ABSENT)
candidate_new_manifestations
correspondence_continuity / correspondence_basis
dependencies_examined[]:
    kind
    recorded_fact
    dependency_change
    delta_evidence          preserved|retargeted|removed|… references
known_uncertainty[]         heuristic basis, unresolved delta, partial capability
grounds_summary
continuation
maintenance_action
persistence_implication     NO_RENEWAL
limitations[]
```

`delta_evidence` MUST point at ProgramDelta entries actually used, not at
the whole delta.

## Source authority remains immutable evidence

This milestone does not compare source documents.

Assessments MUST NOT conclude that original evidence is stale because the
program changed. Evidence recovery remains: stored `SourceObservation` plus
driver reconstruction at the recorded revision.

Leave room for a later `AuthorityDelta` or equivalent. Program maintenance
MUST NOT silently reinterpret newer source text.

## Worked maintenance examples

These are conceptual. They do not adjudicate.

### Example 1 — cancellation invocation retarget

Old attachment:

```text
A1  SEMANTIC_PROGRAM
    semantic:CancellationEntryAction
        -> call_site C_old
warrant:
    program_entity = C_old
    structural_context includes SubscriptionPage
    program_invokes(C_old, openRetentionFlow)
```

ProgramDelta:

```text
C_old -> C_new
continuity = CONTINUED
basis = HEURISTIC
program_invokes: retargeted
    openRetentionFlow -> cancelSubscription
```

Assessment:

```text
continuation: UNIQUE
candidate_new_manifestations: [C_new]
correspondence_basis: HEURISTIC
entity_identity: PRESERVED          (unique heuristic continuation)
structural_context: PRESERVED       (SubscriptionPage continues and still owns C_new)
program_relation program_invokes: CHANGED   (RETARGETED)
resolution_outcome: as recorded     (CHANGED if RESOLVED target identity changed)
grounds_summary: GROUNDS_CHANGED
maintenance_action: RERESOLVE
persistence_implication: NO_RENEWAL
```

Do **not** persist `CancellationEntryAction -> C_new`.

Do **not** say whether `cancelSubscription` violates the retention-flow
requirement.

### Example 2 — harmless movement

Old attachment depends on:

```text
callable A_old
program_invokes(A_callsite_old, PaymentGateway.authorize)
```

New snapshot moves/renames the callable. Correspondence is unique HEURISTIC.
The justifying invocation is in `preserved`. Source location changed.
Warrant did not list source manifestation as a dependency.

Assessment:

```text
continuation: UNIQUE
correspondence_basis: HEURISTIC
entity_identity: PRESERVED
program_relation program_invokes: PRESERVED
source_manifestation: not a recorded dependency (not examined as such)
grounds_summary: GROUNDS_PRESERVED
maintenance_action: HOLD
persistence_implication: NO_RENEWAL
```

This is mechanically different from Example 1 (`PRESERVED` vs `CHANGED`).
HOLD still is not renewal. HOLD also does not decide case selection: if the
callable’s declared relevance surface includes implementation
(`source_manifestation`), a body change may still be `AFFECTED` for
`AuthorityChangeImpact`. A neighboring helper with no recorded surface stays
`UNAFFECTED`. See the case contract.

### Example 3 — ambiguous continuation

Old attached identity has two plausible new candidates, comparison
continuity `AMBIGUOUS`.

Assessment:

```text
continuation: AMBIGUOUS
candidate_new_manifestations: [N1, N2]
correspondence_continuity: AMBIGUOUS
correspondence_basis: HEURISTIC
entity_identity: UNKNOWN            (no unique continuation)
program_relation: UNKNOWN or NOT_COMPARABLE as the delta states
grounds_summary: GROUNDS_UNKNOWN or GROUNDS_INCOMPARABLE
maintenance_action: RERESOLVE
persistence_implication: NO_RENEWAL
```

Do not choose N1 or N2.

## Kernel reuse

| Need | Reuse |
| --- | --- |
| Old/new program handles | existing snapshot-local `REFERENT` IDs |
| Warrant and claims | ordinary `BASE` relations in the old World |
| Evidence pointers | `SourceObservation` / `_world_groundings` |
| Relation delta | application ProgramDelta; not kernel staleness |
| Completeness of compared capabilities | existing spine completeness receipts, via comparison |
| Open-world | `UNKNOWN` / `NOT_COMPARABLE` rather than “invalid” |
| Unresolved construction | ordinary `authority_unresolved` rows; not assessed as attachments unless they carry warrants |
| Artifact integrity | both Worlds stay sealed; sidecar is extra |
| Inspectable summary | application sidecar, like `spine.comparison.json` |

Experimental kernel `Contract` / `Obligation` / `Resolution` /
`Adjudication` types MUST NOT be this assessment.

## Kernel limitations

No new kernel primitive is required.

1. Referents do not join two sealed Worlds. Assessments name IDs from each
   snapshot; they do not FK across databases.
2. Relation-level kernel staleness does not detect program-snapshot
   replacement. ProgramDelta does.
3. Warrant v0 stores some dependency lists as JSON text. Maintenance parses
   those lists. An implementation MAY later persist dependencies as ordinary
   tuples; that is not a kernel change.
4. The kernel has no lineage primitive, and MUST NOT grow one to auto-renew
   attachments.
5. Completeness receipts remain relative to a named universe. They do not
   mean “no other authority exists.”

## Intentionally deferred

- Source-authority maintenance / `AuthorityDelta`.
- Revalidation or re-resolution construction that would persist new
  attachments in a new governed World.
- Carrying semantic referents into a new sealed World.
- Policy compilation. Adjudication is specified in
  [`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
- Treating `HOLD` as permission to copy under `DETERMINISTIC` correspondence.
- Normalizing warrant JSON into relations (allowed later, not required).
- Human acceptance of a maintenance sidecar.

Change impact and case assembly are specified in
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md).
Adjudication of an assembled case is specified in
[`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
