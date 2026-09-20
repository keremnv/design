# GovernanceCase readiness: pending vs required construction

This milestone tests whether formulated `ConstructionObligation`s can be
kept as valid pending semantic questions while only the subset that
materially blocks the current `GovernanceCase` is demanded.

It does not execute construction, invoke Composer, or adjudicate.

## Lifecycle

```text
DETECTION
    deterministic consumer exposes missing fact
        ↓
FORMULATION
    deterministic synthesis expresses a bounded ConstructionObligation
        ↓
MATERIALITY
    GovernanceCaseReadiness decides whether that obligation
    is required for this case
        ↓
[execution policy for exactly one required obligation]
```

An obligation means the question could be resolved. It does not mean it
must be resolved now.

```text
PENDING
    valid unresolved ConstructionObligation exists

REQUIRED
    pending obligation is material to resolving this case

DORMANT
    pending obligation exists but current case does not require it
```

These are workflow views. They are not persisted as semantic truth.
Dormant obligations are not deleted, resolved, or executed.

## API

```text
assess_governance_case_readiness(
    pending_obligations=...,
    derivation=...,
    case=...,
) -> GovernanceCaseReadiness

status:
    READY_FOR_ADJUDICATION
    CONSTRUCTION_REQUIRED
```

`READY_FOR_ADJUDICATION` is not `CONFORMS`, `ADOPT`, or `DELEGATED`. It
means only that material semantic inputs are already established enough
to enter the existing adjudication stage.

When status is `CONSTRUCTION_REQUIRED`, `required_construction_obligations`
references already synthesized obligations. It does not invent a second
semantic question.

Optional `ConstructionRequired` is the same bounded required list. It
documents that this result could later map to adoption-policy
`CONTEXT_REQUIRED` without implementing that policy change here.

Case overlay, identity-preserving:

```text
construction_context:
    pending_obligation_ids
    required_obligation_ids
    dormant_obligation_ids
    readiness_status
```

Full obligation objects stay outside the case.

Readiness consumes gaps and already synthesized obligations. It does not
synthesize as a side effect.

## Materiality rule

Consumer: `checkout-provider-boundary/v1` only.

```text
any known VIOLATES  -> overall FALSE  -> membership gaps are not required
COMPLETE + all SATISFIES -> overall TRUE -> no membership construction
otherwise -> overall UNKNOWN
    supported MembershipGaps that have formulated CLASS_MEMBERSHIP
    obligations are required
```

`CLASS_MEMBERSHIP` does not always block governance. Known `FALSE`
suppresses unrelated unknown memberships.

Unsupported or non-membership UNKNOWN (for example incomplete structural
enumeration with no `MembershipGap`) does not fabricate CLASS_MEMBERSHIP
work.

## Causal chain

```text
GovernanceCase
    ↓ needs
ScopedInvariantDerivation
    ↓ UNKNOWN because
MembershipGap
    ↓ formulated as
ConstructionObligation
```

## CONTEXT_REQUIRED mapping

Implemented as a pre-adjudication orchestration branch, not an AdoptionPolicy
rewrite. See
[Semantic construction as candidate CONTEXT_REQUIRED](SEMANTIC_CANDIDATE_CONTEXT_REQUIRED.md)
and
[Semantic construction execution policy](SEMANTIC_CONSTRUCTION_EXECUTION_POLICY.md).

## Tests

`tests/test_governance_case_readiness.py` covers C3/C3a/C3b/C4, three-unknown
fan-out with and without a known violation, duplicate-consumer identity,
inspectable causal chain, no adjudicator/constructor/model/search, READY ≠
CONFORMS/ADOPT, unsupported gaps, and no World-kernel coupling.
