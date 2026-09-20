# Program-spine contract

This document defines the smallest mechanically trustworthy program
representation that software governance may consume without reparsing or
semantically reinterpreting code structure. It governs durable output, not the
implementation used to produce that output.

The normative words **MUST**, **MAY**, and **DEFERRED** have their usual
contract meaning. A standard capability has a versioned identifier. Changing
the meaning of a capability, relation, endpoint, resolution state, or
completeness basis requires a new capability version.

## Architectural position

```text
CODE SNAPSHOT
      |
      | deterministic mechanical analysis
      v
PROGRAM SPINE
      |
      +-- program identities
      +-- mechanical claims and relations
      +-- exact program evidence
      |
      v
SEMANTIC / GOVERNANCE STRUCTURE
```

The spine is part of the governed World. It is mechanically derived,
versioned, reconstructible from declared inputs, and purpose-independent in
its fact contract. It is not an agent-authored ontology. An agent may
interpret program objects later; it must not manufacture a fact that a
declared capability says is mechanically derivable.

The architecture has three contract layers:

```text
spine_core/v1
  epistemic, provenance, integrity, closure, and admission guarantees

standard capabilities
  versioned mechanical meanings owned by this project

project/framework extensions
  additional declared meanings that compose without redefining standards
```

An extractor can be built with a compiler API, an existing structural index,
a deterministic project script, a framework analyzer, or an agent-authored
program. The implementation is private. Durable output must identify the
core and every claimed capability.

## Snapshot and declared universe

A **program snapshot** is the immutable mechanical state against which a
spine is true. Git revision alone is insufficient when generated inputs,
configuration, dependency resolution, extractor behavior, or capability
profiles can affect facts.

The snapshot manifest MUST identify, directly or through content-addressed
manifests:

```text
source state
user-declared program boundary
effective consumed inputs
relevant build/language/dependency configuration
extractor identity and version
spine core contract and capability versions
extractor configuration
```

The source state and the mechanism interpreting it are separate identities.
An analyzer upgrade can produce a different snapshot representation from the
same source state. Snapshot-local program IDs make no cross-version
continuity claim.

The user or application declares the program boundary. The extractor
mechanically expands it into effective inputs and resulting program
identities. A manifest MUST distinguish at least:

```text
IN_SCOPE           material whose program identities belong to the governed universe
EXTERNAL_BOUNDARY  known endpoint material outside that universe
ANALYSIS_SUPPORT   material consumed to analyze or resolve the snapshot
```

Support material does not automatically become a program identity. An
external endpoint may become a stub when a claimed relation needs it.

## Exhaustive presence and sparse significance

Within a declared capability universe:

```text
PROGRAM PRESENCE IS EXHAUSTIVE.
SEMANTIC / GOVERNANCE SIGNIFICANCE IS SPARSE.
```

Every first-class in-scope identity established by a claimed capability MUST
be represented in an explicit membership relation for that snapshot. The
generic referent table alone is not the program universe. Presence in the
universe is distinct from attachment to semantic or governance claims.

The World may therefore contain an unattached program identity. Its absence
of semantic attachment is not evidence that it is irrelevant or ungoverned.
Negative governance conclusions require a relevant completeness claim over
an appropriate universe.

## Program identities and evidence

An extractor MUST declare its first-class identity surfaces and the mechanical
reason each surface deserves durable identity. It need not expose every AST
node, syntax token, compiler object, or source phrase.

Typical surfaces include modules/source units, types, interfaces, callables,
methods, signatures, parameters, data or members, and call sites. The set is
profile-specific. A source range is evidence or a manifestation location; it
is not automatically a program identity. One identity may have several
locations, and one location may localize to several enclosing identities.

Every first-class identity and durable mechanical relation MUST have
reconstructible evidence identifying, as applicable:

```text
immutable input identity or digest
exact source/configuration range or non-source location
declaration/definition/occurrence role
extractor and capability versions
resolution information
```

The canonical coordinate convention is owned by the capability. Evidence
must be recoverable from immutable inputs without copying complete source
bodies into semantic relations.

## Structural context and relations

Each emitted identity MUST have inspectable mechanical structural context. A
native context relation may express module-to-callable, type-to-method,
callable-to-nested-callable, or callable-to-call-site placement. It does not
mean semantic `part_of`, visual containment, runtime instantiation, or
governance relevance.

Standard capabilities own their relation meanings. A capability MUST state
its endpoint kinds, positive assertion rule, evidence, uncertainty, boundary
behavior, known omissions, and completeness basis. Precise predicates are
preferred over a universal `depends_on` relation.

For invocation, a call site remains a first-class support identity when the
claimed capability needs source localization, resolution state, attachment
granularity, or later comparison:

```text
owning callable -> structural context -> call site -> invokes -> target
```

Resolved targets receive a positive relation. Multiple candidates and
unresolved calls retain explicit outcome records without a guessed target.
Omitted relations have open-world meaning unless a capability-specific
completeness claim licenses a narrower conclusion.

## Boundary and endpoint closure

Every referent endpoint of a persisted mechanical relation MUST have a
represented identity. An in-scope endpoint MUST belong to the snapshot
universe. A known endpoint outside the boundary MUST be represented as an
external identity with explicit boundary classification. An external stub
does not imply that its implementation was analyzed, trusted, or governed.

When analysis knows that a relation crosses the boundary, it MUST preserve
the known endpoint or preserve an explicit unresolved outcome. It must not
silently discard the relation because the endpoint is outside the workspace.

## Uncertainty and completeness

Mechanical analysis MUST preserve uncertainty. The standard resolution
outcomes are:

```text
RESOLVED
MULTIPLE_CANDIDATES
UNRESOLVED
```

These states describe a particular capability's mechanical resolution. They
do not describe semantic truth or governance applicability. A missing
relation is not automatically a negative fact.

Completeness is capability-scoped. A construction may be complete over
program-universe membership while only statically complete for resolved call
sites and not complete for runtime targets. A completeness record MUST name:

```text
capability and version
covered universe
basis and analyzer conditions
known gaps
result identity
```

The existing World completeness machinery remains the authority for its
individual records. A construction receipt may summarize or reference those
records but may not broaden them.

## Construction outcomes

These outcomes remain distinct:

```text
CONTRACT FAILURE
  durable output violates the core or a claimed capability; reject it.

CAPABILITY LIMITATION
  a capability was not produced or static knowledge remained unresolved;
  allow it when explicitly declared.

PURPOSE INADEQUACY
  the valid representation is too coarse for a particular governance use;
  evaluate this through purpose-specific adequacy probes.
```

The hard contract guarantees honesty, reproducibility, declared semantics,
grounding, closure, uncertainty, and scoped completeness. It does not
guarantee one universally adequate program granularity.

## World lifecycle and lineage

Program identities and mechanical claims are ordinary World referents and
typed relations. Mechanical facts are BASE assertions with exact grounding;
deterministic convenience relations may be DERIVED from persisted inputs.
No generic kernel primitive is required by this contract.

The lifecycle is:

```text
construct candidate
  -> write manifest, facts, capability records, and construction receipt
  -> validate core and claimed capabilities
  -> publish immutable sealed World
```

Cross-snapshot correspondence and program delta remain separate comparison
operations. A snapshot-local program ID is a manifestation identity for that
snapshot; it is not a permanent cross-version identity. Implementations should
expose deterministic snapshot-local descriptors, structural context,
declaration and occurrence evidence, input/configuration identity, and known
losses so a later comparison can establish continuity or report ambiguity.
The spine itself does not promise rename, move, split, merge, delete, or any
other lineage result. Detailed correspondence and delta semantics belong to
[SPINE_COMPARISON_CONTRACT.md](SPINE_COMPARISON_CONTRACT.md).

Attaching authoritative non-code material to snapshot-local program identities
belongs to
[AUTHORITY_CONSTRUCTION_CONTRACT.md](AUTHORITY_CONSTRUCTION_CONTRACT.md).
Maintenance of those attachments across program snapshots belongs to
[AUTHORITY_MAINTENANCE_CONTRACT.md](AUTHORITY_MAINTENANCE_CONTRACT.md).
The spine remains mechanically derived and purpose-independent. Correspondence
does not copy or renew those attachments.

## Extensions

An extension MUST declare:

- an ID and version;
- identity and endpoint kinds;
- the mechanical construction rule;
- evidence and reconstruction requirements;
- uncertainty and omission semantics;
- completeness scope; and
- composition behavior with core and standard capabilities.

It MAY add information. It MUST NOT silently redefine a standard capability,
turn interpretation into mechanical fact, treat omitted extension facts as
false, or require every extractor to emit the extension.

## Deliberately deferred

This contract does not choose an extraction technology, plugin protocol,
universal program ontology, universal granularity, framework capability,
cross-version lineage algorithm, diff algorithm, runtime completeness model,
or mandatory interactive acceptance flow. These choices must preserve the
contract boundary when introduced.
