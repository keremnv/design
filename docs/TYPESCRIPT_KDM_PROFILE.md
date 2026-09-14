# TypeScript/TSX KDM extraction profile

This document defines the first language-specific extraction contract for
TypeScript and TSX. It is subordinate to:

- [`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md);
- [`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md);
- [`PROGRAM_SPINE_CONTRACT.md`](PROGRAM_SPINE_CONTRACT.md); and
- [`KDM_PROFILE.md`](KDM_PROFILE.md).

It defines how TypeScript mechanical analysis is projected into the selected
KDM 1.4 semantics and then into the Ontology Author World. It does not redefine
the program spine, KDM, or governance semantics.

The direction is:

```text
TypeScript source and configuration
        -> TypeScript mechanical analysis
        -> selected KDM 1.4 semantics
        -> Ontology Author World
```

The TypeScript compiler's `Program`, `SourceFile`, `Symbol`, `Type`, and
`Signature` concepts are extraction machinery. They are not public program
spine kinds. The [TypeScript compiler API documentation](https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API)
is useful implementation background, but this profile exposes only the KDM
meaning and the evidence needed to reproduce it.

## Contract status and capability boundary

The profile is capability-layered. A TypeScript snapshot MUST declare which
capabilities were produced and a separate completeness status and basis for
each capability. A snapshot that omits a capability has not thereby proved
that the corresponding facts are absent.

### V0 required capabilities

1. **Program-universe membership:** explicit snapshot membership for every
   admitted TypeScript KDM program element, including unattached elements.
2. **Source traceability:** KDM `SourceRef`/`SourceRegion` meaning through
   reconstructible TypeScript source evidence.
3. **Code modules:** KDM `Module` and `CompilationUnit` for in-scope source
   units, with namespace/package structure where mechanically available.
4. **Declaration structure:** KDM `ClassUnit`, `InterfaceUnit`,
   `CallableUnit`, `MethodUnit`, `Signature`, and mechanically meaningful
   `DataElement` instances.
5. **KDM ownership:** structural owner/owned-element relationships for emitted
   KDM elements.
6. **KDM `Imports`:** recognized static module imports and their mechanically
   resolved local or external targets.
7. **KDM `Calls`:** recognized call sites with explicit resolution outcomes.
8. **External/boundary endpoints:** known external targets preserved as
   snapshot-local KDM-compatible stubs.
9. **Snapshot/build provenance:** the user boundary, effective consumed inputs,
   TypeScript configuration and project-resolution inputs, extractor/profile
   versions, and source digests.

The required slice is useful for structural localization and static impact
queries without requiring React semantics, a complete control-flow graph, or
deep data-flow analysis.

### Next capability

- KDM `Reads`, `Writes`, and `Addresses`.

These belong in the next capability rather than required v0. TypeScript can
mechanically expose many property and variable accesses, but a useful and
portable KDM data-access profile requires decisions about aliases, narrowing,
destructuring, side effects, library behavior, and generated code. Calls and
ownership provide a useful first impact backbone while those decisions remain
unsettled. A later capability MUST use the KDM data-relation meanings; it must
not add a broad TypeScript-specific `reads` or `writes` synonym.

### Deferred

- KDM UI and React composition/rendering;
- routing and navigation;
- KDM Event/state extraction;
- full `ControlFlow`/`Flow` output;
- deep data flow, SSA, taint, or runtime behavior;
- framework-specific lifecycle semantics;
- semantic construction, source adapters, case assembly, and adjudication; and
- cross-snapshot lineage.

## User-declared TypeScript universe

The user or application declares a boundary and configuration. The extractor
expands that declaration mechanically. It does not ask the user to enumerate
the resulting program entities.

A conceptual declaration is:

```yaml
program_boundary:
  workspace_roots:
    - packages/checkout
  projects:
    - tsconfig: packages/checkout/tsconfig.json
  package_roots:
    - packages/checkout
  include_tests: false
  generated_files: exclude
  declarations: in_scope_if_under_boundary
  external_dependencies: preserve_known_endpoints
```

This is illustrative configuration, not a required serialization. The
declaration MUST be retained exactly enough to reconstruct what the user
requested. The effective input manifest MUST separately record what the
TypeScript project expansion actually consumed.

### Expansion rules

The extractor resolves, records, and fingerprints:

- each selected `tsconfig` and its complete `extends` chain;
- compiler options relevant to module resolution, target language, JSX,
  paths, base URL, `types`, `lib`, `allowJs`, `checkJs`, declaration handling,
  and project references;
- explicit `files`, `include`, and `exclude` results;
- referenced projects and the inputs or declaration outputs used from them;
- package metadata relevant to module resolution, including applicable
  `package.json` fields;
- package-manager resolution and lockfile material where it affects the
  resolved endpoint;
- compiler-provided library declarations; and
- generated files actually read by the analysis.

The effective input manifest records each consumed path or logical input,
content digest, classification, reason for consumption, owning project when
known, and whether it was analyzed for program facts.

Compiler consumption and program membership are different. Every consumed
input receives one of these profile dispositions:

```text
IN_SCOPE
  contributes program identities and facts to this snapshot's declared
  program universe

EXTERNAL_BOUNDARY
  may contribute a known endpoint or resolution evidence, but its
  implementation is outside the declared universe

ANALYSIS_SUPPORT
  was consumed to resolve or analyze in-scope code, but does not itself
  contribute program-universe identities or positive program claims
```

The disposition is an input decision, not a semantic judgment about
importance.

### Default input dispositions

The user declaration may override these defaults, but the override becomes
part of the snapshot manifest:

| Input | Default disposition |
|---|---|
| `.ts`/`.tsx` under a selected workspace/package root and included project | `IN_SCOPE` |
| `.js`/`.jsx` consumed under an explicit `allowJs` boundary | `IN_SCOPE` when the boundary includes JavaScript; otherwise `ANALYSIS_SUPPORT` |
| `.d.ts` under the declared boundary and selected project | `IN_SCOPE`, with declaration evidence and no assumed implementation |
| `.d.ts` in `node_modules`, the TypeScript standard library, or an unselected referenced project | `ANALYSIS_SUPPORT`; a referenced target may also receive an external stub |
| generated source under an explicitly included generated root | `IN_SCOPE` |
| generated source consumed only as compiler support | `ANALYSIS_SUPPORT` |
| tests under an included test root or explicit test policy | `IN_SCOPE` |
| tests excluded by the boundary | `ANALYSIS_SUPPORT` if consumed, otherwise absent from effective inputs |
| selected workspace package outside the governed package roots | `EXTERNAL_BOUNDARY` for known endpoints; its files may be support inputs |
| third-party package or standard library | `EXTERNAL_BOUNDARY` for known endpoints; declarations are support inputs |

Project references do not silently widen the boundary. A referenced project
is in scope only when its package/root is included by the declaration. Its
declarations or build outputs may still be consumed as support material.

The extractor MUST record excluded files and excluded project roots when the
configuration expansion can identify them. A file that was never consumed is
not a failed analysis; a consumed file that could not be analyzed receives an
explicit diagnostic and affects the relevant completeness claim.

## Snapshot and build provenance

The TypeScript snapshot identity commits to the mechanical state, not only a
Git revision. Its canonical manifest contains at least:

```text
source_state
user_declared_boundary
effective_consumed_inputs
project_and_package_configuration
dependency_resolution
typescript_version
extractor_identity_and_version
typescript_profile_version
kdm_profile_version
```

`source_state` identifies immutable source/configuration content, including
generated inputs that are classified as consumed. `typescript_version` and
extractor identity describe the mechanism interpreting that state; they are
not source revision. The profile version identifies this contract and KDM
profile version identifies the normative semantic basis.

The manifest records configuration content or digests, not just paths. It
includes the `tsconfig` extends graph, project-reference graph, relevant
package metadata, lockfile/dependency-resolution identity, TypeScript library
inputs, JSX/module settings, and generated-file policy. Environment values
are included when the declared configuration makes them semantic inputs; the
exact environment capture policy remains an implementation question.

KDM Build concepts may represent applicable build resources, descriptions,
steps, and products. They do not replace this snapshot manifest. The manifest
is the profile-level identity and reconstruction envelope; KDM Build facts are
additional mechanical facts when build analysis is available.

## Snapshot-local program identities

Every first-class TypeScript program manifestation receives a deterministic
identity scoped to one snapshot. The identity is not a lineage ID and MUST NOT
be presented as surviving arbitrary refactors.

A conceptual identifier grammar is:

```text
program:ts:<snapshot-id>:<kdm-kind>:<mechanical-descriptor>
```

The actual escaping and digest encoding are implementation choices, but the
descriptor rules are contractual. The snapshot component prevents accidental
identity reuse across different mechanical states. The descriptor MUST be
deterministic from the immutable snapshot, the applicable TypeScript semantic
model, and the declared profile. It MUST not depend on an agent-supplied
semantic label.

### Module identity

An in-scope source module uses a canonical source input identity:

```text
module-key = canonical source blob identity + project/module-resolution context
```

The canonical path is normalized according to the project host's case and
path rules and is accompanied by the source blob digest. A relative path alone
is insufficient when project references, virtual files, or case-insensitive
file systems can distinguish inputs.

The KDM program element is a `CompilationUnit` or applicable `Module`.
`source::SourceFile` remains the inventory/evidence object. It is not promoted
to a program referent merely because it has a path.

### Named declarations

For a named declaration, the extractor obtains the mechanically bound
declaration symbol and constructs a descriptor from:

```text
owning KDM module/element identity
declaration kind
canonical declared name
symbol declaration-set identity within that owner
```

The declaration-set identity is based on the TypeScript binding result and a
deterministic declaration discriminator. Source ranges may be retained as
manifestation evidence and may be used as a final collision discriminator
inside one snapshot, but a line number or display name alone MUST NOT be the
identity.

The emitted KDM kind is selected by declaration meaning:

| TypeScript declaration | KDM kind |
|---|---|
| source file/module | `CompilationUnit` or `Module` |
| class | `ClassUnit` |
| interface | `InterfaceUnit` |
| named function/procedure | `CallableUnit` |
| class member method/accessor/constructor | `MethodUnit` |
| class field/property or mechanically meaningful variable | `DataElement`, normally `MemberUnit` or `StorableUnit` |
| overload signature | `Signature` associated with the callable/method |
| call site needed by `Calls` | KDM `ActionElement` |

The public spine stores these KDM meanings and evidence. It does not store a
TypeScript `SyntaxKind` as the program kind.

### Scope, overloads, constructors, and merging

- Same-name declarations in different scopes are distinguished by the
  recursively identified owning element and binding result.
- A nested named function is owned by its containing KDM callable or module,
  not by its source line.
- An overloaded function or method has one callable `CallableUnit` or
  `MethodUnit` identity for the bound callable and one KDM `Signature` identity
  per mechanically represented overload signature. Calls target the callable
  element; resolution metadata may identify the selected signature or
  candidate signatures.
- A constructor is a `MethodUnit` owned by its `ClassUnit`, with constructor
  kind metadata. Constructor overloads are represented as `Signature`
  elements. A `Creates` relation is outside required v0.
- Declaration merging uses the bound symbol identity for one KDM entity when
  the merged declarations have one mechanically meaningful entity. Every
  contributing declaration receives its own `SourceRef`/`SourceRegion`.
- A named default export retains the declaration identity and an export
  manifestation. An anonymous default export receives a deterministic
  `default_export` descriptor owned by the module.
- An imported alias is not a second identity for the target declaration by
  default. `Imports` and occurrence evidence preserve the alias. A local alias
  becomes a first-class data/binding element only if a later capability
  establishes an independent KDM identity need.

### Anonymous and synthetic callables

An anonymous function or arrow function receives a first-class `CallableUnit`
only when it is needed to preserve a required KDM relation, structural
ownership, or source-range localization. Its descriptor uses:

```text
owning KDM element
mechanical role (initializer, callback argument, returned callable, etc.)
deterministic ordinal among equivalent callable occurrences
```

The resulting identity is marked `synthetic=true` in profile metadata. This
means “constructed because a KDM program element was required,” not “invented
by the compiler.” It remains a snapshot manifestation and may later be
relinked by lineage.

Compiler `Symbol`, `Type`, `Signature`, `Node`, temporary variable, control
flow helper, and emit artifact are not persisted merely because the compiler
exposes them. A KDM `ActionElement` for a call site and a KDM `Signature` for
an overload are persisted because the selected KDM semantics require them,
with explicit profile status and evidence.

## Source coordinates and evidence

### Canonical persisted coordinate

The canonical source location is a half-open UTF-8 byte range over an
immutable source blob:

```text
source_blob_digest
byte_start
byte_end_exclusive
```

The blob digest and source revision identify the exact bytes. This convention
is deterministic across newline conventions and does not make Unicode code
units ambiguous. A BOM, if present, is part of the blob and coordinate
calculation is defined over the stored bytes.

TypeScript UTF-16 positions and line/character positions may be used during
extraction. They are converted to the canonical byte range against the exact
source text and are retained only as optional diagnostic/presentation
metadata. KDM `SourceRegion` line/position values may be presented or stored
as a derived KDM-compatible view, but the byte range is the authoritative
reconstruction coordinate for this profile.

The conversion MUST reject or explicitly diagnose a position that cannot be
mapped to the immutable source blob used for the snapshot. A display line and
column without the source digest and coordinate convention is insufficient.

### Required identity evidence

Every emitted program referent MUST have an evidence record containing:

```text
snapshot identity
KDM metaclass
source blob/file identity or explicit non-source basis
declaration/definition byte range when source-defined
TypeScript project context
extractor identity/version
TypeScript profile and KDM profile versions
synthetic status when applicable
```

An external stub has no local definition range. It has the local import,
reference, or call occurrence and dependency-resolution evidence instead.

### Required assertion evidence

Every emitted KDM relationship assertion MUST have:

```text
snapshot identity
KDM relationship name
exact occurrence or declaration byte range when applicable
source input/configuration identity
resolution status and candidate information where relevant
extractor identity/version
profile versions
```

The evidence is represented through existing `SourceObservation` and
`AssertionGrounding`. A TypeScript observation uses a provider such as
`typescript`, a native handle containing the source blob identity, a
`source_revision` equal to the snapshot source state, and a
`native_location` containing the canonical byte range. Configuration and
dependency observations use the same pattern with a config or lockfile
digest and a path/JSON-pointer location. Full source bodies are not copied
into every assertion.

The grounding detail may include KDM metaclass, source-coordinate conversion,
TypeScript project, resolution diagnostic, and extractor metadata. It must be
observable provenance, not private reasoning.

## Required World projection

The following is the proposed minimal logical projection. Names are World
relation names; their definitions explicitly conform to the KDM meanings in
the right-hand column. All extracted facts are `BASE` assertions with
`ConstructionOrigin.MECHANICAL`. A deterministic projection or index may be
`DERIVED`, but that does not change the origin of its inputs.

### Snapshot and input relations

```text
program_snapshot(
  snapshot          REFERENT,
  source_state      TEXT,
  boundary_digest   TEXT,
  inputs_digest     TEXT,
  configuration     TEXT,
  typescript        TEXT,
  extractor         TEXT,
  profile           TEXT
)

program_input(
  snapshot          REFERENT,
  input_descriptor   TEXT,
  disposition       TEXT,       -- IN_SCOPE | EXTERNAL_BOUNDARY | ANALYSIS_SUPPORT
  content_digest    TEXT,
  input_role        TEXT
)
```

`program_snapshot` and `program_input` are profile provenance relations. Their
structured manifest values are canonical serialized metadata referenced by
the grounding and stored alongside the World as required by the bundle
convention. The exact serialization is deferred; the fields and distinctions
are not.

### Program universe and KDM identity relations

```text
program_entity(
  snapshot          REFERENT,
  entity            REFERENT,
  kind              TEXT,
  boundary          TEXT        -- IN_SCOPE | EXTERNAL_BOUNDARY
)

kdm_element_type(
  snapshot          REFERENT,
  entity            REFERENT,
  metaclass         TEXT        -- e.g. CompilationUnit, ClassUnit, CallableUnit
)

kdm_ownership(
  snapshot          REFERENT,
  owner             REFERENT,
  owned_element     REFERENT
)
```

`program_entity` is the language-independent explicit universe relation from
the generic spine contract. TypeScript populates it; it does not create a
TypeScript-specific universe relation. In-scope entities MUST have
`boundary=IN_SCOPE`. External stubs have `boundary=EXTERNAL_BOUNDARY` and are
represented so that KDM relationship endpoints remain closed, but they do not
make the external implementation part of the local universe.

`kdm_ownership` is the World projection of KDM's `owner`/`ownedElement`
semantics. It is structural ownership. It is not semantic `part_of`, and it
does not mean that a source file or source range is a separate program entity.

### Required KDM mechanical relations

```text
kdm_imports(
  snapshot          REFERENT,
  from              REFERENT,
  to                REFERENT
)

kdm_calls(
  snapshot          REFERENT,
  from              REFERENT,   -- KDM ActionElement
  to                REFERENT    -- KDM CodeItem/callable
)

kdm_has_type(
  snapshot          REFERENT,
  from              REFERENT,
  to                REFERENT
)

kdm_extends(
  snapshot          REFERENT,
  from              REFERENT,
  to                REFERENT
)

kdm_implements(
  snapshot          REFERENT,
  from              REFERENT,
  to                REFERENT
)
```

`kdm_imports` is KDM `Imports`; `kdm_calls` is KDM `Calls`; the type relations
are KDM `HasType`, `Extends`, and `Implements`. The prefixed World names avoid
collisions with application relations while preserving the KDM predicate
meaning. All referent roles are foreign-key checked by the generic kernel;
the TypeScript admission checks additionally require same-snapshot membership
or explicit external-boundary classification.

`kdm_has_type`, `kdm_extends`, and `kdm_implements` are required relation
schemas but individual rows are emitted only when TypeScript mechanically
establishes the corresponding KDM fact. A missing row is not a negative claim.
`InstanceOf` is available for a later or explicitly supported object/type
capability and is not required for the initial slice.

### Resolution relations

KDM does not supply the profile's general uncertainty model. The minimum
TypeScript projection therefore adds profile metadata without changing KDM
relation semantics:

```text
typescript_resolution(
  snapshot          REFERENT,
  subject           REFERENT,
  relation_name     TEXT,       -- kdm_imports or kdm_calls
  status            TEXT,       -- RESOLVED | MULTIPLE_CANDIDATES | UNRESOLVED
  evidence_key      TEXT,
  details           TEXT        -- canonical JSON diagnostic/candidate metadata
)

typescript_resolution_candidate(
  snapshot          REFERENT,
  subject           REFERENT,
  relation_name     TEXT,
  candidate         REFERENT
)

program_capability(
  snapshot          REFERENT,
  capability        TEXT,
  status            TEXT,       -- COMPLETE | INCOMPLETE | UNKNOWN
  universe          TEXT,
  basis             TEXT,
  known_gaps        TEXT,       -- canonical JSON list
  result            TEXT        -- deterministic result fingerprint
)
```

`subject` is the importing module or KDM `ActionElement` associated with the
attempt. The candidate relation is populated only for known candidates;
candidates may be in-scope entities or external stubs. A `RESOLVED` row may
have one candidate, `MULTIPLE_CANDIDATES` has two or more where known, and
`UNRESOLVED` has none or only a diagnostic. The relation records the attempt
even when no KDM positive relation is emitted.

These relations are profile bookkeeping, not KDM semantic predicates. They
are required because “no `Calls` assertion” and “analysis proved no call
exists” have different meanings.

`program_capability` is the application-level receipt for capability-scoped
base extraction. The generic World completeness tables remain the mechanism
for derivation receipts; no new kernel primitive is required for this profile.

### Optional next-capability relations

When the data-access capability is added, its World projection will use:

```text
kdm_reads(snapshot REFERENT, from REFERENT, to REFERENT)
kdm_writes(snapshot REFERENT, from REFERENT, to REFERENT)
kdm_addresses(snapshot REFERENT, from REFERENT, to REFERENT)
```

These names mean KDM `Reads`, `Writes`, and `Addresses`, respectively. They
are intentionally not required v0 relations.

## TypeScript `Calls` semantics

The KDM `Calls` source is an `ActionElement` representing a call statement;
the target is a KDM `CodeItem`. The TypeScript profile creates a KDM
`ActionElement` referent for a call site when the required Calls capability
recognizes that site. The AST call expression remains evidence used to ground
the action element and assertion.

### Outcomes

For every recognized call attempt, the profile records one
`typescript_resolution` outcome:

```text
RESOLVED
  exactly one KDM target is mechanically established under this profile

MULTIPLE_CANDIDATES
  more than one KDM target remains mechanically possible

UNRESOLVED
  the call occurrence is known, but no target can be established under the
  profile
```

Only `RESOLVED` emits one `kdm_calls` assertion. `MULTIPLE_CANDIDATES` retains
candidate rows and evidence but does not emit one certain target.
`UNRESOLVED` retains the call occurrence and diagnostic but does not invent an
endpoint. A known pointer/procedure-dispatch case may use KDM `Dispatches` only
when its KDM semantics are actually established; it is not a generic
uncertainty relation.

### Required cases

- **Direct function call:** resolve the identifier to its bound callable and
  emit `Calls(ActionElement, CallableUnit)`.
- **Method call:** resolve the member to a `MethodUnit` or other KDM
  `CodeItem`. Do not infer every runtime override from a syntactic member
  name.
- **Constructor call:** resolve to the class constructor `MethodUnit` when
  mechanically identifiable. `Creates` remains outside required v0.
- **Overload:** target the callable/method identity and record the selected
  `Signature` or candidate signatures in resolution metadata. Do not create
  one runtime method per overload declaration.
- **Union receiver/interface dispatch:** emit one target only when the
  TypeScript mechanical model establishes one KDM target. If multiple
  concrete targets remain, record `MULTIPLE_CANDIDATES`. A known interface
  method may itself be the resolved KDM target; do not manufacture an
  implementation target.
- **Callback/higher-order value:** passing a function value is not a call.
  Emit `Calls` only for a mechanically established invocation site. A callback
  API's runtime invocation behavior is not inferred from argument position.
- **Computed property access:** record `UNRESOLVED` or
  `MULTIPLE_CANDIDATES`; do not use the property container as the target.
- **`any`, reflection, and dynamic loading:** record an explicit unresolved
  outcome unless an independent mechanical rule establishes the endpoint.
- **Unresolved import:** preserve the import occurrence and resolution result.
  If the package/module endpoint is canonical, an external module stub may
  receive `Imports`; an unresolved member call remains unresolved. If no
  endpoint can be canonicalized, emit no positive KDM relation.

The profile never interprets an omitted `kdm_calls` row as proof of no runtime
call. A complete Calls capability can support only a scoped conclusion about
recognized call sites and statically resolved KDM targets.

## External and boundary identities

External endpoints are program-plane identities with less information, not
semantic identities and not trust judgments. A conceptual form is:

```text
program:ts:<snapshot-id>:external:<canonical-external-descriptor>
```

The descriptor is chosen in this order:

1. resolved package identity, package manager, package version/locator, and
   resolved export/member path;
2. for an external workspace package, canonical workspace package identity
   plus the boundary declaration that excludes its implementation;
3. for the TypeScript standard library, compiler version and library name;
4. a resolved declaration source identity when it uniquely identifies the
   external element.

The raw module specifier is always retained as evidence. It is not sufficient
as the endpoint identity when different resolution contexts can map it to
different packages. If only a specifier is known and no stable external
endpoint can be established, preserve an unresolved outcome rather than
inventing a stub.

External stubs may use KDM `Module`, `CodeItem`, `CallableUnit`, `MethodUnit`,
or another applicable KDM metaclass. They have boundary evidence, such as an
import or call range and package-resolution record, but no local definition
range. The profile does not persist the external implementation, internal
call graph, runtime behavior, semantic meaning, authority, or governance
status.

Analysis-support declarations may help the checker resolve an external stub.
Their existence in the effective input manifest does not make them in-scope
program entities.

## Completeness semantics

Completeness is declared per capability, never inferred from the existence of
a TypeScript compiler `Program` or a KDM model. Each receipt names the
snapshot, capability, declared universe, recognized forms, basis, analyzer
and profile versions, execution result, and known gaps.

| Capability | `COMPLETE` means | Does not license |
|---|---|---|
| Program universe | Every declared input has an explicit disposition and every in-scope first-class KDM identity produced by the contract is in `program_entity`. | That every compiler-internal object or every runtime-loaded file exists in the universe. |
| Source evidence | Every emitted required identity and assertion has reconstructible evidence at the declared coordinate convention. | That every source byte has semantic meaning or became a referent. |
| Code structure | All in-scope supported declarations and KDM ownership recognized by the profile were processed; parse/type failures are accounted for. | That unsupported language constructs or runtime-generated objects do not exist. |
| Imports | All recognized static import/include/export forms in the covered inputs have a resolved, external, or unresolved outcome. | That dynamic loading or runtime module behavior is complete. |
| Calls | All recognized static call sites have a resolved, multiple-candidate, or unresolved outcome under the stated TypeScript rules. | That all runtime call targets are known, or that an omitted target is impossible. |
| External endpoints | Every known boundary endpoint required by an emitted KDM relation has a represented stub or explicit unresolved outcome. | That external implementations were analyzed or trusted. |
| Reads/writes | Only applies when the next capability is produced, over its declared recognized access forms. | That all aliasing, side effects, or runtime data flow is known. |

Malformed or unsupported input prevents `COMPLETE` for any capability whose
required facts could have been affected, unless the profile can prove the
unsupported region is outside that capability's declared basis. A complete
program universe may coexist with incomplete Calls or no UI capability.

The existing World completeness machinery can record receipts for derived
relations. Base mechanical extraction still needs the profile admission
receipt or an equivalent manifest-backed validation; a base relation's
existence is not proof of exhaustive extraction.

## Mechanical admission checks

Before a TypeScript spine candidate enters the generic candidate -> validate ->
sealed lifecycle, admission MUST verify:

1. the snapshot manifest exists and identifies source state, boundary,
   effective inputs, configuration, TypeScript/extractor versions, and profile
   versions;
2. the user-declared boundary is preserved separately from effective consumed
   inputs;
3. every effective input has a disposition and content/configuration digest;
4. every emitted in-scope KDM element is present in `program_entity` with the
   same snapshot;
5. every external endpoint used by a mechanical relation has an external
   `program_entity` record or an explicit unresolved outcome;
6. every KDM relationship endpoint passes generic REFERENT foreign-key
   integrity and same-snapshot/profile boundary checks;
7. every required identity and assertion has reconstructible byte-range or
   non-source evidence;
8. every recognized import/call attempt has a well-formed resolution outcome;
9. `MULTIPLE_CANDIDATES` and `UNRESOLVED` outcomes do not have a positive
   guessed KDM relation;
10. every capability receipt states its exact declared universe, recognized
    forms, basis, status, gaps, and execution result;
11. semantic/governance attachment is not required for program membership;
12. no TypeScript AST/compiler-internal type appears as a public KDM
    metaclass or relation without an explicit justified profile mapping; and
13. no required v0 relation is silently replaced by a TypeScript-specific
    synonym or by a generic `depends_on` relation.

These checks are application/profile admission checks over the existing World
primitives. They do not require changes to the generic kernel.

## Fixture matrix for the implementation task

The next extractor task should implement a compact fixture suite with
expectations stated in KDM/profile terms:

| Fixture | Required expectation |
|---|---|
| Two `.ts` modules with a relative import | In-scope `CompilationUnit` members, `kdm_ownership`, grounded KDM `Imports`, and distinct module identities. |
| Class, interface, function, method, field | `ClassUnit`, `InterfaceUnit`, `CallableUnit`, `MethodUnit`, and meaningful `DataElement` identities with KDM ownership and source evidence. |
| Nested named function and anonymous callback | Named nested callable is emitted; anonymous callable is emitted only when required by a KDM relation/localization and is marked synthetic. |
| Direct resolved call | KDM `ActionElement`, `CallableUnit` target, `Calls`, and `RESOLVED` outcome. |
| Overloaded/interface/dynamic call | KDM signatures and evidence are preserved; `MULTIPLE_CANDIDATES` or `UNRESOLVED` prevents a guessed `Calls` target. |
| External package call | External KDM-compatible callable stub, external boundary membership, grounded `Imports`/`Calls` where resolved, and no external implementation facts. |
| Workspace package outside governed boundary | Support inputs may be consumed, but the endpoint is an external stub and the package's implementation is absent from the local program universe. |
| Unattached helper | In-scope callable remains in `program_entity` with evidence and no required semantic attachment. |
| Changed source byte range | Localization returns the containing `CompilationUnit` and callable/action entities supported by evidence; it does not infer governance impact. |
| Same immutable snapshot rebuilt | Identical manifest, program IDs, KDM metaclasses, relation tuples, and evidence coordinates are reconstructed. |

Fixtures should also cover declaration merging, default exports, constructor
overloads, aliases, `.d.ts` support inputs, generated-file policy, and
newline/Unicode coordinate conversion before the profile is considered ready
for implementation.

## Explicitly deferred decisions

The following are intentionally not finalized by this profile:

- the TypeScript compiler API version and extractor implementation;
- the exact snapshot digest and manifest serialization;
- whether the first implementation includes `.js`/`.jsx` beyond explicit
  support;
- the complete canonicalization algorithm for package-manager locators;
- the precise declaration discriminator algorithm for pathological duplicate
  declarations;
- whether KDM `Signature` elements are physically materialized for every
  overload or represented as required metadata until a consumer needs them;
- the next-capability KDM data-access rules;
- full control flow, UI, React, routing, Event/state, and platform extraction;
- compiler-generated output and macro-like transform identities beyond the
  synthetic policy stated here;
- cross-snapshot lineage and rename/move/split/merge matching; and
- semantic construction, source adapters, traversal, case assembly, and
  adjudication.

No extractor, parser, KDM serializer, TypeScript integration, or World-kernel
change is implemented by this document.
