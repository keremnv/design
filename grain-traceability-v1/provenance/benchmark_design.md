# Benchmark design and freeze boundary

`grain-traceability-v1` is a controlled re-instantiation of the NIST grain-elevator-to-processor traceability problem. The host-visible corpus is newly generated, redistributable, and deliberately operational rather than semantic: CSV exports, JSON logs, and ordinary notes use local terminology and independently shaped identifiers.

The canonical event/material ledger was authored before the host-visible projections. It is the evaluator's underlying world and is never mounted in the construction host. The hidden question sets and gold consequences were authored from that ledger before any construction run.

The host receives only `host_visible/PURPOSE.md`, the `host_visible/evidence/` files, and ordinary source documentation. It does not receive `evaluator_only/`, `reference_only/`, or this provenance directory.

The benchmark is intentionally modest: five inbound receipts, four outbound dispatches, ten bin/movement rows, four carrier manifests, three processor receipts, two processor runs, four inspection rows, seven title/custody records, and one operational-notes file. Every row participates in a deliberate case.

The following cases are fixed before construction:

- a complete single-source chain from Cedar Ridge receipt through BIN-12, Redline transport, HFM-N receipt, and feed run;
- a two-source BIN-12 blend from Willow Bend and East Fork;
- custody changes without title changes and title changes while the elevator remains custodian;
- sample and carrier/processor identifiers that require bounded reconciliation;
- an unsupported `N3 / EF-18?` identity hint;
- a departure with no processor receipt and no source allocation;
- a South House 14 shipment whose contributing inbound load is not individually allocated;
- a time query whose answer changes after the title and custody timestamps;
- completeness scoped to HFM-N but not HFM-E.

No Ontology Author construction, World creation, RAW/WORLD consumer run, or model-behavior tuning is performed as part of freezing this artifact.
