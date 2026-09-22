# Ontology Author — Pre-Application Research Baseline

**Status:** downstream research baseline, not Core architecture authority.
Non-authoritative for Core Product v1. It records the reconciled
pre-application conclusions intended to be carried into Application v1. It
does not modify the frozen Core boundary, does not duplicate the exploratory
material in
[CONSTRUCTION_AND_APPLICATION_RESEARCH.md](CONSTRUCTION_AND_APPLICATION_RESEARCH.md),
and does not define the test application.

Relationship between the three layers:

```text
research document      = exploratory reasoning / evidence
pre-application base   = reconciled downstream conclusions (this document)
Application v1 contract = concrete normative application specification (not yet written)
```

Core authority remains
[CORE_PRODUCT_V1_BASELINE.md](CORE_PRODUCT_V1_BASELINE.md),
[CORE_PRODUCT_V1_COMPLETION_CONTRACT.md](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md),
and [ARCHITECTURE.md](ARCHITECTURE.md).
This baseline does not prescribe the domain, schema, or implementation of the
first application.

## 1. Starting boundary

Core Product v1 is treated as the fixed substrate.

The application may rely on:

* heterogeneous evidence being mechanically addressable and revisioned;
* executable semantic construction;
* typed relational Worlds;
* grounding and construction origin;
* derivations;
* scoped completeness;
* explicit unresolvedness;
* sealed, independently addressable revisions;
* supported relational and inspection reads.

The application owns:

* domain vocabulary;
* semantic interpretation;
* application questions;
* evidence scope;
* ambiguity policy;
* completeness adequacy;
* admission policy above the Core minimum;
* authority where needed;
* workflow;
* application adequacy.

Core is reopened only if a concrete application requirement cannot be represented honestly with the existing primitives.

---

## 2. Evidence adaptation and semantic construction

The fundamental separation is:

```text
SOURCE
    ↓
EVIDENCE ADAPTATION
    ↓
mechanically justified observations
    ↓
SEMANTIC CONSTRUCTION
    ↓
CANDIDATE RELATIONAL KNOWLEDGE
    ↓
VALIDATION / ADMISSION
    ↓
SEALED REVISION AT A FRESH ADDRESS
```

Accepted history is never mutated; renewal publishes a new sealed revision at
a fresh address, leaving prior revisions independently addressable.

Evidence adaptation answers questions such as:

* what source was observed;
* at what revision;
* what bounded region or record was addressed;
* what source-native mechanical structure exists;
* whether the addressed material can be reconstructed;
* what known losses or parser limitations apply.

Evidence adaptation does not decide semantic meaning.

Semantic construction may:

* normalize source representations;
* establish cross-source identities;
* construct relations;
* classify or abstract;
* fuse competing evidence;
* synthesize cross-source claims.

A semantic binding is one subtype of construction: it relates a semantic identity or interpretation to another address space, such as a program entity. Not every semantic construction is a binding.

Grounding preserves the connection between a semantic assertion and its evidence. It does not prove the assertion objectively true.

Support, authority, and truth remain distinct:

```text
material support
    ≠
authority to establish
    ≠
objective truth
```

Recorded maintenance dependencies likewise describe an inspectable declared basis. They do not prove that every condition relevant to the interpretation has been captured.

---

## 3. Construction is free in representation but bounded in consequences

The constructor is intentionally executable and expressive.

The application should therefore constrain construction primarily through required consequences rather than a prescribed ontology.

```text
APPLICATION INTENT
        ↓
APPLICATION SPECIFICATION
        ↓
visible adequacy requirements
        ↓
CONSTRUCTION
        ↓
WORLD
       / \
      /   \
CORE       APPLICATION
CONFORMANCE ADEQUACY
```

The application specification should identify consequential distinctions such as:

* identities that must remain distinguishable;
* relations that must be recoverable;
* temporal distinctions;
* ambiguity that must remain unresolved;
* scopes where absence may or may not be meaningful;
* questions the resulting representation must support.

Unless schema itself is an application requirement, the specification should not prescribe exact table names, relation names, row sets, constructor internals, or one canonical ontology.

Different Worlds may therefore be equally adequate.

```text
World A ──┐
World B ──┼── satisfy the same application specification
World C ──┘
```

This freedom does not mean anything goes. A World can still fail because it is epistemically dishonest, loses a required distinction, silently resolves ambiguity, overstates completeness, or cannot support required application behavior.

---

## 4. World acceptance

World acceptance for an application has two independent components:

```text
CORE CONFORMANCE
    structural validity
    grounding / origin honesty
    revision
    completeness claims
    unresolvedness
    historical integrity

            +

APPLICATION ADEQUACY
    required distinctions
    questions
    invariants
    ambiguity behavior
    perturbation behavior
    held-out compositional capability
```

Neither substitutes for the other.

A World may be epistemically impeccable but application-inadequate because required knowledge is missing.

A World may answer every visible application question while containing unsupported semantic guesses and therefore still be unacceptable.

Application adequacy is evidence that the World satisfies a bounded behavioral specification. It is not proof of objective semantic truth or of one uniquely correct conceptualization.

---

## 5. Adequacy methodology

Application adequacy should use several kinds of probes.

### Competency questions

Questions establish capabilities the application requires.

They should express consequences rather than freeze representation.

### Invariants

Invariants specify properties that must hold across relevant Worlds or cases.

### Ambiguity probes

Ambiguity tests ensure that insufficient or competing evidence remains explicitly unresolved rather than being forced into a unique answer.

### Perturbation / metamorphic probes

Perturbation tests establish whether meaningful distinctions respond correctly to source changes.

Examples include:

```text
unrelated evidence change
    → semantic answer remains stable

relevant ownership change at time T
    → historical and later answers diverge correctly

second equally plausible identity candidate appears
    → previously unique correspondence becomes unresolved

supporting evidence disappears
    → affected semantic assertion loses sufficient standing
```

### Held-out adequacy probes

Some probes should remain unavailable while developing construction.

Their purpose is not to demand arbitrary future knowledge. They test whether construction captured reusable distinctions and relations rather than merely compiling known fixture answers.

Tests remain evidence of specification satisfaction. They are not the entire specification.

---

## 6. Adequacy and completeness are orthogonal

Application adequacy means:

> enough structured knowledge exists to perform the specified work honestly.

Completeness means:

> a particular relation or universe has an explicitly established coverage status under a particular scope.

An adequate application World may intentionally know only a bounded subset of the external world.

Honest unresolvedness or UNKNOWN completeness may therefore be fully adequate.

---

## 7. Persist high-leverage joins, not anticipated answers

Raw evidence remains a first-class part of the agent's information environment.

Cheap, local, representation-specific facts should normally remain raw when ordinary tools can recover them efficiently.

Durable construction is strongest when information is:

* identity-bearing;
* cross-source;
* non-local;
* expensive to reconstruct;
* broadly reusable;
* compositionally useful;
* stable enough to amortize construction cost.

The default heuristic is:

```text
cheap / local / source-specific
        → raw evidence

cross-source / identity-bearing / reusable / compositional
        → candidate World knowledge
```

The World should therefore complement grep, read, git, shell, source-native APIs, and other low-level tools rather than replace them.

---

## 8. Bridge relations

A **bridge relation** is an application/research heuristic, not a Core primitive.

It is:

> a reusable constructed identity or relation whose primary leverage comes from connecting otherwise disconnected information spaces.

Examples might include:

```text
repository → service
service → team
service → deployment
deployment → revision
service → incident
dataset → pipeline
ticket → customer
```

Bridge relations are interesting because small amounts of durable relational knowledge may unlock many compositions over information that otherwise remains disconnected.

The heuristic is:

> Prefer durable construction of high-leverage bridges over exhaustive modeling of every source.

Whether this hypothesis is actually useful must be tested in applications.

---

## 9. Admission is proportional to claim and intended use

Admission is not synonymous with semantic construction.

Admission asks:

> What must be mechanically inspectable or established before this application is willing to persist or rely on this claim in the intended way?

Admission strength should be selected per claim/relation family rather than globally for the application.

This ladder is downstream application guidance, not a Core primitive.

### Level 0 — ordinary grounded construction

Appropriate for mechanically established or low-risk facts.

Typical requirements:

* valid relation shape;
* referential integrity;
* grounding;
* correct construction origin.

### Level 1 — bounded semantic claim

Appropriate for semantically inferred identities or bridge relations where ambiguity or unsupported correspondence would matter.

Possible requirements:

* bounded claim shape;
* bounded identities/endpoints;
* inspectable material support;
* semantic origin;
* explicit ambiguity handling;
* no unsupported endpoint substitution.

### Level 2 — completeness-sensitive claim or inference

Appropriate when consumers rely on:

* absence;
* uniqueness;
* universality;
* exhaustive sets;
* bounded negatives.

Additional requirements may include:

* explicitly defined universe;
* matching scoped completeness;
* uniqueness basis;
* currentness of the relevant completeness basis.

### Level 3 — durable governed commitment

Appropriate only when a semantic interpretation must survive into later revisions, be actively reassessed, or drive sufficiently consequential workflow.

Possible additional machinery includes:

* explicit construction obligation;
* admission profile;
* authority requirements;
* commitment warrant;
* maintenance dependencies;
* later-state reassessment.

The existing semantic-binding machinery is evidence for this stronger case. It is not mandatory merely because an application contains semantic relations.

The default rule is:

> Use the weakest admission regime that survives the application's adversarial probes.

Admission strength follows **claim + intended use**, not whether the claim was produced by an LLM, deterministic program, or human.

---

## 10. Application task taxonomy

Future applications should contain tasks with different information requirements.

### Raw-dominant

Best solved primarily with raw inspection.

### Structured-dominant

Best solved primarily from persistent relational knowledge.

### Mixed sequential

Require movement from raw discovery into structured context, or vice versa.

### Mixed compositional

Require substantial composition between raw evidence and persistent relational context.

### Investigative

The agent chooses its own path through raw and structured information and must retain evidentiary discipline.

Including raw-dominant tasks is important as a negative control. A useful World need not improve every task.

---

## 11. Product evaluation ladder

The first application experiment should compare:

```text
A — RAW

grep
read
git
source-native tools
```

against:

```text
B — RAW + WORLD

same raw capabilities
+
SQL / supported World reads
```

This tests whether persistent relational context adds useful capability.

Only if B reveals repeated orchestration friction should a later experiment introduce:

```text
C — RAW + WORLD + RELATIONAL RETRIEVAL
```

where ephemeral retrieval operations such as grep may participate directly in relational composition.

The contrasts are deliberately separate:

```text
A → B
value of constructed durable relational knowledge

B → C
additional value of relationally composable retrieval
```

No assumption is made that C is needed or superior.

---

## 12. Failure diagnosis before architectural response

Application failures should first be classified.

Possible failure classes include:

```text
missing evidence
bad evidence adaptation
bad semantic construction
insufficient application specification
inappropriate admission
inadequate World representation
insufficient completeness
agent query / reasoning failure
awkward raw/World interface
```

These imply different remedies.

In particular:

```text
agent query failure
    ≠ automatically bad World schema

semantic construction failure
    ≠ automatically missing Core primitive

application inadequacy
    ≠ automatically need richer admission
```

Core should reopen only after a concrete failing requirement demonstrates that the existing primitives cannot represent the necessary state honestly.

---

## 13. Deferred hypotheses

The following remain explicitly downstream until application evidence justifies them:

* relational retrieval such as `grep(...)` inside relational composition;
* live or virtual external relations;
* automatic semantic renewal;
* generic admission DSLs;
* richer canonical program representations;
* generic authority/governance machinery;
* automatic application-specification generation;
* universal ontology synthesis.

Live relations, retrieval relations, and durable World relations should remain epistemically distinguishable even if they later share a relational query layer.

---

## 14. Pre-application working principles

Before defining the first application, the project adopts the following downstream research principles:

1. Preserve raw evidence and ordinary low-level tools.
2. Keep evidence adaptation mechanical and semantic interpretation explicit.
3. Treat semantic binding as one construction form, not the universal construction model.
4. Let applications constrain consequences rather than prescribe schemas.
5. Require both Core conformance and application adequacy.
6. Treat explicit unresolvedness as potentially adequate.
7. Use competency questions, invariants, ambiguity probes, perturbations, and held-out cases.
8. Persist high-leverage joins rather than cheap local facts or anticipated answers.
9. Treat bridge relations as a design hypothesis, not a new system primitive.
10. Choose admission strength per claim and intended use.
11. Begin with the weakest honest admission regime and strengthen it only when experiments demonstrate failure.
12. Diagnose failures before adding infrastructure.
13. Test raw + World before inventing tighter retrieval composition.
14. Do not reopen Core without a concrete application requirement that existing primitives cannot honestly represent.

## 15. Handoff to Application v1

The pre-application research phase is complete when these principles are captured and reconciled with the repository.

The next artifact is then a bounded **Application v1 Completion Contract** defining:

* the actual job;
* available evidence;
* consequential distinctions;
* required relational/bridge capabilities;
* competency questions;
* invariants;
* ambiguity cases;
* perturbation behavior;
* held-out evaluation policy;
* admission expectations by claim family;
* raw capabilities retained by the agent;
* application completion criteria.

That contract should be the point where a concrete test application is finally chosen. This baseline does not define it.

No further generic architecture work is required before that step.
