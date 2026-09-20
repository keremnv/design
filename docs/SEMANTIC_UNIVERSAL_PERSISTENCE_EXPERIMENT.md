# Scoped-universal semantic-persistence experiment

This experiment tests whether a scoped universal payment-boundary meaning can
fit the finite commitment-warrant contract. It is implemented by
`experiments/run_payment_universal_persistence_experiment.py` and retained in
`experiments/semantic-universal-persistence-20260916-run4/`.

## Authority and obligation

The experiment uses a separate authoritative fixture sentence:

```text
All payment-provider access from Checkout must go through PaymentGateway.
```

This is intentionally stronger and separate from the existing bounded ADR.
The manual obligation is `PROGRAM_INVARIANT`, with the semantic subject
`semantic:CheckoutProviderAccess`, boundary `semantic:PaymentGatewayBoundary`,
and scope `declared Checkout payment-provider access universe`.

The trusted assertion shape is:

```text
semantic_payment_provider_access_invariant(
    access,
    boundary,
    scope_root
)
```

The model chooses the bounded semantic roles and scope root; it does not
choose the predicate. Mechanical spine kinds constrain the scope root to the
known Checkout callable.

## Baseline universe and candidate

S0 contains two Checkout-originating mediated branches:

```text
Checkout -> authorize       -> PaymentGateway -> StripeClient
Checkout -> authorizeRetry  -> PaymentGateway -> StripeClient
```

The program spine exposes five `program_invokes` tuples. The completeness
receipt enumerates exactly those five relation-evidence IDs. C1 preserves the
old branches and adds:

```text
Checkout -> checkoutDirect -> StripeClient
```

The new path is deliberately not in the S0 finite receipt.

## Results

Composer 2.5 was available through the authenticated Cursor CLI. Two
independent bounded construction runs both selected the same semantic tuple,
the Checkout scope root, and supplied commitment-grade output. Both passed
the unchanged deterministic admission profile as `PERSIST_COMMITMENT`.

The deterministic control results were:

| Control | Result |
| --- | --- |
| complete finite S0 universe | `PERSIST_COMMITMENT` |
| incomplete universe | `RECORD_UNRESOLVED` |
| only one known member selected | `RECORD_UNRESOLVED` |
| known-bypass hypothesis (`HYPOTHESIZED`) | `RECORD_UNRESOLVED` |
| over-optimistic positive with a supplied known bypass | `PERSIST_COMMITMENT` |
| wildcard graph-query dependency | `INVALID_CANDIDATE` |

The selected live commitment was published in a sealed World revision. The
baseline and revision have the same program snapshot ID; only governed
semantic knowledge differs. The finite warrant contained 10 program
identities, 5 relation tuples, 5 source-manifestation dependencies, and 1
structural dependency: 21 dependencies total. Its exact receipt is retained
in the selected live-run directory.

The S0-to-C1 comparison added two `program_invokes` relation changes that were
not named by the old receipt. Existing maintenance returned `CHANGED`, with
`model_invoked=false`, `transferred=false`, and candidate semantic status
`UNRESOLVED`. This status is also affected by changed baseline manifestations,
but the new relation additions were not directly covered by the finite member
receipt.

## Architectural finding

For a universal meaning, a finite receipt can maintain the listed S0 members,
but it cannot by itself answer whether a newly introduced member belongs to
the universal set. Correct maintenance therefore needs deterministic
re-derivation of the scoped universe (or an equivalent maintained enclosing
relation) when future universal governance depends on membership. This
experiment labels that boundary `DEPENDENCY_RECEIPT_INSUFFICIENT`; it does
not implement a resolver, query language, wildcard dependency, or model
maintenance call.

The existing realization and bounded relational commitments remain finite
member/endpoint receipts. The universal commitment is qualitatively
different only at the new-member boundary: its completeness is an enumerable
S0 receipt, not future membership discovery.

The adversarial known-bypass control is an intentional boundary observation:
the admission gate checks obligation shape, evidence classes, completeness,
and inspectable dependencies; it does not adjudicate whether a positive
universal proposition is semantically true. A positive candidate that supplies
the bypass as another enumerated member therefore passes admission. Truth
evaluation remains outside persistence admission and is not patched into this
experiment.

## Scope and non-goals

No automatic obligation generation, semantic resolver, graph query, semantic
renewal, World-kernel change, or candidate adoption was added. The model was
used only for initial bounded semantic construction. The experiment does not
assert that the C1 direct endpoint violates the authority; absent a separately
established provider identity and positive bypass evidence, that conclusion
remains open-world.

## Successor for snapshot truth

The finite invariant commitment is retained as historical S0 evidence. It is
not the authoritative current-state result.

```text
old finite invariant commitment:
    useful evidence about S0

new invariant definition:
    reusable semantic question
    (ScopedInvariantDefinition, checkout-provider-boundary/v1)

new snapshot derivation:
    authoritative deterministic current-state result
    (ScopedInvariantDerivation for S0, C1, C2, ...)
```

Future GovernanceCase assembly should prefer the candidate
`ScopedInvariantDerivation` for candidate-state truth. The evaluator
discovers C1's new unmediated member from the current program spine without
LLM maintenance, wildcard receipts, repository search, or a generic
resolver. Structural enumeration completeness is not semantic membership
completeness: a provider identified only because PaymentGateway already
reaches it cannot honestly prove that every provider is reached through
PaymentGateway. See [SEMANTIC_SCOPED_INVARIANT_EVALUATOR.md](SEMANTIC_SCOPED_INVARIANT_EVALUATOR.md).
