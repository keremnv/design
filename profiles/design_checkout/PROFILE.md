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

The adequacy counterfactual adds this fourth, deliberately narrow family:

```text
does_not_remain_available_during(subject, activity, context)
```

The reason is concrete: a world containing neither a positive availability
commitment nor a candidate for one cannot distinguish “order summary need not
remain available” from “the required question has not been determined yet.”
The negative commitment preserves that design distinction without introducing
generic negation or a conflict framework.

`candidate_for` is kernel bookkeeping, not Design vocabulary. Every Design
obligation remains `UNRESOLVED` in this slice even when it has a candidate;
there is no resolution engine.
