# Incremental semantic acquisition (one construction per cycle)

This experiment tests whether required semantic work is dynamic. When several
obligations currently block a case, the application executes **at most one**
authorized construction, publishes any admitted commitment, and recomputes
case materiality before spending intelligence again.

It is not a scheduler, not semantic ranking, and not a batch executor.

## Workflow

```text
required = [O1, O2, O3]
    ↓
select one eligible obligation deterministically
    ↓
execute at most one
    ↓
admit/publish if appropriate
    ↓
reevaluate SAME candidate
    ↓
recompute readiness/materiality
    ↓
only then consider another obligation
```

API:

```python
advance_semantic_construction_cycle(...)
    -> SemanticConstructionCycleResult
```

One invocation never recursively continues into another obligation.

## Cycle status

```text
NO_CONSTRUCTION_REQUIRED
CONSTRUCTION_ATTEMPTED
APPROVAL_REQUIRED
DEFERRED
```

If readiness is already `READY_FOR_ADJUDICATION`, the cycle returns
`NO_CONSTRUCTION_REQUIRED` and does not inspect dormant work.

## Canonical selection

If more than one required obligation is `AUTO_EXECUTABLE`, the cycle sorts by
`obligation_id` and takes the first.

> This ordering is for reproducibility only. It is not a claim that this
> obligation is more important, more likely to resolve the case, or
> semantically preferable.

Selection does not inspect source text, model confidence, endpoint names,
likely truth value, token cost, or semantic content.

`canonical selection != semantic ranking`.

## Authority mixture

Authorization is evaluated **per obligation**. An `AUTO_ALLOWED` required
obligation may run even if another required obligation is
`REQUIRE_APPROVAL`. After publication, re-readiness decides whether the
approval-required work remains material.

If no required obligation is auto-executable and one or more require
approval, the cycle returns `APPROVAL_REQUIRED` for the canonically selected
obligation. It does not bulk-approve. An exact
`ConstructionExecutionAuthorization` for that one decision may then execute
that obligation; see
[semantic construction execution approval](SEMANTIC_CONSTRUCTION_APPROVAL.md).

If none are executable or approval-capable, the cycle returns `DEFERRED`.

## Execution, admission, publication

These remain separate contracts. The cycle may coordinate them:

```text
EXECUTE
    ↓ existing guarded executor (max_attempts = 1)
SemanticCandidate / UNRESOLVED / FAILURE

UNRESOLVED or FAILURE
    ↓ stop; do not select O2

CANDIDATE_PRODUCED
    ↓ existing admission

PERSIST_COMMITMENT
    ↓ existing World revision
    ↓ reevaluate same candidate against G1

RECORD_UNRESOLVED / DROP
    ↓ stop
```

`constructor_attempts <= 1` per cycle.

## Prior UNRESOLVED

If the caller supplies same-obligation, same-profile, same-material-basis
`SEMANTICALLY_UNRESOLVED` provenance, that obligation is not auto-executable.
That is not a generic retry ledger. A later snapshot-scoped obligation
(`O1@C3b` vs `O1@C3`) is a new question.

## After READY_FOR_ADJUDICATION

The cycle may report `next = ADJUDICATION`. It does not invoke the
adjudicator. The caller resumes the existing candidate lifecycle.

## Tests

`tests/test_semantic_construction_cycle.py`

Exact one-shot approval for a cycle that currently returns
`APPROVAL_REQUIRED` is
[semantic construction execution approval](SEMANTIC_CONSTRUCTION_APPROVAL.md)
(`tests/test_construction_execution_approval.py`).
