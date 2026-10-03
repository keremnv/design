# Software Governance write semantics experiment

**Status:** experiment / architecture discovery note. Not a contract, Core authority, production action framework, authorization design, or persistence redesign.

## 1. Why this is a separate question

The [config correspondence probe](CONFIG_ROUTE_CORRESPONDENCE_CONTRACT_EXPERIMENT.md) showed both directions of source/knowledge divergence: identical software bytes can support different sealed governance Worlds, and changed software does not create a new governance binding. “Write” therefore names several possible destinations and events, not one operation. This experiment asks what Design may claim after each event. It uses the accepted [Construction](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md), [Judgment](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md), [Investigation](SOFTWARE_GOVERNANCE_INVESTIGATION_CONTRACT.md), [Core baseline](CORE_PRODUCT_V1_BASELINE.md), and [durable-knowledge scenario catalogue](DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md) as boundaries. The executable probe is [`tests/test_software_governance_write_semantics_experiment.py`](../tests/test_software_governance_write_semantics_experiment.py).

The accepted facts remain: Worlds are sealed; a Judgment or Investigation artifact is outside its World; discovery, proposal, admission, and publication differ; a proposal is not an assertion; a successful external edit does not admit semantic knowledge; failed construction is a failure, not epistemic unresolvedness. Historical publications remain inspectable after later source changes. This probe does not implement admission, Decision, affected-governance retrieval, or authorization.

## 2. Destinations and events actually separated

| Destination | Event tested or inspected | What changed | What did not thereby change |
| --- | --- | --- | --- |
| External/source state | File edit, failure, partial edit, manual edit, reversion | Current bytes at the target, if actually written | Any sealed World or governance binding |
| Knowledge candidate | Producer/Construction staging, later validated candidate | Unpublished construction state | Durable reusable World knowledge |
| Sealed knowledge publication | Fresh Design World after construction and admission checks | Published assertions at a new exact address | External file bytes, approval, execution outcome |
| Application-local artifact | Fixture action outcome and accepted Investigation proposal | Inspectable local account of an attempt or proposed claim | World assertion or external reality by itself |
| Organizational decision/adoption | Only an input possibility here; rejection is a test-local disposition | Standing of a proposal if a real authority decides | Source mutation or publication without further events |

The test-local file edit result records a target, method, actor label, intended replacement, starting SHA-256, attempt, outcome, post-attempt observed SHA-256, and error where relevant. It is deliberately a **config-file fixture result**, not a generic `Action`, `Write`, or transaction type. The accepted Investigation `make_proposal` supplies a real proposal shape; the test-local rejection records that no admission/publication occurred. No record is written into W0.

## 3. Executed scenario matrix

The tests use the accepted `config.routes/v1` producer and Software Governance fresh-publication path. `W0`, `W1`, and `W1b` are distinct sealed addresses. A producer staging `world.sqlite` is **not** counted as a sealed Design publication; the first test run caught this distinction and the probe now checks publication addresses explicitly.

| Scenario | Execution and observed result | Honest product message / boundary |
| --- | --- | --- |
| **A. Ontology-only addition** | W0 has no export binding. W1 is published from byte-identical route source with an independently constructed binding. W0 bytes remain unchanged. | “Source did not change; a new governance interpretation was published at W1.” The binding is new knowledge, not a source edit. |
| **B. Source-only mutation** | Route path changes in the external file. W0 remains the only sealed Design World; its retained old manifestation still reconstructs. | “Source change succeeded. W0 still describes its prior source revision.” |
| **C. Source → reconstruction → publication** | File edit succeeds, its resulting SHA-256 is observed, and a separate fresh W1 is built from matching bytes. W1 has no automatic binding even though W0 did. | “Source change and World publication both succeeded as two linked events.” |
| **D. Failed external mutation** | Requested bytes are absent; fixture edit returns `FAILED`, observed source digest is unchanged, and no W1 appears. | “The attempt failed; the desired source state was not observed or published.” A fabricated success flag without a post-read is likewise insufficient. |
| **E. Successful mutation, failed construction** | The file is changed to malformed route JSON; producer reconstruction raises. External SHA changes; only W0 remains sealed. | “Source is now S1, but latest valid Design World remains W0.” Source success is not rolled back conceptually. |
| **F. Construction succeeds, publication fails** | A valid `.sg-work/world.sqlite` candidate exists at the final rename; an injected failure prevents the fresh publication address. Candidate work is discarded by the existing path. Source is still S1 and W0 remains intact. | “Candidate construction reached publication, but no W1 exists.” Candidate existence is not publication. |
| **G. Knowledge proposal rejected** | Accepted Investigation proposal shape is created locally, then given a test-local rejection disposition. Source and W0 hashes remain unchanged; no binding or negative assertion is added. | “Proposal was rejected. No source or published World changed.” Rejection does not prove the proposition false. |
| **H. Same source, different Worlds** | Two W1 publications use identical software bytes and snapshot ID. One has no binding; the other independently publishes the binding. | World publication identity and governance state cannot be reduced to source revision. |
| **I. Source reversion** | S0→S1; W1 publishes S1-derived route facts; external source returns to S0. W1 bytes and retained S1 manifestation remain inspectable. | “W1 historically described S1.” Source reversion neither edits W1 nor designates W0 current automatically. |
| **J. Source edit outside modeled governance relevance** | A leading newline changes source SHA but parsed route records remain identical; no new World is created. W0 remains readable and its source revision is visibly different from the current file. | A formatting edit need not force governance publication. A claim that W0's source bytes are current would still require a fresh observation. |
| **Partial external result** | First config file changes; second target is missing and raises `FileNotFoundError`. Test-local result says `PARTIAL`; no World follows. | Re-read every target and its actual after-state before constructing claims about the combined result. |
| **Manual and agent edits** | A direct file write bypasses Design's action helper and is later observed/reconstructed. Agent-labeled edits follow the same source observation checks. | Actor is provenance, not extra epistemic authority. Observation can follow an external change Design did not initiate. |
| **Immediate obsolescence** | W1 publishes from observed S1; another source write produces S2 immediately after. W1 remains sealed, now source-revision-misaligned. | Publication success does not freeze external reality or make W1 perpetually current. |

These scenarios falsify a mandatory “every source edit → new World” rule, a “new World → source edit” rule, and an atomic source-plus-publication transaction. They also show a legitimate knowledge-only publication grounded in existing retained software and governance evidence. The test does not independently adjudicate the semantic correctness of that new binding; existing Construction validates its recorded support and origin, not objective truth.

## 4. Ordering, evidence, and atomicity

For an external edit, the distinct stages are **intent → attempt → outcome → observation → possible knowledge claim**. The fixture's outcome includes a post-write read; a bare success report without that read cannot ground a claim that the desired bytes exist. A future source-derived World needs bounded observations of actual state, source revision identity, and retained reconstructible evidence. The old config World continues to reconstruct its original canonical record from stored evidence after the external file changes. Mutable source paths alone would not provide that historical guarantee.

For a knowledge change, the distinct stages are **discovery → proposal (if the application chooses) → admission → publication**. A semantic assertion can be grounded in retained source evidence without a source edit; a future decision/approval might itself be evidence for a claim about a decision, but no such authority or admission flow was implemented here. A request to edit code is not evidence that code changed. A successful edit is not evidence that a governance proposition applies. An admitted candidate is not a sealed publication.

The source and knowledge sides cannot be one honest atomic transaction in this environment. The source-success/publication-failure test gives a concrete split outcome; the immediate-obsolescence test shows that publication cannot keep external state fixed. Core's atomic publication visibility is local to the World bundle. The product may coordinate the two transitions, but must expose both outcomes and their exact evidence/revision linkage. No distributed transaction or rollback fiction is warranted.

The catalogue's `ADDS`, `REFINES`, `RESOLVES`, `SUPERSEDES`, `CORRECTS`, `WITHDRAWS`, `LOSES_SUPPORT`, `PROPOSES`, and `ADMITS` remain distinct **relations to prior knowledge** and possible destinations. This probe executes an addition of a binding and a rejected proposal; it does not implement correction, withdrawal, or admission lifecycle. A later World can express a changed epistemic relation without editing W0. A decision/adoption record and a Judgment artifact likewise remain separate from both execution and publication.

## 5. Currentness, receipts, and responsibility boundary

The probe mechanically compares a sealed World's recorded software snapshot digest with a freshly read source digest. This answers **“do these exact source revisions match?”** for this fixture. It does not define a universal “stale” predicate. A source mismatch may be a route change, malformed input, or irrelevant whitespace; a governance interpretation can change while source digests match. Core derivation staleness is narrower and should not be reused as a universal semantic/currentness label.

“Latest published,” “latest candidate constructed,” “latest known source-aligned,” and “designated current” are different questions. After S1 plus failed construction, W0 is latest published but not source-aligned. After S1→S0 reversion, W0 can again have matching bytes, but that alone does not settle which governance interpretation is designated current. The product can show publication address, source revision, and latest observation before inventing a durable `CurrentWorld` primitive. No current pointer or staleness engine was added.

An action-result record is useful for a Design-initiated edit, especially failure or partial success. It belongs outside the sealed World, in product execution history or a bounded sidecar, until a separately constructed assertion about that event is admitted and published. Durability is a product/audit requirement **not established** by these fixtures; a manual edit has no Design action receipt at all, yet can still be observed. The producer's unsealed staging file and a Judgment/Investigation artifact also remain outside reusable published knowledge. Shared fields such as target, method, before/after revision, outcome, and provenance help link events, but source mutation and World publication have different validity and failure semantics. One semantic `WriteReceipt` did not earn a contract.

The responsibility picture that survived is:

```text
DECIDE (if an actor chooses)
    ↓
EXECUTE an external capability, or observe an independent external change
    ↓
OBSERVE actual external state
    ↓
CONSTRUCT / ADMIT / PUBLISH knowledge when a grounded claim is warranted
    ↓
JUDGE / DECIDE again on a bounded published basis, if useful
```

This is not a required linear workflow: knowledge-only publication bypasses execution, manual changes bypass Design execution, and a decision may never lead to action. **Outcome A** is best supported: several transition families, product-coordinated, with no shared semantic write abstraction. A small provenance link may later help inspection, but the current tests did not need a production transition envelope (Outcome B). Common orchestration state (C) and unified action/write semantics (D) were not forced. “Write” is a useful research label, not a first-class Design responsibility box.

OA continues to own sealed publication, grounding, construction origin, revision, completeness and independent inspection. Design owns governance interpretations, proposal/admission choices, product messaging, and any later decision-to-action meaning. External tools and source producers own their mutation/observation contracts. Nothing here requires an OA Action primitive or Core edit. Authorization would matter before real external actions or admissions; its design is deferred, not implicitly granted.

## 6. Narrow Palantir comparison

The existing [OA application-platform research](OA_APPLICATION_PLATFORM_CAPABILITY_RESEARCH.md) records why Palantir standardizes Actions for application leverage. Palantir's [Action type documentation](https://www.palantir.com/docs/foundry/action-types/overview) describes one action as a transaction editing Ontology objects, properties or links, with shared logic/validations across applications. OA's sealed World is a historical knowledge publication, while the config file is a separately mutable external source. That environmental difference rules out treating an OA World publication as a Palantir-style object edit.

The transferable motivation is **consistent invocation and inspectable outcome** for a declared external capability when several Design front doors or agents use it. Method identity, input validation, target/before revision, observed after-state, errors and partial results could make product actions easier to inspect. Whether those deserve a shared Design interface requires more than this one config edit. Mutable Ontology writeback, one transaction spanning source and knowledge, or a generic OA Action are unsupported.

## 7. Falsifiers, next probe, and verification

This conclusion would change if multiple Design actions and publication flows independently required one common transition invariant that could not be represented by destination-specific receipts; if a product needed durable cross-session linkage that simple publication/source revision references could not supply; or if a concrete external system and World publication genuinely shared one transactional authority. It would also change if a required read could not distinguish current source from published evidence without a new durable pointer. The tests instead showed divergence with ordinary exact revisions and product-local results.

**Smallest next experiment:** one bounded config edit from a Decision-like product request through an external capability to a verified after-state **without publishing governance yet**. Pressure the minimum externally inspectable action outcome and post-action evidence, including a manual competing edit between attempt and observation. Then ask whether the observed source revision is eligible for Construction; keep admission/publication as a second experiment. This would test the actual handoff needed for a future Decision → Action → Feedback loop without assuming an action framework.

**Tests:** 15 new deterministic tests passed. They cover A–J, partial external success, manual and agent writes, an unobserved success report, and immediate post-publication source change. The new probe plus related correspondence and Investigation tests passed **38**; Core acceptance passed **18**; the default repository gate passed **87**. The tests use sealed config Worlds, retained evidence reconstruction and injected publication failure; no live model or production write package is involved. No commit or push was made.

### Explicit answers

1. **What can change?** External source bytes, unpublished candidates, sealed knowledge at a fresh address, application-local artifacts, and decision/admission standing; each has different semantics.
2. **Same responsibility?** No. Source execution/observation and knowledge admission/publication are separate.
3. **Knowledge without source change?** Yes: byte-identical software supports W0 without and W1 with an independently constructed binding.
4. **Source without World change?** Yes: S1 can be current externally while W0 remains the latest sealed publication.
5. **Mutation succeeds, reconstruction fails?** Keep S1 as observed external state, W0 as latest valid published history, and expose their revision mismatch. No W1 is claimed.
6. **Construction succeeds, publication fails?** A candidate existed, but no fresh sealed World exists; W0 and the external source retain their separate states.
7. **Is success itself evidence?** No. A reported success must be followed by observation of the actual target state; the fixture receipt includes that read.
8. **Required observation?** Bounded post-action read of the relevant target(s), with revision/content evidence that a future World can retain and reconstruct.
9. **Atomic combined operation?** No demonstrated honest atomic operation spans external mutation and World publication.
10. **Durable receipt required?** A bounded outcome is useful for initiated actions and partial failures; this probe did not justify a universal durable receipt contract.
11. **Where?** Product execution history or an external sidecar, not an assertion in W0. A later grounded publication about the event would be a separate knowledge transition.
12. **Manual changes?** Observe and reconstruct them without requiring a Design action invocation or receipt.
13. **Agent changes?** Actor provenance may differ; evidentiary standing and post-action observation requirements do not.
14. **What is current amid divergence?** Specify the dimension: latest published address, latest observed source revision, source-aligned publication, or a separately designated choice. They need not coincide.
15. **Generic staleness?** No. Exact source-revision mismatch is useful; semantic currentness needs application interpretation.
16. **First-class Write box?** No evidence for one.
17. **Existing responsibilities enough?** Execute, Observe, Construct, Admit, Publish and Evolve describe the tested transitions; Decision remains separate.
18. **Generic Design Action?** Not yet; one fixture edit and product-local receipt do not establish shared action semantics.
19. **OA Action?** No. Core's sealed-publication epistemic duties do not require external-action meaning.
20. **Palantir ideas that transfer?** Consistent declared invocation, validation, and inspectable result/provenance may help future Design tools; mutable Ontology transaction semantics do not transfer.
21. **Next transition?** Decision-like request → one config external edit → independently observed after-state → eligibility for later Construction, including a competing edit control.
22. **Decision → Action → Feedback implication?** Keep decision, invocation, actual outcome, observation, bounded Judgment, and any new publication as separately attributable events; feedback may occur with no new World.

## Working-tree and gate status

This pass adds this report and one test file; both remain untracked and unpushed. Existing uncommitted UI, research and Design work was left in place. No OA Core source, accepted Design contract, or production action/write package was edited. `uv sync --locked --extra dev`, `npm ci --prefix frontend`, targeted tests, Core acceptance, the default gate, and `git diff --check` passed.
