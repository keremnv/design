# Final findings

## Experiment identity

- Experiment: `grain-traceability-v1-durable-computation-20260909`.
- Product: Cursor CLI 3.19.13, `cursor-grok-4.6-medium`, medium reasoning; agent package `2026.09.02-c22c1a3`.
- Benchmark and sealed World inputs remain unchanged. The prior GPT-6-Astra artifacts were used only as historical comparators.

## Main result

The computation-authoring boundary generalized imperfectly but usefully. Both bundles exposed the four requested computation families and were invoked by every durable consumer. However, durable consumers still inspected the World and wrote ad hoc semantic queries. OA-G2 showed a small consumer-token reduction relative to synopsis, while OA-G1 did not; therefore the primary token result is representation-dependent in this small workload.

## Grok result table

| Metric | OA-G1 Synopsis | OA-G1 Durable | OA-G2 Synopsis | OA-G2 Durable |
| --- | ---: | ---: | ---: | ---: |
| Correct | 25 | 25 | 28 | 25 |
| Partial | 5 | 5 | 2 | 5 |
| Mean input tokens | 124791 | 134008.67 | 128854.67 | 125882 |
| Mean reported total | 134688.67 | 143058.67 | 137867 | 134229.67 |
| Mean tools | 22.33 | 28.67 | 20 | 22.67 |
| Mean ad hoc semantic queries | 5 | 2 | 3.67 | 2.67 |
| Mean computation invocations | n/a | 8.33 | n/a | 2.67 |

## GPT-6-Astra comparison where available

The earlier GPT-6-Astra World-context experiment used a different downstream question set and no durable computation bundle, so it is not a matched causal comparison. Its historical three-run means were:

| Historical condition | Mean input | Mean reported total | Mean tools |
| --- | ---: | ---: | ---: |
| GPT-6-Astra OA-1-DISCOVERY | 192037.7 | 194789.3 | 7.00 |
| GPT-6-Astra OA-1-SYNOPSIS | 189328.0 | 191943.7 | 7.00 |
| GPT-6-Astra OA-2-DISCOVERY | 167479.0 | 170199.3 | 7.00 |
| GPT-6-Astra OA-2-SYNOPSIS | 141240.3 | 143923.0 | 6.33 |

Cursor/Grok durable mean reported totals were 143,058.7 for OA-G1 and 134,229.7 for OA-G2; matched current synopsis means were 134,688.7 and 137,867.0. The Grok current workload is not numerically pooled with the GPT-6-Astra historical workload because task wording and World lineage differ.

## Frozen judgments

- DURABLE COMPUTATION GENERALIZATION: **PARTIALLY_SUPPORTED**. Both bundles generalized across held-out parameters, but both had uncovered application consequences and several output-shape limitations.
- SEMANTIC NON-INFERIORITY: **INDETERMINATE**. OA-G1 preserved its synopsis count; OA-G2 declined from 28/30 to 25/30 under the frozen heuristic audit, while several partials are scope-sensitive.
- CONSUMER TOKEN REDUCTION: **PARTIALLY_SUPPORTED**. OA-G2 reduced mean reported total by about 2.6%; OA-G1 increased it by about 6.2%.
- AD HOC QUERY REDUCTION: **SUPPORTED** as a directional process result: mean ad hoc semantic-query actions fell from 5.00 to 2.00 for OA-G1 and 3.67 to 2.67 for OA-G2, but did not reach zero.
- APPLICATION-LEVEL TOKEN AMORTIZATION: **PARTIALLY_SUPPORTED**. No OA-G1 break-even; OA-G2 break-even is about 64.9 repeated uses under reported-total accounting.
- REPRESENTATION-INDEPENDENT REUSE: **PARTIALLY_SUPPORTED**. Both schemas accepted and executed durable computations, but the token benefit appeared only for OA-G2.
- KERNEL PRESSURE: **NONE**. All required computation outputs were representable as ordinary parameterized programs over read-only SQLite Worlds; observed gaps are authoring/interface/evaluator-scope issues.

## Interpretation boundary

The frozen gold contains at least two scope-sensitive obligations. `CUST-001` asks for Northstar custody of WB-390 although the evidence records Northstar custody for aggregate OUT-5002 and leaves individual quantity allocation unresolved. `CUST-002` promotes intake owner and physical storage into a point-in-time custody result without a covering ownership event. `SMP-604Q` similarly links “South House 14 cargo” to HFM-IN-604 by path/timing rather than an explicit sample-to-receipt identifier. These remain frozen scoring outcomes and are disclosed rather than used to repair the experiment.

## Holdout integrity caveat

The held-out task file and gold were physically hidden from authoring and consumer hosts, and the frozen bundles contain no held-out literals or answer maps. Because authoring hosts could inspect their complete Worlds, they could infer and test some held-out-looking identifiers; OA-G2’s author-only tests did so. Those tests were excluded from the consumer-visible bundles. The experiment therefore supports computation-shape reuse, but not a stronger claim of strict parameter-value blindness.

## Reuse-history boundary

The preserved execution receipts contain development, direct held-out audit, and durable-consumer invocation records. They are not exposed to any consumer. The history is sufficient for a future experiment on capability/history discovery, which was not run here.
