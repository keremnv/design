# Semantic persistence contract

This document defines the v0 boundary between semantic construction and
durable semantic state. It is an application contract above the generic World
kernel. It complements [authority construction](AUTHORITY_CONSTRUCTION_CONTRACT.md),
[program comparison](SPINE_COMPARISON_CONTRACT.md), the [GovernanceCase
contract](GOVERNANCE_CASE_CONTRACT.md), and the [adjudication
contract](GOVERNANCE_ADJUDICATION_CONTRACT.md).

## Problem

An LLM, human, or deterministic resolver may make a semantic interpretation
once. The system must then decide deterministically whether that interpretation
is merely a construction result, a snapshot fact, an unresolved construction
question, or durable governed evidence with mechanically inspectable
maintenance dependencies.

The admission gate does not decide whether the interpretation is true. It
checks whether the proposed interpretation has the declared purpose, bounded
identities, inspectable grounding, admissible support, scope, completeness,
and maintenance shape required by the selected profile.

## Constructor versus admission

```text
semantic constructor
    -> SemanticCandidate
    -> deterministic validation
    -> deterministic persistence admission
    -> durable state, unresolvedness, or discard
```

`SemanticCandidate` is not a World assertion. The constructor cannot set an
admission outcome, confidence, trust score, renewal decision, or maintenance
result. Invalid candidates are `INVALID_CANDIDATE`; they are not epistemic
`UNRESOLVED` results.

## ConstructionObligation

`ConstructionObligation` is the narrow question that construction is allowed
to answer. v0 has four explicit, non-generic kinds: `PROGRAM_REALIZATION` for
a single manifestation, `PROGRAM_RELATIONSHIP` for the one bounded payment
path experiment, the experimental `PROGRAM_INVARIANT` for one scoped
universal claim, and `CLASS_MEMBERSHIP` for one supplied program
manifestation's membership in one named semantic class. All are represented
through an explicit semantic subject, expected relation, tuple role shape,
bounded program scope, allowed program endpoints, required evidence classes,
and a versioned admission profile.

An obligation is construction provenance, not semantic truth. A candidate must
reference the exact obligation. Incidental observations that do not discharge
it are valid construction observations but are deterministically dropped with
`DOES_NOT_DISCHARGE_OBLIGATION`.

## SemanticCandidate

A candidate contains:

- obligation and claim identity;
- relation and tuple;
- positive or negative polarity;
- semantic and program endpoint references;
- support kind and endpoint resolution;
- case-catalog evidence references;
- declared program scope;
- optional maintenance dependencies and completeness receipts.

The model-facing draft contains only aliases from a deterministic catalog.
Canonical IDs, evidence kinds, endpoint resolutions, candidate IDs, and
maintenance dependency records are compiled by runtime code.

## Model-facing construction projection

`build_semantic_construction_catalog()` creates a finite catalog for one
obligation. It aliases only the supplied semantic referents, program
endpoints, authoritative observations, program source, mechanical facts,
supporting material, maintenance dependencies, and completeness receipts.
Supporting material has its own category and cannot be selected in a
governing evidence field. The dynamic candidate schema enumerates the legal
aliases for each field; evidence kinds and endpoint resolutions are derived
from the catalog during compilation.

The model-facing evidence fields are structurally separate:
`authority_evidence_aliases`, `program_source_evidence_aliases`, and
`mechanical_evidence_aliases`. Their enums contain only aliases in the
case-scoped catalog, and `minItems` is applied to classes required by the
selected admission profile. The compiler still rechecks every alias and
derives durable evidence kinds from the catalog.

For the bounded `PROGRAM_RELATIONSHIP` profile, the catalog also carries a
trusted role signature derived from mechanically established spine kinds. In
the payment fixture, `checkout_entry`, `service_call_site`, and
`gateway_call_site` enumerate only `call_site` entities, while `service`,
`gateway`, and `provider` enumerate only `callable` or `method` entities.
These are structural restrictions only: semantic roles and the identity of
the gateway remain choices for the constructor. Compilation and final
candidate validation repeat the role-kind check, so provider structured
output is not the sole guard.

`construct_semantic_candidate()` reuses the provider-neutral governance
transport. Its input is the obligation, the catalog, and that dynamic schema;
it is not a repository-backed query. It performs at most two attempts. A
repair receives the same catalog and exact local validation errors. The
invocation receipt records provider metadata and template/catalog/schema
hashes without retaining hidden reasoning. The durable candidate is written
only after deterministic compilation passes.

## Candidate validation

Validation rejects unknown obligations, aliases, evidence, endpoints,
completeness receipts, or maintenance dependencies; tuple shapes that do not
match the obligation; unsupported reference resolution; and model-supplied
persistence fields. Known endpoints outside the obligation's allowed scope are
kept valid long enough for admission to produce `DROP / OUTSIDE_DECLARED_SCOPE`.

The dynamic construction schema enumerates only legal aliases for the specific
obligation and case. It does not expose repository access or an ontology query
language.

## PersistenceAdmissionDecision

The deterministic decision has four outcomes:

```text
DROP
RECORD_UNRESOLVED
PERSIST_SNAPSHOT_FACT
PERSIST_COMMITMENT
```

For `semantic-binding/v1` the matrix is:

| Condition | Outcome | Reason |
| --- | --- | --- |
| Relation, subject, or claim kind does not discharge the obligation | `DROP` | `DOES_NOT_DISCHARGE_OBLIGATION` |
| Program scope or endpoint is outside the obligation | `DROP` | `OUTSIDE_DECLARED_SCOPE` |
| Endpoint is ambiguous or unresolved | `RECORD_UNRESOLVED` | `AMBIGUOUS_ENDPOINT` |
| Support is `HYPOTHESIZED` | `RECORD_UNRESOLVED` | `HYPOTHESIZED_SUPPORT` |
| Required evidence class is absent, or program grounding is only an identity | `RECORD_UNRESOLVED` | `INSUFFICIENT_GROUNDING` |
| Negative candidate lacks a matching complete scoped receipt | `RECORD_UNRESOLVED` | `NEGATIVE_WITHOUT_COMPLETE_SCOPE` |
| Positive candidate is grounded but has no fully inspectable dependencies | `PERSIST_SNAPSHOT_FACT` | `GROUNDED_BUT_NO_INSPECTABLE_MAINTENANCE_DEPENDENCIES` |
| Positive candidate is grounded and all supplied dependencies are inspectable | `PERSIST_COMMITMENT` | `GROUNDED_WITH_INSPECTABLE_MAINTENANCE_DEPENDENCIES` |

No probabilistic threshold or confidence score is used.

## Evidence shape

An admitted durable positive program binding requires authority/semantic
grounding and program grounding beyond a bare program identifier. v0 accepts
bounded source or mechanical facts for the program side. A model label such as
`CROSS_EVIDENCE_INFERRED` cannot substitute for those evidence classes.

## Negative claims

```text
semantic absence + no matching scoped COMPLETE receipt
    != negative semantic fact
```

The gate records unresolvedness instead. A complete negative admission is
possible only when a supplied completeness receipt explicitly matches the
obligation scope or the semantic-program scope.

## Snapshot facts and commitments

`PERSIST_SNAPSHOT_FACT` admits a fact for the snapshot but does not create a
maintenance trigger. `PERSIST_COMMITMENT` admits the same kind of snapshot
fact plus a `semantic_commitment_warrant` application relation containing the
obligation, evidence, resolution basis, admission decision, and inspectable
dependencies.

Neither outcome makes the fact true in a future snapshot. A commitment at S0
plus correspondence to S1 never silently renews it.

For `PROGRAM_REALIZATION` under `semantic-binding/v1`, commitment
materialization uses the trusted typed relation
`semantic_program_realization(semantic_subject, program_manifestation)`. The
relation name and roles come from the obligation/profile mapping, never from
the candidate. A sealed baseline bundle is copied to writable staging, the
relation/assertion/warrant are inserted and contract-validated, and staging is
sealed and atomically published. Baseline and revision may therefore share a
program snapshot while differing in governed semantic knowledge; failed
publication leaves the baseline unchanged.

The bounded payment-path experiment adds one obligation/profile pair:
`PROGRAM_RELATIONSHIP` with `semantic-program-relationship/v1`. Its exact
tuple has two semantic roles (`access`, `boundary`) and six program roles
(`checkout_entry`, `service`, `service_call_site`, `gateway`,
`gateway_call_site`, `provider`). It is persisted through the trusted typed
relation `semantic_payment_access_path`.

This is a concrete bounded path commitment, not a universal path predicate.
The warrant lists selected program identities, exact `program_invokes`
tuples, and optional manifestation properties. Maintenance checks those
finite entries individually; it does not watch arbitrary payment paths or
run a graph query. The model-facing draft uses role-keyed endpoint objects for
this multi-role obligation so alias order cannot change tuple meaning.

The scoped-universal payment experiment adds the deliberately narrow
`PROGRAM_INVARIANT` / `semantic-program-invariant/v1` profile. Its trusted
World relation is `semantic_payment_provider_access_invariant(access,
boundary, scope_root)`. The assertion is scoped to a declared Checkout
provider-access universe; it does not mean that all payment code in a
repository satisfies the boundary. A complete receipt must enumerate the
baseline universe members by their case-scoped mechanical relation evidence.
That receipt establishes complete coverage of the declared S0 enumeration,
not a mechanism for discovering future members.

The invariant profile admits a positive commitment only when every enumerated
member is selected as mechanical evidence and appears in an inspectable finite
warrant. It does not add a wildcard dependency, graph query, or truth
evaluator. If a later candidate adds a relation not named by the S0 receipt,
finite maintenance can report changes to listed dependencies but cannot
establish that the new member belongs to the universal class. That is an
explicit experiment finding, not an implicit closed-world assumption.

That finding is now answered by a separate, still-narrow evaluator. Keep
the old finite invariant commitment as S0 evidence, and treat snapshot
truth as a `ScopedInvariantDefinition` plus a
`ScopedInvariantDerivation` for each program snapshot. See
[the scoped invariant evaluator](SEMANTIC_SCOPED_INVARIANT_EVALUATOR.md).
Do not copy S0 `TRUE` forward. Composer may establish the question;
deterministic evaluation establishes the current answer. Structural
call-graph completeness is not PaymentProvider membership completeness.
See the C3 circular-membership finding in that evaluator note, and the
follow-on [CLASS_MEMBERSHIP experiment](SEMANTIC_CLASS_MEMBERSHIP_EXPERIMENT.md)
for constructing and reusing a positive class-membership commitment.

## Commitment warrant and maintenance

The v0 warrant uses existing World relation and grounding mechanisms; no
generic kernel schema was changed. Its dependency kinds are deliberately
small: `program_identity`, `relation_tuple`, `structural_context`, and
`manifestation_property`.

Existing ProgramDelta/comparison machinery assesses each dependency as
`PRESERVED`, `CHANGED`, `LOST`, `UNKNOWN`, or `NOT_COMPARABLE`. Maintenance
reports the strongest affected status, never calls an LLM, never transfers the
assertion to the candidate endpoint, and never creates a negative semantic
fact. The S0 assertion remains in the S0 World.

Core v1 limitation (also applicable to this experiment): `PRESERVED` means
preservation of the explicitly recorded maintenance basis, not exhaustive
preservation of semantic truth. The system can inspect and reassess recorded
dependencies; it does not generally establish that they include every condition
on which the interpretation depends. Dependency adequacy remains the
constructor/application's responsibility.

The warrant is not a watch query and does not authorize semantic renewal. A
changed dependency produces a candidate-side affected or unknown status. It
does not copy the old assertion to the new endpoint, and it does not produce
the corresponding negative assertion.

## Lazy re-resolution

An affected commitment produces candidate-side unresolvedness. No new semantic
construction occurs automatically. A caller must explicitly create a new,
bounded `ConstructionObligation` for a candidate endpoint before construction
may run again.

This permits callers to target semantic work at selected unresolved questions.
It is not a demonstrated complexity bound or productivity advantage: selection
may scan commitments, and relevance depends on the adequacy of recorded bases.

## Storage boundaries

Construction obligations, candidates, admission decisions, invocation
receipts, `ScopedInvariantDefinition` records, and
`ScopedInvariantDerivation` records are application artifacts. Only admitted
semantic assertions and commitment warrants enter the governed World.
Rejected candidates and model scratch output are not semantic truth.
Chain-of-thought is never persisted. Snapshot derivations are not World
kernel types; if they are later materialized, use candidate → validate →
seal → atomic publish without mutating a sealed World.

The persistence helper re-runs the deterministic admission profile before
asserting anything. A caller-provided `PERSIST_*` receipt cannot bypass the
profile. A `RECORD_UNRESOLVED` result remains a construction decision and
question; it is never silently materialized as a guessed semantic tuple.

## Failure modes and non-goals

Provider failure, malformed output, and invalid candidate references remain
runtime or validation failures, not semantic `UNRESOLVED` facts. This v0 does
not implement automatic obligation generation, ontology discovery, resolver
plugins, semantic completeness inference, cross-project semantic libraries,
automatic renewal, background maintenance LLM calls, coding-agent integration,
or adoption workflow changes.

The design is falsified if deterministic admission must reinterpret semantic
truth, if maintenance dependencies require duplicating the semantic claim as a
hidden query language, or if snapshot and commitment semantics cannot remain
distinct in the existing World model.

## Maintenance comparison

These are the experimentally justified maintenance shapes. They are not a
generic resolver taxonomy.

```text
PROGRAM_REALIZATION

maintenance:
    finite dependency receipt


PROGRAM_RELATIONSHIP

maintenance:
    finite dependency receipt


PROGRAM_INVARIANT

maintenance:
    deterministic scoped re-derivation
```

Measured on the payment fixtures:

- `PROGRAM_RELATIONSHIP` S0 receipt: 6 program identities, 3
  `program_invokes` tuples, 3 manifestation dependencies, plus bounded
  structural context.
- old `PROGRAM_INVARIANT` S0 receipt: 10 identities, 5 relation tuples, 5
  manifestation dependencies, 1 structural dependency (**21** total). That
  receipt cannot name C1's new member.
- `checkout-provider-boundary/v1` S0 derivation: 2 members, 5 scoped invoke
  edges, overall `TRUE` when `chargeStripe` is independently classified.
  C1 derivation: 3 members, 7 scoped invoke edges, overall `FALSE`.
  C3 without an independent provider identity: structural `COMPLETE`,
  semantic membership not `COMPLETE`, overall `UNKNOWN`. Evaluation model
  invocations: **0**.

GovernanceCase assembly should prefer the current-snapshot derivation over
the old finite invariant warrant for candidate-state truth. The old warrant
remains useful S0 evidence.
