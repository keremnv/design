# Governance-case assembly contract

This document defines deterministic selection of a self-contained
`GovernanceCase` from a program change and previously constructed authority
attachments. It is subordinate to
[`FOUNDATIONS.md`](FOUNDATIONS.md),
[`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md), and
[`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md).

It consumes:

- [`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md)
- [`SPINE_COMPARISON_CONTRACT.md`](SPINE_COMPARISON_CONTRACT.md)
- [`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md)
- [`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md)
- [`MARKDOWN_SOURCE_PROFILE.md`](MARKDOWN_SOURCE_PROFILE.md) for reconstructing
  Markdown observations

This contract governs case *assembly*. It does not adjudicate. Adjudication
of an assembled case is specified by
[`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
It does not prescribe a UI or an agent.

v0 identity:

```text
contract:   governance_case/v0
artifact:   GovernanceCase
sidecar:    governance.case.json     (application sidecar; not a World)
API:        assess_authority_change_impact
            assemble_governance_case
            assess_authority_governance   (orchestrator; stages remain distinct)
```

The v0 writer lives in `ontology_author.authority.impact` and
`ontology_author.authority.case`. Change-impact sidecar:
`authority.impact.json`.

## Architectural position

```text
PROGRAM DELTA
        ↓
ATTACHMENT MAINTENANCE          AttachmentMaintenanceAssessment
        ↓
CHANGE IMPACT                   AuthorityChangeImpact
        ↓
CASE ASSEMBLY                   GovernanceCase
        ↓
ADJUDICATION                    GovernanceAdjudication
                                GOVERNANCE_ADJUDICATION_CONTRACT.md
```

Keep these meanings distinct:

```text
attachment maintenance
    validity/support of the persisted mapping

change impact / relevance
    did this ProgramDelta touch the program surface this
    authority relationship governs?

case selection
    whether original authority belongs in the assembled case

adjudication
    what the authority implies for the changed program
```

Maintenance is specified in
[`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md).
This contract consumes it. It MUST NOT treat `HOLD` as “not relevant.”

The normal path is **selection, not discovery**.

```text
SEARCH / INTERPRET
      ONCE                       (authority construction)
       ->
     PERSIST                     (attachments, warrants, relevance scopes)
       ->
   SELECT MANY TIMES             (this contract)
```

Case assembly MUST NOT decide whether the change is allowed.

It MUST NOT search, grep, embed, or RAG the authority corpus in the happy
path. Search MAY exist later as a repair/exception path; it is **DEFERRED**
and MUST be labeled as such if ever added.

## Maintenance is not relevance

An attachment may remain perfectly valid while the implementation it governs
changes substantially.

```text
authority:  Cancellation occurs only after final confirmation.
attachment: → cancelSubscription
delta:      cancelSubscription implementation changes
mapping:    still correctly points to cancelSubscription
```

Maintenance may be `HOLD`. The authority may still need to enter the case.

Another shape:

```text
ADR:        Checkout must access payment providers through PaymentGateway.
attachment: → CheckoutPayment
delta:      a new direct call to StripeClient is added inside CheckoutPayment
```

The attachment did not become stale. Its continued validity is why the ADR
is relevant.

Do not implement case selection as:

```text
maintenance_action ≠ HOLD
```

The relevance surface is not a formal compliance rule. It exists only for
deterministic case selection. It answers:

```text
should this original authority be presented to an adjudicator
for this mechanical change?
```

not:

```text
does this change violate the authority?
```

Do not compile prose into executable prohibitions merely to solve selection.

## Explicit non-goals

Do not implement or require:

- adjudication outputs (`PASS`, `FAIL`, `COMPLIANT`, `VIOLATION`,
  `ALLOWED`, `PROHIBITED`);
- attachment migration or automatic reattachment;
- LLM re-resolution;
- source-authority lineage;
- policy enforcement;
- agent prompting, semantic search, RAG, Git diff ingestion, UI;
- new spine capabilities or domain predicates;
- kernel case tables, cross-World joins, or lineage primitives;
- interactive “expand more context” (adjudication MAY emit a
  `ContextRequest`; satisfying it is deferred);
- compiling authority prose into watch queries, prohibition rules, or a
  policy engine;
- treating every descendant of an attached module as automatically relevant.

## Inputs

```text
old governed World
new program-spine World          authority need not be copied into it
spine.comparison.json
authority.maintenance.json       AttachmentMaintenanceAssessment per warrant
authority.impact.json            AuthorityChangeImpact per warrant
AuthorityConstructionReceipt
authorized source files          at the revisions recorded in the old World
                                 (unchanged this milestone)
```

Application-level assembly MAY read those artifacts and write a sidecar.
No kernel cross-World join is required.

## Output topology

One comparison produces one `GovernanceCase` sidecar:

```text
.worlds/<name>/world/                 old governed World (untouched)
<new-spine>/world/                    new program World (untouched)
spine.comparison.json
authority.maintenance.json
authority.impact.json
governance.case.json
```

The case is self-contained JSON. It copies the selected original text,
claim tuples, and mechanically relevant program tuples into the sidecar so
a later adjudicator need not rediscover why the material is relevant.

When a selected attachment already has persisted semantic/program
relationships in the governed World, the case also projects a bounded
`semantic_context` section:

```text
semantic_context:
    referents[]
    claims[]
    program_links[]
```

These are copied World facts, not new assertions. Each item records its
`included_because` reason and source observation references. The selector
starts with semantic referents directly present in the selected attachment,
adds source-derived claims sharing the selected authority observations, and
adds old-side semantic/program links only for the bounded changed context.
It does not traverse the whole semantic graph or infer meaning from
identifier labels.

For a changed endpoint, the case may record an explicit new-side absence.
`POSITIVE`, `ABSENCE_WITH_COMPLETE_COVERAGE`, and
`ABSENCE_WITHOUT_COMPLETE_COVERAGE` remain distinct. The latter is not a
negative semantic proposition. A complete negative conclusion is emitted
only when a matching semantic/program-link completeness fact already exists
in the governed World.

Where the selected relevance scope already exposes a mechanical old/new
value, the case may also include a bounded `transition_facts[]` projection.
This is derived from the comparison and creates no World assertion. It does
not establish semantic meaning that authority construction did not persist.

When a caller selects the Checkout provider-boundary invariant, the case may
also include `invariant_context` with the durable definition plus baseline
and candidate `ScopedInvariantDerivation` records. This is copied evaluator
output, not semantic rediscovery. Candidate derivation `program_invokes`
facts are also copied into `program_context.relation_tuples` so an
adjudicator can cite them as mechanical program evidence. The case should
prefer that candidate derivation over interpreting absence of the old finite
invariant commitment. See
[SEMANTIC_SCOPED_INVARIANT_EVALUATOR.md](SEMANTIC_SCOPED_INVARIANT_EVALUATOR.md).

It is not a World. It does not replace either snapshot. It does not copy
attachments into the new spine.

## Warrant dependencies vs relevance dependencies

These are different surfaces.

### Warrant dependencies

Justifies:

> why does this authority attach to this program manifestation?

Recorded on `authority_attachment_warrant`. They drive
`AttachmentMaintenanceAssessment`. Examples: attached identity, listed
structural context, `program_invokes(C, openRetentionFlow)`, recorded
resolution outcome.

### Relevance / selection dependencies

Describe:

> which mechanical program changes should cause this authority to be
> considered for a governance case?

They need not be identical to the warrant. Example: authority →
`cancelSubscription` may have a warrant of identity/context only, while
implementation changes of that callable still make the authority relevant.

Recorded on `authority_relevance_scope`, not by silently extending the
warrant. See
[`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md).

Do not infer relevance from file proximity, module containment, or “any
relation that mentions the entity” unless that clause is explicit.

## AuthorityChangeImpact

Application-level record, not a kernel type. Sidecar:
`authority.impact.json`. One record per old warrant (same subjects as
maintenance).

It answers:

> Given ProgramDelta and a persisted authority/program attachment, did the
> changed program intersect the program surface for which this authority
> relationship is relevant?

| `impact` | Meaning |
| --- | --- |
| `AFFECTED` | At least one declared relevance-surface fact mechanically changed. |
| `UNAFFECTED` | Every declared surface fact is comparable and none of those facts changed. |
| `UNKNOWN` | Comparison left a surface fact unresolved; cannot tell whether it changed. |
| `NOT_COMPARABLE` | A capability required by the surface cannot be compared. |

No compliance vocabulary. No numeric relevance score.

Required fields:

```text
attachment_assertion_id
warrant_assertion_id
old_program_entity
candidate_new_manifestations[]
scope_source                    PERSISTED | DEFAULT_KIND_RULE
scope_clauses[]                 the clauses actually used
impact
intersecting_deltas[]           ProgramDelta entries that justified AFFECTED
limitations[]
```

Derivation (worst-case; evaluate in order):

```text
any required surface capability NOT_COMPARABLE / NOT_PRODUCED
    → NOT_COMPARABLE

any surface fact in a relation/identity bucket unresolved
    → UNKNOWN

any surface fact in added / removed / retargeted
    or listed manifestation property CHANGED
    → AFFECTED

otherwise
    → UNAFFECTED
```

`HOLD` maintenance plus `AFFECTED` impact is a normal, expected pair.

### v0 relevance clauses

| `clause_kind` | Meaning |
| --- | --- |
| `ATTACHED_IDENTITY` | Correspondence/identity delta of the warrant’s `program_entity`. Unique continuation alone is not an impact hit. Removal, split, merge, ambiguous, or no-match is. |
| `IDENTITY_MANIFESTATION` | Named comparable manifestation properties of that identity (and of a unique continuation): e.g. `signature`, `source_manifestation`. |
| `ENDPOINT_RELATION` | Named native relation tuples where the attached identity (or unique continuation) is an endpoint. |
| `STRUCTURAL_SCOPE` | Identity or relation delta on structural descendants of an explicitly declared root. **Only if construction declared it.** |
| `EXPLICIT_IDENTITY` | Additional named program identities treated like extra `ATTACHED_IDENTITY` roots, with optional extra clauses. |

Do not adopt an implicit “whole file” or “whole module body” clause.

### Default selection surface (fine-grained)

If construction persisted no `authority_relevance_scope` rows for an
attachment, case assembly MUST apply the kind default and record
`scope_source: DEFAULT_KIND_RULE`. Construction SHOULD materialize the
default so the World is explicit; missing rows are a known omission, not a
license to invent a broader watch.

| Attached kind | Default clauses |
| --- | --- |
| `call_site` | `ATTACHED_IDENTITY`; `ENDPOINT_RELATION program_invokes` |
| `callable` / `method` | `ATTACHED_IDENTITY`; `IDENTITY_MANIFESTATION {signature, source_manifestation}`; `ENDPOINT_RELATION program_invokes` (the callable as target) |
| `module` / `source_unit` | `ATTACHED_IDENTITY`; `ENDPOINT_RELATION program_imports` |
| other kinds | `ATTACHED_IDENTITY` only |

Defaults do **not** include: source-location-only moves, name-only renames,
boundary unless listed, or structural descendants.

A callable body/implementation change is typically
`source_manifestation CHANGED` → `AFFECTED` even when the warrant never
listed source manifestation.

A payment-boundary ADR attached only to a module MUST persist extra clauses
(`EXPLICIT_IDENTITY`, `STRUCTURAL_SCOPE`, or further `ENDPOINT_RELATION`)
if inner calls should select. The default will not watch every descendant
call site. That is intentional minimality, not a finding that the ADR is
inapplicable in the adjudicator’s sense.

`STRUCTURAL_SCOPE` is retained only as an **opt-in** construction clause.
It MUST name the root identity and the capabilities/relations it covers.
It MUST NOT be the module default.

## What counts as considered / selected

### Considered

Every `authority_attachment_warrant` in the old World whose
`program_snapshot_id` matches the comparison’s old snapshot.

Unresolved construction records (`authority_unresolved`) are **not**
attachments. They MAY appear in the case’s uncertainty section when a
changed identity is listed as an unresolved candidate; they MUST NOT enter
the authoritative portion.

### Selected

Select a considered attachment when **at least one** of:

```text
1. attachment support changed or cannot be assessed
   maintenance_action ∈ {RERESOLVE, CANNOT_ASSESS}

2. attachment remains supported but its declared relevance surface
   was mechanically affected
   maintenance_action = HOLD
   AND impact = AFFECTED

3. impact cannot be determined
   impact ∈ {UNKNOWN, NOT_COMPARABLE}
```

`selected_because` MUST list every firing reason:

```text
ATTACHMENT_GROUNDS_CHANGED         maintenance RERESOLVE
ATTACHMENT_GROUNDS_UNASSESSABLE    maintenance CANNOT_ASSESS
GOVERNED_SURFACE_CHANGED           impact AFFECTED
GOVERNED_SURFACE_UNKNOWN           impact UNKNOWN
GOVERNED_SURFACE_NOT_COMPARABLE    impact NOT_COMPARABLE
```

`ATTACHMENT_SUPPORT_UNKNOWN` is the earlier spelling of
`ATTACHMENT_GROUNDS_UNASSESSABLE`. v0 emits the latter.

Both grounds-changed and surface-changed MAY fire together.

### Not selected merely because

```text
the same file changed somewhere else
the same module contains another changed function
source byte offsets shifted
a name/rename occurred
an unrelated native relation on a neighboring identity changed
```

unless that fact is on the **declared relevance surface** (or, for
maintenance, a warrant dependency). File proximity is never a clause.

`ProgramDelta.maintenance.relations_changed` is too coarse and MUST NOT be
the selection predicate.

Heuristic correspondence alone does not select. Renewal remains forbidden
by the maintenance contract regardless of selection.

### Direct and semantic-mediated

Selection keys off the **program-involving** warrant (`SOURCE_PROGRAM` or
`SEMANTIC_PROGRAM`).

For `SOURCE_PROGRAM`, include that claim and its evidence.

For `SEMANTIC_PROGRAM`, include:

- the SEMANTIC_PROGRAM claim, warrant, maintenance, and impact;
- the semantic referent;
- SOURCE_SEMANTIC / SOURCE_PROPOSITION claims that involve that semantic
  referent and share support with the attachment (same governing evidence
  set, or claims the warrant’s assertion lists via grounding / claim
  index);
- their exact observations.

Do not walk the entire semantic neighborhood. Do not include every claim
that merely mentions the same source file.

Several program attachments MAY share one semantic referent. Deduplicate
observations; preserve `selected_because` attachment IDs.

## Selection algorithm

Deterministic, no search:

```text
1. Load ProgramDelta, correspondence, maintenance assessments, impacts.
2. Consider all old warrants for the old snapshot.
3. Compute or load AuthorityChangeImpact from authority_relevance_scope
   (or the kind default).
4. Select when the selected predicate holds.
5. For each selected warrant, collect:
     attachment claim, warrant
     AttachmentMaintenanceAssessment
     AuthorityChangeImpact
     selected_because
     program endpoints (old; new candidates)
     warrant relation tuples and relevance-surface tuples that intersected
     structural context IDs listed on the warrant, old and continued
     semantic referent if SEMANTIC_PROGRAM
     source-derived claims attached as above
     SourceObservations of those claims
6. Reconstruct literal text for each observation at the recorded revision.
7. Partition observations by standing (AUTHORITATIVE vs other).
8. Deduplicate observations by (provider, handle, revision, native_location).
9. Include comparison/capability limitations that intersect selected
   warrant dependencies or relevance clauses.
10. Compute case_result from selection ∪ attachment completeness
    ∪ impact determinability (see empty-case semantics).
11. Write GovernanceCase.
```

If reconstruction fails (missing bytes or digest mismatch), record
`reconstruction: FAILED` with the observation pointer. Do not paraphrase.

## GovernanceCase schema

Conceptual record. Field names are normative for v0 JSON.

```text
case_id
contract: governance_case/v0
assembly:                         embedded CaseAssemblyReceipt (see below)

case_result:
  SELECTED
  | NO_APPLICABLE_AUTHORITY
  | NO_ATTACHMENT_FOUND
  | UNRESOLVED

change:
  old_snapshot_id
  new_snapshot_id
  comparison_id
  triggering_deltas[]             ProgramDelta entries that justified
                                  a selected warrant-dependency change
                                  or a selected relevance-surface hit
                                  each copied row has a stable evidence_id
  comparison_limitations[]        capability NOT_COMPARABLE / partial that
                                  touched a considered warrant or surface

program_context:
  referents[]                     old/new IDs actually cited
  structural_context[]            warrant-listed chains only
  relation_tuples[]               justifying warrant tuples and
                                  intersecting relevance-surface tuples,
                                  with matching new delta rows; copied rows
                                  have stable evidence_id values
  resolution_outcomes[]           justifying old/new resolution rows with
                                  stable evidence_id values
  boundary[]                      only if it was a warrant dependency
  source_evidence[]               bounded program source regions;
                                  see program-source inclusion.
                                  Assembled from spine grounding and
                                  digest-addressed snapshot input blobs.

authority:
  observations[]                  AUTHORITATIVE only
    handle, revision, standing, native_location
    reconstructed_text            literal bytes decoded as the driver requires
    reconstruction                OK | FAILED
  claims[]                        governing source-derived / attachment claims
    assertion_id, relation_name, tuple, claim_kind, relation_support
    endpoint_resolution
  semantic_referents[]            where involved

supporting_material[]             AVAILABLE / ANALYSIS_SUPPORT only,
                                  explicitly labeled; omitted unless a
                                  selected claim was grounded there
                                  (should not happen for governing claims)

selection[]:
  attachment_assertion_id
  warrant_assertion_id
  maintenance_assessment_ref
  change_impact_ref
  selected_because[]              ATTACHMENT_GROUNDS_CHANGED
                                  | ATTACHMENT_GROUNDS_UNASSESSABLE
                                  | GOVERNED_SURFACE_CHANGED
                                  | GOVERNED_SURFACE_UNKNOWN
                                  | GOVERNED_SURFACE_NOT_COMPARABLE
  selection_path                  warrant-dependency and/or relevance-clause
                                  facts that fired, with delta buckets
  semantic_referent?
  observation_ids[]

uncertainty:
  heuristic_correspondences[]
  ambiguous_continuations[]
  unresolved_construction[]       authority_unresolved intersecting the change
  maintenance_cannot_assess[]
  impact_unknown[]
  impact_not_comparable[]
  reconstruction_failures[]
  completeness_limitations[]

conflicts[]                       two or more AUTHORITATIVE claims selected
                                  whose tuples concern the same change;
                                  recorded, not resolved
```

No opaque relevance score. No PASS/FAIL.

### Why this authority was selected

Each `selection[]` row MUST make this inspectable, including when
maintenance is `HOLD`:

> this paragraph is here because the governed callable’s
> `source_manifestation` changed.

or:

> this paragraph is here because this attached call site’s
> `program_invokes` relation changed.

`selection_path` names the firing axis (`warrant` or `relevance`), the
clause or dependency kind, the old fact, the delta bucket, and the
assessment ids.

## Standing

Only `AUTHORITATIVE` material enters `authority.observations` and governing
`authority.claims`.

`AVAILABLE` and `ANALYSIS_SUPPORT` MUST NOT appear there. If construction
incorrectly grounded a governing claim on them, assembly MUST move that
observation to `supporting_material` with standing visible, and MUST record
a known omission: governing standing was not licensed.

Supporting material MUST be labeled so it cannot be mistaken for
AUTHORITATIVE.

## Multiple authority sources

A single program change MAY select several regions. Do not merge them into
a synthetic rule.

Preserve per observation:

```text
standing
source identity (handle)
revision
exact reconstructed text
claim/support provenance
```

If selected governing claims appear inconsistent, append `conflicts[]`
naming the claims and observations. Conflict resolution is adjudication or
later authority policy. Assembly includes the conflict.

## Case minimality / expansion

Include:

```text
the changed justifying relation (old and new counterpart if any)
its endpoints that participate in the tuple
the attached semantic referent when the attachment is mediated
the attachment warrant
the exact grounding paragraphs of the selected claims
the maintenance assessment and the change-impact assessment
structural owners listed on the warrant
relevance-surface tuples that intersected the delta
bounded program source evidence when the inclusion rules fire
```

Do not automatically include:

```text
the entire module
the entire Markdown document
every authority claim sharing the source file
the entire program graph
all program_invokes of the owning callable
HOLD + UNAFFECTED attachments
unrelated completeness receipts
```

Goal:

> sufficient context with minimal unrelated material.

If more context is needed later, adjudication MAY emit a `ContextRequest`
as specified in
[`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
Deterministic case expansion that satisfies such a request is **DEFERRED**.
The adjudicator MUST NOT search the repository to fill the gap.

## Empty cases and completeness

An empty selected set does **not** mean “no governance applies.”

Do not conclude no authority merely because every existing attachment
received maintenance `HOLD`. A `HOLD` attachment may still be `AFFECTED`.

Reuse existing attachment-coverage completeness from the old World
(`authority_attachment_coverage` / `authority_completeness` scope
`ATTACHMENT`, plus the World completeness receipt over
`authority_attachment_scope`).

Let `U` be the declared attachment universe for the construction purpose
(the program identities listed in `authority_attachment_scope` for that
purpose).

Let `D` be the set of old program identities that appear in ProgramDelta as
removed, retargeted-endpoint, ambiguous, unresolved, manifestation-changed,
or newly related in a comparable capability — the identities the change
actually touched.

`NO_APPLICABLE_AUTHORITY` requires enough completeness to know that **no
authoritative attachment or relevance surface applies to the changed
program region** for the declared purpose, not merely that mappings did
not go stale.

| Situation | `case_result` |
| --- | --- |
| At least one warrant selected | `SELECTED` |
| No warrant selected; every considered impact is `UNAFFECTED`; none has maintenance `CANNOT_ASSESS`; `D ⊆ U`; attachment coverage `COMPLETE` over `U` with no known gaps that cover `D` | `NO_APPLICABLE_AUTHORITY` |
| No warrant selected, and (`D` not ⊆ `U`, or coverage is not `COMPLETE`, or known gaps intersect `D`) | `NO_ATTACHMENT_FOUND` |
| No warrant selected, but some considered impact is `UNKNOWN` or `NOT_COMPARABLE`, or some considered maintenance is `CANNOT_ASSESS`, or comparison cannot tell whether a surface in `U` was hit | `UNRESOLVED` |

`NO_APPLICABLE_AUTHORITY` is the only empty result that MAY be read as
“absence licensed for this purpose/universe.” It is still not a PASS. It
does not mean the code is acceptable.

`NO_ATTACHMENT_FOUND` MUST NOT be treated as no governance. Completeness
was insufficient to conclude absence.

`UNRESOLVED` MUST NOT look like a compact negative. Record the comparison,
maintenance, or impact limitation.

Addressability or construction-coverage completeness MUST NOT license
`NO_APPLICABLE_AUTHORITY`. Only attachment coverage over `U`, plus
determinable `UNAFFECTED` impact on every considered attachment, may.

Unattached program identities remain ordinary spine members. Absence of
attachment is not irrelevance, except where attachment completeness
explicitly covers that universe **and** declared relevance surfaces do not
hit the change.

## Case assembly receipt

Prefer the simplest model: **the case carries its own receipt** as
`assembly`. A separate `CaseAssemblyReceipt` file is unnecessary in v0.

```text
assembly:
  receipt_version: governance_case_receipt/v1
  case_id
  mechanism_id / mechanism_version
  old_snapshot_id / new_snapshot_id
  comparison_id
  purpose
  triggering_delta_refs[]
  warrants_considered
  warrants_selected
  selected_because_counts
  assessments_hold
  impacts_affected / impacts_unaffected / impacts_unknown
  observations_selected
  semantic_referents_involved
  program_referents_included
  unresolved_or_ambiguous_items
  completeness_basis               receipt ids + universe + status
  known_omissions[]
  selection_mechanism: governance_case/v0
```

Counts are inspection aids. They MUST NOT imply that all future governance
questions are solved.

## Worked examples

These do not adjudicate.

### Example 1 — cancellation invocation retarget

```text
CancellationEntryAction -> call_site C
warrant: C invokes openRetentionFlow
delta:   C invokes cancelSubscription
```

```text
maintenance:    RERESOLVE
change impact:  AFFECTED          (ENDPOINT_RELATION program_invokes retargeted)
case_result:    SELECTED
selected_because:
  ATTACHMENT_GROUNDS_CHANGED
  GOVERNED_SURFACE_CHANGED
```

Case contains old/new call site and targets, reconstructed paragraph 1,
`CancellationEntryAction`, and the path that the warrant’s
`program_invokes` tuple retargeted. Do **not** include paragraph 2 unless
another selected warrant depended on it. Do **not** say whether the new
code violates the requirement.

### Example 2 — HOLD but AFFECTED (governed implementation changed)

```text
authority:   cancellation requires final confirmation
attachment:  → cancelSubscription callable
warrant:     callable identity / context
ProgramDelta:
  callable CONTINUED + HEURISTIC
  structural context preserved
  source_manifestation / body changed
```

```text
maintenance:    HOLD
                NO_RENEWAL
change impact:  AFFECTED          (IDENTITY_MANIFESTATION source_manifestation)
case_result:    SELECTED
selected_because:
  GOVERNED_SURFACE_CHANGED
```

The authority enters the case because the governed program changed, not
because the attachment became stale.

### Example 3 — HOLD and UNAFFECTED (neighboring helper)

```text
attachment:  → cancelSubscription
change:      formatSubscriptionDate helper changed
```

No recorded relevance connection.

```text
maintenance:    HOLD
change impact:  UNAFFECTED
case:           not selected
```

This preserves case minimality.

### Example 4 — ambiguity / not comparable

If correspondence or a required surface capability cannot tell whether the
governed program surface changed:

```text
change impact:  UNKNOWN | NOT_COMPARABLE
case_result:    SELECTED
selected_because:
  GOVERNED_SURFACE_UNKNOWN
  or GOVERNED_SURFACE_NOT_COMPARABLE
```

If maintenance also cannot uniquely continue, add
`ATTACHMENT_GROUNDS_CHANGED` or `ATTACHMENT_GROUNDS_UNASSESSABLE`. Expose
candidates and limitations. Do not choose a winner. Do not omit the case.

### Example 5 — empty case vs unknown absence

ProgramDelta changes an unattached helper `H`. Every constructed attachment
is `HOLD` and `UNAFFECTED`.

If `H ∈ U` and attachment coverage is `COMPLETE` over `U`:

```text
case_result: NO_APPLICABLE_AUTHORITY
```

If `H ∉ U`, or coverage is not `COMPLETE`, or known gaps cover `H`:

```text
case_result: NO_ATTACHMENT_FOUND
```

If calls comparison is `NOT_COMPARABLE` so a callable attachment’s
`source_manifestation` or `program_invokes` surface cannot be assessed:

```text
case_result: UNRESOLVED
```

even if the selected set is empty. `HOLD` on the mapping is not enough.

## Kernel reuse

| Need | Reuse |
| --- | --- |
| IDs | snapshot-local referents from each World |
| Claims | named typed relations + assertion IDs |
| Exact evidence | SourceObservation + driver reconstruct |
| Standing | `authority_source` (not grounding) |
| Completeness | existing ATTACHMENT-scope receipts |
| Open-world | empty-case trichotomy above |
| Unresolvedness | `authority_unresolved`, comparison UNRESOLVED, maintenance `CANNOT_ASSESS`, impact `UNKNOWN` / `NOT_COMPARABLE` |
| Construction origin | left on claims; not re-derived |
| Sealed Worlds | read-only inputs |
| Sidecar receipts | case embeds assembly receipt |

Experimental kernel `Obligation` / `Adjudication` MUST NOT be reused as
`GovernanceCase`. Mapping those words onto this artifact would lie about
who decided what.

## Kernel limitations

No new kernel primitive is required unless a later implementation cannot
represent exact reconstructed evidence, standing separation, or the
empty-case trichotomy without lying.

Known limits:

1. No cross-World FK. The case copies cited tuples by value.
2. No Claim primitive. The case lists assertion IDs and tuples.
3. Completeness cannot honestly mean “the corpus is understood.”
4. Kernel staleness is not ProgramDelta.
5. JSON warrant lists and relevance-scope rows remain application structure.

Awkward assembly is not a kernel case.

## Program-source evidence (case amendment)

Adjudication needs exact program source for some triggers and only
mechanical tuples for others. Inclusion is a case-assembly duty, using
existing spine grounding — not adjudicator search.

Include reconstructed source for identity `I` when any of:

```text
selected IDENTITY_MANIFESTATION hit on I
  (source_manifestation or signature CHANGED)
ambiguous continuation of a selected identity
  (old identity and every recorded candidate)
selected EXPLICIT_IDENTITY / STRUCTURAL_SCOPE
  whose manifestation change fired
warrant-listed source-manifestation dependency CHANGED
```

Reconstruct the identity's own `SourceObservation` byte range for
`OLD` / unique `NEW` / each `CANDIDATE`. Do not dump files or modules.

Do **not** include bodies merely because a call-site `program_invokes`
tuple retargeted. The relation is usually sufficient.

On reconstruction failure, record `FAILED`. Do not grep a replacement.

Normative field:

```text
program_context.source_evidence[]:
  evidence_id
  program_entity
  side                    OLD | NEW | CANDIDATE
  observation             provider, handle, revision, native_location
  reconstructed_text
  reconstruction          OK | FAILED
  inclusion_reason        MANIFESTATION_CHANGED
                          | AMBIGUOUS_CANDIDATE
                          | EXPLICIT_SCOPE_IDENTITY
                          | WARRANT_MANIFESTATION_DEPENDENCY
```

The v0 case writer emits `source_evidence[]` when inclusion rules fire.
Reconstruction uses sealed `program_inputs` blobs, not workspace search.
If reconstruction fails, the case remains valid with a known omission.
Details: [`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).

## Intentionally deferred

- Deterministic expansion that satisfies an adjudication `ContextRequest`.
- Repair-path search when selection is `UNRESOLVED` or reconstruction fails.
- `AuthorityDelta` / source revision maintenance.
- Persisting selected attachments onto a new governed World.
- Policy compilation.
- Whether repeated case shapes should become ordinary derivations.

Success condition for this design:

> attachment validity and governance relevance are represented
> independently, so a still-valid authority relationship can correctly
> enter a case when the program it governs changes, while unrelated
> neighboring changes do not create noisy cases; exact original authority
> is assembled without searching the corpus or silently migrating claims.
