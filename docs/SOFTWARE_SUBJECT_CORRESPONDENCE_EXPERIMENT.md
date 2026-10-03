# SoftwareSubject correspondence across snapshots

**Status:** experiment / architecture discovery note. Not a contract, accepted architecture, maintenance design, affected-governance design, or production implementation.

## 1. Question, boundary, and prior evidence

The [Selection / Scoping experiment](SOFTWARE_GOVERNANCE_SELECTION_SCOPING_EXPERIMENT.md) can navigate governance for a **known current SoftwareSubject**, but a software-change trigger supplies neither that subject nor a justified join to an earlier one. This probe asks what evidence can justify a cross-snapshot correspondence. It stops before affected-governance retrieval or binding renewal.

Authority for the existing boundaries is [Construction v0](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md), [Judgment v0](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md), [Investigation v0](SOFTWARE_GOVERNANCE_INVESTIGATION_CONTRACT.md), and the [scenario catalogue](DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md). The [Core baseline](CORE_PRODUCT_V1_BASELINE.md) makes sealed publication addresses and independent reads available, but does not supply global cross-revision identity.

Archaeology used as evidence, not a Design contract:

| Prior probe | Demonstrated result relevant here |
| --- | --- |
| `tests/test_manifestation_granularity.py` | Local token-range content, file digest, source location, and snapshot-local identity diverge. The current spine comparison's source-manifestation flag can follow a whole-file digest. Inserting a call before another can mispair owner/order occurrences. |
| `tests/test_semantic_identity_persistence.py` | Direct evidence-to-software joins cover simple cases. Persistent semantic identity was justified only when a durable semantic subject survived replacement of wording and software endpoints; ambiguity did not select a winner. |
| `tests/test_program_spine_comparison.py` | Program Spine has a comparison sidecar with `CONTINUED`, `AMBIGUOUS`, `UNRESOLVED`, `NO_MATCH` vocabulary and heuristic/observational/deterministic basis classes. Automatic rules are **heuristic** even when repeatable. Partial comparison universes can yield unresolved results. |
| Construction v0 and `ID-08` in the scenario catalogue | `software_subject` names a snapshot-local subject. Manifestation and location are separate. Cross-snapshot correspondence remains unaccepted in Software Governance; a comparison could be external to both Worlds or published later with evidence of both. |

The executable probe is [`tests/test_software_subject_correspondence_experiment.py`](../tests/test_software_subject_correspondence_experiment.py). It uses sealed TypeScript Program Spine snapshots and the accepted sealed JSON route Governance fixtures. It imports no historical checkout, authority, semantic binding, or maintenance machinery. No production package or World was modified.

## 2. What was compared

A SoftwareSubject is a producer-identified occurrence **within** one software snapshot. A manifestation is reconstructible subject-local content under a producer scheme. A location is a coordinate. Structural context describes containment and nearby structure. A correspondence is a qualified claim **between** two snapshot-local subjects. None of these is persistent semantic identity; none says that old and new implementations mean the same thing.

The TypeScript producer comparison is `ontology_author.program_spine.comparison/v0`. It reads two sealed spine snapshots, their manifests, capabilities, structural facts and source observations, and emits a comparison-local sidecar. These tests compare **producer entities**; Construction v0 can expose selected entities as `SoftwareSubject` receipts, but the comparison does not itself publish those receipts or a Design correspondence. Its automatic `CONTINUED` claims have `HEURISTIC` basis. The deterministic execution of a matcher is not an entailed match. Its source-order and signature rules may be useful candidate generators but cannot certify continuation.

The JSON route producer `config.routes/v1` exposes a snapshot-local subject, `record_id`, path, handler, JSON pointer, and can produce a canonical-record manifestation. The accepted W0 fixture publishes that manifestation; its conflict W1 fixture publishes changed `config_route` facts but **no local manifestation receipt**. It has **no declared cross-snapshot comparison capability or stable-key promise**. The probe does not invent one. Repeated `customer-export` record IDs and a repeated logical World ID therefore leave correspondence unresolved, even though they are useful observations.

| Shape | Executable observation | Honest Design interpretation |
| --- | --- | --- |
| Unchanged local declaration, surrounding edit | Spine reports heuristic `CONTINUED`; local declaration bytes remain identical while its file-level source-manifestation flag changes. | Candidate continuation; whole-file digest is too coarse for this subject. |
| Local body edit | Same structural declaration is paired, with manifestation changed. | Correspondence can survive changed implementation content, with no semantic-equivalence claim. |
| Pure file move | Paired declaration has changed source location. | Location equality is unnecessary. Pair remains heuristic under the current producer. |
| Rename | Preserved structural/signature context yields a heuristic `RENAME`. | Name equality is unnecessary; rename is not mechanically proved by that context alone. |
| Delete plus unrelated similar replacement | Existing matcher emits one heuristic `CONTINUED`/`RENAME`, with an explicit “not mechanically entailed” limitation. The new declaration begins at the old coordinate. | **False-continuity counterexample:** one winner, same starting location, and compatible signature are insufficient. Do not promote the claim. |
| Two identical call manifestations | Two current `fire()` occurrences have the same local bytes but distinct subject IDs. | Content equality alone cannot choose which occurrence continued. |
| Insert a call before an old call | Owner/order matcher pairs the old `charge()` with the new `audit()`, while `charge()` still exists later. | Concrete current matcher defect for identity use. The claim remains a heuristic observation, not accepted correspondence. |
| Ambiguous duplication | One old callable gets two current candidates and `AMBIGUOUS`; no winner is chosen. | Preserve both alternatives; historical governance cannot attach to either current subject. |
| Incompatible replacement | Old callable is in `removed`, new in `added`, with a complete **entity inventory**. | This is matcher membership, not proof that no semantic correspondence exists. |
| Split / merge | Automatic comparison does not establish split. The existing sidecar can represent both directions when an explicit observational grouping is supplied. | Cardinality can be recorded but v0 has no automatic proof of 1→N or N→1 continuity. |

These observations falsify standalone continuity tests based on label, file path, owner, source order, record ID, manifestation digest, location, or logical World ID. Several may contribute to a **versioned producer-specific rule**. None individually proves correspondence in the tested contracts.

## 3. States, strength, and inspectability

The narrow semantic distinctions needed by a later Design consumer are:

| State | Meaning in this probe |
| --- | --- |
| Qualified correspondence | A named producer capability or explicit supplier relates a prior and current subject and records its basis and limits. `HEURISTIC` remains contestable even with one winner; `SUPPLIED` records who asserted the pairing. |
| `AMBIGUOUS` | Two or more candidates survive; no unique pair is established. |
| `UNRESOLVED` | The producer lacks a comparison contract, capabilities are partial/incompatible, or the available observations cannot decide continuity. The config producer is an example. |
| `NO_MATCH` | Only a producer with a sufficient *correspondence* coverage rule can assert no corresponding subject exists. An empty candidate list or `removed` delta under a complete entity inventory does **not** meet that bar. No test in this probe established such a rule. |

This is not a recommendation to add a global status enum now. Program Spine already has these spellings, but its `NO_MATCH`/delta language must be read in the scope of its matcher. The tests show why `CONTINUED` plus `HEURISTIC` cannot be collapsed into a mechanically established identity. No numeric confidence is used. `DETERMINISTIC` in the existing spine schema denotes entailed basis, not merely reproducible computation; none of the automatic probe matches has that basis.

An inspectable comparison needs: exact prior and current **publication addresses**; both snapshot and subject IDs; producer/capability/version; evidence such as reconstructed local content, locations, descriptors, structural relations and candidate alternatives; a basis class; known losses and comparison scope. It needs no private algorithm trace. Program Spine's receipt carries snapshot IDs, capability compatibility, mechanism ID/version, evidence/rules, and losses. A test-local envelope adds both exact sealed publication addresses. Swapping those addresses fails verification. Snapshot IDs, shared record labels, and `world_id` do not substitute for publication addresses.

## 4. Where the result lives and what it permits

For the required read, an external comparison artifact or ephemeral inquiry input is sufficient. The Program Spine sidecar is already such an artifact. It describes **two** sealed publications and cannot truthfully be inserted into either existing World without rewriting history. A later sealed comparison World could publish an ordinary relation grounded in both snapshots if durable reuse or generic independent inspection warrants it; this experiment did not need that step. A producer can emit a sidecar with its comparison snapshot, but calling that a snapshot does not make the relation part of W0 or W1. No persistent Design correspondence package is justified yet.

The downstream fixture supplies a **qualified observational pairing** between a prior and current config route, with exact W0/W1 addresses. This supplied pairing is conditional test input: `config.routes/v1` did not infer or validate it. The read returns historical governance published for A0 and, separately, current governance actually published for A1. In these accepted fixtures both Worlds independently publish the same proposition ID against different subject IDs and evidence. The test verifies that W0 contains no binding to A1 and W1 contains no binding to A0. Matching proposition IDs do not make the W0 assertion current. If W1 had no binding, this read would show only historical governance and no current binding. An ambiguous pairing would display historical governance plus candidate current subjects, never attach the old binding to one candidate; the ambiguous comparison test supplies the no-winner premise.

The useful product answer is thus conditional and labeled:

```text
Current route: A1 in exact publication W1
Prior route: A0 in exact publication W0
Correspondence: explicitly supplied in this fixture; producer inference unresolved
Basis: supplied observation, with producer/version and inspected route data
Historical governance: P was bound to A0 in W0
Current governance: only W1's independent assertions about A1
```

Cross-snapshot SoftwareSubject correspondence is evidence for later **reconsideration**, not governance applicability or renewal. A relation about software occurrences cannot license `governance_binding(P,A1)` from `governance_binding(P,A0)`. Construction would need new governance evidence and a fresh publication for that claim. Judgment remains bounded to its own Case and publication. No semantic identity was needed for the tested software-occurrence comparison; durable identity across replacement of the semantic thing, not merely its software representation, remains a separate Construction question.

## 5. Ownership and candidate architecture

| Mechanism | Classification | Why |
| --- | --- | --- |
| Snapshot-local subject and manifestation evidence | **PRODUCER SEMANTICS** | TypeScript and JSON producers define their own occurrence/manifestation schemes. |
| TypeScript candidate matching and comparison receipts | **PRODUCER SEMANTICS** | Rules depend on language structure and known extractor losses. |
| JSON route cross-snapshot matching | **UNRESOLVED** | No stable-key or comparison capability exists in `config.routes/v1`. |
| Exact-address verification, pairing serialization, candidate-set handling | **SHARED IMPLEMENTATION MECHANISM** | May be reusable but supplies no universal continuity rule. |
| Historical versus current governance display; refusal to renew bindings | **DESIGN SEMANTICS** | Design owns governance interpretation and product read boundaries. |
| Sealed immutable publications, grounded snapshot assertions, independent reads | **OA CORE GUARANTEE** | Existing Core provides the epistemic base; no change required. |

**Outcome A, producer-owned comparison, is best supported**, with a possible small shared result vocabulary consumed by Design. Outcome C remains plausible for matching algorithms: each producer may require distinct rules. Outcome B, one Design-level generic matcher over common subject fields, is falsified by the TypeScript insertion/replacement controls and the config producer's lack of a stable-key contract. Outcome D is not forced: current subject/manifestation/location semantics express every test; the missing capability is comparison evidence. Do not productionize a correspondence abstraction from one heuristic producer and one producer without a comparator.

The current Program Spine comparison is useful but not canonical Design correspondence. Specifically, `CONTINUED` is an output of its v0 matching rule, not a Design identity guarantee. `AMBIGUOUS` remains justified as an explicit multi-candidate state. `UNRESOLVED` is justified when comparison evidence or coverage is insufficient. `NO_MATCH` needs a stronger no-correspondence basis than this experiment obtained.

## 6. Falsifiers, verification, and recommendation

This recommendation would change if a producer declared a stable cross-snapshot identifier with independently checked uniqueness and persistence semantics; if two unlike producers independently needed the same Design-owned correspondence invariant beyond their own comparison rules; if a required later consumer could not interpret producer sidecars without a shared contract; or if durable reuse demanded a sealed comparison World citing both inputs. A case where current `SoftwareSubject` receipt semantics cannot express a needed endpoint would falsify the no-Construction-change finding. A certified exhaustive correspondence rule could justify real `NO_MATCH`. Conversely, more owner/order false matches would strengthen the case for keeping heuristics visibly qualified.

**Verification:** 14 new targeted tests passed. They exercise four change shapes, false continuity from replacement and insertion, identical local content with distinct occurrences, ambiguity, unmatched membership, supplied split/merge representation, exact publication addressing, config-producer non-proof, and historical/current governance separation. The existing comparator, manifestation, and Selection suites passed **23 tests with 1 deselected**; they provide the partial-capability and richer manifestation controls referenced above and are not counted as new tests. Core acceptance passed 18 tests; the default gate passed 87. No Core, Construction, Judgment, or Investigation change was required. The experiment did not prove a general matcher or a trustworthy `NO_MATCH` for arbitrary software.

**Recommendation:** keep comparison rules producer-owned; have Design consume only qualified, exact-publication comparison evidence for historical navigation. Do not infer current governance from it. The smallest next experiment is a producer-declared comparison contract for one bounded subject kind, with an explicit stable-key/uniqueness basis or an explicit ambiguity result, then test it against delete/replacement and duplicate cases. Only after that should a change-trigger inquiry consume the correspondence.

### Explicit answers

1. **What is correspondence?** A qualified cross-snapshot relation between two snapshot-local software occurrences.
2. **Identity or evidence?** A separate relation supported by comparison evidence; it neither merges their IDs nor creates durable semantic identity.
3. **Sufficient facts?** A versioned producer or explicit supplier must define a rule whose evidence, scope, uniqueness/alternatives, and limits support the particular pairing. The current automatic TypeScript rules supply useful **heuristic** pairings, not mechanically entailed continuity. No generic field combination was proved sufficient.
4. **Insufficient facts?** Equal label, path, owner, source order, record ID, logical World ID, location, or manifestation alone; a single heuristic winner; an empty matcher result.
5. **Can manifestation change?** Yes. A local implementation edit is paired heuristically with changed manifestation.
6. **Can location change?** Yes. A move is paired heuristically with changed location.
7. **State distinctions?** `AMBIGUOUS` retains multiple candidates; `UNRESOLVED` lacks deciding evidence/coverage; `NO_MATCH` requires a sufficient negative comparison basis, not merely failure to find a candidate.
8. **Cardinality?** v0 sidecars can represent 1→N and N→1 when supplied; automatic establishment of either was not demonstrated.
9. **Owner?** Producers own software comparison rules; Design owns interpretation of comparison strength and governance navigation. A shared result shape is at most a future candidate.
10. **Where?** A sidecar or ephemeral input suffices now. A new sealed comparison World citing both snapshots is optional future work, never an edit of W0/W1.
11. **Which identities?** Both exact sealed publication addresses, both snapshot IDs, and both subject IDs, with comparison method/version.
12. **Semantic identity?** No. Software-occurrence continuity and durable semantic identity answer different questions.
13. **Historical governance navigation?** Yes, conditionally through a qualified pair, labeled as W0 history, with W1 assertions read separately.
14. **What blocks renewal?** Correspondence contains no proposition-to-current-subject governance assertion or evidence of current applicability. W0 and W1 bindings remain separate published facts.
15. **Core change?** None.
16. **SoftwareSubject or Construction change?** None was forced; the missing piece is a producer comparison capability, not a different snapshot-local subject definition.
17. **Production abstraction now?** No. One heuristic implementation plus one producer without a comparison contract does not establish stable common semantics.
18. **Smallest next experiment?** Test one producer-declared, versioned stable-key/uniqueness rule against replacement and duplication, then expose only the qualified result to a change inquiry.

## Working-tree status

This experiment adds this report and one test file. No files were staged, committed, or pushed. The workspace also contains pre-existing uncommitted and untracked UI, research, and accepted Design work. During verification, the already dirty bundled UI asset changed from untracked `index-pLO_elPu.js` to untracked `index-DzVzgYa1.js`, with `static/index.html` now referencing the latter. It was not staged or reverted because the former untracked asset is no longer present; no OA Core source or API was edited for this probe.
