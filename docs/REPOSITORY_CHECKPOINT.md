# Core v1 repository checkpoint — 2026-09-21

This is a hygiene/verification record, not a new architectural contract or a
release. The [Core v1 baseline](CORE_PRODUCT_V1_BASELINE.md) remains authoritative.
No application, kernel primitive, framework or automatic renewal was added.

## Commit boundaries

- `252e0fec` — Core v1 contract, acceptance, baseline/handoff, golden profile and
  tests, read-only fixes, Markdown bounds, SQLite URI addressing, default gate
  and architecture reconciliation.
- `e6f64c5b` — downstream maintenance conformance, semantic-delta selection,
  checkout granularity, comparison/admission fixes and tests. Two previously
  ignored experiment source helpers are now tracked so these tests reproduce.
- The hygiene commit containing this record — README, contributor guidance,
  documentation status/archive, generated-state exclusions, package metadata
  and documentation-example regression updates. No functional core change.

## Archive and retained debt

Moved eight historical root documents under `docs/research/archive/`:

- `Benchmark Adaptation_ Grain Traceability.md`
- `Grain Traceability v1 — Integrated Research Record.md`
- `OLD_HARNESS_COMPONENT_TRANSFER_AUDIT.md`
- `Read-side World v0 — first product-shaped reuse slice.md`
- `constructor_frontend_spec.md`
- `world_ir_frontend_spec.md`
- `world_ir_secondary_states.md`
- `makerspace_checkout_tour.md`

The old Cursor guide, always-applied model restriction and graph/MCP example
also live there as `CURSOR_GRAPH_GUIDE.md`, `cursor-model-experiment-policy.md`
and `graphauthor-mcp.json.example`. They are inert historical evidence, not
instructions to current agents. The current Cursor guide has been replaced.
Earlier `FOUNDATIONS.md` is explicitly superseded as product authority.

The [checkout-authority snapshot](../evaluation_runs/checkout-authority-snapshot/README.md)
retains 12 source fixture files and two authority result records byte-for-byte.
Six intermediate generated JSON files under the old `.worlds/checkout-authority/`
were untracked: spine receipt, TypeScript manifest and admission JSON in each
of `fixture/spine/` and `world/`. Local originals were not deleted or changed;
Git history retains every prior tracked version. No useful research was erased.

Existing evaluation transcripts (including original machine paths), grain
traceability fixtures and transfer-audit data remain historical evidence.
Eleven root graph modules and legacy `requirements.txt` remain because historical
tests/results import them; none is included in the installed package. Some
historical tests target removed/private graph interfaces and are not the
configured default gate. See the [research inventory](research/README.md).

Explicit Purpose compatibility, mixed Contract responsibilities, application
records in ContractWorldStore, governance naming, shared read surfaces and
legacy replacement publication APIs remain intentionally deferred debt.

## Verification

Dependency setup: `uv sync --locked --extra dev` and `npm ci --prefix frontend`
both succeeded. Finish dependency installation before starting TypeScript tests.
The exact standard pytest commands are in the [acceptance record](CORE_PRODUCT_V1_ACCEPTANCE.md#reproduction-and-final-solidification-results).
Counts overlap and must not be summed.

| Check | Result |
| --- | --- |
| Golden acceptance (`uv run --extra dev pytest -q tests/test_core_v1_acceptance.py`) | 18 passed, including physical isolation |
| Default gate (`uv run --extra dev pytest`) | 87 passed, no skips |
| Focused kernel/evidence/read/compatibility command in acceptance record | 96 passed, no skips |
| Capability/package regressions (`uv run --extra dev pytest -q tests/test_world_product_surface.py tests/test_packaging_contract.py`) | 16 passed |
| Downstream maintenance/granularity command in acceptance record | 105 passed, no skips, from tracked-files export |
| `npm run build --prefix frontend` | TypeScript and Vite passed; tracked assets unchanged |
| `uv build --quiet` | Wheel and sdist built; inspected 85 wheel / 105 sdist entries |
| README build then fresh consumer commands | Passed; semantic join, unresolvedness and scoped completeness reported |
| Isolated `uv tool install .`, `author --help`, `author attach all --project …` | Passed; Cursor, Claude and Codex files generated in temporary project |
| Local Markdown link targets | 216 checked, no broken targets |
| Archive integrity | 14/14 copied source/result files byte-identical |

The wheel contains current package code, capability, extractor and inspector
assets. It contains no root graph modules, experiment helpers or generated
Worlds. The sdist no longer includes an incomplete automatically selected test
subset whose profiles/fixtures were absent. Tests are run from the checkout.

For reproducibility, exported staged tracked files with
`git checkout-index --all --prefix="$checkpoint_export/"`, reused the installed
Python test environment, and symlinked only the installed frontend dependencies.
No ignored experiment scripts, local Worlds or untracked source were copied.
Product and payment-helper imports were verified to resolve inside that export.
The golden, default and downstream commands were run there using
`"$checkpoint_python" -m pytest` in place of `uv run --extra dev pytest`.
Export results were 18 passed in 2.11s, 87 passed in 28.13s and 105 passed in
182.95s respectively. Focused checks in the working tree passed 96 in 1.55s.

Syntax/whitespace commands:

```sh
uv run python -m compileall -q ontology_author profiles/core_v1 experiments/run_payment_semantic_persistence_experiment.py experiments/run_governance_product_experiments.py tests/test_core_v1_acceptance.py tests/test_markdown_source_profile.py tests/test_world_product_surface.py tests/test_packaging_contract.py
git diff --check
git diff --cached --check
```

All exited 0. No configured Python lint/formatter gate exists; none was invented.
An initial documentation test still selected the legacy Purpose example; it now
executes the documented two-argument constructor and verifies no Purpose relation
is required. An initial downstream invocation overlapped `npm ci` and failed
TypeScript extraction (84 passed, 4 failed, 17 errors); it is not the final result.

`npm audit --prefix frontend --json` exits 1 with four existing dependency
advisories (one moderate, three high). No automatic dependency upgrade was made.
Vite also warns about the existing large chunk. See [release notes](RELEASING.md)
for the retained dependency limitations; this is not a clean security audit.

No live model, release, version tag, application implementation or architecture
redesign was part of this pass. Historical research is preserved without making
it Core v1 product authority.
