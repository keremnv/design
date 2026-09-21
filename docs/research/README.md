# Research and historical material

This material is evidence, not current product authority. Start with the
[Core v1 baseline](../CORE_PRODUCT_V1_BASELINE.md) and
[documentation index](../README.md).

## Downstream experiments

The semantic/authority/governance/program-spine documents in `docs/` describe
bounded application contracts and experimental mechanisms. The tracked
[`experiments/`](../../experiments/README.md) sources make the recent maintenance,
semantic-selection and checkout-granularity regressions reproducible without
making them part of Core v1. Their live-run entrypoints are opt-in only.

## Archived documents

`archive/` contains earlier root-level frontend specifications, grain-traceability
research, the old-harness transfer audit, the read-side reuse proposal, the
makerspace tour, and superseded Cursor/model/MCP guidance. They retain historical
terminology and may mention paths/protocols no longer present. Such references
describe the original work; they are not setup instructions for this checkout.

## Retained research areas

| Location | Status and retention reason |
| --- | --- |
| [`evaluation_runs/`](../../evaluation_runs/README.md) | Frozen research evidence, including transcripts, result tables and original machine paths; not portable active Worlds |
| [`architecture_transfer_audit/`](../../architecture_transfer_audit/) | Machine-readable companion to the [archived audit](archive/OLD_HARNESS_COMPONENT_TRANSFER_AUDIT.md); claims/evidence retain their original context |
| [`grain-traceability-v1/`](../../grain-traceability-v1/) | Source corpus, provenance and historical application fixture; not the core ontology |
| [`lifecycle_generic_core_v1/`](../../lifecycle_generic_core_v1/) | Earlier lifecycle research fixture; its name does not identify today's Core Product v1 |
| Root graph modules and `requirements.txt` | Legacy graph/retrieval code still referenced by historical tests; excluded from the installed package |

The root legacy modules are `backend_tools.py`, `contract.py`, `engine.py`,
`graph_overlay.py`, `graph_read.py`, `models.py`, `normative.py`,
`retrieval_program.py`, `seeds.py`, `spine.py`, and `tools.py`. Moving/deleting
them would require a broader historical-test migration; that is intentionally
not part of repository hygiene. `requirements.txt` is their legacy dependency
record, not the core installation path (`uv sync --locked --extra dev`).

Historical tests also remain, including `tests/test_readme_example_compiles.py`,
which targets a removed graph-era README/`mcp_server` interface. These are not
the configured default gate and may require earlier/private source artifacts;
keeping them is evidence retention, not a claim that the entire historical
suite runs against the current product.

Large evaluation transcripts and receipts are retained because they are primary
research evidence, not reproducible source fixtures. Do not edit original paths,
hashes or observations to make old results appear portable. New runs remain
ignored unless deliberately selected for archival review.
