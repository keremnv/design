# Bounded mobile checkout Design profile

This profile is a probe, not an attempt to create the ontology of Design. It
preserves only decisions that are consequential for the task:

> Redesign mobile checkout while preserving purchase confidence. Critical order
> information should remain available during payment entry, and the hierarchy
> at the commitment point should support confident purchase.

The production fixture uses these three relation families:

```text
relative_prominence(more, less, context)
remains_available_during(subject, activity, context)
supports(subject, goal, context)
```

The adequacy counterfactual adds this fourth, deliberately narrow and
provisional family:

```text
does_not_remain_available_during(subject, activity, context)
```

The reason is concrete: a world containing neither a positive availability
commitment nor a candidate for one cannot distinguish “order summary need not
remain available” from “the required question has not been determined yet.”
The negative commitment preserves that design distinction without introducing
generic negation or a conflict framework.

`candidate_for` is the human-readable name of a kernel Obligation↔Commitment
association, not a Design relation or ontology vocabulary. Every Design
obligation is evaluated separately after construction. The approved
requirement-backed availability candidate resolves in the current bounded
experiment; agent-judgment candidates remain unresolved because the Design
Contract accepts only the structured `APPROVED_REQUIREMENT` warrant authority
for resolution. This is not final Design authority policy.

The fixture's structural adapter is deliberately limited to literal JSX tags
with double-quoted attributes. It does not execute React, resolve components,
inspect CSS, or infer runtime visibility. It records only nodes, containment,
current child order, and surface/context containment. The Governance Law then
selects governed subjects from those descriptive facts; it does not treat the
current arrangement as the desired answer.

Evidence authority is selected separately in
`fixture/evidence-authorities.json`. It binds the stable source identities
`file://checkout-requirements.md` and `file://Checkout.tsx` to
`APPROVED_REQUIREMENT` and `IMPLEMENTATION_OBSERVATION` respectively. The
constructor records those sources as Warrant bases but does not receive this
configuration and cannot write an authority label. The resolver joins recorded
source identities to the selected configuration, then asks the Contract which
authority classes are sufficient. The sealed bundle records the authority
configuration and each candidate assessment records its matched source and
authority basis.

Adjudication is a separate, optional input. The fixture's
`adjudication-authorities.json` binds `design-review-decision` to
`AUTHORIZED_ADJUDICATION`, but ordinary construction creates no adjudication.
When an adjudication is explicitly recorded, it selects an existing candidate
and the resolver may use it only to break an otherwise sufficient conflict.

Governance Law is not authored directly in the constructor or in this module's
dimension declarations. `fixture/governance-sources.json` explicitly selects
`fixture/design-governance.md` as law-bearing. The bounded compiler in
`governance.py` turns that human-readable source into a proposed structured
law, and `load_design_law()` explicitly adopts it before `Project.run()` is
called. The constructor receives only the effective law. The answer-bearing
`checkout-requirements.md` and observational `Checkout.tsx` remain evidence
for candidate commitments; neither is selected as constitutional law.

The compiler currently recognizes only `## Availability`, `## Priority`, and
`## Goal support` sections with labeled bindings. This is a fixture adapter,
not a general natural-language interpreter. Each generated obligation is
published with an adjacent `world.obligations.json` explanation linking it to
the adopted law rule, source revision/location, and structural bindings.

The law is `design-mobile-checkout-law@1` and currently has three finite rules:

1. Select the order-summary region, payment-entry region, and mobile-checkout
   surface to ask an availability question.
2. Select the order-total field, promo-code interaction, and checkout-commitment
   context to ask a priority question.
3. Select the order-summary region and checkout-commitment context, pairing
   them with the law-level goal `purchase_confidence`, to ask a goal-support
   question.
