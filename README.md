# Ontology Author

Ontology Author turns heterogeneous workspace evidence into a bounded,
queryable relational **World**, preserving provenance, revision, construction
origin, scoped completeness, and unresolvedness where represented.

**Core Product v1 is the current frozen capability baseline.** Applications
and research build above it. Core acceptance does not establish application
completeness, agent-productivity improvement, or economic/product-market value.

## Why construct a World?

Documents, code, and configuration can jointly support relationships that no
single source states. Construction makes those joins inspectable and reusable:

```text
requirements + program source + deployment configuration
    → semantic construction
    → grounded relationships queryable with SQL or Python
```

The [golden scenario](profiles/core_v1/README.md) constructs a requirement's
governing relationship to a checkout entrypoint and provider from three source
forms. Another boundary has two candidate implementations and stays explicitly
unresolved. This demonstrates a technical capability, not its value relative
to repeatedly inspecting the sources.

## Core lifecycle

```text
heterogeneous sources
    → evidence adaptation
    → executable construction
    → candidate relational knowledge
    → mechanical validation / admission
    → append-only sealed World revision
    → independent read / inspection
```

Evidence adapters supply source identity, revision, bounded addresses,
reconstruction, known losses, and source-native structure such as Markdown
paragraphs, AST syntax, or CSV rows. **Construction owns semantic interpretation**;
adapters do not extract an ontology or assign authority.

Canonical v1 publication allocates a fresh revision root for every build.
Old and new sealed bundles remain independently addressable. The reference
workflow is [`profiles/core_v1/build.py`](profiles/core_v1/build.py), composed
from the existing `Project` runtime. A live LLM is not required.

## Try the core scenario

From this repository checkout, with Python 3.11–3.13 and
[uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked --extra dev
revision_root="$(mktemp -d)/revision-1"
uv run python -m profiles.core_v1.build "$revision_root"
uv run python -m profiles.core_v1.consume "$revision_root/world"
uv run --extra dev pytest -q tests/test_core_v1_acceptance.py
```

The consumer discovers schema and reports constructed knowledge, grounding,
origins, unresolved questions, and completeness-based conclusions. For another
build, choose a new revision root; existing roots are rejected. Use
`--sources /path/to/source-copy` to construct from an edited copy of the fixture.
The profile is a repository example, not an installed domain framework.

Supported Python reads include `WorldExplorerAdapter.schema()`, `rows()`,
`assertion()`, `derivation()`, and `query_semantic()`, plus
`ConstructionWorld.open(..., read_only=True).latest_completeness()`.
See the [baseline/read-surface contract](docs/CORE_PRODUCT_V1_BASELINE.md).

The installed `author` CLI also supports workspace creation, agent attachment,
and the bundled read-only inspector; inspect it with `uv run author --help`.
**Compatibility note:** `author rebuild` and in-place `Project.run()` replace
their current bundle. They do not implement the v1 historical-retention pattern.
See [agent attachment](docs/AGENT_CLIENTS.md) for the optional conversational
workflow. `governance` is an opt-in downstream application CLI, not a core stage.

## What a World contains

Thin referents; typed named n-ary relations; assertions; grounding and origins;
deterministic derivations; revision state; scoped completeness; and explicit
unresolvedness where construction represents it. Meaning resides in relations,
not a universal object schema. Purpose machinery is not required.

You can inspect what was asserted, its evidence and construction basis, its
revision context, and the completeness claims recorded for a named scope.
Retained evidence bytes can support digest-checked historical reconstruction.

These guarantees are narrower than truth:

- Recorded dependencies need not exhaust every semantic dependency.
- `PRESERVED` means the recorded maintenance basis was preserved.
- Completeness supports bounded inference; arbitrary SQL can misuse absence.
- There is no automatic semantic renewal, objective-truth guarantee, or promise
  of application correctness or improved agent performance.
- Sealing protects the supported workflow, not against a malicious filesystem
  owner or untrusted constructor. Power-loss durability is not established.

## Develop and explore

```sh
npm ci --prefix frontend
uv run --extra dev pytest
```

Node/TypeScript enables the existing program-spine compatibility tests; it is
not needed for the golden scenario. Linux bubblewrap enables an additional
physical-isolation check; the audited fresh-process consumer test always runs.
See [contributor guidance](AGENTS.md) for verification and package-build steps.

- [Core v1 baseline and application handoff](docs/CORE_PRODUCT_V1_BASELINE.md)
- [Frozen completion contract](docs/CORE_PRODUCT_V1_COMPLETION_CONTRACT.md)
- [Acceptance evidence and exact verification commands](docs/CORE_PRODUCT_V1_ACCEPTANCE.md)
- [Four-region architecture](docs/ARCHITECTURE.md)
- [Documentation index](docs/README.md)
- [Research/archive orientation](docs/research/README.md)

`ontology_author/`, `profiles/`, `tests/`, and `frontend/` contain product code,
examples/application profiles, tests, and inspector source. Program spine,
semantic binding, maintenance, authority, governance, and workflow mechanisms
are downstream extensions—not Core v1 requirements. Historical graph modules
and research results remain for evidence/compatibility; they are excluded from
the installed product and are not architecture authority.
