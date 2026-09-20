# Semantic construction execution approval

This milestone adds an explicit, one-shot workflow approval for a
`ConstructionExecutionDecision` whose action is `REQUIRE_APPROVAL`. It does
not add an approval UI, identities, notifications, queues, or a generic
permission platform.

Approval answers only:

```text
May we spend intelligence to answer this exact semantic question,
once, under this exact execution-policy decision?
```

It does not answer:

```text
May this program candidate be adopted?
```

Those are different authority questions. Candidate-adoption
`APPROVAL_REQUIRED` remains on `CandidateAdoptionDecision`. Construction
execution approval is `ConstructionExecutionApproval`.

## Meaning

```text
execution approval
    !=
semantic truth
    !=
semantic admission
    !=
candidate approval
```

`APPROVED` means the named constructor may be attempted once for this exact
`ConstructionObligation` and this exact `ConstructionExecutionDecision`. It
does not mean:

* `PaymentProvider(x)` is true;
* the eventual `SemanticCandidate` should persist;
* the constructor will succeed;
* the candidate is approved for adoption;
* conformance is approved;
* the generated semantic answer is trusted automatically.

## Workflow

```text
ConstructionObligation
        ↓
case materiality
        ↓
execution policy
        ↓

AUTO_ALLOWED
    -> execution authorization inherent in EXECUTE

APPROVAL_REQUIRED
    -> explicit ConstructionExecutionApproval
    -> ConstructionExecutionAuthorization
    -> guarded execution if AUTHORIZED

DEFER / DISALLOWED
    -> stop; approval cannot override
```

The original policy decision is immutable. A valid approval does not rewrite:

```text
ConstructionExecutionDecision(action = REQUIRE_APPROVAL)
```

into `EXECUTE`. Authorization is a later, separate result:

```text
policy decision: REQUIRE_APPROVAL
        +
valid explicit approval
        ↓
execution authorization: AUTHORIZED
```

That preserves why approval was required.

## Artifacts

Application/workflow state only. Not World kernel types. Not domain claims.

`ConstructionExecutionApproval`

```text
approval_id
execution_decision_id
obligation_id
policy_id
policy_version
approved_constructor_id
scope           ONE_EXECUTION_ATTEMPT
decision        APPROVED | DENIED
source          explicit external approval provenance
created_at / metadata
kind            CONSTRUCTION_EXECUTION_APPROVAL
```

`ConstructionExecutionAuthorization`

```text
status          AUTHORIZED | NOT_AUTHORIZED | DENIED
obligation_id
execution_decision_id
approval_id
constructor_id
max_attempts    1
reason
```

API:

```python
approval = construction_execution_approval(decision, outcome="APPROVED")
authorization = authorize_construction_execution(
    decision,
    approval,
    consumed_approval_ids=(),
)
execute_construction_obligation(
    obligation,
    decision,
    constructor=transport,
    case=case,
    execution_authorization=authorization,
    consumed_approval_ids=(),
)
```

Authorization itself does not invoke a constructor.

## Exact binding

An approval must match the `REQUIRE_APPROVAL` decision on:

```text
approval.execution_decision_id == decision.decision_id
approval.obligation_id         == decision.obligation_id
approval.policy_id/version     == decision.policy_id/version
approval.approved_constructor_id == configured constructor
approval.scope                 == ONE_EXECUTION_ATTEMPT
```

There is no wildcard, bulk, or class-wide approval. These remain distinct:

```text
PaymentProvider(endpointA@C1)
PaymentProvider(endpointB@C1)
PaymentProvider(endpointA@C2)
```

An approval for `PaymentProvider(settleExternal@C3)` cannot authorize
`PaymentProvider(settleExternal@C3b)`.

## One-shot consumption

`max_attempts = 1`. After one construction attempt, the caller records the
approval id as consumed. The same approval does not authorize another
attempt. There is no approval database or scheduler; consumption is an
explicit argument on the authorization/executor contract.

## Executor guard

Execution is legal when either:

```text
A. decision.action == EXECUTE

B. decision.action == REQUIRE_APPROVAL
   and authorization.status == AUTHORIZED
   and the authorization binds to this decision/obligation
   and the approval id is not consumed
```

All other cases reject before constructor invocation.

`EXECUTE` does not fabricate an approval. `DEFER` cannot be overridden.
`DISALLOWED` cannot be approved around. `DENIED` means do not execute this
construction under this approval request; it does not invalidate the
semantic question, resolve the obligation, reject the candidate, or forbid a
later different policy/decision.

## Approval is not semantic evidence

The constructor receives the same bounded semantic question/evidence package
it would have received under `AUTO_ALLOWED` execution. Approval provenance
is never catalog evidence, prompt evidence, or support for `MEMBER`.

## Live result semantics

Unchanged:

```text
UNRESOLVED        -> SEMANTICALLY_UNRESOLVED
EXECUTION_FAILED  -> EXECUTION_FAILED
MEMBER candidate  -> still requires deterministic admission
```

Approval does not strengthen a semantic result. The executor still does not
publish. World knowledge changes only after admitted publication.

## Incremental re-materiality

If several required obligations currently need approval, one cycle returns
the canonically selected `REQUIRE_APPROVAL` decision. Approving that one
obligation does not approve the others. After a published decisive
construction, remaining obligations may become dormant and then never need
approval.

## Audit chain

```text
required ConstructionObligation
    ↓
ConstructionExecutionDecision(REQUIRE_APPROVAL)     workflow policy
    ↓
ConstructionExecutionApproval(APPROVED)             workflow authority
    ↓
ConstructionExecutionAuthorization(AUTHORIZED)      workflow authority
    ↓
ConstructionExecutionResult                         semantic construction
    ↓
SemanticCandidate
    ↓
PersistenceAdmissionDecision                        deterministic admission
```

## Tests

`tests/test_construction_execution_approval.py`

This is not a generic approvals platform. It is the smallest contract that
lets application policy withhold automatic construction while still allowing
an exact, one-shot human/application authorization of that construction.
