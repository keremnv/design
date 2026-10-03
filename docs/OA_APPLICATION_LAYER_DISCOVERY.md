# OA application-layer discovery

Status: research note, 2026-09-25. Not a contract. Not Core authority. Not an
accepted architecture. Not an implementation plan.

In this note, **Ontology Author (OA)** means the general epistemic kernel,
Core Product v1. **Design** means the accepted Software Governance
application built above that kernel: Construction v0, Judgment v0, and
Investigation v0. It does not mean the historical design-checkout profile.

Authority for the inventory is production code and the accepted contracts.
The [evolution catalogue](DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md) is a
falsification set, not a design. Historical governance, authority, and
checkout packages are not current Design.

## 1. Question

Between OA Core and a domain application such as Design, is there a reusable
ontology-application model or runtime, and if so what is the smallest
responsibility surface it should own?

The exercise does not decide what Design should build next.

## 2. Current boundary

```text
local files, bounded artifacts, mechanical producer output
        ↓
evidence adapters          reconstruct observations; assign no standing
        ↓
OA Core                    referents, typed relations, assertions,
                           grounding, construction origin, revision,
                           sealed publication at a fresh address,
                           derivation, scoped completeness,
                           explicit unresolvedness as ordinary relations
        ↓
Design                     software subjects and manifestations,
                           governance propositions and bindings,
                           candidates and questions, Construction,
                           Judgment, cases, Investigation, proposals
```

Core does not know software-governance vocabulary. Design does not reopen
Core. The [four-region architecture](ARCHITECTURE.md) already says that a
mechanism which would not make sense in a wholly different evidence domain
belongs above Core, and that maintenance and inspection are not a fifth
write-authority layer.

Two facts keep the boundary from being read off package names:

- Design’s eight frozen relations are generic only inside Software
  Governance. Both acceptance profiles use them. A non-software application
  does not.
- Core’s own golden scenario, `profiles/core_v1`, already records an
  unresolved cross-source correspondence as ordinary grounded relations and
  an unresolved question. It does not use Design’s case, judgment artifact,
  or proposal.

Kernel tables for obligation, candidate association, and adjudication are
called out in the architecture note as deferred debt. They are not Core v1
guarantees and they are not evidence for a middle layer.

## 3. Inventory

| Name | Where it lives | Guarantee | Core knows it | Design vocabulary | Required by |
| --- | --- | --- | --- | --- | --- |
| Referent, typed relation, assertion id | World kernel | A claim has a declared shape and a tuple identity | Yes | No | Every sealed World |
| Grounding and construction origin | World kernel | Support and the mechanical/semantic character of a claim are stored with it | Yes | No | Admission and later inspection |
| Revision and fresh publication address | World kernel; Design cases copy the address | A sealed publication is an address. A reused `world_id` string is not that address | Yes. Design reapplied it | No | History; Investigation expansion |
| Derivation | World kernel | A registered computation retains inputs and revision state | Yes | No | Core derivations. Design judgments are not derivations |
| Scoped completeness | World kernel, and Design’s own `governance_completeness` rows | Emptiness inside a declared scope is not a negative | The kernel receipt, yes. The governance relation, no | The relation name, yes | Core consumers; Design’s incomplete-coverage control |
| Explicit unresolvedness | Ordinary relations in the golden scenario; `governance_question` in Design | A non-unique correspondence can be stored without picking a winner | The capability, yes. The relation, no | Design’s relation, yes | Golden refund correspondence; Design construction gaps |
| Contract admission | Kernel contract | A candidate tuple meets recorded-support rules before seal | Yes | No | Every publication. This is not Design admission of a proposal |
| Evidence reconstruction | Evidence adapters; Design calls them when building citation support | Observation text can be recovered from retained bytes | No | No | Citation support; Investigation proposals |
| `software_subject` | Design construction | A mechanically identified software individual, snapshot-local | No | Yes | Both Design profiles |
| `software_manifestation` | Design construction, optional | A producer-named coordinate whose bytes reconstruct | No | The receipt is software-scoped | Profiles that expose local content |
| Producer mechanical relations | The producer’s World, read by Design | Observations the producer chose to assert | No | Producer-owned (`program_invokes`, `config_route`, …) | Judgment of those facts |
| `governance_proposition` | Design | An interpreted sentence with its own evidence | No | Yes | Construction |
| `governance_binding` | Design | An established correspondence. Not applicability | No | Yes | Judgment `APPLIES` |
| `governance_candidate` and `governance_question` | Design | An unresolved correspondence, without a winner | No | Yes | Construction-gap control |
| Case | Judgment | A bounded citation set for one publication, one proposition, one subject. Inclusion is not applicability | No | The selection rules name Design relations | Judgment and Investigation |
| Citation verification | Judgment `verify_case` | Values and support must match the sealed assertion. Labels do not | Uses assertion identity | No mail or route words | Every judged case; Investigation refuses foreign citations through it |
| Judgment evaluator and artifact | Profile `judge` plus Judgment artifact | Applicability, program finding, and conformance, with a method id, version, rule parameters, and fingerprint | No | The rules, yes. The artifact fields, no | Accepted mail and config judgments |
| Context request | Judgment artifact | A missing fact. Not a search instruction. Not `DOES_NOT_APPLY` | No | Need names are demonstrated, not a closed ontology | Missing path; construction gap |
| Investigation question, receipt, proposal | Investigation records; config `investigate` | Explore beyond a case. Expand only with assertions already in that publication. Otherwise propose or stop | No | The config key list, yes. The envelopes, no | Investigation acceptance |
| Epistemic class on a proposal | Investigation | A label for the kind of unpublished discovery | No | The four words are generic; only `mechanical` was exercised | One proposal shape |
| Method fingerprint | Judgment evaluators only | The rule and the evaluator source are identifiable without a filesystem path | No | No | Judgment. Investigation explicitly did not copy it |

## 4. Classification

### A. Already Core

Referents, typed relations, assertions, grounding, construction origin,
revision, sealed publication at a fresh address, derivation, scoped
completeness, explicit unresolvedness as ordinary data, and mechanical
admission of a candidate tuple.

Design’s `governance_completeness` and `governance_question` are application
relations that use those guarantees. They are not missing Core features.
The golden scenario already represents an unresolved correspondence without
them.

### B. Clearly Design-specific

`software_subject`, software manifestation schemes, producer relation names,
`governance_proposition`, `governance_binding`, `governance_candidate`,
`governance_question`, applicability, program findings, conformance, the
mail and config rule parameters, the config published-key list, and the
selection rules inside `assemble_case` that name those relations.

Applicability is not binding. A program finding is not conformance. A
construction gap is not a judgment gap. A case inclusion is not judgment
support. Those distinctions are the application.

### C. Plausibly reusable application machinery

These are patterns Design repeated. They are not yet a layer. Section 5
says which of them survive a second domain, and section 6 says which
external platforms actually recur. None of them is promoted here.

| Pattern | Why it looks reusable | Why that is not enough |
| --- | --- | --- |
| A sidecar that cites one publication and is not itself a World assertion | Case, judgment artifact, investigation receipt, and proposal are four sidecars. Investigation refused to put lineage on the case | The golden scenario does not need them. External platforms’ “views” are queries over current records, not non-knowledge |
| Same-publication identity | Investigation rejects another directory even when `world_id` and labels match | Core already states that the bundle path is the revision address and that `world_id` may be reused. Design applied that rule; it did not discover a new one |
| A semantic procedure records the parameters it used | Judgment copies rule parameters and a source fingerprint into the artifact | Investigation refused the fingerprint. Producers and constructors do not use it. One activity earned it |
| Positive exclusion versus failure to prove | `DOES_NOT_APPLY` needs a positive basis. `UNKNOWN` and `UNRESOLVED` are not negatives | Core already requires scoped completeness before a negative read. Design specialized the words |
| Proposal kept apart from admission and publication | Investigation stops at the sidecar. The catalogue treats the later events as distinct | One application has done this once. No second application has proposed anything |

### D. Uncertain

| Abstraction | Why the evidence is insufficient |
| --- | --- |
| Epistemic class (`mechanical`, `semantic`, `source/evidence`, `other`) | The envelope allows four classes. Acceptance exercised `mechanical` once. `other` is an escape hatch, not a demonstrated type |
| A shared question record | Design has a construction question relation, a judgment request, and an investigation question. They are different records on purpose. The golden scenario uses an ordinary relation instead |
| Standing and currentness | The architecture note leaves authority standing to applications. Core currentness is derivation-input version, not “what is current governance.” The catalogue does not settle a current-view operator |
| Transition, action, correction, supersession, withdrawal | Named as future concerns and as catalogue scenarios. No accepted Design behavior implements them |

## 5. Second-domain falsification

The families used only as falsifiers are research or scientific knowledge,
legal analysis, and engineering or architecture decisions. None of these
applications is designed here.

| Design abstraction | Research | Legal analysis | Engineering decisions | Reading |
| --- | --- | --- | --- | --- |
| Typed relations, grounding, origin, sealed address, scoped completeness | A paper’s claim, its excerpt, and the method that extracted it | A cited holding, the passage, and who constructed the citation | A requirement, the drawing region, and the review method | Already Core. All three need it. None need SoftwareSubject |
| SoftwareSubject and manifestation | A sample or instrument is not a software subject | A clause is not a software subject | A component may be software, or a beam, or a specification paragraph | Design. Another application would declare its own individual |
| Proposition and binding | “This result supports this hypothesis,” bound to a dataset | “This clause obligates this party,” bound to a provision | “This decision governs this component” | The *shape* “interpreted sentence related to an individual” is plausible. The relation names and the software receipt are not. The golden scenario already did a join with ordinary relations |
| Case as Design defines it | A notebook might cite a subset of claims | A brief cites authorities | A review packet cites the drawings under discussion | Bounded citation is plausible. Design’s case also fixes one governance proposition and one software subject, and it is the input to applicability. That case is Design |
| Applicability and conformance | “Does this hypothesis apply to this run, and does the run meet it?” | “Does this rule apply to this party, and is the conduct conforming?” | “Does this decision apply to this component, and is the design conforming?” | The words travel. The evidence does not. Each domain would be inventing its own evaluator. Judgment v0 refused a universal policy language for this reason |
| Program finding | A measured value is not a program finding | A found fact is not a program finding | A calculated load is not a program finding | Design. It is the producer fact the evaluator used |
| Investigation expansion versus proposal | A lab note may find an existing assertion, or a measurement the dataset never asserted | Counsel may find a case already in the corpus, or a fact only in the record | A reviewer may find a note already published, or a dimension only on the drawing | The split “already asserted” versus “only in the source” is plausible. The config key list is not |
| One action that admits and publishes | Publishing a dataset is not the same event as a referee accepting a paper | Filing is not the same event as a court adopting a reading | Approving a drawing is not the same event as issuing it | The catalogue’s split holds in these families. It does not justify one transition type |

The sharpest in-repo falsifier is the golden scenario. It is a non-software
correspondence problem, with candidates and an unresolved question, and it
does not use Design’s case, evaluator, receipt, or proposal. A reusable
inquiry runtime is not required for that application.

## 6. External middle layers

The comparison is only what each platform generalizes above storage and
below a particular domain application. Sources are the vendors’ current
primary docs, retrieved 2026-09-25.

### Palantir Foundry

Ontology overview and core concepts
([overview](https://palantir.com/docs/foundry/ontology/overview/),
[core concepts](https://palantir.com/docs/foundry/ontology/core-concepts/)).

| | |
| --- | --- |
| Substrate | Datasets, virtual tables, and models integrated into the platform |
| Application model | Object types, properties, link types. Interfaces share a shape across object types |
| Computation | Functions over objects and object sets. Models can be bound to objects and actions |
| Inquiry | Object sets and link traversal. Workshop and other applications sit on that |
| Transition | Action types: a set of edits, plus side effects, as the way operators change objects |
| Lifecycle | Ontology Manager, versioning, and security on the ontology and on models |
| Left to the domain | Which objects, links, and actions exist; the operational procedures |

Foundry describes this ontology as an operational layer and a digital twin:
semantic elements plus kinetic elements. The object is mapped from backing
data. It is not a claim constructed from inspectable grounding.

### ServiceNow

[Build the data model](https://www.servicenow.com/docs/r/application-development/build-data-model.html),
[Flow Designer](https://www.servicenow.com/docs/r/application-development/building-applications/flow-designer.html),
[business rules](https://www.servicenow.com/docs/r/build-workflows/business-rules-classic/c_BusinessRules.html).

| | |
| --- | --- |
| Substrate | Tables and columns, often by extending a platform table such as task |
| Application model | Scoped application, tables, reference fields, dictionary |
| Computation | Business rules on query, insert, update, delete; script includes; Flow Designer actions |
| Inquiry | Queries and lists over those tables. Database-view rules are query-only |
| Transition | Flows for process; business rules when logic must run in the database thread |
| Lifecycle | Application scope, cross-scope access, update sets and store applications in the wider platform |
| Left to the domain | The tables and the process being automated |

The record is the operational item. A business rule mutates it. There is no
separate sealed claim whose support must be re-checked before reuse.

### Microsoft Dataverse

[Dataverse introduction](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-intro),
[apply business logic](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/processes),
[plug-ins](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/plug-ins).

| | |
| --- | --- |
| Substrate | Tables, columns, relationships |
| Application model | Table metadata reused by every app on that table |
| Computation | Business rules, calculated columns, real-time workflows, plug-ins on data events |
| Inquiry | Apps and queries over the same tables. Business rules can also affect forms |
| Transition | Business process flows guide people; cloud flows and plug-ins change rows; connectors reach other systems |
| Lifecycle | Solutions package metadata. Server logic is registered on table messages |
| Left to the domain | The tables and the process. Microsoft tells makers to prefer declarative logic and to use plug-ins when that is not enough |

Logic is reusable across apps because it is attached to the shared table,
which those apps treat as current authoritative state.

### Salesforce

[Data model](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/data_model.htm),
[Apex](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm),
[Flow Builder](https://help.salesforce.com/s/articleView?id=sf.flow_build.htm&language=en_US&type=5),
[record-triggered flows](https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger.htm&language=en_US).

| | |
| --- | --- |
| Substrate | Standard and custom objects and fields |
| Application model | Objects, relationships, record types, validation rules |
| Computation | Formula fields, Apex, triggers |
| Inquiry | SOQL and list views; Flow Get Records |
| Transition | Record-triggered and screen flows create, update, and delete records; Apex DML does the same in code; approvals are a flow task |
| Lifecycle | Metadata components and packaging |
| Left to the domain | Which objects and automations exist |

A flow updates the record. The platform does not keep the pre-update
publication as a sealed address that later judgments must cite.

### Recurring families, and where OA’s setting drops them

| Family | Recurs externally | OA setting |
| --- | --- | --- |
| Model above raw storage | Objects, tables, custom objects | Core already has typed relations. Another object system would duplicate that and add identity the evidence does not have |
| Logic bound to that model | Functions, business rules, Apex, plug-ins | Real, but the external logic mutates current rows. Design’s activities do not share one contract |
| Query or interaction | Object sets, lists, Get Records, apps | Real for operators. Design’s case is a verified citation set, which those queries are not |
| Action or transition | Actions, flows, plug-ins, DML | Real for operational writeback. OA’s accepted path seals a new address and does not write the old one |
| Lifecycle and security | Solutions, packages, scope, ontology security | Real for multi-team platforms. OA’s current environment is local files and bounded artifacts. No accepted Design behavior needs an authorization platform |

Enterprise integration, streaming ingestion, change-data capture, master
data, and distributed transactional writeback are outside the environment
this note is about. Copying the layers those problems forced would answer
a different product.

## 7. Recurring responsibilities inside Design

| Candidate | Design evidence | Second domain | External recurrence | OA-specific reason | Disposition |
| --- | --- | --- | --- | --- | --- |
| Typed relation schema | Design declares relations with Core’s machinery | Any evidence domain needs some schema | Objects, tables, custom objects | Core already is this layer | KEEP IN CORE |
| Object types and inheritance | Not used. Subjects are referents plus a relation | A legal “instrument” hierarchy is possible and unshown | Central on all four platforms | Would hide partial, constructed individuals behind a platform object | REJECT AS GENERIC ABSTRACTION |
| SoftwareSubject | Both Design profiles | Falsified. Other domains have different individuals | Object instances look similar and are authoritative rows | The receipt is software observation, not governance | KEEP IN DESIGN |
| Manifestation coordinate | Optional, producer-defined scheme | A page span or a drawing region is the same *kind* of need, with a different scheme | Attachments and files, without a content digest tied to a claim | The scheme stays with the producer. Core grounding already holds the bytes | KEEP IN DESIGN |
| Producer, constructor, derivation, evaluator, investigator | Five activities, deliberately different records | A lab has instruments, arguments, and reviews, and they are not one method | One function or plug-in type | Collapsing them erases mechanical versus semantic, and exploration versus admission | REJECT AS GENERIC ABSTRACTION |
| Judgment method record | Rule parameters plus a path-free fingerprint | A review rubric could record its parameters | Function versioning is the weak analogue | Only one of the five activities needed it | RESEARCH FURTHER |
| Design case | One proposition, one software subject, verified citations | A brief is similar only after the software selection rules are removed | Object sets and list views | The epistemic half is “working set is not the corpus.” The golden scenario did not need a case type | RESEARCH FURTHER |
| Applicability and conformance | Mail and config evaluators | Words travel; no shared rule exists | Validation rules are current-row checks | Design’s judgment contract | KEEP IN DESIGN |
| Context request | Missing fact, not a search | A review can name a missing exhibit | Not a platform primitive | Useful inside Design. Not shown elsewhere in this repo | KEEP IN DESIGN |
| Investigation receipt | Lineage outside the case | A research log could point at a notebook | Workflow history is an audit of writes | One application, one receipt shape | KEEP IN DESIGN |
| Proposal versus admission versus publication | Proposal exists. Admission and publication of it do not | The split is plausible | Platforms collapse them into one write | Catalogue constraint. One write type would erase it | REJECT AS GENERIC ABSTRACTION |
| Publication address distinct from `world_id` | Investigation acceptance | Any second sealed corpus has the same bug if it trusts the logical id | Deployment versions are a different problem | Already a Core publication rule | KEEP IN CORE |
| Scoped completeness before a negative | Design’s incomplete-coverage control | A partial literature review must not treat silence as refutation | Not central. Platforms usually model the records they have | Fundamental to partial knowledge | KEEP IN CORE |
| Generic workflow, registry, or plugin host | Design refused these at each freeze | A second app might want one, which is not evidence yet | Central externally | Convenience. No shared invariant | REJECT AS GENERIC ABSTRACTION |

No row earns `CANDIDATE OA APPLICATION LAYER`. That disposition required
Design evidence and an independent recurrence of the same guarantee, or an
exceptionally strong generic guarantee of its own. The strong guarantees
found here are already Core. The Design repetitions are real and still
one application wide.

## 8. Candidate OA application layer

No middle runtime is justified.

The smallest honest surface is empty. What follows is the pressure test of
the four families that looked like they might fill it, and why each one
stops short.

### Application model

Fundamental question: does a domain need a schema above Core’s typed
relations?

Inputs and outputs would be type declarations and instances. Core already
accepts relation declarations, roles, and referents. Design’s vocabulary is
eight relations whose names are the application. A legal application would
declare different relations with the same kernel calls.

Generic guarantee worth adding: none. An object type would not protect a
guarantee Core’s relations fail to protect.

What stays application-owned: the relation names and their meanings.

Why Core should not grow it: Core’s completion bar is a mechanism that
cannot be expressed honestly with current primitives. Design expressed its
vocabulary with those primitives.

Design evidence: two producers, one relation vocabulary, zero need for a
type registry.

External evidence: every platform has objects because many applications
share one mutable database. OA applications do not share one current row
store.

Falsifier: a second OA application that cannot declare its individuals as
referents plus relations without lying. The golden scenario is a counterexample
in the other direction: it did not need SoftwareSubject.

### Capability and method model

Fundamental question: are producer, constructor, derivation, evaluator, and
investigator one declared computation?

They are not.

| Activity | What it may read | What it may emit | What it must not do |
| --- | --- | --- | --- |
| Producer | Source bytes | Mechanical assertions in a software World | Interpret governance prose |
| Constructor | Evidence and that World | Semantic governance relations, then a seal | Treat a producer relation name as the ontology |
| Derivation | Registered inputs inside a World | A derived tuple with input versions | Decide applicability |
| Evaluator | The explicit case only | A judgment artifact | Open the World or the repository |
| Investigator | The publication, plus capabilities the caller passes | Another case, a proposal, or nothing | Treat a discovery as an assertion, or admit it |

A shared record of “id, version, inputs, outputs” would fit all five the
way a function signature fits a plug-in. It would also hide the differences
the contracts exist to protect. Judgment’s fingerprint is earned because
that evaluator’s rule is the meaning of the artifact. Investigation’s
result is the added assertion ids or the proposal basis, and a fingerprint
was refused. A producer’s method is the capability version on the subject
receipt, which is data, not an evaluator fingerprint.

Falsifier: force one method record onto the config investigator and onto a
TypeScript producer, and show that the record still prevents a hidden
semantic choice without also forcing rule parameters the producer does not
have. That has not been shown.

### Inquiry model

Fundamental question: which of case, judgment, context request,
investigation question, and receipt could another application use without
importing applicability and conformance?

The separable guarantee is narrow:

```text
a working set of citations is not the publication
every citation in it still verifies against that publication
a later conclusion names the citations it used
```

Design demonstrates it. Judgment verifies the case. Investigation will not
add a citation `verify_case` rejects. The conforming judgment does not cite
`config_member` merely because the case contains it.

That guarantee does not require an object named Case. The golden scenario
keeps its working correspondence in ordinary relations inside the
publication, because there the correspondence *is* the knowledge being
constructed. Design’s case exists because the judgment must not become more
knowledge in the World. A research notebook has the same reason only when
the notebook is not itself the corpus. Until a second application has that
shape, a case runtime would standardize Design’s selection rules (one
governance proposition, one software subject, a fixed relation list) under
a generic name.

Falsifier: implement the notebook as Design cases and count how many fields
are unused or lying. Or express the notebook as ordinary relations plus one
JSON sidecar and show that no shared code was required. The second outcome
is the one this repo has already lived through: Judgment and Investigation
share `verify_case` by call, not by a new framework.

### Transition and action model

Fundamental question: is there one reusable transition among proposal,
admission, publication, correction, supersession, withdrawal, and external
action?

The catalogue’s constraint, which Design’s investigation pass obeyed, is:

```text
discovery != proposal != admission != publication
```

Investigation implements discovery of an existing assertion, and a proposal
for a field the producer did not assert. It does not admit or publish.
Construction’s seal is a different event: mechanical admission of a
candidate World, at a fresh address. Kernel contract admission is a third
event: shape and recorded support. Calling all three “an action” makes a
proposal look like a write.

External platforms generalize the opposite design. An action, flow, or
plug-in applies an edit to current state, sometimes with side effects.
That is the right abstraction when the row is the business fact. It is the
wrong abstraction when applying it would skip the distinctions above.

Several families, not one type:

| Family | Status |
| --- | --- |
| Discover an assertion that already exists | Accepted in Investigation. It is a read plus a new case |
| Propose something the publication does not assert | Accepted as a sidecar |
| Admit a proposal | Not designed |
| Publish a new sealed address | Core, for Worlds. Not a way to accept a proposal |
| Correct, supersede, withdraw | Catalogue only |
| External operational action | Outside the current environment |

Falsifier: a single transition type whose fields can represent a proposal
and a seal without a nullable “kind” that reintroduces the split. If the
kind field does all the work, the type is not shared.

## 9. Rejected generic abstractions

Rejected as a layer, not rejected as future Design work:

| Abstraction | Why it was considered | Why it is rejected |
| --- | --- | --- |
| Object model | All four platforms lead with it | Core relations already exist. Objects in those platforms denote authoritative operational entities |
| Universal method or plugin registry | Five Design activities look like “computations” | They have incompatible permissions. Design refused a registry at each freeze |
| Generic policy or rule language | Two evaluators share an artifact | The contract forbids a universal policy language. The rules stay in the profiles |
| Generic question ontology | Three question-shaped records | They were kept apart so a construction gap would not become a judgment request |
| Generic workflow or action engine | Platforms put process above the data model | Accepted OA behavior does not step through mutable state. The catalogue forbids collapsing proposal into publication |
| Common JSON envelope as an architecture | Case, artifact, receipt, and proposal are JSON | A shared serializer does not protect an invariant. Section 9 of the task: envelopes are conveniences |
| Capability registry | Investigation takes caller-supplied capabilities | The caller passed a map. No registry was required to keep the World unchanged |
| Authorization platform, scheduler, streaming, CDC, master data | Standard enterprise middle-layer pieces | No accepted scenario. The environment is local and bounded |
| UI framework | Workshop, model-driven apps, Lightning | No accepted Design surface depends on one |

What those platforms generalized that OA should currently leave out:
enterprise data integration, stream processing, transactional writeback,
a generic workflow engine, a general UI framework, an authorization
platform, an object model, an automation scheduler, and distributed
eventing.

The useful negative lesson is that their middle layer exists to let many
applications share one current operational database and the automations
that write it. OA’s middle-looking problems are about not mistaking a
later reading for the sealed claim. Those are kernel guarantees, not a
workflow host.

## 10. Why the epistemic kernel is heavier

Operational platforms can leave grounding, origin, completeness, and
revision off the center of the model because the row is entered as the
thing it denotes. The account *is* the customer record. A validation rule
checks the row. A flow updates the row. Silence usually means the field
was not filled, inside a schema the organization treats as the inventory.

OA’s claim is different. Someone, or something, constructed it from
evidence by a method, and a later consumer is supposed to reuse the claim
without redoing that work. Reuse without the method’s trace is how a
plausible sentence becomes an unexamined fact. The kernel therefore stores
the distinctions that make reuse inspectable:

| Guarantee | What fails if it is left to each application |
| --- | --- |
| Grounding separate from the assertion | The tuple can be copied and the warrant dropped. Design’s citation check exists because this already happened in spirit: a tuple-only digest was not enough |
| Construction origin | A mechanical observation and a semantic interpretation become the same kind of row. Design’s producer-versus-constructor split depends on the kernel keeping them distinct |
| Scoped completeness | An incomplete publication reads as “not governed,” “not cited,” or “refuted.” Design’s unbound call site under `INCOMPLETE` coverage is the application form of this |
| Fresh publication address | A later write changes the bytes a previous judgment cited. Investigation’s cross-publication rejection is this rule applied to a reused `world_id` |
| Explicit unresolvedness | A constructor or an agent picks a winner in order to have a total model. Both the golden scenario and Design’s construction gap refuse that |

Classification of those guarantees:

| | |
| --- | --- |
| Fundamental to evidence → knowledge | Grounding, origin, scoped completeness, sealed address, room for an unresolved correspondence |
| Amplified by agent authoring | All of the above. An agent produces claims cheaply and at a volume a reader will not reconstruct. The kernel makes the cheap output fail closed unless support, scope, and address are present. Humans authoring slowly need the same distinctions; agents make omission the default |
| Specific to Design | Applicability, conformance, software subjects, the eight governance relations |
| Accidental or historical | Obligation and adjudication tables sitting in the kernel package. The architecture note already marks them as debt, not as the Core v1 story |

Attempted falsification of this rationale: “a careful application could
store support in a sidecar and keep the kernel as a plain relation store,
the way a warehouse stores tables and a catalog stores lineage.” Design
already tried the sidecar half. The citation still has to point at an
assertion whose support the publication itself retains, because a sidecar
digest of the tuple did not detect a changed warrant. Support that can be
detached from the sealed address is not support a later consumer can
trust. That argues for keeping grounding in the kernel, not for a second
lineage product.

A second falsification: “revision is just version control, which every
platform has.” Salesforce and Dataverse version metadata and keep audit
history of rows. The consumer still reads the current row. OA’s consumer
of a judgment must read the publication that judgment named, including
after a newer publication exists. Those are different guarantees. Audit
history does not replace a fresh address.

## 11. Alternative layerings

### The five-layer sketch

```text
product
domain application
OA application model / runtime
OA Core
evidence and compute environment
```

The middle box is not coherent yet. It has no responsibility that is both
shared and unsafe to leave either in Core or in Design. Filling it with
model, method, inquiry, and transition imports four platform families that
section 7 did not survive.

### Two layers, which is the current boundary

```text
OA Core
    evidence → sealed, inspectable, partial knowledge
Design
    software observation, governance interpretation, judgment, investigation
```

This is sufficient for the accepted behavior. Design already calls Core
and does not need a framework between the call and the vocabulary.

### A discipline, not a runtime

The repetitions worth remembering, without a package, are:

```text
a sidecar is not an assertion
a reused world id is not a publication
failure to prove is not a negative
a method that makes a semantic choice records the choice
discovery, proposal, admission, and publication stay separate events
```

These are writing rules for the next application. They are not types.

### Something that was generalized too early

The kernel package’s obligation, candidate-link, and adjudication tables.
They look like an application runtime that landed below the application.
Core v1’s accepted story does not depend on them. They should not be cited
as proof that OA already has a generic case or action model.

### Something that looks like Design and is actually Core

Publication address, scoped completeness, and “do not invent a winner when
the correspondence is unresolved.” Design reimplemented the last of these
as `governance_question` because the *content* is governance. The
*refusal to invent a winner* was already the golden scenario.

## 12. Falsifiers

| Proposed middle-layer claim | What would falsify it | What the repo shows |
| --- | --- | --- |
| OA needs an object model above relations | A second application cannot name its individuals with referents and relations | The golden scenario names requirements, code, and rows without one. Design’s subjects are referents |
| Producers and evaluators are one method type | One record prevents a hidden semantic choice in both a producer and an evaluator without unused fields that change meaning | Investigation refused Judgment’s fingerprint. The activities stayed separate |
| Design’s case should become the inquiry runtime | A non-governance application needs those fields and cannot use a sidecar plus `verify_case` | The golden scenario has no case. Investigation’s case is a Judgment case, not a new type |
| One action type should cover proposal through publication | A proposal and a seal can share a transition without a kind field that restores the split | Investigation stops at the proposal. The catalogue treats the later events as distinct |
| External action or workflow is part of the same layer | An accepted OA scenario writes an operational system as part of knowing | No accepted scenario does this |
| The kernel is heavy only because of software governance | Removing Design leaves no need for grounding, completeness, or fresh addresses | The golden scenario is that removal |

## 13. Open questions

- Whether a second OA application, aimed at something other than software,
  would need a sidecar that verifies citations and is not stored as
  assertions. The golden scenario did not. A notebook or a brief might.
- Whether Judgment’s method record becomes a writing rule for every
  semantic procedure, or stays specific to evaluators whose hidden
  constants would change the conclusion.
- Whether proposal admission, when it is eventually specified, wants any
  shared check beyond Core’s existing contract admission. That is a Design
  or catalogue question, not a reason to add a transition framework now.
- Whether the kernel’s historical obligation tables should be ignored,
  moved, or deleted. Out of scope here. They are not the middle layer.

## 14. Recommendation

There is not enough evidence for a reusable runtime between OA Core and
Design. A few patterns are visible. They are disciplines the next
application should try to violate, not a framework to extract.

Keep the implementation boundary:

```text
OA Core → a bespoke application
```

Do not add an OA application model. Do not move Design’s case, proposal,
or evaluators into a generic package. Do not import object types, workflow
engines, or action frameworks from operational platforms. Their middle
layer shares current state across applications. OA’s kernel exists so a
constructed claim can be reused without being mistaken for that kind of
state.

Before any reusable application layer is implemented, one additional OA
application is needed, and it should not be another software-governance
profile. Two profiles of Design already failed to justify a vocabulary
above the eight relations. A third profile would fail the same way.

The smallest next experiment that could falsify this recommendation:

Take a bounded non-software corpus the golden scenario already resembles,
such as the requirements, code, and tabular correspondence, and try to
answer one new question that is not itself a new sealed relation. Require
the answer to cite existing assertions, to remain outside the World, and
to refuse a source fact that was never asserted. If that can be done with
ordinary relations plus the existing `verify_case` behavior, this note
stands. If the attempt has to recreate Design’s applicability, case
selection rules, and proposal envelope in order to avoid lying, the empty
middle layer is wrong, and the specific lying field is the responsibility
to specify. Do not start that experiment by defining the framework.
