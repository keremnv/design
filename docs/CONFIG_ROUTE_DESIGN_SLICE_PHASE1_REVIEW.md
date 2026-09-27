# Config-route Design slice Phase 1 review

Status: independent production review, 2026-09-27.
Not architecture authority, not implementation plan.
Implementation report:
[CONFIG_ROUTE_DESIGN_SLICE_PHASE1_IMPLEMENTATION.md](CONFIG_ROUTE_DESIGN_SLICE_PHASE1_IMPLEMENTATION.md).
Prior audit:
[MINIMUM_USABLE_DESIGN_PRODUCT_AUDIT.md](MINIMUM_USABLE_DESIGN_PRODUCT_AUDIT.md).

This review traces code and executes behavior; where the implementation
report and the code disagree, the code wins. No production code was changed
for this review.

## 1. What the production path actually does

`construct_config_world(...)` (`ontology_author/config_routes/construct.py`):

1. Normalizes optional expected revisions (hex or `sha256:`); rejects
   malformed digests. Rejects `profile != "config.routes/v1"` and any
   pre-existing `output` (`lexists`: file, dir, symlink, empty dir).
2. Creates a unique producer staging dir beside `output`
   (`.config-routes-<pid>-<uuid8>`).
3. `produce_routes` stats the software file (`is_file`, no content
   pre-read), reads it **once**, hashes to `consumed`, compares to expected
   (mismatch raises before any World write), validates bounded JSON
   (object, non-empty `routes` list, per-record non-empty string
   `id`/`path`/`handler`, unique IDs), locates each record span with a
   flexible-whitespace `"id"` regex plus string-aware brace scan, writes a
   mechanical World (`config_member`, `config_route`), and self-checks
   parsed-vs-published counts.
4. `_acquire_governance` stats the governance file, requires a `.md`
   suffix, reads it **once**, hashes, compares to expected, reuses those
   exact bytes in `MarkdownSource(..., data=bytes)`, and requires at least
   one paragraph.
5. Builds one `SourceObservation` per unique paragraph (first occurrence's
   span), runs `extract_propositions` (SPECIFIC/GENERIC regexes, dedup
   identical statements, hash-suffix ID collisions), and refuses with no
   publication when zero supported paragraphs exist.
6. For each proposition emits specs: SPECIFIC with a found route ID gets
   one binding grounded by **two** observations (governance paragraph +
   software record span); SPECIFIC with a missing ID gets a question + gap;
   GENERIC gets one candidate per route plus a question and never binds.
   Coverage is always INCOMPLETE with explicit gaps. Evaluator mapping is
   computed per proposition (covered only for customer-export).
7. Calls generic `construct_software_governance`, which copies the producer
   World to fixed `.sg-work`, asserts governance rows, writes blobs and
   sidecars, validates, **seals staging**, then exclusive-renames to the
   final address.
8. Post-publishes, reopens the sealed World read-only and verifies
   `config_route`/`software_subject`/`config_member` counts and values
   match the parsed source (raises on mismatch — see §11).
9. Returns `ConfigRoutesReport` (also on failures, with staged cleanup and
   `lexists(output)` false).

## 2. Hidden fixture knowledge

Searched all of `ontology_author/config_routes/`:

| Occurrence | Classification |
|---|---|
| `customer-export`, `CustomerExport`, `/customers/export` in `rules.py` evaluator constants + covered sets | Intentional bounded profile contract, but fixture-inherited values elevated to contract. Isolated to the report/evaluator mapping; construction and binding rules do not depend on them. A fresh workspace with other IDs builds honestly with explicit evaluator gaps. Phase 2 Judge must revisit the single-route evaluator. |
| `proposition:customer-export-route` in covered set | Same as above (evaluator routing only). |
| Exact source sentences | None in production code (regex grammar only). |
| Repository-relative paths, `PROFILE_ROOT`, fixture filenames | None. Handles use the caller-supplied basenames (`target.name`), so any workspace filename works. |
| Known subject/proposition IDs as inputs | None required; all derived. |
| Fixed paragraph order | None; source order preserved but order-independent. |
| Hard-coded route meaning | None in binding/proposition rules. |
| `.md` suffix requirement | Intentional bounded contract (explicit, fail-closed). |

No hidden fixture dependency blocks cold start. Remaining assumptions are
documented in §17.

## 3. Proposition establishment

Accepted (after strip, full-paragraph match, case-sensitive, single spaces):

- SPECIFIC `"<subject> must use the approved <route-id> route."`,
  `route-id = [A-Za-z0-9][A-Za-z0-9_-]*`, emits
  `proposition:<route-id>-route` grounded by the paragraph observation,
  rule `config.routes.proposition/v1:specific`.
- GENERIC `"<subject> must use an approved route."`, emits
  `proposition:approved-<slug>-route`, rule
  `config.routes.proposition/v1:generic`.

Correctly rejected (probed): missing period, `MUST`/`Approved`,
negation, modal swaps, plural `routes`, missing ID, bad ID starts,
dotted IDs, embedded quotes, double spaces, interior newlines.

**Finding R1 (fail-open): multi-sentence paragraphs are swallowed.**
`SPECIFIC_RE`'s subject group `.+?` admits periods, so one paragraph
containing two requirements —
`"Customer export must use the approved foo route. Health must use the
approved bar route."` — matches as ONE specific proposition about `bar`
with the `foo` requirement absorbed into the subject phrase. Verified
end-to-end: publishes one proposition, one binding to `bar`, **zero**
unsupported entries and no gap mentioning `foo`. The `foo` text survives
verbatim in the statement/blob, but it has no proposition, candidate,
question, or gap. The same holds for a subject embedding
`"must use the approved"`. A narrow grammar must not silently drop a
stated requirement; such paragraphs should be unsupported. Small fix:
exclude sentence terminators (and ideally the keywords) from the subject
group.

Related narrowness (fail-closed, acceptable but should be documented):
interior newlines never match (`.` without DOTALL), so normally wrapped
Markdown paragraphs become unsupported; double spaces never match;
software IDs containing dots/spaces/quotes are producible but unnameable
by the grammar (dots/spaces verified producible, grammar rejects them).

## 4. Binding establishment

Every positive `governance_binding(P,S)` arises from exactly one rule:
P is a SPECIFIC proposition naming route ID `r`, and the parsed software
universe contains exactly one record with ID `r` (duplicates are refused
upstream, lookup is exact case-sensitive dict match). The binding is
grounded by the governance paragraph observation plus that record's byte
span, with structured `software_evidence`
(`record_id=<id> location=/routes/<i> subject=<subject>`), rule
`config.routes.binding/v1`, method
`config.routes.binding/v1:exact-route-id`, and the ordinary
`software_subject` receipt + canonical manifestation.

Falsification results (probed or tested): missing route → question + gap,
no binding; duplicate route → whole construction refused; renamed route
(`customer-export-v2` vs `customer-export`) → no binding; same path and
handler but different ID → no binding (identity is by ID only, as
declared); materially different handler with same ID → still binds (the
rule is ID correspondence, not conformance — correct per the binding
contract; conformance is a later judgment concern); generic → candidates
only; unsupported → no proposition at all; multiple plausible endpoints
only arise for generics, which never bind. The convenience-lookup concern
does not materialize: the lookup key is the source-named ID under an
exact-match rule, with duplicates eliminated before lookup.

**Finding R2 (wrong evidence span, silently accepted): nested object
before the `"id"` key.** `_object_span` uses `rfind(b"{")` before the ID
match, which lands on an inner brace when a nested object precedes `"id"`
in file order. Probed:
`{"meta": {"a": 1}, "id": "x", ...}` yields span `bytes:21:29` (8 bytes:
the inner `{"a": 1}`), containing **neither** the ID nor the path — yet
construction succeeds with that span as the route's grounding and binding
basis. A fresh reader sees software text unrelated to the route. Small
fix: verify the computed span encloses the ID match (refuse otherwise),
or scan backwards with depth counting to the true enclosing object.

## 5. SOURCE_EXPLICIT / DETERMINISTIC

Justified for bindings within the declared rule. The governance source
literally names the endpoint ID string, and the endpoint is selected by an
exact, total, deterministic function over (named ID, parsed ID set) with
no judgment, ranking, or tie-breaking. `DETERMINISTIC` here describes the
licensed correspondence procedure (declared rule over explicit material),
matching the construction contract's definition, not merely reproducible
execution. The contrast class is honest: generic candidates use
`SOURCE_GENERIC`/`AMBIGUOUS`. The labels would overstate only if the
grammar hole (R1) or span bug (R2) is hit; both are fixed at their source
rather than by relabeling.

## 6. Both sides of binding evidence

Verified by fresh read (`open_governance_world` only): two evidence
entries, both `status OK`; handles parse to blob filenames whose bytes
hash to the handle digests; governance text is the full paragraph;
software text is the route record bytes. A reader answers "why P concerns
S" from the retained bytes plus the recorded rule/method/reference
without profile source or fixture knowledge. Digest/span integrity holds
for the flat records the grammar realistically pairs; R2 bounds the
exception (span valid but wrong content when nesting precedes `"id"`).

## 7. Producer inventory

Verified: duplicates refused; pretty and compact JSON accepted with
correct spans; malformed records, wrong types, empty/whitespace-only
fields, empty lists, non-object tops refused; extra scalar fields
preserved in canonical bytes; key order without nesting fine; braces in
values handled by string-aware scan; escaped quotes handled (span
correct; naive decoded-substring check fails only due to JSON escaping,
not a bug); every accepted route yields exactly one subject receipt, one
member row, one route row, one manifestation, with parsed-vs-published
counts checked twice (producer self-check + post-publication verify).

Fail-closed narrowness (acceptable, document): non-ASCII IDs written with
standard `json.dump` (default `ensure_ascii=True`, `\uXXXX` escapes) are
refused with "0 matches" because the span regex seeks literal UTF-8;
a nested object containing `"id": "<same>"` (2 matches) is refused;
route IDs containing `"` are unlocatable. R2 remains the one fail-open
exception. Coverage reporting is accurate: the report counts equal World
rows (tested), and nothing is silently skipped except identical-paragraph
dedup, which is reported in `skipped`.

## 8. Expected revision

Verified for both sources. No content pre-read exists: only `is_file`
stats precede the single `read_bytes`; consumed digests come from the
acquired bytes; comparison happens before any World write (software) and
before `MarkdownSource` construction over the same bytes (governance).
Mismatch paths discard staging and publish nothing, reporting both
revisions. The post-acquisition-mutation probe (R2 written immediately
after the producer's read, promise R1) succeeds consuming exactly R1,
proving consumed-vs-expected rather than check-then-trust. No race can
publish wrong bytes under a promise: the promise is checked against what
was consumed, not what is live.

## 9. Publication atomicity and exclusivity

Traced `construct_software_governance`: fixed `.sg-work` staging,
writable copy, assert, blobs/sidecars, `validate_governance_world` (fail →
discard, no publication), `_seal_world(work)` (fail → discard, no
publication), `mkdir -p` parent, `_exclusive_rename` (fail → discard, no
publication). Existing file/dir/symlink/empty-dir all refuse; injected
validation/seal/rename failures leave `lexists(output)` false (tested).

`renameat2(RENAME_NOREPLACE)` implementation: correct constants
(`AT_FDCWD=-100`, flag `1`), `fsencode`d paths, `use_errno` handling,
`ENOSYS`/`EINVAL` → fallback, `EEXIST` → `FileExistsError`, others →
`OSError`. Probed active on this machine (`True`): second publisher and
empty-dir victim both refused with victim intact.

Fallback (`os.path.lexists` re-check + `os.rename`): **not truly
no-clobber under a race.** It is safe against the realistic
World-vs-World race (a winner's non-empty directory makes the loser's
`rename` fail), but an empty directory appearing between re-check and
rename is silently replaced by POSIX `rename` semantics. The code
docstring is honest ("fails safe for the deterministic cases"); the
implementation report's "no-clobber" phrasing omits the fallback's
empty-dir hole. Classification: exclusivity VERIFIED on Linux with
`renameat2`; PARTIAL elsewhere. For a foundational guarantee, state the
platform dependence explicitly.

Two further warts (fail-closed, not blockers): `.sg-work` is a fixed name
shared by concurrent same-output publishers (producer staging is unique,
but both publishers discard/share `.sg-work`, so they interfere with
confusing errors rather than one clean win — no overwrite is possible);
`publication.parent.mkdir` after seal is fine.

## 10. Sealed-state integrity

Rename preserves modes (verified: no write bits on bundle or
`world.sqlite`); full-read suite (`propositions_for_subject`, binding
inspect, completeness, manifestation, mechanical facts) leaves every byte
identical; direct SQLite write rejected (`OperationalError`); blobs,
sidecars, and metadata all sealed (recursive `rglob` chmod). Normal reads
cannot mutate the publication. (Root/owner chmod-back remains possible as
documented; sealing is not a sandbox.)

## 11. Failure cleanup

Every failure route returns a structured report with no final bundle and
no residue: profile mismatch, existing address, producer/JSON/duplicate
refusals, governance refusals, zero-proposition refusal, generic
validation/seal/rename failures. Leftover-staging check after success is
empty. Prior publications byte-identical after later failures (tested).

**Minor wart:** `_verify_published_inventory` runs after successful
publication and **raises** instead of returning a report. Reachable only
on internal inconsistency (counts cannot mismatch by construction), but if
hit, the caller gets an exception with a publication already in place —
outside the "every failure returns a report" contract. Suggest wrapping
or documenting; not a blocker.

## 12. W0 → W1 history

Independently reproduced (report's test plus own probe): W0 constructed,
every file hashed; governance corrected to a new in-grammar endpoint
(`health`) with no Python edit; W1 constructed at a fresh address. W0
hashes identical; W0 still opens with binding evidence `OK`; W1 address
differs and binds only `health`; route removal in W1 yields
`missing_route_*` with zero bindings. Bindings are re-derived from W1
rules + W1 evidence in every case; no ID/path/similarity inheritance
exists in the code path (lookup is per-construction over freshly parsed
routes). Rename/removal pressure passes.

## 13. Evaluator consistency

Mechanism: `rules.py` declares one evaluator
(`config.customer_export_route/v0`, `CustomerExport`, `/customers/export`)
covering `proposition:customer-export-route` / route `customer-export`;
`evaluator_status` marks every other proposition `unsupported` with gap
`evaluator_rule_not_declared`, included in the report per proposition and
as a World `governance_known_gap`. A new governance sentence for another
route publishes successfully (correct — construction is correspondence,
not judgment) while the report explicitly withholds evaluator coverage,
so no old evaluator can later be silently selected by an honest Phase 2
reader of the report. Limitation (honest, partial): per-proposition
covered/unsupported routing and the rule parameters live only in the
report + profile source; the World carries just the coarse gap ID. The
system does not imply every proposition is judgeable — the gap says the
opposite — but a World-only reader cannot route judgment. Acceptable for
Phase 1 (no Judge built); Phase 2 must define evaluator discovery and
must not treat report-only routing as durable truth.

## 14. Construction report honesty

The report is a useful product result, not a second source of truth, with
one noted exception. Publication address, profile/rules, consumed and
expected revisions, inventory, questions, gaps, and errors all summarize
or are reconstructible from the World and retained blobs (revisions appear
as `source_revision`s; unsupported paragraph text is recoverable from the
retained governance blob; `skipped` duplicates add no new fact). The
exception is per-proposition evaluator routing + rule parameters (§13):
indispensable for future judgment, absent from the World. Flagged, not
blocking, since no consumer yet judges from the World alone.

## 15. API/package boundary

`ontology_author/config_routes/` is a thin bounded product/profile layer:
`producer.py` (mechanical JSON→World, no governance knowledge),
`rules.py` (pure versioned grammar/ID/evaluator data + functions),
`construct.py` (orchestration + report). It composes generic
`software_governance` construction/validation/reads, existing Markdown
evidence, and World primitives. No duplicated assertion logic (specs flow
into the generic constructor), no new evidence model (existing
observations + blobs), no generic profile framework (two regexes + dict
lookups), no parallel publication semantics (the generic fix is shared by
fixture paths too). The small spec extension (`establishment_rule`,
optional, backward compatible) belongs in the generic layer and does not
fork it. Nothing should move; nothing generic was built to deduplicate.

## 16. Packaging

Independently verified beyond "build succeeded": fresh `uv build`
produces a wheel containing exactly
`ontology_author/config_routes/{__init__,construct,producer,rules}.py`
and no `profiles/`; clean-target install (`pip install --target` a temp
dir, `PYTHONPATH` pointed there, cwd outside the repo) imports the
package from the installed location and cold-constructs a sealed World
from a temp workspace. No repository-only or test imports in the package
(`grep` shows only stdlib + `ontology_author.{config_routes,evidence,
software_governance,world}`).

## 17. Cold-start user test

Simulated with only paths + profile name + optional revisions (also from
the clean install): construction succeeds and the report supplies every
derived identity. Undocumented assumptions encountered: (a) wrapped
(multi-line) or double-spaced Markdown sentences never match (§3);
(b) software IDs outside `[A-Za-z0-9][A-Za-z0-9_-]*` are producible but
unnameable; (c) non-ASCII IDs via default `json.dump` are refused (§7);
(d) the report's `output` is absolute on success but as-given on failure.
None blocks a careful caller; (a)–(c) should be one paragraph of profile
docs.

## 18. Product-thesis test

After Construction a fresh reader of W0 + report can answer: which
propositions (rows + statements), which subjects (receipts + route rows),
which-concerns-which (bindings/candidates), why (two-sided evidence +
rule/method/reference), what is unresolved (questions + gaps), what bytes
were retained (blobs), what scope was claimed (INCOMPLETE + basis), and
which rule licensed each proposition/binding/candidate
(`establishment_rule`). Gaps in the "every rule" claim: questions,
completeness, and known-gap rows record only `profile_id`, not a rule ID
(`QuestionSpec` has no `establishment_rule` field; verified extras), and
candidate/question rule identity is only partly surfaced in reads. Small
doc-or-schema fix: either record the rule on questions or correct the
report's "each semantic assertion" sentence.

## 19. Architecture regression

None introduced. Checked for: Admission subsystem, Action abstraction,
workflow/run model, generic application runtime, cross-snapshot identity,
Decision/Adoption, proposal lifecycle, generic EvidenceInput framework.
No equivalents under other names: `ConfigRoutesReport` is a frozen
dataclass result, not a run object; `_exclusive_rename` is a filesystem
primitive, not a workflow; evaluator mapping is a static dict, not a
registry. The generic `establishment_rule` extra is a provenance label,
not an admission authority.

## 20. Tests reviewed adversarially

Genuinely tested end-to-end: happy cold start with two-sided OK evidence,
compact JSON, duplicates, 10 malformed JSON shapes, governance form
refusals, missing/ambiguous/same-looking endpoints, both revision
mismatches + match, single-read acquisition, post-acquisition mutation,
existing file/dir refusal with byte-identity, order seal→rename,
injected validation/seal/rename failures with no publication, W0→W1
history + no-inheritance, evaluator covered/gap split, inventory
equality, JSON report shape. Mock-based but legitimate: the three
injected-failure tests and the order test assert wiring (the `renameat2`
primitive itself is untested in-tree; this review probed it live).
A test that would still pass if semantics were wrong: none found for the
covered branches — assertions check World rows, not just report echoes.

Missing high-value tests (would have caught R1/R2): (1) multi-sentence /
rule-embedding paragraph must be unsupported (currently swallowed);
(2) nested-object-before-`"id"` record span must enclose the ID match
(currently wrong span accepted); (3) span-content assertion on happy path
(`"id": "<id>"` bytes inside each span); (4) near-miss grammar battery
(negation, modal/case/period/double-space variants reject). No
concurrency test is missing — deterministic injection covers what is
deterministic; the fallback race is a primitive limitation, not a test
gap.

## 21. Verification run

All observed in this review session, production code untouched:

- Phase 1 `tests/test_config_routes_phase1.py`: 35 passed
- Existing config profile: 7 passed
- Construction acceptance (construction + config + architecture): 30 passed
- Judgment/Investigation sanity: 20 passed
- Core acceptance: 18 passed
- Default gate `pytest -q`: 87 passed
- `git diff --check`: clean
- `uv build` + wheel contents + clean-install cold construct: verified
- Adversarial probes (grammar battery, span edges, fresh-reader
  reconstruction, renameat2 paths, multi-sentence E2E, read-stability):
  executed as `/tmp` heredocs, results cited inline above

## 22. Classification

- fixed fixture inputs: VERIFIED
- explicit semantic mapping: PARTIALLY VERIFIED (rules versioned and
  recorded for propositions/bindings/candidates; R1 swallows multi-sentence
  paragraphs; questions/completeness carry no rule ID)
- strong binding basis: PARTIALLY VERIFIED (two checked sides + rule +
  receipt for flat records; R2 mis-grounds nested-before-`"id"` records)
- duplicate/unsupported inputs: VERIFIED (fail-closed; R2 is a grounding
  bug, not an acceptance bug)
- expected-revision integrity: VERIFIED (both sources, no pre-read window)
- publication ordering: VERIFIED (seal precedes rename; failures publish
  nothing)
- publication exclusivity: PARTIALLY VERIFIED (true no-clobber via
  `renameat2` on Linux, probed active; fallback is check-then-rename with
  an empty-dir replacement hole)
- evaluator/source consistency: PARTIALLY VERIFIED (declared mapping,
  explicit per-proposition gaps, no silent reuse; routing is report-only)
- workspace cold-start construction: VERIFIED (tmp workspaces, clean
  install, no caller IDs)
- history preservation: VERIFIED (byte-identical W0, distinct W1,
  evidence reconstructs)
- no automatic binding carry: VERIFIED (per-construction re-derivation)
- package/installability: VERIFIED (wheel contents + clean-install build)

## 23. Independent verdict

**READY AFTER SMALL FIXES**

No publication-integrity blocker on the supported Linux path, no false
binding rule, no architecture regression. Two small semantic/evidence
fixes stand between this slice and a trustworthy foundation (R1, R2
below), plus honest doc corrections for the fallback and the
"each assertion" overclaim.

## 24. Smallest patch plan (not implemented)

**R1 — grammar swallows multi-sentence paragraphs.**
Why: a stated requirement vanishes with no proposition, question, or gap
(fail-open). Code:
[`rules.py`](/home/kerem/Desktop/Personal%20Projects/design/ontology_author/config_routes/rules.py)
`SPECIFIC_RE`/`GENERIC_RE` subject groups. Invariant: a paragraph matching
a rule contains exactly one requirement. Fix: exclude sentence terminators
from subjects, e.g. `(?P<subject>[^.?!]+?)`, and reject subjects
containing `must use` (one-line regex change + doc line). Test: the §3
two-requirement paragraph must yield `unsupported` (or two propositions —
either is honest if explicit; simplest is unsupported).

**R2 — span locator mis-grounds nested-before-`"id"` records.**
Why: accepted grounding points at bytes unrelated to the route,
corrupting the binding basis. Code:
[`producer.py`](/home/kerem/Desktop/Personal%20Projects/design/ontology_author/config_routes/producer.py)
`_object_span`. Invariant: each record span encloses its `"id"` match.
Fix: after computing `(start, end)`, require
`start <= match.start()` and `match.end() <= end`, else raise
`ConstructionError` (fail-closed; ~5 lines). Test: nested-before-`"id"`
fixture asserts refusal or enclosing span; happy-path test asserts each
span contains `"id": "<id>"`.

**R3 — doc corrections (no code):** (a) implementation report §"safe
publication": state fallback is check-then-rename, truly no-clobber only
with `renameat2` (Linux); (b) "each semantic assertion records
`establishment_rule`": restrict to propositions/bindings/candidates, or
add the field to `QuestionSpec`; (c) profile docs: one paragraph on
wrapping/whitespace strictness, unnameable ID characters, and
`\uXXXX`-escaped non-ASCII refusal.

Optional hardening (not required for readiness): wrap
`_verify_published_inventory` so its impossible-but-post-publish failure
returns a report noting the existing publication instead of raising; give
`.sg-work` a unique suffix to make same-output concurrency fail cleanly
instead of interfering mid-build.

## 25. Phase 2 readiness

Phase 2 (Inspect + guarded Judge) may proceed once R1–R3 land. Stable
interfaces to build on: `construct_config_world` signature and
`ConfigRoutesReport.to_dict()` keys; `PROFILE_ID`/`RULES` and the
`establishment_rule` + two-observation grounding shape on bindings and
candidates; the sealed-bundle layout with `governance_evidence/` blobs.
Phase 2 must define evaluator discovery itself and must not treat
report-only evaluator routing as durable truth. No Phase 2 design is
offered here.

