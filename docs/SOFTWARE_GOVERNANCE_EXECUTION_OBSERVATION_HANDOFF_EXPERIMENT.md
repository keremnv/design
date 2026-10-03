# Software Governance execution–observation handoff experiment

**Status:** experiment / architecture discovery note. Not a Decision contract, Action contract, authorization design, Construction contract, Core authority, or production capability framework.

The executable probe is [the test-local config exercise](../tests/test_software_governance_execution_observation_handoff_experiment.py). This report uses the accepted [Core baseline](CORE_PRODUCT_V1_BASELINE.md), [Construction contract](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md), and preceding [write-semantics experiment](SOFTWARE_GOVERNANCE_WRITE_SEMANTICS_EXPERIMENT.md) as boundaries. It creates no World.

## 1. Why this boundary

The write experiment separated source mutation from published knowledge. It left a concrete handoff unanswered: after an external capability runs, what source revision may later Construction actually consume? An action report can be wrong, a competing edit can occur before observation, and another edit can occur after observation. This probe stops at a producer-readable observation and an eligibility decision; it does not construct, admit, or publish governance knowledge.

## 2. Exact capability

One test-local `fixture.config_route_path_edit/v0` edits the actual `profiles/software_governance_config_v0/software.json` fixture copied to a temporary path. It changes the `customer-export` route path from `/customers/export` to `/internal/export`. The capability declares its route-document target, accepted inputs, and an exact SHA-256 starting-byte precondition. It reads and writes the external JSON file only. Its reported written digest is computed from bytes it *intends to write*, not an independent read after invocation. Fault injection can fail before or after writing, or falsely report success without writing. A second invocation against the `health` route tests a composite operation with mixed results; it is not one atomic multi-route capability.

## 3. Minimal request

The test-local request contains a request ID, actor label, target path, route ID, expected path, desired path, and expected starting SHA-256. It records wanted state and an invocation precondition. It does not attest approval, authority, invocation, or resulting state. A request can remain uninvoked while the original file remains eligible as observed source evidence.

## 4. Capability precondition

The capability reads current bytes just before its edit and refuses with `PRECONDITION_FAILED` if their digest differs from the request's expected revision. A pre-execution manual edit to `/manual/export` therefore survives untouched; the request was **not** applied. Expected-revision checking belongs in this particular mutation contract because blindly applying the edit to a changed source would violate the request's stated starting condition. This is not a lock or an atomic compare-and-swap with the filesystem: a writer could still race between the precheck and write. Independent observation and, for live Construction, a later revision check remain necessary.

## 5–13. Execution and observation results

| Scenario | Capability report | Independent observation and Construction handoff |
| --- | --- | --- |
| Normal | `SUCCESS`, claimed written digest R1 | Reads producer-supported R1 containing `/internal/export`; R1 is eligible while live bytes still match. |
| Failed before write | `FAILED` | Reads R0 and `/customers/export`; only R0 is eligible, not requested X. |
| Competing edit before invocation | `PRECONDITION_FAILED` against R1 | Reads actor-written R1 and `/manual/export`; R1 can enter Construction but was not produced by this request. |
| Competing edit after write, before observation | `SUCCESS` for X | Reads Y (`/other/export`), whose digest differs from claimed X. **Y** is eligible; X is not the observed current state. |
| Competing edit after observation | `SUCCESS` for X; observation recorded R1/X | Live handoff rejects R1 after the file becomes R2/Y. Retained R1 bytes remain eligible only for an explicitly historical construction input. |
| Composite partial result | First route edit `SUCCESS`; second route edit `FAILED` | One later read sees `customer-export` changed and `health` unchanged. Each target state is reported; no overall `SUCCESS` is invented. |
| Failure after write | `FAILED` after bytes were written | Reads changed R1. A failure report does not prove that external state stayed R0. |
| False success | `SUCCESS` with claimed X digest; no write happened | Reads R0 and original path. Observation defeats the report; R0, not X, is eligible. |
| Manual edit | No request or capability result | Reads valid R1 and can offer it to Construction. |
| Agent edit | Same bounded capability, actor=`agent` | Reads R1 under the same observation and eligibility rules; actor is provenance only. |

These are source-state outcomes, not governance conclusions. The central adversarial case is X successfully written, Y written by another actor before observation, and Y selected for the handoff.

The product can therefore say “the requested route change was applied and observed at R1,” “the tool reported success but observation found Y,” “source changed before execution, so this request was refused,” or “the observed R1 was superseded before live Construction.” The composite control reports the two route states separately. None of these messages says governance changed.

## 14. Request, invocation, outcome, observation

The request establishes intent and a precondition. Invocation establishes that the capability was called and may have attempted a write. Outcome reports what that capability says happened under its contract; `SUCCESS` here means its write path completed, while `FAILED` may occur after a partial write. Observation is a separate read of the actual target. Handoff names which observed revision is eligible under a chosen Construction mode. Neither a request nor an outcome is itself an observed source fact; no observation in this probe is a published World assertion.

## 15. Minimum observation contract

The observer records the exact target, observer method/version, SHA-256 of all read bytes, retained bytes, byte-range source locator, bounded route facts and record spans, plus `OK`, `UNSUPPORTED`, or `UNAVAILABLE`. It uses the current config producer's `_object_span` locator and validates the route shape before offering source to Construction. A raw digest alone is insufficient: a compact JSON file can have a perfectly valid digest and parse as JSON, yet fail this producer's present byte-span reconstruction rule. A missing target has no eligible revision. No timestamp is needed to identify exact bytes; digest equality does not prove who edited the file or that no intermediate edit occurred.

The observer is a trusted, test-local read, not a general evidence-attestation protocol. The handoff checks target, method, status, retained-byte digest, and recomputes the recorded route facts, spans, and locator from retained bytes. It checks the live digest where applicable. A forged route field or locator is rejected. It does not authenticate an actor or a physical write history. The producer remains responsible for its full validation when Construction eventually runs; this probe checks the bounded route form, not all future Construction inputs.

## 16–17. Eligibility and two Construction meanings

**Eligibility** means exact, reconstructible, producer-readable source bytes can honestly be offered as input. It says nothing about the requested change being semantically correct, authorized, governance-conformant, or published.

For **live-current Construction**, the observed digest must still equal the target's digest when Construction actually reads it. The test-local handoff checks this once and passes an exact revision precondition. That check is only useful if the later producer/intake enforces it at the read boundary; otherwise another edit can occur after the handoff check. Current config Construction reads a live path, so the probe has not proven that the production constructor already enforces this precondition.

For **retained-historical Construction**, the exact retained R1 bytes remain valid evidence of R1 even after the live file becomes R2. This requires the later construction path to explicitly consume those retained bytes as historical input. The current live-path config flow cannot silently be treated as that path. Historical eligibility is not a claim that R1 is current.

## 18. Feedback versus Observation

Observation exists without any Design action, as the manual-edit control proves. “Feedback” is a product interpretation of observation against an earlier request and outcome: did the observed path equal the requested path, and which revision was actually seen? It should not replace the general Observe responsibility. A feedback view may say the tool reported success yet the requested state was not observed.

## 19–20. Receipts and capability contract

The local outcome records capability ID/version, target, actor, expected and actual pre-invocation revisions, invocation status, reported written revision, and error. The observation is separate. Together with the request they can explain the product messages in §5–13. No durable receipt was required for this bounded immediate handoff; a later cross-session audit or several action types could change that assessment. This experiment contains only one real mutation capability and one composite two-call control. It supports a **candidate small external-capability contract** for exact input/precondition and structured outcome, not a production `DesignAction`, universal outcome schema, registry, or routing layer. Authorization would need to precede invocation in a real product but is not tested here.

## 21. Ownership classification

| Mechanism | Classification | Reason |
| --- | --- | --- |
| Route-path edit, expected path, write failure semantics | EXTERNAL CAPABILITY SEMANTICS | The concrete source mutation and reported outcome are defined by this bounded capability. |
| Request meaning, feedback against desired path, choice of live versus historical handoff | DESIGN PRODUCT SEMANTICS | These frame the user inquiry and later Construction intent. |
| Exact source read, digest, route parsing, spans, supported source form | PRODUCER / OBSERVATION SEMANTICS | These establish bounded reconstructible evidence, independent of who edited. |
| SHA calculation and record plumbing | SHARED IMPLEMENTATION MECHANISM | Useful code reuse alone does not create a Design layer. |
| Future grounding, retained evidence, sealed publication | OA CORE GUARANTEE | Applicable only when later Construction/publishing occurs; none is exercised as a World write here. |
| Receipt durability, cross-capability interface, truly race-free live read | UNRESOLVED | One capability and a test-local handoff do not establish these. |

## 22. Narrow Palantir lesson

The existing [OA application-platform research](OA_APPLICATION_PLATFORM_CAPABILITY_RESEARCH.md) records why Palantir standardizes [Ontology Actions](https://www.palantir.com/docs/foundry/action-types/overview): many applications and agents invoke mutations against one shared operational object model. Declared inputs, preconditions, structured outcomes, and inspectable invocation could also help several Design external capabilities. This one probe demonstrates the value of the precondition and distinct outcome/observation; it does not establish a shared mutable Ontology transaction, an Action framework, or any direct write to a sealed World.

## 23. Falsifiers and limits

- If a second real Design capability cannot use the same precondition/outcome distinction without losing its semantics, keep capability-specific interfaces.
- If a future producer can only reconstruct live paths and cannot enforce an expected digest at its actual read, the live handoff must be revised; this test-local precheck alone is insufficient.
- If independently retained evidence can be safely and directly supplied to the config producer, historical Construction could become executable without a live-source check, but must be labeled historical.
- If a product must inspect action histories across sessions, a durable action-result or request–observation linkage may earn a contract; this probe does not need one.
- The probe uses a local file and controlled sequential races. It does not prove filesystem-level atomicity, protection against simultaneous writes during reading, actor attribution, malicious observation forgery, or durable ordering of external events.

## 24. Tests

Fourteen deterministic tests cover request-only, normal execution, both failure timings, pre-execution revision refusal, edits on both sides of observation, composite mixed result, false success, manual and agent edits, unsupported source form, observation tampering at the byte/fact/locator/target/method boundary, and absence of World publication. They use a copied config fixture and test-local dictionaries/functions. No live model or new production package is involved. The focused probe passed **14** tests; the probe plus related write, correspondence, and config-profile tests passed **51**; Core acceptance passed **18**; the default repository gate passed **87**.

## 25. Recommendation

Keep **Execute** and **Observe** separate. For this config edit, declare target/input/revision preconditions at the capability boundary and return a structured capability-specific outcome. Perform a separate producer-compatible observation; then offer an exact observed revision to a live-current or explicitly retained-historical Construction path. Keep feedback as the product's comparison of observation with request/outcome. Do not introduce a generic Design Action or OA Action.

The smallest next probe is the **actual config Construction intake boundary**: after this handoff, make the producer either enforce the offered live revision at the bytes it reads or consume an explicitly retained historical observation, then inject a race between handoff and read. Only after that boundary succeeds should an end-to-end Decision-like request → execution → observation → Construction → publication experiment be attempted. This is a proposed experiment, not authorization to change Construction now.

## Explicit answers

1. **What does a request establish?** Intent, target, desired change, actor label, and expected starting revision; neither execution nor approval.
2. **What does invocation establish?** A capability was called and checked/attempted its bounded operation; no resulting source state by itself.
3. **What does reported success establish?** The capability reports completion under its own contract. It does not prove what is now on disk.
4. **What observation is required?** An independent, bounded read identifying exact bytes/revision and producer-supported reconstructible route material.
5. **Another edit between execution and observation?** Offer the later observed Y, if valid. Never offer the intended X as current merely from the outcome.
6. **Another edit after observation?** Refuse an R1 live-current handoff when current bytes are R2, or explicitly construct historical R1 from retained evidence. Enforce the chosen revision at Construction's actual read.
7. **Expected revision in capability contract?** Yes for this bounded config edit; mismatch refuses before the requested edit.
8. **Where is post-action observation?** In the independent Observe responsibility. The handoff checks that observation for the requested Construction mode.
9. **Can manual edits enter Construction?** Yes, after valid observation; no Design Action record is required.
10. **Do agent edits differ epistemically?** No. Actor provenance differs, not the observation standard.
11. **Partial mutations?** Report each attempted target/step and independently observe each actual relevant target state; do not flatten to one success boolean.
12. **False success detectable?** Yes. Claimed written digest/path differs from independently observed digest/path.
13. **What makes a revision eligible?** Exact target and method, valid retained bytes and digest, producer-readable bounded form, and for live-current use a digest match at the actual Construction read.
14. **Does eligibility mean requested semantic success?** No. It is source-input integrity only.
15. **Durable receipt required?** No evidence yet; local request/outcome/observation records suffice for this probe.
16. **Reusable external-capability interface?** A small precondition/outcome shape is plausible, but one real capability does not establish a production interface.
17. **Generic Design Action?** No evidence.
18. **OA Action?** No evidence and no Core change.
19. **Feedback distinct from Observation?** Feedback is a product comparison relative to a prior request; Observation is independently usable. No separate Feedback subsystem was forced.
20. **Smallest next experiment?** Enforce live-revision or retained-evidence input at the config Construction read boundary, with an intervening edit.
21. **Ready for full end-to-end loop?** The boundaries are clear enough to design that later test, but the production Construction intake has not yet been shown to enforce the handoff precondition. Test that first.

## Working-tree note

This pass adds only this report and one test-local file. It does not modify Core, accepted Design contracts, or production packages; it does not construct or publish a World; it does not commit or push. Other uncommitted repository changes predate this pass and were left in place. `uv sync --locked --extra dev`, `npm ci --prefix frontend`, focused tests, Core acceptance, default pytest, and `git diff --check` passed.
