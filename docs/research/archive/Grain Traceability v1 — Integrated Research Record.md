> Historical research record — not current product or agent instructions.
> See the [Core v1 baseline](../../CORE_PRODUCT_V1_BASELINE.md).

# Grain Traceability v1: Integrated Research Record

**Status:** Frozen experimental record  
**Date:** 9 September 2026  
**Product:** Ontology Author 0.1.0  
**Benchmark:** `grain-traceability-v1`  
**Frozen benchmark/product commit:** `17e1314f10d8b491b4462f821876a0a42642f1f8`

## Abstract

`grain-traceability-v1` tested whether capable coding agents, given only an operational purpose, ordinary heterogeneous supply-chain evidence, and Ontology Author, could independently construct useful grounded semantic Worlds without receiving a prescribed ontology, source mappings, competency questions, evaluator gold, or reference representation.

The benchmark is a controlled re-instantiation of the published NIST grain-elevator-to-processor traceability use case. It preserves the operational scenario and competency-question lineage while replacing the unavailable or ontology-shaped original data pipeline with a frozen heterogeneous pre-semantic evidence corpus. The experiment therefore does **not** claim to reproduce the original NIST experiment or use a recovered “NIST dataset.” The NIST work establishes the traceability problem and conventional semantic-engineering reference boundary; its published methodology was substantially ontology-, mapping-, and competency-question-driven. 
Two independent construction agents produced materially different Worlds from the same purpose and evidence. Both converged autonomously, preserved nearly all hidden benchmark consequences, made no incorrect semantic commitments or unsupported closures, maintained the deliberately ambiguous cases as unresolved, and exposed auditable grounding. Their direct hidden evaluations were identical: 8/10 standard-backed questions fully correct with 2 partial, and 9/10 novel questions fully correct with 1 partial.

Subsequent analysis showed that the two apparent shared omissions were not equivalent. Omission of `LO-3 / Spout 3` was a real finer-grain coverage gap but was not necessary for the short declared operational purpose. The hidden 15,000 kg / 11,000 kg source-allocation requirement was not established by the host-visible evidence and should not have been committed; the constructors’ conservative treatment was epistemically appropriate. The frozen benchmark verdict therefore remains `PARTIALLY_SUPPORTED`, while the post-audit purpose-only interpretation is `SUPPORTED`.

Fresh downstream consumers showed that both Worlds preserved the supported consequence frontier reached by RAW consumers while requiring zero native-source reads. RAW consumers repeatedly reconstructed cross-source identity, shipment, custody, ownership, sample-scope, and completeness semantics; World consumers instead inspected and queried compiled semantic state. An engineered REFERENCE arm behaved similarly downstream, but its nominal advantage on the disputed quantity split came from evaluator canonical truth rather than evidence-established semantics.

This supports **semantic amortization**—source interpretation and reconciliation can be moved into persistent semantic state—but not a general accuracy, token-efficiency, or monetary-efficiency claim. In the frozen token experiment, fresh World consumers used substantially more reported tokens than RAW consumers, and neither World reached a token break-even point. A later deterministic World synopsis reduced consumer tokens without changing semantic outcomes, but did not consistently reduce observable orientation actions. Durable task-specific computations generalized partially and reduced repeated ad hoc semantic-query authoring, but token benefits were representation-dependent.

Across all phases:

> **KERNEL PRESSURE: NONE**

No observed failure demonstrated that the Ontology Author semantic kernel could not represent a purpose-relevant, evidence-supported consequence.

---

# 1. Research questions

The experiment developed in stages, with each stage testing a progressively stronger claim.

### Semantic construction

Can a capable agent transform ordinary heterogeneous supply-chain evidence into a grounded, purpose-fit World without being supplied an ontology, mapping specification, or hidden competency questions?

### Representation independence

Can independent agents choose materially different conceptualizations while preserving the same required semantic consequences?

### Epistemic discipline

Can the Worlds preserve unsupported meaning as unresolved rather than collapsing ambiguity into false semantic commitments?

### Downstream reuse

Can fresh consumers answer purpose-relevant questions using only a sealed World, without reopening or reinterpreting the native evidence?

### Conventional-reference proximity

Does downstream use of an organically agent-constructed World resemble downstream use of a deliberately engineered semantic representation?

### Semantic amortization

Does compilation eliminate repeated source-specific semantic reconstruction across fresh consumers?

### Token amortization

Does that semantic reuse also reduce model-token consumption after accounting for construction?

### Orientation compression

Can deterministic structural context reduce the repeated cost of discovering an unfamiliar agent-authored World?

### Durable computation

Can repeated semantic computations over a World themselves become persistent parameterized programs that later agents reuse?

These questions were kept separate. Success on semantic reuse was not treated as evidence of token savings, and semantic correctness was not reduced to structural similarity with a reference ontology.

---

# 2. Benchmark lineage and adaptation

## 2.1 Published use case

The benchmark derives its problem setting from published NIST agri-food supply-chain traceability work.

The relevant scenario runs broadly through:

```text
growers
   ↓
grain elevator receiving
   ↓
storage / bins
   ↓
loadout
   ↓
transport
   ↓
processor / feed manufacturer
```

The published scenario covers receiving, storage, loadout, shipment, inspection, ownership changes, custody changes, transformation, source and destination locations, transport/container relationships, and provenance tracing.

Published competency-question themes include:

- transfer-event containers;
- events related to a load;
- containers contacted by a load;
- location of a load at a time;
- source ownership of a sampled load;
- source location in a transport event;
- originating and loadout bins;
- custody holders and custody intervals.

The published approach was conventional ontology engineering:

```text
use case / requirements
        ↓
competency questions
        ↓
domain terminology
        ↓
BFO / IOF / SCRO-aligned ontology
        ↓
classes / properties / axioms
        ↓
source mappings
        ↓
RDF
        ↓
SPARQL / rules / reasoning
```

Concrete semantic specification included ontology classes and properties, mappings, URI rules, transformation code, query semantics, and derivation rules.

## 2.2 Why a controlled re-instantiation was necessary

The publicly recoverable NIST material did not provide a clean reproducible pre-semantic benchmark corpus suitable for the intended experiment. The 2023 data were generated by simulation and the original Excel/JSON instance artifacts were not recovered; the earlier real `.xlsx` dataset was likewise unavailable from the recovered public material.

The benchmark was therefore defined as:

> **A controlled re-instantiation of the published NIST grain-elevator-to-processor ontology use case, preserving its operational scenario and competency-question semantics while replacing its unavailable or ontology-shaped data pipeline with a new heterogeneous pre-semantic evidence corpus.**

The standardized object is the **problem and competency boundary**, not the unavailable raw corpus or the reference ontology.

---

# 3. Frozen benchmark

## 3.1 Host-visible purpose

The constructor received the following operational purpose:

> Build a reusable World that lets us trace grain through receiving, storage, processing, and outbound shipment, including determining where material came from, what happened to it, and where it went when the available evidence establishes those links. Preserve uncertainty where material identity or event linkage cannot be established.

The purpose does not prescribe classes, relation names, mappings, standards, query forms, evaluator categories, or a canonical ontology.

## 3.2 Evidence corpus

The frozen host-visible corpus contained ordinary documentation plus eight heterogeneous operational evidence sources representing:

- 5 elevator receipts;
- 10 bin movements;
- 4 loadout records;
- 4 carrier manifests;
- 3 processor receipts;
- 2 processor runs;
- 4 inspection results;
- 7 ownership/custody records.

The evidence represented:

- receiving;
- storage;
- blending;
- loadout;
- transport;
- processor receipt;
- inspection;
- sampling;
- transformation;
- ownership;
- custody;
- temporal ordering;
- locations;
- material provenance;
- incomplete linkage.

Deliberately difficult cases included:

- `PGE-OUT-5003`: missing processor receipt and source allocation;
- `PGE-OUT-5004`: unresolved allocation between inbound sources;
- `MCR-118`: unresolved Meadow Creek ownership identity;
- `N3 / EF-18?`: unsupported possible identity match;
- `HFM-E`: absence not licensed as a negative because completeness was not established for that site.

There was deliberately no universal join key.

## 3.3 Evaluator boundary

Evaluator-only material contained:

- 31 canonical events;
- 10 standard-backed questions;
- 10 novel questions;
- gold consequences;
- unresolvedness rules;
- scoring rules.

Reference-only material contained the deliberately engineered semantic comparator and standards/context material.

The Ontology Author constructors had access to neither evaluator-only nor reference-only artifacts.

The core visibility boundary followed the precommitted design:

```text
ONTOLOGY AUTHOR CONSTRUCTION
ordinary evidence
+ operational purpose
+ ordinary Ontology Author capability

not visible:
reference ontology
competency questions
hidden questions
gold
reference mappings
```

The downstream OA consumer later received only:

```text
sealed World
+ purpose
+ downstream questions
```

with native source evidence absent. This consequence-based rather than schema-based comparison was precommitted before construction.

---

# 4. Independent World construction

## 4.1 Environment

Both independent construction runs used:

```text
Codex CLI 0.153.4
model: gpt-6-astra
reasoning: medium
isolated bwrap workspaces
Ontology Author: 0.1.0
```

The construction instruction was identical between runs.

Each host received only the host-visible workspace and normal Ontology Author capability.

No clarification was requested.

## 4.2 Construction outcomes

| Property | OA-1 | OA-2 |
|---|---:|---:|
| Duration | 341 s | 327 s |
| Relations | 19 | 17 |
| Referents | 85 | 66 |
| Assertions | 293 | 185 |
| Derived relations | 1 | 1 |
| Explicit unresolved states | 13 | 13 |
| Rebuilds | 10 | 12 |
| Recovered failed intermediate rebuilds | 2 | 3 |
| Human semantic intervention | 0 | 0 |

Frozen World hashes:

```text
OA-1
d39faa9ed9e40b03fea7cd329033ae7756664f4dae533ff83a6c7c725006b116

OA-2
1eebe0f15eacb711080db8826d7bc2bad39da3ff28658afcfa5fb5f30da7e9d3
```

Both agents accessed all ten host-visible files and independently created construction code, diagnostics, semantic metadata, documentation, and sealed World bundles.

Constructor-authored tests exercised, among other things:

- source-revision grounding;
- SQLite integrity;
- supported and withheld provenance;
- shared-bin ambiguity;
- intended destination versus confirmed receipt;
- inspection scope;
- ownership versus custody;
- unresolved identity;
- bundle portability.

Intermediate rebuild failure was treated as ordinary construction convergence, not experimental failure:

```text
inspect
→ construct
→ rebuild/test
→ detect failure
→ revise
→ converge
```

The retained telemetry confirms autonomous convergence, zero human semantic intervention, and successful sealed Worlds.

---

# 5. Independent conceptualizations

The two agents did not converge on one ontology.

OA-1 was primarily **event-first**, using relations centered on explicit events, event participation, movement, receiving, dispatch, departure, material flow, ownership, inspection scope, and candidate identity.

OA-2 was primarily **lifecycle/stage-first**, using relations such as intake, storage, movement, loadout, departure, manifest linkage, acceptance, flow, processing, party records, and sampling.

OA-2 also used more explicitly scoped identifier namespaces.

Despite these differences, both produced the same scored semantic consequence profile, used recursive trace derivation, and represented the same major uncertainty boundaries. The evaluator explicitly found no canonical schema preference.

This provides evidence for:

> **consequence convergence without schema convergence**

rather than evidence for discovery of one canonical ontology.

---

# 6. Direct hidden semantic evaluation

No World was modified, rebuilt, or repaired during evaluation. Hashes, manifests, SQLite integrity, sidecars, derivation state, and read-only status all passed.

## 6.1 Frozen result

| Metric | OA-1 | OA-2 |
|---|---:|---:|
| Standard-backed fully correct | 8/10 | 8/10 |
| Standard-backed partial | 2/10 | 2/10 |
| Standard-backed incorrect | 0 | 0 |
| Novel fully correct | 9/10 | 9/10 |
| Novel partial | 1/10 | 1/10 |
| Novel incorrect | 0 | 0 |
| Unsupported closures | 0 | 0 |
| Incorrect commitments | 0 | 0 |
| Grounding defects | 0 | 0 |
| Completeness defects | 0 | 0 |
| Frozen purpose verdict | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED |



The two Worlds missed exactly the same apparent consequences.

### `LO-3 / Spout 3`

The loadout event, source bin, truck, quantity, and related traceability semantics were represented, but the individual loadout point `Spout 3` was not materialized.

This was a real source-supported finer-grain omission.

### OUT-5002 source quantities

Both Worlds represented WB-390 and EF-18 as contributors to the blended shipment but did not assert a 15,000 kg / 11,000 kg individual allocation.

The initial frozen evaluator treated this as missing purpose-relevant meaning.

Later evidence audit showed that the host-visible record establishes the contributors and combined quantity while explicitly withholding the individual allocation. The individual split came from evaluator canonical truth rather than justified host evidence.

Thus the conservative World behavior was appropriate.

---

# 7. Unresolvedness and false closure

Both Worlds correctly preserved every deliberately dangerous uncertainty boundary tested in the direct evaluation.

They did not:

- invent an OUT-5003 processor receipt;
- invent OUT-5003 source allocation;
- force a single source for OUT-5004;
- select an MCR-118 account identity;
- turn `N3 / EF-18?` into an established match;
- infer a negative HFM-E receipt conclusion from HFM-N completeness.

No incorrect closure and no incorrectly unresolved benchmark case was found.

This is important because false committed meaning is especially damaging in a reusable semantic artifact: downstream consumers may treat a committed World proposition as established state rather than reopening it for epistemic reconsideration.

---

# 8. Grounding, derivation, and completeness

Every committed gold-critical positive consequence in both Worlds had auditable source grounding.

Each World independently created:

```text
8 direct material-flow edges
        ↓
recursive trace derivation
        ↓
16 derived trace outputs
```

Neither derivation collapsed unresolved co-storage or incomplete source allocation into false provenance.

The two Worlds made different but valid completeness choices:

- OA-1 declared trace `INCOMPLETE`;
- OA-2 declared recursive trace closure `COMPLETE` over its finite admitted graph while explicitly disclaiming complete real-world lineage.

The evaluator accepted both because the semantic universe was explicit and neither completeness declaration licensed an unsound negative conclusion.

OA-2's formulation nevertheless has greater interpretation risk if a downstream consumer ignores the declared universe.

---

# 9. Benchmark coverage versus purpose sufficiency

Post-evaluation diagnosis materially changed how the partial results should be interpreted, without modifying the frozen evaluation artifact.

The two omissions have different status:

### Spout 3

`Spout 3` is source-supported and legitimately tested by the standard-backed competency-question lineage.

However, the declared operational purpose can still be performed at bin/truck/loadout-event grain.

It is therefore:

```text
real benchmark coverage gap
but
not strictly required for the short declared purpose
```

### 15,000 / 11,000 kg allocation

The individual split is:

```text
not established by host-visible evidence
not required by the declared purpose
unsafe to commit
```

Both constructors saw the combined movement and preserved allocation uncertainty.

Therefore:

```text
FROZEN BENCHMARK VERDICT:
PARTIALLY_SUPPORTED

POST-AUDIT PURPOSE-ONLY INTERPRETATION:
SUPPORTED
```



This produces an important methodological distinction:

> **Benchmark competency coverage and purpose sufficiency are related but not identical constructs.**

---

# 10. Fresh consumer experiment

Fresh downstream consumers were then evaluated under four conditions:

```text
RAW
REFERENCE
OA-1
OA-2
```

RAW consumers received native evidence.

REFERENCE consumers received only the engineered semantic representation.

OA consumers received only one sealed World.

All received the same downstream question set appropriate to the condition and purpose.

## 10.1 Results

Across two replicates per condition:

| Condition | Correct | Partial | Incorrect | Unsupported closure | Native-source reads |
|---|---:|---:|---:|---:|---:|
| RAW | 18/20 | 2 | 0 | 0 | 2/2 runs |
| REFERENCE | 20/20* | 0 | 0 | 0 | 0/2 runs |
| OA-1 | 18/20 | 2 | 0 | 0 | 0/2 runs |
| OA-2 | 18/20 | 2 | 0 | 0 | 0/2 runs |

`*` The REFERENCE result includes the unsupported evaluator-side 15,000/11,000 kg allocation.

The strongest defensible correctness conclusion is therefore not `World > RAW`.

It is:

> **On supported consequences, both organically constructed Worlds preserved the same downstream consequence frontier as RAW without false closure and without native-source access.**

The engineered reference matched frozen gold more closely only because one hidden consequence had been materialized from evaluator truth not established by the evidence. 

---

# 11. Source independence and work character

The strongest consumer finding concerns the type of work performed.

RAW consumers repeatedly reconstructed:

- receipt-ticket to bin-movement identities;
- carrier bill to processor receipt correspondence;
- departure versus actual receipt;
- ownership versus custody;
- combined-sample material scope;
- site-scoped completeness.

World and Reference consumers did not reopen the operational sources to reconstruct these semantics. They inspected already compiled semantic representations.

The observed shift was:

```text
RAW
source discovery
+ parsing
+ cross-source reconciliation
+ semantic reconstruction
+ task reasoning

WORLD
semantic schema discovery
+ semantic query / derivation
+ task reasoning

REFERENCE
semantic schema discovery
+ semantic query / derivation
+ task reasoning
```



This is the primary evidence for **semantic amortization**.

Meaning established during semantic construction remained available to fresh consumers as computational state.

---

# 12. Relationship to the engineered reference

Grain was the first clean experiment in this research sequence with an explicit engineered semantic reference consumer condition.

On supported traceability consequences and uncertainty handling:

```text
REFERENCE consumption
≈
organic World consumption
```

in work character.

Both operated source-free over semantic state.

The reference's nominal frozen-gold advantage is not a clean semantic superiority result because its extra quantity allocation was inherited from evaluator canonical truth.

Moreover, the reference representation had already required substantial semantic engineering before downstream consumption:

- concepts and relations;
- identity decisions;
- mappings;
- transformations;
- derivations;
- uncertainty semantics;
- query semantics;
- evaluator-side materialization.

The important comparison is therefore not RDF versus SQLite or one schema versus another.

It is:

```text
CONVENTIONAL
human semantic specification
→ ontology/mappings/transforms
→ semantic representation
→ downstream semantic querying

ONTOLOGY AUTHOR
operational purpose + evidence
→ capable construction agent
→ World
→ downstream semantic querying
```

Grain provides evidence of **downstream behavioral proximity** between the two routes on supported consequences.

---

# 13. Token analysis

Semantic amortization did not imply token amortization.

The Codex usage records were judged trustworthy for descriptive token accounting, though not as provider billing receipts.

Mean fresh-consumer reported totals were approximately:

```text
RAW          66,400
REFERENCE   139,083
OA-2        164,833
OA-1        194,497
```

World consumers used more tokens than RAW even before adding one-time construction cost.

Construction itself consumed:

```text
OA-1   456,456 reported tokens
OA-2   568,110 reported tokens
```

The consumer slopes were already unfavorable:

```text
RAW(n)  = 66,399.5 n

OA-1(n) = 456,456 + 194,496.5 n
OA-2(n) = 568,110 + 164,833 n
```

Neither World has a non-negative token break-even in this experiment.

The non-cached-input sensitivity analysis had the same direction.

Therefore:

```text
TOKEN AMORTIZATION: NOT_SUPPORTED
SEMANTIC AMORTIZATION: SUPPORTED
```

This does not contradict semantic reuse.

It shows that a small raw corpus can be cheap for a frontier agent to interpret directly, while a fresh World consumer pays a substantial cost to discover and navigate an unfamiliar generated semantic interface.

The result therefore distinguishes:

> **amortization of semantic interpretation**

from:

> **amortization of model tokens**

They are separate empirical properties.

---

# 14. Deterministic World-context experiment

The token result motivated a narrow follow-up question:

> Can deterministic lean orientation context reduce the repeated cost of learning an unfamiliar World?

A non-LLM renderer generated a compact `world-context.md` directly from sealed World structure.

The artifacts were small:

| World | Context bytes | Words |
|---|---:|---:|
| OA-1 | 4,118 | 488 |
| OA-2 | 3,773 | 464 |

They contained only stored purpose/interface metadata, relation structure, derivation/completeness/unresolvedness/grounding mechanisms, and access filenames. No sample tuples, evaluator terms, benchmark answers, or source facts were included.

Twelve fresh consumers tested DISCOVERY versus SYNOPSIS.

Semantic behavior was unchanged:

```text
9/10 correct
1/10 partial
0 unsupported closures
```

for every condition.

Mean input tokens changed:

```text
OA-1
192,038 → 189,328
≈ 1.4% reduction

OA-2
167,479 → 141,240
≈ 15.7% reduction
```

The effect was therefore descriptive but representation-dependent.

Observable orientation-action count did not improve consistently, and the first task-relevant semantic query remained action 6 in every run.

Frozen judgments:

```text
SEMANTIC NON-INFERIORITY: SUPPORTED
ORIENTATION TOKEN REDUCTION: SUPPORTED
ORIENTATION ACTION REDUCTION: NOT_SUPPORTED
```

The result supports compact deterministic orientation context as useful, but does not show that schema discovery has been eliminated.

---

# 15. Durable semantic computation experiment

A further experiment tested whether repeated application-level semantic computations could themselves become durable.

The question was:

> Can one agent author parameterized semantic programs over a World, freeze them, and allow later agents to reuse those programs on other task instances rather than repeatedly reconstructing World-specific query logic?

This experiment used:

```text
Cursor CLI 3.19.13
cursor-grok-4.6-medium
medium reasoning
```

The model change means its token numbers must not be causally compared with the earlier GPT-6-Astra runs. The matched comparison is Grok SYNOPSIS versus Grok DURABLE within the new experiment. 

## 15.1 Direct computation generalization

The independently authored bundles generalized imperfectly but usefully:

```text
OA-G1
6 held-out cases directly supported
1 supported compositionally
3 not covered

OA-G2
5 directly supported
2 compositionally supported
3 not covered
```

There were no incorrect deterministic outputs or unsupported closures.

The durable programs therefore generalized **computation shape**, but not the entire application consequence surface.

## 15.2 Consumer behavior

Every durable consumer used the computation bundle.

No durable consumer was `PURE_DURABLE`; all were:

```text
DURABLE_PLUS_WORLD
```

meaning the reusable computations reduced but did not replace direct World interaction.

The strongest process result was reduced ad hoc semantic-query construction:

```text
OA-G1
5.00 → 2.00 mean ad hoc semantic queries

OA-G2
3.67 → 2.67
```



This supports the idea that repeated semantic computation can be persisted as ordinary programs over a read-only World.

## 15.3 Token result

Token savings were not representation-independent.

OA-G1 durable consumption became more expensive.

OA-G2 became slightly cheaper, producing a modeled application-level break-even at approximately 64.9 repeated uses.

Frozen judgments were:

```text
DURABLE COMPUTATION GENERALIZATION:
PARTIALLY_SUPPORTED

SEMANTIC NON-INFERIORITY:
INDETERMINATE

CONSUMER TOKEN REDUCTION:
PARTIALLY_SUPPORTED

AD HOC QUERY REDUCTION:
SUPPORTED

APPLICATION-LEVEL TOKEN AMORTIZATION:
PARTIALLY_SUPPORTED

REPRESENTATION-INDEPENDENT REUSE:
PARTIALLY_SUPPORTED

KERNEL PRESSURE:
NONE
```



## 15.4 Important limitations

The durable-computation evaluation contained additional scope-sensitive gold obligations involving individual custody and sample linkage. These frozen judgments were disclosed rather than repaired.

The parameter holdout was also not fully blind to identifiers: authoring agents could inspect their complete Worlds and OA-G2's author-only tests included held-out-looking identifiers. The held-out task file and gold remained physically hidden, no answer maps or held-out literals appeared in the consumer-visible bundles, and author-only tests were excluded. The result therefore supports computation-shape reuse, not strict parameter-value blindness.

---

# 16. Integrated findings

## 16.1 Capable agents can organically construct useful supply-chain ontologies from ordinary evidence

Two independent agents received no prescribed ontology or hidden evaluator structure.

Both produced non-degenerate, grounded semantic Worlds.

Both independently discovered the central traceability abstractions required for:

- receiving;
- storage;
- movement;
- shipment;
- transportation;
- processing;
- provenance;
- temporal ownership;
- temporal custody;
- sampling;
- inspection;
- explicit unresolvedness;
- derived multi-hop traceability.

No human semantic intervention was needed.

## 16.2 Correctness did not require schema convergence

OA-1 and OA-2 differed materially in:

- relation structure;
- conceptual grain;
- event representation;
- identity strategy;
- naming;
- unresolvedness encoding.

Yet they converged on essentially the same semantic consequence frontier.

This supports:

> **The target is not one canonical ontology. The target is preservation of purpose-relevant semantic consequences.**

## 16.3 Conservative incompleteness was safer than evaluator over-closure

Neither World made a false semantic commitment.

The most important disputed omission—the per-source quantity split—ultimately exposed an evaluator defect rather than a constructor failure.

The constructors' refusal to commit unsupported allocation was correct.

This reinforces the product principle:

> **Missing positive assertion is preferable to unsupported durable meaning.**

## 16.4 Purpose sufficiency and benchmark coverage must remain distinct

The Worlds missed a legitimate standard-backed finer-grain field: `Spout 3`.

That does not imply that the World failed the operational job stated in `PURPOSE.md`.

A benchmark may intentionally probe beyond the shortest operational purpose.

Reporting should therefore distinguish:

```text
coverage against evaluator obligations
```

from:

```text
sufficiency for declared purpose
```

rather than silently treating them as one construct.

## 16.5 Semantic compilation changes downstream work

RAW and World consumers reached the same supported consequence frontier in the main consumer comparison.

The important difference was how.

RAW repeatedly reconstructed source meaning.

World consumers queried semantic state in which those source-specific interpretations had already been compiled.

This is the strongest demonstrated form of:

> **Compile meaning once → compute over it many times.**

## 16.6 Semantic amortization does not imply token amortization

The grain corpus is compact enough that direct RAW interpretation by a capable model is cheap.

Fresh World consumers instead pay a substantial orientation and semantic-interface-discovery cost.

Thus:

```text
semantic reconstruction ↓
does not necessarily imply
token consumption ↓
```

The product should not make universal token-efficiency claims from semantic persistence alone.

## 16.7 Deterministic context can reduce World-orientation cost

A sub-5 KB deterministic synopsis reduced mean consumer input in both World families without changing semantic outcomes.

The magnitude varied substantially by representation and did not reduce orientation actions in aggregate.

This is promising interface evidence, not a reason to enlarge the semantic kernel.

## 16.8 Repeated semantic computation can itself become durable

Agent-authored parameterized programs generalized beyond their authoring examples and reduced repeated ad hoc semantic-query authoring.

They did not eliminate World interaction, and token benefits were inconsistent.

The likely stable architecture is therefore not:

```text
World
→ closed fixed application API
```

but:

```text
World
→ durable computations for repeated dependencies
+
free World access for new questions
```

---

# 17. What the experiment does not establish

The grain sequence does **not** establish:

### Universal World accuracy superiority

Prior research and grain itself support conditional semantic adequacy, not `World > RAW` for every task.

### Universal token savings

The primary grain token experiment directly rejects that claim in this setting.

### Monetary ROI

No provider billing model or economic deployment study was performed.

### Canonical schema discovery

The two Worlds differ structurally while preserving similar consequences.

### Equivalence to NIST, IOF, GS1, or SCRO

Those are standards/reference contexts, not target schemas for Ontology Author.

### Exhaustive representation of source evidence

The objective is purpose-fit semantics, not full source replication.

### Strictly blind durable-program generalization

The durable-program holdout protected questions and gold, but authoring agents could inspect the full World identifier space.

### A universal need to query the World

Simple literal questions may be better served by direct source access, grep, ordinary SQL, or existing application code.

The World is useful where compiled meaning prevents repeated semantic reconstruction, not as a mandatory route for every information request.

---

# 18. Kernel-pressure assessment

Across:

- two free construction runs;
- direct semantic auditing;
- explicit unresolvedness;
- scoped completeness;
- derived provenance;
- RAW/REFERENCE/World consumers;
- deterministic context projection;
- durable parameterized application programs;

no result demonstrated a missing semantic primitive in the Ontology Author kernel.

Observed problems were attributable to:

- constructor abstraction choice;
- evaluator over-specification;
- consumer interface/orientation cost;
- computation-authoring coverage;
- representation-dependent efficiency;
- experimental holdout design.

The kernel successfully represented:

- referents;
- typed n-ary relations;
- WORLD/PURPOSE scope;
- asserted and derived state;
- evidence grounding;
- construction origin;
- temporal semantics;
- ownership/custody distinctions;
- explicit unresolvedness;
- scoped completeness;
- deterministic derivations.

Therefore:

```text
KERNEL PRESSURE: NONE
```

The direct evaluation reached the same conclusion.

---

# 19. Strongest supported claims

The grain sequence supports the following claims.

### Construction

> Given an operational purpose and heterogeneous ordinary evidence, capable coding agents can independently construct grounded, non-canonical semantic Worlds without being supplied a reference ontology, source mappings, or evaluator competency questions.

### Consequence convergence

> Independent agents can choose materially different ontology structures while preserving substantially the same purpose-relevant semantic consequences.

### Epistemic discipline

> The Worlds can preserve ambiguous identity, incomplete traceability, scoped completeness, and other unsupported meaning without converting it into false durable commitments.

### Reuse

> Fresh consumers can compute over a sealed World without native evidence and preserve the supported downstream consequence frontier reached by consumers reasoning directly over the source corpus.

### Semantic amortization

> Semantic compilation can move source interpretation and reconciliation into persistent computational state so that later consumers do not need to reconstruct those native-source semantics.

This is the strongest cumulative formulation in the frozen consumer analysis.

### Reference proximity

> On supported traceability consequences, downstream use of organically constructed Worlds can resemble downstream use of a deliberately engineered semantic representation, without requiring the constructor to receive the reference semantic specification.

### Interface compression

> A compact deterministic projection of World structure can reduce consumer context use without altering semantic state or answer quality, although the effect is representation-dependent.

### Progressive computation persistence

> Agents can author reusable parameterized semantic programs over Worlds that later consumers invoke on other cases, reducing repeated ad hoc semantic-query construction, although generalization and efficiency remain incomplete.

---

# 20. Final conclusion

The grain experiment began as a test of a simple product claim:

```text
purpose + messy supply-chain evidence
              ↓
       capable agent
              ↓
            World
```

The results support a richer but still disciplined interpretation:

```text
ordinary heterogeneous evidence
          +
operational purpose
          ↓
free agent semantic construction
          ↓
grounded purpose-fit World
          ↓
fresh semantic computation
without reopening native evidence
          ↓
optional deterministic orientation
          ↓
repeated application semantics
may become durable programs
```

The strongest result is not that Ontology Author always beats direct source reasoning.

It does not.

The strongest result is that **semantic interpretation can become durable computational state**.

In this benchmark, two independent agents compiled the same heterogeneous evidence into different Worlds, preserved the same important semantic consequences and uncertainty boundaries, and enabled fresh consumers to operate without native-source reconstruction. The experiment further showed that the World representation is not free to consume: fresh agents pay an orientation cost, and semantic persistence alone does not guarantee token savings. Small deterministic context can reduce some of that cost, and repeated semantic programs can themselves be persisted, but neither optimization is yet universal.

The evidence therefore supports:

> **Ontology Author as a semantic compilation substrate: agents can construct purpose-fit semantic state once and reuse it downstream, while unsupported meaning remains explicit and the representation remains free to vary.**

It does not support:

> a universal ontology, guaranteed accuracy superiority, guaranteed token savings, or a requirement that all downstream work pass through the World.

No experiment in the grain sequence required a semantic-kernel change.

The sequence therefore ends with the architecture intact:

```text
FREE CONSTRUCTION
      ↓
NARROW GROUNDED WORLD
      ↓
FREE CONSUMPTION
```

with orientation context and durable application computation remaining optional layers outside the kernel.

---

# Frozen research artifacts

## Direct construction/evaluation

```text
/tmp/grain-traceability-v1-experiment-final-20260908/
```

Construction metadata:

```text
metadata/construction_result_report.json
```

Frozen Worlds:

```text
sealed/OA-1/world
sealed/OA-2/world
```

Construction transcripts:

```text
transcripts/OA-1.jsonl
transcripts/OA-2.jsonl
```

Direct hidden evaluation:

```text
evaluation_runs/grain-traceability-v1-direct-semantic-20260908/report.md
```

Frozen direct-evaluation report SHA-256:

```text
dfd0cdaccdc48694f1fce5adac61c0ba7b4d7703c077268d488002b0e019d2f9
```

## Consumer / reference comparison

```text
evaluation_runs/grain-traceability-v1-consumer-20260909/
```

Principal reports:

```text
prior_reuse_evidence.md
grain_consumer_comparison.md
shared_omission_diagnosis.md
cumulative_findings.md
```

## Token analysis

```text
evaluation_runs/grain-traceability-v1-consumer-20260909/token_analysis.md
evaluation_runs/grain-traceability-v1-consumer-20260909/token_analysis.json
```

Frozen hashes:

```text
token_analysis.md
7b63ca1bb8e0034e4146b82dfae370e6cdf781e74023504e9e6356d955c4410c

token_analysis.json
7b88629c0a0f5c09fd0a5a2d039e813e4d04cb941a6cc24f40923fa396672274
```

## World-context experiment

```text
evaluation_runs/grain-traceability-v1-world-context-20260909/
```

Principal artifacts:

```text
world_context_spec.md
world_context_renderer.py
freeze_manifest.json
results.md
results.json
output_hashes.sha256
```

## Durable-computation experiment

```text
evaluation_runs/grain-traceability-v1-durable-computation-20260909/
```

Principal reports:

```text
final_findings.md
direct_computation_audit.md
consumer_results.md
token_amortization.md
freeze_manifest.json
output_hashes.sha256
```

All benchmark, World, evaluator, reference, and previously frozen research artifacts remained unchanged throughout the later analysis and reuse experiments.
