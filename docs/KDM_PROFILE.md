# v0 KDM profile

This document defines the KDM 1.4 subset used by the program-spine contract.
It is normative for the meaning of v0 program facts. It does not prescribe an
XMI serializer, an extractor, a language, or a physical World schema.

The normative source is the [OMG KDM 1.4 specification](https://www.omg.org/spec/KDM/1.4/PDF) and its
[official machine-readable CMOF and XSD definitions](https://www.omg.org/spec/KDM/1.4/).
The CMOF release is dated 2016-02-01; the specification identifies the
published KDM version as 1.4. The package names and metaclass names below use
the normative KDM spelling.

KDM is the sole v0 program-semantic standard. IFML, UML, SysML, SCIP, CPG,
FAMIX, and other models may be compared in research, but they do not define
the meaning of a v0 spine fact.

## How the profile uses KDM

KDM supplies the semantic vocabulary for mechanically recovered program
knowledge. The governance architecture supplies the surrounding conditions
that KDM does not define:

```text
user-declared boundary and inputs
        -> effective consumed inputs
        -> KDM-profile program facts
        -> World admission and scoped completeness
```

KDM model elements and relationships are snapshot manifestations. A KDM
`xmi:id`, URI, qualified name, name, or source location identifies or locates
an element in a model instance; none is a permanent cross-version program
identity. The World may use an opaque snapshot-scoped program referent and
retain the KDM identifier as extraction provenance. Later lineage is a
separate mapping between snapshot manifestations.

KDM `SourceRef` and `SourceRegion` preserve traceability from a KDM element to
an `InventoryItem` and an exact region. They address evidence. They do not
turn every source file, line, or region into a program referent.

When the spine's baseline `file` kind is admitted, its program-plane identity
is a KDM `CompilationUnit` or another applicable KDM `Module`. The KDM
`SourceFile` in the InventoryModel remains the physical input/evidence object;
it is not promoted to a program referent merely because it has a path.

KDM relationships are propositions involving KDM entities. In the World they
may be represented as typed assertions with KDM relationship names, while
their exact program evidence remains in existing grounding. A relation does
not become a new identity merely because KDM models relationship objects in
XMI.

## Requirements-to-KDM matrix

The status has this meaning:

- **EXACT**: KDM has a construct whose stated semantics can be used directly
  for the requirement, subject to the profile's evidence and completeness
  rules.
- **PARTIAL**: KDM has useful related semantics, but it does not settle the
  whole governance requirement or the profile must constrain its use.
- **GAP**: KDM does not provide the required governance meaning. A profile
  admission record may add the missing boundary or epistemic metadata; that
  metadata is not a new program-semantic standard.

| Requirement | KDM construct | Normative meaning used here | Fit | v0 status |
|---|---|---|---|---|
| Program model container | `kdm::Segment`, `kdm::KDMModel`, `code::CodeModel` | A `Segment` groups coherent model data; a `KDMModel` owns model elements; `CodeModel` owns top-level code elements. | PARTIAL: these organize a KDM model but do not define our user-declared universe. | REQUIRED as model organization |
| Program/file inventory | `source::InventoryModel`, `InventoryItem`, `SourceFile`, `ConfigFile`, `Project`, `Directory`, `LibraryFile`; code `CompilationUnit`/`Module` | Inventory elements represent physical artifacts and inventory containers; `SourceFile` and `ConfigFile` distinguish common artifact roles. A code `CompilationUnit` is the program-plane file/module manifestation when the file kind is admitted. | PARTIAL: inventory is evidence/input structure, not automatically program identity or boundary membership. | REQUIRED for consumed input evidence and applicable code units |
| Source location/reference | `source::SourceRef`, `source::SourceRegion`, `source::Region` | `SourceRef` links a model element to source; `SourceRegion` identifies a precise text region with file, line, position, and language. | EXACT for source traceability, with existing grounding as the physical implementation. | REQUIRED |
| Namespace/package/module hierarchy | `code::NamespaceUnit`, `code::Package`, `code::Module`, `code::CompilationUnit`, ownership through `ownedElement` | KDM code elements are organized through typed module containers and KDM ownership. `CompilationUnit` is a module representing a source compilation unit; `Package` is a module. | EXACT for KDM code organization; the profile does not invent a universal `contains` predicate. | REQUIRED |
| Types/classes | `code::Datatype`, `ClassUnit`, `InterfaceUnit`, `TypeUnit`, `PrimitiveType`; `Extends`, `Implements`, `InstanceOf`, `HasType` | KDM represents data types and class/interface units and defines typed relationships for inheritance, implementation, instance/type, and type association. | EXACT where the language mapping establishes the KDM construct. | REQUIRED for emitted declaration kinds; type detail can be capability-scoped |
| Functions/methods/callables | `code::ControlElement`, `CallableUnit`, `MethodUnit`, `Signature`, `ParameterUnit` | `CallableUnit` represents named callable behavior; `MethodUnit` represents member functions owned by a `ClassUnit`; signatures own parameters. | EXACT for callable and method declarations. | REQUIRED |
| Fields/data/state objects | `code::DataElement`, `StorableUnit`, `MemberUnit`, `ItemUnit`, `ParameterUnit`; `HasType`, `HasValue` | KDM models data elements, variables, class members, items, and formal parameters and their type/value associations. | EXACT for represented declarations; runtime state is a different concern. | REQUIRED for fields and other emitted data objects; local-variable detail optional |
| Component identity | `structure::Component`, `Subsystem`, `Layer`, `SoftwareSystem` | KDM structure elements represent architectural entities and their relationships to implementation elements. | PARTIAL: a source-level component is not automatically a KDM architectural component without a declared extraction rule. | OPTIONAL capability |
| Route/endpoint identity | `source::Service`; KDM Code and Structure elements may implement it | KDM `Service` represents a network resource exposing operations; it is not a general web-route declaration. | PARTIAL/GAP for framework routes. A route identity needs a later declared KDM extension and mechanical rule. | DEFERRED capability |
| Declaration/containment | KDM `owner`/`ownedElement` associations on `KDMEntity` and typed KDM model containers; `SourceRef` | KDM ownership expresses model containment; source regions locate declarations. | PARTIAL for the draft's separate `declared_in` and lexical `contains` predicates. KDM does not require those as two universal relations. | REQUIRED through KDM ownership; separate declaration relation deferred |
| References | `code::CodeRelationship`, `Includes`, `VisibleIn`, `UsesType`, `ParameterTo`, `GeneratedFrom`, plus language-specific KDM relations | KDM has several precise reference-like relationships, but no one universal name-resolution relation with the draft's broad `references` meaning. | PARTIAL. Emit a specific KDM relation when its semantics fit; otherwise retain evidence or a declared extension. | OPTIONAL capability |
| Imports | `code::Imports` | `Imports` is a KDM code relationship between code elements for import/include-style dependencies. | EXACT for recognized import/include mechanics; resolution and external boundary remain profile metadata. | REQUIRED |
| Calls/invocation | `action::ActionElement`, `action::Calls`; `Dispatches` for procedure-pointer style calls | `Calls` represents a call-type relationship from an `ActionElement` to a `CodeItem`; `Dispatches` represents a call through a data item/pointer where the exact target is not known statically. | EXACT for the KDM call semantics. | REQUIRED |
| Reads | `action::Reads` from `ActionElement` to `DataElement` | `Reads` represents read access/data flow from a data element to an action element. | EXACT for modeled data accesses; it is not every abstract dependency. | OPTIONAL capability |
| Writes | `action::Writes` from `ActionElement` to `DataElement` | `Writes` represents write access/data flow from an action element to a data element. | EXACT for modeled data accesses. | OPTIONAL capability |
| Address/reference access | `action::Addresses` | `Addresses` represents access to a complex data structure or taking a data element address. | EXACT where the analyzer establishes that KDM situation. | OPTIONAL capability |
| Control flow | `action::ActionElement`, `ControlFlow`, `Flow`, `TrueFlow`, `FalseFlow`, `GuardedFlow`, `EntryFlow` | KDM action relationships represent control flow between action elements and entry/branch behavior. | EXACT for the modeled static control flow; not a runtime path guarantee. | OPTIONAL capability |
| Data flow | `Reads`, `Writes`, `Addresses`; data-package relationships where a narrower data model applies | KDM action data relations represent specific action/data access flows. | PARTIAL for a general all-language data-flow graph. Do not call every dependency data flow. | OPTIONAL capability |
| Architectural/component structure | `structure::StructureModel`, `Component`, `Subsystem`, `Layer`, `SoftwareSystem`, `ArchitectureView`, `StructureRelationship` | KDM structure elements represent an architectural viewpoint and may group or relate implementation elements. | PARTIAL: KDM supplies the viewpoint, but component recovery and grouping rules are analyzer/profile dependent. | OPTIONAL capability |
| UI composition | `ui::UIModel`, `UIResource`, `UIDisplay`, `Screen`, `UIField`, `UIElement`, `UILayout`, `UIRelationship` | KDM UI elements model display resources and their composition/relationships; `Screen` is a compound display. | PARTIAL for React/JSX. KDM has no universal React render rule; a declared KDM lightweight extension may be required. | OPTIONAL capability |
| UI events/actions | `ui::UIEvent`, `UIAction`, `ReadsUI`, `WritesUI`, `ManagesUI`, `UIFlow` | KDM models UI events/actions and UI data/control/workflow relationships. | PARTIAL: exact when the extractor has a defensible UI model; framework inference is not implied. | DEFERRED capability |
| Display flow | `ui::UIFlow`, `Displays`, `UILayout` | KDM provides UI flow and display relationships for a UI architectural view. | PARTIAL: the constructs fit, but arbitrary source does not mechanically prove user-visible flow. | DEFERRED capability |
| Events | `event::EventModel`, `Event`, `EventAction`, `ProducesEvent`, `ConsumesEvent` | KDM event elements and relationships describe event production/consumption and event actions. | PARTIAL: event extraction depends on language/framework mechanics. | DEFERRED capability |
| States/transitions | `event::State`, `Transition`, `OnEntry`, `OnExit`, `ReadsState`, `NextState` | KDM represents explicit state machines and state relationships. | EXACT for an explicitly recoverable state model; GAP for a universal inference from ordinary code. | DEFERRED capability |
| External program objects | `code::CodeItem`, `CallableUnit`, `Module`, `CodeAssembly`; source `LibraryFile` | KDM can represent a referenced code item or library artifact in a model. | PARTIAL: KDM does not define our local/external analysis boundary or stub epistemology. | REQUIRED profile boundary extension |
| Build/project/configuration provenance | `build::BuildModel`, `BuildResource`, `BuildComponent`, `BuildDescription`, `BuildStep`, `BuildProduct`, `BuildLibrary`; source `ConfigFile` | KDM Build represents build facts, inputs, transformations, products, tools, and descriptions; inventory represents configuration artifacts. | PARTIAL: it does not define the full snapshot manifest, user boundary request, analyzer identity, or World completeness receipt. | REQUIRED provenance envelope; detailed build semantics optional |
| Program snapshot identity | `kdm::Segment`, `Audit`, model names/IDs | KDM can package a model and record audit metadata. | GAP for our content-addressed snapshot identity and analyzer/configuration tuple. | REQUIRED profile metadata |
| Program-universe closure | KDM ownership/model containers | KDM can contain model elements, but does not say that every object in a declared analysis universe must be present or how to certify that. | GAP. | REQUIRED profile admission |
| Mechanical uncertainty | KDM `Dispatches` and `kind=unknown` in some metaclasses | Some KDM constructs describe pointer dispatch or unknown properties, but KDM has no general resolution result model. | GAP. | REQUIRED profile metadata |
| Per-output completeness | KDM model/view and `Audit` | KDM describes model content, not scoped extraction completeness or permissible negative reasoning. | GAP. | REQUIRED World/profile receipts |
| Source-range localization | `SourceRef`/`SourceRegion`, code ownership | KDM provides source-to-element mapping within a model. | PARTIAL: same-snapshot localization is supported; completeness and cross-snapshot matching are outside KDM. | REQUIRED boundary |
| Cross-version lineage | none | KDM does not define rename/move/split/merge correspondence between separately built models. | GAP. | DEFERRED |

KDM's `Core` package supplies the common `Element`, `KDMEntity`, and
`KDMRelationship` structure. `KDMEntity.source` is useful traceability
metadata, while `KDMRelationship.from` and `.to` are typed relationship
endpoints. The World may project those semantics into ordinary typed
relations without copying KDM's XMI containment or relationship-object
representation.

## Minimal v0 profile

The smallest useful v0 profile is deliberately narrower than all of KDM:

### V0 required

- **Core and KDM framework:** `Element`, `KDMEntity`, `KDMRelationship`,
  `KDMModel`, `Segment`, and the ownership/model pattern as needed to
  identify the selected facts.
- **Source:** `InventoryModel`, `InventoryItem`, `SourceFile`, `ConfigFile`
  where applicable, `SourceRef`, and `SourceRegion`.
- **Code structure:** `CodeModel`, `Module`, `CompilationUnit`, `Package`,
  `NamespaceUnit`, `ClassUnit`, `InterfaceUnit`, `Datatype`, `ControlElement`,
  `CallableUnit`, `MethodUnit`, `Signature`, `DataElement`, `StorableUnit`,
  `MemberUnit`, and `ParameterUnit` when the corresponding program object is
  inside the declared identity profile.
- **Code relations:** KDM ownership, `Imports`, `HasType`, `Extends`, and
  `Implements` where mechanically established. `InstanceOf` is available for
  explicit object/type facts.
- **Action invocation:** `ActionElement` and `Calls`. `Dispatches` is the
  canonical KDM representation for the specific pointer/procedure-dispatch
  situation described by KDM; an unresolved ordinary call must not be changed
  into `Dispatches` without satisfying that meaning.
- **Build/input provenance:** the applicable KDM Build and Source elements,
  plus the profile snapshot manifest for the user boundary, consumed inputs,
  analyzer, and contract version.
- **Profile admission metadata:** explicit program-universe membership,
  external-boundary classification, mechanical resolution outcomes, and
  capability-scoped completeness. These are profile/governance metadata, not
  KDM semantic replacements.

### V0 optional capability

- `Reads`, `Writes`, and `Addresses`;
- `ControlFlow`, `Flow`, `TrueFlow`, `FalseFlow`, `GuardedFlow`, and
  `EntryFlow`;
- richer type, value, template, visibility, and language-specific code
  elements;
- KDM `StructureModel` and its structure elements;
- KDM `UIModel`, UI elements, and UI relationships;
- KDM `EventModel` and event/state elements;
- detailed Build relationships and products;
- KDM `PlatformModel` for runtime resources; and
- KDM `DataModel` for database/content semantics.

An optional capability can be emitted only with its own evidence and
completeness scope. Its absence does not remove required code identities.

### Deferred

The following remain deferred even though KDM contains related concepts:

- a universal reference/name-resolution relation;
- a universal React component/rendering profile;
- full UI, event/state, platform, database, and architecture recovery;
- cross-snapshot lineage;
- runtime behavior or dynamic dispatch completeness; and
- the physical representation of KDM relationship objects and attributes in
  the World.

### Not relevant to the v0 program spine

The KDM `Conceptual` package is not part of the v0 program-semantic spine.
Conceptual terms, rules, scenarios, and business concepts belong to semantic
construction or authoritative source interpretation. They must not be used to
turn a program extraction into an agent-authored ontology. KDM's full
platform and build viewpoints are also not required unless a concrete v0
boundary or governance use needs them.

## World representation recommendation

Use **B: a KDM semantic profile**. Store a small, explicitly documented
projection of selected KDM entities and relations using existing World
referents, typed n-ary assertions, grounding, construction origin, and
completeness/admission metadata.

The alternatives are less suitable for v0:

- **A, near-literal KDM**, would reproduce KDM's broad model and relationship
  object structure before the governance system depends on it. It also risks
  allowing XMI containment or IDs to masquerade as World identity.
- **C, an intermediate literal KDM model**, may become useful if an extractor
  naturally produces KDM or if interchange is required. Introducing it as a
  required implementation stage now would add a second physical model without
  changing the semantic contract.

The profile projection should follow these rules:

| KDM meaning | Natural World representation |
|---|---|
| KDM code/UI/event/structure entity selected as first-class | Snapshot-scoped thin program referent, with KDM metaclass recorded as typed metadata or an explicit type assertion. |
| KDM model/container and program-universe membership | Explicit profile relation such as `program_entity(snapshot, entity, ...)`; KDM `CodeModel` ownership remains separate from admission membership. |
| KDM ownership | Typed World relation or scalar role preserving the KDM owner/owned-element direction. Do not rename it to semantic `part_of`. |
| KDM `Calls`, `Imports`, `Reads`, `Writes`, `Addresses`, `Flow`, `HasType`, `Extends`, `Implements` | Typed BASE mechanical assertions using the KDM predicate meaning and endpoint roles. The relation row is the claim. |
| KDM `SourceRef`/`SourceRegion` | Existing `SourceObservation`/`AssertionGrounding` addressing the consumed file and exact range. Store KDM source metadata only when it contributes required reconstruction. |
| KDM relationship attributes such as action `kind` | Scalar roles or metadata attached to the assertion when required by the selected KDM semantics. |
| KDM `Audit`, Build, and inventory facts | Build/snapshot provenance records and grounded World assertions as appropriate. |
| KDM XMI/model IDs | Provenance within the snapshot, never a cross-version identity contract. |

Mechanically extracted KDM-profile assertions use the coarse
`ConstructionOrigin.MECHANICAL` compatibility label and retain exact KDM and
program evidence. Deterministic World projections use `DERIVED` only for the
projection computation; that label does not change the epistemic origin of the
KDM facts from which the projection was computed.

## Profile extensions beyond KDM

These are the only v0 extensions currently justified by concrete governance
requirements:

1. **Snapshot manifest.** Records source state, user-declared boundary,
   effective consumed inputs, relevant configuration, extractor identity and
   version, and profile/contract version. KDM packages can describe pieces of
   this information, but do not define the identity tuple or reproducibility
   rule.
2. **Explicit program-universe membership.** Records that an emitted program
   identity belongs to the effective universe of a particular snapshot. KDM
   model ownership and `CodeModel` containment do not certify exhaustive
   admission over user-declared inputs.
3. **Boundary classification and external stubs.** Distinguishes an
   in-scope entity from a represented external endpoint and records the local
   evidence and the unknown implementation extent. KDM can model library/code
   elements but does not define this local governance boundary.
4. **Mechanical resolution outcome.** Records `RESOLVED`,
   `MULTIPLE_CANDIDATES`, or `UNRESOLVED`, candidate identities where known,
   and a diagnostic/evidence record. KDM's `Dispatches` is a semantic model
   for one particular call mechanism, not a general uncertainty model.
5. **Capability-scoped completeness.** Binds a completeness receipt to a
   declared universe, KDM capability, analyzer/profile version, basis, and
   known gaps. KDM describes model semantics but does not license negative
   reasoning from omitted elements.
6. **Later lineage relation.** Maps manifestations between snapshots using
   explicit unchanged/rename/move/split/merge/delete/new/ambiguous outcomes.
   KDM 1.4 does not define cross-version correspondence.

These extensions constrain admission and provenance. They do not add a second
program ontology or change the meaning of KDM predicates.

## Closure, uncertainty, and completeness

The user-declared boundary is expanded mechanically into effective consumed
inputs. Every in-scope KDM-profile program identity produced under the
declared identity profile is a member of the explicit World program-universe
relation, including identities with no semantic attachment. `_world_referents`
is not sufficient for this purpose.

Every KDM relationship endpoint projected into the World must resolve to a
represented in-scope identity or a represented external stub. This reuses the
World kernel's REFERENT-role referential integrity. An omitted endpoint is a
construction failure, not a silent drop.

KDM omission has open-world meaning. A missing `Calls`, `Reads`, UI, event, or
state relationship is not proof of absence. A profile completeness receipt
must state whether it covers the declared universe, recognized syntactic
forms, statically resolved targets, or another narrower capability. Only that
scope licenses negative reasoning.

For a call or reference attempt, the profile may have:

```text
RESOLVED             -> emit the KDM relationship with its target
MULTIPLE_CANDIDATES  -> retain candidates and do not emit one certain target
UNRESOLVED           -> retain occurrence/diagnostic; emit no guessed edge
```

KDM `Dispatches` may be emitted only when its KDM pointer-dispatch semantics
are established. It is not a generic escape hatch for an unresolved target.

## Examples against the profile

These examples use hypothetical TypeScript syntax to expose the semantic
boundary. They do not select an extraction technology.

### Ordinary functions

```ts
export function submitOrder(total: number) {
  return validateTotal(total);
}

function validateTotal(total: number) {
  return total >= 0;
}
```

The profile emits snapshot members for the source inventory item,
`CallableUnit`-compatible `submitOrder` and `validateTotal`, their KDM code
ownership, `SourceRef`/`SourceRegion` evidence, and an `action::Calls` relation
from an `ActionElement` at the call site to `validateTotal`. It may emit
`Imports`, `HasType`, or `Reads` only when their KDM meanings are established.
It does not emit a semantic `PurchaseAction`, and it does not make a runtime
execution claim.

### React composition

```tsx
function CheckoutPage() {
  return <PurchaseButton total={finalTotal} />;
}
```

The required v0 code profile can represent `CheckoutPage` and
`PurchaseButton` as KDM-compatible `CallableUnit`/`ControlElement` or other
selected code elements, grounded at their definitions. KDM UI is optional.
If a future declared UI capability establishes `UIElement` composition and
uses KDM's UI relationships or a KDM lightweight extension, it may emit that
fact. The code profile must not invent a universal `renders` fact merely from
the JSX spelling.

### Local call to an external package

```ts
import { createPaymentIntent } from "@stripe/payments";
export function pay(orderId: string) {
  return createPaymentIntent(orderId);
}
```

The profile may emit KDM `Imports` and `Calls` to an external `CodeItem` or
`CallableUnit` stub if package/member resolution establishes that identity.
The stub has local import/call `SourceRegion` evidence and no implementation
region. If only the package is resolved and the member is not, preserve the
unresolved member attempt instead of inventing a callable.

### Dynamic call

```ts
const handler = handlers[event.type];
handler(payload);
```

The profile may emit known `Reads`/references and local code identities. It
records an `UNRESOLVED` or `MULTIPLE_CANDIDATES` call outcome for the call
site. It does not emit a certain `Calls` edge to `handlers` and does not
interpret KDM `Dispatches` unless pointer-dispatch semantics actually hold.

### Unattached helper

```ts
function formatDebugLabel(value: unknown) {
  return `[debug] ${String(value)}`;
}
```

The KDM-compatible callable and its membership/evidence remain in the World
even with no semantic attachment. It is conceptually `UNATTACHED`; a separate
complete governance analysis would be needed before calling it `UNGOVERNED`.

### Source-range localization

For a changed range inside `validateTotal`, `SourceRegion` and the code
ownership/evidence mapping allow localization to the containing source file,
compilation/module unit, and callable. That result is independent of whether
`submitOrder` is governance-affected. Cross-snapshot rename or move matching
is later lineage work.

## Open questions before implementation

- Which KDM code-element subset is mandatory across the first supported
  languages?
- Which KDM relationship instances require a first-class `ActionElement` or
  other relationship support element in the World, and which can be projected
  directly as a typed assertion?
- What exact KDM lightweight-extension profile, if any, is needed for React
  UI composition?
- How should KDM `SourceRegion` line/position coordinates be reconciled with
  the existing grounding location format and byte/UTF-16 requirements?
- Which Build and Platform elements are needed to describe a user-declared
  boundary without implying that all build/runtime resources are in scope?
- How should KDM `Audit` and profile admission receipts be joined without
  making audit metadata a completeness assertion?
- What canonical external identity rule can remain stable within a snapshot
  without implying cross-version permanence?
- How should partial parsing and compiler-generated elements be represented
  while preserving universe closure?
- Which optional KDM capabilities provide enough value to promote to v0
  required status after experiments?

No implementation technology or physical KDM serialization is selected here.
