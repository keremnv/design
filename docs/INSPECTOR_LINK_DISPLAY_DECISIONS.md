# Inspector link display: open decisions (DRAFT)

Decisions still open after the Proposal A roster work and the stacked-label
fixes. Each settles here as Draft; nothing becomes Final without explicit
user acceptance. Deferred implementation stages are proposals only.

## D1. Dense-fan declutter (crowded signal) — DRAFT

Fact: on short spokes with many labels the fan is geometrically
inextricable. It already reports `crowded: true` honestly; WorldPage does
not subscribe (`onCrowded` is supported by WorldCanvas but unwired), so the
signal is dropped and the ring renders best-effort overlapping.

Options under discussion (see interview):
- (a) Count instead of names when crowded, opening the Links roster.
- (b) Cap named labels at K with a count for the rest.
- (c) Keep best-effort overlap, wire the signal to nothing.

Decision (DRAFT): (c) keep best-effort overlap, wire the signal to nothing.

## D2. Same-route spoke stacking — UNRESOLVED

Fact: `SpokeOptions.labelOffsetX/Y` exists for spokes sharing a station but
both call sites pass `{x: 0, y: 0}`. This world has zero self-bound tuples.
It does have duplicate endpoint pairs — across relations, not within one: on
the review world 25 of 28 binary pairs carry 3+ claims (max 5), mostly
`program_entity` / `program_entity_kind` / `program_identity_descriptor`.
Those form bond stacks (D3), not same-route spokes.

Decision: UNRESOLVED (wire offsets now vs leave documented vs remove option).

## D3. Bond-stack ink air — UNRESOLVED

Fact: stack pitch is chipHeight + 2px with a measured comment resisting 4px.
Parallel bonds are common here once several relations share a field (see
D2), so the ink case is reproducible: place all of `program_entity_kind`,
`program_identity_descriptor` and `program_entity`.

Decision: UNRESOLVED (leave pitch vs widen vs canvas-knockout stacks).
