# Software Governance Construction Contract v0

Status: accepted Construction v0 baseline, 2026-09-23. This is not Core
Product v1 authority and not a change-processing or judgment design. The
executable record is
[SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md).

It defines the durable state Software Governance may construct and the
guarantees a fresh consumer of a sealed World may rely on. Historical
application contracts are evidence. Where they conflict with the experiments
and the two acceptance profiles named in the appendix, this contract follows
that evidence.

Normative words are **MUST**, **MUST NOT**, **MAY**, and **NOT YET JUSTIFIED**.
A capability has a versioned identifier. Changing the meaning of a subject
kind, relation, resolution state, manifestation, or completeness basis
requires a new capability version.

```text
heterogeneous evidence
        +
mechanically trustworthy software representation
        ↓
semantic construction
        ↓
governance knowledge
        +
grounded knowledge ↔ software bindings
        +
explicit unresolvedness
        ↓
sealed World
        ↓
independent application reads
```

## 1. Architectural position

Software Governance is an application above Core Product v1.

Core provides the relational World, grounding, construction origin, revision,
scoped completeness, and explicit unresolvedness. It does not know governance
vocabulary.

Software Governance adds application semantics for consuming a software
representation, recording governance knowledge, and recording grounded
bindings between that knowledge and software subjects.

The demonstrated producer-neutral boundary is:

```text
software_subject
software_manifestation?       optional
producer-owned mechanical relations / observations
```

A producer that meets sections 2–4 supplies subjects through that receipt.
Program Spine is one such producer. It is not the interchange schema. The
config-route profile is the acceptance evidence for that separation. An AST
or compiler object is producer-private unless a versioned mechanical
capability exposes it as a durable subject, relation, or observation.

Construction submits candidates. The kernel admits them mechanically. Sealing
publishes a revision at a fresh address. Independent reads follow sealing.
This contract does not define how a later snapshot is compared, how bindings
are retrieved after a change, or how a judgment is reached.

The generic durable vocabulary justified by both acceptance profiles is:

```text
software_subject
software_manifestation          optional

governance_proposition
governance_binding
governance_candidate
governance_question

governance_completeness
governance_known_gap
```

None of these is profile vocabulary. None is recoverable without loss from
the others: the receipt is not the binding, the manifestation scheme is not
the subject kind, the proposition’s evidence is not the correspondence
basis, a candidate is not a binding, and a known gap is not a status word.
No further generic relation is frozen.

## 2. SoftwareSubject

A **SoftwareSubject** is a mechanically identified member of a declared
program snapshot. It is the thing governance knowledge may concern.

A durable software subject MUST have:

- a snapshot-local identity that does not claim cross-snapshot continuity;
- a declared subject kind owned by a named producer capability and version;
- reconstructible evidence for that identity;
- explicit membership in the snapshot’s program universe, including an
  explicit boundary when the producer distinguishes in-scope subjects from
  external stubs;
- structural context where the producer mechanically has it.

A label, a containing file, or a structural parent MUST NOT be treated as
semantic meaning or as governance scope.

Subject kinds are capability vocabulary. This contract does not freeze a
universal subject-kind enum.

`software_subject` is the demonstrated application-facing receipt for one
mechanically identified software subject. A fresh consumer MUST be able to
recover at least:

- the snapshot-local subject identity;
- the subject kind;
- the producing capability and version;
- membership in the software snapshot or universe named by the receipt;
- the mechanical grounding for that identification.

The receipt does not interpret governance meaning. It does not require a
source byte range, a call-site kind, or a Program Spine table. A producer
MAY record an explicit in-scope or external boundary when it distinguishes
those, as its own mechanical fact rather than as a column of this receipt.

A source region is not a software subject. An observation of bytes, a token
range, or a file MAY ground a subject. It becomes a subject only when a
declared capability identifies it as one.

## 3. Manifestation

These are separate facts:

```text
subject identity
manifestation content
source or non-source location
structural context
```

A subject MAY change manifestation without moving. A subject MAY move without
changing manifestation. Structural context records placement. It does not
state what the subject means or which governance knowledge applies to it.

A subject-local manifestation MUST be:

- defined by the producer capability and version that exposes it;
- mechanically reconstructible from the snapshot’s immutable inputs;
- content-addressed where that capability has a content representation;
- recorded separately from the subject’s location.

Byte offsets and file paths are location. They MUST NOT be used as identity.

When a producer exposes a trustworthy local manifestation for a subject, the
digest of a whole source file MUST NOT be the canonical local manifestation
of that subject. A file digest MAY remain a producer fact about the file.

`software_manifestation` is optional. A subject that is mechanically
identified and grounded remains valid when the producer has no honest local
manifestation to record. The read for that subject reports that no
manifestation was produced.

When a producer does record one, the row MUST make recoverable:

- the manifestation scheme;
- the location or coordinate, kept distinct from identity and from content;
- the producing capability, including its version;
- grounding from which the manifestation content can be reconstructed.

The digest is computed from that reconstructed content. This contract does
not require a source byte range and does not prescribe one scheme.

Two schemes have been tested. They are evidence, not normative vocabulary:

```text
source-token-range        TypeScript token range; offsets are location
canonical-json-record     canonical JSON of one structured record;
                          a JSON pointer is the coordinate
```

A software subject NEED NOT be source-backed. A coordinate that is not a
source token range MUST stay distinct from the subject’s identity, MUST name
its producer capability and version, and MUST NOT be disguised as a source
token range.

The current comparison limit on call-site insert-before and reorder is a
correspondence limit. It is not a reason to widen a subject’s manifestation
to the owner or the file.

## 4. ProgramRelation

Software Governance does not standardize every mechanical software relation.

A producer MAY expose additional precise mechanical relations whose schemas
and positive rules it owns. The mail profile’s invocation facts and the
config profile’s route facts are examples. `program_invokes`, `config_route`,
and `config_member` are not Software Governance vocabulary. A producer NEED
NOT expose the same additional relations as another producer. Governance
construction succeeds when the concern only needs a subject.

A generic consumer MAY discover mechanical facts that name a SoftwareSubject
by reading ordinary World relations. It does not interpret their domain
meaning, and it does not require those relations to exist.

A **ProgramRelation**, in this contract, means any such producer-owned
mechanical assertion. It is not a required relation name. Governance does
not receive a universal edge vocabulary, and it does not require a
first-class relation object.

A capability that emits a relation MUST define:

- the relation name and the capability version;
- the role names and the endpoint kinds allowed in each role;
- the rule under which a positive assertion is emitted;
- the grounding of each assertion;
- boundary behavior for external endpoints;
- how uncertainty is recorded;
- the completeness basis and the known omissions.

Precise relations are required. A universal `depends_on` MUST NOT stand in
for a capability that can name a more specific relation.

Where a capability resolves an endpoint, it MUST be able to record:

```text
RESOLVED
MULTIPLE_CANDIDATES
UNRESOLVED
```

A positive relation assertion MUST be emitted only when every endpoint
assignment required by that capability’s positive assertion rule is
established. Several positive relations from one subject are ordinary when
each of those assignments is established. That is not `MULTIPLE_CANDIDATES`.

`MULTIPLE_CANDIDATES` and `UNRESOLVED` record an endpoint role the capability
has not uniquely assigned. They MUST NOT be rewritten as a positive endpoint,
and a positive relation MUST NOT use a candidate or an unresolved outcome as
a stand-in endpoint.

An endpoint of a positive relation MUST be a software subject or an explicit
external stub.

An assertion identifier names one tuple inside one snapshot. It is not a
governance binding target under section 7. Creating an application-level
relation referent, or a kernel edge object, to give governance something to
point at is **NOT YET JUSTIFIED**.

## 5. Governance knowledge

These identities stay distinct:

```text
source evidence
source-native identity
source-derived proposition
semantic identity
software identity
```

Source evidence is the addressable original. A durable governance record MUST
keep that evidence recoverable. Construction MUST NOT replace the source
wording with a normalization and discard the wording.

A source-native identity exists only when the source provider supplies one.
Prose does not automatically mint one.

A source-derived proposition is a constructed reading of one or more evidence
regions. It is an index over that evidence. One evidence region MAY support
several propositions. A proposition MAY be recorded without a semantic
identity.

A semantic identity is the optional commitment in section 6.

A software identity is a SoftwareSubject. It is not a semantic identity and
MUST NOT be reused as one.

This contract does not freeze a domain predicate vocabulary. A profile chooses
the relation names that make its propositions inspectable.

## 6. Semantic identity

A semantic identity is optional. Governance knowledge and a GovernanceBinding
MUST NOT be required to have one.

Direct construction from authoritative evidence to software subjects is the
ordinary form. It is sufficient while a needed read can be answered from
shared evidence, a shared software endpoint, or the evidence and subjects
named in the current snapshot.

The demonstrated v0 use of a persistent semantic identity is one
constructor-recorded semantic subject that a read must name after replacement
of both its source expression and every current software endpoint. That use
is admitted. Equivalence across that replacement is a constructor decision.
The durable record MUST include the provenance of that decision. Comparison
of snapshots does not establish it.

Other uses are **NOT YET JUSTIFIED**. This section does not claim that the
cross-replacement condition is the necessary and sufficient rule for every
future read. A provenance-bearing equivalence between direct
evidence-to-software claims, with no semantic referent, is still an open
alternative for that same read.

A semantic identity MUST NOT be minted only to repeat one role, one named
software subject, or an ambiguous phrase. It MUST NOT turn ambiguous or
unresolved software correspondence into a positive binding.

Semantic identities are application referents. They do not join sealed Worlds
by themselves, and they are not snapshot-local software ids.

## 7. GovernanceBinding

A **GovernanceBinding** answers:

```text
Which governance knowledge concerns which mechanically identified software subject?
```

A binding MUST make these recoverable:

```text
governance knowledge or proposition
software subject
support and basis provenance
endpoint resolution, where a semantic choice of endpoint is involved
construction origin and method
exact grounding
```

The software endpoint of a binding is a SoftwareSubject. The knowledge
endpoint is a proposition referent. That referent is the address of one
source-derived proposition. It is not a semantic subject, not a software
subject, and not an assertion id.

```text
governance_proposition(proposition, statement, domain relation name)
        grounded by the proposition’s source evidence

governance_binding(proposition, software_subject)
        grounded by the correspondence basis
```

These names are the v0 shape. A profile MAY use other relation names when a
fresh consumer can still find this split without a registry of domain
predicates.

A fresh consumer answers “what concerns subject S” and “which subjects
proposition P concerns” from `governance_binding` alone, then reads the
proposition row for the statement and the domain-relation name. Evidence for
P is the grounding of the proposition assertion. The basis for the
correspondence to S is the grounding of the binding assertion. Several
subjects share one proposition assertion, so a second evidence region is
added once.

This stored relation is required for that split. A domain assertion that
itself names the software subject collapses the proposition’s evidence and
the correspondence basis into one tuple, and a consumer cannot separate those
tuples from mechanical relations without a registry of predicate names. A
registry would classify assertions. It would not give the proposition an
address independent of each subject. Grounding a subject-only binding with
the proposition assertion uses grounding as support, which is not the
concern relation. The construction path does not check such a pointer, and
the default Core contract does not admit a commitment-reference role. An
unchecked text copy of an assertion id survives retraction of the proposition.

The binding MUST NOT copy a current ProgramRelation tuple into itself.
ProgramRelations and resolution outcomes remain independent World facts. A
fresh consumer traverses from the bound software subject to the mechanical
relations and resolution rows that currently involve that subject.

An attempted correspondence that is ambiguous or unresolved MUST be a
separate candidate or unresolved record. It MUST NOT be a `governance_binding`
row.

Binding the governance record directly to a ProgramRelation assertion is
**NOT YET JUSTIFIED**. The invocation experiment showed that a subject binding
was sufficient for that concern. It did not examine every governance shape.
Until a later experiment shows a read that subject traversal cannot answer,
profiles MUST NOT add a relation-assertion binding target.

For an invocation-specific concern, the narrowest tested subject is the
call-site occurrence. The owner callable is too broad for that concern: a
binding to the owner does not say which invocation it governs. This call-site
result MUST NOT be generalized into a universal binding grain.

A binding MAY name a call-site subject while that site’s mechanical resolution
is `MULTIPLE_CANDIDATES` or `UNRESOLVED`. In that case the binding concerns
the occurrence. It does not establish a positive relation to any candidate.

## 8. Binding grain and adequacy

```text
Bind to the narrowest mechanically justified SoftwareSubject
sufficient for the constructed correspondence.
```

This rule is provisional outside the tested invocation case.

Contract validity and application adequacy are separate. A binding can satisfy
sections 2 and 7 and still be too coarse for a particular governance purpose.
Adequacy is an application judgment about the constructed correspondence. It
is not a kernel check, and it is not established by mechanical validity alone.

This contract does not prescribe file, callable, call-site, or AST-node
granularity as a global default. The producer must have identified the chosen
subject. Containment inside a coarser subject does not make the coarser
subject the binding target.

A binding to a subject MUST NOT be read as governing every relation inside
that subject. A binding that happens to name a callee MUST NOT be read as
governing every caller of that callee.

## 9. Support and endpoint resolution

Relationship support and endpoint resolution are separate facts. A profile
MUST record both where a binding or proposition selects a software endpoint.
They MUST NOT be collapsed into one score. Numeric confidence MUST NOT be
used.

A relationship MAY be `SOURCE_EXPLICIT` while its software endpoint is
`AMBIGUOUS` or `UNRESOLVED`.

`DETERMINISTIC` endpoint resolution means a declared rule over explicit
material selected that endpoint. It does not make an inferred semantic
relationship mechanical. A deterministic procedure that interprets prose
remains semantic construction.

`ConstructionOrigin.MECHANICAL` and `ConstructionOrigin.SEMANTIC` stay the
kernel origins. A profile’s support and resolution classes sit on the
grounding of the assertion. They MUST NOT be erased by the coarser origin.

Further support and resolution class names MAY be declared by a profile.
They remain two axes.

## 10. Ambiguous and unresolved construction

The constructor MUST be able to leave these as durable, grounded records:

- several plausible software subjects for one piece of knowledge, with no
  unique binding asserted;
- a proposition whose software endpoint is unresolved;
- a proposition that is understood and recorded without a semantic identity;
- a software subject whose mechanical resolution is `MULTIPLE_CANDIDATES`
  or `UNRESOLVED`;
- a candidate that lacks sufficient grounding, recorded as not established.

The constructor MUST NOT force a winner among candidates. A positive binding
or a positive ProgramRelation to one candidate MUST NOT be emitted in these
cases.

Epistemic unresolvedness is an ordinary grounded relation that says the
question is open. Invalid constructor output, a shape violation, or a runtime
failure is a failed construction. Profiles MUST NOT encode failure as an
unresolved binding, and MUST NOT treat an unresolved binding as a crash.

Existing Core relations are sufficient for these records. This contract does
not add a kernel unknown type.

## 11. Construction and admission

Investigation MAY be broad. Durable claims MUST be bounded, grounded,
versioned, and validated.

A mechanical fact MUST keep mechanical origin when a semantic constructor
reads it. A semantic interpretation MUST keep semantic origin when the
procedure that produced it was deterministic.

Origin belongs to the support or construction path, not merely to the
relation name. This is the same Core rule.

These paths are semantic interpretation, including when the procedure is
deterministic:

```text
governance_proposition
governance_binding
governance_candidate
governance_question
```

`governance_completeness` and `governance_known_gap` MAY use mechanical
origin when the row is entailed by what the construction run covered. The
accepted profiles record `INCOMPLETE` and `supplied_correspondences_only` that
way: the run stored the correspondences it was given and did not survey the
snapshot. The same relation names MUST NOT be forced to mechanical origin
globally. A later completeness claim may itself be a semantic judgment about
scope. Admission accepts either origin on those two relations and checks that
the recorded origin matches the path that produced the row.

Admission checks declared shape, support, scope, and grounding. Admission
does not decide that a governance proposition is true, and a passing
admission MUST NOT be presented as adjudication.

The historical four construction-obligation kinds are not the abstraction of
this contract. A profile MAY record which question a construction run was
answering. That record is provenance. It is not a universal obligation type
system.

## 12. Completeness and negative reads

Completeness is scoped to a named capability, a stated universe, and a stated
basis. Completeness of one capability does not transfer to another.

Absence of a row is not negative knowledge. A negative semantic claim MUST
cite an applicable completeness basis that covers the universe of the claim.

The absence of a GovernanceBinding for a subject MUST NOT be read as “this
subject is ungoverned” unless an explicit completeness claim, with its basis
and known gaps, licenses that conclusion for that subject and that body of
knowledge.

The v0 records are `governance_completeness` and `governance_known_gap`.
They are application claims about binding coverage. They are not a Core SQL
derivation receipt: that receipt rewrites a derived relation and stamps the
rows derived. A known gap is its own row, a gap identifier, not a sentence
packed into one text field. `COMPLETE` with a known gap is rejected.

Raw SQL emptiness is not that completeness claim.

## 13. Application read surface

A fresh consumer of the sealed World MUST be able to answer the following
when the World represents the relevant records, without rereading source text
for navigation. The original source MUST remain reconstructible when the
consumer needs the wording itself.

```text
What governance knowledge concerns this software subject?
Which software subjects does this knowledge concern?
What exact evidence supports that knowledge or binding?
Why was this software endpoint selected?
Is the binding established, ambiguous, or unresolved?
What is this subject's local manifestation?
What mechanical relations currently involve this subject?
What resolution and completeness limits apply?
Does this knowledge use a persistent semantic identity, and why?
```

“Why this endpoint” is the recorded endpoint-resolution class and its
grounding, not a reconstructed chain of constructor deliberation.
“Why this semantic identity” is the recorded equivalence provenance required
by section 6. If no semantic identity was used, the consumer MUST be able to
see that the construction was direct.

Navigation that stops at a bound subject MUST still be able to reach that
subject’s current producer-owned mechanical relations by ordinary relational
reads. When the producer did not emit any, the read is empty. That emptiness
is not a missing binding and is not a negative governance claim.

## 14. Explicit non-goals

This contract does not define, and a profile MUST NOT treat it as settling:

- Git diff ingestion;
- cross-snapshot correspondence;
- maintenance algorithms;
- affected-binding retrieval;
- automatic semantic renewal;
- judgment or adjudication workflow;
- GovernanceCase redesign;
- ContextRequest expansion;
- coding-agent execution;
- a universal policy language;
- a universal AST;
- a universal program ontology;
- a universal relation vocabulary;
- a generic invariant engine;
- decision-right or adoption workflow.

Judgment over a sealed construction World is accepted separately in
[SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md)
and [SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md).
That acceptance is not part of the accepted Construction v0 baseline.

## 15. Falsification

| Restriction | Revisit it if |
| --- | --- |
| Standard binding target is a SoftwareSubject; relation-assertion bindings are not yet justified | A governance concern has a required read that cannot be answered by binding a subject and then reading that subject’s current mechanical relations and resolution rows. |
| Call-site grain is only the tested invocation case | A non-invocation concern has no mechanically identified subject narrow enough for its correspondence, or the owner alone answers every required read for a concern that names one interaction inside the owner. |
| Semantic identities are optional and persist only for the cross-replacement join | A read that direct evidence→software construction cannot answer is solved without a semantic referent, including by a provenance-bearing equivalence between direct claims; or a read that is not that cross-replacement join cannot be answered without a semantic referent. |
| A manifestation scheme is defined by the producer that exposes it; token-range and canonical JSON are tested examples | A subject-local digest for that scheme changes when the reconstructed subject content does not, or fails to change when that content does, or a whole-file digest distinguishes a local change that the subject digest cannot. |
| Relation vocabulary stays per capability | A precise capability relation cannot be given an honest positive rule, grounding, and completeness basis without a universal edge. |
| No first-class relation referent | Naming a relation by its capability, name, and role tuple fails a required governance read that an assertion identifier also fails, and a new referent succeeds without copying the tuple into the binding. |
| Positive relations require a unique target | A consumer need is met only by emitting a positive relation while the capability still reports `MULTIPLE_CANDIDATES` or `UNRESOLVED`. |
| Support and endpoint resolution stay separate | A single recorded class answers both “what licensed the relationship” and “how the endpoint was selected” without losing either read. |
| “No binding” is not “ungoverned” | A scoped completeness claim is shown to be unnecessary for a negative governance conclusion the application must draw. |

## Appendix — evidence note

Core Product v1 supplies the path this contract sits on: addressable evidence,
typed relations, grounding, origin, scoped completeness, ordinary-relation
unresolvedness, and a sealed revision at a fresh address. Adapters do not
assign governance meaning.

Repository archaeology placed software representation, governance knowledge,
and bindings in the application, and treated compiler objects as
producer-private. It also separated structural context from governance scope.
Those placements are the boundary in section 1. Historical contracts remain
evidence. They are not superior to this baseline.

Program Spine is one producer of mechanically trustworthy software
observations. It is not required as the Software Governance interchange
schema. The config-route profile
(`profiles/software_governance_config_v0/`, exercised by
`tests/test_software_governance_config_profile.py`) constructs and reads
governance with no Program Spine tables and no invocation graph. The mail
profile continues to use the spine as its producer and projects the subjects
it binds into `software_subject`.

The manifestation-granularity experiment
(`tests/test_manifestation_granularity.py`) separated identity, token-range
content, and location; showed that a whole-file digest moves when a
neighboring edit does; and showed that insert-before and reorder mis-joins
are comparison limits. Sections 2, 3, and 8 follow that experiment. The
spine’s current source-manifestation fact can still change with the file
digest. This contract does not redefine that producer field. It tells
governance which digest a local dependency may use.

The semantic-identity experiment
(`tests/test_semantic_identity_persistence.py`) answered rewording, a second
source, several manifestations of one sentence, a replaced entry with a
stable endpoint, a one-off named subject, and an ambiguous phrase by direct
evidence→software records. A semantic identity was required only for the
constructor’s join across replacement of both the wording and every software
endpoint. Sections 5 and 6 follow that experiment.
`docs/AUTHORITY_CONSTRUCTION_CONTRACT.md` allows a broader set of reasons for
a semantic referent to persist. That broader list is not the rule here.
`docs/GOVERNANCE_FOUNDATIONS.md` presents semantic referents as part of the
identity layer a governed system has. Persistence of that layer is optional
under section 6.

The binding-target experiment
(`tests/test_governance_binding_target.py`) used one invocation sentence. An
owner binding could not distinguish two calls. A call-site binding could.
The current `program_invokes` row stayed a spine fact. The positive assertion
identifier disappeared when the callee changed, and it did not exist for a
`MULTIPLE_CANDIDATES` call. Sections 4, 7, and 8 follow that experiment.

The representation probe
(`tests/test_governance_binding_representation.py`) stored that call-site
binding in Core relations. A proposition referent plus `governance_binding`
answered the reads without a semantic subject. A domain tuple, an assertion
used as grounding, and a text assertion id did not. Section 7 follows that
probe. The TypeScript token-range digest is one tested profile manifestation.
The config profile’s canonical JSON record is the other. Neither is the
general rule in section 3.
The same run found that today’s TypeScript extractor records a concrete
method call as `MULTIPLE_CANDIDATES` and emits no positive edge. That is a
producer gap. It is not a reason to invent a positive relation in governance.

`docs/GOVERNANCE_CASE_CONTRACT.md` already refuses file proximity as relevance.
That part agrees with section 3. Its selection and case machinery is deferred
by section 14.

## Non-normative companion

The sections below are not additional requirements.

### UNFROZEN QUESTIONS

1. The cross-replacement join was demonstrated with a semantic referent. It
   is still open whether a provenance-bearing equivalence between two direct
   evidence→software claims can answer that same read without the referent.
2. The config-route profile showed that one non-invocation sentence can bind
   a mechanically identified route record. It remains open whether every
   other governance concern already has a mechanically justified subject
   narrow enough to bind, or whether some concern would require a coarser
   subject or a new subject kind.
3. It is open whether any governance read requires the binding to identify a
   ProgramRelation assertion, rather than a subject plus traversal to current
   mechanical rows.
4. The config profile demonstrated a JSON-pointer coordinate and a
   canonical-record manifestation distinct from identity. A grounded subject
   with no manifestation row remains valid. A coordinate that is not
   reconstructible content at all is still untested.
5. The current TypeScript spine does not emit a positive `program_invokes`
   edge for the method calls tried in the binding experiment. Until a
   capability version does, those calls cannot be consumed as established
   caller→target facts. That limits the present producer. It does not settle
   the binding rule.

### EVIDENCE → RULE

| Evidence | Rule in this contract |
| --- | --- |
| Core v1: grounding, origin, scoped completeness, ordinary-relation ambiguity, fresh-address seal | Sections 1, 10, 11, 12, and the read surface |
| Archaeology: application owns meaning; compiler objects are not public identity; structural context is not governance scope | Sections 1, 2, and 8 |
| Manifestation experiment: identity, content, and location diverge; file digest is coarse; token-range digest tracks the subject; insert-before is a comparison limit | Sections 3 and 8 |
| Semantic-identity experiment: direct evidence→software answers the simpler joins; a semantic identity earned persistence only across replacement of wording and all endpoints; ambiguity stays unresolved | Sections 5, 6, and 10 |
| Binding-target experiment: owner is too broad for one invocation; call site suffices; the invoke tuple stays mechanical; assertion identity does not survive retarget and does not exist when unresolved | Sections 4, 7, and 8 |
| Core completeness limits, carried through archaeology | Section 12 |

### Reusable mechanisms

These existing mechanisms can carry the contract without taking on the domain
vocabulary of the programs that first used them:

- World referents, declared typed relations, assertion grounding, and
  construction origin;
- source observations and digest-checked reconstruction of a stored range;
- snapshot-local software subjects through the `software_subject` receipt;
- producer-owned mechanical relations when that producer has them, including
  spine invocation and resolution rows for the TypeScript producer only;
- scoped completeness records with an explicit basis and known gaps;
- ordinary grounded relations for candidates and unresolved questions;
- sealing a revision at a fresh address;
- the separation between relationship support and endpoint resolution.

### Do not reuse

- Checkout, payment, Design, GovernanceLaw, PaymentProvider, and payment-path
  vocabulary, including as example domain.
- The four historical construction-obligation kinds, and admission profiles
  built around them, as the governance abstraction.
- GovernanceCase selection, adjudication workflow, and ContextRequest as part
  of construction.
- A whole-file digest as the canonical local manifestation.
- Byte offsets as identity.
- A semantic twin for every software subject or noun phrase.
- A first-class relation object, or a copy of a ProgramRelation tuple inside
  a GovernanceBinding.
- Numeric confidence.
- `docs/FOUNDATIONS.md` as architecture authority.
- The historical authority-construction earn-persistence list as the semantic
  identity rule.
- An owner binding as the default grain for an invocation-specific concern.
- A positive program relation emitted from `MULTIPLE_CANDIDATES` or
  `UNRESOLVED`.
- In-place rebuild as historical retention.
