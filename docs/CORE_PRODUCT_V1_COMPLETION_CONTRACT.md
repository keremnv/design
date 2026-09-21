# Ontology Author — Core Product v1 Completion Contract

**Status: frozen acceptance contract, 2026-09-21.**

This document defines what must be true for the core Ontology Author product
to be complete enough for a v1 application to depend on it. It does not claim
that product-market value has been established. Acceptance results belong in
a separate record; they must not weaken this contract to fit an implementation.

Three questions remain separate:

```text
CORE CAPABILITY
Can heterogeneous evidence become inspectable relational operational
knowledge with explicit epistemic guarantees?

APPLICATION CAPABILITY
Can a real application use that machinery end-to-end for useful work?

VALUE
Does the application justify construction and maintenance cost
relative to alternatives?
```

Core v1 addresses the first. A complete application addresses the second.
External evaluation addresses the third. The kernel must not encode their
answers.

## 1. Core product thesis

Ontology Author constructs operational knowledge from heterogeneous evidence
while preserving the recorded conditions under which it was established and
the explicit limits on relying upon it. This does not assert that those
recorded conditions exhaust the interpretation's dependencies (see §6.7).

```text
HETEROGENEOUS SOURCES → EVIDENCE ADAPTATION → CONSTRUCTION
→ CANDIDATE RELATIONAL KNOWLEDGE → MECHANICAL ADMISSION / VALIDATION
→ SEALED WORLD → QUERY / INSPECTION / APPLICATION USE
```

The distinctive output is a queryable relational model whose semantic
assertions remain connected to evidence, construction origin, revision
context, and explicit epistemic limits. It is not merely an ontology file or
a model transcript.

## 2. Evidence adaptation

### 2.1 Responsibility

An adapter observes an external source and exposes mechanically trustworthy
addressing and reconstruction. It identifies the source, exact revision,
bounded observed material, reconstruction capability, mechanically observable
structure, and information lost or not interpreted.

It does not determine meaning, semantic class membership, authority standing,
ontology relations, semantic truth, or operational decisions.

### 2.2 Evidence as addressable material

The common observation is approximately:

```text
SourceObservation(provider, native_handle, source_revision,
                  native_location, optional locator/payload)
```

Coordinates are source-specific: Markdown byte spans; source-file declarations,
calls or ranges; table records/cells; API response fields under a version or
ETag. An observation must precisely identify and, where supported, reconstruct
the material on which downstream knowledge relied. Reconstruction limitations
must be explicit.

### 2.3 Appropriate evidence granularity

Expose the smallest useful mechanically defensible units:

- prose: document, section, heading, paragraph, list item, table cell, span, link;
- code: file, declaration, call site, range, compiler-resolved relation;
- structured data: dataset, record, field, range, query result.

An adapter may expose a paragraph or heading called "Payment Boundary". It
must not thereby create a semantic requirement, boundary, or `governs` claim.
Mechanical granularity must not become invented semantic granularity.

### 2.4 Interpreter consumption

```text
RAW SOURCE → ADAPTER → bounded reconstructible units
→ CONSTRUCTION PROJECTION → LLM / deterministic resolver / human
```

Adapters own addressability, revision identity, reconstruction, defensible
segmentation, and known losses. Construction owns relevance selection, context
size, questions, allowed vocabulary/identities, and candidate output shape.

Making evidence efficient to present to an interpreter does not authorize an
adapter to become a hidden ontology constructor.

## 3. Construction

Construction is executable semantic compilation: `construct(source, world)`.
It may use deterministic parsing, source adapters, static-analysis facts,
domain rules, LLM interpretation, human-authored mappings, or prior knowledge.

A construction program may implement the following operations using the
existing relational primitives; these are not built-in general-purpose
interpreters or guarantees of correct semantic interpretation:

1. Mechanical projection: a declaration becomes a program callable; a CSV row
   becomes a normalized record.
2. Normalization: different source forms are mapped to a shared vocabulary.
3. Identity construction: evidence from several sources is explicitly and
   groundedly related to one operational entity.
4. Relation construction: a relation such as `governs(requirement, component)`
   is established even when no source states that tuple verbatim.
5. Classification/abstraction: a callable may be classified as a provider,
   with an inspectable basis.
6. Cross-source synthesis: requirements, architecture, program structure, and
   configuration combine into reusable semantic joins.

A resulting cross-source relation may exist nowhere explicitly in the inputs.
That capability is a reason to construct a World; its economic value remains
an empirical question.

## 4. Evidence and construction remain separate

```text
EVIDENCE:     What exactly was observed?
CONSTRUCTION: What semantic knowledge should be constructed from it?
WORLD:        What was admitted, under which inspectable conditions?
APPLICATION:  What should be done with that knowledge?
```

The same evidence adapter should be usable with another ontology. Equivalent
observations from another adapter should be consumable by a constructor.
Domain-specific mechanical source structure is allowed: JSX containment may
be evidence structure; satisfying a purchase-confidence requirement is a
semantic construction.

## 5. The World

The durable semantic plane consists of thin referents, typed named n-ary
relations, assertions, grounding, and derivations. Its epistemic/system plane
preserves identity/revision, provenance, construction origin, derivation
dependencies, scoped completeness, explicit unknown/unresolved states where
represented, and historical immutability.

SQLite is an implementation choice. The contract is ordinary inspectable
relational knowledge, not hidden model state.

## 6. Epistemic guarantees

### 6.1 Structural integrity

Relations have declared roles and types. Invalid relation shapes are rejected
through the supported construction APIs. Construction is trusted executable
code, not an adversarial-code or arbitrary database-write sandbox.

### 6.2 Provenance

Assertions that require grounding retain inspectable evidence or prior
assertion support.
Admission checks the recorded support required by the chosen Contract. Source
address validity/reconstruction belongs to adapters; semantic adequacy and
source authenticity are not established by the mere presence of a pointer.

### 6.3 Historical scope and retention

A sealed World records knowledge relative to its construction inputs. Later
evidence must not rewrite that history. After reconstruction/publication,
both the prior and new sealed Worlds must remain independently addressable.
A mutable current pointer or atomic replacement alone is insufficient evidence
of historical retention.
The canonical v1 pattern is fresh-root publication as exercised by
`profiles/core_v1/build.py`; legacy in-place rebuilding is not that pattern.
See [the baseline](CORE_PRODUCT_V1_BASELINE.md) for the precise supported scope.

### 6.4 Origin

Preserve meaningful distinctions between mechanically projected, semantically
constructed, derived, or otherwise established knowledge where required by
the application contract.

### 6.5 Completeness and its enforcement boundary

Core records and exposes explicit scoped completeness. Absence does not imply
falsehood without appropriate completeness for the relevant universe.
Completeness is a recorded construction claim with scope, basis and execution/
revision context, not automatic proof that an arbitrary external universe was
exhaustively observed.

Completeness-gated negative/exhaustive inference belongs in supported
reasoning/read mechanisms and application logic. Arbitrary SQL remains an
escape hatch: core does not guarantee that a SQL consumer cannot misuse
absence. A complete finite enumeration must not be presented as completeness
over a broader external universe.

### 6.6 Uncertainty

Unknown or unresolved knowledge can remain explicitly unknown. It must not
silently collapse into false.

### 6.7 Dependency honesty

For a declared maintenance/derivation basis the system may guarantee that the
declared dependencies are inspectable and their later state assessable. It
must not generally claim they exhaust every fact on which the interpretation
depends. `PRESERVED` means the recorded maintenance conditions were preserved,
not that semantic truth was exhaustively re-proven. Dependency completeness
belongs to construction/application logic unless a stronger specific contract
establishes it.

## 7. Candidate → validate → seal

Construction writes candidate state, never accepted historical state.
Publication must produce a valid new sealed World or leave the prior World
intact. Successful reconstruction must also retain the prior World at an
independent address (§6.3). Renewed knowledge is newly published durable state.

## 8. Consumption

Core exposes SQL, Python, schema/role discovery, relation rows, assertion
identities, grounding/provenance, and derivation/completeness inspection.
Consumers must discover what is known, its representation, origin, unresolved
questions, and completeness limits without private runtime state. Agent-specific
APIs are optional and are not prerequisites for World correctness.

## 9. What core v1 does not require

Semantic/program maintenance warrants, ProgramDelta, canonical program
correspondence, authority classes, GovernanceCase, adoption or Git-candidate
workflows, design law, PaymentProvider, automatic semantic renewal, a universal
ontology/schema, or a plugin framework are not core-v1 requirements. They may
be application/runtime mechanisms.

## 10. Golden heterogeneous-source acceptance scenario

One deliberately small, complete scenario must consume at least three
materially different evidence forms, preferably prose/requirements, program
source or mechanical program structure, and structured configuration/tabular
data. At least one useful semantic relation must require a cross-source join
that cannot be copied from any one source.

For example, requirements name a boundary, program source contains callables,
and configuration identifies an implementation/provider. Construction relates
requirements, boundaries, program entities, and providers through grounded
`governs`, `realized_by`, `uses_provider`, or reachability relations.

Include at least one ambiguous cross-source correspondence that remains
explicitly unresolved. A live LLM is **not required**: human-authored or
deterministic semantic interpretation suffices when origin and evidence are
represented honestly.

## 11. Golden acceptance criteria

### Evidence

- Every source has an adapter or trustworthy observation mechanism.
- Relevant material is revisioned and addressable.
- Evidence can be reconstructed, or its reconstruction limitation is explicit.
- Adapters do not assign semantic truth.

### Construction

- One program consumes heterogeneous observations and creates semantic
  identities/relations, including a genuine cross-source join.
- Claims retain their evidence basis.
- Mechanical and interpretive operations are distinguishable where material.

### Relational output

- Knowledge is stored in typed queryable relations.
- Queries can consume the joins without rereading raw evidence.
- Schema/roles and required stable assertion identities are inspectable.

### Epistemic behavior

- Grounded assertions expose grounding and construction origin/status.
- An intentionally ambiguous case remains unresolved.
- Recorded completeness permits only appropriately scoped negative conclusions;
  incomplete/unknown scope prevents stronger conclusions in supported reasoning.
- Sealed history remains unchanged after publication and consumption.

### Lifecycle

- Construction happens in candidate state.
- Invalid publication fails safely.
- Successful publication atomically establishes a valid sealed World.
- Reconstruction retains both old and new Worlds at independent addresses;
  replacing a current pointer or artifact alone does not satisfy this test.

### Independent consumption

A fresh consumer receives **only the sealed bundle and supported read
interfaces**: no constructor internals, fixture-specific helpers, or raw-source
access. It discovers schema and answers from the World:

```text
What requirements govern this operational entity?
What evidence supports that relationship?
Which knowledge was mechanically projected versus semantically constructed?
What relevant question remains unresolved?
What completeness guarantee permits or prevents a negative conclusion?
```

The consumer must not reconstruct the joins from original evidence. Evidence
reconstruction is tested independently from this consumption restriction.

## 12. Complete application criterion

A complete application defines a real bounded domain, constructs useful
knowledge, asks meaningful questions, uses supported sealed-World reads,
surfaces unresolvedness, keeps decisions outside the kernel, and supplies an
end-to-end user/agent workflow.

Maintenance, authority, governance, adequacy, comparison, and semantic
persistence are included only when needed. Applications may bind knowledge
to evidence regions, program entities, program relations, or domain-specific
structural objects. There is no universal canonical-program-entity requirement.

## 13. Lean-architecture rule

A new core primitive must protect a generic guarantee that cannot adequately
be expressed using referents, relations, assertions, grounding, derivations,
revision, and completeness. Reuse, similar payloads, workflow convenience, or
an LLM's preferred representation are insufficient reasons. Reusable application
mechanics remain above the kernel.

## 14. Deferred cleanup

Legacy explicit Purpose compatibility, Contract's mixed admission/resolution
concerns, obligation/candidate/resolution/adjudication storage under core,
governance naming, and eventual read-surface separation do not block core v1.
Do not refactor them for conceptual purity before the golden path and first
complete application are finished.

## 15. Completion sequence

1. Freeze this corrected contract.
2. Build the golden heterogeneous-source end-to-end acceptance scenario.
3. Identify missing core capability strictly from scenario failures.
4. Complete one real application.
5. Observe which stronger application/runtime mechanisms it needs.
6. Revisit deferred architecture debt.
7. Evaluate value/economics with external tasks.

Classify scenario failures as missing core capability, bad constructor,
application-specific need, or fixture limitation before introducing machinery.
The target is the smallest coherent core that can construct, preserve, publish,
and expose useful relational knowledge without overstating what it proves.
