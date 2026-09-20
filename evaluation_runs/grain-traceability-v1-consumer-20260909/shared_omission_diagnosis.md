# Shared-omission diagnosis

This diagnosis was started only after the eight final consumer outputs were frozen. It does not modify either World, the benchmark, the gold, the reference artifacts, or Ontology Author.

## Executive finding

The two apparent omissions have different causes.

1. **LO-3 / Spout 3** is a real finer-grain coverage omission. Both constructors read the loadout row, but both represented the loadout with bin, truck, time, quantity, and route while dropping the `spout` field. This is best classified as `MODELED_AT_COARSER_GRAIN`, with a `PURPOSE_SALIENCE_OMISSION` and `SELF_TEST_COVERAGE_GAP`. It is required by frozen CQ-01/CQ-07 but is not unambiguously required by the short natural-language purpose.

2. **WB-390 = 15,000 kg and EF-18 = 11,000 kg within OUT-5002** is not established by host-visible evidence. The source states only that a 26,000 kg hopper movement named `WB-390 / EF-18`; the operating notes explicitly say blended loadout records do not allocate back to individual tickets unless the desk comment says so, and no such comment exists. Both constructors correctly represented the two contributor identities while refusing unsupported quantities. The shared behavior is `CONSIDERED_AND_LEFT_UNRESOLVED`, not a semantic failure. The frozen NQ-01 gold and canonical ledger over-specify the evidence.

## Evaluator obligation audit

| Omission | Host evidence establishes the fact? | Required by purpose alone? | Obligation source | Purpose-only judgment |
|---|---|---|---|---|
| LO-3 / Spout 3 for OUT-5001 | Yes: `loadout_log.csv` explicitly gives `Spout 3` for LD-18; local notes explain the loadout record identifies the bin, truck, and spout | Not strictly. The purpose requires receiving, storage, processing, outbound shipment, provenance, and uncertainty; a trace to the bin/truck can perform that job without spout-level equipment identity | STANDARD_CQ_ONLY | Supported without this finer detail; the missing field is benchmark coverage, not purpose collapse |
| 15,000/11,000 kg split for OUT-5002 | No. `BM-004` and LD-19 give only the combined 26,000 kg and the two ticket names; the notes warn against blended allocation | No. A reasonable evidence-preserving consumer should leave per-source quantities unresolved | NOVEL_BENCHMARK_EXTENSION plus NOT_ACTUALLY_ESTABLISHED | Supported by retaining contributors and unresolved allocation; the frozen gold is not evidence-valid for this detail |

The 15,000/11,000 numbers do sum to the 26,000 kg outbound total, but arithmetic does not identify the source shares. The inbound quantities are 23,850 kg and 17,900 kg, which do not imply the hidden split. No source record, desk comment, timestamp, or ownership record selects those amounts. The canonical ledger’s composition is therefore an evaluator adjudication unsupported by the host-visible corpus.

## LO-3 path, OA-1

### Host evidence

OA-1’s construction transcript line 12 records a full `cat` of all CSV/JSON evidence and includes the loadout row `LD-18 ... Spout 3 ... PGE-OUT-5001`. Thus the row was physically read.

### Constructor representation

In the sealed construction artifact `OA-1/construction.py`:

- line 75 reads `loadout_log.csv`;
- lines 106–110 create `dispatch` assertions with event, cargo, bin, vehicle, quantity, and route code;
- `spout` is not a relation role or assertion value;
- lines 120–126 use work order, bin, date, quantity, and movement sequence to connect the movement to the dispatch;
- the acceptance checks in `checks.py` test the bin/truck lineage and other boundaries, but no spout/loadout-point query or assertion.

The final OA-1 README describes loadout semantics but does not expose a spout field. There is no observable transcript statement saying “Spout 3 was rejected”; the defensible conclusion is that it was modeled at a coarser loadout grain, not that an internal decision can be inferred.

### OA-1 classification

`MODELED_AT_COARSER_GRAIN`; secondary `PURPOSE_SALIENCE_OMISSION`; secondary `SELF_TEST_COVERAGE_GAP`. Not a grounding defect, not a false commitment, and not a kernel limitation.

## LO-3 path, OA-2

### Host evidence

OA-2’s construction transcript records the same full evidence inspection, including the `loadout_log.csv` row with `Spout 3`.

### Constructor representation

In the sealed OA-2 artifact `OA-2/construction.py`:

- line 74 reads `loadout_log.csv` and lines 75–79 materialize each row;
- the `loadout` relation at line 79 contains `cargo`, `dispatch`, `at`, `bin`, `truck`, `kg`, and `route`;
- it has no `spout` role;
- lines 104–109 establish material flow for OUT-5002 using the combined hopper note and dispatch, without equipment-point detail;
- `checks.py` tests positive traces, unresolved cases, source grounding, and completeness, but no spout-level consequence.

Again, no observable evidence shows that OA-2 considered and rejected Spout 3 specifically. It selected the same operational abstraction boundary as OA-1.

### OA-2 classification

`MODELED_AT_COARSER_GRAIN`; secondary `PURPOSE_SALIENCE_OMISSION`; secondary `SELF_TEST_COVERAGE_GAP`. Not a product defect.

## 15,000/11,000 path, OA-1

OA-1 read the full source and its source code explicitly defines the `material_flow` relation at line 50 with the description: “No exact contribution mass or whole-lot equivalence is implied.” Lines 127–130 create two positive flow edges, WB-390 → OUT-5002 and EF-18 → OUT-5002, from BM-004/BM-005 and LD-19. Lines 204–205 add an unresolved source-allocation requirement for OUT-5002/OUT-5003; the OUT-5002 reason states that the two contributors are established but each contribution mass and exhaustive allocation are not recorded.

OA-1’s acceptance query and check validate contributor sets, not a mass split. Its README says the source shares are unknown. This is direct evidence that the constructor noticed the identity relationship and deliberately withheld the unsupported quantitative consequence. Classification: `CONSIDERED_AND_LEFT_UNRESOLVED`, with the underlying evidence state `SOURCE_AMBIGUITY`/`NOT_ACTUALLY_ESTABLISHED`.

## 15,000/11,000 path, OA-2

OA-2’s `flow` relation description at line 17 says that established material contribution does not imply contribution mass. Lines 104–109 create separate WB-390 and EF-18 flow assertions to OUT-5002, with the basis “Explicit combined hopper note WB-390 / EF-18 and OUT-5002 work order.” Line 134 records the unresolved `blend_allocation` requirement: individual kg and proportions are unknown.

The OA-2 acceptance checks require contributor identities in the FEED-2207 trace but do not require quantities. Its README likewise describes the source shares as unknown. This independently reproduces the same conservative semantic judgment. Classification: `CONSIDERED_AND_LEFT_UNRESOLVED`, not `NEVER_NOTICED_SOURCE_FACT` and not `FAILED_TO_PROPAGATE_THROUGH_DERIVATION`.

## Why the correlation occurred

The best-supported explanation is different for each case:

| Candidate explanation | LO-3 | 15,000/11,000 split |
|---|---|---|
| SHARED PURPOSE BLIND SPOT | Contributing: the purpose does not name spout/equipment-point grain | Not the main explanation; purpose and evidence both support unresolvedness |
| SHARED SOURCE SALIENCE ISSUE | Contributing: spout is a field inside an otherwise sufficient loadout row | The source itself makes non-allocation salient through the notes |
| SHARED MODEL/AGENT BIAS | Plausible: both agents naturally modeled a loadout by bin/truck/quantity/route | Not supported as an error; both independently chose the epistemically safe boundary |
| BENCHMARK OVER-SPECIFICATION | Yes: CQ-01/CQ-07 add a point-level consequence beyond the purpose | Strongly yes: gold requires an unsupported source split |
| GENUINE CONSTRUCTOR INCOMPLETENESS | Mildly, for the CQ-required spout field | No; the evidence does not establish the split |
| EVIDENCE AMBIGUITY | No for Spout 3 itself | Yes, decisive |

The identical result is therefore not evidence of one common model hallucination. It is consistent with a common purpose-induced abstraction for LO-3 and a common evidence-preserving refusal for the quantity split.

## Purpose sufficiency without rewriting frozen history

The frozen direct evaluation remains:

```text
FROZEN EVALUATOR VERDICT: PARTIALLY_SUPPORTED
```

That verdict is correct as a benchmark-coverage result because both Worlds omit a frozen gold consequence. It should not be overwritten.

The purpose-only judgment after audit is:

```text
PURPOSE-ONLY INTERPRETATION: SUPPORTED
```

For the declared operational purpose, both Worlds preserve the supported receiving/storage/processing/shipment paths, ownership/custody distinction, temporal ordering, inspection scope, explicit missing links, and completeness-sensitive uncertainty. A consumer can perform the traceability job without reconstructing native source semantics. The spout omission is useful evidence of finer-grain coverage limits, but not enough to make the short purpose unsupported. The 15,000/11,000 split should remain unresolved under the purpose’s own “when the available evidence establishes those links” boundary.

## Evaluator defect statement

The frozen v1 result must remain immutable, but the evaluator design has a concrete defect: `novel_gold.json` NQ-01 marks the 15,000/11,000 split establishable, while the host evidence and operating notes do not establish it. The evaluator-side reference materialization inherits that unsupported split from `canonical_truth/ledger.json`; it does not independently repair the evidentiary gap. Any paper table must label NQ-01 as a gold-match for REFERENCE but an evidence-grounding caveat for the benchmark itself.

This is a separately reportable benchmark/evaluator issue, not a reason to repair OA-1, OA-2, the reference, or Ontology Author during this experiment. A future corrected benchmark would require a new version, not a silent v1 edit.
