# Config route correspondence contract experiment

**Status:** experiment / architecture discovery note. Not an accepted producer contract, Design contract, Core authority, affected-governance design, or write model.

## 1. Why this producer, and what it currently says

The [prior correspondence probe](SOFTWARE_SUBJECT_CORRESPONDENCE_EXPERIMENT.md) found that Program Spine's automatic comparison is heuristic and that the config route producer has a narrower possible key: `record_id`. This experiment pressures one route kind, `config:route`, through the accepted [`config.routes/v1` producer](../profiles/software_governance_config_v0/produce.py) and [Software Governance Construction v0](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md). The executable evidence is [`tests/test_config_route_correspondence_contract_experiment.py`](../tests/test_config_route_correspondence_contract_experiment.py). No comparison package or production contract was added.

**Current finding:** `record_id` is an observed field. The [profile README](../profiles/software_governance_config_v0/README.md), source fixture, producer code, and [config acceptance tests](../tests/test_software_governance_config_profile.py) do not promise persistence across snapshots or forbid reuse after deletion. The producer creates subject IDs from the **whole document digest plus record ID**, so a changed document normally creates different snapshot-local IDs. It does not validate `record_id` uniqueness, publish a route-universe completeness receipt, or declare a comparison capability. The current source format accepts a later unrelated record with a reused ID. Repeated fixture values are not an identity contract.

## 2. Candidate rule and the three independent guarantees

The test-local hypothesis is `config.routes.correspondence/v0`, scoped to `config:route` in two exact sealed publications made by compatible `config.routes/v1` construction. It would use `record_id` as a stable key **only if the source/producer contract promises unique, persistent, never-reused IDs**. Its comparison universe would be every route successfully parsed and published from each bounded `software.json`. The test-local result carries method, version, producer, subject kind, key scheme, exact publication addresses, source revisions, snapshot IDs, pairs, uncovered keys, basis, and coverage state. This is a conditional model, not an accepted declaration.

| Guarantee | Evidence in the current producer | Test result |
| --- | --- | --- |
| **Extraction**: observe a key on a route | `config_route` publishes `record_id`, path and handler with document grounding. | Present for supported valid records. |
| **Uniqueness**: one key names one route in a snapshot | No producer check. Duplicate IDs generate the same snapshot-local subject ID and the same first matching source observation for both route records; the current Construction path can seal that input. | Fails without an added producer validation rule. The test-local comparison audit rejects the sealed duplicate publication. |
| **Persistence**: a key denotes the continuing producer-level record across snapshots and cannot be reused for an unrelated record | No source-schema or producer promise. | **Not established.** A declared no-reuse source contract would make key equality sufficient relative to that contract; two snapshots' fields cannot verify the history by themselves. |

The test-local audit compares retained source bytes with the sealed World's route rows, `software_subject` receipts and `config_member` rows, checks the source digest-derived snapshot ID, and rejects skipped receipts. It creates a **conditional route-universe certificate** for the experiment. The World's `governance_completeness=INCOMPLETE` concerns supplied governance bindings; it is not a route-enumeration certificate. These scopes must not be conflated.

## 3. Executed change matrix

All normal comparisons use two fresh sealed config/Design Worlds made through the accepted producer and Construction path. The current producer mode returns `UNRESOLVED` for continuity even when keys repeat. A separate test flag activates the **hypothetical source persistence promise** to expose its consequences; results in that mode are marked `CONDITIONAL_PRODUCER_ESTABLISHED` and must not be read as current production evidence.

| Case | Observed result | Conditional rule, if a no-reuse source contract existed |
| --- | --- | --- |
| Exact continuation | Same key and canonical route content. Exact publication addresses differ; subject IDs may coincide when the whole source is identical. | One pair by key. Publication identity still distinguishes the two reads. |
| Path change | Same key, different path and local manifestation digest. | One pair; route-record continuity says nothing about governance or endpoint meaning. |
| Handler change | Same key, different handler and manifestation digest. | One pair; implementation target can change without changing the producer-level record key. |
| Reorder | Same keys and canonical manifestations, changed JSON-pointer location and document-derived subject IDs. | Both pairs remain; source order is irrelevant. |
| Textual source movement | Leading whitespace moves the source byte offset while JSON pointer and canonical manifestation stay the same. | Both pairs remain; byte location is irrelevant. |
| Addition | A new key appears in a complete current route universe. | `NO_PRIOR` for that key, scoped to these two publications and this producer contract. |
| Deletion | A prior key is absent from a complete current route universe. | `NO_CURRENT` for that key, with the same scope. It is not a claim that the route's business purpose vanished. |
| Duplicate key | Current producer processes both records with the same subject ID and same first-match evidence observation. The existing path can seal the resulting World. | Invalid key universe, not an ambiguous winner or a positive correspondence. A production producer would need to reject this before sealing a comparison-ready snapshot. |
| Malformed/unsupported record | Invalid JSON, numeric `id`, or missing required route form makes producer extraction fail. The current byte locator also rejects valid compact JSON because it searches for the literal pretty-printed `"id": "..."` form. | No sealed comparison-ready snapshot and no negative claim. A production producer would need an explicit supported-input contract or a stronger locator. |
| Skipped published receipt | Test-local construction omits one `software_subject` receipt while the source and route rows contain two records. | Audit reports `INVALID_OR_INCOMPLETE`; no pair or negative is emitted. |
| Version incompatibility | A request for hypothetical producer `v2` against two actual `v1` receipts is refused. | `UNRESOLVED` until an explicit compatibility rule exists. No `v2` producer was invented. |
| Key reuse after deletion | The source accepts an unrelated route with the old `customer-export` ID and radically different path/handler. | A blind stable-key rule still pairs it. Under a real no-reuse source contract, the stated history would violate the contract. The two snapshots alone cannot detect that violation. This is the decisive limit. |

This distinguishes deterministic execution from a strong correspondence basis. With no persistence promise, same-key matching is only candidate evidence. Under an explicit, trusted persistence contract plus audited uniqueness and complete route enumerations, pair and negative outputs would be mechanically entailed **relative to that contract**. The current inputs do not supply it.

## 4. Positive, negative, invalid, and unresolved semantics

No Design-wide status enum was needed. The test-local result uses pairs, `no_prior`, `no_current`, basis and scope, plus a coarse coverage state:

- A **conditional pair** means the exact prior and current subjects have the same validated key under the hypothetical persistent-key contract. It is a producer-level route-record continuation, not merged SoftwareSubject IDs, Design semantic identity, or governance renewal.
- `NO_PRIOR` and `NO_CURRENT` are licensed only by complete enumeration of the relevant finite route sets, unique keys, compatible producer/correspondence versions, and the persistent/no-reuse key meaning. Without the final meaning, the current system must not publish these as true correspondence negatives.
- A duplicate key is an **invalid snapshot for unique comparison**, not a choice between two equally valid successors. Malformed input and missing receipts likewise stop the comparison; they do not imply absence.
- `UNRESOLVED` means the current persistence contract is absent or versions are incompatible. It is not `NO_MATCH`. Partial or malformed evidence is separately reported as invalid/incomplete by the test-local audit.

The negative coverage is only “no route with key K in this producer's complete route universe at this exact publication.” It does not mean no route with equivalent function exists, nor “ungoverned.” The fixture audit can check a bounded JSON array and its sealed projection; a production capability would need to publish or retain an inspectable coverage receipt and reject unsupported/duplicate records at construction time.

## 5. Publication verification and product read

The comparison retains **both exact sealed publication addresses**, both snapshot IDs, both subject IDs for each pair, both source SHA-256 revisions, `config.routes/v1`, and the test-local method/version. Fresh verification reopens the exact publications, reaudits source/World correspondence, and checks the pair endpoints. A twin publication with identical source, snapshot labels, route IDs and logical World ID cannot be substituted: address mismatch fails. Altered source-revision or method fields also fail. Exact address discipline is independent of stable-key semantics.

The product read exercises both governance boundaries:

```text
producer correspondence (conditional in this experiment): A0 ↔ A1
historical W0: governance_binding(P, A0)
current W1a: no governance_binding(P, A1)
current W1b: independently published governance_binding(P, A1)
```

With W1a, the read shows the prior and current manifestations and **historical** P, while current governance is empty and its absence is not a negative governance conclusion. It does not synthesize `governance_binding(P,A1)`. With W1b, the read shows P separately as an independently published current binding. W1a and W1b use identical software source bytes and snapshot IDs but have different World publication addresses and different governance knowledge. This demonstrates source-state change and ontology/World-knowledge change as distinct future write-model concerns; no write behavior was designed here.

The conditional pair would be a useful input to a later change → prior-subject → historical-governance **reconsideration candidate** inquiry. It is not yet an accepted input because persistence is unproven, and this probe neither implements affected-governance retrieval nor creates any reconsideration relation.

## 6. Decision, ownership, and falsifiers

**Outcome C: the source contract must change before a strong producer correspondence capability is justified.** The accepted producer owns extraction, subject IDs, route properties and manifestations. A future `config.routes.correspondence/v0` should be producer-owned if a source contract can promise persistent, unique, never-reused IDs and the producer enforces duplicate/malformed failures and inspectable complete coverage. Design would consume the qualified sidecar and keep historical/current governance separate. OA Core already supplies the sealed publications, assertions and reads; no Core or `SoftwareSubject` change was forced. No Design-generic matcher or status ontology was earned.

This decision would be falsified by a documented existing source guarantee that IDs are immutable and never reused; by an independently verifiable generation/creation token making reuse distinguishable; by a producer-defined retirement ledger that can validate the no-reuse claim; or by a bounded required read that cannot be represented with the current snapshot-local subject and publication model. Conversely, another same-key unrelated replacement would confirm the current limit. Merely adding path/handler similarity must not rescue the key hypothesis.

**Verification:** 15 targeted tests in the new test file. They cover exact/path/handler/reorder/text-move, addition/deletion, duplicates, malformed and unsupported forms, skipped receipts, version refusal, key reuse, exact publication checks, and two governance-read controls. The new probe plus accepted config and prior correspondence tests passed **36 tests**; Core acceptance passed **18** and the default repository gate passed **87**. No production code or accepted contract changed; no commit or push was made.

### Explicit answers

1. **Current `record_id` meaning?** An observed field, not accepted persistent identity.
2. **Can the producer strengthen it now?** Not honestly from the present source format and implementation alone. It needs a source-level no-reuse promise and enforcement/coverage work.
3. **Sufficient invariant?** Within each complete compatible snapshot, each supported route has one unique key; across snapshots, that key is persistent and never reused for an unrelated record. The last clause is absent today.
4. **Path/handler changes?** The hypothetical key rule preserves producer-record correspondence while manifestations change; current producer cannot certify it.
5. **Reorder/move?** The hypothetical pairing survives both JSON-pointer order and byte-offset movement.
6. **Duplicate keys?** Invalid unique-key state. The current producer reuses a subject ID and first source observation; a comparison must stop without choosing.
7. **Key reuse?** Current source permits it. A blind key rule falsely pairs unrelated records; a true persistence contract would deem that history invalid but cannot detect it from these two snapshots alone.
8. **Real `NO_MATCH`?** Only under complete, unique, compatible, persistent-key-covered route universes. None is currently licensed as a producer correspondence negative.
9. **Completeness basis?** Exhaustive successful parse of the bounded route array, no skipped/unsupported records, and equality between source records and published route/member/subject receipts. Governance completeness is a different scope.
10. **Incompatible versions?** Refuse comparison as unresolved until a version compatibility rule is declared.
11. **Strength?** Current same-key evidence is observational/candidate. The test's stronger result is conditional mechanical entailment from a hypothetical source contract, not an accepted producer fact.
12. **Publication identities?** Exact W0/W1 addresses, snapshot IDs, subject IDs, source SHA-256 revisions, producer and comparison method/version.
13. **Historical navigation?** Yes, conditionally; show the prior binding at W0 through the pair and label it historical.
14. **Why no renewal?** Correspondence does not assert `governance_binding(P,A1)`; only W1's own published relation can supply current governance.
15. **SoftwareSubject change?** None required.
16. **Construction change?** None for the experiment. A future production producer capability would need its own validation/coverage contract; accepted Construction was not changed.
17. **OA Core change?** None.
18. **Production config comparison now?** No. The source persistence promise, duplicate rejection and inspectable coverage are missing.
19. **Design-generic abstraction?** No; this remains one producer's possible contract and a test-local sidecar shape.
20. **Ready for change-to-reconsideration experiment?** The conditional shape is useful, but not as established evidence from current fixtures. Establish the source contract first.
21. **Source/World divergence to preserve?** The changed route source can be published with no new binding; the same source bytes can back two separate Worlds with different independently published governance bindings.

## Working-tree status

This pass adds this report and one test file. Both remain untracked and unpushed. The workspace contains other pre-existing uncommitted and untracked work; this pass neither staged nor reverted it. No OA Core file, accepted Design contract, or production config producer was edited.
