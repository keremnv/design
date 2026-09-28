# Config-route Design slice Phase 2 review

**Status:** independent adversarial production review, 2026-09-28. **Not architecture authority or an implementation plan.** Production code was not changed. This review treats executable behavior as stronger evidence than the Phase 2 implementation report.

## Verdict

**JUDGMENT INTEGRITY BLOCKER. Do not freeze or commit Phase 2 yet.** A normal, fresh installed process can construct, inspect, judge, persist, and verify the bounded example using only the exact World address after construction. The production Judge assembles a sound Case for the ordinary Phase 1 publication. Its independent bundle verifier, however, accepts a Case with published evaluator inputs removed and a newly computed `UNKNOWN` artifact. It also accepts a manually evaluated proposition that `judge_config_world` explicitly refuses as unsupported. This defeats the claimed meaning of a *verified* Judgment. Retained evidence can be corrupted without changing the recorded SQLite fingerprint, and a fresh Judge still returns `JUDGED` with failed evidence reconstruction.

The separate historical limitation is real: evaluator selection and behavior depend on the **currently installed** profile grammar, covered-route constants, evaluator parameters, and implementation/dependencies. The World records a proposition's statement, `profile_id`, and `establishment_rule`; it does not pin the old classification algorithm or evaluator parameters. The artifact records a method fingerprint but cannot supply the old executable semantics. This limitation can be documented for the bounded product after the integrity defects are fixed; it is not a reason to build an evaluator registry or archive executable code now.

## Code path reconstructed

`inspect_config_world` opens the address through `open_config_world_view`, which checks existence, a `world.sqlite`, non-writable bits on the bundle directory and database, three governance relation schemas, and at least one `software_subject` receipt for `config.routes/v1`. It then enumerates relation rows, uses `GovernanceView.completeness()`, and derives source revisions from assertion warrants. `inspect_proposition` gets its statement and grounding through `GovernanceView.inspect_governance_proposition`, looks up bindings/candidates/questions, and calls the installed `evaluator_for_statement`. `inspect_subject` reads its receipt, all producer relation rows naming that subject, and its retained manifestation. `inspect_binding` calls `GovernanceView.inspect_governance_binding`: the warrant's two observations reconstruct through digest-named retained blobs; extras carry the profile, rule, method, support and resolution labels; `local_manifestation_for_subject` reconstructs the software side. These are historical, snapshot-local reads. A row called `governance_binding` records an established *construction correspondence*, not adoption, authority, applicability, or current live alignment.

`judge_config_world` opens the same view, records resolved address, logical `world_id`, SQLite revision, and `SHA-256(world.sqlite)`. It checks the selected proposition and subject, verifies proposition `profile_id`, reruns `evaluator_for_statement`, assembles a Case with `assemble_case`, calls `verify_case` and `_verify_exact_association`, evaluates with installed `evaluate_route_case`, checks artifact shape/method/citation containment, and optionally writes JSON. The required call arguments are W/P/S; `persist_to` and caller-controlled `case_id` are optional. The generated default Case ID is deterministic (`P::S`), not a unique judgment identifier. The Case's question is fixed by this facade. A caller cannot skip those guards through this entry point.

`assemble_case` selects the named proposition and subject, their bindings/candidates/questions, global governance coverage/gaps, subject manifestation, and every producer relation row whose referent role names that subject. For the honest Phase 1 specific rule, the resulting Case contains the relevant `config_route`, binding, receipt, and proposition. `verify_case` checks **facts that are present**: each assertion ID exists in the opened World, values match, support is reconstructed, and the reconstructed and presented support hashes match. It does not check that required facts are present, the question or selected IDs, address, revision, profile, evaluator support, or reconstruction status `OK`. `verify_judgment_bundle` reopens the bundle's recorded address, runs those citation checks and today's evaluator, and compares today's artifact fields. It does not call the Judge's exact-Case check, rediscover evaluator eligibility, or reconstruct and compare a canonical Case.

The evaluator's effective inputs are: exactly one proposition and receipt; candidate presence plus total selected binding count; the selected binding; the first selected `config_route` row; subject kind; route handler and path; and installed rule constants (`applies_to_kind`, `required_handler`, `required_path`, `conformance_field`). Questions, gaps and coverage are included as context but are not consulted by its verdict code. A positive, recorded handler mismatch yields `DOES_NOT_APPLY` before any absence reasoning. With the required handler but no binding, it yields applicability `UNKNOWN`, including under `INCOMPLETE` coverage. With a binding but no route/path, it yields conformance `UNKNOWN`. The normal Phase 1 constructor emits at most one exact-route binding for a supported specific proposition, and the producer refuses duplicate route IDs; this supports the Judge's ordinary Case assembly. The verifier does not inherit that guarantee merely by checking citations.

## Reproduced adversarial results

All probes created temporary Worlds outside the repository and left production files unchanged. `true` below is the actual `verify_judgment_bundle(...)["verified"]` result.

| Probe | Observed result | Consequence |
| --- | --- | --- |
| Fresh sealed W0, normal J0 | `true`; `APPLIES/CONFORMS` | Ordinary path works. |
| Remove `config_route` fact from J0 Case, recompute artifact with installed evaluator | `true`; `APPLIES/UNKNOWN` | Verifier accepts an omitted published path. |
| Remove `governance_binding`, recompute artifact | `true`; applicability `UNKNOWN` | Verifier accepts omission of an established correspondence. |
| Remove `software_subject`, recompute artifact | `true`; applicability `UNKNOWN` | Verifier accepts omission of a published receipt. |
| Remove only candidates, gaps, or manifestation without recomputing artifact | `true` in this Case | No canonical-Case completeness check; unused inputs may disappear silently. |
| Directly assemble/evaluate `orders-export` Case and package it | `true`, `APPLIES/CONFLICTS`; official Judge returns `UNSUPPORTED_EVALUATOR` | Bundle verification does not enforce evaluator eligibility. |
| Change Case `world_address`, `question`, `proposition_ids`, or `subject_ids` independently | `true` for each | Case identity and selected question are not checked. |
| Flip verdict or remove applicability citation without recomputing | `false`, `verdict_reproduced` fails | Replay catches simple artifact edits. |
| Change applicability, finding status, subject/proposition fact values, add bogus citation, or change method version | `false` in each probe via shape, citation, or replay checks | Direct edits to evaluated/cited material are detected. |
| Change method ID | `false`, method and replay checks fail | Current method record is compared. |
| Corrupt retained governance blob, leave J0 unchanged | `false`, citations fail; SQLite hash unchanged | Original support fingerprint detects an uncoordinated blob edit. |
| Corrupt blob, rewrite Case support/status and support hashes to match failed reconstruction | `true`; SQLite hash unchanged | Bundle verifier accepts reconstructed `FAILED` evidence. |
| Fresh Judge on the corrupted W0 | `JUDGED`, with `FAILED` reconstruction in proposition/binding/coverage Case facts | Guarded Judge also treats a broken retained basis as verified. |
| Alter `world.admission.json` only | `true`; SQLite hash unchanged | Sidecar is outside the fingerprint; it is not consulted for this verdict. |
| Copy identical W0 to a new address and pass it as explicit World | `false`, exact address check | Recorded address blocks this simple substitution. |
| Copy identical W0; rewrite recorded and Case addresses | `true` | The JSON has no independent authenticity seal; consistency is all that is checked. |
| Move W0 after J0 | Old-address verification `false` (`world_readable`); rewrite both addresses and it becomes `true` | Exact path is a location binding, not a portable identity or signed claim. |
| Use Case from byte-identical W1 with W0 bundle/artifact | `true` | Case address is ignored by bundle verification. |
| Use materially different W1 by argument, or mix its Case/artifact with W0 | `false` via address/fingerprint/citation or replay checks | Different content is ordinarily detected. |
| Relative path or symlink alias to W0 | Resolved to W0; verification `true` | Alias resolution is coherent. |
| Change recorded bundle address to relative `W0`; change only Case address to relative `W0` | Recorded-address variant `false`; Case-address variant `true` | Bundle address is checked exactly; Case address is not. |
| Change installed `required_path` with W0/J0 unchanged | J0 verification `false`; a new Judge result changes to `CONFLICTS` while method version stays `v0` | Current parameters control history. |
| Judge a route with a positively different handler | Artifact `DOES_NOT_APPLY`, `conformance: null`, but `unknowns.conformance_unknown: true` | Explanation field mislabels non-applicability as epistemic uncertainty. |
| Change covered-route set or classification function after W0 | Inspect changes `covered` → `unsupported`; Judge refuses | Same W0 can become unjudgeable. |
| Force current routing to unsupported while verifying old supported J0 | J0 verification remains `true` | Verification does not rediscover support. |
| Change imported `facts` helper to hide `config_route` | New result `UNKNOWN` instead of `CONFORMS`; method fingerprint unchanged; J0 replay fails | Fingerprint omits behavior in imported dependencies. |
| Truncated JSON or missing artifact method | Raises `JSONDecodeError` or `KeyError`, respectively | Not falsely verified, but not a structured negative verification report. |
| Persist to a dangling symlink | Target file created through the link | `Path.exists()` is not an exclusive no-clobber write. |

The normal World has source revisions and digest-named blobs. A changed blob yields `FAILED` because reconstruction checks the blob's SHA-256 against the handle. That check is valuable, but `verify_case` compares *status/text representations* and never requires `OK`; a newly assembled or edited Case can faithfully record `FAILED` and pass. A wrong span, absent blob, or tampered manifestation is the same class of problem. The SQLite fingerprint authenticates exactly the SQLite bytes, not `governance_evidence/`, `program_inputs/`, or `world.admission.json`. The latter sidecar did not affect the tested verdict, while the evidence blobs did.

## Inspect truthfulness and independence

Cold inventory needed only W0 and returned the `config.routes/v1` receipt/profile label, software subjects with route IDs/path/handler, propositions, binding pairs, candidates, questions, `INCOMPLETE` coverage and known gaps, and software/governance source revisions. Initial IDs are discovered, not prerequisites. Per-item reads returned JSON-compatible dict/list/scalar values. A clean wheel install outside the repository ran separate Agent A/B/C processes: A constructed W0, B received W0 and selected P/S from inventory then judged and persisted J0, C received W0+J0 and got `verified: true`. The installed wheel contained the config-route modules; neither B nor C imported a repository profile, fixture, report, source workspace, or construction global. The retained source handles were basenames plus digests, not absolute workspace paths.

The inventory's `profile_id` is the installed constant selected after finding at least one matching software receipt; it is not an authenticated per-World construction manifest. On genuine Phase 1 output that label is correct. `inspect_proposition` reports `evaluator.status=covered` from today's installed grammar and rule constants, whereas Judge additionally checks the proposition's recorded `profile_id`; a malformed mixed-profile World could produce Inspect/Judge disagreement. The inspected `evidence.status=OK` means a digest-named blob and byte span reconstruct *now*; it does not certify source authority or semantic correctness. Source revisions are recorded historical revisions, not live source observations. `software_subject` is a snapshot-local receipt. `coverage=INCOMPLETE` is a recorded scope claim, not exhaustive knowledge. `binding` is a construction assertion with two recoverable source observations; `SOURCE_EXPLICIT`/`DETERMINISTIC` describe the producer's rule decision, not `APPLIES` or in-force governance. Inspect does not imply adoption, live alignment, or cross-snapshot identity.

One Judge output label is false even on an honest World: `_explain_unknowns` treats absent conformance (`None`) as `UNKNOWN`, so a legitimate `DOES_NOT_APPLY` artifact reports `conformance_unknown: true`. The applicability and conformance fields themselves are correct; the explanatory boolean should distinguish “not evaluated because inapplicable” from epistemic `UNKNOWN`.

On the supported flat JSON example, `inspect_binding` exposed the governance paragraph and software route record as separate `OK` reconstructions, the `config.routes.binding/v1` establishment label, exact-route-ID method string, support/resolution labels, profile ID, and the subject manifestation. `inspect_subject` supplied the receipt's snapshot/kind/producer and all mechanical facts. Together those reads answer why the proposition concerns the route: the named route ID in the paragraph exactly matches the retained route record. The binding read itself does not embed the complete receipt, and no read proves that the producer's semantic choice was objectively correct. Damaged blobs show `FAILED` in Inspect rather than masquerading as intact evidence. The open-view seal check examines only bundle/database mode bits, not every retained file's mode or content.

There is no `ConfigRoutesReport` dependency in the installed Inspect/Judge imports or calls. `evaluate.py` is a bounded installed profile evaluator, not a generic runtime. It duplicates the repository fixture evaluator's verdict logic; the cross-check test covers a few matching branches, but future semantic fixes need attention in both copies. This is temporary profile duplication, not an architecture regression; a generic evaluator framework is not warranted by the present evidence. No new Action, Admission, Decision, current pointer, proposal lifecycle, cross-snapshot identity, or generic profile engine appeared in the Phase 2 modules.

### Phase 2 test quality

The 13 Phase 2 tests have meaningful construction-to-read and construction-to-Judge paths, including a new subprocess, unsupported generic/other-route propositions, same-handler unbound `UNKNOWN`, positive handler exclusion, address refusal, and one persisted bundle. They use real Worlds rather than mocked warrant/evaluator results. The subprocess sets `PYTHONPATH` to the repository, so the separate clean-wheel handoff above adds packaging evidence. The fixture equivalence test compares a few verdict branches, but its three assembled Cases do not exercise a conflicting route path, evidence corruption, evaluator drift, or verifier eligibility. The tamper test flips a result and drops a fact without recomputing an artifact; it therefore misses the central selective-Case failure. The substitution test overrides the World address but does not mix Cases and artifacts from byte-identical publications. High-value regression cases are the four forged-bundle and damaged-evidence probes in the patch plan, not more count-based coverage.

## Installed-code and historical guarantee

The World retains statement, profile ID, and establishment-rule label. `evaluator_for_statement` reclassifies that statement with the **installed** regex and checks the **installed** covered-route set. It does not compare a World-retained evaluator rule version, code digest, parameter record, or old classification result. `evaluate_route_case` uses today's constants. An artifact method record contains method ID/version, rule parameters, and a fingerprint of functions defined in `evaluate.py`; it does not transitively fingerprint imported `facts`, `artifact_shell`, or other dependencies. The same method string and even fingerprint can accompany changed behavior, as the helper monkeypatch showed.

With package A constructing W0 and judging J0, package B can usually read the same SQLite schema and evidence if it preserves those formats. B may call W0 judgeable or unsupported differently. B's verifier can reject J0 because its current evaluator differs, or accept it when today’s replay matches; acceptance does **not** prove that B recovered A's semantics. B cannot promise a historically equivalent new Judgment unless it has the compatible A semantics externally. The exact guarantee achieved is **same-installed-code, current-rule replay over cited Case facts**, conditional on mutable installed dependencies. Installed package compatibility is a legitimate external handoff assumption, but it must be explicit; “derived from durable World content alone” and unqualified “historical reproducibility” are false.

## Classification

| Claim | Classification | Reason |
| --- | --- | --- |
| Cold Inspect independence | VERIFIED | Clean installed, separate process, W0-only read. |
| Inventory completeness | PARTIALLY VERIFIED | Complete for tested Phase 1 rows; profile label and revision meaning have stated scope. |
| Binding evidence reconstruction | PARTIALLY VERIFIED | Both sides reconstruct in intact W0; damaged basis is visible but not fatal to Judge. |
| Evaluator discovery | PARTIALLY VERIFIED | No report/registry; mutable installed grammar and routing decide support. |
| Unsupported versus epistemic `UNKNOWN` | FALSE / REGRESSION | Judge separates them; verifier accepts a manually evaluated unsupported proposition. |
| Guarded Case assembly | VERIFIED | Entry point assembles all selected Phase 1 evaluator facts in tested Worlds. |
| Case verification | FALSE / REGRESSION | Citations validate presence, not semantic completeness or successful reconstruction. |
| Exact World association | PARTIALLY VERIFIED | Judge and explicit World override check address; verifier ignores Case address. |
| Publication fingerprint | FALSE / REGRESSION | SHA-256 covers only `world.sqlite`; relevant evidence is outside it. |
| Bundle tamper detection | FALSE / REGRESSION | Recomputed selective Case/artifact and changed Case metadata verify. |
| Verdict reproducibility | PARTIALLY VERIFIED | Replay checks current evaluator output over supplied Case, not historical or complete Case. |
| Artifact persistence | PARTIALLY VERIFIED | Normal write/read works; dangling symlink bypasses no-clobber; partial files fail by exception. |
| Cold Judge | VERIFIED | Clean installed B judged W0 from discovered P/S. |
| Cross-process handoff | PARTIALLY VERIFIED | Honest A/B/C works; C can also bless forged/incomplete bundle. |
| Installed-package independence | NOT VERIFIED | Current grammar, rule constants, evaluator code/dependencies remain external. |
| No architecture regression | VERIFIED | Bounded facade/evaluator; no new generic lifecycle machinery. |

## Smallest patch plan — not implemented

1. **Verifier accepts selective Cases and unsupported artifacts.** Why: a published binding/path can be omitted to make `UNKNOWN`, and a proposition Judge refuses can be certified by the verifier. Affected: `ontology_author/config_routes/judge.py` `verify_judgment_bundle`; `ontology_author/software_governance/judgment/case.py` only if a reusable helper is needed. Required invariant: verification must establish that the Case is the canonical full Case for exactly the recorded W/P/S/question under a currently declared evaluator, before replay. Minimal fix: rediscover profile/evaluator support from the opened proposition; require one selected P and S, exact Case address/revision/question, and compare Case facts/inspected relations with fresh `assemble_case` using the recorded Case ID. Then verify citations and replay. Regression: remove binding/route/receipt and recompute artifact; manually package an unsupported proposition; change Case selectors/question/address; all must fail named checks.
2. **Broken retained evidence passes Judge/verification.** Why: the SQLite hash stays fixed while a blob changes; a fresh Judge generates `FAILED` support and still marks it verified. Affected: `inspect.py` `publication_fingerprint`, `judge.py` validation, and/or `judgment/case.py` support checks. Required invariant: every evidence item relied on by a judged Case must reconstruct `OK`, and the recorded publication identity must bind all retained verdict-relevant files. Minimal fix: reject non-`OK` reconstruction for the bounded Case and compute/check a deterministic bundle fingerprint over SQLite and retained evidence (plus sidecars if described as part of the authenticated World); reject missing/extra unexpected files or symlink escapes. Regression: corrupt/remove governance and manifestation blobs, wrong span, altered sidecar, and recomputed support; none may verify or produce `JUDGED` against a supposedly intact W0.
3. **No-clobber persistence has a symlink hole.** Why: a dangling symlink passes `exists()` and `write_text` follows it; concurrent writers can also pass the check. Affected: `judge.py` `write_judgment_bundle`. Required invariant: an existing path entry is never followed or replaced. Minimal fix: exclusive creation (`x`/`O_EXCL`) with symlink refusal; if atomic publication is claimed, write a sibling temp and install exclusively before reporting success. Regression: existing file, dangling symlink, concurrent same target, and truncated write. Truncated JSON currently cannot verify, so atomicity is a reliability concern, not a demonstrated false-positive integrity path.
4. **Historical replay wording overclaims.** Why: W0 cannot select package-A semantics under package B by itself. Affected: Phase 2 report/API documentation, and version-handling policy for this bounded profile. Required invariant: say that support/replay require a compatible installed implementation; do not call the SQLite hash a full-World fingerprint. Minimal fix: document this limit and make mismatch explicit rather than silently claiming historical equivalence. Regression: controlled rule/coverage/dependency drift tests assert the documented behavior. No executable-code archival or generic registry is required for this patch.
5. **`conformance_unknown` mislabels an inapplicable result.** Why: `DOES_NOT_APPLY` has no conformance evaluation, yet the explanation says it is unknown. Affected: `judge.py` `_explain_unknowns`. Required invariant: that boolean is true only for an actual conformance result of `UNKNOWN`. Minimal fix: test the non-null result explicitly. Regression: handler mismatch yields `conformance: None` and `conformance_unknown: false`; a missing path after `APPLIES` yields true.

## Verification record

- `uv sync --locked --extra dev`: passed.
- `npm ci --prefix frontend`: passed; npm reported dependency audit advisories unrelated to this review.
- Focused Phase 2, Phase 1, existing config profile, Judgment, Investigation, Construction, and Core acceptance command: **122 passed**.
- Default `uv run --extra dev pytest -q`: **87 passed**. This is the configured default gate, not the whole historical suite.
- `git diff --check`: passed before this document; rerun after writing it.
- `uv build`: built sdist and wheel. `npm run build --prefix frontend`: passed and refreshed bundled assets from the already-modified frontend tree; review its generated diff as part of that separate work.
- Clean wheel install with three separate processes outside the repository: construct `A=True`; inspect two subjects and one proposition with both binding observations `OK`; judge `JUDGED/APPLIES/CONFORMS`; later bundle verification `true`.
- Temporary adversarial scripts in `/tmp/phase2_review_probe*.py` produced the results above; no production or test file was changed by the probes.

## Required answers

1. **Can a fresh process inspect W0 with only its exact address?** Yes, with a compatible installed package.
2. **Construction-session state?** No; no report, fixture, workspace source, or global is read.
3. **Inventory honesty?** Mostly for genuine Phase 1 W0; labels describe recorded historical rows, but profile and judgeability are partly installed-code interpretations.
4. **Both sides of accepted binding?** Yes on intact W0 via binding plus subject reads; both digest-checked observations reconstruct. Damaged evidence is labeled `FAILED`.
5. **Evaluator support from durable World state?** Partly: retained statement/rule/profile are inputs; installed routing determines the answer.
6. **Installed-code assumptions?** Compatible schemas/evidence readers, grammar, covered set, evaluator parameters, evaluator logic and imported Judgment helpers.
7. **Can evaluator behavior drift?** Yes; parameter and dependency probes changed verdicts after W0.
8. **Can W0 become differently judgeable?** Yes; coverage/classification monkeypatches changed support.
9. **Acceptable under claimed guarantee?** Only if compatible installed code is stated as an external prerequisite; the current unqualified durability claim is not.
10. **Does guarded Judge require only W/P/S?** Yes for a normal call; it owns Case assembly, question, evaluator, verification and artifact. Optional persistence/Case ID inputs do not bypass its guards.
11. **Is Case assembly complete?** For the current Phase 1 specific evaluator and tested publications, yes; it collects all selected subject mechanical facts. The verifier does not establish that completeness.
12. **What does Case verification prove?** Presented citations exist, values match, and support representation matches current reconstruction; not successful reconstruction, inclusion completeness, or semantic truth.
13. **What authenticates the World?** Resolved address, logical ID, revision and SHA-256 of SQLite, checked for consistency. They are not an authenticated seal over the complete directory.
14. **Does SQLite hash cover blobs/sidecars?** No. Raw blob edits disrupt old support hashes, but recomputed support or a fresh Judge passes; sidecar edits pass unchanged.
15. **Can W0/W1 substitution succeed?** A simple World override fails; relative/symlink aliases resolve; copied/rewritten address and identical-content Case substitution can pass. Different-content substitutions failed.
16. **Can Cases/artifacts from different Worlds combine?** Byte-identical W0/W1 artifacts and Cases can combine because Case address is unchecked; materially different ones failed in the probe.
17. **Can verdict tampering escape?** Simple flip fails; selective Case plus recomputed artifact changes the verdict and passes.
18. **Can cited sets be tampered?** Simple add/remove fails replay; recomputing the artifact on an incomplete Case yields a different cited set that passes.
19. **Method identity verified?** Compared to today's method record; it does not bind all imported behavioral dependencies or historical version semantics.
20. **Verdict reproduced?** Today's evaluator reproduces the artifact over the supplied Case; this is weaker than reproducing the original complete historical Judgment.
21. **After evaluator code changes?** Verification may fail, pass coincidentally, or use changed routing; historical equivalence is not established.
22. **Persisted bundle integrity sufficient?** No; selective Cases and unsupported artifacts verify. Partial JSON raises, and no-clobber is not exclusive.
23. **Unsupported versus `UNKNOWN` always distinct?** Judge separates them; verifier does not, as a fabricated unsupported bundle passed.
24. **Incomplete coverage blocks false negatives?** Yes in the current evaluator: unbound same-handler subject yielded applicability `UNKNOWN`, not a negative/conflict.
25. **`DOES_NOT_APPLY` positive basis?** Yes: a recorded route handler explicitly differs from installed `required_handler`; it is not inferred from absent binding.
26. **Unjudgeable durable knowledge?** Yes: generic/other-route propositions remain inspectable and grounded, with candidates/bindings/questions as constructed.
27. **Can Agent C verify without A/B state?** Yes for an honest bundle, but C's positive result currently overclaims integrity.
28. **What must C share?** Compatible installed readers, grammar, evaluator constants and transitive implementation semantics, plus W0 retained files and J0.
29. **Is `evaluate.py` reasonable?** Yes as a bounded installed evaluator; fixture duplication creates a two-place maintenance risk.
30. **Unearned architecture?** None found in Phase 2.
31. **Most serious defect?** Verifier accepts a deliberately incomplete Case with a recomputed, changed verdict as verified.
32. **Freeze and commit?** No; fix Judgment integrity first. No commit or push was performed.
33. **Next work bounded UNKNOWN continuation?** Not yet. Reassess that product step only after Phase 2 passes the integrity fixes and can be frozen; no Phase 3 design is proposed here.
