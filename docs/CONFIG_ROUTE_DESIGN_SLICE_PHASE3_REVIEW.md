# Config-route Design slice Phase 3 independent review

Status: **independent adversarial production review**, 2026-09-28. Not architecture authority and not an implementation plan. Reviewed the uncommitted working tree against the Phase 2 baseline `14a2685c597b6d0dae9989983aa1d638ba22f829`. Production code and observed executions take precedence over the Phase 3 report. No production code, tests, commit, push, or next phase was made by this review.

## Verdict

**PROPOSAL INTEGRITY BLOCKER.** A genuine guarded `UNKNOWN` can produce and persist a verified proposal for an unasserted field that the caller did not focus on. The fixed, generic question prose is treated as a field selector, and the investigator returns the first matching field in canonical JSON key order. In a real constructed W0 with an extra `proposition` field, no focus yielded `PROPOSAL` for `proposition`; `question_focus="subject"` and even `question_focus="missing"` yielded the same `proposition` proposal. The record did not establish or admit a World assertion, but it falsely represented what this bounded investigation selected. The current proposal path is therefore too broad to freeze. Malformed-bundle verifier exceptions and an in-W0 persistence path also need repair.

## Executable path and actual guarantees

`investigate_config_world` (`ontology_author/config_routes/investigate.py`) opens a config World through `open_config_world_view`, which checks the seal and opens `ConstructionWorld` read-only. It gets a fresh guarded `judge_config_world` result or verifies a supplied Judgment bundle with `verify_judgment_bundle` against the opened exact address and checks the requested P/S. Phase 2 reconstructs the canonical Case, checks evaluator support, citations and `OK` support, and replays the artifact. The Phase 3 eligibility predicate accepts only artifact applicability `UNKNOWN`, or `APPLIES` with conformance `UNKNOWN`; refusals are `INVESTIGATION_NOT_APPLICABLE`. `UNSUPPORTED_EVALUATOR` has no usable artifact and stays distinct from epistemic `UNKNOWN` in both paths. A normal config route can exercise the first eligible branch; its required route fields make the second branch difficult to reach through honest Phase 1 construction, although the predicate implements it.

The facade derives a question from the first Judgment context request, or an open question, and optionally sets `structured_need` from `question_focus`. It gives `investigate_bounded_case` one same-World `manifestation-text` capability. That rule inspects published mechanical subject relations and a reconstructed manifestation. A relevant extra JSON field takes priority and becomes a `PROPOSAL`; otherwise missing published subject facts can form a same-publication expanded Case; otherwise it returns `UNRESOLVED`. The facade adds an explanation and optionally writes an external JSON bundle. The bundle reader parses JSON; the verifier opens the recorded World, reruns guarded Judge with the recorded case ID, requires the same eligible artifact, derives the question again, reruns the investigator, compares the stored outcome/receipt/proposal/case, and checks citations or proposal basis. It does not call Construction, admission, a publisher, or any World writer.

The generic `software_governance/investigation/` package remains profile-neutral. `expanded_case` uses existing Judgment `assemble_case` and `verify_case`, rejects another publication address/World ID/revision and a removed parent assertion ID; record factories only make questions, receipts, and proposals. It has no config route imports, publishing path, registry, planner, admission, or mutation. Its direct expansion test produces a genuine added `config_route` citation. Generic `expanded_case` itself does not demand `OK` reconstruction or authenticate a caller-supplied parent; the guarded Phase 3 parent and the bundle verifier provide those conditions in this product path.

## Adversarial findings

### 1. The relevance rule selects an unasked field (blocking)

`_relevant` at `investigate.py:757` returns true when a JSON key occurs as a **substring of the generated prose**, even when `structured_need.property` names a different field. `_unpublished` at line 744 returns the first matching key. Because the manifestation is serialized with sorted keys, a producer-unasserted `proposition` can precede `subject`, `owner`, or a missing requested property. An independent constructed World with fields `owner`, `proposition`, `subject`, `binding`, `approved`, and others produced:

| Caller focus | Actual outcome/payload |
| --- | --- |
| none | `PROPOSAL {field: proposition, value: governance_binding(P,S)}` |
| `subject` | same `proposition` proposal |
| `missing` | same `proposition` proposal |
| `owner` | `owner=data-platform` proposal |

The normal no-extra-field same-handler case returned `UNRESOLVED`; an `owner`-only World without focus also returned `UNRESOLVED`. Thus this is a real conditional defect, not a claim that every UNKNOWN proposes. The fixed question supplies the accidental `proposition` match; the caller does not need to write arbitrary prose. The fixture cross-check reproduces this decision rule rather than independently validating its product semantics.

**Why it matters:** the persisted, verifier-approved proposal can answer a different question, and a reserved-looking source key can look like a semantic proposition. **Required invariant:** the candidate field must be the explicitly requested top-level source property, or a property explicitly named by an evaluator request under a well-defined rule; unrelated boilerplate words must not select it. **Minimal fix:** when `structured_need.property` is nonempty, require exact key equality and do not fall back to question-text matching. For an open question with no named property, leave extras as observations and return `UNRESOLVED` unless a separate bounded, explicit relevance rule exists. **Required regression:** no-focus and missing/wrong focus with a `proposition` extra remain unresolved; `focus="subject"` cannot return `proposition`; an exact `owner` focus still proposes `owner`.

### 2. Proposal schema permits assertion-looking material (blocking companion)

`_manifested_extras` at line 711 accepts any top-level extra JSON value, including arrays, objects, booleans, numbers, and `null`; `_proposal` copies that value into `payload`. The generic `make_proposal` and the verifier reject an `assertion_id` **key directly in** payload or basis, but neither prevents `payload.field == "assertion_id"` or a nested value such as `{"assertion_id":"forged-a123"}`. Both real proposals verified in an independent W0. `binding=yes`, `approved=true`, and `proposition=governance_binding(P,S)` also produced valid mechanical proposals when focused. The basis necessarily quotes raw source text, so no literal-string ban on source data is possible; the defect is that the **proposal payload** can carry assertion-shaped or governance-shaped material without a stricter source-field boundary. No real World assertion ID was minted, and no World assertion was added.

**Why it matters:** a downstream consumer could treat a payload labelled `assertion_id` or a nested assertion object as an established identity, despite the current record's `mechanical` class and `not an assertion` reason. **Required invariant:** proposal payloads remain plainly observed source fields/values, never an assertion identity or semantic binding. **Minimal fix:** explicitly bound the product rule to supported top-level scalar source values and reject reserved identity/semantic field names from proposal selection, or use unmistakably source-observation names and enforce that shape in replay/support checks. Retain such source material in inspection without proposing it. **Required regression:** focused `assertion_id`, nested assertion-shaped objects, and governance-looking keys cannot be mistaken for established claims; ordinary scalar `owner` remains a proposal. This is a product rule correction, not a new generic framework.

### 3. Malformed bundles can escape as exceptions

The verifier docstring promises structured negatives for malformed bundles. It only validates the outer key sets and selected World/request/trigger types. `_replay_mismatch` at line 620 calls `.get` on a stored receipt without checking its type; `receipt=None` or `[]` raised `AttributeError`. `_proposal_basis_errors` at line 700 uses a supplied `payload.field` as a dict key without a string check; a list/dict raised `TypeError`. `_support_errors` calls `verify_case` on a supplied child without guarding its shape; `{}`, `facts=None`, or malformed facts raised `KeyError`/`TypeError`. All came from parseable in-memory bundle objects; no false positive was observed.

**Why it matters:** a cold verifier can crash on attacker-controlled persisted JSON instead of returning a bounded verification result. **Required invariant:** every malformed JSON-compatible bundle fails with a structured negative, and malformed children never reach citation functions. **Minimal fix:** validate receipt, proposal field, and expanded Case shapes before replay/support checks and guard citation inspection. **Required regression:** each concrete malformed value above returns `verified: false` without an exception.

### 4. Caller-selected persistence can write inside W0

The normal sealed W0 root and evidence directory have mode `0555`, and normal tested persistence outside W0 leaves every file byte-identical. But `open_config_world_view` checks write bits only on the bundle root and `world.sqlite`, while `write_investigation_bundle` accepts any `persist_to` path. In a temporary W0, after making only `governance_evidence/` writable, the root and database still passed the seal check. `investigate_config_world(..., persist_to=W0/governance_evidence/I-inside.json)` returned `PROPOSAL` and created that file under W0; the before/after directory hash changed. The initial permission change was external, but the new file was written by the Investigation product path. No established assertion was changed, yet the absolute “Investigation never mutates W0” claim is false for this accepted address and caller path.

**Why it matters:** historical directory preservation should not depend on every descendant's mode remaining unchanged. **Required invariant:** no Investigation artifact path resolves inside its input World directory. **Minimal fix:** reject `persist_to` under the resolved World root before creating parents or opening the target. **Required regression:** an otherwise readable W0 with a writable child directory refuses in-World persistence and retains identical file hashes; external persistence still succeeds.

### 5. A support check is narrower than its label suggests

`_proposal_basis_errors` at line 674 parses the retained manifestation and proves `payload.field` exists at the top level with exactly `payload.value`; it does **not** merely search for the value in text. It also checks the `OK` reconstruction, basis scheme/location/digest/text. A forged key sharing the true value returned `support_sound: true`, because that key/value was genuinely present, but `replay_match: false` and overall `verified: false` because it was not the focused field selected by a fresh replay. The overall verifier therefore rejected the tested wrong-field forgery. The two checks have distinct meanings; `support_sound` alone does not prove relevance or selection. `_proposal_basis_errors` reimplements JSON extraction separately from `_manifested_extras`; one shared bounded extraction rule would reduce semantic divergence. This is justified reuse, not a request for an abstraction to reduce line count.

### 6. Expanded-case verifier has a dormant comparison gap

The canonical Phase 2 Case contains every published mechanical fact for the selected subject, so `added_assertion_ids` was empty and normal Phase 3 never emitted `CASE_EXPANDED`. The facade correctly returns `UNRESOLVED` when there are no additions. A direct generic thin-Case test produced a citation-complete same-World child. If a future product path does produce a child, `_replay_mismatch` compares child identity fields and a sorted **multiset** of whole facts, and `_support_errors` checks citations and `OK` evidence. It does not compare the child `inspected_relations` field or exact child key set. This is dormant in the current canonical path but should be closed before claiming comprehensive expanded-case bundle replay. A stored child with removed or altered exploration metadata should fail; fact order may remain semantically irrelevant. Generic `expanded_case` also checks parent assertion IDs as a set, so its direct API does not by itself detect duplicated or forged parent facts; the product's canonical trigger prevents that input.

## Other boundary results

- **Trigger and supplied Judgment:** Phase 2's verifier is called before using a supplied Case/artifact. Its current canonical Case, eligibility, evidence-OK and replay checks reject selective Cases, recomputed UNKNOWN artifacts, unsupported evaluator artifacts, wrong selectors/question/case ID, and tampered relied evidence. Fresh decided results and `DOES_NOT_APPLY` refused explicitly. `UNKNOWN_PROPOSITION`, `UNKNOWN_SUBJECT`, `INVALID_CASE`, and `UNSUPPORTED_EVALUATOR` refused explicitly. No caller Case parameter exists.
- **World binding:** recorded resolved absolute address, World ID, integer revision and SHA-256 of `world.sqlite` are checked. Relative paths and symlinks resolving to W0 verify; a byte-identical copy at a different address fails `exact_address`; an explicit W1 override fails. This is a location binding plus current database fingerprint and per-item evidence reconstruction, not a signed or complete-directory fingerprint. Unread sidecars are outside the authenticated set; in-place replacement with identical bytes at the same path is not distinguishable. No current pointer is read.
- **W0 immutability:** entire-directory file hashes stayed equal after `UNRESOLVED`, `PROPOSAL`, external persistence, verification, no-clobber failure, and external W1 construction in normal tests/probes. Production opens the World read-only. An explicit probe made only a retained-evidence child directory writable, then passed an in-W0 `persist_to`; Investigation created the bundle there and changed the directory hash. The seal check still accepted the World. Thus normal behavior is read-only, but the absolute product-path guarantee is false.
- **Evidence damage:** corrupt or removed governance/software support prevents guarded Judge from yielding a usable trigger; Phase 2 tests cover both blob classes. A damaged manifestation that is relied on by the canonical Case likewise yields `INVALID_CASE`, rather than an ordinary absent-field proposal. `_unpublished` alone would decline a non-OK manifestation and `_explain` labels the status; the guarded product trigger is the decisive failure. The database hash covers SQLite only; retained blobs are checked through cited evidence reconstruction.
- **Unresolved meaning:** the normal same-handler unbound case reports missing established `governance_binding(P,S)`, sibling bound and candidate subjects, open questions, `INCOMPLETE` coverage/gaps, inspected relations, and manifestation status. It does not say that binding ought to exist or infer a conflict/negative/`DOES_NOT_APPLY`. The `missing` field's alternative “or another published assertion answering the question” is broad but not a recommendation to assert one.
- **Question and provenance:** caller controls only a property-name focus, not the prose, purpose, origin, evaluator context request, or published evidence. Context requests come from the verified trigger. Receipt `inspected_relations` and question origin explain exploration, not support; a proposal's basis is reconstructed manifestation material, while an expanded Case uses citations. Search found no persisted hidden reasoning, thoughts, analysis trace, planner state, or scratchpad.
- **Proposal extraction:** production uses `json.loads` on a digest-checked canonical route-record manifestation, takes top-level keys, excludes `id/path/handler` and already published mechanical role names, and copies the parsed value. It does not search for values as substrings. Escaping, Unicode escaping, whitespace, repeated values in other fields, nested-only keys and value-only mentions did not fabricate a focused top-level field. The producer parses original JSON with Python's last-key-wins behavior and reserializes a canonical record; duplicate input keys are not retained as separate values. The observed typed top-level object/array/null support is broader than a scalar-only claim.
- **Replay and persistence:** question, receipt and proposal are compared by Python equality, so lists in those records are ordered and duplicates matter. Expanded facts are sorted whole JSON records, retaining multiplicity while allowing fact order changes. Altered focus/question/trigger ID/basis/location/receipt fields and duplicate inspected relations failed in probes. A complete recomputation for a different legitimate focus can of course produce another verifying bundle; the JSON is replay-verifiable, not signed historical authorship. Persistence uses `O_CREAT|O_EXCL|O_NOFOLLOW`; existing file, directory, dangling symlink and symlink to a file were refused. A truncated file failed parsing. Concurrent creation is protected by `O_EXCL`; no atomic-publication or crash durability claim is made.
- **Cold handoff and code drift:** a clean wheel installed outside the repository passed four separate processes A/B/C/D: construct W0, inspect/judge UNKNOWN and persist J0, investigate using only W0+J0 and persist I0, verify J0/I0 using only W0+durable bundles. No source workspace or construction report was passed after A. Compatible installed schema/readers, Phase 2 grammar/evaluator, question derivation, relevance, extraction, investigator decision and verifier logic remain ambient. Package B can turn an old `UNRESOLVED` into `PROPOSAL` or reject an old proposal by changing these rules; replay under B proves B's current result, not package A's historical executable semantics. There is no code archive.
- **Correction/history:** a caller changed the other route's handler and constructed W1 at a fresh address. W1's rediscovered subject judged `DOES_NOT_APPLY` with positive handler-mismatch basis; this shows a later World where the old question no longer applies, **not** resolution of W0's missing governance binding. W0 hashes, J0 and I0 verification remained intact after W1. W1 has a different subject ID; Phase 3 does no cross-snapshot matching by route ID/path/manifestation.
- **Architecture and usefulness:** the 795-line facade contains bounded orchestration, a copied profile decision rule, explanatory reads, persistence, and replay verification; it does not duplicate Case assembly or Judgment evaluation and introduces no workflow, agent state, admission, decision/action, queue, registry, or current pointer. It is larger than a thin facade in ordinary wording, but no new framework is hidden. The useful capability is real: it explains the epistemic gap and inspects retained manifestation material, with a narrow `owner` proposal. The current proposal selector makes that utility unsafe to freeze. Construct, Inspect, Judge and Investigate are callable product surfaces, but the minimum usable bounded loop is not yet integrity-complete.

## Test quality and verification record

The 14 Phase 3 tests contain strong constructed-World paths for UNKNOWN, proposal, W0 hashes, decided/refused states, persistence, evidence damage, W1 correction and separate-process handoff. The fixture equivalence test is an implementation echo: it compares the installed rule against a copied rule and therefore misses their shared relevance bug. The tests lack a no-focus reserved-key control, focus priority control, nested assertion-shaped payload control, wrong-key/same-value control, malformed inner-bundle types, and a post-W1 I0 verification assertion. The Phase 2 suite supplies strong canonical-Judgment and blob-damage regressions, but cannot validate Phase 3 proposal semantics. Temporary probes lived under `/tmp`; no production or tracked test file was modified.

| Gate | Observed result |
| --- | --- |
| Phase 3 | 14 passed |
| Phase 2 | 43 passed |
| Phase 1 | 44 passed |
| Existing config profile | 7 passed |
| Judgment acceptance | 12 passed |
| Investigation acceptance | 8 passed |
| Construction acceptance | 20 passed |
| Core acceptance | 18 passed |
| Combined focused command | 166 passed |
| Configured default `pytest -q` | 87 passed |
| `git diff --check` | passed |
| `uv build` | sdist and wheel built |
| Clean-wheel UNKNOWN handoff | A/B/C/D succeeded; J0 and I0 verified |

The configured default gate is not the whole historical suite. The clean wheel required a compatible installed implementation. A package build is not publication.

## Classification

| Boundary | Result | Limit |
| --- | --- | --- |
| UNKNOWN eligibility | VERIFIED | Honest evaluator UNKNOWN only; unsupported distinct. |
| Canonical trigger integrity | VERIFIED | Supplied Judgment passes current Phase 2 verifier first. |
| Exact World association | VERIFIED | Resolved-address identity; not a signed directory identity. |
| W0 immutability | FALSE / REGRESSION | In-W0 `persist_to` writes when a child directory is writable despite the root/database seal check. |
| UNRESOLVED honesty | VERIFIED | Normal missing binding is explained without a negative inference. |
| PROPOSAL boundedness | FALSE / REGRESSION | Unfocused or mismatched focus can select a `proposition` field; assertion-shaped payloads allowed. |
| Proposal extraction integrity | PARTIALLY VERIFIED | Structured top-level parse and exact value; overbroad types/names/relevance. |
| Proposal verification integrity | PARTIALLY VERIFIED | Overall replay rejects tested wrong-field forgery; malformed types can crash; `support_sound` alone is weaker. |
| CASE_EXPANDED integrity | PARTIALLY VERIFIED | Correctly unreachable normally; child metadata comparison is incomplete. |
| Investigation replay verification | PARTIALLY VERIFIED | Honest replay strong; malformed inner shapes escape as exceptions. |
| Damaged-evidence handling | VERIFIED | Guarded trigger rejects relied broken evidence. |
| Artifact persistence | VERIFIED | Exclusive no-clobber; no atomic-publish claim. |
| Cold-agent handoff | VERIFIED | Four clean-wheel processes, compatible code. |
| Installed-package dependence | PARTIALLY VERIFIED | Dependency explicit; historical semantics are not archived. |
| Architecture boundary | VERIFIED | No new framework; facade responsibility remains product-local. |
| Product usefulness | PARTIALLY VERIFIED | Explanation and mechanical discovery useful; selector unsafe. |
| Minimum-loop completeness | NOT VERIFIED | Four surfaces exist, but proposal integrity blocks freeze/use claim. |

## Required answers

1. **Canonical guarded Judgment only?** Yes, for the production entrypoint: fresh Judge or Phase 2-verified supplied bundle.
2. **Unsupported/non-UNKNOWN entry?** No; each refuses explicitly. `UNSUPPORTED_EVALUATOR` is not `UNKNOWN`.
3. **Forged supplied Judgment trigger?** Tested selective/tampered/unsupported forms fail the Phase 2 verifier; no arbitrary Case is accepted.
4. **Exact W0 binding?** Yes by resolved address, ID, revision, SQLite hash, and relied evidence checks, with the stated non-cryptographic scope.
5. **W0 byte-identical?** Yes in tested normal outcomes, external persistence, verification, failure, and later W1 construction; no as an absolute guarantee, because in-W0 `persist_to` wrote a new file in a writable child directory.
6. **CASE_EXPANDED unreachable normally?** Yes: canonical Phase 2 Case includes all published subject mechanical facts, so no additions remain.
7. **Judge weakened?** No.
8. **UNRESOLVED honest?** Yes for the ordinary same-handler unbound case.
9. **Missing versus damaged evidence?** Yes through guarded Judge's `INVALID_CASE` and `OK` reconstruction requirement; damage does not become a trustworthy proposal.
10. **What can `question_focus` influence?** It sets `structured_need.property`, question ID, and thus proposal relevance, but prose fallback can override the intended field and choose an earlier key.
11. **Can focus establish semantics?** No World assertion, binding, admission, or publication occurs; it can induce a misleading durable proposal.
12. **Extraction?** Parsed top-level JSON from the reconstructed canonical manifestation, not text search.
13. **Text collisions/escaping/nesting?** They did not forge top-level key/value; nested objects and arrays are themselves accepted values, creating a different payload risk.
14. **Verification key/value or occurrence?** Exact parsed top-level key/value plus live basis; relevance is established only by fresh replay, not `support_sound` alone.
15. **Real value, wrong field verify?** The tested forgery failed overall replay even when both fields held the same value; its `support_sound` could still be true.
16. **Assertion ID in proposal?** No actual World assertion ID is created, but a source field named `assertion_id` or a nested `assertion_id` value can enter a verified payload. This violates the strong wording of the boundary.
17. **Proposal mutates W0?** Normal proposal path does not; persistence path placement caveat in answer 5.
18. **Proposal constructs/publishes W1?** No.
19. **Exploration versus support provenance?** Separate: receipt inspection versus manifestation basis/case citation.
20. **Hidden reasoning persisted?** No such fields found.
21. **Evidence corruption fail closed?** For relied trigger/manifestation blobs, yes; malformed bundle types are a separate verifier exception defect.
22. **Expanded Cases complete and same-World?** Direct generic assembly uses same World and citations; product parent is canonical and product verifier requires `OK`. Dormant child metadata comparison gap remains.
23. **Selective recomputation?** Simple/selective edits fail replay; a complete rerun for a different valid focus can verify as a different investigation. No signed authorship claim.
24. **No-clobber?** Yes for existing entries and symlinks; `O_EXCL` handles concurrent target creation.
25. **Fresh A/B/C/D handoff?** Yes with exact W0, J0, I0 and compatible installed wheel.
26. **Installed-code assumptions?** Schema, readers, Phase 2 evaluator and all Phase 3 question/relevance/extraction/replay rules.
27. **Historical drift?** Yes: later compatible code may change a replayed outcome or reject a prior bundle.
28. **W0→W1 proof?** W1's changed software makes P inapplicable to a rediscovered S; it does not fill W0's missing binding.
29. **Cross-snapshot identity?** None assumed in Phase 3.
30. **New architecture?** No framework, registry, workflow, current pointer, or admission path.
31. **795-line facade?** Large but mostly product orchestration/replay; copied bounded rule and duplicated proposal parsing deserve focused correction, not size-driven abstraction.
32. **Single most serious defect?** The verified proposal can name a field unrelated to the explicit focus, selected by generic question prose.
33. **Ready to freeze?** No: **PROPOSAL INTEGRITY BLOCKER**.
34. **Minimum usable bounded product?** The four navigation operations exist, but the claimed integrity of Investigate is not complete.
35. **Next step?** Repair and regress the bounded proposal selector and verifier input handling, then use real examples to assess value. No basis here requires a new subsystem or W0/W1 comparison first.
