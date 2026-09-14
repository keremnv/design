# Program-spine contract

This document defines the smallest mechanically trustworthy program
representation that software governance may consume without reparsing or
semantically reinterpreting code structure.

It is a contract, not an implementation plan. It does not choose TypeScript,
SCIP, Tree-sitter, CodeQL, a compiler API, a code property graph, an index, or
any other concrete technology.

The normative terms are used as follows:

- **MUST** states a contract invariant;
- **MAY** states a permitted implementation choice; and
- **DEFERRED** marks a decision intentionally left open.

## Architectural position

The program spine is part of the governed World. It is the mechanically
grounded backbone over which semantic and governance structure may be built:

```text
CODE SNAPSHOT
      |
      | mechanical analysis
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

The spine is mechanically derived, versioned, reconstructible from program
inputs, and purpose-independent in its fact contract. It is not an
agent-authored ontology. Semantic construction may interpret what program
objects mean, but it must not manufacture a fact that this contract says is
mechanically derivable.

### Normative v0 semantic basis

The v0 program spine conforms semantically to the useful subset of [OMG KDM
1.4](https://www.omg.org/spec/KDM/1.4/PDF). The exact requirements matrix,
profile classification, and World projection recommendation are in
[KDM_PROFILE.md](KDM_PROFILE.md). KDM terminology defines the meaning of
selected program entities and mechanical relationships; it does not define
our snapshot manifest, user-declared boundary, completeness receipts,
external-stub policy, or cross-version lineage.

KDM `SourceRef` and `SourceRegion` address program evidence. They do not make
every source location a program referent. KDM model IDs, names, qualified
names, and source locations are snapshot-model identifiers or evidence, not
cross-version program identity. The World may use a snapshot-scoped program
referent and retain the KDM identifier as provenance.

The central closure invariant is:

```text
PROGRAM PRESENCE IS EXHAUSTIVE
within the declared program-spine universe.

SEMANTIC / GOVERNANCE SIGNIFICANCE IS SPARSE.
```

An object can therefore be present in the program universe with no semantic or
governance attachment.

The conceptual layers remain distinct:

```text
program evidence
      -> mechanically established program identities and claims
      -> semantic and governance claims
```

The arrows describe support and construction flow, not a mandatory physical
storage topology.

The durable-output contract is independent of extraction implementation. A
conforming construction may be produced by a built-in analyzer, compiler API,
existing structural index, user-provided deterministic analyzer, framework
extractor, or agent-authored program. The mandatory core and any claimed
capability semantics remain the same. [`SPINE_EXTRACTOR_CONTRACT.md`](SPINE_EXTRACTOR_CONTRACT.md)
defines the extractor-independent conformance boundary, construction receipt,
explicit losses, and the distinction between contract failure, capability
limitation, and purpose inadequacy.

## 1. Program snapshots

A **program snapshot** is the mechanical state against which one spine is
true. A Git commit alone is not a sufficient definition because generated
files, build configuration, language settings, dependency resolution, and the
analysis mechanism can change the facts produced from the same commit.

A snapshot MUST have a canonical manifest containing, at minimum:

```text
source_state
analysis_universe
build_and_language_configuration
spine_contract_version
analyzer_identity_and_version
analyzer_configuration
```

The snapshot identity MUST commit to all of those inputs. A useful conceptual
shape is:

```text
source_state_id
analysis_universe_id
configuration_id
spine_contract_version
analyzer_id
analyzer_version
analyzer_configuration_id
        |
        v
program_snapshot_id
```

`source_state_id` identifies the source state, such as a commit plus generated
input digests or a content-addressed working-tree manifest. It is separate
from the analyzer identity. `analyzer_version` identifies the mechanism that
interprets the source; it is not a source revision.

The manifest MUST make generated inputs and configuration inputs explicit.
When a build configuration affects resolution, module boundaries, generated
source, or language semantics, its content or a content-addressed equivalent
belongs in the snapshot identity. A tool's version alone is insufficient when
its configuration changes the result.

The snapshot manifest MUST be reconstructible from the declared program
inputs and analyzer inputs. A later consumer need not rerun the analyzer to
use the spine, but a maintainer must be able to determine what state and
mechanism produced it.

The snapshot identity is a version of mechanical state. It is not a semantic
World revision, source-native object identity, semantic referent identity,
program lineage identity, or governance decision.

### Deferred snapshot decisions

The exact digest encoding, manifest serialization, treatment of environment
variables, and minimum reproducibility guarantees for toolchains are deferred.
The invariant is that any input capable of changing a contracted fact is
identified in the manifest; the encoding can be chosen with the implementation
technology.

## 2. Program-universe closure

Each admitted snapshot MUST declare an analysis universe. The universe is a
bounded, inspectable description of what the analyzer was asked to enumerate.
It MUST identify, as applicable:

- project and package roots;
- included source roots and files;
- language and module configuration;
- generated-file policy and generated inputs;
- whether tests are included;
- whether declarations and type stubs are included;
- monorepo and package boundaries; and
- the treatment of external dependencies.

The contract does not require one universal ecosystem configuration model. It
requires a future implementation to state which configuration it used and
what it excluded.

For every admitted snapshot, every program identity that falls inside the
declared universe and the contract's first-class identity kinds MUST be
represented as a member of an explicit program-universe relation, conceptually
like:

```text
program_entity(snapshot, entity, kind, boundary, ...)
```

The exact physical schema is deferred, but the relation MUST distinguish:

```text
referent X exists
```

from:

```text
X belongs to the mechanically enumerated program universe of snapshot S
```

`_world_referents` alone is not the program universe. A referent may be
created for another reason, and a program identity's presence in the generic
referent table does not establish snapshot membership.

The program-universe relation MUST contain entities with no semantic or
governance edge. Construction MUST NOT filter entities based on whether an
agent currently considers them meaningful.

### What universe completeness means

Program-universe completeness is a claim over the declared analysis universe,
not over all code that exists in the wider world. A `COMPLETE` universe claim
means that:

1. every declared input was accounted for;
2. inclusion and exclusion decisions are recorded by the manifest;
3. every included input received the contract's required analysis outcome;
4. every first-class program object established by those outcomes was emitted
   into `program_entity`; and
5. no object was omitted because it lacked semantic or governance attachment.

An input that cannot be parsed or analyzed under the contract MUST have an
explicit outcome. If that prevents reliable enumeration of the contract's
first-class objects, the program-universe claim is `INCOMPLETE` or `UNKNOWN`,
not `COMPLETE`.

Generated files are included, excluded, or treated as external according to a
declared policy. They MUST NOT disappear through an undocumented default.
Tests and declaration files follow the same rule.

An external dependency is not an in-scope universe member merely because a
local file imports it. It may be represented by an external program stub when
the boundary contract requires an endpoint.

### Edge closure

Every persisted mechanical relation with program referent endpoints MUST have
represented identities for all endpoints. For in-scope endpoints this means a
`program_entity` member in the same snapshot. For a known boundary endpoint it
means an external stub. An unresolved endpoint has no positive mechanical edge
and must instead have an explicit unresolved outcome.

The generic World kernel already enforces the important part of this rule:
`REFERENT` relation roles are foreign-key checked against `_world_referents`.
Spine construction should rely on that mechanism by creating identities before
asserting relations. The spine strengthens it by requiring that a program
endpoint is also in the declared snapshot universe or explicitly marked as an
external boundary identity. It should not duplicate generic foreign-key
validation.

### Semantic sparsity

Program-universe closure and governance coverage answer different questions:

```text
UNATTACHED
  no semantic or governance attachment is persisted

UNGOVERNED
  sufficient relevant construction and completeness warrants that no
  applicable governance attaches

UNKNOWN
  no attachment exists, but coverage is insufficient for that negative claim
```

These are conceptual states for now, not required permanent stored enums. A
complete `program_entity` universe establishes presence, not `UNGOVERNED`.
Semantic construction must not delete or omit a program identity to make the
semantic graph sparse.

## 3. Program identities

A program referent identifies a mechanically recognized program object within
one snapshot. For v0, program identities SHOULD be snapshot-scoped. Cross-
snapshot identity and lineage are explicitly outside this contract.

An implementation MUST choose a canonical identity key for every emitted
object and MUST use that key consistently within the snapshot. The key may be
opaque to consumers. It MUST distinguish two mechanically distinct objects and
MUST not depend on semantic labels invented during governance construction.

The v0 identity rule is:

> Prefer the highest-level mechanically identifiable program object that a
> downstream semantic or governance consumer could reasonably attach meaning
> to.

The proposed v0 baseline kinds are:

```text
file
module
function
class
method
field
```

`module` is emitted when the language/build model gives it identity separate
from its file; otherwise the file is the container. Function, class, method,
and field are the baseline declaration-level objects. `symbol` is a useful
umbrella term, not an additional duplicate identity that must be emitted for
each specific declaration.

The following are declared extensions rather than universal v0 kinds:

```text
component
route / endpoint
```

A React/JSX extension may define a component identity and `renders` relation;
a routing extension may define route or endpoint identities. Each extension
MUST document its identity rule. The complete kind vocabulary MUST remain
small and declared.

Every AST node, token, expression, and source coordinate is not automatically
a program referent. Lower-level syntax is program evidence unless it has an
independent identity that downstream consumers can attach to. Source
coordinates describe manifestations of objects; they are not program identity.

An object may have multiple source manifestations in one snapshot. For
example, a symbol's declaration and references are different evidence regions
for one program identity. Conversely, one source region may contain several
program objects and several claims.

Program identities have a different origin from source-native and semantic
identities:

- program identity is mechanically derived from the snapshot and analyzer;
- source-native identity exists only when a provider exposes useful native
  object identity; and
- semantic identity is a constructed identity commitment that earns
  persistence through independent governance value.

No semantic referent is required between a source observation and a program
identity. A semantic claim may directly relate authoritative evidence to a
mechanically identified program object when that is the honest representation.

## 4. Mechanical relations

The spine preserves precise KDM mechanical predicates. It does not collapse
all program structure into `depends_on`, and it does not emit a relation merely
because an analyzer could calculate one. The names and endpoint meanings in
the following table are the KDM profile terms; the physical World encoding may
use ordinary typed relations and ownership roles as described in
`KDM_PROFILE.md`.

The v0 core relation contract is:

| KDM construct | What establishes it | Endpoint contract | Evidence and limits |
|---|---|---|---|
| KDM ownership (`owner` / `ownedElement`) | The KDM model hierarchy establishes that one element owns another. | KDM entity -> owned KDM entity. | Owner and member evidence. It is structural ownership, not semantic `part_of`. |
| `code::Imports` | A recognized import/include mechanism establishes the code relationship. | Code element -> imported code element, module, or boundary stub. | Import occurrence and resolution details. An unresolved module does not become a guessed edge. |
| `action::Calls` | A call site is mechanically resolved to a KDM `CodeItem` target. | `ActionElement` -> `CodeItem`/callable target. | Call-site range and resolution evidence. It covers the statically established target, not every possible runtime target. |
| `action::Reads` / `action::Writes` | A modeled action/data access satisfies KDM's read or write semantics. | `ActionElement` -> `DataElement`. | Access occurrence and KDM data-flow meaning. These are not generic dependencies. |
| `action::Addresses` | The action accesses a complex data structure or takes a data-element address as defined by KDM. | `ActionElement` -> KDM data element. | Address/reference evidence. Do not use it as a generic unresolved-target relation. |
| `action::ControlFlow` and `Flow` | KDM action elements establish a static control-flow successor relationship. | `ActionElement` -> `ActionElement`. | Control-flow evidence and capability scope. It is not a complete runtime-path model. |
| `code::HasType`, `Extends`, `Implements`, `InstanceOf` | The language mapping mechanically establishes the corresponding KDM type/inheritance fact. | KDM code/type entities according to each KDM relation's endpoint types. | Declaration/type evidence. Preserve the KDM predicate rather than a generic `references` edge. |

The draft labels `declared_in`, `contains`, `references`, and `calls` remain
useful explanatory shorthand in older examples, but they are not additional
v0 semantic predicates. Declaration evidence and KDM ownership must be
preserved distinctly when the source and KDM model distinguish them. A future
profile extension may define a narrower relation only when KDM has no faithful
construct and the extension records its own semantics, endpoints, evidence,
and completeness scope.

### Conditional mechanical extensions

Framework- or language-specific predicates MAY extend the KDM profile when the
extension declares its mechanical rule, endpoint kinds, evidence, and
completeness scope. KDM's lightweight extension mechanism is the normative
route for a KDM-specific extension. Examples include:

```text
renders(component, component)
route_handles(route, endpoint)
instantiates(class, class)
```

`renders` is therefore not a v0 core relation. It may be a later KDM UI
lightweight extension when JSX resolution and the framework rule establish it;
it is not a universal synonym for “may display”. Semantic interpretation of
visual or product meaning remains outside the spine.

An extension MUST NOT turn an intelligent interpretation into a mechanical
claim. If a framework behavior cannot be established under the declared
analyzer contract, it remains unknown or unresolved.

### Relation endpoints and claims

The relations above are mechanical claims involving program identities. A
relation row is a proposition, not an entity. Its endpoint identities MUST be
represented or explicitly represented as boundary stubs. Its evidence MUST
remain separate from any later semantic claim that interprets it.

## 5. Mechanical evidence

Every first-class program identity and every mechanical claim MUST be
auditable against concrete program evidence.

### Minimum identity evidence

An in-scope source-defined identity MUST have:

```text
program snapshot identity
source file identity
exact source range for declaration or definition
object kind
analyzer identity/version
spine contract version
```

A file identity is grounded by the file input and its source-state digest. A
generated or synthesized object is grounded by the generated input or
analysis artifact that establishes it, plus the local source manifestation
when one exists.

### Minimum relation evidence

Every mechanical claim MUST have at least one evidence record identifying:

```text
program snapshot
source file or analysis artifact
exact occurrence/declaration range where applicable
evidence role
analyzer identity/version
spine contract version
resolution information
```

Useful evidence roles include `definition`, `declaration`, `reference`,
`call_site`, `import`, `render_site`, and `boundary_use`. The vocabulary may be
extended by a declared analyzer extension.

An exact range MUST identify the source revision and coordinate convention
used by the analyzer. Line/column, byte offsets, UTF-16 offsets, or another
coordinate system may be selected by the implementation, but the convention
MUST be recorded and reconstructible. A bare line number or an unqualified
file path is insufficient for an exact program evidence claim.

An external stub has no local definition range. Its evidence is the local
boundary occurrence, such as an import or call site, plus any dependency
resolution record that identifies the external object. The absence of an
implementation range MUST remain visible.

This evidence supports a later warrant chain such as:

```text
semantic claim
    depends on
mechanical program claim
    grounded in
exact program evidence
```

The spine does not need to copy source bodies into every claim. It needs a
stable, exact route back to the program input and the analyzer's evidence.

## 6. Mechanical uncertainty

Static analysis has limits. The spine MUST represent those limits rather than
guessing to improve connectivity.

For a mechanically attempted relation, v0 uses the following conceptual
outcomes:

```text
RESOLVED
  one mechanically established target or target set is established

MULTIPLE_CANDIDATES
  more than one compatible target remains possible

UNRESOLVED
  the analyzer cannot establish a target under the contract
```

The exact storage representation is deferred, but the outcome and its
evidence MUST be inspectable.

- `RESOLVED` MAY produce an ordinary mechanical relation claim.
- `MULTIPLE_CANDIDATES` MUST preserve the candidate identities and the
  resolution evidence, but MUST NOT be presented as one certain target.
- `UNRESOLVED` MUST preserve the attempted occurrence and reason or diagnostic
  and MUST NOT silently become no edge.

Examples include dynamic dispatch, computed property access, reflection,
malformed or incomplete code, and framework behavior outside analyzer
knowledge. Unknown does not mean “there is no call”, “there is no reference”,
or “the object is irrelevant”.

An unresolved target MAY be an external boundary identity only when the
analyzer has mechanically established that external identity. A guessed
package member is not a conforming stub.

## 7. Completeness semantics

Completeness is claimed separately for each spine output. A complete program
universe does not imply complete call-target knowledge, and complete static
call resolution does not imply complete runtime behavior.

The contract distinguishes at least these scopes:

```text
program_entity universe:
  COMPLETE over the declared project inputs and contract-defined identity kinds

KDM ownership and source declaration mapping:
  COMPLETE over the KDM ownership and declaration evidence the analyzer
  contract recognizes in the successfully analyzed universe

KDM Imports:
  COMPLETE over recognized static import forms and their resolvable targets

KDM type/reference relations:
  COMPLETE only for the named KDM relation and recognized forms covered by the
  analyzer contract

KDM Calls:
  COMPLETE over recognized call sites and targets statically resolvable under
  the analyzer contract

runtime call targets:
  not implied COMPLETE by a static calls receipt
```

An extension such as `renders` needs its own scope, for example “recognized
JSX component render sites under the declared React resolution rule”.

Every completeness receipt MUST name:

```text
target output
declared universe
snapshot identity
spine contract version
analyzer identity/version
basis and recognized forms
known gaps or diagnostics
execution/result identity
```

`COMPLETE` licenses only the negative reasoning described by its scope. For
example, a current complete `calls` receipt may support:

> no statically resolved call edge exists for this recognized call-site class
> under this analyzer contract.

It does not support:

> this function can never call that target at runtime.

`INCOMPLETE` and `UNKNOWN` do not license a negative conclusion. A missing
semantic attachment is never converted into “ungoverned” merely because the
program universe is complete.

### Relationship to Ontology Author completeness

The existing World completeness machinery is useful when a spine output is
materialized as a derived relation from explicit input relations. Its receipts
already record a target, universe, basis, known gaps, input versions,
execution status, and result identity. Those semantics can support scoped
mechanical outputs without broadening `COMPLETE` beyond its declared universe.

The current kernel attaches completeness receipts to derivation runs. A
mechanically enumerated `BASE` program-universe relation does not receive a
generic completeness receipt merely because it is a base relation. Initial
governance admission MUST therefore carry the program-universe receipt at the
application boundary, or construction MUST arrange a derived materialization
whose declared input and receipt honestly establish the enumeration. The
kernel's rule that a base universe is sufficient by extension MUST NOT be
interpreted as proof that an analyzer exhaustively enumerated project inputs.

This is a mapping constraint, not permission to add a generic completeness
primitive in this milestone.

## 8. Diff localization boundary

The spine contract MUST support localization within one snapshot:

```text
(snapshot, source file, exact source range)
    -> program referents represented by or containing that range
```

The localization result uses the same program identities and evidence model as
the spine. It MUST be able to return the containing file/module/function/class
or other first-class objects whose evidence spans the changed range, subject
to the declared localization completeness and uncertainty.

This boundary supports the mechanical operation:

```text
changed source range -> changed program identities
```

It does not define:

```text
changed program identities -> governance-relevant impact
```

Impact, semantic attachment, authority, and adjudication are purpose- and
case-dependent work outside the core spine.

For two snapshots, localization is performed independently against each
snapshot. Cross-version lineage, rename continuity, and identity matching
between snapshots are deferred.

## 9. External and boundary identities

When a known mechanical relation crosses the local analysis boundary, the
spine MUST preserve the known endpoint as an external program identity or
explicit unresolved outcome. It MUST NOT silently drop the relation.

An external stub is still a program-plane identity, but it is not an in-scope
member of the local program universe. An illustrative naming shape is:

```text
program:local:Checkout
    calls
program:external:npm:stripe/createPaymentIntent
```

The exact identifier syntax is deferred. The identity MUST distinguish at
least:

```text
local/in-scope program object
external/boundary program object
```

An external stub MAY be the endpoint of `imports`, `references`, `calls`, or a
declared extension relation when the analyzer establishes that endpoint. Its
minimum support is the local boundary occurrence and, where available, the
dependency/module resolution record.

An external stub MUST NOT claim an implementation range, internal call graph,
type behavior, runtime behavior, trust, authority, semantic significance, or
governance status that the analyzer did not establish. External does not mean
semantic, ungoverned, trusted, or irrelevant.

If the package or member cannot be mechanically resolved to a stable external
identity, preserve an unresolved boundary event instead of inventing one.

## 10. Admission invariants

Before a produced spine may be admitted into a sealed governed World, the
governance/program-spine boundary MUST verify:

1. the program snapshot identity and manifest are explicit;
2. the declared analysis universe and inclusion/exclusion policy are explicit;
3. the spine contract and analyzer identity/version are recorded;
4. every in-scope first-class program identity is represented in
   `program_entity`;
5. no program relation has an unrepresented endpoint;
6. every known boundary endpoint is preserved as an external stub or explicit
   unresolved outcome;
7. every first-class identity and mechanical claim has reconstructible program
   evidence;
8. resolution outcomes such as `MULTIPLE_CANDIDATES` and `UNRESOLVED` remain
   explicit;
9. each completeness claim names its exact target, universe, basis, gaps, and
   snapshot;
10. a `COMPLETE` claim is not accepted when required input analysis failed or
    when the analyzer silently omitted an included input; and
11. semantic or governance attachment is not required for program-universe
    membership.

These are program-spine admission checks over existing World primitives and
application metadata. They do not require a new generic World `Contract`
mechanism.

After admission, semantic construction may add sparse claims involving spine
identities. It may not mutate the mechanical facts in place. A changed
snapshot produces a new spine artifact and, eventually, a new governed World
revision through construction.

## 11. Contract examples

The examples use illustrative IDs and ranges. They do not prescribe an ID
format, TypeScript analyzer, or storage schema. `program_entity` is the
governance profile's explicit snapshot-membership relation. Mechanical
relations use KDM names and meanings; KDM ownership is shown in prose because
the World need not mirror KDM's XMI containment representation.

### 11.1 Function containment and reference

```typescript
export function submitOrder(total: number) {
  return validateTotal(total);
}

function validateTotal(total: number) {
  return total >= 0;
}
```

A conforming spine may emit:

```text
program_entity(S, program:local:checkout.ts, file)
program_entity(S, program:local:checkout.ts#submitOrder, function)
program_entity(S, program:local:checkout.ts#validateTotal, function)

KDM ownership:
  code::CompilationUnit owns submitOrder and validateTotal

action::Calls(
  from = action::ActionElement(call site in submitOrder),
  to   = program:local:checkout.ts#validateTotal
)
```

Each identity is grounded in its declaration range. The `Calls` claim is
grounded in the call occurrence. The spine need not emit an AST node for the
parameter, return expression, or comparison unless the contract separately
makes one first-class.

It MUST NOT emit a semantic `PurchaseAction`, infer that the function is a
checkout action, or claim that `validateTotal` is called in every runtime
execution.

### 11.2 React component rendering another component

```tsx
function CheckoutPage() {
  return <PurchaseButton total={finalTotal} />;
}

function PurchaseButton(props: { total: number }) {
  return <button>{props.total}</button>;
}
```

The required v0 code profile emits the two callable/component code identities.
Under a later declared KDM UI lightweight extension that resolves the JSX
identifier, a conforming spine may additionally emit:

```text
program_entity(S, program:local:checkout.tsx#CheckoutPage, component)
program_entity(S, program:local:checkout.tsx#PurchaseButton, component)

KDM UI composition extension:
  CheckoutPage -> PurchaseButton
```

That extension claim is grounded in the JSX element range and its resolution
record. It does not mean that the product concept `CheckoutFlow` exists, that
the button is semantically a purchase action, or that all runtime rendering
paths have been enumerated. The profile does not make `renders` a universal
v0 predicate.

If the JSX target is unresolved or has multiple candidates, the extension
records that resolution outcome rather than emitting one certain `renders`
edge.

### 11.3 Local call to an external package

```typescript
import { createPaymentIntent } from "@stripe/payments";

export function pay(orderId: string) {
  return createPaymentIntent(orderId);
}
```

If package and member resolution are mechanically established, a conforming
spine may emit:

```text
program_entity(S, program:local:checkout.ts#pay, function)
program_entity(S,
  program:external:npm:@stripe/payments/createPaymentIntent,
  function,
  EXTERNAL)

code::Imports(
  from = program:local:checkout.ts,
  to   = program:external:npm:@stripe/payments/createPaymentIntent
)
action::Calls(
  from = action::ActionElement(call site in pay),
  to   = program:external:npm:@stripe/payments/createPaymentIntent
)
```

The stub is grounded in the import and call ranges plus package-resolution
metadata. The spine MUST NOT emit Stripe's implementation, internal callers,
trust level, or governance status.

### 11.4 Unresolved dynamic call

```typescript
const handler = handlers[event.type];
handler(payload);
```

A conforming spine may emit program identities and resolved references for
`handlers`, `event`, and the containing function where those are mechanically
known. It MUST record an unresolved call-site outcome for `handler(payload)`:

```text
mechanical resolution:
  relation: calls
  status: UNRESOLVED
  evidence: exact call-site range
  reason: computed property target is not statically established
```

It MUST NOT emit a KDM `Calls` relation to `handlers` merely because the value
came from `handlers`, and it MUST NOT treat the absent `Calls` edge as
proof that no runtime target exists.

### 11.5 Unattached helper remains in the universe

```typescript
function formatDebugLabel(value: unknown) {
  return `[debug] ${String(value)}`;
}
```

If this function is inside the declared analysis universe, the spine MUST
emit its program identity, declaration evidence, and structural relations even
when no semantic or governance claim refers to it:

```text
program_entity(S, program:local:debug.ts#formatDebugLabel, function)
```

The semantic layer may classify it as `UNATTACHED`. It cannot call it
`UNGOVERNED` unless a separate, sufficient governance completeness and
applicability process establishes that conclusion. Otherwise its governance
significance is `UNKNOWN`.

### 11.6 Source-range change localization

Suppose a later snapshot changes only the body of `validateTotal`:

```diff
 function validateTotal(total: number) {
-  return total >= 0;
+  return total > 0;
 }
```

For the changed range in the later snapshot, the spine's localization boundary
may return:

```text
program:local:checkout.ts
program:local:checkout.ts#validateTotal
```

It may also return a containing class/module identity when one exists. It does
not infer that `submitOrder` is governance-affected. A later purpose-specific
impact query may discover that `submitOrder` calls `validateTotal`, but that is
selection and interpretation over the spine, outside localization itself.

The localization result is grounded in the same source ranges and snapshot
manifest as the spine. If a malformed change prevents reliable localization,
the result carries an explicit incomplete or unresolved status.

## 12. Deferred design questions

The following questions remain intentionally open:

- Which analyzer technology and language set will implement the contract?
- What exact canonical ID encoding and snapshot manifest serialization will be
  used?
- Which program kinds are mandatory in v0 across languages, and which belong
  to extensions?
- Is `module` distinct from `file` for every supported language, or only when
  the language's module system supplies independent identity?
- What exact source-range coordinate convention provides the best cross-tool
  auditability?
- What is the smallest stable representation for multiple candidates and
  unresolved mechanical attempts?
- How should compiler-generated and macro-generated objects be identified and
  evidenced?
- How should package-manager resolution and external symbol identity be
  canonicalized?
- Which framework extensions, including React rendering, belong in the first
  implementation?
- How should a malformed file be partially enumerated without overstating
  program-universe completeness?
- How should static relation completeness be computed and compared when an
  analyzer changes version or configuration?
- How should program-universe and relation completeness receipts be attached
  physically when outputs are base mechanical assertions?
- How should source-range localization represent edits that move, split, or
  merge program objects within one snapshot?
- What cross-snapshot lineage model, if any, should be added after v0?

These questions do not permit semantic construction to fill gaps by guessing.
Until resolved, the relevant fact remains explicitly unknown or belongs to an
analyzer extension with its own declared contract.

## Non-goals

This contract does not implement or select:

- TypeScript compiler integration, SCIP, Tree-sitter, CodeQL, or CPG machinery;
- AST extraction or Git diff extraction;
- cross-version program lineage;
- semantic construction or source adapters;
- Figma integration;
- case assembly or governance adjudication; or
- a universal software ontology.
