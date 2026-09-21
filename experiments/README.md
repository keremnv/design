# Downstream experiment sources

These are application/research harnesses, not Core Product v1 architecture.
The core boundary is [the baseline](../docs/CORE_PRODUCT_V1_BASELINE.md).

Two previously local source scripts are retained because committed regression
tests import their deterministic fixture/setup helpers:

- `run_payment_semantic_persistence_experiment.py`: payment-boundary semantic
  commitment fixture and persistence controls.
- `run_governance_product_experiments.py`: supporting governance/transport
  definitions imported by the payment harness.

The relevant tests are `test_maintenance_dependency_conformance.py`,
`test_semantic_delta_selection.py`, `test_payment_semantic_persistence.py`,
and `test_design_checkout_granularity.py` under `tests/`. They need the local
TypeScript compiler dependency (`npm ci --prefix frontend`), but do not invoke
a live model. Run them with `uv run --extra dev pytest` and explicit test paths.

The conformance work distinguishes identity, exact relation tuples, structural
context and assessed manifestation properties. Selection surfaces recorded
semantic commitments whose declared basis was affected; it does not establish
a semantic verdict or renew knowledge automatically.

The checkout experiment preserves a negative locality result: both relevant
and unrelated same-file UI edits affect the callable's file-based manifestation.
Removing that dependency hides both changes. No richer program representation
is introduced or implied by this record.

The scripts also contain opt-in live experiment entrypoints. They are not the
core quickstart or part of test verification; do not launch them without an
explicit experiment request. Generated runs and other local lab scripts remain
ignored. The installed package excludes this directory and its test helpers.
