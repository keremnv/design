# Spine extractor contract

This document defines the boundary between an extractor implementation and a
durable program spine. It is subordinate to
[`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md),
[`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md), and
[`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md).

The contract governs output. It does not prescribe a parser, compiler API,
index, graph database, process boundary, or intermediate representation.

```text
arbitrary deterministic extractor
        |
        | satisfies
        v
spine_core/v1 + declared capability contracts
        |
        v
mechanically grounded World
```

## Three separate outcomes

### Contract failure

The candidate is invalid and MUST NOT be sealed. Examples include a missing
relation endpoint, unreconstructible evidence, nondeterministic IDs for the
same immutable inputs, an omitted identity inside a claimed complete universe,
or a relation that does not follow its declared capability semantics.

### Capability limitation

The extractor honestly does not provide a capability, or cannot resolve a
mechanical fact. This is allowed when the receipt says so. Examples include
unmodelled component usages, unresolved dynamic calls, absent routing, or
absent state transitions.

### Purpose inadequacy

The extractor conforms to its declared capabilities, but those surfaces are
too coarse for a purpose. A spine exposing only an enclosing callable can be
valid while being inadequate for individual UI-instance attachment. Purpose
adequacy is tested by explicit probes, not hidden in conformance.

## Versioned capability contracts

Every construction identifies:

```text
spine_core/v1
claimed capability IDs and versions
extractor ID and version
profile/configuration identity
```

The mandatory core requires the following output envelope:

- a declared universe and effective consumed-input manifest;
- an immutable snapshot identity;
- deterministic reconstruction;
- declared first-class identity surfaces;
- mechanical structural context for emitted identities;
- reconstructible evidence for identities and claims;
- relation endpoint and boundary closure;
- explicit resolution outcomes where a capability resolves targets;
- capability-scoped completeness records; and
- a construction/conformance receipt.

The core does not require Calls, imports, type relations, UI, routing,
Reads/Writes, or any other optional fact capability. A claimed capability
must follow its own versioned contract.

The reference native standard capabilities currently used by the TypeScript
profile are:

```text
spine.code_structure/v1
spine.imports/v1
spine.calls/v1
spine.type_relations/v1
```

Their precise current meanings are defined in
[`TYPESCRIPT_SPINE_PROFILE.md`](TYPESCRIPT_SPINE_PROFILE.md). These IDs are
project-owned meanings; an implementation may use a different internal model.

An extension can add a capability under its own ID and version. It must state
its identity kinds, endpoint kinds, construction rule, evidence,
uncertainty, completeness, omissions, and composition behavior. It may add
information but cannot silently redefine a standard capability.

## Core contract

### Declared boundary and effective inputs

The user or application declares the program boundary. The extractor expands
it mechanically and records both forms. Each effective input has a stable
identity or digest, disposition, input role, owning project/configuration
where relevant, and an accounted-for outcome when it can affect a claimed
capability.

At minimum, dispositions distinguish:

```text
IN_SCOPE
EXTERNAL_BOUNDARY
ANALYSIS_SUPPORT
```

An input disposition does not itself create a program identity. In particular,
configuration and dependency metadata can be support inputs without being
program entities.

### Snapshot identity

The snapshot manifest identifies all immutable inputs capable of changing a
contracted fact:

```text
source state
declared boundary
effective inputs
relevant build/language/dependency configuration
extractor identity/version
core contract version
capability/profile versions
extractor configuration
```

The exact digest and serialization remain implementation choices. The
manifest must make the construction reconstructible. Snapshot identity is
not World revision, source revision, semantic identity, or lineage identity.

### Deterministic reconstruction

Identical immutable inputs, extractor/profile versions, and configuration MUST
produce identical snapshot metadata, identity descriptors/IDs, relation
tuples, evidence coordinates, resolution outcomes, and receipt values. Output
order, process IDs, temporary paths, cache state, or hash-map iteration MUST
not affect durable output.

### First-class identities

The receipt declares identity surfaces and the mechanical reason each exists.
The extractor may expose modules, source units, types, interfaces, callables,
methods, signatures, parameters, data/members, call sites, or extension
surfaces. It must not emit arbitrary syntax nodes merely because the
implementation can see them.

Source coordinates, display names, compiler objects, and AST nodes are not
automatically identities. Snapshot-local IDs make no cross-snapshot claim.

### Structural context

Each emitted identity is a root, an external boundary identity, or a child in
an inspectable native structural-context relation. The relation expresses
mechanical declaration/lexical placement, such as:

```text
module -> source unit -> callable -> nested callable
type -> method
callable -> call site
```

It does not mean semantic `part_of`, visual containment, runtime
instantiation, or governance significance.

### Evidence and provenance

Each identity and mechanical claim has enough evidence to reproduce why it was
emitted. Evidence records immutable input identity/digest, exact range or
non-source location, declaration/definition/occurrence role where relevant,
extractor/profile versions, and resolution information where relevant.

The World may use `SourceObservation` and `AssertionGrounding` for these
pointers. The extractor must not depend on a private database to recover its
own evidence and need not copy complete source bodies into semantic tuples.

### Closure and uncertainty

Every relation endpoint has a represented identity. A known endpoint beyond
the declared boundary is represented as an external stub. An unresolved
endpoint has no guessed positive edge and has an explicit outcome record.

Capabilities that resolve relationships use the common outcomes:

```text
RESOLVED
MULTIPLE_CANDIDATES
UNRESOLVED
```

The outcome is capability-specific mechanical knowledge. It does not mean
semantic applicability or governance significance. A missing relation is not
negative evidence unless a scoped completeness claim licenses that inference.

### Completeness

Completeness records are separate for each capability. A record identifies
the capability/version, covered universe, extraction basis, known gaps, and
result identity. Examples include complete program presence over declared
inputs, complete recognition of supported static imports, or static-complete
call-site outcomes under a particular analyzer.

The World completeness machinery remains authoritative. The construction
receipt summarizes or references those records and may not broaden them.

## Supplemental and replacement extractors

A **supplemental extractor** adds facts or a capability to an existing core
spine. It records the snapshot it supplements, its input/configuration
identity, its own versions, and whether it adds a new capability or evidence
to an unchanged assertion. It cannot weaken closure or silently replace the
meaning of an existing relation.

A **core/replacement extractor** constructs the mandatory core itself. It must
satisfy the same core requirements as every other conforming extractor. A
different extractor or profile creates a distinct snapshot representation;
cross-snapshot continuity remains a later explicit comparison.

No plugin registry, loader, or command interface is implied by these
semantics.

## SpineConstructionReceipt

Every construction SHOULD emit a
`SpineConstructionReceipt` next to the sealed World. The current reference
implementation serializes it as
`spine.construction.receipt.json` and records its path, construction ID, and
digest in the snapshot manifest.

The receipt is an inspectable construction/admission artifact, not a second
truth system and not a replacement for individual completeness records.

```yaml
receipt_version: spine_construction_receipt/v1
construction_id: ...
conformance:
  status: PASS | CONTRACT_FAILURE
  diagnostics: [...]
snapshot:
  id: ...
  source_state: ...
  declared_boundary: ...
  effective_inputs: [...]
  configuration: ...
  extractor: {id: ..., version: ...}
  core_contract: {id: spine_core, version: v1}
  capability_profiles: [{id: ..., version: ...}]
capabilities:
  - id: ...
    version: ...
    status: COMPLETE | STATIC_COMPLETE | PARTIAL | INCOMPLETE | UNKNOWN | NOT_PRODUCED
    scope: ...
    completeness_basis: ...
    completeness_receipt_refs: [...]
    known_gaps: [...]
identity_surfaces:
  - kind: ...
    semantic_basis: ...
    emitted_count: ...
    context_model: ...
resolution_summary: ...
boundary_summary: ...
losses: ...
representative_examples: ...
comparison_readiness: {observations: [...]}
acceptance: optional
```

`NOT_PRODUCED` means the capability was not claimed. It is distinct from an
empty complete capability, which means the extractor completed that scoped
capability and found no emitted facts. A receipt must never use one to imply
the other.

### Loss disclosure

Material losses known to the extractor MUST be disclosed. Use categories such
as:

```text
COLLAPSES
DOES_NOT_REPRESENT
UNKNOWN
```

Examples are collapsing ordinary syntax into an enclosing callable,
omitting runtime-created routes, omitting component instances, leaving
reflection targets unresolved, or omitting external implementation bodies.

`losses: []` does not mean that nothing was lost. It means the extractor has
declared no known loss. The list is not presumed exhaustive; a representation
can lose distinctions the extractor did not recognize.

### Representative examples

The receipt should include a few human-readable examples showing input/range,
identity/context chain, relation, resolution state, and capability reference.
Examples are inspection aids, not a graph dump or a hidden quality score.

### Adequacy probes and acceptance

An optional purpose-specific adequacy probe records:

```yaml
question: ...
input_or_test: ...
observed_result: ...
relevant_capability: ...
implication: ...
receipt_ref: ...
```

For example, a probe may show that two component uses both localize only to
one page callable. That is evidence of purpose inadequacy for instance-level
UI linking, not a core failure.

An application MAY record acceptance of a receipt for a stated purpose and
conditions. Acceptance means adequate for that purpose under those
conditions. It does not mean globally complete or universally true.

### Comparison readiness

Cross-snapshot correspondence and delta remain separate operations. A receipt
may report observations such as deterministic rebuilds, preserved structural
descriptors, declaration and occurrence roles, exact source ranges, and known
loss disclosures. It must not promise that a later comparison will recognize
rename, move, split, merge, or deletion, claim universal lineage adequacy, or
emit an opaque lineage score. The detailed comparison boundary is defined in
[SPINE_COMPARISON_CONTRACT.md](SPINE_COMPARISON_CONTRACT.md).

## Admission

The candidate -> validate -> sealed lifecycle remains:

```text
construct candidate
  -> persist manifest, World facts, completeness records, receipt
  -> validate core and claimed capabilities
  -> publish immutable sealed World
```

Admission MUST reject at least:

- missing or malformed core identity/version;
- missing declared boundary or effective input manifest;
- missing or nondeterministic snapshot metadata;
- an in-scope emitted identity absent from explicit universe membership;
- invalid structural-context or relation endpoints;
- a known boundary endpoint silently discarded;
- unreconstructible evidence;
- malformed resolution states or claimed capability versions;
- a completeness claim broader than its recorded basis; or
- receipt fields inconsistent with the World records they summarize.

Capability limitations and purpose inadequacy do not fail admission when
declared honestly.

## Reference TypeScript fit

The current TypeScript Compiler API extractor is one conforming implementation
of this boundary. It uses Node and Python, TypeScript checker symbols,
UTF-16-to-UTF-8 conversion, package metadata, and a JSON manifest internally.
Those are profile details, not core requirements.

It currently claims code structure, imports, calls, type relations, source
evidence, program-universe membership, and external endpoint preservation. It
retains call-site identities because they provide useful evidence,
resolution, localization, and attachment granularity. It explicitly reports
that UI/component instances, routing, runtime dynamic targets, and external
implementation bodies are not represented.

## Deferred

This contract does not define plugins/loaders, a universal program ontology,
one universal granularity, Reads/Writes, control flow, UI or routing
semantics, semantic construction, adjudication, diff extraction, or
cross-version lineage.
