# TypeScript/TSX spine profile

This document defines the first language-specific profile for the native
program spine. It is subordinate to
[`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md) and
[`SPINE_EXTRACTOR_CONTRACT.md`](SPINE_EXTRACTOR_CONTRACT.md). TypeScript is
construction machinery; the durable output is the native program-spine
contract.

## Profile identity and capabilities

The reference extractor identifies itself as:

```text
profile: typescript-spine-v0
extractor: ontology_author.program_spine.typescript-compiler-api@v0
core: spine_core/v1
```

It claims these standard capabilities:

```text
spine.code_structure/v1
spine.imports/v1
spine.calls/v1
spine.type_relations/v1
```

The construction also records core coverage for program-universe membership,
source evidence, and external endpoint preservation. Those records describe
the construction envelope; they do not make an unclaimed analysis capability
complete.

The reference extractor does not produce UI/component-instance, routing,
Reads/Writes, control-flow, state/event, semantic-construction, or runtime
lineage capabilities. A construction receipt may declare these as
`NOT_PRODUCED` when their absence matters.

## User-declared boundary and inputs

The Python boundary declaration has this semantic shape:

```text
workspace_roots
projects                 one or more tsconfig paths
package_roots
include_tests
generated_files          include | exclude
declarations             declared policy
external_dependencies    preserve known endpoints
```

The user declares roots and projects. The extractor expands each project
configuration with the TypeScript configuration parser and records the
effective consumed input set. It does not allow the user to enumerate
program entities by hand.

Effective inputs are classified as:

```text
IN_SCOPE
  source files under an admitted package root, subject to test/generated and
  declaration policy; their supported first-class program identities belong
  to the snapshot universe.

EXTERNAL_BOUNDARY
  source material in the workspace but outside the declared package roots;
  it may establish a known endpoint without making its implementation local.

ANALYSIS_SUPPORT
  tsconfig chains, compiler libraries, node_modules, package metadata, tests
  or generated files excluded by policy, and other consumed support material.
```

An effective input can be present without becoming a program identity. A
TypeScript compiler input is not automatically an in-scope program file.
Project references and extended configurations are recorded as configuration
and support inputs. Declaration files under an admitted package root follow
the declared declaration policy. Tests and generated files follow their
explicit boundary settings.

The manifest retains both the normalized user declaration and each effective
input's path, digest, byte length, readability, disposition, role, project,
and analysis outcome.

## Snapshot identity

The snapshot is content-addressed from the normalized boundary, effective
input manifest, relevant configuration and dependency-resolution data,
TypeScript version, extractor/profile identity, core version, and claimed
capability versions. The source-state digest and snapshot ID are separate
fields. A source revision alone is not sufficient.

The manifest and the World `program_snapshot` relation retain the provenance.
The World relation has these native roles:

```text
program_snapshot(
  snapshot REFERENT,
  source_state TEXT,
  boundary_digest TEXT,
  inputs_digest TEXT,
  configuration TEXT,
  analyzer TEXT,
  extractor TEXT,
  core_contract TEXT
)
```

The relation is one snapshot's mechanical provenance. World revision and
future lineage are separate concepts.

## Snapshot-local identity

IDs use the form:

```text
program:ts:<snapshot-id>:<identity-kind>:<sha256(descriptor)[0:24]>
```

The descriptor is deterministic and contains a stable category, module
descriptor, native identity kind, and checker-derived symbol or deterministic
owner-local discriminator. It never uses a source line number as identity.
The snapshot ID prevents an ID from claiming cross-version permanence.

The current native identity surfaces are:

| Identity kind | What is preserved | When it deserves identity |
|---|---|---|
| `module` | a source module/file context | one admitted source module participates in the program model |
| `source_unit` | the source unit under its module | the source file is an explicit structural context |
| `class` | a named or checker-identifiable class | declaration identity is mechanically available |
| `interface` | a named interface | declaration identity is mechanically available |
| `callable` | a named function or required function expression/arrow | callable structure or a required relation needs it |
| `method` | a method, accessor, or constructor | member callable identity is mechanically meaningful |
| `signature` | a callable signature, including overload declarations | overload and callable contract evidence needs it |
| `parameter` | a named or mechanically meaningful parameter | parameter/type structure is emitted by this profile |
| `data` | a meaningful field, property, or variable declaration | declaration/type structure needs the data object |
| `call_site` | a call/new expression occurrence | source localization, context, resolution, or invocation needs it |
| `type` | a resolved type endpoint without local declaration | a type relation requires a known boundary target |
```

Display names are labels, not identity. Aliases are resolved through the
checker before descriptor construction and do not create duplicate target
identities. Same-name declarations in different modules/scopes receive
different descriptors through module and checker context. Declaration merging
uses the checker symbol where it can be recovered. Overloaded declarations
share the bound callable identity and have separate signature identities.

Nested named callables use their owning descriptor. Named function expressions
and arrows assigned to a binding use the binding's checker identity. An
anonymous function or arrow is emitted only when it is needed for the claimed
structure or calls capability; its deterministic owner-local ordinal is a
mechanical discriminator. Unused anonymous functions can remain source
evidence without becoming identities.

Compiler objects and AST nodes are never durable public kinds. They are used
only to construct these native descriptors.

## Canonical source evidence

The canonical persisted source location is a half-open UTF-8 byte range over
the exact immutable input bytes:

```text
bytes:<start>:<end>
```

The TypeScript compiler reports UTF-16 code-unit offsets. The adapter converts
them by iterating the decoded immutable UTF-8 text. ASCII, CRLF/LF, Unicode,
and surrogate-pair boundaries are tested. A range that splits a surrogate pair
or lies outside the input is invalid.

Each `SourceObservation` records the provider, path-plus-content digest,
source-state identity, and canonical byte range. Manifest-level evidence uses
the same immutable input identity with `input` location. The profile does not
copy complete source bodies into World relations.

Every identity, structural relation, import, invocation, type relation,
resolution outcome, and capability record has source/configuration grounding
or manifest evidence sufficient to reconstruct the emitted fact.

## Explicit program universe

The explicit native universe uses:

```text
program_entity(snapshot REFERENT, entity REFERENT, kind TEXT, boundary TEXT)
```

Every emitted in-scope identity is present in this relation, including
unattached helpers and call-site support identities. External endpoint stubs
are also represented there with `EXTERNAL_BOUNDARY`. Analysis support is
represented by `program_input`, not as program presence.

The companion relation exposes identity surface and synthetic status:

```text
program_entity_kind(
  snapshot REFERENT,
  entity REFERENT,
  kind TEXT,
  synthetic BOOLEAN
)
```

The generic referent table is not a substitute for either relation.

The profile also persists the deterministic descriptor used to construct each
snapshot-local identity:

```text
program_identity_descriptor(
  snapshot REFERENT,
  entity REFERENT,
  kind TEXT,
  descriptor TEXT
)
```

This is comparison input, not a cross-snapshot identity. The descriptor is
profile-owned construction metadata: a stable snapshot-local construction key
from category, module, native kind, and checker symbol or owner-local
discriminator. Identical immutable inputs reproduce the same descriptor. The
profile does not declare that descriptor equality across compatible snapshots
licenses identity continuation. A comparison may use compatible descriptor
equality as heuristic evidence. Rename and move still require structural,
signature, or other comparison evidence, and even an unchanged descriptor is
not mechanically entailed sameness.

## Native structural context

The profile uses:

```text
structural_context(snapshot REFERENT, parent REFERENT, child REFERENT)
```

It means mechanically observed declaration or lexical context. Examples are:

```text
module -> source_unit
source_unit -> class/interface/callable
class -> method/data
callable -> nested callable/signature/parameter/call_site
```

The relation does not mean semantic `part_of`, visual containment, runtime
instantiation, or governance significance. An external stub need not have an
implementation context.

## Imports capability

`spine.imports/v1` describes static module import/export occurrences recognized
by the TypeScript compiler and public module resolver.

```text
program_imports(snapshot REFERENT, importer REFERENT, imported REFERENT)
```

The importer is the source module. The imported endpoint is an in-scope module
or an external module stub. The assertion is grounded at the exact string
specifier range and its grounding metadata retains the raw specifier.

Each recognized occurrence receives a `program_resolution` record with:

```text
capability: spine.imports
status: RESOLVED | MULTIPLE_CANDIDATES | UNRESOLVED
evidence_key: immutable path and byte range
details: raw specifier, target file, or diagnostic reason
```

The current resolver normally produces one resolved module or an unresolved
outcome. The raw textual specifier is evidence, not the canonical endpoint
when resolution establishes a stronger target.

## Calls capability

`spine.calls/v1` describes recognized call and constructor occurrences. Its
native shape preserves the call site:

```text
owning callable
      -> structural_context -> call_site
      -> program_invokes(call_site, target)
```

```text
program_invokes(snapshot REFERENT, call_site REFERENT, target REFERENT)
```

Every recognized call/new expression receives a `call_site` identity and a
resolution record grounded at the complete call-expression byte range. A
resolved call emits exactly one positive `program_invokes` assertion.

Resolution semantics are:

```text
RESOLVED
  exactly one mechanically established target; emit the invocation edge.

MULTIPLE_CANDIDATES
  more than one mechanically possible target; retain candidate records and
  do not choose one positive edge.

UNRESOLVED
  no target was mechanically established; retain the occurrence and reason.
```

`program_resolution_candidate` retains candidate identities for the middle
state. A missing invocation edge never means that no call exists.

The checker supports direct functions, methods, constructors, overload
selection, imported callables, and some union-method cases. Computed
properties, `any`, reflection, dynamic dispatch, higher-order callbacks, and
incomplete code can remain unresolved or multiple-candidate. The profile does
not guess, and it does not use a generic dispatch relation as a substitute for
an unresolved call outcome.

## Type-relations capability

`spine.type_relations/v1` retains only mechanically clear relations currently
produced by the reference extractor:

```text
program_has_type(snapshot REFERENT, subject REFERENT, type REFERENT)
program_extends(snapshot REFERENT, subtype REFERENT, supertype REFERENT)
program_implements(snapshot REFERENT, implementer REFERENT, interface REFERENT)
```

`program_has_type` is emitted for meaningful property, parameter, and variable
declaration type annotations when the checker resolves the type. `extends` and
`implements` are emitted from explicit heritage clauses. A known external type
endpoint is represented as an external stub. No relation is emitted when the
checker cannot establish the endpoint.

These predicates do not imply runtime assignability, all inferred types, or a
complete type-theoretic model. Reads/Writes and deeper data flow are deferred.

## Resolution and capability records

The profile stores outcome metadata in:

```text
program_resolution(
  snapshot REFERENT,
  subject REFERENT,
  capability TEXT,
  status TEXT,
  evidence_key TEXT,
  details TEXT
)

program_resolution_candidate(
  snapshot REFERENT,
  subject REFERENT,
  capability TEXT,
  candidate REFERENT
)
```

The capability-scoped completeness records are:

```text
program_capability(
  snapshot REFERENT,
  capability TEXT,
  version TEXT,
  status TEXT,
  universe TEXT,
  basis TEXT,
  known_gaps TEXT,
  result TEXT
)
```

The current status basis is:

| Capability | Complete means | It does not license |
|---|---|---|
| program universe | every declared effective input was accounted for and every emitted first-class identity was a membership row | that compiler internals or runtime-created objects are all represented |
| source evidence | every emitted identity/claim has reconstructible input/range evidence | that unrecognized source distinctions do not exist |
| code structure | supported declarations and structural context in analyzed inputs were processed | unsupported syntax or runtime structure is absent |
| imports | recognized static module occurrences received resolved or unresolved outcomes | that dynamic loading is absent |
| calls | recognized call sites received outcomes; `STATIC_COMPLETE` means this under the checker basis | that all runtime targets are known |
| type relations | recognized explicit type/heritage relationships were processed | that every inferred or runtime type relation is represented |
| external endpoints | every known endpoint needed by an emitted relation has a stub | that external bodies were analyzed or trusted |
|

The status is not a global `spine_complete` flag. The receipt references the
assertion IDs of these World records and cannot broaden their basis.

## External endpoint identity

Known endpoints outside the governed package roots use the same snapshot-local
ID shape with `external` as the identity category. The descriptor prefers:

```text
resolved package name
resolved package version
package-relative declaration/module path
resolved member/checker symbol when available
```

If package metadata is unavailable, the resolved path and module specifier
are retained as the strongest available mechanical descriptor. The endpoint
is an `EXTERNAL_BOUNDARY` member of `program_entity`, has source evidence at
the local import/call/type occurrence, and has no asserted implementation
body or internal structural facts.

A workspace file outside `package_roots` exercises the same boundary behavior
as a third-party package. `ANALYSIS_SUPPORT` material such as compiler library
files is not silently promoted to governed program presence.

## Synthetic identity policy

The profile does not persist compiler implementation artifacts or arbitrary AST
nodes. A synthetic identity is emitted only when the native capabilities need
it. Current examples are call sites, required anonymous callable support, and
constructor method support. `synthetic: true` is explicit in
`program_entity_kind` and the identity remains grounded to a concrete source
range.

## Admission

Before candidate publication, the application checks:

- manifest and receipt identify `spine_core/v1` and the TypeScript profile;
- declared boundary and effective inputs are present and reconstructible;
- snapshot metadata is deterministic and complete;
- every emitted identity has `program_entity` and `program_entity_kind` rows;
- every structural, import, invocation, and type endpoint is represented;
- known external endpoints were preserved;
- every identity and assertion has source or manifest grounding;
- every resolution state has valid candidate cardinality;
- every claimed capability has a version, scope, basis, and World record; and
- the construction receipt agrees with the World records it summarizes.

The generic World referent foreign-key checks provide the low-level endpoint
integrity. These profile checks add snapshot membership, boundary, evidence,
and capability semantics without changing the kernel.

## Reference fixture matrix

The implementation must retain tests for:

1. modules and resolved/unresolved imports;
2. class, interface, callable, method, signature, parameter, and data
   identities;
3. nested named and required anonymous callables;
4. a resolved direct call and constructor/method calls;
5. overload resolution;
6. union/dynamic calls with explicit uncertainty and no guessed edge;
7. third-party and out-of-boundary workspace endpoints;
8. an unattached helper retained in the explicit universe;
9. call-site structural context and exact byte grounding;
10. source-range localization to containing program identities;
11. ASCII, Unicode, surrogate-pair, CRLF, and LF coordinate conversion;
12. identical immutable input producing identical IDs, facts, and receipt;
13. relation endpoint closure and malformed-candidate admission failure; and
14. construction receipt inspection, known-loss disclosure, and capability
    record reference integrity.

Tests assert native profile outcomes and World relations, not compiler AST node
shapes.

## Deferred

This profile does not implement or define React rendering/component instances,
routing, UI semantics, Reads/Writes, Addresses, full control flow, deep data
flow, state/event extraction, cross-version lineage, diffing, semantic
construction, or source-authority linking. Case assembly and adjudication
are outside this profile;
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md) specifies case
assembly.
