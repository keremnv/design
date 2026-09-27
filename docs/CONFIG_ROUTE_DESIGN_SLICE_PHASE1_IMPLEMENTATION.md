# Config-route Design slice Phase 1 implementation

Status: implementation report / production slice evidence, 2026-09-27.
Not architecture authority. The contracts remain
[construction](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md),
[acceptance](SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md), and
[Core baseline](CORE_PRODUCT_V1_BASELINE.md); executable code and tests
take precedence over this note.

## What production surface now exists

Installed Python facade (no fixture imports, no CLI in this slice):

```python
from ontology_author.config_routes import construct_config_world
report = construct_config_world(
    software_source="workspace/software.json",
    governance_source="workspace/governance.md",
    output="out/W0",
    profile="config.routes/v1",
    expected_software_revision=None,   # optional sha256 hex
    expected_governance_revision=None, # optional sha256 hex
)
```

- Package: `ontology_author/config_routes/` (`producer.py`, `rules.py`,
  `construct.py`). It depends on generic Software Governance construction
  and existing evidence/World primitives; it does not import
  `profiles/*`, historical authority/semantic-binding/governance-checkout,
  or any MCP/graph layer.
- Result: `ConfigRoutesReport` with `to_dict()`/`to_json()`: profile,
  exact absolute publication address, source identities, consumed and
  expected revisions, propositions/subjects/bindings/candidates/questions,
  coverage, gaps, unsupported/skipped, evaluator mapping, and
  validation/errors. Durable facts remain in the sealed World and retained
  evidence; the report is ephemeral product output.
- Generic changes (application only, no Core change):
  `ontology_author/software_governance/construction.py` seals staging
  before exclusive publication and records optional `establishment_rule`;
  `reads.py` exposes it. Existing fixture builders keep working.

## Supported profile inputs

The caller provides only:

- `software_source`: existing regular JSON file (bounded form below).
- `governance_source`: existing regular `.md` file (bounded form below).
- `output`: fresh publication directory; must not exist (file, dir,
  symlink, or empty dir all refuse without overwrite).
- `profile`: must equal `config.routes/v1`.
- `expected_software_revision`, `expected_governance_revision`: optional
  hex or `sha256:`-prefixed digests.

The caller does not supply snapshot-local subject IDs, proposition IDs,
route subject IDs, or Python constants. The profile derives deterministic
snapshot/subject IDs (`snapshot:<sha32>`, `route:<sha16>:<id>`),
proposition IDs, domain relations, bindings/candidates/questions, coverage,
gaps, and evaluator mapping, and reports them.

## Declared establishment rules

Versioned rules in `ontology_author/config_routes/rules.py`
(`PROFILE_ID = config.routes/v1`):

- `config.routes.proposition/v1:specific`
  `<subject> must use the approved <route-id> route.`
  (`route-id = [A-Za-z0-9][A-Za-z0-9_-]*`, case-sensitive).
  `<subject>` holds one requirement's subject phrase: no `.`, `?`, `!`,
  and no embedded `must use` requirement (see Post-review corrections).
  ID `proposition:<route-id>-route`,
  domain `<route-id snail>_route`.
- `config.routes.proposition/v1:generic`
  `<subject> must use an approved route.`
  ID `proposition:approved-<slug>-route` (hash suffix on collision).
- `config.routes.binding/v1`: exact route-ID match only. One binding when
  the named ID exists (SOURCE_EXPLICIT, DETERMINISTIC); otherwise no
  binding, one UNRESOLVED question, and a `missing_route_*` gap. Never
  fuzzy-matches (`customer-export-v2` does not satisfy `customer-export`).
- `config.routes.candidate/v1`: generic yields one candidate per parsed
  route (SOURCE_GENERIC, AMBIGUOUS) and never a binding.
- `config.routes.question/v1`: explicit UNRESOLVED question for every
  unbound proposition.
- `config.routes.coverage/v1`: always INCOMPLETE with basis
  “only the correspondences established by config.routes/v1 rules from the
  supplied source pair are recorded” and gaps (`supplied_correspondences_only`
  plus missing/unsupported/generic/evaluator gaps as applicable).
- `config.routes.evaluator/v1`: declares the only judgment rule
  `config.customer_export_route/v0` (`CustomerExport`, `/customers/export`)
  and maps it to `proposition:customer-export-route` / route
  `customer-export`. Any other proposition reports
  `evaluator_rule_not_declared` instead of silently reusing it.

Each proposition, binding, and candidate records `establishment_rule`
plus `construction_method`, `profile_id`, support/resolution (bindings and
candidates), and reconstructible observations. Questions, completeness
claims, and known gaps carry profile-level provenance (`profile_id` and
`contract`) but no per-row `establishment_rule`. Identical supported
paragraphs deduplicate to one proposition (reported in `skipped`);
distinct colliding wordings get hash-suffixed IDs.

## Supported and refused source forms

Software JSON (production producer):

- Supported: regular UTF-8 file; top-level object; non-empty `routes` list;
  each route an object with non-empty string `id`/`path`/`handler`; unique
  IDs; pretty-printed or compact JSON; extra fields preserved in the
  canonical manifestation but not interpreted.
- Refused (no publication): missing/not-a-file, invalid JSON, top-level
  non-object, missing/empty/non-list `routes`, non-object route, missing or
  non-string/empty `id`/`path`/`handler`, duplicate IDs, route span without
  exactly one `"id": "<id>"` match (flexible whitespace, string-aware brace
  scan), or a span that does not enclose its `"id"` match (for example a
  nested object before the `"id"` key; see Post-review corrections).

Governance Markdown:

- Supported: regular `.md` file, UTF-8, with at least one paragraph matching
  a rule pattern above (bounded Markdown subset).
- Refused (no publication): missing/not-a-file, non-`.md` suffix, non-UTF-8,
  no paragraphs, or zero supported paragraphs. Non-matching paragraphs yield
  no proposition; they are listed in `unsupported` with a
  `unsupported_governance_statements` gap. A supported plus an unsupported
  paragraph publishes the supported one with an explicit gap.

Deliberate strictness (supported vs explicitly unsupported vs known
limitation — no syntax expansion in this slice):

- Supported: single-line paragraphs, single spaces, lowercase `must use`
  / `the approved` / `an approved` keywords, route IDs matching
  `[A-Za-z0-9][A-Za-z0-9_-]*`, subjects without `.`/`?`/`!` or embedded
  requirements, `.md` suffix, UTF-8 bytes.
- Explicitly unsupported / fail-closed: wrapped (multiline) requirement
  text, double spaces, other modals/capitalization/negation, route IDs
  with dots/spaces/quotes (producible in JSON but unnameable in
  governance), multi-requirement or rule-embedding paragraphs, non-`.md`
  suffixes. These yield `unsupported` entries (or whole-construction
  refusal when nothing supported remains), never silent interpretation.
- Known limitation: non-ASCII route IDs written with standard
  `json.dump` (default `\uXXXX` escaping) are refused because the bounded
  byte locator seeks literal UTF-8; literal-UTF-8 JSON is required.

## How binding basis is recorded

No new evidence model. Binding/candidate grounding contains two checked
observations:

- governance paragraph (`markdown`, `governance.md@sha256:<gov>`,
  `bytes:<para span>`);
- software route record (`json`, `software.json@sha256:<soft>`,
  `bytes:<record span>`).

Both blobs are retained under `governance_evidence/` and both reconstruct
`OK` via existing `reconstruct_governance_observation`. Extras record
`relation_support`, `endpoint_resolution`, structured `software_evidence`
(`config_route record_id=<id> location=/routes/<i> subject=<subject>`),
`establishment_rule`, `profile_id`, and `contract`. The endpoint receipt
(`software_subject`) and canonical manifestation remain ordinary reads.
`GovernanceView.inspect_governance_binding` shows both evidence texts, so a
fresh reader answers “why does P concern S” without reading profile source.

## How expected revision is enforced

No pre-read. The software producer reads once (`Path.read_bytes`), computes
`consumed = sha256(bytes)`, and compares to normalized expected before any
World write; mismatch raises `ExpectedRevisionMismatch`, discards staging,
and publishes nothing. Governance acquisition is symmetric: one
`read_bytes`, one digest, compare, then `MarkdownSource(..., data=bytes)`
reuses those exact bytes. Tests prove single acquisition, consumed-vs-R1
comparison, R1-still-succeeds-after-R2-appears-post-read, and mismatch
refusal with both revisions reported. No retry, no relabeling.

## How safe publication works

Generic `construct_software_governance` now implements:

```text
copy software world to staging
assert governance + write blobs/sidecars
validate staging (fail -> no publication, discard staging)
seal staging (fail -> no publication, discard staging)
exclusive rename staging -> fresh final address
```

- Final address never exposes writable/unsealed state: seal precedes rename;
  rename preserves read-only bits.
- Exclusive publication (support is intentionally Linux-first for the
  strong guarantee): on Linux with `renameat2(RENAME_NOREPLACE)`, the
  rename is a true exclusive no-clobber publication — an existing file,
  directory, symlink, or empty directory refuses without overwrite, even
  under a race. The fallback path (other platforms, or kernels/mounts
  without `renameat2`) is check-then-rename: it fails safe for the
  realistic pre-existing-address and World-vs-World cases (a winner's
  non-empty World makes a loser's `rename` fail), but it is NOT a general
  race-proof no-clobber primitive — an empty directory appearing between
  the re-check and `rename` could be replaced. Deterministic collisions
  return failure without overwrite on both paths.
- Validation/seal/publication failures return errors with no final bundle;
  unique producer staging plus fixed `.sg-work` cleanup leaves no fake World.
- Tests inject validation, seal, and rename failures deterministically and
  assert no `lexists(output)`; an order test asserts seal precedes rename.

## What W0→W1 history test proves

`test_w0_survives_w1_construction_unchanged` and
`test_new_snapshot_does_not_inherit_old_binding`:

- W0 from `(software R0, governance “... customer-export ...”)` at `W0`;
  byte-hash every file under `W0`.
- Edit only workspace governance to `Health checks must use the approved
  health route.` (same grammar, no Python edit); construct `W1` at a fresh
  address.
- W0 hashes identical; W0 still opens; W0 binding evidence still `OK`;
  W1 is a distinct address with `proposition:health-route → health` and no
  `customer-export` binding.
- Removing a bound route in W1 yields `missing_route_*` with zero bindings:
  no ID/path/similarity inheritance across snapshots.

Coverage stays INCOMPLETE; `absence_is_negative` remains false for unbound
subjects, so empty results are not false negatives.

## What remains intentionally absent

No Inspect/Judge/Investigation facade or CLI, no World diff/compare command,
no Decision/Adoption/Action/Admission/proposal/current-pointer machinery, no
cross-snapshot identity, no generic profile engine or rule DSL, no frontend
or agent harness, no OA Application Runtime. Evaluator consistency is
construction-time declaration plus report gaps only; no guarded Judgment
call was built.

## Audit-gap classification

- fixed fixture inputs: FIXED (explicit workspace/source/profile/output/
  expected inputs; facade derives and reports IDs).
- implicit semantic mapping: FIXED (versioned proposition/binding/candidate/
  question/coverage/evaluator rules with per-assertion `establishment_rule`).
- weak correspondence basis: FIXED (two checked observations plus structured
  software reference, rule, method, and receipt; fixture path unchanged).
- duplicate/unsupported producer inputs: FIXED (duplicate rejection,
  bounded JSON validation, flexible-span locator, pretty+compact support,
  parsed-vs-published inventory checks).
- expected-revision handoff: FIXED (single-acquisition consumed-vs-expected
  for software and governance; mismatch refuses with no publication).
- publication ordering/exclusivity: FIXED (seal-before-exclusive-rename,
  no-clobber, injected-failure proofs; no partial/fake Worlds).
- evaluator/source consistency: PARTIALLY FIXED (declared evaluator mapping,
  covered-vs-gap report, unsupported text refuses instead of reusing stale
  semantics; no Judge facade yet).
- workspace cold-start construction: FIXED (non-fixture tmp workspaces,
  no caller IDs, exact address + evidence + coverage verification).

No audit assumption was falsified. No Core change was required.

## Post-review corrections

Independent review
([CONFIG_ROUTE_DESIGN_SLICE_PHASE1_REVIEW.md](CONFIG_ROUTE_DESIGN_SLICE_PHASE1_REVIEW.md),
verdict READY AFTER SMALL FIXES) found two fail-open bugs plus
documentation overclaims. Fixed without redesign; the review is left
intact and the sections above now describe corrected behavior:

- R1 fixed: a paragraph holding two requirements (or rule-like text in
  the subject) previously matched one proposition rule and silently
  dropped all but the last requirement. Subjects now exclude `.`/`?`/`!`
  and embedded `must use`; such paragraphs are UNSUPPORTED (reported, or
  whole-construction refusal when nothing supported remains).
- R2 fixed: `_object_span` could return a nested object's span that
  excluded the `"id"` match, mis-grounding the route and any binding.
  Every accepted span must now enclose its `"id"` match
  (`start <= id_match.start()`, `id_match.end() <= end`); otherwise
  construction is refused with no publication.
- Publication fallback guarantee clarified: true no-clobber holds on
  Linux with `renameat2(RENAME_NOREPLACE)`; the fallback is
  check-then-rename, fail-safe for realistic cases but not a general
  race-proof primitive. Repository/product support for the strong
  guarantee is intentionally Linux-first.
- `establishment_rule` wording corrected: recorded on propositions,
  bindings, and candidates; questions/completeness/known gaps carry
  profile-level provenance only.
- Profile strictness documented: supported vs explicitly unsupported vs
  known limitation for wrapping, spacing, route-ID characters,
  `\uXXXX`-escaped non-ASCII IDs, and the `.md` requirement.

Deferred (not readiness blockers, per the review): post-publication
inventory verification raises rather than returning a report on
impossible inconsistency; fixed `.sg-work` makes same-output concurrent
publishers interfere messily (fail-closed, no overwrite possible).
