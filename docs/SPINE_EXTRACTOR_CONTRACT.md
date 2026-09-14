# Spine extractor contract

This document defines the boundary between an extractor implementation and
the mechanically grounded program spine. It is subordinate to:

- [`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md);
- [`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md);
- [`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md);
- [`KDM_PROFILE.md`](KDM_PROFILE.md); and
- [`TYPESCRIPT_KDM_PROFILE.md`](TYPESCRIPT_KDM_PROFILE.md).

The contract governs durable output. It does not prescribe how an extractor
finds, indexes, resolves, or stores its intermediate facts.

```text
arbitrary extractor implementation
        |
        | conforms to
        v
versioned spine core and capability contracts
        |
        v
mechanically grounded World
```

The v0 semantic foundation remains the selected subset of OMG KDM 1.4. Where
an extractor claims a KDM-backed capability, the applicable KDM profile gives
the emitted entity or relation its meaning. An extractor may be written with
a compiler API, an existing structural index, a project script, a framework
analyzer, or an agent-authored deterministic program. Its internal data model
does not become the public spine model merely because it is convenient for the
implementation.

## Conformance, coverage, and adequacy

Three questions must remain separate.

### Contract conformance

A spine conforms when its durable output satisfies the mandatory core and all
capability contracts it claims. Conformance concerns epistemic honesty,
reproducibility, provenance, closure, and scoped completeness.

### Capability coverage

An extractor may provide only some standard capabilities. It may declare that
Calls, UI composition, routing, or state transitions were not produced. A
capability limitation is allowed when the receipt makes it visible and no
claim depending on that capability is made.

### Purpose adequacy

A conforming spine may still be too coarse for a particular governance
purpose. The spine contract does not define one universally adequate program
granularity.

For example, both of these can be honest representations when their declared
capabilities support them:

```text
Page -> ComponentUsage -> CallSite -> Callable
Page -> Callable
```

The second representation cannot claim component-instance attachment merely
because its enclosing callable is known.

The outcomes are therefore:

```text
CONTRACT FAILURE
  durable output violates the core or a claimed capability contract;
  the candidate is rejected and cannot be sealed.

CAPABILITY LIMITATION
  the extractor does not produce a capability; this is allowed when visible.

PURPOSE INADEQUACY
  the extractor conforms, but the preserved structure cannot answer a
  particular purpose at the required granularity.
```

A purpose requirement may cause an application to reject a construction for
that purpose. It does not change a conforming spine into a contract failure.

## Contract versions and profiles

Every construction has a versioned contract identity:

```text
spine_core_contract_id
spine_core_contract_version
capability_profile_ids_and_versions
```

The core version governs the mandatory output envelope. A capability version
governs the meaning of that capability's entities, relations, evidence,
uncertainty, and completeness claims. Versioning is semantic: changing the
meaning of a relation, endpoint, resolution outcome, or completeness basis
requires a new version.

An extractor identity and version describe the mechanism that produced the
candidate. They are separate from the core and capability contract versions.

The following classes of output are distinct:

```text
MANDATORY SPINE CORE
  required for every extractor that claims to construct a spine.

OPTIONAL STANDARD CAPABILITY
  a versioned capability defined by this spine/KDM profile family.

PROJECT OR FRAMEWORK EXTENSION
  additional declared semantics that do not silently redefine the core or a
  standard capability.
```

KDM 1.4 remains normative for the v0 KDM-backed standard capabilities. A
project extension may use KDM lightweight-extension semantics or another
explicit profile mechanism, but it must state its own meaning and version.

## Mandatory spine core

The mandatory core is the smallest promise that allows downstream consumers
to inspect what was constructed without reparsing the extractor's private
model.

### 1. Declared universe and effective inputs

The construction MUST retain the user or application declaration of the
program boundary. The declaration may identify workspace roots, project
configuration, package roots, inclusion/exclusion rules, generated-file
policy, tests, declarations, or other inputs appropriate to the extractor.

The construction MUST separately retain the effective consumed input set:

```text
declared boundary
        -> mechanical expansion
effective consumed inputs
        -> emitted spine facts
```

Every effective input MUST have:

- a reconstructible identity or digest;
- a disposition such as `IN_SCOPE`, `EXTERNAL_BOUNDARY`, or
  `ANALYSIS_SUPPORT`, or an equivalent declared classification;
- its role in construction;
- its owning project or configuration when applicable; and
- an accounted-for outcome when it could affect a claimed capability.

An input disposition does not itself create a program referent. Support
material can be consumed without becoming program presence. A user declares
the boundary and configuration; the extractor enumerates resulting entities.

### 2. Snapshot identity

The extractor MUST identify the immutable mechanical state against which its
facts are true. The snapshot identity MUST include, directly or through
content-addressed manifests, every input capable of changing a contracted
fact:

```text
source state
declared boundary
effective consumed inputs
relevant configuration and dependency resolution
extractor identity and version
core contract version
capability/profile versions
extractor configuration
```

The source state and the mechanism interpreting it are separate identities.
An analyzer upgrade can produce a different snapshot representation from the
same source state. A Git revision alone is not sufficient when generated
inputs, dependency resolution, or configuration affect extraction.

The exact digest and serialization format remain implementation choices. The
manifest must make the identity reconstructible.

### 3. Deterministic reconstruction

Given identical immutable construction inputs, extractor identity/version,
extractor configuration, and contract/profile versions, an extractor MUST
reconstruct the same:

- snapshot identity;
- declared/effective input manifest;
- first-class identity descriptors and IDs;
- durable relation tuples;
- resolution outcomes;
- evidence coordinates and references; and
- capability receipt values, apart from explicitly non-semantic build
  metadata that the contract identifies as such.

Emission order, process identifiers, temporary paths, hash-map iteration, and
private cache state MUST NOT affect durable output. A deterministic ID is not
a lineage ID. Cross-snapshot continuity remains a later comparison result.

### 4. First-class identities and identity surfaces

The extractor MUST declare which kinds of program identity it emits and what
mechanically establishes each kind. Every emitted first-class identity MUST
have:

- a snapshot-local deterministic ID;
- an identity kind and profile meaning;
- a declared context or ownership placement;
- reconstructible evidence or a declared non-source basis; and
- no implied semantic or governance significance.

The core does not mandate one universal set of kinds or one granularity. A
coarse extractor may emit modules and callables. A richer extractor may also
emit methods, component usages, routes, or call sites. It must declare the
surfaces it actually preserves.

Source locations, AST nodes, compiler symbols, names, and display labels are
not automatically program identities. A source range can manifest one or
several identities. An identity can have several declaration or occurrence
regions.

### 5. Structural context

Every emitted identity MUST be placed in an inspectable structural context.
That context may use the KDM ownership model or an equivalent declared core
context relation. An emitted identity with no parent is allowed only when it
is a declared root of the snapshot or an external boundary stub.

Structural context is not semantic `part_of`, visual containment, runtime
instantiation, or governance relevance. An extractor must not claim a finer
context than its evidence establishes.

### 6. Evidence and provenance

Every first-class identity and every durable mechanical claim MUST have
reconstructible evidence. Evidence MUST identify, as applicable:

```text
snapshot
source/configuration/analysis input identity
exact range or non-source location
evidence role
extractor identity/version
core and capability profile versions
resolution information
```

The exact coordinate convention is capability-specific, but it must be
declared. For source evidence, a later consumer must be able to recover the
relevant immutable bytes without relying on a private extractor database.
Full source bodies need not be copied into the World.

KDM `SourceRef`/`SourceRegion` meaning and the Ontology Author
`SourceObservation`/`AssertionGrounding` mechanism address evidence. They do
not make every evidence location a program referent.

### 7. Boundary and relationship closure

Every persisted mechanical relation with referent endpoints MUST satisfy both
forms of closure:

```text
referential closure
  every endpoint has a represented referent;

program closure
  every in-scope endpoint is a member of the snapshot's explicit program
  universe, while a known out-of-scope endpoint is an explicit boundary
  identity.
```

An extractor MUST NOT silently delete a known cross-boundary relationship.
An external endpoint may be a thin stub with no implementation facts. A
relationship whose target cannot be established must retain an explicit
uncertainty outcome instead of a guessed endpoint.

The generic World kernel's `REFERENT` role integrity remains the underlying
referential check. The extractor contract adds snapshot-universe and boundary
checks; it does not replace or duplicate the kernel's foreign-key behavior.

### 8. Resolution honesty

For each relationship capability, the extractor MUST distinguish at least:

```text
RESOLVED
  a positive target or target set is mechanically established;

MULTIPLE_CANDIDATES
  more than one compatible target remains possible;

UNRESOLVED
  the occurrence or attempted relationship is known, but no target is
  mechanically established under the capability contract.
```

A capability may define a more precise taxonomy, but it must preserve these
semantics. An omitted positive relation is not proof of absence unless a
scoped completeness claim licenses that conclusion. The extractor must not
use an agent's semantic guess to improve graph connectivity.

### 9. Scoped completeness

The extractor MUST publish completeness separately for each produced
capability. A core-conforming receipt MUST NOT use one global
`spine_complete=true` flag as a substitute for scoped claims.

Every completeness claim names:

- the capability and version;
- the declared universe or input scope;
- recognized forms and analysis rules;
- the analyzer/configuration basis;
- known gaps and exclusions; and
- the result or receipt it summarizes.

`COMPLETE` means complete only over that declared scope and basis. For
example, a complete program universe may coexist with incomplete static call
resolution, and complete static call resolution does not mean complete runtime
behavior.

### 10. Source-range localization

The core MUST define how a source range, when applicable, is localized to the
snapshot's emitted program identities. The result MUST be mechanical and
inspectable:

```text
(snapshot, input identity, coordinate convention, range)
      -> zero or more program identity IDs
```

Localization returns identity coverage. It does not infer governance impact,
semantic relevance, or the smallest purpose-adequate attachment surface.

An extractor that has no source-addressable input may declare source
localization not applicable, but it must then expose the non-source evidence
model needed to audit its claims.

### 11. Comparison readiness

Lineage and diffing remain deferred. A conforming extractor MUST nevertheless
retain enough information for later comparison to be possible without
pretending that comparison has already been done:

- stable snapshot-local descriptors;
- source/configuration evidence;
- structural ownership/context;
- declaration and occurrence roles; and
- explicit loss/collapse declarations.

The receipt MAY record observations such as identical-input reconstruction or
whitespace-edit behavior. It MUST NOT replace those observations with an
opaque lineage-quality score.

## Optional standard capability contracts

An extractor claims a standard capability by naming its version and emitting
the capability-specific contract fields. A standard capability contract
defines:

```text
semantic basis
identity and endpoint kinds
accepted relation meanings
positive assertion rule
evidence requirements
uncertainty outcomes
completeness scope and negative reasoning
boundary behavior
```

The following capabilities are examples of the current KDM-backed family,
not mandatory output for every extractor:

| Capability | Current semantic basis | Typical status examples |
|---|---|---|
| code structure | KDM Code, Source, and ownership semantics | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| imports | KDM `code::Imports` | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| calls | KDM `action::Calls` with call-site `ActionElement` | `STATIC_COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| data access | KDM `Reads`, `Writes`, `Addresses` | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| control flow | KDM `ControlFlow`/`Flow` | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| UI composition | selected KDM UI semantics or declared KDM extension | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| events and states | KDM Event semantics where mechanically recoverable | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |
| routing | declared KDM-backed or profile extension | `COMPLETE`, `PARTIAL`, `NOT_PRODUCED` |

The status vocabulary is capability-specific. `STATIC_COMPLETE` is not a
claim about all runtime targets. `NOT_PRODUCED` is a visible capability
limitation, not an assertion that the capability has no instances.

If an extractor claims KDM `Calls`, it must preserve KDM's semantic shape.
For a call-site capability this means, conceptually:

```text
owning CallableUnit
      -> owns ActionElement for the call site
      -> KDM Calls -> CodeItem target
```

An extractor cannot replace that fact with a different caller-to-callee
predicate and still call the result KDM `Calls`. It may add a derived
callable-level convenience relation if its definition is explicit.

The same rule applies to `Reads`, `Writes`, `Imports`, `Extends`, `Implements`,
and other selected KDM predicates. A profile may be sparse, but it may not
silently change the predicate's endpoint or evidence meaning.

## Project and framework extensions

An extension may add program identity kinds, relations, evidence roles,
resolution states, or capability summaries for a project or framework. It
MUST declare:

- extension ID and version;
- semantic definition and endpoint kinds;
- mechanical rule establishing each fact;
- evidence and reconstruction requirements;
- uncertainty and omission semantics;
- completeness scope; and
- how it composes with the core and standard capabilities.

An extension MAY add information. It MUST NOT:

- redefine a standard KDM predicate under a new name;
- turn semantic interpretation into mechanical fact;
- treat an omitted extension fact as negative evidence without completeness;
- use framework labels as universal program identity; or
- require every extractor to emit the extension.

For example, a React extractor may define a `ComponentUsage` surface and a
KDM UI `renders` capability. A generic TypeScript extractor that preserves
only enclosing callables remains conforming; it simply does not produce
component-instance attachment capability.

## Supplemental and replacement extractors

### Supplemental extractor

A supplemental extractor adds facts or capabilities to an existing core
spine. It MUST identify:

- the existing snapshot it supplements;
- the boundary and effective inputs it used;
- its own extractor and capability versions;
- whether it adds a new capability or additional evidence for an existing
  capability; and
- any compatibility assumptions about the existing spine.

The supplement MUST NOT weaken core closure, replace a standard fact with a
different meaning, or silently override an existing assertion. If two
supplements produce incompatible claims for the same semantic tuple, the
combined candidate has a conflict requiring explicit resolution or admission
failure; the system must not choose by insertion order.

The safe default is that a supplement adds a capability whose output can be
inspected independently. Adding evidence to an existing assertion is allowed
when the assertion identity and predicate meaning are unchanged.

### Core or replacement extractor

A replacement extractor constructs the mandatory spine core itself. It may
use a radically different implementation from the reference TypeScript
extractor, but it MUST satisfy the same core contract and every claimed
capability contract.

Replacing an extractor does not preserve program identity across snapshots.
If the replacement uses a different analyzer or profile version, that
difference belongs in snapshot/provenance identity. Cross-version continuity
is a later explicit lineage operation.

An extractor must not call itself supplemental merely to avoid core closure
requirements while emitting relations that downstream consumers will treat
as the program spine.

## SpineConstructionReceipt

Each construction SHOULD produce an inspectable
`SpineConstructionReceipt`. It is a construction/admission artifact, not a
second truth system and not an individual relation completeness receipt.

The receipt may be a canonical JSON bundle member, a World-linked sidecar, or
another inspectable artifact defined by the bundle convention. It MUST be
available with the sealed World and MUST be covered by the World admission
record or an equivalent integrity reference.

The conceptual schema is:

```yaml
receipt_version: ...
construction_id: ...
conformance:
  status: PASS | CONTRACT_FAILURE
  diagnostics: [...]
snapshot:
  id: ...
  source_state: ...
  declared_boundary: ...
  effective_inputs: ...
  configuration: ...
  extractor: { id: ..., version: ..., configuration_digest: ... }
  core_contract: { id: ..., version: ... }
  capability_profiles: [...]
capabilities:
  - id: ...
    version: ...
    status: COMPLETE | STATIC_COMPLETE | PARTIAL | NOT_PRODUCED | UNKNOWN
    scope: ...
    completeness_basis: ...
    completeness_receipt_ref: ...
    known_gaps: [...]
identity_surfaces:
  - kind: ...
    semantic_basis: ...
    emitted_count: ...
    context_model: ...
resolution_summary:
  by_capability: ...
boundary_summary:
  in_scope: ...
  external_boundary: ...
  analysis_support: ...
losses:
  - category: COLLAPSES | DOES_NOT_REPRESENT | UNKNOWN
    scope: ...
    statement: ...
    consequence: ...
representative_examples: [...]
comparison_readiness:
  observations: [...]
acceptance: optional
```

The exact serialization is deferred. The fields and distinctions are
contractual.

### Produced capabilities

The receipt MUST list every capability relevant to the construction result,
including capabilities deliberately not produced when their absence matters
to interpretation. A typical declaration might be:

```text
program_universe       COMPLETE
code_structure         COMPLETE
imports                COMPLETE
calls                  STATIC_COMPLETE
component_usage        NOT_PRODUCED
routing                NOT_PRODUCED
```

Each status must point to or summarize the underlying scoped completeness
record. A receipt that says `COMPLETE` without a declared basis is a contract
failure.

### Identity and attachment surfaces

The receipt MUST expose the kinds of first-class program objects that exist,
their semantic basis, and useful counts. Counts are inspection aids only. A
count of zero can mean `NOT_PRODUCED`, an empty complete universe, or a
capability-specific result; the status and scope supply the meaning.

The receipt SHOULD identify whether a surface is suitable for attachment at
the level of modules, callables, methods, call sites, component usages,
routes, state objects, or another declared kind. It must not infer a finer
surface from a coarser count.

### Resolution and boundary summaries

Resolution summaries MUST be broken down by capability where resolution has
meaning. They summarize `RESOLVED`, `MULTIPLE_CANDIDATES`, and `UNRESOLVED`
outcomes; they do not replace the individual outcome and evidence records.

Boundary summaries MUST distinguish local program members, known external
identities, and analysis-support material. An external count does not mean
external code was analyzed, trusted, or semantically understood.

### Explicit losses and collapses

Every extractor SHOULD declare meaningful loss explicitly. Examples include:

```text
COLLAPSES
  lexical blocks into the owning callable;
  several syntax forms into one KDM CodeItem;
  source references into a single declaration identity.

DOES_NOT_REPRESENT
  runtime-created routes;
  component instances;
  reflection-derived call targets;
  external implementation bodies.
```

A loss declaration is not a failure. It prevents a sparse but honest graph
from being mistaken for an exhaustive representation of program meaning.
An extractor must not claim that a collapsed distinction is available to a
downstream purpose.

### Representative examples

The receipt SHOULD include or reference a small number of examples. Each
example contains enough information for a human to inspect the construction:

```text
input and exact range
  -> emitted identity/context chain
  -> relevant mechanical relation
  -> resolution outcome
  -> completeness/capability reference
```

For example:

```text
CheckoutPage.tsx bytes:410:427
  -> CompilationUnit checkout module
  -> CallableUnit CheckoutPage
  -> ComponentUsage Button#2       [only if produced]
  -> ActionElement                 [only if produced]
  -> KDM Calls submitOrder         [only if resolved]
```

The example must show omitted or unresolved portions rather than filling them
with inferred nodes.

## Adequacy probes

Adequacy probes are optional, purpose-specific experiments. They are not
universal conformance tests and do not alter the meaning of the spine.

An adequacy probe records:

```yaml
probe_id: ...
purpose: ...
question: ...
input_or_test: ...
observed_result: ...
relevant_capability: ...
implication: ...
receipt_ref: ...
```

The probe must state what the observed result licenses. It must not turn an
answer such as “both uses localize only to CheckoutPage” into a hidden quality
score.

Examples include:

- Can two uses of the same component be distinguished?
- Can a source range inside a handler localize to the component usage and
  callable separately?
- Can a UI-triggered call be followed through an unattached helper?
- Can a changed range localize to the smallest emitted identity actually
  preserved by the extractor?

A valid result may be:

```text
valid spine;
component-instance capability not produced;
inadequate for instance-level Figma linking.
```

An adequacy probe may be run during construction, review, or later purpose
evaluation. Its result is evidence about usefulness, not a new mechanical
claim.

## Optional user or agent acceptance

An application MAY record an acceptance after inspecting the construction
receipt and adequacy probes. Acceptance SHOULD include:

```text
receipt digest
intended purpose
accepted capability scope
probe references and conditions
actor and timestamp
```

Acceptance means:

> this representation is accepted as adequate for the stated construction
> purpose under the recorded conditions.

It does not mean that every emitted fact is globally true, that all source
meaning was formalized, or that the program is semantically complete.

Interactive acceptance is not required for every build. A policy may require
it for a new extractor, a changed profile, or a purpose with high attachment
cost, while ordinary rebuilds proceed through mechanical admission alone.

## Relationship to World completeness

The existing World completeness machinery remains authoritative for the
individual scoped completeness records it stores. The construction receipt
summarizes or references those records:

```text
individual capability/relation completeness receipts
        -> summarized/referenced by
SpineConstructionReceipt
```

The receipt MUST NOT broaden a completeness claim. If an underlying record is
`COMPLETE` over statically resolved calls, the construction receipt may report
that status with the same basis; it may not report complete runtime call
behavior.

For base mechanical extraction, the receipt is an admission and inspection
artifact. It does not make a base relation complete merely by existing.
Individual claims still require grounding, and the explicit program universe
still supplies the universe against which presence is evaluated.

## Diff and lineage readiness

Cross-snapshot lineage remains deferred. A construction receipt SHOULD expose
observations that help a later comparison, such as:

```text
identical immutable input rebuilt -> identical IDs and facts
whitespace-only edit -> which descriptors and evidence changed
rename/move sample -> what structural context remains available
coarse surface -> which possible correspondences are necessarily lost
```

These are observations, not lineage decisions. The receipt must not emit a
single opaque `lineage_quality` score. It should state which identity
descriptors, declaration contexts, source manifestations, and loss
declarations are available to a future matcher.

## Construction lifecycle and failure handling

The extractor boundary fits the existing lifecycle:

```text
construct candidate
      -> produce manifest, World facts, capability records, receipt
      -> validate core and claimed capabilities
      -> publish receipt and sealed World
```

If validation finds a contract failure, the candidate MUST NOT be sealed or
published as a conforming spine. Diagnostics may be retained outside the
sealed World for repair, but they do not become durable program facts.

Capability limitations do not fail admission when they are declared and do
not violate a claimed capability. Purpose inadequacy is evaluated by the
application or adequacy probes and is not silently converted into a broader
completeness claim.

No extractor plugin registry, command protocol, loader, or generic kernel
primitive is implied by this lifecycle. Those are implementation decisions
for a later milestone.

## Worked fit: current TypeScript extractor

The current TypeScript/TSX vertical slice is a reference implementation of
the core boundary, not its definition.

### Core properties it demonstrates

It currently provides:

- a declared TypeScript boundary and effective consumed-input manifest;
- snapshot identity including source/configuration, TypeScript, extractor, and
  profile information;
- explicit `program_entity` membership;
- snapshot-local IDs for modules, declarations, signatures, and required
  call-site support elements;
- structural KDM ownership;
- exact UTF-8 byte evidence after conversion from TypeScript UTF-16 offsets;
- known external stubs and relation endpoint closure;
- explicit call/import resolution outcomes;
- source-range localization; and
- candidate validation followed by sealed World publication.

Its ordinary World projection uses thin referents, typed base relations,
`SourceObservation`/`AssertionGrounding`, `ConstructionOrigin.MECHANICAL`, and
an application-level `program_capability` relation. Those are concrete choices
of the TypeScript profile and existing World substrate.

### Capabilities it demonstrates

The current implementation declares scoped results for:

```text
program_universe
source_evidence
code_structure
imports
calls
external_endpoints
```

It also emits the selected TypeScript profile's straightforward
`HasType`, `Extends`, and `Implements` facts. Reads/Writes/Addresses, UI,
routing, event/state, full control flow, and semantic construction remain
unproduced or deferred.

A future construction receipt would report those deferred capabilities as
`NOT_PRODUCED` where their absence matters, rather than implying that they
were analyzed and found empty.

### Current losses

The TypeScript profile already makes several losses visible:

- compiler AST and checker objects are extraction machinery, not public KDM
  identities;
- unused anonymous functions need not become durable callable identities;
- dynamic/computed calls can remain unresolved;
- external implementation bodies are not modeled;
- React rendering and UI instance structure are not produced; and
- KDM `Calls` retains a call-site `ActionElement` rather than flattening to a
  caller/callee predicate.

Those choices can inform a receipt but must not become universal assumptions.

### Assumptions that remain TypeScript-specific

The following are implementation/profile details and are not mandatory for a
future extractor:

- Node.js as a process boundary;
- the TypeScript `Program`, `SourceFile`, checker, and compiler diagnostics;
- UTF-16-to-UTF-8 conversion as the coordinate conversion path;
- TypeScript fully qualified symbol names as ID inputs;
- `typescript_resolution` and `program_capability` as relation names;
- package.json discovery as dependency identity support; and
- the shape of `typescript.manifest.json`.

An alternate extractor may use another implementation entirely if it produces
the same core guarantees and declares its own capability profiles. The current
implementation therefore does not prevent a language, framework, user, or
agent-authored extractor from supplementing or replacing it.

## Contract failure examples

The following are mandatory admission failures for a claimed spine:

- an admitted in-scope identity is absent from explicit universe membership;
- a relation endpoint is missing and is neither an external stub nor an
  explicit unresolved outcome;
- evidence cannot be reconstructed from the recorded immutable input;
- identical inputs produce different durable IDs or facts;
- a claimed complete universe silently skips an admitted input;
- a standard capability uses a different predicate meaning than its versioned
  KDM profile; or
- a receipt claims a completeness scope broader than its underlying basis.

The following are allowed capability limitations when declared:

- no component-instance identities;
- no routing capability;
- unresolved dynamic calls;
- no state-transition extraction; or
- no external implementation facts.

The following are purpose questions rather than core failures:

- whether the available identities are fine-grained enough for Figma-node
  attachment;
- whether a source range can be localized to the user's preferred smallest
  identity; or
- whether the preserved call structure is sufficient for a particular impact
  query.

## Deliberately deferred

This contract does not decide:

- a plugin or command-loading architecture;
- a universal program granularity;
- a universal identity vocabulary beyond declared profile surfaces;
- a physical receipt storage schema;
- a universal extension namespace mechanism;
- cross-version lineage or matching algorithms;
- diff extraction;
- runtime completeness;
- a mandatory interactive acceptance flow; or
- whether a future implementation uses a literal KDM model, a KDM semantic
  projection, or another intermediate representation.

Those decisions must preserve this boundary if introduced later.
