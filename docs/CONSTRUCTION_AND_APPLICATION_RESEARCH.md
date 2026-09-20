# Construction Envelope, Relational Leverage, and Program-Linked Applications

**Status:** Research synthesis, not architecture authority  
**Date:** 2026-09-18

## 1. Research question

The constructor is intentionally able to perform arbitrary computation over heterogeneous evidence. That makes computational expressiveness a poor product boundary: almost any structured representation could be emitted.

The useful boundary is instead:

> What recurring work is `construct()` unusually good at, which of those constructions deserve durable representation as a World rather than direct reinspection or a simpler data structure, and what stronger applications become possible when semantic knowledge is linked into a program representation and then into concrete change?

This research separates three sources of value:

1. **Construction value:** useful identities, relations, abstractions, and synthesized joins are compiled from heterogeneous evidence.
2. **World value:** the compiled artifact carries an epistemic floor—identity, revision, grounding/lineage, origin, scoped completeness, unresolvedness, and sealed historical integrity—without pretending to guarantee semantic truth.
3. **Application value:** domain-specific logic composes the World into questions, authority, currentness, adequacy, change impact, decision rights, and action.

The constructor does not need to maximize all World guarantees. The guarantees are a floor on epistemic honesty, not a checklist every construction must exercise.

---

## 2. What existing fields already solve

### 2.1 Data integration and OBDA

Ontology-Based Data Access (OBDA) provides a conceptual view over multiple heterogeneous sources. Mappings relate source schemas to ontology terms, and users query the conceptual vocabulary rather than each source directly. Virtual knowledge graphs keep the graph virtual and rewrite queries back to source systems.

This establishes that the broad thread—heterogeneous sources → canonical conceptual model → query—is well established.

The important distinction for this project is that `construct()` can do more than mapping/query rewriting:

- resolve cross-source identity;
- create semantic abstractions;
- materialize relations not explicitly present in a source;
- synthesize relations from several evidence sources;
- use mechanical and intelligent interpretation in the same construction;
- persist the result as a revisioned artifact.

Virtual KGs have an important advantage: source freshness. Materialized KGs can have better query performance when mappings are sufficiently complex, at the cost of maintaining the materialization. This maps directly onto the World economics: if a relation can be cheaply reconstructed by query rewriting, materialization is weakly justified; if the join is expensive, semantic, repeatedly reused, or needs historical identity, materialization becomes more attractive.

### 2.2 Ontology/schema matching

Ontology matching explicitly warns that adopting an ontology does not eliminate heterogeneity; it can move heterogeneity to the ontology layer. The central task is constructing correspondences between semantically related entities. Those correspondences can be equivalence, subsumption, disjointness, consequence, or richer relations.

This supports treating **constructed joins** rather than “ontology existence” as the unit of value.

### 2.3 Entity matching / entity resolution

Entity matching identifies records that refer to the same real-world entity across sources whose structures, schemas, formats, terminologies, and semantics differ.

This closely corresponds to the constructor’s cross-source referent construction. Identity is not merely an implementation detail: once identities are unified, facts from otherwise disconnected systems become composable.

### 2.4 Knowledge-graph construction

Modern KG-construction research distinguishes simple fact extraction from conceptualized structured knowledge. Common stages include entity acquisition/typing, coreference resolution, relationship extraction, fusion/refinement, and knowledge evolution.

The constructor’s expressive envelope overlaps strongly with this field, but the World’s epistemic model provides an independent axis: two graphs can contain the same edge while making very different claims about where it came from, how it was produced, whether absence is meaningful, and whether the edge is unresolved or historically bounded.

### 2.5 Provenance and lineage

W3C PROV models entities, activities, derivation, revision, agents/responsibility, and alternate descriptions of the same thing. Importantly, provenance describes production/influence; it does not by itself prove semantic correctness or authority.

OpenLineage similarly represents jobs, runs, input/output datasets, and exact lineage relations.

These systems are strong substitutes when the problem is primarily transformation/dataflow lineage. A World should not be justified merely because provenance is useful.

### 2.6 Graph and operational ontology products

Graph systems provide native nodes, edges, traversal, dependency analysis, and graph algorithms. Microsoft Fabric explicitly distinguishes Graph from Ontology: Graph stores and computes over connections; Ontology defines shared entity meaning, properties, relationships, rules, constraints, and source bindings.

Palantir’s Ontology is an operational layer over organizational data and models with objects, links, actions, functions, permissions, and applications. This is significant overlap with the broader “operational model” direction.

The project therefore should not claim novelty merely from:
- graphs;
- ontologies;
- heterogeneous integration;
- object/link operational models;
- workflow actions.

The sharper differentiation is the combination of arbitrary semantic compilation with an explicit epistemic artifact model and application-controlled stronger guarantees.

---

## 3. Construction taxonomy

The recurring useful constructor operations can be reduced to five primary join families plus three secondary operations.

### 3.1 Representation joins

Map heterogeneous source forms into a shared operational vocabulary.

Example:

```text
JSON.service_name
YAML.app
database.deployment_service_id
        ↓
Service
```

Typical construction: mechanical or rule-based, occasionally semantic.

This is legitimate but low differentiation when it simply restates source schemas.

### 3.2 Identity joins

Establish that multiple source descriptions refer to one operational referent.

Example:

```text
"billing-api"
service_id=481
repo/services/billing
"Billing Service"
        ↓
Service:billing
```

Identity joins are high leverage because all facts attached to the previously disconnected descriptions become composable.

### 3.3 Relation joins

Establish reusable relations between identified things.

Examples:

```text
Requirement R → governs → Component C
Component C → owned_by → Team T
Service A → depends_on → Service B
```

Relations may be:
- source-explicit;
- mechanically extracted;
- semantically interpreted;
- adjudicated.

The important threshold is not the presence of an edge, but whether the edge creates an operational join that was not already cheaply available from one source.

### 3.4 Abstraction / classification joins

Relate source-native referents to constructed domain concepts.

Example:

```text
StripeAdapter → instance_of → PaymentProvider
```

This is semantic lift: construction introduces a conceptualization useful to downstream reasoning.

### 3.5 Synthetic cross-source joins

Create a relation that no source explicitly contains.

Example:

```text
requirement: R applies to production payments
config:      S is the production payment service
code:        C invokes S
                       ↓
constructed: R governs C
```

This is the most characteristic form of semantic compilation: several source-native observations and joins are composed into operational knowledge.

### 3.6 Fusion

Preserve or reconcile competing claims.

Example:

```text
CMDB:      owner = Team A
CODEOWNERS owner = Team B
catalog:   owner = Team A
```

The constructor may preserve conflict, establish an effective interpretation under application authority, or leave the question unresolved.

### 3.7 Derivation

Mechanically compose existing World relations.

Example:

```text
A → B
B → C
  ↓
A → C
```

This should generally remain deterministic derivation rather than become a new semantically asserted BASE fact unless there is a specific reason to materialize it.

### 3.8 Cross-revision correspondence

Relate identities across revisions:

```text
G0 entity ↔ G1 entity
```

This is useful for long-lived semantic bindings and program-change analysis but should remain outside the primitive epistemic core.

---

## 4. Semantic lift and epistemic strength are independent

A useful World need not maximally exercise the epistemic stack.

### Semantic / relational lift

A rough qualitative progression:

```text
representation change
    ↓
normalization
    ↓
identity integration
    ↓
new relations
    ↓
semantic abstraction
    ↓
cross-source synthesis
```

### Epistemic strength

An independent progression:

```text
structurally valid
    ↓
revisioned
    ↓
grounded / provenance-aware
    ↓
origin-aware
    ↓
explicitly incomplete/unresolved
    ↓
scoped-complete where warranted
    ↓
support/currentness-aware
    ↓
authority/admission governed
```

Examples:
- A mechanically extracted program graph can have modest semantic lift but strong provenance/completeness.
- An LLM-generated domain graph can have high semantic lift but weak epistemic strength.
- A governed operational World can have both.

The rule is:

> A construction may use only the epistemic machinery it needs, but must never imply a stronger guarantee than it has established.

---

## 5. Constructor limits

`construct()` has almost no interesting computational limit. Its meaningful limits are epistemic, representational, temporal, and economic.

### 5.1 Evidence limit

Construction may introduce interpretation, but it must distinguish:
- source-native observation;
- mechanical extraction;
- semantic interpretation;
- derivation;
- adjudication.

Persistence must not launder semantic interpretation into observed fact.

### 5.2 Identity limit

Cross-source identity requires an explicit basis. Identity can be mechanical, semantic, adjudicated, or unresolved. It should not disappear into an implicit join whose epistemic status cannot later be inspected.

### 5.3 Abstraction limit

The constructor may introduce useful concepts not present in any source, but constructed concepts must remain distinguishable from source-native identities.

### 5.4 Information-loss limit

World construction is normally lossy. The World is a compiled operational representation, not a replacement for all source reality. Addressability back to evidence is therefore fundamental.

### 5.5 Completeness limit

A World can model a small useful slice of reality. Absence becomes meaningful only when completeness is established over an explicit relation/universe/scope.

### 5.6 Temporal limit

A sealed World describes a bounded historical construction. Persistence does not make semantic facts timeless.

### 5.7 Semantic reliability limit

The kernel cannot guarantee the objective truth of an intelligent semantic interpretation. It can guarantee facts about the interpretation:
- identity;
- origin;
- grounding;
- revision;
- structural validity;
- completeness claims;
- unresolvedness;
- sealed history.

### 5.8 Economic limit

Even a better representation is not automatically worth constructing. If an agent can cheaply reread a short source and reconstruction is unlikely to recur, direct inspection wins.

---

## 6. When persistence earns itself

Persistence value appears to depend mainly on four properties.

### Establishment cost

How difficult is the join to reconstruct?

- one AST edge: cheap;
- cross-source semantic applicability: expensive.

### Reuse breadth

How many future tasks can use the relation?

Canonical identity tends to have broad reuse; a one-off interpretation may not.

### Compositional leverage

Can the relation combine with other relations to answer unforeseen questions?

This distinguishes ontology edges from cached prompt answers.

### Volatility

How long will the join survive before it must be reconstructed?

A stable organizational identity and a rapidly changing line-level source relation have different economics.

The strongest persistence candidates are therefore:
- cross-source identity joins;
- non-local relations;
- reusable abstractions;
- synthetic relations;
- large relational backbones whose individual edges are cheap but whose aggregate traversal value is high.

The weakest candidates are:
- representation-only projection;
- one-off semantic classifications;
- local facts already trivial to retrieve;
- answers tailored to one anticipated prompt.

A key product hypothesis follows:

> Persist high-leverage joins, not anticipated answers.

---

## 7. Materialization versus virtual access

Virtual knowledge graphs provide an important negative control.

If ontology mappings can cheaply rewrite a conceptual query back to current sources, virtual access offers freshness and avoids maintaining a materialized artifact.

Materialized construction earns itself when one or more are true:

- mappings/joins are too complex or expensive to repeatedly unfold;
- the result uses semantic interpretation that cannot be reproduced as a simple query;
- the constructed identities/relations are reused broadly;
- the artifact must have a durable historical identity;
- downstream consumers need a bounded inspectable epistemic record;
- the construction itself is part of what must be audited.

This is a more precise boundary than “graphs versus Worlds.”

---

## 8. Substitute analysis

### Raw source inspection / grep / search

Best when:
- task is local;
- evidence is small;
- relevant relation is explicit;
- no durable reuse is expected.

World adds little.

### RAG / vector retrieval

Best when:
- the core problem is locating relevant text/context;
- semantic relations do not need durable identity;
- each task can interpret retrieved context afresh.

World becomes stronger when repeated tasks depend on the same cross-source identities/joins rather than merely relevant passages.

### Database / ETL / SQL views

Best when:
- source schemas are known;
- integration is deterministic;
- joins are explicit and stable;
- ordinary lineage/constraints suffice.

A World adds value when semantic construction, unresolvedness, scoped completeness, or origin distinctions matter.

### Graph / knowledge graph

Best when:
- connected structure and traversal are the primary requirement;
- edges are trusted enough for their consumers;
- provenance/currentness/completeness do not need first-class semantics.

A World should not be preferred merely because relations exist.

### OBDA / virtual KG

Best when:
- a canonical conceptual layer is needed;
- mappings can remain declarative;
- source freshness matters more than artifact history;
- query-time integration is affordable.

A materialized World becomes attractive when the integration involves expensive or intelligent construction, broad reuse, or durable historical epistemic state.

### Provenance / lineage systems

Best when:
- the central question is how datasets/artifacts were produced;
- transformation lineage is more important than domain-semantic synthesis.

World construction is broader only if it compiles domain identities/relations in addition to production lineage.

### Operational ontology / digital twin platforms

These already provide objects, links, shared semantic models, actions, functions, security, and decision applications.

The project’s differentiation cannot be “operational ontology” alone. Its sharper design center is semantic compilation into an inspectable epistemic artifact, with stronger application guarantees composed only where needed.

---

## 9. Where the current application fits

The design-originated application is broader than design.

The clearest general shape is:

```text
SEMANTIC / EXTERNAL ARTIFACT
requirement
design concept
architectural decision
product invariant
policy
domain concept
        │
        │ semantic/mechanical binding
        ▼
PROGRAM REPRESENTATION
module
symbol
call
type
program entity
        │
        │ revision correspondence / delta
        ▼
PROGRAM CHANGE / DIFF
        │
        ▼
AFFECTED SEMANTIC KNOWLEDGE
        │
        ▼
application reasoning / governance / action
```

### 9.1 Closest established field: software traceability

Software traceability links requirements, architecture, design, code, tests, and other artifacts. Research consistently identifies maintenance, evolution, validation, rationale understanding, and change impact as important uses.

Requirements-to-code traceability is explicitly concerned with connecting requirements to implementing code artifacts.

Architecture-to-code traceability similarly supports quality control and maintenance.

### 9.2 Closest operational problem: change impact

Change-impact analysis identifies the effects of a change or what else must change. Program-dependence representations provide a graph over which code impacts can propagate.

The program spine therefore has a familiar role: it is a change-addressable structural substrate.

### 9.3 Where this application appears stronger than ordinary traceability

The application is not merely storing file-to-file trace links.

Potentially distinctive properties are:

1. **Semantic referents rather than artifact-only links.**  
   A design requirement, policy, invariant, or domain concept can be represented as a typed semantic referent/claim, not merely a document URI.

2. **A canonical program representation as the join substrate.**  
   Semantic artifacts bind to program entities; program entities already carry calls/imports/types/containment and can therefore compose with other semantic links.

3. **Change-addressability.**  
   Revision correspondence/program deltas connect the program model to a concrete diff, allowing external semantic knowledge to be bounded by actual change.

4. **Mixed construction.**  
   Trace links can be mechanical, semantic, or derived, with their origins preserved.

5. **Epistemic inspection.**  
   A link can retain grounding, construction basis, unresolvedness, and potentially currentness rather than being a bare similarity score or opaque recovered trace.

6. **Questions/governance above the trace layer.**  
   Once a diff selects an affected semantic neighborhood, applications can ask domain-specific questions, require authority, resolve uncertainty, or gate action.

This suggests the application is best understood provisionally as:

> **program-linked semantic traceability with change-bounded reasoning**

or, more compactly:

> **semantic change-impact infrastructure**

Neither should yet become a product name.

---

## 10. Why this application is wider than design

“Design” occupies the left-hand side of the pipeline; the mechanics do not require design specifically.

Other possible semantic artifacts include:

- requirements;
- architectural decisions;
- security assumptions;
- compliance rules;
- product invariants;
- operational constraints;
- domain classifications;
- ownership/responsibility models;
- test intent;
- migration assumptions.

What remains common is:

```text
semantic thing
    ↓ bind
program thing
    ↓ compare across revision
changed program thing
    ↓
semantic impact / applicability
```

The program representation is therefore not the application itself. It is the shared change-addressable substrate that lets several semantic domains attach to implementation and become actionable around a diff.

---

## 11. Important precedent and important gap

Traceability literature validates the value of these links but also identifies the central practical weakness: **creating and maintaining trace links is expensive, links decay as artifacts evolve, and industrial evidence is weaker than the conceptual promise**.

This matters directly.

The product should not claim victory merely because typed semantic links are expressive. Its application-level advantage depends on whether construction + correspondence + epistemic maintenance can reduce the traditional cost of keeping traces useful as software changes.

This is a stronger and more falsifiable product question than “can we link design to code?”

---

## 12. Use-case families supported by this research

The research supports a small number of broad families rather than an industry catalog.

### A. Compiled semantic integration

Heterogeneous evidence is compiled into canonical identities, relations, abstractions, and synthetic joins.

Use when the constructed joins have broad reuse and are more expensive to recreate than maintain.

This is the most general constructor use.

### B. Long-lived operational knowledge

A canonical model is valuable because it is repeatedly queried over time and must retain revision/grounding/epistemic distinctions.

This is where World-specific guarantees begin to matter more than a plain graph.

### C. Program-linked semantic traceability and change impact

External semantic artifacts bind to program entities; program revisions/diffs bound the affected semantic neighborhood.

This is the most concrete generalization of the existing design application.

### D. Governed operational reasoning

Questions, authority, material support, adequacy, currentness, and workflow decisions are composed above constructed knowledge.

This is a stronger application mode, not the definition of every World.

---

## 13. What is *not* established

This research does **not** establish that:

- agents will prefer a World over grep/read/search;
- persistent joins improve agent task success;
- the current schema is the right ontology for external repositories;
- all semantic integrations should be materialized;
- every application needs authority/currentness/questions/adequacy;
- the product is inherently better than knowledge graphs or operational ontology platforms;
- traceability maintenance is solved;
- the program-linked application has a final product category or name.

These require empirical product work.

---

## 14. Agent interaction hypothesis

The most defensible current hypothesis is hybrid:

```text
local narrow query
    → raw evidence/tooling often wins

join-heavy heterogeneous query
    → constructed World becomes more useful

mixed task
    → World for orientation/composition
      + raw source for exact implementation detail
```

The World should not attempt to force itself into every agent reasoning step.

The critical variable is not natural-language query complexity but **join reconstruction**:

> Does answering the task require the agent to reconstruct identities/relations that have already been compiled into the World?

This remains unproven.

---

## 15. External validation specification

A credible external experiment should use:

- a repository/corpus not designed for the system;
- independently authored tasks;
- an external outcome/oracle where possible;
- task-blind construction.

Sequence:

1. freeze repository revision;
2. build World without seeing held-out tasks;
3. freeze constructor/schema/instructions;
4. reveal held-out tasks;
5. test whether tasks reuse constructed joins;
6. only then test whether an agent actually uses those joins;
7. only after that measure end-to-end task outcomes.

Controls:

```text
A. raw sources

B. raw sources + plain constructed graph

C. raw sources + World
```

This separates:
- relational construction value;
- epistemic World value;
- agent-interface value.

Negative/local tasks should be included where raw inspection is expected to win.

---

## 16. Product implications

### 16.1 Constructor

The constructor’s useful recurring work is not arbitrary structure generation. It is:

> **compiling high-leverage joins from heterogeneous evidence into a reusable operational model.**

Those joins include representation, identity, relation, abstraction, and synthetic joins, with fusion/derivation/correspondence as secondary operations.

### 16.2 Kernel

The kernel should not dictate what ontology must be built.

Its job is to constrain the epistemic claims made by whatever is built.

The primitive floor remains approximately:

- identity and structural integrity;
- revision identity;
- source observation addressability;
- grounding/lineage;
- origin/epistemic kind;
- scoped completeness;
- explicit unresolvedness;
- sealed historical integrity.

### 16.3 Generic runtime

Construction runners, admission helpers, resolution, receipts, currentness, explorer/read surfaces, and generic question/candidate storage can remain reusable implementation machinery without defining the philosophical core.

### 16.4 Application

Anything that cannot generalize to essentially every World construction belongs on the application side, even if reusable:

- program spine;
- semantic binding;
- source/domain adapters;
- authority models;
- question generation;
- adequacy;
- governance workflows.

Reuse does not promote something into the essential core.

---

## 17. Resulting product description

The most defensible general description remains:

> **A semantic compilation runtime that turns heterogeneous evidence into inspectable, revisioned operational knowledge with explicit epistemic guarantees.**

But the research adds an important qualifier:

> Its practical construction value begins when it compiles reusable identities, relations, abstractions, or synthesized joins that are not already cheaply available from the source representation.

And for the current program-linked application:

> **Semantic knowledge is bound to a canonical program representation, which makes that knowledge addressable by concrete program change and usable for change-bounded reasoning, impact analysis, and—where applications require it—governance.**

---

## 18. Open questions to carry forward

These belong to product/application exploration rather than more foundational ontology research.

1. How often will coding agents actually use a World when direct source tools are available?
2. Which relation/join families have enough reuse to justify construction cost in practice?
3. How should an application expose a semantic→program→diff impact set to an agent?
4. Which semantic domains beyond design benefit from the same program-binding mechanics?
5. Can link maintenance/correspondence materially reduce the traditional cost of traceability?
6. Which parts of the current design application are domain-specific versus generic program-linked semantic mechanics?
7. What should the application be called and presented as once its actual workflow is clear?

---

## 19. Stop condition reached

The research question is sufficiently bounded to stop foundational constructor/use-case taxonomy work.

The main conclusions are:

1. The constructor’s meaningful recurring operation is **semantic integration through reusable joins**, not arbitrary graph construction.
2. Materialization earns itself when those joins are expensive, semantic, broadly reused, historically meaningful, or difficult to express as virtual mappings.
3. A plain graph is sufficient when relationship structure is all the consumer needs.
4. World machinery earns itself when the constructed artifact needs explicit epistemic properties rather than merely connectivity.
5. The design-originated application is best understood more broadly as **program-linked semantic traceability/change-impact infrastructure**.
6. The strongest unresolved product question is no longer “what can the constructor represent?” but **which external semantic domains and agent workflows gain enough leverage from semantic→program→change linkage to justify the construction and maintenance cost.**

The next work should return to that application.

---

## References

- Schneider, T. & Šimkus, M. *Ontologies and Data Management: A Brief Survey.* KI, 2020.
- Xiao, G., Ding, L., Cogrel, B. & Calvanese, D. *Virtual Knowledge Graphs: An Overview of Systems and Use Cases.* Data Intelligence, 2019.
- Ontop project / *Accessing scientific data through knowledge graphs with Ontop*, 2021.
- Euzenat, J. & Shvaiko, P. *Ontology Matching*, 2nd ed., Springer, 2013.
- Moslemi et al. *Heterogeneity in entity matching: A survey and experimental analysis.* Data & Knowledge Engineering, 2026.
- Zhong et al. *A Comprehensive Survey on Automatic Knowledge Graph Construction.*, 2023.
- W3C. *PROV-DM: The PROV Data Model*, 2013.
- OpenLineage specification, current v1.53 documentation, 2026.
- Microsoft Fabric. *Ontology Frequently Asked Questions* (Graph vs Ontology), 2026.
- Palantir Foundry. *Ontology Core Concepts / Ontology Overview*, current documentation, 2026.
- Wang et al. *An empirical study on the state-of-the-art methods for requirement-to-code traceability link recovery.*, 2024.
- Mucha, Kaufmann & Riehle. *A systematic literature review of pre-requirements specification traceability.*, 2024.
- Tian et al. *The impact of traceability on software maintenance and evolution: A mapping study.*, 2021.
- Javed & Zdun. *A systematic literature review of traceability approaches between software architecture and source code.*, 2014.
- Javed & Zdun. *The Supportive Effect of Traceability Links in Change Impact Analysis for Evolving Architectures*, 2015.
- Hammad, Collard & Maletic. *Automatically identifying changes that impact code-to-design traceability during evolution.*, 2011.
- Li et al. *A survey of code-based change impact analysis techniques.*, 2013.
- Joern / Code Property Graph Specification and documentation.
- IEEE/ACM and related traceability/change-impact literature cited through the studies above.
