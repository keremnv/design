# Software Governance change-reconsideration experiment

**Status:** experiment / architecture discovery note. Not a renewal
contract, Decision contract, admission contract, maintenance framework,
Core authority, or production reconsideration subsystem.

The executable probe is
[the test-local reconsideration exercise](../tests/test_software_governance_change_reconsideration_experiment.py).
Authority is the accepted [Construction v0](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md),
[Judgment v0](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md), and
[Investigation v0](SOFTWARE_GOVERNANCE_INVESTIGATION_CONTRACT.md) contracts,
plus the preceding
[correspondence](CONFIG_ROUTE_CORRESPONDENCE_CONTRACT_EXPERIMENT.md),
[selection/scoping](SOFTWARE_GOVERNANCE_SELECTION_SCOPING_EXPERIMENT.md), and
[end-to-end loop](SOFTWARE_GOVERNANCE_END_TO_END_OPERATIONAL_LOOP_EXPERIMENT.md)
experiments as boundaries. The
[durable-knowledge catalogue](DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md)
supplies the MO-11 / ID-08 / SE-03 vocabulary used below. The probe adds no
production package, performs no admission or publication of new bindings,
and modifies no production file.

## 1. Concrete gap after the end-to-end loop

The integrated loop publishes W1 with a new subject A1 and zero carried
bindings where W0 bound P to A0. That refusal of automatic renewal is
correct — and it leaves a product hole: nothing tells a consumer that
historical `governance_binding(P, A0)` might be worth re-examining for A1.
This probe asks what evidence licenses that re-examination without turning
it into current governance.

## 2. W0/W1 baseline

`test_baseline_new_subject_without_binding`: W0 binds EXPORT_ID to the
`customer-export` subject A0; the demonstrated request → execute → observe
→ construct → publish loop moves the route path to `/internal/export`;
W1 holds the new subject A1 (A1 ≠ A0, revision-scoped) and no bindings.
W1 republishes the same proposition ID, which §3 separates from binding.

## 3. Historical governance versus current governance

Historical governance is the sealed W0 row `governance_binding(P, A0)`,
readable forever through W0 navigation. Current governance for A1 is
whatever `governance_binding` rows W1 itself publishes — here, none — and
that absence under `INCOMPLETE` coverage is not a negative conclusion. The
same proposition ID in both Worlds is shared proposition identity, not a
shared binding. The product answer in §13 keeps four states visibly apart:
historical, candidate-for-reconsideration, applicable, current/published.

## 4. Bridge types tested

Three licensed bridge kinds plus the no-bridge control, each a sidecar
record outside both snapshots (the ID-08 destination shape):

```text
fixture.operation-continuity/v0        bounded in-place edit, exact revision chain
fixture.supplied-correspondence/v0     explicit human/system assertion, endpoints grounded
config.routes.correspondence/v0        hypothetical producer pair, labeled not established
(no bridge)                            manual/unrelated change, nothing licensed
```

All three licensed kinds feed the same consumer: historical binding +
bridge + current subject → ordinary `Case(P, A1)`. None claims identity,
persistence, or a binding.

## 5. Operation-grounded bridge construction

`test_operation_bridge_links_a0_to_a1_without_identity` builds the bridge
from the loop's own stage records. It licenses exactly one sentence: A1 is
the post-operation subject reconstructed from observed R1 after a bounded
in-place mutation targeting A0's source occurrence. The license requires
all of: the path-edit capability id, a SUCCESS outcome, a valid
observation, observed revision equal to the capability's reported revision,
a tied pre-operation target (§6), and a tied post-operation subject (§7).
The record names W0/A0, request, capability, R1, W1/A1, method, basis, and
limitations; the limitations disclaimer names identity and binding only to
refuse them. The bridge plus the W0 binding yields exactly one
reconsideration candidate, `(P, A1)`; W1 still holds no binding.

## 6. Pre-operation target linkage

`test_pre_operation_target_linkage`: the request ties to A0 only through
W0's exact source revision matching the expected starting revision, the
named route record existing in W0, and its path matching the expected
value. A wrong revision, an unknown route, or a wrong expected path each
yields no tie. A request mentioning `customer-export` therefore does not by
itself mean it targeted A0; the W0 receipt, record, and exact revision do.

## 7. Post-operation subject lookup

`test_post_operation_subject_lookup`: A1 is found through W1's own
published receipts — W1's snapshot must equal the observed revision and
exactly one `config_route` row may carry the request's route ID. A missing
record or a mismatched revision yields no tie. A stale observation still
resolves against W1 while the live handoff has moved on, keeping
construction truth and live currentness distinct as in the loop experiment.

## 8. Delete/replacement control

`test_delete_replacement_produces_no_successor` runs a test-local
removal variant (same precondition discipline, different capability id)
with two legs: replacement reusing the `customer-export` ID with an
unrelated handler, and replacement under a fresh ID. Both publish valid
W1 knowledge; both refuse the operation bridge — the reuse leg on
transformation semantics ("capability is not the bounded in-place edit"),
so the same-ID trap pairs nothing. "The operation affected source
previously containing A0" is recorded; "A1 continues A0" is not claimed.
No similarity heuristic rescues or refuses either leg.

## 9. Split/merge result

Split is feasible and tested: `test_split_preserves_ambiguity_without_winner`
replaces the targeted record with two new records via a test-local split
variant. The operation bridge refuses (not an in-place edit); the probe
records an explicit `AMBIGUOUS_SUCCESSORS` set `{A1a, A1b}` from exact
record-ID set arithmetic on retained bytes, assembles no Case, and chooses
no winner. Resolution would need a supplied or producer correspondence.

Merge has no demonstrated operation: the bounded request names one route,
so a two-prior/one-current transformation cannot be operation-licensed.
`test_merge_surfaces_both_contexts_only_via_supplied_bridges` performs the
merge as a manual edit (no operation bridge buildable) and supplies two
correspondences, A0→M1 and H0→M1, against a W0 binding two propositions.
Both historical contexts surface as candidates; each assembles an ordinary
Case judging `UNKNOWN`. Merge is therefore handled through qualified
supplied bridges, not operation provenance — a documented limit of the
operation bridge, not a fabrication.

## 10. Producer-correspondence control

Per the correspondence experiment, the current producer establishes no
cross-snapshot correspondence, and this probe does not strengthen that:
`test_conditional_producer_pair_is_consumable_but_not_established` asserts
`produce_routes` output carries no correspondence and no W1 relation names
one. The same test feeds the hypothetical `config.routes.correspondence/v0`
pair shape into the reconsideration consumer to show the read side is
ready — the Case assembles and judges `UNKNOWN` — while the bridge record
labels its own basis "not established." Producer correspondence could
license reconsideration the day a producer qualifies it; same-record-ID
matching alone never does.

## 11. Supplied-correspondence control

`test_supplied_correspondence_licenses_inquiry_not_applicability`: after a
manual edit, a human supplies A0→A1 with named provenance. Endpoints are
grounded against exact publications (an unknown subject refuses the
bridge), while the correspondence claim itself stays labeled supplied.
The candidate surfaces, the Case assembles with the supplied method in its
question, and Judgment returns `UNKNOWN` with no conformance — inquiry
licensed, applicability undetermined.

## 12. No-bridge/manual-change control

`test_manual_change_without_bridge_surfaces_nothing`: a manual edit
publishes W1 with the same record ID and no bridge of any kind. The
reconsideration candidate set is empty. P remains discoverable in W0
through ordinary navigation, and W1's missing binding stays
non-negative under incomplete coverage. Structural similarity and repeated
record IDs surface nothing.

## 13. Exact-publication discipline

`test_bridge_requires_exact_publications`: bridge verification reopens the
named W0/W1 addresses and rechecks snapshots, route-subject endpoints, and
the reported/observed equality. A twin W0 (identical bytes and bindings,
different address) fails substitution, as does a twin W1 built from
identical R1 bytes; a tampered A1 endpoint fails the endpoint check.
Same logical world ID, record ID, label, and source path never substitute
for the address.

## 14. Reconsideration → Case assembly

`test_reconsideration_case_carries_lineage_outside_support`: historical
binding + licensed bridge + current subject assembles an ordinary Case via
the production `assemble_case`, with published-ID checks, exact-address
check, and `verify_case` all passing. The Case schema is unchanged (no
bridge field); historical lineage travels in the question text naming the
bridge method and the W0/W1 addresses. Reconsideration terminates at the
existing Case boundary — no new evaluator, no new Case field.

## 15. Reconsideration versus applicability

The same test judges the assembled Case `UNKNOWN` with conformance absent
and no context request: no binding and no recorded exclusion under
incomplete coverage. Surfacing P for inquiry decided nothing about whether
P governs A1. The replacement control (§18) strengthens this from the
other side: a licensed inquiry can end in a positive `DOES_NOT_APPLY`.

## 16. Context versus Judgment support

Also from the lineage test: the verdict's cited assertion IDs are a proper
subset of the Case's included facts, and the W0 binding's assertion ID is
provably not among them. The W0 address appears in the question (context
narrative) while support names only W1 assertions. Why P entered the Case
and why Judgment concluded what it did stay mechanically separate,
extending the selection experiment's context/support split across the
revision boundary.

## 17. APPLIES control

`test_independent_current_binding_judges_without_inheritance` seals W1b
from the same R1 software with an independently supplied binding(P, A1).
The reconsidered Case judges `APPLIES` with `CONFLICTS` (observed
`/internal/export` vs required `/customers/export`); a conforming leg on a
republished unchanged record judges `APPLIES` with `CONFORMS`. In both
legs the binding predates the verdict, sealed bytes are unchanged by
judging, and the binding count stays one: the Judgment result is not a
binding and creates none. W1b's binding is shown alongside the historical
binding and the bridge — never described as inherited.

## 18. DOES_NOT_APPLY control

`test_replacement_inquiry_can_be_refused_by_evaluator`: the operation
bridge refuses the replacement (per §8), a supplied A0→B1 bridge licenses
inquiry, and the evaluator returns `DOES_NOT_APPLY` on the positive
handler-exclusion reason with two cited assertions and no conformance.
This is the crucial `reconsidered ≠ applies` falsifier: the bridge did its
job bringing P to the question, and the question was answered no.

## 19. UNKNOWN control

The main reconsideration Case (§14) is the UNKNOWN control: a licensed
bridge, an unbound current subject of the ruled kind, no exclusion fact,
`INCOMPLETE` coverage → applicability `UNKNOWN`, conformance absent, no
context request. Existing gap machinery is preserved untouched; nothing
about the bridge converts uncertainty into a verdict.

## 20. Proposal boundary

`test_proposal_expresses_candidate_binding_without_publication` answers
the §21 question affirmatively but with an honest trigger gap. After the
UNKNOWN verdict on unbound W1, the existing Investigation proposal
envelope expresses "consider `governance_binding(P, A1)` for admission"
with `epistemic_class: semantic`, a profile-owned payload, and a basis
citing the W1 address, bridge method, and the UNKNOWN verdict. No
assertion ID exists, W1 is unchanged, no binding appears. The gap: this
config evaluator's `APPLIES` rule presupposes an established binding, so
an APPLIES verdict cannot motivate a proposal for an *unbound* subject —
and where a binding is already published (W1b), the test-local rule
refuses the proposal as redundant. A proposal here is motivated by
bridge plus inquiry, not by an APPLIES verdict. No second envelope was
needed; no admission was performed.

## 21. Admission boundary

Identified, not implemented. Before a proposed `binding(P, A1)` could
become published, something must supply the rule this probe deliberately
lacks: what combination of Judgment result, human/adoption decision,
producer evidence, or application policy authorizes a new binding row in a
later construction. The probe shows the inputs such a rule would read
(verdict, bridge, exact publications) and the envelope that would carry
the request, but no generic admission system was built and none is
justified by one probe.

## 22. Remaining Decision/Adoption question

Precisely located: after `APPLIES` with `CONFLICTS` on W1b, nothing in the
demonstrated machinery says whether Design should publish anything,
change the software, grant an exception, or do nothing. The verdict is a
case-local result about cited evidence, not an instruction. The Decision
question is now concrete — which actor, under what standing, disposes of a
conflicting binding — rather than abstract, and it remains unanswered.

## 23. Operation provenance versus producer correspondence

Explicitly different standing. Operation provenance attests that *this
bounded event* transformed a verified target occurrence into a verified
post-state; it is event-scoped, dies with any competing overwrite, and
says nothing about records it did not touch. Producer correspondence
would attest that two producer subjects continue across snapshots as a
property of the records — a stronger, snapshot-pair claim the current
producer does not make. Either can license reconsideration inquiry, but
neither is identity, and operation provenance must not be mistaken for a
general continuity relation: it cannot cover manual edits, merges, or any
second hop without a new licensed event.

## 24. Whether reconsideration deserves its own responsibility

No — not as an architectural box. The demonstrated shape is exactly the
selection experiment's "another front door": change event → historical
lookup + qualified bridge → ordinary Case assembly, with Judgment,
Investigation follow-up, and proposal machinery reused unchanged. What is
new is the *bridge-evidence* semantics (three qualified kinds with
distinct strength), not a Reconsideration engine. Outcome D holds for the
machinery; Outcome C holds for the bridge vocabulary. Neither earns a
production package on this evidence.

## 25. Whether a durable reconsideration artifact was needed

No. Every required read was answered from the historical binding row, the
bridge sidecar, the current subject receipts, the ordinary Case, and the
Judgment artifact. No `ReconsiderationResult`, receipt, or relation was
introduced. A product may retain bridge sidecars across sessions the way
it retains Cases, but no required independent read forced a durable
reconsideration artifact in this probe.

## 26. OA/Core sufficiency

Core remains unaware of reconsideration, operation succession, renewal,
and adoption, as scoped. Everything the probe needed — sealed
publications at exact addresses, assertions with warrants, retained
evidence, read-only reopening, and the Judgment/Investigation application
APIs — already existed. No Core, Construction, Judgment, or Investigation
change was required or made.

## 27. Falsifiers

Per the task's falsification standard, the probe preferred "historical
stays historical" at every pressure point:

- Operation bridge licensing inquiry without identity/renewal: held for
  the bounded in-place edit (§5); refused for delete/replace (§8),
  overwrite (§5, second control), split winners (§9), and cross-event
  reuse (§5, scoping leg).
- No-bridge manual change surfacing nothing: held (§12), including under
  a repeated record ID.
- `bridge licenses inquiry, not renewal`: held everywhere — no test
  produced a binding from a bridge; bindings appear only from explicit
  construction input.
- `reconsidered ≠ applicable ≠ adopted ≠ published`: held — one licensed
  inquiry judged UNKNOWN (§15), one refused DOES_NOT_APPLY (§18), two
  APPLIES verdicts changed no World (§17), one proposal stayed
  unadmitted (§20).
- Lineage leaking into support: refused (§16); the W0 binding assertion
  is absent from every verdict's cited set.
- The bridge collapsing to same-record-ID inference: refused — the
  reuse-ID replacement leg pairs nothing while a naive key rule would
  pair falsely (§8).

The disposition would change if a required read needed bridge state the
sidecar plus Case cannot carry; if a second operation shape forced a
shared continuity invariant beyond per-capability rules; or if an
admission rule required durable reconsideration state. None appeared.

## 28. Test counts

Nineteen deterministic tests in the new probe:

| Test | Pressure |
| --- | --- |
| `test_baseline_new_subject_without_binding` | W0/W1 baseline, proposition/binding split |
| `test_operation_bridge_links_a0_to_a1_without_identity` | licensed bridge, candidate surfacing |
| `test_pre_operation_target_linkage` | request→A0 tie and its negatives |
| `test_post_operation_subject_lookup` | observation→A1 tie and its negatives |
| `test_operation_bridge_is_event_scoped` | two-hop non-transfer |
| `test_delete_replacement_produces_no_successor` | removal legs incl. ID-reuse trap |
| `test_overwritten_operation_yields_knowledge_without_continuity` | X/Y bridge refusal |
| `test_split_preserves_ambiguity_without_winner` | ambiguous successors, no Case |
| `test_merge_surfaces_both_contexts_only_via_supplied_bridges` | multi-context via supplied bridges |
| `test_conditional_producer_pair_is_consumable_but_not_established` | producer control |
| `test_supplied_correspondence_licenses_inquiry_not_applicability` | supplied control |
| `test_manual_change_without_bridge_surfaces_nothing` | no-bridge negative |
| `test_bridge_requires_exact_publications` | twin/tamper discipline |
| `test_reconsideration_case_carries_lineage_outside_support` | Case assembly, support purity |
| `test_independent_current_binding_judges_without_inheritance` | APPLIES/CONFORMS/CONFLICTS |
| `test_replacement_inquiry_can_be_refused_by_evaluator` | DOES_NOT_APPLY |
| `test_proposal_expresses_candidate_binding_without_publication` | proposal boundary |
| `test_agent_operation_bridge_same_standing` | actor provenance |
| `test_product_answer_distinguishes_historical_candidate_and_current` | product reads |

Focused probe: **19** passed. The probe plus related loop, write,
correspondence, config-profile, construction, architecture, handoff, and
intake tests passed **123**; Core acceptance passed **18**; the default
repository gate passed **87**. `git diff --check` passed. No live model, no
new production package, no Core edit.

## 29. Recommendation

Treat reconsideration as a Case-assembly front door fed by qualified
bridges, not as a new subsystem: keep the three bridge kinds with their
distinct strength labels, keep bridges as sidecars outside both snapshots
(the ID-08 destination), keep lineage in Case context narrative rather
than support, and keep every binding explicit-input-only. Do not
productionize bridge, reconsideration, proposal-trigger, or admission
machinery on this evidence.

The next experiment should be **admission semantics for a proposed
binding**: this probe leaves a well-formed semantic proposal
(`binding(P,A1)`, motivated by bridge plus inquiry) with no rule that may
admit it. Resolving what authorizes a new binding row — verdict plus
human adoption, application policy, or other standing — is now the concrete
blocker, and it will ground the Decision/Adoption design the same way
this probe grounded the inquiry side.

## Explicit answers

1. **What exactly is governance reconsideration?** Surfacing a historical
   binding's proposition as a candidate for ordinary inquiry against a
   current subject, via a qualified bridge. It is a front door, not a
   verdict, renewal, or publication.
2. **What licenses historical governance to enter inquiry for a current
   subject?** A licensed bridge: operation-continuity (bounded in-place
   edit, exact revision chain), supplied correspondence (explicit
   assertion, grounded endpoints), or a qualified producer pair (not
   currently established for config).
3. **Is operation provenance sufficient?** Yes, narrowly: for the bounded
   in-place edit with verified pre/post linkage and observed-equals-reported
   bytes. It fails closed for delete, overwrite, split, merge, manual
   edits, and second hops.
4. **If so, what exact relation does it establish?** "A1 is the
   post-operation subject reconstructed from observed R1 after a bounded
   mutation targeting A0's source occurrence." Event-scoped; nothing more.
5. **Does it establish SoftwareSubject identity?** No. A0 ≠ A1 stays
   asserted; the bridge disclaims identity in its limitations.
6. **Does it establish semantic identity?** No. No semantic claim of any
   kind is made or needed for the inquiry.
7. **Does it establish a current governance binding?** No. W1 bindings
   come only from explicit construction input; bridges never create them.
8. **Can producer correspondence license reconsideration?** It could once
   a producer qualifies a pair — the consumer side is demonstrated — but
   the current config producer establishes none, and record-ID equality
   alone licenses nothing.
9. **Can supplied correspondence license it?** Yes, with endpoints
   grounded and the claim labeled supplied; it licensed inquiry ending in
   both UNKNOWN and DOES_NOT_APPLY.
10. **What happens with no bridge?** Nothing surfaces. Historical
    governance stays discoverable in W0; no candidate, no Case, no
    verdict for the current subject.
11. **How are delete/replacement cases handled?** The operation bridge
    refuses (different transformation semantics); knowledge still
    publishes; a supplied bridge may later offer the replacement for
    inquiry, which the evaluator may refuse.
12. **How are ambiguous/split/merge cases handled?** Split records an
    explicit ambiguous-successor set and assembles no Case. Merge has no
    operation licensing; supplied bridges surface each historical context
    as its own candidate. No winner is ever chosen without evidence.
13. **Is reconsideration simply another Case-assembly front door?** Yes.
    Historical lookup plus bridge, then the unchanged Case/Judgment
    boundary. No new responsibility box earned.
14. **Does reconsideration itself decide applicability?** No. Only the
    evaluator's verdict does, and licensed inquiries in this probe ended
    in UNKNOWN, DOES_NOT_APPLY, APPLIES/CONFORMS, and APPLIES/CONFLICTS.
15. **Does Judgment APPLIES create a binding?** No. APPLIES presupposed
    the binding in the case here, and judging changed no World's bytes
    or binding count.
16. **Does Judgment CONFLICTS mandate remediation?** No. It is a
    case-local result about cited evidence. Disposition (publish,
    change, except, ignore) is the unresolved Decision question.
17. **Can reconsideration produce a proposal without publication?** Yes,
    via the existing Investigation semantic-proposal envelope, motivated
    by bridge plus inquiry; it stays unadmitted and unpublished.
18. **What remains unresolved about admission?** The authorizing rule:
    what combination of verdict, human/adoption decision, producer
    evidence, or policy may turn a proposed binding row into a published
    one. Inputs identified; rule not designed.
19. **What remains unresolved about Decision/Adoption?** Which actor with
    what standing disposes of verdicts — especially APPLIES/CONFLICTS —
    and whether that disposition publishes, mutates, excepts, or ignores.
20. **Was any new durable state required?** No. Bridge sidecars, Cases,
    and artifacts sufficed as ordinary records.
21. **Was a reconsideration artifact required?** No. No result, receipt,
    or relation object was introduced.
22. **Was a new production package justified?** No. Test-local machinery
    only.
23. **Did anything require OA Core changes?** No.
24. **Did anything require accepted Judgment/Investigation changes?** No.
    Both were consumed through their accepted APIs unchanged.
25. **What should the next experiment be?** Admission semantics for a
    proposed binding: what authorizes `binding(P,A1)` to be published,
    grounding Decision/Adoption in the concrete proposal this probe
    produces.

## Working-tree note

This pass adds only this report and one test-local file. It does not modify
Core, accepted contracts, or production packages; it does not commit or
push. Other uncommitted repository changes predate this pass and were left
in place.
