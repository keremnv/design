# Bounded account-settings Design profile

This profile is a second small probe of the generic World lifecycle. It covers
ordinary preference editing and an account-deletion flow with a confirmation
step. It is not an ontology of account management or a prescription for visual
style.

The fixture contains one account-settings surface with profile settings,
email preferences, a save action, a danger zone, a delete action, a
confirmation context, and an account-deleted consequence context. The
structural adapter records only those observable nodes, their containment, and
their order. It does not infer that deletion is destructive or irreversible.

The selected law source is `fixture/design-governance.md`, named explicitly by
`fixture/governance-sources.json`. It is compiled into a proposed law and
explicitly adopted before construction. The effective law asks two questions:

```text
requires_confirmation_before(action, consequence, context)
distinct_in_consequence(routine, destructive, context)
```

The first question has one candidate supported by both the approved
requirements source and the implementation observation, so it resolves under
the Contract's `APPROVED_REQUIREMENT` standard. The second has only an
implementation/agent interpretation, so it remains `INSUFFICIENT_WARRANT`.
This keeps interpretation, authority, and sufficiency separate.

The profile has no natural competing sufficient candidates, so it does not add
a conflict checker, negative proposition, or adjudication. If a future
settings task needs to represent both confirmation and non-confirmation as
competing answers, that counter-proposition should remain profile-specific.

The fixture has no `PURPOSE.md` and uses the governed Purpose-free construction
path. The same generic Contract, Warrant/grounding, candidate association,
resolver, persistence, sealed reopen, explorer, and HTTP read surfaces are
used as in the checkout profile.
