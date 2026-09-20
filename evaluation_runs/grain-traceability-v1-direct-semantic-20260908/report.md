# grain-traceability-v1 direct semantic evaluation

Evaluation phase: direct hidden semantic evaluation only. No World was rebuilt or modified. RAW, REFERENCE, fresh World-only consumers, repair construction, and model-assisted remediation were not run.

## Frozen inputs

- Benchmark: `grain-traceability-v1`
- Benchmark commit: `17e1314f10d8b491b4462f821876a0a42642f1f8`
- Ontology Author: `0.1.0`
- Ontology Author product commit: `17e1314f10d8b491b4462f821876a0a42642f1f8`
- Evaluation basis: evaluator-only canonical truth, standard gold, novel gold, and `evaluation_spec.md`

Frozen World hashes supplied by the construction phase and matching the frozen construction-result metadata:

- OA-1: `d39faa9ed9e40b03fea7cd329033ae7756664f4dae533ff83a6c7c725006b116`
- OA-2: `1eebe0f15eacb711080db8826d7bc2bad39da3ff28658afcfa5fb5f30da7e9d3`

The per-file sealed manifests also validate for both bundles. The World directories were read-only during evaluation.

## Integrity results

| Check | OA-1 | OA-2 |
|---|---|---|
| Frozen bundle hash record | verified | verified |
| Read-only World directory | pass | pass |
| SQLite integrity check | `ok` | `ok` |
| Foreign-key check | no violations | no violations |
| Readable schema | 19 semantic relations | 17 semantic relations |
| Admission sidecar | valid | valid |
| Purpose sidecar | valid | valid |
| Grounding/origins sidecar | valid | valid |
| Derivation execution | succeeded | succeeded |
| Current/stale state | current | current |
| Completeness receipt | present, `INCOMPLETE` | present, `COMPLETE` over finite admitted graph |

No artifact defect prevented evaluation.

## Primary result table

Question-level “fully correct” requires all required established consequences and the required unresolvedness discipline. Partial means the World preserves the main meaning but omits a gold-critical consequence.

| Metric | OA-1 | OA-2 |
|---|---:|---:|
| Standard-backed fully correct | 8/10 | 8/10 |
| Standard-backed partial | 2/10 | 2/10 |
| Standard-backed incorrect | 0 | 0 |
| Standard-backed incorrectly unresolved | 0 | 0 |
| Novel fully correct | 9/10 | 9/10 |
| Novel partial | 1/10 | 1/10 |
| Novel incorrect | 0 | 0 |
| Novel incorrectly unresolved | 0 | 0 |
| Unsupported closures | 0 | 0 |
| Incorrect commitments | 0 | 0 |
| Grounding defects | 0 | 0 |
| Completeness defects | 0 | 0 |
| Gold-critical consequence coverage | all except LO-3 and blended per-source kg | same |
| Purpose-level verdict | `PARTIALLY_SUPPORTED` | `PARTIALLY_SUPPORTED` |

Both Worlds preserve the important positive paths and all tested uncertainty boundaries. The two partial results are the same in both Worlds.

## Standard-backed questions

All positive commitments listed below had auditable source grounding. Relation names are World-local and are shown only to identify the inspected assertions.

| ID | Expected consequence | OA-1 | OA-2 | World consequence and grounding |
|---|---|---|---|---|
| CQ-01 | BIN-12, LO-3, and RLT-088 associated with OUT-5001 loadout | Partial | Partial | BIN-12 and RLT-088 are represented in `dispatch`; OA-2 has them in `loadout`. Neither World materializes the `Spout 3`/LO-3 field. Grounding: `bin_movements.csv:5`, `loadout_log.csv:2`, local-name note. |
| CQ-02 | DR-44 receiving, storage, sample, loadout, custody/title, transport, processor receipt, and processing events | Correct | Correct | OA-1: `event`, `event_material`, `movement`, `dispatch`, `departure`, `event_link`, `ownership_record`, `receiving`, `processing`. OA-2: `intake`, `stored`, `movement`, `loadout`, `departure`, `party_record`, `acceptance`, `processing`, `flow`. Grounding covers the gold evidence basis. |
| CQ-03 | INTAKE-2, BIN-12, RLT-088, and S-4 | Correct | Correct | Intake movement, BIN-12 loadout, truck, and HFM-N/S-4 receipt are queryable. Grounding: elevator, movement, carrier, and processor records. |
| CQ-04 | WB-390 at BIN-12 at the specified time | Correct | Correct | Entry into BIN-12 precedes the time and later OUT-5002 loadout follows it. Grounding: `bin_movements.csv:3,4` plus event timestamps. |
| CQ-05 | Cedar Ridge Farm as source owner; Prairie Gate as later title holder | Correct | Correct | OA-1 `intake_party` plus `ownership_record`; OA-2 `intake` plus `party_record`. Grounding: elevator receipt, SMP-7714A, TR-101. |
| CQ-06 | Prairie Gate Elevator / PGE-01 as transport source | Correct | Correct | `departure.pickup` is Prairie Gate/PG-ELEV for OUT-5001. Grounding: carrier manifest and local-name documentation. |
| CQ-07 | BIN-12, LO-3, and RLT-088 for OUT-5001 | Partial | Partial | BIN-12 and RLT-088 are represented; LO-3/Spout 3 is omitted as a semantic field. Grounding exists in the loadout source row but the consequence is not materialized. |
| CQ-08 | Prairie Gate, Redline, Hearthland custody intervals | Correct | Correct | Time-scoped custody records distinguish holder from owner and preserve open-ended final interval. Grounding: TR-101/TR-103/TR-106, manifest, and HFM-IN-601. |
| CQ-09 | Prairie Gate, Northstar, Hearthland custody intervals for blended OUT-5002 | Correct | Correct | Aggregate shipment custody is represented separately from component ownership. Grounding: TR-104/TR-105, NS-8848, HFM-IN-602. |
| CQ-10 | NS-5002-B maps to HFM-IN-602 at HFM-N with origin PG-OUT-5002 | Correct | Correct | OA-1 `departure`, `event_link`, and `receiving`; OA-2 `departure`, `manifest_for`, `acceptance`. Grounding: manifest and processor receipt. |

## Novel questions

| ID | Expected consequence | OA-1 | OA-2 | World consequence, unresolvedness, and grounding |
|---|---|---|---|---|
| NQ-01 | WB-390 contributes 15,000 kg and EF-18 contributes 11,000 kg to OUT-5002 | Partial | Partial | Both identify WB-390 and EF-18 as contributors but omit individual contribution quantities. The Worlds explicitly retain the split as unresolved. The gold-required quantity consequence is therefore missing, without false closure. Grounding basis: `bin_movements.csv:6` and source composition adjudication. |
| NQ-02 | BIN-12 downstream shipments: OUT-5001 established, OUT-5002 established to WB/EF, OUT-5003 source allocation unresolved | Correct | Correct | `dispatch`/`movement` or `loadout`/`stored` identify the three shipments; flow exists only for established source contributions. OUT-5003 remains unresolved. |
| NQ-03 | WB-390 and EF-18 forward history through BIN-12, OUT-5002, Northstar, HFM-IN-602, and FEED-2207; WB title change included | Correct | Correct | Temporal event and flow records support the full interval-scoped history. Grounding: receipts, movements, TR-102/TR-104, manifest, HFM-IN-602, and MILL-2207. |
| NQ-04 | Complete upstream provenance for HFM-IN-601 and HFM-IN-602; HFM-IN-604 remains incomplete at source allocation | Correct | Correct | Trace returns DR-44 for HFM-IN-601 and WB/EF for HFM-IN-602; HFM-IN-604 has downstream receipt but no individual inbound allocation. |
| NQ-05 | OUT-5003 and OUT-5004 unresolved chains with the specified missing portions; N3/EF-18? unsupported | Correct | Correct | Both Worlds record explicit unresolved failures for OUT-5003 receipt/source, OUT-5004 allocation, MCR-118 identity, and the route-note sample/source hint. |
| NQ-06 | Missing OUT-5003 processor receipt and source allocation | Correct | Correct | Departure/intended HFM-E is represented; no acceptance/receipt edge is asserted and no source-ticket edge is asserted. North completeness is not misapplied to East. |
| NQ-07 | At 2025-09-04 13:10, WB-390 owner is GrainLink and custody is Northstar | Correct | Correct | TR-102 supplies title state; aggregate OUT-5002 TR-104 supplies custody state. The distinction is preserved. |
| NQ-08 | SMP-602B affects OUT-5002, HFM-IN-602, and FEED-2207 | Correct | Correct | OA-1 `inspection_scope` and `material_flow`; OA-2 `sample_of` and `flow`. No propagation to WB-390 alone or EF-18 alone. |
| NQ-09 | Do not commit N3/EF-18?, MCR-118 account, or OUT-5004 single-source identity | Correct | Correct | Candidate identities and purpose failures remain unresolved; no candidate is asserted as an established identity. |
| NQ-10 | HFM-N: justified no supplied receipt; HFM-E: unknown, not negative | Correct | Correct | HFM-N completeness is scoped and used only for the North negative. HFM-E is represented as an intended destination with unresolved receipt status. |

## False-closure analysis

Both Worlds correctly avoid all tested false closures:

- `PGE-OUT-5003`: departure and intended HFM-E destination are established, but source allocation and processor acceptance are unresolved.
- `PGE-OUT-5004`: HFM-IN-604 receipt is established, while contribution from MCR-118 versus S-52 is unresolved.
- `MCR-118`: `M. Creek` remains a designation with two candidate accounts; neither account is selected.
- `N3 / EF-18?`: remains an unsupported handwritten/route-note match, not EF-18.
- HFM-E absence: neither World converts omission from the North-complete extract into a negative East conclusion.

Unresolvedness is exposed both in explicit purpose-failure assertions and, where relevant, in candidate/context relations. There were no `INCORRECTLY_UNRESOLVED` findings.

## Completeness analysis

### OA-1

OA-1 marks `trace` over `material_flow` as `INCOMPLETE`, with 8 direct material-flow edges and 16 transitive outputs. Its receipt states that closure is complete over admitted direct edges but not complete real-world lineage, with source allocation and missing downstream evidence as known gaps.

This does not block justified positive paths. It also does not license negative conclusions. The HFM-N negative in NQ-10 is supported by the separate site-scoped coverage assertion, not by the trace receipt.

### OA-2

OA-2 marks `trace` over `flow` as `COMPLETE`, with the same 8 direct edges and 16 transitive outputs. Its completeness basis explicitly says the recursive closure exhausts the finite admitted graph and is not complete real-world lineage. Purpose metadata separately retains unresolved source allocation, arrival, and other gaps.

Under the frozen scoring rule, this is acceptable: the universe is explicit and the basis disclaims evidence completeness. It creates a higher downstream interpretation risk than OA-1 because the status is `COMPLETE` and `known_gaps` is empty, but no completeness defect is scored because the scope is explicit and no unsound negative was derived.

Neither World uses trace completeness to conclude that HFM-E has no receipt.

## Grounding audit

All gold-critical positive assertions in both Worlds have auditable source grounding. Grounding pointers reference all eight host-visible evidence files, and their recorded source revisions match the frozen host-visible files. No wrong-source or missing-source grounding was found for committed semantic facts.

The 13 purpose-failure rows in each World do not use ordinary `SOURCE` grounding rows in the same way as factual assertions; they carry explicit `grounding_ref` fields to the relevant host-visible evidence and gaps. This is sufficient for the unresolvedness audit and is not a gold-critical positive grounding defect.

Grounding classification:

- `SUFFICIENT`: all committed gold-critical positive consequences.
- `COARSE_BUT_AUDITABLE`: none material to scoring.
- `WRONG_SOURCE`: none.
- `MISSING`: none for committed positives. The omitted LO-3 and per-source kg are missing representations, not grounding defects.

## Derived-state audit

| Property | OA-1 | OA-2 |
|---|---|---|
| Direct flow relation | `material_flow`, 8 rows | `flow`, 8 rows |
| Derived relation | `trace`, 16 rows | `trace`, 16 rows |
| Inputs | `material_flow` | `flow` |
| Execution | succeeded at current revision 362 | succeeded at current revision 235 |
| Derived origins | 16 `DERIVED` assertions | 16 `DERIVED` assertions |
| Derivation grounding | 16 derivation groundings | 16 derivation groundings |
| Unsupported source collapse | none | none |

Neither derivation creates an OUT-5003 source/receipt edge or an OUT-5004 individual source edge. The recursive closure preserves the intended contribution semantics rather than converting co-storage into provenance.

## Semantic audit classifications

### SUPPORTED

Receiving, storage, movement, loadout, departure, processor receipt, processing, transport origin, source ownership, custody, title/custody distinction, temporal ordering, shipment cross-reference, multi-source contributor identity, sample-to-combined-cargo linkage, and completeness-sensitive East uncertainty are supported in both Worlds.

### CORRECTLY_UNRESOLVED

Both Worlds correctly preserve unresolvedness for OUT-5003 source allocation and receipt, OUT-5004 individual source allocation, MCR-118 account identity, N3/EF-18?, sample scope for ambiguous samples, missing downstream product fate, and incomplete mass/ownership coverage.

### SUPPORTED_BUT_OVERMODELED

OA-1 records SMP-604Q as scoped to BIN-14 with `storage_cargo_context_only`. This is an explicit contextual association, not a claim that the sample is from MCR-118, OUT-5004, or HFM-IN-604. It is harmless overmodeling rather than a false identity commitment. OA-2 leaves the same sample without a `sample_of` assertion and records the unresolvedness in purpose metadata.

### MISSING_PURPOSE_RELEVANT_MEANING

1. Both Worlds omit the `Spout 3`/LO-3 loadout-point consequence for OUT-5001.
2. Both Worlds omit the adjudicated individual contribution quantities 15,000 kg and 11,000 kg for WB-390 and EF-18 in OUT-5002.

### INCORRECT_COMMITMENT

None.

### UNSUPPORTED_CLOSURE

None.

### INCORRECTLY_UNRESOLVED

None.

### GROUNDING_DEFECT / COMPLETENESS_DEFECT

None.

## Representation comparison after independent scoring

OA-1 is event-first. It uses explicit `event`, `event_material`, `event_link`, `movement`, `receiving`, `dispatch`, `departure`, `material_flow`, `ownership_record`, `inspection_scope`, and `party_candidate` relations. It generally uses host-facing identifiers directly and records semantic aliases separately.

OA-2 is lifecycle/stage-first. It uses `intake`, `stored`, `movement`, `loadout`, `departure`, `manifest_for`, `acceptance`, `flow`, `processing`, `party_record`, and `sample_of`. It uses scoped identifiers such as `ticket:`, `bin:`, `site:`, and `point:` to separate namespaces.

The Worlds use different grains for event history and identity reconciliation, but preserve the same scored consequences except for the same two omissions. Both use a recursive derived trace relation. OA-1 expresses unresolvedness through 13 detailed requirement rows tied to specific identities; OA-2 uses 13 semantically named purpose failures tied to relations. Neither schema is canonical, and neither is preferred for structural resemblance.

## Construction-convergence telemetry

This section was inspected only after primary semantic scoring was frozen.

| Telemetry | OA-1 | OA-2 |
|---|---:|---:|
| Autonomous convergence | yes | yes |
| Human semantic intervention | 0 | 0 |
| Rebuilds | 10 | 12 |
| Recovered intermediate rebuild iterations | 2 failed intermediate attempts, recovered | 3 failed intermediate attempts, recovered |
| Clarification requests | none | none |
| Constructor-authored self-test/diagnostic actions | 6 recorded | 8 recorded |
| Sealed valid World | yes | yes |

Recovered semantic self-correction is not counted as a separate confirmed event because the retained telemetry does not prove a specific candidate-to-candidate semantic correction independent of ordinary iterative construction. The final artifacts do show explicit self-tests and intentional uncertainty boundaries.

The earlier launcher, DNS, and disposable capability-frontmatter issues are infrastructure/setup matters, not semantic-construction failures.

## Material failure diagnoses

| Failure | Classification | Kernel relevance |
|---|---|---|
| LO-3/Spout 3 absent from both loadout representations | `MISSING REPRESENTATION`, `UNDER-SPECIFIED GRAIN` | Constructor schema omission; the kernel could represent the field. |
| OUT-5002 per-source 15,000/11,000 kg absent from both flow representations | `MISSING REPRESENTATION`, `UNDER-SPECIFIED GRAIN` | Constructor did not materialize the gold-required split; no kernel limitation demonstrated. |

Neither failure is an unsupported closure. Both are omissions in the constructor's semantic projection.

## Kernel-pressure assessment

`KERNEL PRESSURE: NONE`

The observed misses are representational/construction choices. The existing Ontology Author kernel successfully represented typed referents, scoped aliases, event records, time intervals, custody versus ownership, explicit unresolvedness, source grounding, site-scoped completeness, and deterministic derived relations. No purpose-relevant consequence failed because the kernel could not express it.

## Frozen evaluation artifacts

- Sealed evaluation report: `evaluation_runs/grain-traceability-v1-direct-semantic-20260908/report.md`
- OA-1 frozen World: `/tmp/grain-traceability-v1-experiment-final-20260908/sealed/OA-1/world`
- OA-2 frozen World: `/tmp/grain-traceability-v1-experiment-final-20260908/sealed/OA-2/world`
- OA-1 construction-result metadata: `/tmp/grain-traceability-v1-experiment-final-20260908/metadata/construction_result_report.json`
- OA-1 transcript: `/tmp/grain-traceability-v1-experiment-final-20260908/transcripts/OA-1.jsonl`
- OA-2 transcript: `/tmp/grain-traceability-v1-experiment-final-20260908/transcripts/OA-2.jsonl`

No World, benchmark source, evaluator artifact, gold file, question file, or reference artifact was modified.
