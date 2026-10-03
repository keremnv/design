# Visibility on the field

Visibility follows the inspector's existing material language: marks keep
their arrangement and meaning while names yield to crowding. A dimmer name
means less room to read it, not weaker evidence or a less present referent.
The shared rule applies to both the vocabulary and the working field.

Names are ranked by selection, hover, naming reach, then structural priority.
Equal ranks favor the name that was already readable; stable identifier order
breaks a first encounter. Explicit attention overrides this memory immediately.

Crowding is the overlapping fraction of the yielding name's painted box.
Short and long names therefore use the same rule, and changing the camera's
scale does not change the answer. A contact starts yielding above 8% coverage,
continues until coverage falls to 4%, and reaches the 25% strength floor at
60% coverage. A smooth curve joins the readable and crowded states. While a
name is yielding, changes smaller than one opacity level (1/255) retain its
last strength so tiny geometry noise does not restart the fade. These are
presentation tuning values in `src/world/visibility.ts`.

The pass resolves stronger names first. A name that has already yielded
exerts less pressure on another name. Several contacts use their strongest
pressure rather than repeatedly multiplying opacity into an unreadable field.

Only text strength changes. Label knockouts remain opaque, marks and status
treatments retain their authored appearance, and names remain at their laid-out
stations. The existing reveal (`emit`) and withdrawal (`absorb`) plans carry
strength changes; reduced motion applies the settled strength directly.
During dragging, a pass runs at most once per animation frame and text strength
tracks the painted overlap directly. The spatial curve supplies the gradual
change, without restarting a timed fade behind every pointer movement. After
release, other changes continue to use the reveal and withdrawal plans.
Attention lighting, naming reach, and selection boundaries keep their existing
rules.

The governing material and motion commentary lives in
`src/styles/graphDna.ts`, `src/styles/light.ts`, and `src/styles/motion.ts`.
Regression checks cover gradual yielding, recovery, attention priority,
incumbency, scale independence, and separate text/background channels in
`tests/visibility.spec.ts`. The browser checks in `tests/inspector.spec.ts`
also exercise partial crowding on the rendered field, interrupted fades,
switching to reduced motion during a fade, and yielding and recovery on both
canvases while a drag is still held. Strength updates write only their own
channel into the graph store, preserving the live positions owned by dragging.
