# Core Product v1 acceptance record

Date: 2026-09-21. Specification: [frozen completion contract](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md).

The repository now has a bounded executable core acceptance path in
[`profiles/core_v1`](../profiles/core_v1/README.md), exercised by
[`tests/test_core_v1_acceptance.py`](../tests/test_core_v1_acceptance.py) and
included in the default pytest gate. This record separates that result from
application completion and product-value claims.

## Contract clarifications frozen

- §6.3 and §11: retain prior and new sealed Worlds at independent addresses;
  replacing a current artifact/pointer is not retention.
- §6.5: core records/exposes scoped completeness. Supported reasoning and
  application logic gate negative inference; arbitrary SQL can misuse absence.
- §11: fresh consumption receives only the bundle and supported reads, with
  no constructor internals, fixture helpers, or raw-source access.
- §10–11: an ambiguous cross-source match remains explicitly unresolved.
  Honest human-authored/deterministic interpretation suffices; no live LLM.

## Evidence and construction

| Input | Mechanical adaptation | Constructed contribution |
| --- | --- | --- |
| `fixture/requirements.md` | Existing Markdown paragraph/byte-span adapter | Requirements R-PAY/R-REFUND, operations, approved boundary concepts |
| `fixture/payments.py` | Scenario-local Python AST declarations and direct-return-call syntax | Grounded program endpoints and an observed call relationship |
| `fixture/deployments.csv` | Scenario-local CSV rows with exact byte spans | Production boundary/implementation/provider correspondences |

All three are SHA-256 revisioned. Sealed bundles retain original bytes with
digest-checked reconstruction; the evidence manifest records mechanical losses.
The constructor, not an adapter, interprets requirement meaning and performs
the join. Mechanical, SEMANTIC, and DERIVED origins remain distinguishable.

`governs(requirement:R-PAY, program:checkout, provider:Stripe)` is a constructed
three-source join: prose contains neither the callable nor provider; config
contains no requirement identity; source contains no requirement/manifest
policy. The code evidence is required to establish the endpoint. Its support
includes the requirement paragraph, finite configuration enumeration, matching
row, and declarations. `realized_by(boundary:Harbor, program:route_payment)`
and the derived `governed_call` retain their respective bases. These facts do
not prove runtime policy compliance.

`Returns` has two manifest matches, `refund_eu` and `refund_us`. Candidates and
an explicit unresolved question are stored as ordinary typed relations; no
special uncertainty primitive or governance resolution is needed.

## Executable evidence by criterion

| Criterion | Acceptance test(s), prefix `test_` omitted |
| --- | --- |
| Typed cross-source output, origins, source spans, reconstruction, derivation dependencies | `heterogeneous_join_grounding_origins_and_reconstruction` |
| Explicit ambiguous correspondence, no selected realization | `ambiguity_is_recorded_without_selected_or_negative_match` |
| Scoped completeness versus unknown; raw SQL escape hatch | `completeness_is_scoped_and_raw_sql_does_not_supply_a_truth_policy` |
| Distinct old/new bundles and answers, unchanged old bytes/modes, stable unchanged assertions, overwrite refusal | `reconstruction_retains_independent_history_and_stable_assertions` |
| No writes through a read-only semantic kernel | `read_only_storage_cannot_mutate_even_through_the_semantic_kernel` |
| Invalid shape, ungrounded assertion, erased stored support all prevent publication | `invalid_candidate_never_publishes_or_changes_history` |
| Seal before publication rename; failure leaves history intact | `publication_failure_and_atomic_visibility` |
| Fresh schema-driven consumer; audited and physical isolation | `fresh_consumer_has_only_bundle_and_reads` |
| Changed sources/renamed relation yield newly discovered answers | `fresh_consumer_discovers_renamed_relations_and_changed_cross_source_answers` |
| Missing prose/config match is unresolved; missing code endpoint fails safely | `cross_source_join_does_not_survive_missing_basis` |
| Mechanical adapters independent of semantic names; exact Unicode/multiline spans | `adapters_are_mechanical_and_retain_exact_unicode_and_multiline_spans` |
| Revision/digest verification rejects corrupt retained material | `evidence_reconstruction_rejects_wrong_revision_and_corruption` |

The consumer discovers schema/roles/physical columns and answers all five
acceptance questions from relational state. It uses question vocabulary, not
private constructor knowledge. Raw evidence reconstruction is a separate test,
not a consumer shortcut. It explicitly distinguishes scoped absence from an
unknown broader universe.

Historical retention is demonstrated by `build.py` reserving a fresh Project
root for each reconstruction, **not** by the legacy replacement path. Both old
and new bundle directories remain independently readable after a provider
change. Existing `Project.run()` in-place replacement semantics are unchanged;
clients must use the append-only workflow for the frozen retention contract.

## Failures and narrowly justified changes

1. **Core read-path defect:** the first independent-consumer run failed because
   `SemanticWorld(read_only=True)` called `chmod` on the sealed database and
   opened a writable store with schema initialization. This prevented genuine
   read-only consumption and could mutate historical state during inspection.
   The fix threads the existing read-only mode into `ContractWorldStore` and
   `WorldStore`, opens SQLite with `mode=ro`, and skips schema creation/migration.
   No new semantic primitive, storage schema, or admission policy was added.
2. **Test-harness limitation:** the initial physical sandbox omitted a Conda
   interpreter located outside `/usr`. The harness now mounts that interpreter
   read-only; it still excludes the repository and source tree.
3. **Invalid-constructor controls:** wrong roles, absent grounding, and removed
   support are rejected by existing admission/validation. These demonstrate
   existing capability, not a need for a new primitive. SOURCE coordinates are
   also present in WORLD construction-support records; deleting only the SOURCE
   copies is not equivalent to removing all recorded support. The corruption
   control removes the complete assertion support before final validation.
4. **Bounded construction/input limitation:** a manifest endpoint with no
   declaration fails safely. Recovery, richer matching, or a different source
   language is an application/adapter need, not a demonstrated core gap.
5. **Retention workflow choice:** separate immutable publication roots meet the
   contract with existing lifecycle machinery. No generic history manager was
   necessary. Publication tests cover visibility and injected process-level
   errors, not power-loss durability.

No other missing core capability was demonstrated. Existing schemas must be
compatible with the reader; inspection no longer implicitly migrates history.

## Mechanisms not needed here

No canonical program spine/correspondence, semantic binding or maintenance
warrants, authority standing, GovernanceCase, Purpose, obligations/resolutions,
or currentness overlays are used by the scenario. Ordinary relations suffice
for ambiguity. The existing runtime still contains some of that storage/code;
this is not an architectural removal or proof that other applications do not
need it. A live model is redundant for this deterministic acceptance task.

## Completion judgment and limits

Initial golden acceptance results (before the subsequent solidification pass):

- Golden suite: `uv run --extra dev pytest tests/test_core_v1_acceptance.py`
  (also run directly with the environment's Python): **16 passed**, including
  both audited-process and physical read-only bubblewrap consumption.
- Default gate: `uv run --extra dev pytest`: **76 passed**.
- Targeted regression run: **130 passed** across the golden suite, World store,
  Contract kernel/runtime, stable and obligation reads, Markdown adapter,
  semantic/payment persistence, delta selection, maintenance conformance,
  program comparison, and checkout granularity tests. Counts overlap the
  default gate; they are not additive. This is not the entire historical suite.
- CLI build followed by consumer inspection succeeded: 11 discovered relation
  schemas, the R-PAY/checkout/Stripe join, one unresolved question, and separate
  scoped-absence versus UNKNOWN conclusions.
- `git diff --check` passed. No commit or push was made.

The bounded golden path meets the frozen core-v1 acceptance criteria, including
independent consumption and independently retained revisions. This is a
repository-level core-capability acceptance result, not a declaration that all
historical APIs enforce every new workflow requirement.

A complete real application, general semantic interpretation, compiler-resolved
call identity, economic usefulness, and product-market value remain unproven.
No broader program representation, governance abstraction, or universal adapter
framework is justified by this scenario. The authorized completion steps stop
at core acceptance; application implementation and external value evaluation
remain subsequent work.

## Solidification follow-up

The [Core v1 baseline](CORE_PRODUCT_V1_BASELINE.md) supplies the explicit
guarantee-to-implementation/test map, working-tree separation, canonical
publication semantics, retained-debt classifications and application handoff.
No new primitive or application was added.

Files changed during solidification (distinct from the pre-existing changes
inventoried in the baseline):

- Documentation: `README.md`, `docs/ARCHITECTURE.md`, `docs/README.md`,
  `docs/SEMANTIC_PERSISTENCE_CONTRACT.md`, all three `docs/CORE_PRODUCT_V1_*.md`
  documents, `ontology_author/world/CAPABILITY.md`, `profiles/core_v1/README.md`.
- Correctness/read paths: `ontology_author/evidence/markdown.py`,
  `ontology_author/world/core/store.py`, `ontology_author/world/runtime/world.py`,
  `ontology_author/world/explorer.py`, `profiles/core_v1/consume.py`.
- Acceptance/regression coverage: `tests/test_core_v1_acceptance.py`,
  `tests/test_markdown_source_profile.py`, `pytest.ini`.

`docs/CORE_PRODUCT_V1_BASELINE.md` is new. Existing core read-only plumbing and
the pre-existing maintenance/granularity experiment edits were otherwise retained.

Strengthened acceptance uncovered two small correctness defects, fixed in
existing mechanisms:

- Markdown observation/reconstruction accepted externally supplied ranges
  outside the source bytes (Python slicing could silently truncate). Bounds
  are now checked on both entrypoints, with foreign-identity rejection tests
  and explicit lexical-parser limitations.
- Read-only SQLite addresses interpolated literal filesystem paths into URIs.
  A `#` or `?` in a valid revision directory could select a truncated/wrong path
  and misparse `mode=ro`. The store and both supported identity-read entrypoints
  now use escaped absolute file URIs. Fresh consumption covers that case and
  checks no truncated-path file is created.

The tests now additionally inspect grounding on both ambiguous candidates,
query both retained revisions in fresh consumers after source relocation,
and rename knowledge, ambiguity and completeness-bearing relations with
both empty and nonempty provider-query controls. Question role vocabulary is
still explicit; this is not an arbitrary-ontology reasoning engine.

### Reproduction and final solidification results

Run from the repository root at the Core v1 checkpoint or later, including
the tracked profile/tests/docs, not a pre-baseline revision.
Dependencies are described by `pyproject.toml`, `uv.lock` and the frontend lock:

```sh
uv sync --locked --extra dev
npm ci --prefix frontend
```

Node/TypeScript is needed to run the existing spine tests without skips, not
for the golden core scenario. Linux bubblewrap with usable user namespaces is
needed for its additional physical-isolation check; the audited fresh-process
check remains mandatory without it. Verification here used Python 3.13.12,
uv 0.12.5, Node v22.22.1, TypeScript 5.9.3 and bubblewrap 0.11.1. No live model,
model credentials or external service is needed for these commands.

Golden suite — **18 passed**, including physical isolation:

```sh
uv run --extra dev pytest -q tests/test_core_v1_acceptance.py
```

Default gate — **87 passed**, no skips (now also includes Markdown adapter tests):

```sh
uv run --extra dev pytest
```

Focused World/kernel, evidence, read, boundary and compatibility regressions —
**96 passed**, no skips:

```sh
uv run --extra dev pytest -q \
  tests/test_world_store.py tests/test_contract_kernel.py \
  tests/test_contract_runtime.py tests/test_construction_origins.py \
  tests/test_markdown_source_profile.py tests/test_stable_read_surfaces.py \
  tests/test_world_product_surface.py tests/test_world_obligation_read_surface.py \
  tests/test_architecture_boundaries.py tests/test_purpose_optional.py \
  tests/test_resolution_write_boundary.py tests/test_design_checkout_claim_support.py \
  tests/test_design_checkout_adequacy.py tests/test_packaging_contract.py
```

Separate application/experimental regressions — **105 passed**, no skips:

```sh
uv run --extra dev pytest -q \
  tests/test_maintenance_dependency_conformance.py \
  tests/test_design_checkout_granularity.py tests/test_semantic_delta_selection.py \
  tests/test_semantic_persistence.py tests/test_payment_semantic_persistence.py \
  tests/test_program_spine_comparison.py tests/test_semantic_construction_cycle.py \
  tests/test_authority_maintenance.py
```

At solidification, this last command required the locally ignored payment
experiment helper and was not a clean-clone regression. The subsequent
checkpoint tracks that helper and its governance import in the separate
downstream experiment commit; it is now reproducible from tracked sources.
Neither helper is a core dependency or part of the installed distribution.
The test counts above overlap and must not be summed; the full historical
repository suite was not run.

A temporary export excluding `experiments/` and frontend artifacts also passed
**46 core checks**. It reused
the installed Python test environment but asserted that product imports came
from the exported tree. Exact command:

```sh
baseline_python="$PWD/.venv/bin/python"
baseline_export=$(mktemp -d /tmp/oa-core-v1-baseline.XXXXXX)
cp -R ontology_author profiles tests "$baseline_export/"
cp pyproject.toml pytest.ini uv.lock "$baseline_export/"
cd "$baseline_export"
"$baseline_python" -c 'from pathlib import Path; import ontology_author; assert Path(ontology_author.__file__).resolve().is_relative_to(Path.cwd()); assert not Path("experiments").exists(); assert not Path("frontend").exists()'
"$baseline_python" -m pytest -q tests/test_core_v1_acceptance.py tests/test_markdown_source_profile.py tests/test_world_store.py tests/test_construction_origins.py tests/test_architecture_boundaries.py
```

Syntax/whitespace checks, from the original repository root — both exit **0**:

```sh
uv run python -m compileall -q ontology_author/evidence ontology_author/world profiles/core_v1 tests/test_core_v1_acceptance.py tests/test_markdown_source_profile.py
git diff --check
```

No Python formatter/linter command is configured in `pyproject.toml` or release
CI; none was introduced for this pass. The frontend has a TypeScript/build
command rather than a lint script; no frontend source was changed.

Solidification judgment: the documented core capability/publication/read boundary is
frozen enough for application development. No new kernel primitive, generic
framework, package migration, cleanup removal, application implementation,
commit or push occurred.

The later authorized repository checkpoint is a separate pass: it preserves
this acceptance result, commits core and downstream research separately, and
reconciles onboarding. See the [checkpoint record](REPOSITORY_CHECKPOINT.md)
for its verification, retained limitations and archive inventory.
