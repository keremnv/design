# Authority construction contract

This document defines how authoritative non-code material is constructed into
durable semantic and program relationships. It is subordinate to
[`FOUNDATIONS.md`](FOUNDATIONS.md),
[`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md), and
[`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md). It consumes the
program spine defined by [`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md)
and the comparison/maintenance hooks in
[`SPINE_COMPARISON_CONTRACT.md`](SPINE_COMPARISON_CONTRACT.md).
Program-side attachment maintenance and governance-case assembly are specified
by [`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md) and
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md). Adjudication of
an assembled case is specified by
[`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
Semantic construction admission and snapshot/commitment maintenance are
specified by
[`SEMANTIC_PERSISTENCE_CONTRACT.md`](SEMANTIC_PERSISTENCE_CONTRACT.md).
This document does not implement those stages.

It governs durable output. It does not prescribe a constructor implementation,
a parser, a model, or a universal ontology.

Markdown is the first concrete source driver. Addressability mechanics for
Markdown live in [`MARKDOWN_SOURCE_PROFILE.md`](MARKDOWN_SOURCE_PROFILE.md).
Markdown-specific mechanics are not part of this universal contract.

The normative words **MUST**, **MAY**, and **DEFERRED** have their usual
contract meaning. Changing the meaning of a named standing, support class,
resolution class, completeness scope, or receipt field requires a new
contract version.

The v0 implementation lives in `ontology_author.authority`. It writes
authority facts into a candidate copy of a sealed program-spine World so
program identities remain first-class referents in the same governed World.

## Architectural position

```text
AUTHORITATIVE SOURCE
        |
        | exact addressable evidence
        v
CONSTRUCTION
        |
        +--> claims / propositions
        |
        +--> semantic identities where genuinely useful
        |
        +--> relationships to program identities
        v
GOVERNED WORLD
```

The World is a grounded semantic index over authority. It is intentionally
lossy. Original source remains authoritative. Construction does not translate
authoritative material into a replacement rule language.

The objective is:

> preserve enough durable semantic structure to recover the relevant original
> authoritative evidence when the program changes.

Do not attempt lossless natural-language formalization.

The architecture has three contract layers:

```text
authority_construction/v0
  epistemic, provenance, identity-plane, completeness, and receipt guarantees

source drivers
  versioned addressability/revision contracts owned by a provider family

construction profiles
  purpose-scoped construction that selects, interprets, and attaches
```

A source driver answers:

```text
What can I address?
```

It does not answer:

```text
What does this region mean?
```

A construction profile answers which examined regions, claims, identities, and
attachments are worth persisting for a declared purpose.

## Explicit non-goals

This contract does not implement or require:

- a Markdown parser or any other source driver;
- semantic extraction as a product feature;
- an LLM constructor;
- source adapters beyond the driver/profile boundary;
- claim maintenance (specified separately; not this construction contract);
- adjudication (specified separately;
  [`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md));
- policy or rule compilation;
- Figma, Storybook, Git-diff ingestion, frontend/UI; or
- generic knowledge-graph machinery.

It does not add program-analysis capabilities. It does not create a universal
semantic vocabulary.

## Core principle

```text
original source
        remains
authoritative evidence

normalized World structure
        is
an index, not a substitute
```

When a source sentence is normalized into a relation, the exact source region
MUST remain reconstructibly addressable. Normalization MAY lose linguistic
nuance only because original evidence remains available to later
adjudication.

## Evidence, claims, and identities

These are different things:

```text
EVIDENCE
    authoritative source regions / source-native objects

CLAIMS
    propositions or relationships supported by evidence

IDENTITIES
    semantic referents and program referents
    source-native referents only where a provider supplies useful object identity
```

The identity invariant remains:

```text
source identity != semantic identity != program identity
```

“Source identity” means source-native object identity where it exists. It does
not mean that every addressable source region has an identity of its own.

### Strong invariant

> Addressable source evidence is not automatically a semantic or source
> referent.

Discourse boundaries, proposition boundaries, and entity boundaries are
different kinds of boundary. A source region can ground a claim without
becoming a referent.

For prose drivers such as Markdown, structures such as document, heading,
section, paragraph, and span are normally evidence locations. They MUST NOT
become persistent semantic identities merely because a noun phrase or heading
exists.

Some future structured sources MAY supply genuine source-native identities.
The contract allows that without treating Markdown paragraphs as equivalent.

## Authorized source universe

The user or application declares the authorized source universe. The
constructor MUST NOT treat arbitrarily discovered files as authoritative
merely because they are relevant.

```text
user-declared authoritative sources
        ↓
source drivers / addressability
        ↓
available authoritative evidence universe
```

This is analogous to the program-universe boundary. The constructor expands a
declaration into effective sources and addressable evidence. It does not
choose the authority boundary.

### Standing

A declared source MUST have exactly one standing:

| Standing | Meaning |
| --- | --- |
| `AUTHORITATIVE` | May ground governing source-derived claims. |
| `AVAILABLE` | May be inspected during construction. Claims grounded only here are not governing. |
| `ANALYSIS_SUPPORT` | Used to address, parse, or interpret. Never governing. |

This distinction is required now. Grounding is not authority. A README, a
generated catalog, a fixture, and a policy document may all be inspectable
while having different governance standing.

A source MAY be available for construction without being authoritative.

### Universe membership is explicit

The generic referent table is not the authorized source universe. Membership
MUST be an explicit application relation for the construction, tentatively:

```text
authority_source
```

Each member records at least:

```text
source identity
provider / driver
native handle
source revision / content digest
standing
```

Support material and merely available material MUST NOT silently become
`AUTHORITATIVE`.

### Revision

A source revision is the immutable content identity used for reconstruction.
A driver owns the digest/revision convention. Optional observational metadata
such as a Git commit MAY be recorded; it is not a substitute for content
identity.

Changing declared membership, standing, or revision is a new authorized
universe. It is not a silent in-place edit of an existing construction.

## Source drivers

A source driver is versioned addressability machinery. It MUST:

- identify sources in the declared universe that it can address;
- produce reconstructible coordinates for native regions or objects;
- preserve literal source fidelity for selected evidence;
- disclose known addressability losses;
- record explicit source-native relationships that the provider actually
  exposes, without interpreting them as World meaning.

A driver MUST NOT:

- construct semantic referents;
- attach regions to program identities;
- treat every addressable region as a World object;
- persist an elaborate source IR unless a concrete need appears.

Principle:

```text
Parse eagerly, select deterministically, interpret lazily.
```

Driver output MAY be ephemeral construction machinery. Durable World state
persists selected evidence pointers, not a copy of the driver’s full parse.

Markdown v0 is specified in
[`MARKDOWN_SOURCE_PROFILE.md`](MARKDOWN_SOURCE_PROFILE.md). Future drivers
(structured specifications, issue systems, Storybook, Figma, API schemas) MUST
satisfy this driver boundary with their own profiles.

## Source-native identity policy

A source-native referent MAY exist only when the provider supplies useful
object identity that is worth retaining independently of a byte range. Examples
include issue IDs, schema objects, API operations, and design-node IDs.

The exact source observation remains evidence addressing that object. Object
identity and evidence addressing are still distinct.

A driver that has no useful native object identity MUST produce evidence
locations only. Markdown headings, sections, paragraphs, and spans are in this
class unless a future Markdown profile proves a concrete native-identity need.

## Semantic referents are constructed commitments

A semantic referent is not an entity discovered in prose. It is an identity
introduced because preserving it independently of one source wording and one
program manifestation is useful.

Approximate test, which implementations SHOULD freeze in construction
profiles:

> Would we still want to talk about this thing if both its current source
> wording and current code manifestation were renamed or replaced?

If not, a direct evidence→program claim is preferable.

A semantic referent SHOULD earn persistence through at least one of:

- several sources referring to the same thing;
- authority connecting to several program manifestations;
- survival across implementation replacement;
- multiple claims concerning it;
- repeated governance need to refer to it.

Do not create a semantic node for every noun phrase or source section.

Semantic IDs are application-level, not kernel identity. A construction
profile owns the namespace. Snapshot-local program IDs remain program
identities; they MUST NOT be reused as semantic IDs.

## Direct and mediated attachment are both valid

```text
source evidence
    -> program referent
```

is valid when no independent semantic identity is needed.

```text
source evidence
    -> semantic referent
    -> program referent
```

is valid when semantic identity has earned persistence.

Do not force a symmetric ontology where every program object has a semantic
twin. Unattached program identities remain ordinary spine members. Absence of
attachment is not irrelevance.

## Source-derived claims

Natural-language authority often expresses propositions rather than entity
identity. One source region MAY contribute several claims. Construction MUST
NOT require every source sentence to become a formal assertion.

Prefer selective construction driven by governance usefulness.

A persisted source-derived claim MUST record:

- the exact original evidence region or regions;
- a normalized relationship or proposition if one is useful;
- qualifiers, modality, scope, conditions, and version/context where
  materially relevant;
- construction method and resolution provenance;
- involved referents where resolved.

Material qualifiers belong in explicit relation roles or companion facts, not
in unrecoverable constructor memory. If a qualifier is too subtle to
normalize honestly, leave it in the original wording and persist the evidence.

The generic kernel has no `Claim` primitive. A claim is an assertion tuple in
a named typed relation, with grounds stored separately. Domain relation names
are purpose-specific. This contract does not freeze a universal predicate
vocabulary.

### Claim kinds

Inspectable construction output MUST distinguish these kinds, even when they
are stored as ordinary World relations:

| Kind | Meaning |
| --- | --- |
| `SOURCE_PROPOSITION` | A source-supported proposition whose endpoints are semantic and/or program referents, or explicitly unresolved. |
| `SOURCE_SEMANTIC` | A relationship between source evidence and a semantic referent. |
| `SOURCE_PROGRAM` | A direct relationship between source evidence and a program referent. |
| `SEMANTIC_PROGRAM` | A relationship between a semantic referent and a program referent. |
| `UNRESOLVED_RECORD` | An explicit construction result that a region, endpoint, or attachment was not resolved. |

Source evidence remains in grounding, not as a fake referent, unless a
source-native identity exists.

### Never detach a normalized claim from original authority

> Every persisted source-derived claim MUST retain the exact authoritative
> evidence that supports it and the construction/resolution provenance that
> produced it.

The normalized World claim is an index, not a replacement for the source
wording. A claim whose only remaining trace is a paraphrase is a contract
failure.

Governing claims MUST be grounded in `AUTHORITATIVE` sources. Grounding in
`AVAILABLE` or `ANALYSIS_SUPPORT` material MUST NOT confer governing standing.

## Construction freedom and durable-claim rigidity

The constructor MAY be an intelligent coding agent. It MAY:

- inspect authoritative and available sources;
- search and grep;
- inspect the program spine;
- write reusable parsers and resolvers;
- follow links;
- use source-native structured APIs;
- introduce semantic identities where warranted;
- decline to resolve uncertain relationships.

The agent’s private reasoning is not persisted.

Persist observable provenance:

```text
exploration provenance
    what material and tools were inspected

support / basis provenance
    the smaller evidence set actually grounding the durable claim
```

Support/basis provenance is required for every persisted claim. Exploration
provenance belongs on the construction receipt and MAY appear on claims as
optional extra. It MUST NOT be substituted for support.

```text
freedom in investigation
rigidity in claims
```

## Derivation preference

Use this preference order. Do not force every construction through all
levels.

```text
explicit source-native relationship
    >
deterministically parsed relationship
    >
agent-authored reusable resolver
    >
reproducible heuristic
    >
one-off intelligent resolution
    >
unresolved
```

Repeated intelligent resolution SHOULD be a candidate for conversion into
reusable code. That is an optimization, not a requirement.

A later deterministic derivation from an inferred premise remains epistemically
dependent on that premise. Determinism does not launder inference.

## Relation support and referent resolution are separate axes

Do not collapse these into one confidence field. Do not use opaque numeric
confidence scores.

### Relation support

How the relationship itself is licensed:

| Class | Meaning |
| --- | --- |
| `SOURCE_NATIVE` | The source system structurally exposes the relationship. |
| `SOURCE_EXPLICIT` | The source states the relationship; intelligence mainly extracts or resolves endpoints. |
| `SOURCE_STRUCTURAL` | Organization, layout, or containment substantially establishes it. |
| `CROSS_EVIDENCE_INFERRED` | Intelligence combines multiple source or program facts. |
| `HYPOTHESIZED` | Plausible, not established strongly enough to be ordinary durable truth. |

`ConstructionOrigin.SEMANTIC` and `ConstructionOrigin.MECHANICAL` remain coarse
kernel labels. They MUST NOT erase this taxonomy.

A source assertion MAY be `SOURCE_EXPLICIT` while resolving its subject or
object still requires intelligence.

### Referent resolution

How an endpoint was bound to a durable identity:

| Class | Meaning |
| --- | --- |
| `NATIVE_ID` | Bound by a provider-native object identifier. |
| `DETERMINISTIC` | Bound by a declared deterministic rule from explicit source tokens or structure. |
| `SOURCE_DEFINED` | The source names or locates the referent in a driver-defined way that does not require open-ended interpretation. |
| `AGENT_RESOLVED` | Bound by intelligent construction, with inspectable support. |
| `AMBIGUOUS` | Multiple durable candidates remain. |
| `UNRESOLVED` | No durable endpoint is committed. |

`DETERMINISTIC` here means the endpoint binding is entailed by declared rules
over explicit source material. It is not a license to treat a heuristic
program correspondence as mechanically the same object.

Each persisted claim with endpoints MUST record a resolution class per
resolved or attempted role. An unresolved endpoint is preferable to a
fabricated link.

## Provenance and support model

Use existing kernel grounding. Do not copy source bodies into relation tuples.

For each persisted source-derived assertion:

```text
AssertionGrounding.observations
    one or more SourceObservation pointers to exact evidence

AssertionGrounding.construction_method
    driver, parser, resolver, or intelligent-resolution identifier

AssertionGrounding.extra
    authority_construction/v0 envelope
```

The v0 envelope MUST be able to carry:

```text
contract: authority_construction/v0
claim_kind
relation_support
endpoint_resolution          role → resolution class
authorized_source_ids
program_snapshot_id          when a program endpoint is involved
warrant_context              see correspondence section
constructor_id / profile
reusable_resolver_ids
```

`SourceObservation` addresses evidence. It does not confer standing. Standing
comes from `authority_source`.

Exploration provenance is receipt-level unless a profile chooses to store a
compact inspected-set digest on the claim. The support set MUST be the smaller
set that actually licenses the claim.

## Unresolved and ambiguous semantics

Unknown is first-class. Graph density is not a goal. An unresolved
construction is preferable to a fabricated link.

The constructor MUST be able to persist records for:

```text
this source region appears relevant but program attachment is unresolved

multiple program candidates remain

the proposition is understood but a durable semantic identity is not warranted

the source asserts a relation but one endpoint cannot be resolved
```

Recommended unresolved kinds:

| Kind | Meaning |
| --- | --- |
| `UNBOUND_REGION` | Examined, relevant, no durable claim selected. |
| `IDENTITY_NOT_WARRANTED` | Concept understood; no semantic referent created; no substitute fabrication. |
| `ENDPOINT_UNRESOLVED` | Relation understood; at least one endpoint unbound. |
| `AMBIGUOUS_REFERENT` | Candidate set retained; no silent winner. |
| `SPINE_SURFACE_MISSING` | Attachment purpose needs a program surface the spine does not expose. |
| `STANDING_INSUFFICIENT` | Material was useful but not `AUTHORITATIVE`. |

Unresolvedness is an ordinary inspectable construction result, not a kernel
unknown primitive. An empty query is not an unresolved record.

`HYPOTHESIZED` claims, if persisted at all, MUST remain labeled and MUST NOT
be treated as ordinary governing truth.

## Construction completeness

Do not claim that every paragraph in every authoritative source has been
semantically formalized.

Separate these scopes:

| Scope | Question | Typical universe |
| --- | --- | --- |
| Source addressability coverage | Can the declared source material be reconstructed and addressed? | `authority_source` plus driver addressability basis |
| Construction coverage | What portions, concepts, or queries were actually examined? | constructor-declared examined set |
| Attachment coverage | For what declared purpose and program universe is program attachment complete? | purpose-scoped attachment universe |
| Adjudication completeness | Was a bounded case decided? | **DEFERRED** |

Use existing World completeness receipts over named universes. `COMPLETE` is
only relative to the declared universe, basis, and known gaps. It does not
mean every authoritative file was understood.

A normal useful claim may be much narrower than “all authority has been
understood.” For example:

> Attachment construction is complete for explicitly identified
> checkout-action requirements over the declared checkout program universe
> under constructor profile v1.

Negative conclusions require a relevant completeness claim. Unexamined
authoritative material is not thereby irrelevant or false.

Addressability completeness MAY be mechanical for a driver. Construction and
attachment completeness are constructor-declared and MUST disclose their
basis.

## Native output vocabulary

Do not build a universal ontology. Distinguish these outputs, then store them
with ordinary World primitives wherever possible.

| Output | Storage |
| --- | --- |
| Authorized source member | `authority_source` membership relation |
| Semantic referent | thin `REFERENT` plus `semantic_entity` membership |
| Source-native referent | thin `REFERENT` plus driver-owned membership, only when native identity exists |
| Program referent | existing spine `program_entity` / capability relations |
| Source-derived claim | named typed relation tuple |
| Source↔semantic, source↔program, semantic↔program | ordinary typed relations whose evidence stays in grounding |
| Unresolved / ambiguous record | ordinary `authority_unresolved` (or purpose-scoped equivalent) |
| Claim envelope / warrant | `AssertionGrounding` extra plus optional `authority_claim` index |
| Relevance / selection surface | `authority_relevance_scope` (not the warrant) |
| Completeness | existing completeness receipts |
| Construction receipt | application sidecar, analogous to spine construction |

Recommended inspectable relations, all application-level `BASE` relations:

```text
authority_source
semantic_entity
authority_claim
authority_endpoint_resolution
authority_attachment_warrant
authority_relevance_scope
authority_unresolved
authority_examined
```

`authority_claim` is an index over persisted assertions. It is not a second
truth system. Domain propositions remain in their precise relation names.

Program identities already in the spine MUST be reused, not duplicated as
semantic twins.

## World lifecycle

Kernel referents cannot join two sealed Worlds. Authority construction that
attaches to program identities MUST therefore see those identities as World
referents.

v0 placement:

```text
construct / reuse program spine in the candidate World
        ↓
declare authorized source universe
        ↓
run source drivers for addressability
        ↓
construct selected claims, identities, attachments, unresolved records,
        and relevance scopes
        ↓
write completeness records and AuthorityConstructionReceipt
        ↓
validate and seal
```

If a program spine is already a separately sealed artifact, a later authority
construction MUST either rebuild a candidate that includes the spine facts or
copy the needed program referents and their evidence into a new candidate
while preserving snapshot-local program IDs as application identifiers. It
MUST NOT invent a cross-database foreign key.

Comparison across program snapshots remains a separate sidecar operation. It
does not copy attachments.

## AuthorityConstructionReceipt

The construction receipt is a first-class inspectable artifact analogous to
`SpineConstructionReceipt`. Tentative name:

```text
AuthorityConstructionReceipt
```

It answers:

> What authoritative material was considered, what durable semantic/program
> relationships were created, what remains unresolved, and what known
> losses/limits apply?

It is not a second truth system. It summarizes and references grounded World
facts and completeness records.

Required fields:

```text
contract                          authority_construction/v0
construction_id
construction_version

authorized_source_universe        declaration identity
source_revisions                  handle → revision/digest
source_standing_summary           authoritative / available / analysis_support

constructor_id
constructor_version
construction_profile
construction_purpose              natural-language or PURPOSE identity

program_snapshot_id               the spine snapshot attached to, if any
program_universe                  declared program universe identity

source_regions_examined           counts / representative locators
source_native_relationships_used

semantic_referents_created
semantic_referents_reused

claims_persisted                  by claim_kind
direct_source_program_links
semantic_program_links
source_semantic_links

resolution_summary
    native_id
    deterministic
    source_defined
    agent_resolved
    ambiguous
    unresolved

relation_support_summary
    source_native
    source_explicit
    source_structural
    cross_evidence_inferred
    hypothesized

known_unbound_material
known_losses
reusable_resolvers                invoked or authored
representative_examples
completeness_references
adequacy_probe_results
optional_purpose_scoped_acceptance
exploration_provenance            inspected material/tools, not support
```

Validation of the receipt is consistency with World facts, not an independent
authority.

## Adequacy probes

Purpose-specific probes are allowed, analogous to spine adequacy probes.

A probe asks whether the persisted construction is adequate for a stated
attachment purpose. It does not ask whether every source sentence was
formalized.

Examples:

```text
Can the "initial cancellation action" requirement be localized
to a specific program attachment surface?

Can two distinct uses of the same Button-like implementation
be distinguished if the source treats them differently?

Can the payment-boundary ADR be connected to the program
boundary it governs?

Can an unresolved source phrase remain unresolved without
creating a guessed program relation?
```

Outcomes:

| Outcome | Meaning |
| --- | --- |
| `SATISFIED` | The probe’s question is answered by persisted structure plus evidence. |
| `UNRESOLVED` | The construction honestly left the question open. |
| `INADEQUATE` | Construction is valid, but a needed surface or distinction is missing. |
| `FAILED` | The probe found a contract violation, not a mere limitation. |

`INADEQUATE` is not a contract failure. Example:

```text
source understood;
program spine lacks component-usage identity surface;
construction valid but inadequate for this attachment purpose.
```

Record that as `SPINE_SURFACE_MISSING` plus probe outcome `INADEQUATE`.

## Interaction with program correspondence and ProgramDelta

Program snapshots are versioned. Source/program attachments MUST target
explicit program manifestations in a named snapshot.

When a new program snapshot exists, do NOT automatically copy attachments
through correspondence.

Frozen:

```text
program correspondence
    ≠
claim validity continuation
```

In particular:

```text
CONTINUED + HEURISTIC
```

MUST NOT silently renew a source/semantic/program attachment.

`DETERMINISTIC` correspondence, if a later comparison version ever emits it,
still does not copy claims. It only supplies stronger input to maintenance,
specified in
[`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md).

### Attachment warrant context

Each attachment that involves a program endpoint MUST retain enough
dependency/provenance for a later maintenance step to ask:

```text
did the manifestation continue?

did the structural context used to justify the attachment survive?

did the relevant program relation change?

was the correspondence exact / heuristic / ambiguous?

does the original evidence still support this attachment?
```

Store that as `authority_attachment_warrant`, grounded to the same evidence as
the claim. Minimum content:

```text
program_snapshot_id
program_entity
justifying_structural_context     enclosing unit / owner / usage surface
justifying_program_relations      e.g. program_invokes target
justifying_resolution_outcomes
source_revision / evidence pointers
constructor_profile
relation_support
endpoint_resolution
```

Later maintenance MUST use this warrant as the dependency surface, together
with correspondence and ProgramDelta, as specified in
[`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md).
ProgramDelta `maintenance` hooks are optional localization aids, not the
assessment. Maintenance MUST NOT treat identity continuity as claim
continuity and MUST NOT persist a new attachment.

The warrant MUST NOT be overloaded as a case-selection watch list. Relevance
scope is a separate structure.

### Relevance / case-selection surface

Each program-involving attachment MUST have an inspectable selection
surface that answers:

```text
which mechanical program changes should present this authority
in a governance case?
```

Store that as `authority_relevance_scope`, application-level `BASE` rows
keyed to the attachment assertion (and warrant when one attachment has
several program endpoints). Clause kinds and kind-defaults are specified in
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md).

Construction SHOULD persist the effective clauses, including when they are
exactly the kind default. Missing rows cause consumers to apply the default
and record a known omission. Construction MUST NOT require an elaborate
watch query on every claim. Direct attachment to a fine-grained identity
(`call_site`, `callable`) MAY use only the published default.

Do not declare `STRUCTURAL_SCOPE` over a module unless the profile
intentionally governs that subtree. File proximity is not a clause.

Examples:

```text
attachment:
    CancellationEntryAction -> call_site C
selection surface (default):
    ATTACHED_IDENTITY C
    ENDPOINT_RELATION program_invokes at C

attachment:
    confirmation authority -> cancelSubscription callable
selection surface (default):
    ATTACHED_IDENTITY cancelSubscription
    IDENTITY_MANIFESTATION signature, source_manifestation
    ENDPOINT_RELATION program_invokes where cancelSubscription is target

attachment:
    payment ADR -> CheckoutPayment module
selection surface (must be explicit if inner calls should select):
    ATTACHED_IDENTITY CheckoutPayment
    ENDPOINT_RELATION program_imports
    EXPLICIT_IDENTITY / STRUCTURAL_SCOPE / further relations
    as the profile actually intends
```

### v0 storage (`ontology_author.authority`)

`authority_relevance_scope` is an application `BASE` relation. One row is
one clause. Roles:

```text
warrant_assertion_id          TEXT, the warrant assertion
attachment_assertion_id       TEXT, the program-involving claim
program_entity                REFERENT, the warrant target
clause_kind                   ATTACHED_IDENTITY | IDENTITY_MANIFESTATION
                              | ENDPOINT_RELATION | STRUCTURAL_SCOPE
                              | EXPLICIT_IDENTITY
identity_id                   REFERENT, identity this clause watches
relation_name                 TEXT; empty unless ENDPOINT_RELATION / optional extras
endpoint_role                 TEXT; empty or a native role such as target
relation_tuple                JSON object; empty `{}` unless an explicit tuple
manifestation_properties      JSON list; empty `[]` unless listed
structural_capability         TEXT; empty unless STRUCTURAL_SCOPE names one
origin                        DEFAULT_KIND_RULE | EXPLICIT
```

`AuthorityConstructor.persist_claim` materializes the kind default after
each warrant. `declare_relevance_scope(...)` adds `EXPLICIT` clauses.
`declare_attachment_universe(...)` records identities in
`authority_attachment_scope` without creating an attachment.

Admission rejects unknown clause kinds, unknown spine relations, missing
identities, watch-query DSL fields (`query`, `cypher`, `watch`, …), and
compliance tokens. Default clauses MUST be persisted; consumers MAY apply
the documented default only when rows are missing, and MUST record that
the scope was inferred.

## Worked example: semantic drift

Authoritative Markdown, standing `AUTHORITATIVE`:

```markdown
The initial "Cancel subscription" action enters the retention flow.

Cancellation occurs only after confirmation on the final
cancellation screen.
```

Program snapshot (TypeScript-like spine surfaces):

```text
SubscriptionPage
    -> cancel button usage / suitable emitted attachment surface
    -> call site
    -> openRetentionFlow

FinalCancellation
    -> call site
    -> cancelSubscription
```

### 1. Source evidence regions

Assume `docs/checkout.md` at digest `sha256:9f…`, driver `markdown/v0`.

```text
E1  docs/checkout.md@sha256:9f…
    bytes of paragraph 1
    “The initial "Cancel subscription" action enters the retention flow.”

E2  docs/checkout.md@sha256:9f…
    bytes of paragraph 2
    “Cancellation occurs only after confirmation on the final cancellation screen.”
```

These are `SourceObservation`s. They are not referents. The document, the
implied heading if any, and the paragraphs are evidence locations.

### 2. Semantic referent worth creating

`semantic:CancellationEntryAction` earns persistence:

- two source claims concern the initial cancellation action and its later
  confirmation boundary;
- it should survive renaming of button copy and of `openRetentionFlow`;
- governance will need to refer to it when the implementation is replaced;
- it connects authority to more than one program manifestation.

`semantic:RetentionFlow` MAY also earn persistence if several sources and
program surfaces talk about that flow as such. If the only use is this one
sentence and a single call target, a direct attachment to
`program:…:openRetentionFlow` can suffice for that endpoint.

Do not create semantic nodes for “subscription”, “screen”, “confirmation”, or
the quoted button label merely because they appear.

### 3. Source-derived claims

Purpose-specific relations; names are illustrative, not a vocabulary:

```text
C1  enters_flow(
      semantic:CancellationEntryAction,
      semantic:RetentionFlow
    )
    support: SOURCE_EXPLICIT
    endpoints: AGENT_RESOLVED, AGENT_RESOLVED
    evidence: E1

C2  cancellation_requires_prior(
      semantic:CancellationEntryAction,
      semantic:FinalCancellationConfirmation
    )
    support: SOURCE_EXPLICIT
    endpoints: AGENT_RESOLVED, AGENT_RESOLVED
    evidence: E2
```

If `FinalCancellationConfirmation` does not earn an independent semantic
identity, C2 MAY attach the confirmation condition to the program
`FinalCancellation` manifestation directly, with the same evidence E2.

### 4. Program attachment

```text
A1  SEMANTIC_PROGRAM
    semantic:CancellationEntryAction
        -> program:…:SubscriptionPage/cancel-button-usage
        -> program:…:call-site → openRetentionFlow
    support: CROSS_EVIDENCE_INFERRED
    program resolution: AGENT_RESOLVED
    warrant: snapshot S1, invokes openRetentionFlow, usage surface on SubscriptionPage
    evidence: E1

A2  SEMANTIC_PROGRAM
    confirmation endpoint
        -> program:…:FinalCancellation/call-site → cancelSubscription
    support: CROSS_EVIDENCE_INFERRED
    program resolution: AGENT_RESOLVED
    warrant: snapshot S1, invokes cancelSubscription
    evidence: E2
```

### 5. Exact grounding and provenance

Each of C1, C2, A1, A2 carries:

- `SourceObservation` for E1 and/or E2 with provider `markdown`, handle
  `docs/checkout.md`, revision `sha256:9f…`, location `bytes:start:end`;
- `construction_method` identifying the constructor profile and any resolver;
- envelope with claim kind, support class, per-role resolution, snapshot id,
  and warrant context;
- standing from `authority_source` for `docs/checkout.md`.

Exploration provenance on the receipt MAY say the constructor grepped
`Cancel`, read `SubscriptionPage`, and inspected call sites. That inspected
set is larger than `{E1, E2}` and is not the claim basis.

### 6. What remains source wording

Left unformalized, on purpose:

- the quoted label `"Cancel subscription"` as a durable semantic object;
- the prose rhythm of “enters”;
- “only after” as a full temporal logic;
- “final cancellation screen” as a UI ontology;
- any user-visible copy besides the evidence span.

The index is enough to recover E1 and E2 when the program changes. It is not
a replacement of the paragraphs.

### Later ProgramDelta

```text
initial action call site:
    openRetentionFlow
        ->
    cancelSubscription
```

Suppose comparison reports the call site `CONTINUED` with `HEURISTIC`
identity continuity and `RETARGETED` `program_invokes`.

The persisted construction is sufficient for a later system to:

1. select attachments whose warrant lists that call site or
   `openRetentionFlow`;
2. recover E1 exactly from the stored `SourceObservation`;
3. see that identity continuity is `HEURISTIC` and invocation changed;
4. refuse silent renewal.

Maintenance and case assembly for this delta are specified in
[`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md) and
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md). This contract
does not adjudicate whether the new target still satisfies the retention-flow
requirement.

## Worked example: direct attachment

Authoritative ADR fragment:

```markdown
## Payment boundary

`src/payments/boundary.ts` MUST NOT import `src/ui/`.
```

No independent semantic referent is warranted. The ADR names a mechanically
identifiable program module.

```text
evidence E3
    docs/adr/payment-boundary.md@sha256:… / paragraph under “Payment boundary”

claim D1  SOURCE_PROGRAM
    forbids_import(
      program:…:src/payments/boundary.ts,
      program:…:src/ui  (external or in-scope module identity)
    )
    support: SOURCE_EXPLICIT
    module resolution: SOURCE_DEFINED or DETERMINISTIC
    evidence: E3
    warrant: snapshot S1, named path tokens in the source
```

There is no `semantic:PaymentBoundary` unless later sources and replacements
make that identity independently useful.

If the path cannot be resolved uniquely, persist `ENDPOINT_UNRESOLVED` or
`AMBIGUOUS_REFERENT` with E3. Do not invent a module.

## Existing World primitives reused

| Need | Reuse |
| --- | --- |
| Semantic and program handles | thin `REFERENT` |
| Precise propositions | named typed n-ary `BASE` relations |
| Claim identity | content-addressed assertion ID |
| Exact evidence | `SourceObservation` |
| Support packaging | `AssertionGrounding` |
| Coarse path label | `ConstructionOrigin` alongside, not instead of, the taxonomies |
| Multiple supports | multiple grounds on one assertion |
| Scoped completeness | `Completeness` receipts over named universes |
| Open-world absence | no negative from empty query without completeness |
| Explicit unresolvedness | ordinary relation rows, as `Purpose.unresolved` already does |
| Artifact integrity | candidate → validate → sealed World |
| Inspectable summary | application sidecar receipt, like the spine |

## Kernel limitations

No new kernel primitive is required by this contract. Concrete limits that
the application layer MUST live with:

1. There is no kernel `Claim` type. Propositions are relation tuples plus
   grounding. Application index relations are allowed.
2. `SourceObservation` does not encode standing. `authority_source` must.
   `as_pointer()` also omits `payload`; v0 copies locators into grounding extra.
3. `ConstructionOrigin` is too coarse for support and resolution taxonomies.
   Store those in grounding extra and inspectable relations.
4. Completeness receipts are relative to a named universe and run. They cannot
   honestly mean “the corpus is understood.”
5. Referents do not join two sealed Worlds. Attachments that FK program
   identities must live with those identities in one World, or copy them.
6. Relation staleness tracks deterministic World inputs, not source-file
   drift, adapter changes, or program-snapshot replacement.
7. Experimental `Contract` / `Obligation` / `Adjudication` types MUST NOT be
   reused as this authority model.
9. Semantic `query_sql` strips hidden `_assertion_id` columns.
   Warrant identity for relevance-scope rows is recovered with ordinary
   SQL, not a kernel foreign key.

If a future implementation cannot represent exact evidence, standing, or the
two-axis epistemic model without lying, that is a concrete correctness case
for a kernel change. Awkward construction workflow is not.

## Intentionally deferred

- Autonomous LLM constructor orchestration.
- Source-authority maintenance / `AuthorityDelta`.
- Revalidation or re-resolution construction that persists new attachments.
- Policy compilation. Adjudication is specified in
  [`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
- Additional source profiles (Figma, Storybook, issues, schemas).
- Cross-World semantic lineage for semantic referents when the sealed World
  is replaced.
- A closed domain relation vocabulary.
- Numeric confidence, fuzzy matching, embeddings, or RAG as construction
  machinery.
- Treating `CONTINUED` correspondence as claim renewal.
- Human acceptance workflow beyond an optional receipt field.
- Whether reusable resolvers become ordinary installed product code.

A v0 Markdown driver, explicit construction writer, receipt, admission
checks, and ProgramDelta evidence-recovery helper exist. They do not yet
persist `authority_relevance_scope`. That relation is specified here so
case assembly need not infer watches from file proximity. This contract
remains sufficient when an intelligent constructor can inspect ordinary
authoritative material and a mechanically grounded program spine, persist
only the relationships worth retaining, and leave an exact inspectable
trail back to the original authority without pretending to formalize all
source meaning.
