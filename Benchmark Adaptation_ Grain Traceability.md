# Benchmark Adaptation

## Source use case

`grain-traceability-v1` is a controlled re-instantiation of the grain-elevator-to-processor traceability use case described by Ameri, Wallace, Yoder, and Riddick in *Agri-Food Supply Chain Traceability Supported by a Formal Ontology: A Grain Elevator to Processor Use Case* (2023).

The published use case concerns traceability of commodity grain moving from a primary grain elevator through storage and loadout to a downstream processor. Its semantic scope includes receiving, storage, transportation, transformation, sampling and observation, custody and ownership changes, source and destination locations, and the ability to trace material backward and forward through these events.

The present benchmark is not a reproduction of the original dataset or knowledge graph. The source data used by the published study are not available as a complete, reproducible pre-semantic public corpus. Instead, this benchmark preserves the published operational scenario and competency-question semantics while independently instantiating the scenario as controlled heterogeneous operational evidence.

## Adaptation objective

The original work evaluated whether a deliberately engineered formal ontology could represent and support queries over supply-chain traceability data.

This adaptation asks a different question:

> Given an operational purpose and ordinary heterogeneous evidence, can a capable coding agent construct a reusable semantic representation sufficient for the traceability problem without being supplied the domain ontology, semantic mappings, competency questions, or expected schema?

The adaptation therefore changes the semantic-construction condition while retaining the underlying traceability problem as an external reference.

## Elements retained from the published use case

The benchmark preserves the following aspects of the published problem:

1. the grain elevator-to-processor operational setting;
2. material receipt, storage, loadout, transport, and downstream receipt;
3. source and destination locations;
4. material/container participation in events;
5. sampling and observation;
6. custody and ownership;
7. temporal traceability;
8. upstream and downstream material provenance;
9. the semantic intent of published competency questions concerning transfer events, containers, historical location, source ownership, source location, storage/loadout bins, and custody.

Published competency questions are retained only on the evaluator side and are never shown to the Ontology Author construction host.

## Elements not reproduced

The adaptation does not reproduce:

- the original simulated dataset;
- the original RDF knowledge graph;
- the original source-to-ontology mappings;
- prescribed Critical Tracking Event or Key Data Element schemas;
- the NIST application ontology as a construction input;
- BFO/IOF/SCRO terminology as host instructions;
- original SPARQL or RDFox query implementations;
- ontology-specific derivation rules.

These artifacts either are unavailable as a reproducible pre-semantic corpus or would disclose the semantic representation that the experiment is intended to ask the construction system to discover.

They may be retained separately as publication context or reference-comparator material.

## Controlled evidence re-instantiation

A new operational evidence instance is generated specifically for this benchmark.

An evaluator-only canonical ledger first defines the intended underlying events, material identities, locations, custody and ownership intervals, observations, transformations, and traceability relationships.

Multiple host-visible source files are then projected independently from this canonical state. These files represent separate operational systems and deliberately differ in schema, terminology, identifiers, and record grain.

The canonical ledger is never accessible to the construction host or downstream World consumers.

This procedure provides exact experimental ground truth while preventing the host-visible corpus from constituting a pre-integrated semantic representation.

The corpus is designed for semantic density rather than scale. Each record participates in an auditable experimental case; filler transactions are avoided.

## Controlled departures from the published scenario

The adaptation introduces several phenomena that are not strongly evaluated by the original competency questions:

- cross-source identifier reconciliation;
- ambiguous but plausible identity correspondences;
- missing event links;
- incomplete traceability;
- distinction between custody and ownership;
- multiple-source material provenance;
- temporal ordering dependencies;
- explicit unresolved cases;
- completeness-sensitive negative conclusions.

These extensions test properties specific to the Ontology Author hypothesis and are reported separately from results on competency questions derived from the published use case.

They must not be presented as original NIST benchmark requirements.

## Host-visible purpose

The Ontology Author construction host receives only the operational evidence, ordinary source documentation, the Ontology Author capability, and the following purpose:

> Build a reusable World that lets us trace grain through receiving, storage, processing, and outbound shipment, including determining where material came from, what happened to it, and where it went when the available evidence establishes those links. Preserve uncertainty where material identity or event linkage cannot be established.

The host receives no ontology, required relation vocabulary, mappings, competency questions, gold answers, reference queries, or evaluator artifacts.

## Competency-question adaptation

Evaluation contains two separately reported question families.

### Published-use-case questions

Questions in this family preserve the semantic intent of competency questions reported in the source traceability work.

Each adapted question records:

- its source publication;
- the source question text;
- the benchmark-specific instantiated question;
- the semantic capability being tested;
- the expected consequence;
- the host-visible evidence supporting that consequence.

Changes required only to substitute benchmark-specific identifiers, dates, facilities, loads, samples, or containers are treated as instantiations rather than new questions.

Any substantive semantic change creates a new benchmark question and is not attributed to the source publication.

### Extension questions

A separate hidden question set evaluates properties not strongly covered by the source work, including incomplete provenance, ambiguous identity, unresolvedness, novel semantic recombination, and completeness-sensitive conclusions.

These questions are authored for this benchmark and are reported as such.

## Conventional reference condition

The NIST traceability ontology work and the IOF Supply Chain Reference Ontology are used as a conventional semantic-engineering reference, not as a target schema.

A separate reference representation may be constructed from the frozen evidence using those resources as guidance.

The reference condition records the deliberate human semantic specification required to produce a reusable representation, including:

- ontology concepts and properties;
- axioms;
- source mappings;
- identity mappings;
- transformation logic;
- derivation rules;
- query semantics.

Ontology Author is not evaluated by structural similarity to this representation.

Representations are compared by their consequences for the precommitted evaluation tasks.

## Experimental conditions

Three consumption conditions are defined.

### RAW

A fresh consumer receives the operational purpose, native evidence, and evaluation questions.

### REFERENCE

A fresh consumer receives the conventionally engineered semantic representation, purpose, and evaluation questions.

### ONTOLOGY AUTHOR

A construction host first receives only the operational purpose, native evidence, and Ontology Author capability.

After construction is frozen, a fresh downstream consumer receives only the resulting World, the purpose, and evaluation questions. Native evidence and construction artifacts are unavailable to that consumer.

This separates semantic construction from downstream semantic reuse.

## Precommitment and freezing

Before the first Ontology Author construction run, the following are frozen:

- canonical truth ledger;
- host-visible source corpus;
- operational purpose;
- published-use-case question set;
- extension question set;
- gold semantic consequences;
- expected unresolved cases;
- completeness assumptions;
- scoring criteria;
- reference semantic representation or its construction protocol;
- corpus hashes;
- visibility boundaries.

The host-visible evidence is not modified in response to construction behavior.

Questions and scoring criteria are not revised after observing an Ontology Author World except to correct a demonstrable benchmark defect, which must be versioned and reported.

## Evaluation principle

Evaluation is representation-independent.

A World is not required to reproduce the classes, properties, ontology hierarchy, RDF structure, or naming conventions of the conventional reference ontology.

It is evaluated on whether:

1. committed semantic propositions are justified by host-visible evidence;
2. distinctions required by the declared purpose are preserved;
3. precommitted traceability consequences can be computed;
4. unsupported relationships remain unresolved;
5. negative conclusions are made only where evidence completeness licenses them;
6. important conclusions retain evidence grounding;
7. a fresh consumer can answer novel questions without reconstructing native-source semantics or accessing the source corpus.

## Primary comparison

The central comparison is not ontology formalism versus relational storage.

It is the semantic-engineering pathway.

Conventional condition:

```text
use case
→ competency questions
→ ontology engineering
→ mappings and transformations
→ semantic representation
→ downstream computation
```

Ontology Author condition:

```text
operational purpose + ordinary evidence
→ capable construction agent
→ World
→ downstream computation
```

The primary process metric is the amount and character of deliberate human semantic specification required before the first correct reusable semantic query.

Schema size and implementation lines of code may be reported descriptively but are not substitutes for this measure.

## Scope of claims

Results from this benchmark may support claims about purpose-driven semantic construction and reuse on the adapted grain-traceability problem.

They do not establish equivalence to the complete NIST ontology, IOF Supply Chain Reference Ontology, GS1 EPCIS, or supply-chain ontology engineering generally.

Success on benchmark-specific extensions must be distinguished from performance on competency questions derived from the published use case.