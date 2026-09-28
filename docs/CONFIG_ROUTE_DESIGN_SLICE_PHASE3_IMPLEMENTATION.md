# Config-route Design slice Phase 3 implementation

Status: implementation report / product slice evidence, 2026-09-28.
Not architecture authority. Phase 2 is frozen at `14a2685c`
([Phase 2 report](CONFIG_ROUTE_DESIGN_SLICE_PHASE2_IMPLEMENTATION.md),
[Phase 2 review](CONFIG_ROUTE_DESIGN_SLICE_PHASE2_REVIEW.md)); executable
code and tests take precedence over this note.

Phase 3 implements exactly one next capability: bounded continuation
from an honest Judgment `UNKNOWN`. No commit or push was performed.

## Production Investigation surface

Installed thin facade in `ontology_author/config_routes/investigate.py`,
exported from `ontology_author.config_routes`:

```python
investigate_config_world(world, proposition, subject,
                         question_focus=None, judgment=None, persist_to=None)
read_investigation_bundle(path)
verify_investigation_bundle(bundle_or_path, world=None)
```

The caller supplies only the exact World address plus proposition and
subject IDs discovered through Inspect. The facade owns the guarded
trigger Judgment, canonical Case handling, UNKNOWN validation, the
Investigation question, invocation, verification, and the structured
result. No CLI, no planner, no workflow object.

An already persisted Judgment bundle may optionally be supplied as
`judgment` so a later agent can continue without re-judging. It is
verified with the Phase 2 verifier first (against the same exact World),
its recorded request must name the same proposition/subject, and only
then is its verified canonical Case used as the trigger. Persistence is
never required to investigate.

## UNKNOWN precondition

Eligible triggers are exactly the evaluator-produced unresolved
verdicts:

```text
applicability = UNKNOWN (any conformance)
APPLIES + conformance = UNKNOWN
```

Everything else refuses with explicit structured outcome
`INVESTIGATION_NOT_APPLICABLE` and a reason naming the trigger state:

```text
APPLIES + CONFORMS / CONFLICTS
DOES_NOT_APPLY
UNSUPPORTED_EVALUATOR (kept distinct from UNKNOWN via trigger_outcome)
UNKNOWN_PROPOSITION / UNKNOWN_SUBJECT / INVALID_CASE (carried through)
unverifiable or mismatched supplied Judgment bundle
damaged evidence (trigger Judge returns INVALID_CASE first)
```

"No evaluator exists" is never confused with "the evaluator ran and
concluded UNKNOWN": the refusal carries `trigger_outcome` unchanged.

## Exact World/Judgment association

Investigation opens one exact sealed publication read-only
(`open_config_world_view`) and retains address, `world_id`, integer
revision, and `database_fingerprint` (SHA-256 of exactly `world.sqlite`,
unchanged Phase 2 semantics). The trigger Case is always the canonical
guarded Case: either freshly assembled by `judge_config_world` inside
the call, or taken from a bundle the Phase 2 verifier accepted for
exactly this World/request. Caller-authored Cases are never accepted.
A `world=` override that names another publication fails `exact_address`
in bundle verification. The World is never mutated: tests hash every
file under W0 before and after Investigation.

## How existing Investigation machinery is reused

The generic package
`ontology_author/software_governance/investigation/` is reused
unchanged and added to the installed closure (it is profile-free; the
existing vocabulary/import boundary test keeps it that way):

```text
expanded_case / added_assertion_ids / citation_errors (same-publication expansion)
make_question / make_receipt / make_proposal (records outside the World)
InvestigationBoundary (leaving the publication/case contract)
CASE_EXPANDED / PROPOSAL / UNRESOLVED (outcome vocabulary, not collapsed)
```

The bounded `config.subject-investigation` rule
(`investigate_bounded_case`) mirrors the repository fixture investigator
(`profiles/software_governance_config_v0/investigate.py`) decision for
decision — unasserted manifestation field the question asks about
becomes a proposal; published subject facts missing from the parent
case expand it through verified `expanded_case`; otherwise unresolved —
because `profiles/` is not installed. A cross-check test runs both
implementations on shared unresolved/proposal/expansion inputs and
asserts identical outcome, receipt, proposal, and expanded case. This
is the same duplication-with-cross-check discipline Phase 2 used for
the evaluator; no investigator registry, planner, or framework was
introduced.

The facade supplies exactly one capability: `manifestation-text`,
reading `view.local_manifestation_for_subject` from the same sealed
World. Nothing external is consulted.

The Investigation question is derived, never caller-authored: a copied
Judgment `context_requests[0]` becomes a `judgment_request` origin
with its `structured_need`; a request-less UNKNOWN becomes an open
question. The optional `question_focus` names one subject property to
ask about (discoverable via `inspect_subject` manifestation); it sets
`structured_need = subject_property/focus`. Relevance keeps the
accepted rule: a field the question names (or whose key appears in the
question text) may propose; anything else stays unresolved.

## Supported outcomes actually demonstrated

`UNRESOLVED` (normal path): the established Phase 2 control —
customer-export plus a same-handler unbound `other` route — judges
`UNKNOWN` ("no binding and no recorded exclusion") and investigates to
`UNRESOLVED`. The explanation names the missing
`governance_binding(P, S)`, the established sibling binding, bound and
candidate subjects, open questions, `INCOMPLETE` coverage with gaps,
inspected relations, and manifestation status. It guesses nothing.

`PROPOSAL` (demonstrated): a route record carrying an extra,
producer-unasserted field (e.g. `"owner": "data-platform"`, preserved
in the canonical manifestation per Phase 1) plus
`question_focus="owner"` yields a mechanical proposal with payload,
reconstructed-manifestation basis (scheme, location, content digest,
text), method, and reason. The proposal carries no assertion id anywhere
and establishes nothing. Without the focus, the same World yields
`UNRESOLVED` that merely observes the unasserted field as exploration
information — unasked-about fields never auto-propose.

`CASE_EXPANDED` (honestly unreachable on the product path): the Phase 2
canonical trigger Case already cites every published mechanical fact
for the subject, so reassembly adds nothing (`added == []`, asserted
by test). Judge completeness was not weakened to manufacture an
expansion. The machinery branch is preserved and cross-checked, and the
bundle verifier fully supports an expanded case (citation verification
plus evidence-OK) should one ever occur.

## What evidence is inspected

Same-World reads only: all producer-relation rows naming the subject
(`config_member`, `config_route`), the subject manifestation
(reconstructed retained bytes), and — for the explanatory context, not
as new citations — the proposition's established/candidate subjects,
the subject's bound propositions, open questions, and coverage/gaps.
`inspected_relations` on the receipt is exploration provenance, never
support. Only verified assertions could enter an expanded case; only
the retained manifestation backs a proposal basis.

## What is verified

Persisted bundles (`config-routes-investigation/v1`, optional,
exclusive no-clobber write refusing symlinks) verify by canonical
replay under the compatible installed implementation:

```text
readable / shape (incl. recorded World value types, focus, trigger case id)
world_readable / exact_address / world_id / revision / database_fingerprint
trigger_valid (fresh canonical re-judgment is JUDGED, UNKNOWN-eligible,
               and artifact-identical, using the recorded case id)
replay_match (question, outcome, receipt, proposal, expanded case
              multiset-equal to a fresh investigator replay)
support_sound (expanded child passes verify_case with all support OK;
               proposal basis scheme/location/digest/text match the live
               OK manifestation and the payload value is in it; proposals
               claiming an assertion id fail; vacuous for UNRESOLVED)
```

Malformed, truncated, tampered, substituted, or stale bundles are
structured negatives, never uncaught exceptions. Verification does not
claim a proposal is semantically true or that future admission is
warranted.

## What correction loop was demonstrated

The acceptance test proves the manual loop with the function stopping
before Construction (asserted statically: the module never imports the
constructor):

```text
construct W0 (customer-export + same-handler other)
inspect, judge(other) = UNKNOWN, persist J0
investigate(other) = UNRESOLVED (missing binding, sibling bound, INCOMPLETE)
caller corrects legitimate workspace input (other route gets its own handler)
construct_config_world(...) -> W1 at a fresh address
judge W1 (P/S rediscovered in W1) = DOES_NOT_APPLY with positive basis
```

W0 is byte-identical after Investigation and after W1 Construction, W0
still opens, old J0 and I0 still verify, W1 is distinct, and no
cross-snapshot subject identity is assumed (IDs are rediscovered per
publication). W1's `DOES_NOT_APPLY` shows a later World where the old
question no longer applies — it does not resolve, answer, or rewrite
W0's missing binding. W0 remains historical truth for that publication;
a fresh Investigation of W0 still returns the same `UNRESOLVED`.

A separate-process A/B/C handoff (construct → judge UNKNOWN + persist
→ investigate from W0 + J0 paths + persist) passes both in-repo and
from a clean wheel install outside the repository.

## What remains absent

No Investigation continuation beyond one bounded call, no automatic
re-judge loop (an expanded case returns material plus why it may
matter; the caller re-judges explicitly), no W1 construction inside
Investigation, no proposal admission/publication path, no World
diff/compare, no Decision/Action/Admission, no agent runtime, no
current pointer, no Core change, no new architectural abstraction.

## Post-review integrity corrections

Independent review
([CONFIG_ROUTE_DESIGN_SLICE_PHASE3_REVIEW.md](CONFIG_ROUTE_DESIGN_SLICE_PHASE3_REVIEW.md),
verdict PROPOSAL INTEGRITY BLOCKER) demonstrated that fixed question
prose could select a proposal field the caller never focused, that
assertion-shaped source material could enter payloads, that persistence
could write inside a World with a writable child directory, and that
malformed bundle shapes could raise from the verifier. Fixed without
redesign; the review is left intact and the sections above now describe
corrected behavior:

- Explicit focus is now exact and exclusive: only the property named by
  `structured_need` may become a proposal field, as a top-level scalar
  of the parsed canonical manifestation. The question-text fallback is
  removed — prose explains the investigation, it never licenses a
  field. Absent, non-scalar, nested-only, reserved, or unpublished
  focused fields yield `UNRESOLVED`, never a substitute field.
- Supported proposal values are JSON scalars only: string, finite
  number, boolean, null. Arrays and objects fail closed to
  `UNRESOLVED`; this also excludes nested assertion-shaped objects.
- Reserved source names `assertion_id` / `assertion_ids` can never
  become a proposal field. Such material stays inspectable (it still
  appears in `observed_unasserted_fields`) but is never proposed, and
  forged reserved payloads fail `support_sound`. No proposal contains
  or mints a World assertion ID.
- Proposal verification proves exact correspondence: the stored field
  must equal the recorded focus, the value must be the parsed
  top-level scalar under that key (via the same bounded extraction as
  selection), and basis scheme/location/digest/text must match the
  live `OK` manifestation. Wrong-field/real-value and
  right-field/wrong-value forgeries fail `support_sound` directly, not
  only in replay.
- Persistence is forbidden inside W0: any `persist_to` resolving to or
  underneath the World directory is refused before parents are created
  or files opened, regardless of permission bits. Direct, nested,
  symlink, and relative in-World paths all refuse with W0 byte-identical.
  Phase 2 Judgment persistence now enforces the same boundary.
- Malformed bundles are structured negatives: receipt/proposal/case
  shapes, receipt outcome/additions, and citation inspection are
  type-guarded, so malformed values return `verified: false` instead
  of `AttributeError`/`KeyError`/`TypeError`.
- Dormant expanded-child metadata is now compared exactly (field set
  plus `inspected_relations`, covered by a comparator unit test).
  `CASE_EXPANDED` remains honestly unreachable on the product path, so
  this closes the replay claim without changing reachable behavior.
- The installed rule is now deliberately stricter than the repository
  fixture investigator (exact focus only; the fixture retains
  question-text relevance for its accepted experiment scope). The
  cross-check still asserts agreement on shared inputs.
- Historical replay limitation stated explicitly: Investigation
  verification replays question derivation, relevance, extraction,
  investigator behavior, and verification under the compatible
  installed implementation. Later code may change a replayed outcome
  or reject a prior bundle; replay proves the current product's
  result, not package A's historical executable semantics.

## Files this slice requires

```text
ontology_author/config_routes/investigate.py          (new facade + bounded rule)
ontology_author/config_routes/__init__.py            (exports)
ontology_author/software_governance/investigation/
    __init__.py, expansion.py, records.py            (installed closure addition)
tests/test_config_routes_phase3.py                  (14 acceptance tests)
docs/CONFIG_ROUTE_DESIGN_SLICE_PHASE3_IMPLEMENTATION.md (this report)
```

No commit or push was performed; unrelated working-tree changes were
not touched.
