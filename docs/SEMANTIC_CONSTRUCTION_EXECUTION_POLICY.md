# Semantic construction execution policy (one required obligation)

This milestone adds the application-layer decision boundary after
`CONTEXT_REQUIRED` / `SEMANTIC_CONSTRUCTION` when exactly one
`ConstructionObligation` is required. It does not schedule, rank, batch,
retry, or run approval machinery.

## Workflow

```text
CONTEXT_REQUIRED
    kind = SEMANTIC_CONSTRUCTION
    required obligation = O1
        ↓
ConstructionExecutionPolicy
        ↓
ConstructionExecutionDecision

    EXECUTE
       ↓
    execute_construction_obligation(...)
       ↓
    SemanticCandidate / UNRESOLVED / FAILURE
       ↓
    existing admission (separate)
       ↓
    existing publication (separate)

    REQUIRE_APPROVAL
       ↓
    explicit ConstructionExecutionApproval
       ↓
    ConstructionExecutionAuthorization
       ↓
    existing guarded executor if AUTHORIZED

    DEFER
       ↓
    STOP
```

This is workflow state, not World truth.

```text
ConstructionObligation
        ↓
REQUIRED_FOR_CASE
        ↓
ConstructionExecutionDecision
```

`REQUIRED` is not `AUTO_ALLOWED`. A semantic question may block adoption and
still require approval or remain deferred.

## API

Trusted application configuration:

```python
ConstructionExecutionPolicy(
    profile_authorities={"semantic-class-membership/v1": "AUTO_ALLOWED"},
)
```

Decision:

```python
decide_construction_execution(
    required_obligations,
    policy=policy,
    resource_permission="AVAILABLE",  # or UNAVAILABLE
)
```

Execution, only after `action == EXECUTE`:

```python
execute_construction_obligation(
    obligation,
    execution_decision,
    constructor=transport,
    case=case,
    ...
)
```

The executor calls the existing pipeline:

```text
ConstructionObligation
    ↓
build_semantic_construction_catalog
    ↓
model-facing schema
    ↓
constructor
    ↓
SemanticCandidate
```

It does not admit, persist, or publish. `max_attempts = 1`.

## Decision shape

`ConstructionExecutionDecision`

```text
decision_id
obligation_id
action            EXECUTE | REQUIRE_APPROVAL | DEFER
status            DECIDED | NOT_REQUIRED | MULTIPLE_REQUIRED_OBLIGATIONS_UNSUPPORTED
policy_id
policy_version
reason
construction_profile
execution_authority
resource_permission
constructor_id
required_obligation_ids
constructor_invoked = false
model_invoked = false
```

`EXECUTE` means the workflow authorizes execution of this obligation under
the declared construction policy. It does not mean a constructor ran, a
model was called, semantic truth was established, persistence was admitted,
or the candidate may proceed.

Zero required obligations: `NOT_REQUIRED`. More than one:
`MULTIPLE_REQUIRED_OBLIGATIONS_UNSUPPORTED`. The policy does not choose,
rank, or execute any of them.

## Authority and resources

Construction authority is application configuration, not World knowledge:

```text
AUTO_ALLOWED
APPROVAL_REQUIRED
DISALLOWED
```

Resource permission is a separate bounded input:

```text
AVAILABLE
UNAVAILABLE
```

Deterministic mapping:

```text
AUTO_ALLOWED + AVAILABLE     -> EXECUTE
APPROVAL_REQUIRED + AVAILABLE -> REQUIRE_APPROVAL
AUTO_ALLOWED + UNAVAILABLE   -> DEFER
DISALLOWED                   -> DEFER
no configured constructor    -> DEFER
```

`semantic-class-membership/v1` maps to the existing semantic constructor.
There is no model routing.

`REQUIRE_APPROVAL` is a policy outcome only. The decision is not rewritten
to `EXECUTE`. Exact one-shot workflow approval is a later contract:
[semantic construction execution approval](SEMANTIC_CONSTRUCTION_APPROVAL.md).

`DEFER` is not failure. The candidate remains `CONTEXT_REQUIRED`. The
obligation is not marked failed, rejected, or impossible.

Policy evaluation does not mutate the obligation, GovernanceCase, candidate
decision, World, or semantic commitment state.

## Execution results

`ConstructionExecutionResult`

```text
CANDIDATE_PRODUCED        valid SemanticCandidate produced
SEMANTICALLY_UNRESOLVED   constructor legitimately answered UNRESOLVED
EXECUTION_FAILED          operational/schema/tool execution failed
```

UNRESOLVED is not EXECUTION_FAILED. A produced MEMBER candidate still needs
existing deterministic admission. Admission still needs existing publication
to change a governed World.

## Control vs live

Deterministic MEMBER control:

```text
C3 + G0  CONTEXT_REQUIRED
    ↓ EXECUTE + fixture constructor
SemanticCandidate MEMBER
    ↓ admit
PERSIST_COMMITMENT
    ↓ new governed World G1
same C3 + G1  READY_FOR_ADJUDICATION
```

Candidate tree, candidate program snapshot, and baseline program snapshot
remain unchanged. Only governed semantic knowledge may change.

Live Composer, if opted in with `ONTOLOGY_AUTHOR_LIVE_CONSTRUCTION`, is a
separate path. A live `UNRESOLVED` result is `SEMANTICALLY_UNRESOLVED` and
does not retry.

## Tests

`tests/test_construction_execution_policy.py`

The next experiment, when several obligations are required, is
[incremental semantic acquisition](SEMANTIC_CONSTRUCTION_CYCLE.md): at most
one authorized construction per cycle, then recompute materiality.

Exact one-shot approval for `REQUIRE_APPROVAL` is
[semantic construction execution approval](SEMANTIC_CONSTRUCTION_APPROVAL.md).
