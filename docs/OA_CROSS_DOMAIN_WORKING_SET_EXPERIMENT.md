# OA cross-domain working-set experiment

**Status: experiment report. Not a contract, Core authority, or accepted architecture.**

This is one synthetic, deterministic non-software falsification pass. It asks
whether a research reader can answer a bounded question from one sealed World,
inspect a useful unasserted source detail, and preserve the difference between
published knowledge and local observation. The construction and consumer live
only in tests. No Core or Design implementation was changed.

## Corpus, construction, and question

Four short Markdown fixtures describe basil plants under shade cloth. Studies
A, B, and C report lower leaf temperature. Study C separately records high
humidity. A research summary says humidity might increase or decrease cooling
and the available measurements do not decide which. The documents are synthetic
and make no claim about real horticultural research.

The test-only constructor uses the existing Markdown adapter for exact UTF-8
byte spans. It retains digest-checked source bytes in each bundle. It creates
thin study, finding, and claim referents and five base relations used by the
reader: `study_finding`, `finding_outcome`, `finding_supports_claim`,
`possible_humidity_effect`, and `open_question`. A sixth relation,
`study_intervention`, is published but irrelevant to the bounded answer. Every
assertion has source grounding and a `SEMANTIC` construction origin. The
constructor intentionally does **not** assert Study C's high-humidity detail.
The alternatives and question are published ordinary relations; neither
alternative is selected as an established effect.

`Project.run()` constructs a candidate, validates it, and seals it under a
newly reserved revision root. The second run uses another root and a similar
corpus in which Study B reports unchanged temperature. Both Worlds reuse the
internal logical `world_id`; their bundle paths are distinct publication
addresses. Neither publication is rebuilt in place.

The primary question is: **Which published studies support the shade-cloth
cooling claim, and through which findings?** The answer joins
`study_finding` → `finding_outcome` → `finding_supports_claim` and identifies
Studies A, B, and C and each reported lower-temperature finding in W0. The
reader also selects the published humidity alternatives and open question to
report what remains unresolved. It excludes all three published
`study_intervention` assertions. Thus its 12 cited assertions are a proper
subset of W0's 15 assertions.

## Bounded read and controls

The test-local result is a plain dictionary containing the question, exact
bundle path, the selected citations, the joined answer, the unresolved
question and alternatives, a negative probe, and a separately labeled source
observation. Each citation contains only its publication address, assertion
ID, relation/values, origin, and grounding as read from the sealed World. This
snapshot permits independent content and support comparison. It creates no
new World assertion and has no generic result schema or lifecycle.

A fresh Python process receives the serialized local result, opens only the
sealed bundle, and checks every citation against `WorldExplorerAdapter.assertion`.
It confirms the selected IDs cover exactly the relevant published relations,
reconstructs every cited grounding span from retained digest-checked bytes,
recomputes the join, checks the unresolved alternatives, and verifies that the
high-humidity detail occurs only in its labeled source observation. Fingerprints
of sealed bundle files are identical before and after reading. This is an
independent re-read of the recorded publication and support, not proof that
the constructor's scientific interpretation is objectively true.

The exact-publication control rejects a W1 citation placed in a W0 result,
including a W1 citation whose assertion ID happens to equal one in W0.
Relabeling W1's changed Study B assertion as W0 also fails because that ID is
absent from W0. No cross-publication correspondence is inferred. Inventing a
published humidity assertion fails because its ID is absent; adding humidity
to a real citation's values or changing its support fails the content/support
comparison. The reader may still say that retained Study C source text records
high humidity, explicitly as a **source-only observation with no published
assertion ID**. It stops there; no proposal object is needed for this task.

The negative probe asks whether Study A reported increased leaf temperature.
The selected assertions contain no such relationship, and
`latest_completeness("finding_outcome")` returns no receipt. The local result
says **not established**, never that the increased-temperature relationship is
false. A bad citation raises a normal verification error while the published
humidity-effect question remains epistemically unresolved. Runtime failure is
not represented as another uncertainty assertion.

## What the experiment actually exercised

| Core mechanism | Classification | Evidence in this pass |
| --- | --- | --- |
| Grounding | Required in this experiment | Admission requires source support; fresh read compares recorded support and reconstructs byte spans. |
| Construction origin | Required in this experiment | The source-to-claim interpretations were marked `SEMANTIC` and independently inspected. |
| Scoped completeness | Required in this experiment | The negative probe checks the absence of an applicable receipt before declining a negative conclusion. No positive completeness claim was constructed. |
| Unresolvedness | Required in this experiment | Two grounded possibilities and an open question are published without a selected effect. |
| Sealed publication and revision identity | Required in this experiment | Two fresh addresses remain unchanged; foreign citations fail even when local logical IDs or assertion IDs coincide. |

The use of a missing completeness receipt exercises the conservative side of
scoped completeness. This pass does not test a licensed negative read from a
`COMPLETE` receipt. It also does not test derivations, admission of a new
scientific conclusion, or any general scientific ontology.

## Comparison with Design, after the result

| Comparison | Classification | What recurred, and what did not |
| --- | --- | --- |
| Bounded citations ↔ Design Case | Same semantic invariant for exact-publication citation verification; Design-specific specialization for its proposition, subject, and selection rules | This reader needed only an address and verified citations. |
| Local answer ↔ Judgment artifact | Superficial structural similarity | Both are outside the World; this answer needed no applicability, conformance, method version, or decision semantics. |
| Source-only observation ↔ Investigation proposal | Insufficient evidence for a shared proposal lifecycle | The distinction from published knowledge recurred; the research reader had no reason to propose durable knowledge. |
| Open question ↔ Design unresolved question | Same Core-supported unresolvedness pattern; Design-specific specialization for the meaning of its question | Ordinary relations sufficed here. |

No Design machinery was recreated because it was semantically necessary. An
architecture test scans both experiment modules for Design and other downstream
application imports. The test-only citation verifier is useful implementation
code, but its duties are ordinary publication lookup, equality, and
question-specific join checking. It carries no new domain-neutral semantic
responsibility.

## Disposition

**H1 rejected in this pass.** A finite citation set anchored to one exact
publication, with ordinary Core assertion reads, was enough. No generic
working-set object was forced. A small verification helper could be reused as
implementation code; this result does not establish an architectural layer.

**H2 rejected for this workflow; durable discovery remains an untested
hypothesis.** “Source evidence observed; no published assertion exists” was
honest and sufficient. An application that later wants to propose and admit
knowledge would have another requirement to test. This experiment did not
need a proposal, admission persistence, or a publication workflow.

The smallest missing abstraction forced by this pass is **none**. The tests
are `tests/test_oa_cross_domain_working_set_experiment.py` (4 tests), with
`tests/oa_cross_domain_working_set_fixtures.py` and four Markdown fixtures.
The supported architecture remains **OA Core → bespoke application → product**.

## Explicit answers

- **Is a bounded citation set a new OA abstraction, or just ordinary use of a sealed World?** Ordinary use of one sealed World.
- **Does a consumer-local conclusion require a generic case/result model?** No; a test-local result was enough.
- **Does encountering useful but unpublished source evidence require a generic proposal lifecycle?** No; an explicitly source-only observation was enough here.
- **Did the second domain reproduce any Design machinery because it was semantically necessary rather than convenient?** No. Exact-publication verification and explicit unresolvedness recurred as Core behavior.
- **Is there now evidence for an OA application layer?** No.
