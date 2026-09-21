# Contributor and agent guidance

Core Product v1 is frozen. Read, in order:

1. [Core baseline and application handoff](docs/CORE_PRODUCT_V1_BASELINE.md)
2. [Completion contract](docs/CORE_PRODUCT_V1_COMPLETION_CONTRACT.md)
3. [Architecture](docs/ARCHITECTURE.md)

Applications own domain vocabulary, semantic interpretation, authority,
questions, policies, and operational workflows. Do not change core unless a
concrete requirement cannot be represented honestly with its existing
primitives without violating a frozen guarantee. Present the failing case
before introducing machinery. Reuse alone does not justify a kernel primitive.

Canonical construction is sources → adapters → construction → candidate →
validation → a sealed revision at a **fresh address** → independent reads.
Never mutate accepted history. Legacy in-place rebuild APIs remain compatibility
paths, not historical retention. Evidence adapters describe/reconstruct source
material; they must not decide semantic meaning or standing.

## Repository orientation

- `ontology_author/world/`: runtime, kernel, reads, CLI and bundled inspector.
- `ontology_author/evidence/`: source addressing/reconstruction.
- `profiles/core_v1/`: executable core acceptance example, not a domain framework.
- Other `profiles/`, program spine, semantic binding, authority and governance:
  downstream application/research mechanisms.
- `docs/research/README.md`: historical code/results inventory. Old contracts,
  prompts and model policies there are evidence, not contributor instructions.

Keep core, downstream experiments and hygiene changes separate. Preserve useful
research and tracked test fixtures. Do not restore old graph/MCP/agent dependencies
to the installed package or move compatibility code merely for package purity.
Do not run live model experiments, publish a release, commit or push unless the
user's task authorizes that action. Never stage credentials or new run transcripts
without explicit review. There is no live-model requirement for core tests.

## Verification

```sh
uv sync --locked --extra dev
npm ci --prefix frontend
uv run --extra dev pytest -q tests/test_core_v1_acceptance.py
uv run --extra dev pytest
git diff --check
```

Run targeted tests for changed code as well. The
[acceptance record](docs/CORE_PRODUCT_V1_ACCEPTANCE.md) lists the focused kernel,
evidence/read and downstream regression commands; counts overlap. Historical
tests outside the default gate may need archived/private artifacts. Report
missing inputs honestly; do not confuse the default gate with the entire suite.

For frontend or packaging changes, also run:

```sh
npm run build --prefix frontend
uv build
```

The frontend build refreshes the intentionally bundled assets under
`ontology_author/world/static/`; review any generated diff. No Python
formatter/linter gate is configured. See [release guidance](docs/RELEASING.md)
for distribution checks; a package build is not authorization to publish.
