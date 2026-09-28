# Config-route Design slice Phase 2 implementation

Status: implementation report / product slice evidence, 2026-09-27.
Not architecture authority. Phase 1 is frozen in commit `9dcb73ad`
([Phase 1 report](CONFIG_ROUTE_DESIGN_SLICE_PHASE1_IMPLEMENTATION.md),
[Phase 1 review](CONFIG_ROUTE_DESIGN_SLICE_PHASE1_REVIEW.md)); executable
code and tests take precedence over this note.

## Production Inspect surface

Installed thin facade in `ontology_author/config_routes/inspect.py`,
exported from `ontology_author.config_routes`:

```python
inspect_config_world(world)            # full inventory from address alone
inspect_proposition(world, P)          # meaning, source, concern, judgeability
inspect_subject(world, S)              # receipt, facts, manifestation, concern
inspect_binding(world, P, S)           # why P concerns S, both evidence sides
```

Every call takes one exact publication address, opens it read-only, and
closes it. No IDs are needed to start: the inventory lists subjects (with
route IDs, paths, handlers), propositions, bindings, candidates,
questions, coverage/gaps, and software/governance source revisions. All
results are JSON-serializable dicts composing `GovernanceView`, Core
warrant/evidence reads, and Phase 1 profile provenance. Invalid, unsealed
(writable bits), non-governance, or non-`config.routes/v1` addresses raise
`ValueError` with explicit reasons; unknown IDs raise likewise. Subject
reads state snapshot-local identity and no cross-publication continuity.

## Production Judge surface

Installed guarded facade in `ontology_author/config_routes/judge.py`:

```python
judge_config_world(world, proposition, subject, persist_to=None, case_id=None)
read_judgment_bundle(path)
verify_judgment_bundle(bundle_or_path, world=None)
```

The caller supplies only the exact address plus P/S discovered via
Inspect. The facade owns case IDs, the question, case assembly over the
full required relations (never omitting evaluator inputs), citation and
support verification, evaluator selection and invocation, artifact
linkage, and optional no-clobber persistence. Outcomes are explicit
product results: `JUDGED` (verified artifact), `UNSUPPORTED_EVALUATOR`,
`UNKNOWN_PROPOSITION`, `UNKNOWN_SUBJECT`, `INVALID_CASE`. World-address
problems raise instead, matching Inspect.

## How evaluator discovery works

No registry, no module scan, no report dependency. The installed profile
re-applies its own versioned grammar (`rules.classify_paragraph`, the
same function Phase 1 construction used) to the proposition's retained
statement plus its durable `establishment_rule` and `profile_id` extras
(`rules.evaluator_for_statement`): SPECIFIC naming a covered route
(`customer-export`) is covered with method `config.customer_export_route
/v0` and its rule parameters; generic, other-route, or
provenance-inconsistent propositions are unsupported with explicit
reasons. Discovery inputs are all World-durable, so a fresh process
opening W0 determines judgeability identically with or without the
ephemeral construction report (proven by cold tests that drop the report
and by fresh-subprocess probes). The product evaluator itself lives in
installed `config_routes/evaluate.py` with parameters single-sourced
from `rules.EVALUATOR_RULE`; the repository fixture evaluator is
untouched, and a cross-check test asserts verdict equivalence across
support/conflict/exclusion/unresolved branches.

## How exact World identity is enforced

A judgment binds `address` (resolved absolute), `world_id`, integer
`revision`, and `database_fingerprint` (SHA-256 of exactly the sealed
`world.sqlite` bytes — not the whole directory; see Post-review
integrity corrections). The facade checks, beyond generic `verify_case`
citations: case address equals opened address, case/bundle revision
equals opened revision, live database bytes equal the fingerprint, and
every relied support item reconstructs `OK` (per-item digest checks on
the retained blobs). Logical World ID alone is never trusted (all config
Worlds share `config-routes`). Two Worlds with identical content at
different addresses produce indistinguishable citations but distinct
addresses, and substitution verification fails on the address check
(tested). The address is a historical location binding, not a portable
signed identity: a byte-identical copy at a new path is a different
exact publication, and bundles for the old address do not transfer.

## How Case + artifact are linked

`JUDGED` results embed the full verified case and artifact with a
per-check verification record. Optional `persist_to` writes one JSON
bundle `{format, world, request, case, artifact}` with exclusive
no-clobber creation (refuses existing paths including symlinks).
`verify_judgment_bundle` re-opens the recorded address (or a given world,
which must equal it), reconstructs the canonical Case for the recorded
request from that World with production `assemble_case`, requires the
supplied Case to match it exactly, rediscovers evaluator eligibility,
and only then checks citations, artifact linkage, and verdict
reproducibility by re-evaluation under the compatible installed
implementation. Selective cases, mixed Worlds, and substituted addresses
all fail named checks (tested). What "verified" means is exactly those
checks; semantic truth is never claimed.

## What evidence a fresh reader sees

Inventory, proposition (statement, OK evidence, revisions, rule,
bindings, candidates, questions, evaluator status, coverage), subject
(receipt, mechanical facts, manifestation, bound/candidate propositions,
questions), binding (both reconstructed evidence texts, rule, method,
support/resolution, receipt). Judgments add the case's cited assertions
with reconstructed support, the evaluator rule, and an unknowns
explanation (because-texts, questions, gaps, context requests) without
automatic follow-up.

## Supported/unsupported Judgment behavior

Preserved accepted semantics: APPLIES/DOES_NOT_APPLY/UNKNOWN
applicability; ESTABLISHED findings; CONFORMS/CONFLICTS/UNKNOWN
conformance only with APPLIES (DOES_NOT_APPLY carries `conformance:
None`); missing/uncertain bindings under INCOMPLETE coverage yield
UNKNOWN, never CONFLICTS. Covered proposition + correct subject →
APPLIES + CONFORMS/CONFLICTS by recorded path. Handler-mismatched
subject → DOES_NOT_APPLY. Same-handler unbound subject → UNKNOWN with
explanation. Generic, other-route, or provenance-mismatched propositions
→ `UNSUPPORTED_EVALUATOR` (structurally distinct from epistemic UNKNOWN:
no artifact, explicit reason plus supported scope). Durably constructed
but unevaluatable propositions remain fully inspectable; judgeability is
not a prerequisite for knowledge.

## What remains absent

No Investigation continuation (UNKNOWN exposes why + questions/gaps
only), no W0/W1 compare/diff, no Decision/Adoption/Action/Admission/
proposal/current-pointer machinery, no cross-snapshot identity, no
generic registry or profile engine, no CLI, no frontend or agent harness.
No Core change; no new architectural abstraction. Optional hardening
deferred from Phase 1 stays deferred.

## Post-review integrity corrections

Independent review
([CONFIG_ROUTE_DESIGN_SLICE_PHASE2_REVIEW.md](CONFIG_ROUTE_DESIGN_SLICE_PHASE2_REVIEW.md),
verdict JUDGMENT INTEGRITY BLOCKER) demonstrated the bundle verifier
accepted selective Cases with recomputed artifacts, certified manually
evaluated unsupported propositions, and passed broken retained evidence.
Fixed without redesign; the review is left intact and the sections above
now describe corrected behavior:

- Canonical Case verification added: the verifier reconstructs the
  canonical Case for the recorded request (W/P/S/question/case ID) with
  production `assemble_case` and requires exact agreement on world ID,
  resolved address, revision, case ID, question, proposition/subject
  selectors, and normalized facts including support fingerprints. Bundles
  now record the request at top level; older request-less bundles fail
  shape validation.
- Evaluator eligibility verified: the verifier rediscovers support from
  the opened World with the same bounded rule Judge uses. Manually
  packaged unsupported propositions fail `evaluator_supported`.
- Broken evidence rejected: any relied support item not reconstructing
  `OK` yields `INVALID_CASE` from fresh Judge and verification failure
  for old bundles. Inspect still reports `FAILED` honestly; damaged
  Worlds stay unjudgeable, never silently verified.
- Fingerprint scope clarified: `database_fingerprint` covers exactly
  `world.sqlite` bytes. Retained-blob integrity is enforced per item at
  read time (handle digests), gated by the evidence-OK rule, so blob
  corruption fails Judge and verification despite an unchanged database
  hash. Sidecars such as `world.admission.json` are read by neither
  Inspect nor Judge and are outside the authenticated set.
- Bundle no-clobber fixed: exclusive creation refuses existing paths
  including dangling symlinks (no atomic-publish claim; truncated files
  fail verification as structured negatives).
- Malformed bundles are structured failures (`readable`/`shape` checks),
  never uncaught exceptions. Artifact inspection and verdict comparison
  are guarded so malformed artifacts (missing keys, non-dict shapes,
  non-dict findings) yield `artifact_shape`/`verdict_reproduced`
  negatives rather than `KeyError`/`TypeError`/`AttributeError`; a
  non-list supplied `facts` value fails `canonical_match` the same way.
  Bundle no-clobber opens with `O_CREAT|O_EXCL|O_NOFOLLOW`, so symlinks
  are refused by the creation call itself, not only by the pre-check.
- `conformance_unknown` fixed: true only for an actual conformance result
  of `UNKNOWN`; `DOES_NOT_APPLY` reports false with empty because-text.
- Historical replay limitation documented: W0 records statement,
  profile ID, rule, and evidence — not evaluator implementation,
  parameters history, or transitive dependencies. Verification replays
  under the compatible installed implementation; package B cannot
  guarantee package A's historical semantics. The method fingerprint is a
  consistency aid, not proof of historical identity.
- Evaluator duplication (`config_routes/evaluate.py` vs the repository
  fixture evaluator) intentionally retained with the cross-check test;
  two-place maintenance risk acknowledged, no framework introduced.
