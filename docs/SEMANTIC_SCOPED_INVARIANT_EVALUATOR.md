# Checkout-provider-boundary/v1 scoped invariant evaluator

This milestone implements the smallest deterministic mechanism that can
re-derive the Checkout payment-provider boundary invariant for each program
snapshot. It is not a generic resolver, query language, or obligation
generator.

The prior scoped-universal experiment showed:

```text
PROGRAM_REALIZATION
    finite dependency receipt works

PROGRAM_RELATIONSHIP
    finite dependency receipt works

PROGRAM_INVARIANT
    finite receipt can persist S0 truth
    but cannot discover new C1 members
```

This evaluator answers that last gap by persisting the semantic question and
re-deriving membership plus truth from the current bounded program spine.

A follow-on pressure test then showed that structural call-graph completeness
does not establish PaymentProvider membership completeness. Evaluator version
2 records that distinction. It does not add a second invariant, a class
primitive, or a generic resolver.

## Architectural distinction

```text
PROGRAM_REALIZATION / PROGRAM_RELATIONSHIP

semantic truth at S0
+
finite SemanticCommitmentWarrant
    ↓
future maintenance checks known dependencies
```

versus:

```text
PROGRAM_INVARIANT

durable invariant definition
    +
deterministic snapshot evaluator
    ↓
derive membership + truth for each snapshot
```

Do not maintain old `TRUE` across snapshots. Persist what semantic question
must remain answerable, then derive what the answer is for snapshot S.

The existing `semantic_payment_provider_access_invariant` commitment and
`SemanticCommitmentWarrant` remain historical S0 evidence. They are not
deleted. Future GovernanceCase assembly should prefer:

```text
ScopedInvariantDefinition          durable question
ScopedInvariantDerivation(S)       authoritative current-state result
```

over the old finite invariant warrant for candidate-state truth.

## ScopedInvariantDefinition

Application record `scoped_invariant_definition/v0`. For this experiment it
represents only `checkout-provider-boundary/v1`.

```text
id
definition_kind = CHECKOUT_PROVIDER_BOUNDARY
version = 2
authority_refs
access_semantic:     semantic:CheckoutProviderAccess
boundary_semantic:   semantic:PaymentGatewayBoundary
scope_root           construction-time Checkout program identity
scope_root_descriptor
boundary_program     construction-time PaymentGateway program identity
boundary_program_descriptor
provider_semantic    optional persisted PaymentProvider semantic identity
provider_programs    construction-time PaymentProvider program identities
provider_descriptors
snapshot_id          construction provenance
evaluator_id:        checkout-provider-boundary/v1
```

The definition is durable semantic configuration. It carries no
`overall_truth`. Composer may still be used during construction to establish
the access, boundary, Checkout scope, and independently known provider
identities. Composer does not decide whether current accesses satisfy the
invariant, and it is not invoked during snapshot evaluation.

`boundary_program` is a trusted construction parameter. Evaluation does not
infer PaymentGateway from names such as `throughGateway`.

`provider_programs` / `provider_semantic` are the only independent
PaymentProvider evidence this evaluator accepts. They are not inferred from
PaymentGateway reachability, identifier spelling, or package names.

## Evaluator API

```python
evaluate_checkout_provider_boundary(
    program_world,
    invariant_definition,
) -> ScopedInvariantDerivation
```

There is no plugin registry. The function refuses any other evaluator id.

Every derivation records `model_invoked = false`,
`repository_searched = false`, and `name_classified = false`. Current-snapshot
IDs are resolved from the definition's construction-time identities, or from
the stored identity descriptors when the snapshot-local IDs have changed.

## Two completeness questions

```text
A. structural enumeration completeness

Have we enumerated all relevant current program edges/paths
under the Checkout scope?
```

```text
B. semantic membership completeness

Can we determine which reachable/new endpoints belong to
the semantic class PaymentProvider?
```

`spine.calls/v1 = COMPLETE` may establish A. It does not establish B.

A universal result may be `TRUE` only when both forms of completeness needed
by this invariant are established.

```text
CURRENT PROGRAM SCOPE
        ↓
structural candidate access enumeration
        ↓
semantic class membership
        ↓
provider-access universe
        ↓
boundary mediation evaluation
```

These stages stay distinct. For every structurally reachable candidate
endpoint:

```text
IS_PROVIDER
IS_NOT_PROVIDER
UNKNOWN
```

Absence of independent evidence is `UNKNOWN`, not `IS_NOT_PROVIDER`.

## Historical finding: circular membership

Evaluator version 1 identified providers approximately as:

```text
callables reachable from PaymentGateway
```

That rule was circular:

> a callable is recognized as a PaymentProvider partly because it is already
> reachable through the boundary whose universal use we are trying to verify.

The C3 candidate was evaluated against that unchanged rule before any
correction. C3 adds:

```text
Checkout
    -> checkoutAlternative
    -> settleExternal
```

`settleExternal` is not reachable from PaymentGateway in S0, is not named by
the S0 finite invariant receipt, and is not inferred from its identifier.
The existing mediated Stripe path is retained.

Pre-correction C3/C4 derivations:

| Snapshot | Enumerated members | Provider classification | Completeness | Overall |
| --- | --- | --- | --- | --- |
| C3 | `authorize`, `authorizeRetry` only; `checkoutAlternative` omitted | `chargeStripe` only, because PaymentGateway reaches it | COMPLETE | TRUE |
| C4 | `authorize`, `authorizeRetry` only; `recordAudit` omitted | `chargeStripe` only | COMPLETE | TRUE |

That is a false `TRUE`. It is recorded as:

```text
SEMANTIC_MEMBERSHIP_COMPLETENESS_UNSOUND
```

`StripeClient` / `chargeStripe` was a PaymentProvider in version 1 only
because PaymentGateway reached it. That is not independent semantic
classification.

`spine.calls/v1 COMPLETE`, a gateway that reaches at least one provider, and
resolved scoped calls established a complete Checkout call graph under this
mechanical profile. They did not establish a complete Checkout
PaymentProvider access universe.

## Scope-membership algorithm

Mechanical profile only: `checkout-provider-boundary/v1` over this fixture's
TypeScript program spine. It does not recognize arbitrary payment
architectures.

1. Read `program_invokes`, `structural_context`, `program_entity_kind`,
   `program_identity_descriptor`, `program_resolution`, and
   `program_capability` from the supplied program World. Optionally read
   persisted `semantic_program_realization` rows when the definition names a
   `provider_semantic`.
2. Locate Checkout (`scope_root`) and PaymentGateway (`boundary_program`).
3. Build an invoke graph: each resolved `program_invokes(call_site, target)`
   becomes an edge from the call site's containing callable/method to
   `target`.
4. Walk only from Checkout. Do not search the repository or the rest of the
   program graph except along those scoped invoke edges.
5. Structural candidate endpoints are scoped leaves excluding Checkout and
   PaymentGateway.
6. Classify each candidate independently:
   * `IS_PROVIDER` if it matches a construction-time `provider_programs`
     identity/descriptor, or a persisted `semantic_program_realization` of
     `provider_semantic`;
   * otherwise `UNKNOWN`.
7. Gateway reachability is recorded as a diagnostic. It is not a membership
   classifier.
8. A member is a Checkout-originating first hop that reaches an independently
   classified provider, an endpoint whose provider membership is unknown, or
   an unresolved Checkout first hop that cannot be classified.

S0 members remain the `authorize` and `authorizeRetry` first hops. The five
in-scope `program_invokes` edges are the structural universe evidence,
matching the prior experiment's enumerated relation receipt.

## Mediation-evaluation algorithm

For each member whose callee is `T`:

```text
VIOLATES
    a resolved path from T reaches an independently classified
    PaymentProvider without visiting PaymentGateway

SATISFIES
    every resolved path from T to an independently classified
    PaymentProvider traverses PaymentGateway
    and the member subgraph has no unresolved calls

UNKNOWN
    available mechanical facts cannot determine mediation
    including unresolved Checkout first hops, unresolved subgraphs
    that may still be provider access, and first hops that reach an
    endpoint whose PaymentProvider membership is UNKNOWN
```

Names such as `checkoutDirect`, `chargeStripe`, `settleExternal`, or
`recordAudit` are not classifiers.

## Completeness rules

Each snapshot gets its own universe receipt. Completeness is
multidimensional for this evaluator only:

```text
structural_enumeration
    COMPLETE when spine.calls/v1 is COMPLETE or STATIC_COMPLETE
    and every scoped call site has a resolved program_invokes edge

semantic_membership
    COMPLETE when every structural candidate endpoint is independently
    classified as IS_PROVIDER
    UNKNOWN/INCOMPLETE when any candidate is UNKNOWN

invariant-universe completeness
    COMPLETE only when both of the above are COMPLETE
```

`TRUE` requires that combined completeness. `FALSE` does not: one proven
unmediated provider access falsifies the universal even when some other
endpoint remains `UNKNOWN`.

Version 1's extra requirement that PaymentGateway reach at least one
provider is not a structural-enumeration fact. It was the circular
membership rule.

## Three-valued aggregation

```text
if any member == VIOLATES:
    overall = FALSE

elif universe completeness == COMPLETE
and every member == SATISFIES:
    overall = TRUE

else:
    overall = UNKNOWN
```

One known violation falsifies the universal even when coverage is incomplete.
An `UNKNOWN` member yields overall `UNKNOWN` unless a violation already
established `FALSE`.

## Membership evidence sources

Legitimate for this evaluator:

```text
construction-time provider identities on the definition
persisted semantic_program_realization of provider_semantic
source-native program identity descriptors used only to relocate
    those already-named identities across snapshots
```

Not legitimate:

```text
identifier contains "Provider"
package name sounds like Stripe
LLM guess during evaluation
PaymentGateway reachability
repository search
```

The payment fixture does not persist
`semantic:PaymentProvider realized_by program:chargeStripe`. After the
correction, `chargeStripe` is `IS_PROVIDER` because construction listed that
program identity on the definition, the same way it lists Checkout and
PaymentGateway. That is independent of gateway traversal. If construction
omits every provider identity, S0 is not `TRUE`.

Absence of such a binding remains `UNKNOWN`. The evaluator does not perform
lazy semantic construction to close that gap.

## Measured snapshot derivations

Model invocation count during evaluation: **0** for S0, C1, C2, C3, C4, and
the incomplete controls.

| Snapshot | Structural | Semantic membership | Combined | Members | Overall |
| --- | --- | --- | --- | --- | --- |
| S0, independent `chargeStripe` | COMPLETE | COMPLETE | COMPLETE | 2 SATISFIES (`authorize`, `authorizeRetry`) | TRUE |
| C1 | COMPLETE | COMPLETE | COMPLETE | 2 SATISFIES + 1 VIOLATES (`checkoutDirect`) | FALSE |
| C2 | COMPLETE | COMPLETE | COMPLETE | 3 SATISFIES (`authorize`, `authorizeRetry`, `checkoutWallet`) | TRUE |
| incomplete, no violation | not COMPLETE | — | not COMPLETE | SATISFIES + UNKNOWN | UNKNOWN |
| incomplete + known bypass | not COMPLETE | — | not COMPLETE | includes VIOLATES | FALSE |
| C3, no extra provider identity | COMPLETE | not COMPLETE (`settleExternal` UNKNOWN) | not COMPLETE | SATISFIES + UNKNOWN (`checkoutAlternative`) | UNKNOWN |
| C3, independent `settleExternal` | COMPLETE | COMPLETE | COMPLETE | includes VIOLATES (`checkoutAlternative`) | FALSE |
| C4 | COMPLETE | not COMPLETE (`recordAudit` UNKNOWN) | not COMPLETE | SATISFIES + UNKNOWN (`recordAudit`) | UNKNOWN |
| S0 without provider identities | COMPLETE | not COMPLETE | not COMPLETE | no independently classified providers | not TRUE |

C1's `checkoutDirect` member is discovered from the current C1 spine. The
evaluator is not given the S0 member receipt. The new member's identity
descriptor is absent from every S0 member. That remains the central discovery
proof:

```text
old finite receipt cannot name the new relation
deterministic scoped re-derivation can
```

C2 proves the same discovery path for a correctly mediated addition.
Overall remains TRUE only because `chargeStripe` is independently classified
and no new unclassified endpoint appears.

C3 without an extra provider identity does **not** become FALSE. That is
correct: the next problem is semantic-class construction, not invariant
evaluation. C3 becomes FALSE only when construction independently names
`settleExternal` as a PaymentProvider.

## GovernanceCase integration

`assemble_governance_case` accepts an optional selected invariant:

```text
invariant_definition
baseline_invariant_derivation
candidate_invariant_derivation
```

When supplied, the case includes `invariant_context`:

```text
AUTHORITY
    All payment-provider access from Checkout
    must go through PaymentGateway.

INVARIANT DEFINITION
    CheckoutProviderAccess
    boundary = PaymentGatewayBoundary
    scope = Checkout

BASELINE DERIVATION
    snapshot = S0
    overall = TRUE
    universe COMPLETE
    members = authorize, authorizeRetry

CANDIDATE DERIVATION
    snapshot = C1
    overall = FALSE
    new member = checkoutDirect
    mechanical evidence = program_invokes path
```

Candidate derivation invoke facts are copied into
`program_context.relation_tuples` so the existing adjudicator catalog can
cite them as `MECHANICAL_PROGRAM_FACT`. No Composer, no repository search,
no absence interpretation: the candidate derivation is a positive current
snapshot result.

The existing adjudication contract is unchanged. An observational
deterministic check can record a `MECHANICAL` program finding against those
evidence IDs. Prompts were not tuned to force `CONFLICTS`.

## Comparison with realization/relationship maintenance

These sizes are fixture-specific. They are not a claim of universality.

| Kind | Maintenance | Measured S0 surface |
| --- | --- | --- |
| `PROGRAM_REALIZATION` | finite dependency receipt | cancellation commitment: identity + manifestation + local relation dependencies |
| `PROGRAM_RELATIONSHIP` | finite dependency receipt | 6 path identities, 3 `program_invokes` tuples, 3 manifestation dependencies, plus bounded structural context |
| `PROGRAM_INVARIANT` (old) | finite member receipt | 10 identities, 5 relation tuples, 5 manifestation dependencies, 1 structural dependency; **21** total. Cannot discover C1's new member |
| `PROGRAM_INVARIANT` (this evaluator) | deterministic scoped re-derivation | S0: 2 members / 5 scoped edges. C1: 3 members / 7 scoped edges. Model calls: 0 |

## Falsification findings

Reported, not patched by broadening the architecture:

- Enumerating this scope did **not** require a graph-query language. The
  algorithm is a bounded invoke-graph walk from Checkout.
- Structural `COMPLETE` is defined from spine.calls receipts and unresolved
  call sites, not LLM judgment.
- Provider membership **must not** be established solely by PaymentGateway
  reachability if that membership is then used to prove that all providers
  are reached through PaymentGateway. Version 1 did this. Version 2 does
  not.
- Independent membership currently comes from construction-time identities
  on the definition, optionally from persisted
  `semantic_program_realization`. The governed World in this fixture does
  not already contain a reusable PaymentProvider class projection.
- Unknown membership remains open-world. It prevents `TRUE`. It does not
  become `IS_NOT_PROVIDER` or `FALSE`.
- A known unmediated provider access remains `FALSE` even when other
  endpoints are unclassified or the structural universe is incomplete.
- Candidate derivations reproduce from program-spine facts plus the durable
  definition. No model, no repository search, no identifier classification.
- GovernanceCase consumed evaluator output without adjudication redesign.
- Evaluation does not read raw repository state. It reads the declared
  program snapshot World.
- On this tiny fixture, the Checkout-reachable graph coincides with the
  whole program graph. The algorithm is still scope-bounded; larger
  programs were not measured.
- No `SemanticClassDefinition` or generic World-kernel type was introduced.
  Repeated snapshot evaluation now needs an independently maintainable
  `PaymentProvider(program identity)` projection; that is the next problem,
  not a reason to invent it in this milestone.

## Viability

Narrow deterministic scoped re-derivation remains viable for mediation once
provider identities are independently given.

It is not viable as a closed-world universal `TRUE` unless semantic
membership completeness is also established. Version 1's S0/C1/C2 successes
hid that gap.

A more general resolver abstraction would still be justified only after the
same definition/derivation split is independently required by a second
scoped invariant whose membership/mediation rules are not this invoke-graph
walk. One specialized evaluator is not that evidence.

A separate semantic-class construction or projection problem has now been
demonstrated: C3's `settleExternal` cannot be classified from existing
persisted/mechanical facts unless construction names it. Evaluation must
leave that as `UNKNOWN` rather than guessing.

## Tests

`tests/test_checkout_provider_boundary_evaluator.py` covers definition
round-trip, evaluator provenance, S0/C1/C2 derivations, independence from
the S0 receipt, incomplete and unknown controls, C3 unknown membership, C3
independently-known bypass, C4 open-world unknown, structural vs semantic
completeness, non-circular membership, zero model/repository/name use,
deterministic repetition, definition/derivation separation, GovernanceCase
consumption, and the continued presence of the historical finite-receipt
tests. No generic World-kernel files were changed for this evaluator.
