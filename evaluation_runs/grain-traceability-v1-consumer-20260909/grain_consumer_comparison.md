# Grain consumer comparison

Benchmark: `grain-traceability-v1`, frozen commit `17e1314f10d8b491b4462f821876a0a42642f1f8`.  
The direct semantic report remains the authoritative benchmark-state record.  
Ontology Author: `0.1.0`, product commit `17e1314f10d8b491b4462f821876a0a42642f1f8`.  
Model/configuration: `gpt-6-astra`, medium reasoning, Codex CLI `0.153.4`, bwrap-isolated workspaces.  
Replicates: two per condition, rather than three; this was the precommitted cost/time deviation in `protocol.md`.

## Protocol and integrity

The same frozen novel question wording was used in all four conditions. RAW saw only `PURPOSE.md`, `README.md`, and host-visible evidence. REFERENCE saw only the evaluator-prepared conventional semantic representation, purpose, and questions. OA-1 and OA-2 saw only one sealed World, purpose, and questions. No consumer saw gold, canonical truth, evaluator files, construction transcripts, another World, or native sources when the condition prohibited them.

The initial two harness attempts are retained as infrastructure failures, not scored runs: attempt 1 mounted the Codex home read-only; attempt 2 mounted `/dev` without a usable pseudo-terminal. Attempt 3 completed all eight runs with exit code zero and usable transcripts. The final result is under `consumer_runs/` in this directory.

World integrity was checked before consumption and again read-only: both supplied bundle hashes matched the frozen metadata, both SQLite databases returned `PRAGMA integrity_check = ok`, foreign-key checks were empty, and all four World files were mode `0444`. The supplied World hashes were:

```text
OA-1 d39faa9ed9e40b03fea7cd329033ae7756664f4dae533ff83a6c7c725006b116
OA-2 1eebe0f15eacb711080db8826d7bc2bad39da3ff28658afcfa5fb5f30da7e9d3
```

World summaries at read time:

| | relations | referents | assertions | derived relation |
|---|---:|---:|---:|---|
| OA-1 | 19 including kernel metadata | 85 | 293 | `trace`, 16 outputs |
| OA-2 | 17 including kernel metadata | 66 | 185 | `trace`, 16 outputs |

## Question-level scoring

Scoring is against the frozen gold consequence set. `CORRECT` includes correct positive consequences and correct handling of the question’s required unresolved parts. `PARTIAL` means the answer preserved the contributor identities but omitted the frozen per-contributor quantities in NQ-01. No run produced an incorrect commitment, unsupported closure, or incorrect unresolvedness on this question set.

| Question | RAW-1 | RAW-2 | REF-1 | REF-2 | OA1-C1 | OA1-C2 | OA2-C1 | OA2-C2 |
|---|---|---|---|---|---|---|---|
| NQ-01 | PARTIAL | PARTIAL | CORRECT* | CORRECT* | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| NQ-02 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-03 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-04 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-05 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-06 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-07 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-08 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-09 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |
| NQ-10 | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT | CORRECT |

`*` The reference answers match frozen gold, but the reference-arm NQ-01 quantity assertion has an evidence-grounding defect discussed below. It is a gold-match, not an independent demonstration that the host evidence establishes the split.

Run durations from the frozen run metadata were: RAW-1 71.3 s, RAW-2 78.6 s, REFERENCE-1 106.8 s, REFERENCE-2 96.5 s, OA1-C1 98.6 s, OA1-C2 97.5 s, OA2-C1 104.0 s, and OA2-C2 102.7 s. These are harness observations, not a cost comparison.

## Aggregate scorecard

| Metric | RAW | REFERENCE | OA-1 | OA-2 |
|---|---:|---:|---:|---:|
| Correct | 18/20 | 20/20* | 18/20 | 18/20 |
| Correctly unresolved consequences | 12/12 | 12/12 | 12/12 | 12/12 |
| Partial | 2 | 0 | 2 | 2 |
| Incorrect | 0 | 0 | 0 | 0 |
| Unsupported closure | 0 | 0* | 0 | 0 |
| Incorrectly unresolved | 0 | 0 | 0 | 0 |
| Native source reads | 2/2 runs | 0/2 runs | 0/2 runs | 0/2 runs |
| Source-specific parsing/reconciliation | yes, both | no | no | no |
| Semantic queries / representation inspection | low; direct file reading | JSON/schema inspection | SQLite relation/schema inspection | SQLite relation/schema inspection |
| Shell/tool actions per run | 4, 5 | 6, 6 (one failed `python` probe retried) | 8 each (one failed `python` probe retried) | 8 each (one failed `python` probe retried) |
| Consumer completion | 2/2 | 2/2 | 2/2 | 2/2 |

The unresolved count is reported as consequence-level coverage of the six questions whose gold explicitly requires unresolvedness (NQ-02, NQ-04, NQ-05, NQ-06, NQ-09, NQ-10), two per condition. It is not a claim that the other questions contain no uncertainty.

## Per-question consequence audit

All four conditions correctly identified the three BIN-12 outbound shipments in NQ-02, preserved the unresolved source allocation for PGE-OUT-5003, and did not use `N3 / EF-18?` as a source identity. All conditions reconstructed the interval-scoped path in NQ-03, including storage, the ownership change for WB-390, OUT-5002, Northstar transport, HFM-IN-602, and FEED-2207. All identified HFM-IN-601 and HFM-IN-602 as having complete identified-load provenance at the frozen benchmark grain while leaving HFM-IN-604 incomplete.

| Question | Capability scored | Evidence/representation basis used in adjudication | Result across conditions |
|---|---|---|---|
| NQ-01 | multi-source composition | BM-004/BM-005, LD-19, plus the frozen gold’s composition assertion | RAW/OA partial; Reference gold-match with grounding caveat |
| NQ-02 | storage-to-downstream reuse | BM-001–BM-006, LD-18–LD-20, operating notes | all complete |
| NQ-03 | interval-scoped forward trace | ER-7721/ER-7729, BM-002/BM-003/BM-004, TR-102, NS-8848, HFM-IN-602, MILL-2207 | all complete |
| NQ-04 | complete versus partial provenance | processor receipt log, carrier bills/manifests, source-ticket flows, unresolved OUT-5004 allocation | all complete |
| NQ-05 | explicit uncertainty inventory | OUT-5003/OUT-5004 gaps, MCR-118 claim conflict, sample candidates, missing downstream records | all complete |
| NQ-06 | missing-event diagnosis | BM-006, LD-20, NS-8910/NS-5003-C, no processor receiving slip, HFM-N completeness scope | all complete |
| NQ-07 | temporal ownership/custody separation | TR-102 and TR-104 effective intervals, OUT-5002 scope | all complete |
| NQ-08 | inspection impact propagation | SMP-602B, HFM-IN-602, MILL-2207/FEED-2207 | all complete |
| NQ-09 | unsupported identity rejection | `N3 / EF-18?`, MCR-118 claims, MC-118/SMP-604Q, South House 14 allocation note | all complete |
| NQ-10 | completeness-sensitive negative | HFM-N complete-window note and log; HFM-E unknown completeness; NS-8910 departure | all complete |

NQ-05 and NQ-06 were especially consistent: every consumer preserved the missing OUT-5003 source allocation and missing processor receiving link, and every consumer kept HFM-E receipt status unknown rather than treating departure or file absence as acceptance/nonreceipt. NQ-07 preserved GrainLink ownership versus Northstar custody at 13:10. NQ-08 propagated the *scope* of SMP-602B to HFM-IN-602 and FEED-2207 without assigning the result separately to WB-390 or EF-18. NQ-09 rejected M. Creek account selection, the MC-118/SMP-604Q near-match, and the question-marked N3/EF-18 identity. NQ-10 made the North-only completeness-sensitive negative and left the East status unresolved.

The only frozen-gold partial was NQ-01. RAW and both Worlds returned WB-390 and EF-18 as contributors but did not return 15,000 kg and 11,000 kg. The reference representation did return those numbers because its evaluator-side materialization copied the canonical ledger composition.

## Source independence and work character

The workspace manifests provide direct physical isolation evidence:

```text
RAW:       PURPOSE.md, README.md, consumer_questions.md, INSTRUCTION.md, evidence/*
REFERENCE: PURPOSE.md, reference/README.md, reference/model.json, reference/instance.json,
           consumer_questions.md, INSTRUCTION.md
OA-1/OA-2: PURPOSE.md, world/world.sqlite, world/world.* sidecars,
           consumer_questions.md, INSTRUCTION.md
```

No REFERENCE or World run had a native evidence path mounted or opened. RAW-1 read the ordinary evidence files in a single shell command; RAW-2 read the notes and then all CSV/JSON files. Neither RAW run wrote a helper database or program; source interpretation was performed directly over the heterogeneous files.

The RAW traces contain source discovery, schema interpretation, cross-source reconciliation, and task reasoning. Representative source-specific conclusions include reconciling receipt tickets to bin movements, matching carrier bills to processor origins, interpreting the operating-note distinction between departure and receipt, and refusing the `N3 / EF-18?` hint. The World traces instead inspect relation schemas and query tables such as `material_flow`, `coverage`, `purpose_requirement_failure`, `ownership_record`, `flow`, `acceptance`, `sample_of`, and `party_record`. The reference traces inspect `model.json` and `instance.json`, then answer over explicit materials, events, intervals, identity decisions, and derived views.

The shift is therefore qualitative, not a tool-count win. OA and REFERENCE consumers still spent time discovering the representation’s schema and uncertainty policy. The compiled World eliminated repeated parsing of CSV/JSON/Markdown and repeated reconstruction of the carrier-to-processor and sample-to-material rules.

## Reference comparison and its caveat

The REFERENCE arm was prepared from the frozen `reference_only/reference_model/model.json` plus the evaluator-side canonical ledger before any consumer ran. The frozen benchmark reference artifacts were not modified. The materialized comparator explicitly contains `M-202` composition entries of 15,000 kg from M-102 and 11,000 kg from M-103.

That is a deliberate semantic-engineering control, but it exposes a benchmark defect: the host-visible records show only a combined 26,000 kg `WB-390 / EF-18` hopper/loadout movement and explicitly state that the loadout does not allocate blended material unless the desk comment says so. No host-visible record supplies a 15,000/11,000 split. Thus the reference consumer is structurally and operationally close to a deliberately engineered semantic layer, but its NQ-01 split is evaluator-supplied rather than host-evidence-grounded.

Subject to that caveat, REFERENCE had the strongest frozen-gold consequence score and the same source-free semantic-query work character as OA. OA-1 and OA-2 achieved the same nine complete question consequences and the same one partial, using materially different schemas. The comparison therefore supports consequence equivalence on 9/10 novel questions, not structural equivalence or universal reference superiority.

The reference model’s shape is conventional and deliberately explicit: `MaterialPortion`, `Load`, `Shipment`, `OperationalEvent`, `Place`, `Container`, `Organization`, `Sample`, `Observation`, `ProcessedProduct`, and `IdentityCandidate`, with relations for event participation, input/output, place/container movement, transport, scoped identity, composition, sampling/observation, ownership, custody, derivation, and status. Its semantic engineering work was precommitted in the reference specification: choose referents and event types; treat identifiers as context-bound; normalize facility/bin/spout/carrier/processor aliases; reconcile bills to receipts; preserve aggregate composition and unresolved allocations; separate ownership from custody; map samples with bounded rules; retain grounding and candidates; implement temporal/provenance/completeness derivations; and define query semantics for both question families. The source mappings additionally specify each file’s grain, identity fields, transformation, and precedence rules. This prior semantic work is a construction cost of REFERENCE and must not disappear from a consumer-only comparison.

## Consumer conclusion

For the frozen-gold benchmark score, REFERENCE was 20/20 question-runs, RAW was 18/20, and each organically constructed World was 18/20. For host-evidence-valid semantics, the interpretation is different: RAW and OA correctly refused to invent a split that the evidence does not establish, while the reference’s 15,000/11,000 assertion is unsupported by the visible source records. The correct paper statement is consequently conditional: an adequate World preserved nearly all required downstream consequences and eliminated native-source reconstruction, but this benchmark’s NQ-01 gold overstates what the operational evidence establishes.
