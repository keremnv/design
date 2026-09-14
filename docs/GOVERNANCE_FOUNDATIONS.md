# Software-governance foundations

This document freezes the architectural meaning of the future software-
governance system. It is layered on top of Ontology Author, but it is not a
rewrite of Ontology Author's generic semantic World.

The words below have different force:

- **Invariant** means an architectural property that current implementation
  must preserve unless this document is deliberately revised.
- **Hypothesis** means a useful design idea that still needs experiments. It
  must not be treated as a required schema or workflow.
- **Deferred question** means an intentional decision gap. Future work should
  make the decision when the relevant evidence exists.

## Invariants

### 1. Evidence, claims, and identities are distinct layers

The governed system has at least three conceptual layers. They need not be
three physical storage layers:

```text
EVIDENCE
  authoritative source material
  addressable source regions
  source-native objects where useful

        ↓ grounds

CLAIMS
  propositions and relations established from evidence, program mechanics,
  derivation, or intelligent interpretation

        ↓ involve

IDENTITIES
  constructed semantic referents
  mechanically derived program referents
  source-native referents where the provider supplies useful object identity
```

The identity invariant remains:

```text
source identity != semantic identity != program identity
```

Here, “source identity” means source-native object identity where it exists.
It does not mean that every addressable source region has an identity of its
own. Claims can relate identities across these planes, and correspondence is
represented through explicit relations.

#### Source evidence is not automatically a source referent

Authoritative material must remain reconstructibly addressable. For prose
sources such as Markdown, mechanically addressable structures may include:

```text
document
heading
section
paragraph
span
```

These are primarily evidence locations. The architectural invariant is:

```text
addressable source evidence != persistent source referent
```

A section may be topically about one subject while expressing several
propositions involving several entities, conditions, consequences, values,
states, or exceptions. For example:

```markdown
## Purchase Action

The purchase action displays the final total.
It submits the order when activated.
If authorization fails, the user returns to review.
```

The section is not semantically equivalent to `PurchaseAction`. It may ground
claims such as:

```text
displays(PurchaseAction, FinalTotal)
activation_triggers(PurchaseAction, SubmitOrder)
authorization_failure_returns_to(Review)
```

Discourse boundaries, proposition boundaries, and entity boundaries are
different kinds of boundary. A source region can ground a claim without
becoming a referent.

#### Source-native referents are conditional

Some providers genuinely expose useful object identity, such as Figma
node/component IDs, issue or ticket IDs, schema objects, and API operations
with native relationships. Those objects may become source-native referents.
Their exact source observation remains evidence addressing the object.

Other source types need produce no source-native referents at all. In
particular, a Markdown heading or section should not become a durable referent
merely because it has a stable locator.

#### Semantic referents are constructed identity commitments

A semantic referent is not an entity discovered in prose. It is an identity
introduced by semantic construction because preserving it independently of one
source representation or one program implementation is useful. Examples are:

```text
semantic:checkout.purchase_action
CheckoutFlow
PaymentAuthorization
```

Different expressions such as “the purchase action”, “submitting the purchase”,
and “the primary checkout action” may be resolved onto one semantic referent.
That resolution is an intelligent identity commitment. Its evidence and
resolution method must remain inspectable.

A semantic referent should earn persistence through concrete value such as
cross-source identity, a connection between source meaning and implementation,
continuity across implementation replacement, repeated governance use,
multiple claims attaching to the same concept, or historical continuity. Do
not create semantic referents for every noun phrase.

Semantic referents are not mandatory intermediates. Both topologies may be
valid:

```text
source evidence -> semantic referent -> program referent
source evidence -> program referent
```

The second is valid when authoritative material directly describes or
constrains a mechanically identifiable program object. Semantic identity
exists because it preserves useful independent identity, not because every
source/program correspondence needs a middle node.

#### Claims are distinct from the identities they involve

Much of what prose contributes is proposition rather than entity identity.
Natural language may express relations involving several participants:

```text
allowed_when(action, condition, context)
displays(component, value, state)
applies_to(policy, action, jurisdiction, version)
replaced_by(component_a, component_b, condition)
```

Preserve these as precise propositions and typed n-ary relations where useful;
do not force them into properties on one entity. A useful construction model
is:

```text
SOURCE LANGUAGE / STRUCTURE
        ↓ interpretation
REFERENTS + CLAIMS
        ↓ selective persistence
DURABLE SEMANTIC WORLD
        ↓ deterministic selection
ADJUDICATION CONTEXT
```

Every transformation can lose information. The architecture does not seek a
perfectly lossless formalization of natural language. It seeks enough explicit
semantic structure to recover the relevant original authoritative evidence.
The World is therefore a grounded semantic structure/index over authority, not
a complete serialization of source meaning. Original evidence compensates for
semantic nuance lost during normalization.

### 2. The program spine is mechanically privileged

The future program spine is versioned, mechanically derived, reconstructible
from code, and purpose-independent in its contract. The program spine is not
an agent-authored ontology.

Whenever a compiler, parser, build graph, type checker, static analysis, or
other mechanical mechanism can establish a software fact, governance should
derive that fact mechanically wherever practical. Intelligence may interpret
what a program object means, but it must not invent a mechanical fact that the
program mechanism can establish.

Program presence is exhaustive within the program spine's declared analysis
universe. The spine's program identities and mechanical claims are part of the
governed World. An in-scope program identity remains represented even when no
semantic or governance claim attaches to it. Program-universe completeness
does not imply semantic or governance completeness.

OMG KDM 1.4 is the normative semantic basis for the v0 mechanically derived
program spine. Snapshot program identities are manifestations in one
mechanical snapshot; cross-version lineage is a later explicit mapping between
those manifestations. The detailed KDM profile belongs in
`docs/KDM_PROFILE.md`, not in these foundations.

This task does not select the program-spine technology.

### 3. Authority defines an evidence boundary, not a representation quota

A user may declare sources authoritative for governance. Construction may use
those sources as governing evidence. That declaration does not require:

- representing every file;
- making every section a referent;
- classifying every source region;
- placing every source statement in the World; or
- achieving corpus-wide semantic completeness.

The durable semantic structure remains sparse and purpose/use driven.
Construction coverage and runtime case-selection completeness are different
properties. An authoritative source can remain unbound to a semantic claim
without thereby becoming irrelevant.

### 4. Original authority remains semantically primary

The World is a structural and semantic interpretation over authoritative
material. It does not replace that material. When a source sentence is
normalized into a relation, the exact source region must remain reconstructibly
addressable.

Normalization may lose linguistic nuance. That is acceptable only because the
original evidence remains available to later adjudication. An adjudicator
must be able to consume the original authoritative material, rather than only
the normalized semantic claim.

### 5. Grounding is not authority

Grounding records why and where a claim was supported. It does not by itself
mean that the claim is authoritative, true, normative, applicable, or
complete. A README, generated artifact, source file, authoritative policy, and
test fixture may all ground claims while having different governance standing.

Authority is an application-level boundary separate from generic World
grounding.

### 6. Epistemic origin and referent resolution must survive

Governance currently needs to preserve distinctions such as:

```text
mechanically_source_native
source_explicit
source_structural
cross_evidence_inferred
hypothesized
```

These mean, approximately:

- `mechanically_source_native`: the source system structurally exposes the
  relationship;
- `source_explicit`: a source states the relationship and intelligence mainly
  resolves or extracts it;
- `source_structural`: organization, layout, or containment substantially
  establishes it;
- `cross_evidence_inferred`: intelligence combines multiple source or program
  facts to establish it; and
- `hypothesized`: the relationship is plausible but not established strongly
  enough to be ordinary durable truth.

Referent resolution is a separate dimension. Useful values may include:

```text
native_id
deterministic
source_defined
agent_resolved
ambiguous
```

For example, a document may explicitly assert a relationship while both
participating referents require agent resolution. The permanent schema for
these dimensions is not fixed here, but future code must retain enough
provenance to avoid silently collapsing them.

`ConstructionOrigin.SEMANTIC` is therefore only a coarse construction/support
classification. It is not the full governance epistemic model.

### 7. Derived determinism does not launder inference

If intelligent cross-source inference establishes `A`, and deterministic SQL
derives `A -> B -> C`, then `B` and `C` are deterministic consequences given
`A`. They are not thereby mechanically established from external reality.

Every provenance or warrant chain must preserve the epistemic dependence on
`A`, including when later relations are derived deterministically.

### 8. Unknown is first-class

Absence is not false unless an appropriate completeness claim warrants that
interpretation. Ambiguous entity resolution must not be silently forced.
Unbound authoritative material must not automatically be treated as
irrelevant. Insufficient evidence may remain unresolved. Graph connectivity is
not a goal by itself.

### 9. Preserve precise relations

Governance does not introduce a universal relation vocabulary at this stage.
When a source or program mechanically establishes a relation such as
`calls`, `instance_of`, `contains`, `code_connects`, or `renders`, preserve
that relation. When authoritative language supports a useful domain-specific
relation, preserve as much specificity as practical. The graph need not reduce
all human meaning to a small relation basis.

Where normalization is lossy, original evidence remains the recovery path.

### 10. Persistence creates maintenance responsibility

Each persistent non-mechanical assertion is a bet that the interpretation will
be reused. It creates an obligation to reconsider or invalidate the assertion
when its grounds change. Persistence is not free caching.

Future maintenance must account for changes in source state, program state,
adapter or resolver logic, and semantic dependencies. The complete invalidation
system is intentionally outside this task.

### 11. Artifact integrity and external validity differ

A sealed World can be internally valid and immutable while being stale relative
to newer code or authoritative sources:

```text
sealed / valid artifact != currently valid model of external state
```

The current sealed-World lifecycle protects artifact integrity. Governance
maintenance must separately establish external validity.

### 12. Normal adjudication is selection over persisted structure

The intended steady-state path is:

```text
code diff
  -> program-spine delta
  -> affected program referents and relations
  -> deterministic query/traversal over persisted semantic structure
  -> exact authoritative source regions
  -> self-contained adjudication case
  -> intelligent adjudication
```

Normal case assembly must not depend on semantic search, embeddings, broad
grep, RAG, or an agent rediscovering relevant sources from scratch. Search and
exploration belong primarily in construction, repair, and unresolved cases.

```text
SEARCH / INTERPRET
      ONCE
       ->
     PERSIST
       ->
   SELECT MANY TIMES
```

### 13. Case assembly and adjudication are separate

Case assembly selects the persisted referents, program facts, semantic claims,
provenance, and exact original authoritative material that accompany a concrete
change. Adjudication interprets that bounded material against the change.

Neither operation should be hidden inside the other.

### 14. Construction is free; durable output is rigid

During construction, the coding agent may inspect sources, navigate code,
write parsers, write adapters and resolvers, run experiments, use ordinary
programming tools, and revise its interpretation. The rigid boundary is what
becomes durable.

```text
freedom in investigation
rigidity in claims
```

Persist observable evidence and provenance. Do not persist private
chain-of-thought.

## Hypotheses

The following are deliberately not invariants:

- Sparse, purpose-specific semantic Worlds will usually be easier to maintain
  than a single broad governance ontology.
- When the correct factorization is unclear, temporary duplication may be safer
  than premature semantic unification.
- Human input may be most valuable as priors over stakes, rare exceptions, and
  consequential distinctions while agents handle semantic engineering.
- Repeated case assembly may reveal deterministic computations that deserve to
  become ordinary software.
- Persisted semantic structure may improve a fresh agent's problem framing and
  judgment, rather than merely reduce retrieval cost.

These require experiments before they become product rules.

## Deferred questions

Leave these unresolved until the program-spine milestone and its evidence make
the choices concrete:

- Which program-spine technology and exact fact contract will be used?
- What permanent schema combines support mode, referent resolution,
  confidence, warrant dependencies, and exact grounding?
- How should source, semantic, and program identity namespaces be represented
  across World revisions and projects?
- What authority registry and policy binds source observations to governance
  standing?
- How are source, program, adapter, resolver, and semantic dependency changes
  detected and invalidated?
- How are semantic referents carried across World revisions without making a
  sealed World mutable?
- Which relations belong in durable semantic structure and which belong in
  case-local or procedural state?
- What source and program adapter contracts are needed, and how should their
  lifecycle be managed?
- How are unresolved cases repaired, escalated, or left unresolved?
- What adjudication input and output format is appropriate, including human
  review and policy decisions?

No program spine, source adapter, diff analysis, traversal, adjudication
policy, or search infrastructure is implied by this document.
