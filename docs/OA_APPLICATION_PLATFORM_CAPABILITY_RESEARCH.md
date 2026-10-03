# OA application platform capability research

**Status: research note. Not a contract, accepted architecture, or implementation plan.**

**Research question:** Which optional capabilities above OA Core would make
several ontology-backed applications substantially easier, safer, or more
interoperable to build without assigning their domain meaning to OA?

This note treats the Core boundary and the cross-domain falsification result
as settled. A bespoke application can use Core directly. A reusable capability
may still be worthwhile for *platform leverage*: one interface could enable a
generic inspector, verifier, SDK, agent, or evaluation tool across applications.
That is a different test from semantic necessity.

**Provisional finding:** The evidence favors a **small, optional read-side SDK
candidate**, centered on exact-publication citation verification, and further
research on a read-only application capability protocol. It does not support a
required semantic application layer or a full application runtime. The
cross-domain fixture is a deliberately tiny second data point, so this is a
candidate direction, not an accepted platform design.

## 1. OA's environment and the applications it could make cheap

OA's likely application path is: bounded evidence → partially constructed
World → reusable reads and joins → domain reasoning → optional further evidence
inspection → optional new durable publication. Evidence is often files,
bounded artifacts, tool results, or stable addressable online resources. A
semantic assertion may be constructed from several observations rather than
copied from one authoritative operational database. Construction may be lazy,
partial, and agent-authored. Worlds are sealed publications at fresh addresses;
reading or reasoning does not mutate them. Applications own the question,
interpretation, policies, and decisions. These are current OA assumptions, not
claims that all future deployments must have the same shape.

An application author should have to engineer the domain vocabulary, source
adequacy, interpretation, question-specific selection, reasoning, and any
operational action. Ideally, the author should get exact publication handling,
ordinary World reads, citation checks, evidence adapters, candidate validation,
and repeatable test fixtures with little infrastructure work. An agent should
be able to discover a World and inspect its epistemic limits without learning
the application; it cannot infer what a domain relation means just from its
name.

This environment rules out direct imitation of enterprise writeback,
streaming, mutable object transactions, or business-process orchestration.
Those capabilities solve different problems. It does leave a plausible OA
problem: several applications may exchange or display results whose published
support needs to be checked against an exact sealed World.

## 2. What Palantir generalizes for leverage

Palantir describes its Ontology as a **Language** for objects, links,
properties, actions, and logic; an **Engine** for read, write, materialization,
and subscription; and a **Toolchain** for SDKs and delivery. This division is
useful here because it shows that standardization is an economic choice: many
application builders and tools can share one model and execution surface. It
does not imply OA needs the same stack. See Palantir's current [Ontology system
description](https://www.palantir.com/docs/foundry/architecture-center/ontology-system)
and [developer toolchain](https://www.palantir.com/docs/foundry/dev-toolchain/overview).

| Generalized capability | Application problem removed; otherwise repeated work | Platform meaning versus domain meaning | Interoperability and tooling unlocked | OA analogue or mismatch |
| --- | --- | --- | --- | --- |
| Objects, properties, links, shared Ontology Language | Each app need not map backing data into its own entity API and link traversal model. | Palantir owns type/link/field mechanics; customers choose entity types, links, and their meaning. | Object-aware functions, Workshop widgets, OSDK bindings, agents, and lineage can all refer to the same model. [Ontology system](https://www.palantir.com/docs/foundry/architecture-center/ontology-system) | Core already supplies thin referents and typed relations. OA assertions additionally need grounding, origin, and publication identity. A second semantic object language would duplicate Core. |
| Ontology Engine and object-set reads | Apps avoid building indexing, query execution, subscriptions, and scalable materialization. | Platform owns read/write execution; domain owns predicates and interpretation. | Shared querying across functions and apps; object sets can be filtered, traversed, and aggregated. [Object sets](https://www.palantir.com/docs/foundry/functions/api-object-sets) | Core already exposes read-only SQL and explorer reads. Live subscriptions and mutable-state scale are environmental mismatches. Stable pagination/inspection may matter if OA grows. |
| Functions and published read-only queries | Each app need not invent how to bind computation to the shared model, publish it, and call it from other apps. | Platform owns callable packaging, inputs/outputs, execution, and API names; app owns function logic. | Workshop, APIs, and code clients reuse one computation. Published queries are explicitly read-only. [Functions](https://www.palantir.com/docs/foundry/functions/functions-on-objects), [queries](https://www.palantir.com/docs/foundry/functions/query-functions) | A narrow optional OA capability descriptor could help expose application-owned reads. No evidence for one function runtime or query language. |
| Actions | Each app need not implement common object edits, validation, and writeback integration. | Platform owns action invocation/transaction mechanics; domain owns action types and edit rules. | One action can be invoked by several apps and agents with consistent edits. [Action types](https://www.palantir.com/docs/foundry/action-types/overview) | OA's sealed World is not a mutable operational object store. Construction and later publication are not Palantir-style object edits. Defer. |
| Application builders and SDKs | Builders avoid rebuilding UI data binding and typed clients for every domain. | Platform owns widget/client bindings; app owns its workflows and presentation. | Workshop, custom apps, and generated OSDKs share objects, functions, and actions. [Workshop](https://www.palantir.com/docs/foundry/workshop/overview), [app building](https://www.palantir.com/docs/foundry/app-building/overview/) | OA has a bundled World inspector and Python/HTTP read surfaces, but no multi-application SDK or generated domain client. A generic read client is more plausible than an OA UI builder. |
| Agent exposure | Agent builders avoid wrapping every object, action, and query separately. | Platform owns discovery/exposure of declared resources; applications still define what actions and queries do. | Ontology MCP can expose object types, actions, and query functions to external agents. [Developer toolchain](https://www.palantir.com/docs/foundry/dev-toolchain/overview) | Core schema/assertion inspection is already possible. Discovering *application* capabilities and safe invocation is not standardized; this is a possible protocol experiment. |
| Branches, proposals, deployment | Teams avoid hand-built isolation, review, and release management of shared Ontology resources. | Platform owns branch/merge mechanics; domain owners approve content. | Changes can be tested against dependent resources and reviewed before merge. [Ontology branching](https://www.palantir.com/docs/foundry/ontologies/branching-ontology) | OA has candidate validation and fresh-address sealed publication, not mutable mainline ontology merges. A generic proposal workflow is unsupported; publication tooling may still help. |
| Lineage and observability | Builders avoid bespoke dependency graphs, traces, run history, and usage inspection for every app. | Platform owns cross-resource instrumentation; app owns the logic being traced. | Workflow Lineage connects objects, functions, actions, and apps; AIP observability exposes traces and metrics. [Workflow Lineage](https://www.palantir.com/docs/foundry/workflow-lineage/overview), [AIP observability](https://www.palantir.com/docs/foundry/aip/aip-observability) | Core has assertion support, derivation, construction receipts, and a World inspector. It lacks cross-application method/artifact lineage. That only pays off when several activities publish compatible provenance. |
| Evaluation | Builders avoid inventing test-case execution and comparison infrastructure around callable AI logic. | Platform owns suite/run/metric mechanics; domain owns expected outcomes and graders. | Comparable runs and variance inspection across functions. [AIP Evals](https://www.palantir.com/docs/foundry/aip-evals/overview) | OA already uses pytest and deterministic acceptance Worlds. A generic eval service is premature; reusable fixture and citation checks may be enough. |

The strongest Palantir leverage is **composition**, not a particular noun:
one shared object/query/function/action surface lets SDKs, application
builders, lineage tools, and agents interoperate. The cost is that the platform
must own the invocation and lifecycle semantics of those surfaces. OA has
evidence for a common *read* surface; it has no comparable evidence for a
common action or workflow surface. This is an inference from the linked
Palantir capabilities and OA's accepted contracts.

## 3. Secondary platform controls

These platforms confirm a recurring economic pattern: a shared schema,
metadata/read API, callable logic, and packaging surface lets multiple apps
reuse tooling. They do not establish that OA needs their mutable record model.

| Platform | Standardized above raw state | Leverage and OA limit |
| --- | --- | --- |
| ServiceNow | Application tables/fields, scoped apps, business rules, reusable flow actions, deployment. [Data model](https://www.servicenow.com/docs/r/application-development/define-tables-fields-application-records.html), [Workflow Studio](https://www.servicenow.com/docs/r/build-workflows/workflow-studio/flow-designer-arch-overview.html) | Shared records and callable actions make workflows reusable across apps. Its record-triggered mutation does not map directly to sealed Worlds. |
| Microsoft Dataverse / Power Platform | Tables, metadata-rich OData API, reusable server logic, events/connectors, and solutions for transporting app components. [Integration surface](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/work-with-any-type-app), [solutions](https://learn.microsoft.com/en-ie/power-apps/maker/data-platform/solutions-overview) | Common metadata and APIs let different app types and automation consume the same state. OA can borrow the discoverable read-surface motivation, not the assumption of one live business database. |
| Salesforce | Described object metadata, SOQL/REST queries, Apex triggers, and platform events. [Describe API](https://developer.salesforce.com/docs/platform/api-rest/guide/resources-sobject-describe.html), [query API](https://developer.salesforce.com/docs/platform/api-rest/guide/resources-query.html), [Apex](https://developer.salesforce.com/docs/platform/webconsole/guide/work-with-code.html), [events](https://developer.salesforce.com/docs/platform/platform-events/guide/platform-events-intro-architecture.html) | Discoverable schema and stable query interfaces enable external tools. Event buses and record triggers solve live-state coordination; OA has not shown that need. |

The cross-platform recurring benefit is a common **discoverable contract**
that third-party builders can target. A shared write/action/runtime model is
not the necessary price of getting that read-side benefit.

## 4. OA evidence: what was built, repeated, and intentionally different

The accepted Design contracts describe Construction, Judgment, and
Investigation as application behavior above Core. Its two profiles demonstrate
producer-neutral software subjects but share Design's vocabulary. The research
fixture is the only independent non-software consumer. The following counts
refer to current repository implementations, not a claim about future
production effort.

| Responsibility and concrete locations | Observed duplication and semantic check | Four-way classification | Possible platform gain |
| --- | --- | --- | --- |
| Vocabulary and selection: `software_governance/construction.py`, `judgment/case.py`; research fixture constructor and `joined_answer` | Design declares eight software-governance relations and has its own `CASE_RELATIONS` and `_selected`; research declares six plant-study relations and its own join. Similar shapes, different meaning. | **B application semantics** | None from moving relation names, applicability, or selection rules. |
| World publication: `profiles/core_v1/build.py`, both Design profile `build.py` files, research test `publish` | Four call sites reserve or reject fresh destinations. Design also copies a producer World into a fresh candidate and validates it. Lifecycle goal recurs; construction pathways differ intentionally. | **A Core guarantee** for sealing; **C potential shared tooling** for fresh-address orchestration | A test/publish harness could prevent accidental use of legacy in-place replacement without standardizing construction. |
| Citation snapshot and verification: `judgment/case.py` versus research test `citation`/`verify_result` | Two independent application implementations compare assertion ID, relation/values, and support. Design reconstructs warrant support and fingerprints it; research copies explorer grounding and compares it. These representations are intentionally different; the verification responsibility is the same. | **C candidate reusable platform capability** | One optional exact-publication verifier and minimal citation reference could power a generic citation inspector and prevent foreign or altered support from appearing published. |
| Exact-address check: Design `investigation/expansion.py` and research `verify_result` | Both check publication address. Design `verify_case` itself checks logical `world_id` and tuple/support but does **not** check `world_address`; its investigation expansion checks the address separately. That split is a concrete reason to test a single verifier entry point. | **C candidate reusable platform capability** | Prevent a recurring omission while retaining domain-owned selection and conclusion. No claim here that accepted Design tests fail. |
| Evidence reconstruction: `profiles/core_v1/evidence.py`, `software_governance/evidence.py`, research `reconstruct_support` | Three digest/span readers exist, but provider/handle/retention conventions differ. Mechanical verification recurs; source location semantics differ. | **A Core-path adapter contract** plus **D shared helper candidates** | Adapter-specific reusable bytes/digest utilities may reduce defects; one universal reconstruction rule is not established. |
| Method identity: Design producer `config_v0/produce.py`, Design constructor receipt, two profile judges and one investigator; research constructor and `answer` | Design records producer capability/version, Core constructor source digest, evaluator method/version/fingerprint, and investigation method ID/capabilities. The research result records no method identity. Different activities require different provenance. | **B application semantics** for capability meaning; **C hypothesis** for an optional descriptor | Generic method discovery or tracing might help only if tools consume declared inputs/outputs and identity across applications. A universal fingerprint field would misdescribe several activities. |
| Local artifacts: Design `judgment/artifact.py` and `investigation/records.py`; research result dict | Judgment, receipt, proposal, and local answer all live outside Worlds. Their status vocabularies and lifecycle are different; JSON serialization is superficial overlap. | **B application semantics** for payloads; **C hypothesis** for a minimal provenance attachment | A verifier could inspect an artifact's publication/citation/method references without interpreting its result. No generic Result ontology follows. |
| Application reads: `software_governance/reads.py` and Core `WorldExplorerAdapter` | One Design-specific `GovernanceView` is 421 lines; Core already has schema, paginated rows, assertions, derivations, and semantic SQL. Design's joins and source interpretation are domain-specific. | **A Core read guarantee**, **B application read semantics**, **C possible client/tooling** | A stable publication-aware client could avoid private Core access and make generic World inspection portable. |
| Investigation expansion, questions, proposals: Design `investigation/*` and config investigator; research source-only note | Design requires a question, receipt, and optional proposal for its workflow. The research consumer stops with a source-only observation. Same published/unpublished distinction, different next step. | **B application semantics** | No shared investigation/proposal lifecycle is justified. |
| Repeated profile evaluator code: the two Design `judge.py` files | Of ten same-named top-level functions, five have identical ASTs (`_applies`, `_binding`, `_construction_gap`, `_implementation_source`, `_one`); both builders' `_excerpt` and `_discard` are also identical. This is duplication **within Design**, not cross-domain proof. | **D mere convenience**, unless a later tool needs a stable interface | Shared Design helpers could reduce maintenance; copying them into OA would not create cross-application leverage. |

The research experiment's 12-citation local answer used no Case, Result, or
Proposal type. It did implement publication-anchored citation snapshots,
support reconstruction, and fresh-process verification. It exercised Core
unresolvedness and conservative negative inference. Those are useful second
observations of the *mechanics*; they do not reverse its finding that Core
alone suffices. See the [experiment report](OA_CROSS_DOMAIN_WORKING_SET_EXPERIMENT.md)
and [test](../tests/test_oa_cross_domain_working_set_experiment.py).

## 5. Pressure on the seven candidate families

**A. Publication-aware citation/context utilities.** The shared
responsibility is real: given an exact sealed address and finite assertion
IDs, re-read identity, values, origin, and published support. A verifier
should accept application-selected IDs without choosing them, making a Case,
or treating a local answer as World knowledge. A minimal optional reference
could be `publication address + assertion ID`; a snapshot may additionally
carry expected relation/values/support for independent comparison. Generic
inspectors and cross-application handoff become possible only if the reference
format and verification outcome are shared. This is the strongest **C**
candidate. Core's existing `WorldExplorerAdapter.assertion` supplies the read;
the optional layer would compose it consistently.

**B. Method/capability descriptors.** Design's producer/version receipt,
constructor digest, evaluator fingerprint, and investigator ID are distinct.
The research reader needed none. A descriptive identity plus declared
read-only capability and input/output hints might support discovery, tracing,
and eval tooling, but it cannot replace activity-specific provenance or assert
that a method is valid. Current evidence is **insufficient** for one
descriptor. In particular, putting evaluator fingerprints on every producer
would create meaningless fields.

**C. Artifact provenance.** A local artifact could optionally state which
publication, assertion IDs, and method produced it. Standardizing only these
links could let an inspector verify references without knowing the artifact's
meaning. Design's judgment and investigation outputs plus the research result
show plausible demand, but none needs cross-application artifact exchange yet.
Keep payloads application-owned; treat a provenance attachment as a **C
hypothesis**, not a generic Result type.

**D. Read/query surface.** Core already offers `schema`, paginated `rows`,
`referents`, `assertion`, `derivation`, `query_semantic`, and completeness reads;
the server exposes several of these over HTTP. A third app should use these
before asking for a new query language. The gap is discoverability of *which
publication* and *which app-owned read* to call, and a transport-neutral
verified citation shape. Generic World inspection is mostly **A** already;
an optional client or manifest may be **C** if it enables tools across apps.

**E. Construction tooling.** Core already validates candidates, seals Worlds,
and records construction receipts. The golden profile and research fixture
both reserve fresh roots; Design has its own copy-and-seal composition.
Optional source/digest helpers and a fresh-publication test harness could be
useful. Source coordinate rules and semantic construction must remain adapter
and application owned. Most helper code here is **D** until it prevents a
demonstrated publication error or enables generic inspection of construction
receipts.

**F. Candidate/publication lifecycle.** Core's candidate admission and seal
already solve the pre-publication mechanics. Design's proposal sidecar does
not proceed to admission; the research reader stops before proposal. A common
proposal, merge, or knowledge-admission workflow is **unsupported**. If a
future application needs to turn local discoveries into durable assertions,
test that transition specifically; do not equate it with Palantir's mutable
Ontology branch merge.

**G. Agent/application interoperability.** Given a bundle path, a generic
agent can already discover relation schemas, page assertions, inspect support,
and read completeness through Core. It cannot know which Worlds are available,
what domain question a relation answers, or which app-defined method is safe
to invoke. A read-only capability discovery protocol could name a World,
describe an application-owned operation's input/output contract, and state
that its output is local rather than published. This could enable one agent
to call several apps without custom wrappers. No second application has yet
exposed a callable capability, so the protocol is a **candidate experiment**,
not an established OA responsibility. Agent access must not turn schema
discovery into authority to infer domain truth or mutate a World.

## 6. Four architecture options and the author experience

| Option | What is shared | Benefit now | Present judgment |
| --- | --- | --- | --- |
| 1. Core → bespoke app | Existing World and adapter contracts only | Proven sufficient; lowest abstraction cost | Accepted baseline. |
| 2. Optional OA SDK/utilities | Publication-aware citation verifier, perhaps a client and test harness | Could prevent address/support mistakes and let one inspector consume citations from several apps | Best small research candidate; must prove use on a third app. |
| 3. OA application protocol | A discoverable, read-only description of app-owned capabilities and publication-bound inputs/outputs | Could let agents and tools invoke different applications through one surface | Plausible leverage, insufficient cross-app evidence. |
| 4. Full application runtime/platform | Common execution, action, artifact, proposal, deployment, and observability lifecycle | Strong only if many apps need the same operational semantics | Unsupported and mismatched to current sealed-World use. |

An OA author experience worth testing would be:

1. Choose evidence adapters and define domain relations and construction.
2. Construct a candidate, validate it, and publish at a fresh address using
   Core; use an optional publication harness if it demonstrably prevents
   replacement mistakes.
3. Define domain-specific reads and reasoning against Core's read surfaces.
4. When exporting a local answer, optionally attach publication-anchored
   citations that a different process can verify with a shared reader.
5. Optionally describe a **read-only** callable capability for human or agent
   discovery; only add this if multiple apps prove a common invocation need.
6. Keep further source inspection and any durable-knowledge proposal/admission
   flow in the application unless a later cross-domain workflow forces more.

This makes selection, interpretation, and decisions bespoke. It aims to make
publication discipline and third-party verification almost free. It does not
invent syntax, a new ontology, or a universal evaluator.

## 7. Recommendation and falsifier

If building the **third** OA application, the smallest shared experiment is a
**test-only, optional publication-aware citation reader/verifier** based on
Core's supported assertion and grounding reads. It should take an exact
bundle address and a finite list of assertion IDs or snapshots, return the
published content/support or precise verification errors, and let the app
choose the citations and interpret the result. Test it with Design and the
research fixture before considering an SDK. A separate read-only capability
discovery experiment should follow only when a third app offers an operation
that an independent agent genuinely needs to find and invoke.

The recommendation fails if the third app needs no transferable citations; if
the shared verifier cannot handle both existing representations without
discarding support or adding Design semantics; if Core's existing reads are
equally usable by independent consumers; or if no generic inspector/agent
can consume its output. Measure more than lines removed: count foreign-address
and altered-support mistakes prevented, independent consumers able to verify
one citation form, and whether a cross-app inspector works without an
application adapter. If only boilerplate falls, keep a local helper rather
than an OA SDK capability.

## 8. Final classification

The classification key is **A** Core semantic guarantee, **B** application
semantics, **C** reusable platform capability, and **D** mere convenience.
Only C candidates can justify an optional platform investment. “Candidate”
means research-worthy, not approved implementation.

| Candidate capability | Current owner | Cross-domain evidence | Palantir/platform precedent | Leverage gained if generalized | Cost/risk of generalizing | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| Publication-bound citation verification and inspection (**C**) | Design case verifier; research test verifier, composed over Core reads | Two independent consumers check exact publications and support; forms differ | Ontology SDK and shared query model enable many clients ([Palantir toolchain](https://www.palantir.com/docs/foundry/dev-toolchain/overview)) | Generic citation inspector, safer exchange, one check against foreign/altered assertions | May overfit two small representations; must retain source-specific support limits | **CANDIDATE OA SDK CAPABILITY** |
| Fresh-root publication harness (**D/C conditional**) | Core profile and each app/test builder | Four call sites implement address discipline, with different construction paths | Branch/deployment tooling standardizes safe release ([Palantir branching](https://www.palantir.com/docs/foundry/ontologies/branching-ontology)) | Could prevent accidental in-place replacement | May duplicate `Project` or falsely promise history without retained evidence | **SHARED UTILITY ONLY** |
| Source digest/span helpers (**D**) | Evidence adapters and fixtures | Three implementations, different provider conventions | Shared ingestion tools are common, e.g. ServiceNow table tooling ([ServiceNow data model](https://www.servicenow.com/docs/r/application-development/define-tables-fields-application-records.html)) | Fewer mechanical bugs | Universal adapter contract could erase source-specific losses | **SHARED UTILITY ONLY** |
| Domain vocabulary, selection, applicability, judgment (**B**) | Each application | Design and research meanings differ | Domain object/action types remain customer-defined ([Palantir Ontology](https://www.palantir.com/docs/foundry/architecture-center/ontology-system)) | Little cross-domain gain | False generic semantics; kernel contamination | **KEEP APPLICATION-OWNED** |
| Method/capability discovery descriptor (**C hypothesis**) | Design-specific IDs/receipts; no research counterpart | Different activity identities, no shared invocation yet | Published functions and query metadata are discoverable ([Palantir functions](https://www.palantir.com/docs/foundry/functions/manage-functions)) | Generic tracing, documentation, agent invocation if contract proves common | Collapses producer, constructor, evaluator, investigator into one misleading method | **INSUFFICIENT EVIDENCE** |
| External artifact provenance attachment (**C hypothesis**) | Design artifacts/receipts; research local dict | All can refer to a World, but no cross-app artifact consumer | Workflow lineage links many resource types ([Palantir lineage](https://www.palantir.com/docs/foundry/workflow-lineage/overview)) | One verifier/inspector across artifacts | A fixed Result envelope may claim shared semantics that do not exist | **INSUFFICIENT EVIDENCE** |
| Generic World read client and metadata inspection (**A/C split**) | Core explorer/server; app-specific views | Both applications use Core reads; Design adds domain joins | Dataverse metadata API and Salesforce Describe enable generic clients ([Dataverse](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/work-with-any-type-app), [Salesforce](https://developer.salesforce.com/docs/platform/api-rest/guide/resources-sobject-describe.html)) | Easier portable humans/agents, especially with citations | Redundant wrapper or premature generic query language | **CANDIDATE OA SDK CAPABILITY** |
| Read-only application capability discovery (**C hypothesis**) | No shared owner; caller-supplied Design investigation capability | Research app has a local answer but no callable contract | Ontology MCP exposes resources to agents ([Palantir toolchain](https://www.palantir.com/docs/foundry/dev-toolchain/overview)) | One agent could find/invoke many app-owned operations | Requires versioning, input/output, side-effect limits; no cross-app test yet | **CANDIDATE OA APPLICATION PROTOCOL** |
| Proposal/admission workflow (**B**) | Design investigation proposal; future apps if needed | Research source-only fact stopped without a proposal | Palantir uses ontology branch proposals ([branching](https://www.palantir.com/docs/foundry/ontologies/branching-ontology)) | Unproved in OA | Confuses local discovery with publication; forces workflow | **KEEP APPLICATION-OWNED** |
| Generic action, event, workflow, or application runtime (**C unproven**) | No OA owner | Neither app needs one | Palantir Actions, ServiceNow flows, Dataverse events, Salesforce platform events | Would coordinate live mutable apps if needed | High complexity; mismatched to sealed read-only Worlds | **INSUFFICIENT EVIDENCE** |
| Shared Design evaluator helper extraction (**D**) | Two Design profile judges | Five identical helper ASTs inside one application, none in research | Function reuse is a normal platform benefit but not sufficient by itself | Less Design maintenance | Mistakes intra-app duplication for OA platform evidence | **SHARED UTILITY ONLY** |

## 9. Explicit answers

1. **Is OA Core sufficient as an epistemic kernel?** Yes, for the accepted
   guarantees and the two exercised domains. That does not prove application
   value or universal adequacy.
2. **Is Core alone also a good developer platform for multiple applications?**
   It is a workable base. The current evidence suggests avoidable read-side
   verification and publication glue, but does not quantify a large productivity
   gain yet.
3. **Where is infrastructure repeated?** Exact-address handling, citation
   snapshots/support checks, digest/span reconstruction, and fresh-publication
   harnesses. Domain joins and judgment rules are not such infrastructure.
4. **What did Palantir generalize for leverage?** A shared model, read/write
   engine, functions/queries/actions, SDKs, agent exposure, and lineage so many
   apps and tools compose over the same resources.
5. **Which motivations transfer?** Discoverable reads, portable citations,
   shared inspection, and perhaps safe discovery of app-owned read operations.
   Mutable writeback, streams, and enterprise workflow do not presently transfer.
6. **What should OA leave bespoke?** Domain relations, interpretation,
   selection, applicability, conformance, questions, proposed meaning,
   authority, and operational actions.
7. **Evidence for a toolkit/SDK?** Yes, as an optional **candidate** for
   publication-aware citation verification and a thin read client; not an
   accepted package design.
8. **Evidence for a stable application protocol?** A credible interoperability
   hypothesis, but no demonstrated second callable app capability. Test it.
9. **Evidence for a semantic runtime layer?** No.
10. **Highest-leverage generic surface?** Exact-publication, inspectable World
    reads plus transferable verified citation references; a read-only
    capability-discovery contract might extend that if a third app needs it.
11. **What remains fully bespoke in Design?** Software subject/manifestation
    meaning, governance relations, producers' semantics, case selection,
    applicability, program finding, conformance, investigation decisions, and
    proposal policy.
12. **Smallest thing for the third app?** Test an optional citation verifier
    over Core reads, consumed by an independent inspector, before adding any
    application protocol or runtime.
13. **What falsifies it?** A third app that needs no portable citation checks,
    or a verifier whose common form either loses support fidelity or forces
    application semantics; lack of any independent consumer would also remove
    the main platform-leverage argument.

Core abstractions protect epistemic honesty. A platform abstraction earns its
cost only when standardization makes multiple applications safer, cheaper, or
interoperable in a way their separate implementations cannot achieve as well.
The current evidence reaches that bar only as a **candidate for read-side
tooling**, not as an application layer.
