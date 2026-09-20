# Semantic construction as candidate `CONTEXT_REQUIRED`

This milestone integrates deterministic case readiness into the governed
candidate lifecycle. It does not execute `ConstructionObligation`s, invoke
Composer, or change `AdoptionPolicy` semantics.

## Workflow

```text
CASE ASSEMBLED
    ↓
READINESS

    ├── CONSTRUCTION_REQUIRED
    │       ↓ skip adjudication
    │   CONTEXT_REQUIRED
    │   kind = SEMANTIC_CONSTRUCTION
    │   [required semantic obligation IDs]
    │
    └── READY_FOR_ADJUDICATION
            ↓
        ADJUDICATION
            ↓
        ADOPTION POLICY
            ↓
        ADOPT
        REVISION_REQUIRED
        APPROVAL_REQUIRED
        CONTEXT_REQUIRED   # kind = ADJUDICATION_CONTEXT
        ESCALATE

CONTEXT_REQUIRED / SEMANTIC_CONSTRUCTION
    (exactly one required ConstructionObligation)
        ↓
    ConstructionExecutionPolicy
        ↓
    EXECUTE | REQUIRE_APPROVAL | DEFER
            ↓
    REQUIRE_APPROVAL → ConstructionExecutionApproval
                    → ConstructionExecutionAuthorization
                    → guarded executor if AUTHORIZED
```

See [semantic construction execution approval](SEMANTIC_CONSTRUCTION_APPROVAL.md).

API: `evaluate_assembled_candidate_case(...)`.
`evaluate_git_candidate(..., pending_obligations=...)` uses the same branch
when pending obligations are supplied.

## Two CONTEXT_REQUIRED paths

| | Semantic construction | Adjudicator context |
|---|---|---|
| Readiness | `CONSTRUCTION_REQUIRED` | `READY_FOR_ADJUDICATION` |
| Adjudicator invoked | no | yes |
| `context_requirement.kind` | `SEMANTIC_CONSTRUCTION` | `ADJUDICATION_CONTEXT` |
| Reason | `REQUIRED_SEMANTIC_CONSTRUCTION` | `ADJUDICATOR_INSUFFICIENT_CONTEXT` |
| Payload | required obligation IDs, gap IDs, derivation IDs, causal chain | `ContextRequest[]` |
| Coding-agent revision brief | none | none (expansion is not source revision) |

`CONTEXT_REQUIRED` is a workflow action, not semantic truth, conformance, or
decision right. Returning it does not mark obligations running, selected,
failed, or resolved.

## Knowledge revision vs program revision

```text
program snapshot:     unchanged
governed semantic World: may advance after construction (G0 → G1)
candidate:            unchanged
reevaluation:         same program candidate, same S0 baseline,
                      richer governed knowledge
```

Example:

```text
C3 + G0  → CONTEXT_REQUIRED (PaymentProvider(settleExternal))
resolve membership → G1
same C3 + G1 → FALSE → READY_FOR_ADJUDICATION → existing adjudication
```

No candidate code changed. S0 remains the program baseline.

After `CONTEXT_REQUIRED` / `SEMANTIC_CONSTRUCTION` with exactly one required
obligation, [execution policy](SEMANTIC_CONSTRUCTION_EXECUTION_POLICY.md)
decides whether that obligation may run, must be approved, or must wait.
Execution, admission, and publication remain later steps.

## Tests

`tests/test_governed_candidate_semantic_context.py`
