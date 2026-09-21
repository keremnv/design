# Core Product v1 baseline and application handoff

Status: frozen capability boundary, solidified 2026-09-21. Read with the
[completion contract](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md),
[acceptance evidence](CORE_PRODUCT_V1_ACCEPTANCE.md), and
[four-region architecture](ARCHITECTURE.md). This is a repository working-tree
baseline, not a release tag or a claim of application/value completion.

## Core Product v1 consists of

Source-specific, mechanically addressable evidence; executable construction;
and a relational World with thin referents, typed named n-ary relations,
assertions, grounding, construction origins, derivations, revision state and
scoped completeness. Candidate admission/publication and supported inspection
complete the path. SQLite is the current storage implementation.

```text
sources → adapters → construction → candidate → validation
→ sealed revision at a fresh address → independent consumption
```

The golden reference is [`profiles/core_v1`](../profiles/core_v1/README.md).
Markdown paragraphs, Python AST syntax and CSV rows are evidence structure.
Requirement identities, approved-boundary interpretation and cross-source
`governs`/`realized_by` joins are constructor decisions, not adapter output.
The adapters can expose unrelated documents/programs/tables without importing
payment concepts. No universal adapter framework is required.

## Core Product v1 guarantees

- Supported construction APIs check declared relation shapes/types and referent
  integrity; admission enforces the selected Contract's recorded-support rules.
- Assertions have inspectable identity, grounding and origin/support paths.
  Registered SQL derivations retain declared inputs and execution/revision state.
- Scoped completeness is recorded and exposed with its basis and known gaps.
  Supported negative inference must consult scope and receipt currentness.
  Currentness here refers to recorded input versions, not unobserved live sources.
- Explicit uncertainty can be represented by ordinary relations: the golden
  refund correspondence retains two grounded candidates and an unresolved
  question, without asserting either candidate is uniquely established.
- Through the canonical fresh-root workflow, old and new sealed revisions
  remain independently addressable and unchanged by reconstruction or reads.
- Consumers can discover schema and inspect relational knowledge, provenance,
  derivations and completeness without constructor internals or raw sources.

Evidence source handles/revisions and reconstruction guarantees are adapter
contracts, not automatic validation of every arbitrary `SourceObservation`.
The golden adapters use SHA-256/UTF-8 byte spans and retained digest-checked
bytes. Markdown segmentation is a lexical subset, not full CommonMark; Python
observations are syntax, not resolved calls/runtime behavior; CSV values are
strings, not business identities. Known losses remain inspectable.

## Core Product v1 does not guarantee

Objective truth, source authenticity, correct arbitrary semantic interpretation,
complete semantic dependency bases, correct consumer use of raw SQL, agent
performance improvement, product value, application completeness, or automatic
semantic renewal. A live LLM is not required.

`PRESERVED` means preservation of the **explicitly recorded maintenance basis**.
The system can inspect and reassess those dependencies; it does not generally
prove that they exhaust every condition on which an interpretation depends.
SQL derivation input checks are a narrower mechanical guarantee, not a semantic
dependency-completeness theorem. Likewise, a COMPLETE receipt is not proof that
an external inventory is exhaustive. Arbitrary SQL can misuse an empty result.

Construction is trusted Python. Sealing/read-only APIs are not a malicious-code
or filesystem-owner sandbox. The tests do not establish power-loss durability,
automatic old-schema migration, global cross-revision identity, or a universal
semantic query language. The small consumer knows its question/role vocabulary;
it is not an ontology-agnostic interpreter or a general large-result client.

## Canonical historical publication

[`profiles/core_v1/build.py`](../profiles/core_v1/build.py) reserves a new root
with exclusive directory creation and runs the existing `Project` there.
The runtime validates a candidate, seals a staging bundle, and renames it to
that root's `world/`. Reconstruction uses a different root. Both bundles are
retained; existing roots, including failed reservations, cannot be reused by
this wrapper. The bundle path is the revision address, not the reused local
`world_id="v0"`, internal mutation counter, or optional mutable current pointer.

This pattern defines Core v1 history semantics. The profile is repository
reference code, not a new installed publication service. An application can
use the same fresh-root pattern with the installed `Project` API and its own
constructor. It must retain the old roots and the supporting blobs/sidecars
needed by its evidence contracts.

Legacy `Project.run()` against an existing root, `rebuild()`, and `author rebuild`
replace their current bundle on success; the temporary `.previous` is removed.
They are not history APIs. They remain unchanged for compatibility. No migration
or promise that every old publication entrypoint now retains history is implied.

## Implementation and executable evidence

Paths are relative to the repository; test names below identify the guarantees,
not merely package presence. `G` means `tests/test_core_v1_acceptance.py`.

| Guarantee | Implementation | Test evidence |
| --- | --- | --- |
| Source/revision identity, bounded addresses, reconstruction, losses | `evidence/markdown.py`, `profiles/core_v1/evidence.py`, `world/core/source.py` (the first and last under `ontology_author/`) | `G`: heterogeneous grounding/reconstruction, Unicode/multiline and corruption tests; `test_markdown_source_profile.py`: bounds and foreign-observation rejection |
| Executable construction, semantic identities and three-source joins | `profiles/core_v1/construction.py`; `world/runtime/project.py` | `G`: heterogeneous join, renamed/changed answers, missing-basis controls |
| Thin referents, typed n-ary relations, assertion identity, revision | `world/core/store.py`: `add_referent`, `declare_relation`, `assert_tuple`, revision bookkeeping | `test_world_store.py`: stable referents, typed tables, assertion uniqueness; `G`: stable unchanged assertions across reconstruction |
| Grounding and distinct construction support origins | `world/core/kernel.py`, `world/runtime/world.py`: assertion admission/supports | `test_construction_origins.py`; `G`: origins and invalid-candidate controls |
| Derivations, dependency tracking, scoped completeness | `world/core/store.py`: `run_derivation`, `latest_completeness`, `absence_is_exhaustive` | `test_world_store.py`: undeclared SQL input rejection, staleness, all three completeness states, unknown derived universe; `G`: scope versus raw SQL |
| Candidate validation and sealed publication | `world/runtime/project.py`, `world/runtime/commit.py` | `G`: shape/grounding/erased-support rejection, pre-publication sealing and injected rename failure |
| Retained immutable history | `profiles/core_v1/build.py` composing the existing lifecycle | `G`: distinct old/new answers, fingerprints, overwrite refusal, fresh consumers after source relocation |
| Schema, relations, grounding, derivation/completeness reads | `world/explorer.py`, `world/runtime/world.py` | `test_stable_read_surfaces.py`; `G`: fresh consumer and renamed relations |
| Truly read-only consumption | `world/core/store.py` SQLite `mode=ro`, no reader schema initialization; escaped SQLite URIs | `G`: SQLite write rejection, audited process, physical read-only mount, revision address containing `#`/`?` |
| Ambiguous cross-source correspondence | Ordinary `candidate_realization` and `open_question` relations in the constructor | `G`: both candidates have prose/CSV/code grounding; no selected realization; consumer reports UNRESOLVED |

Except where qualified, `world/` paths above are under `ontology_author/`.
The fresh consumer is copied with only the World runtime and bundle into a
separate process. It imports no constructor/adapter/fixture helpers; its audit
hook disallows source/evidence-blob reads and writable SQLite. Linux bubblewrap
also excludes the source tree and mounts the bundle read-only. The audited test
is mandatory; physical isolation needs bubblewrap and available user namespaces.

## Working-tree boundary

No files are staged or committed by this pass. These categories must remain
distinct in any later commit/release preparation:

- **CORE V1 BASELINE:** `docs/CORE_PRODUCT_V1_{COMPLETION_CONTRACT,ACCEPTANCE,BASELINE}.md`,
  architecture/docs index/README and `world/CAPABILITY.md` clarifications;
  `profiles/core_v1/`; golden and Markdown tests; `pytest.ini`; the read-only
  plumbing in `world/core/{store,contract_store,kernel}.py`; escaped URI reads in
  `world/core/store.py`, `world/runtime/world.py`, `world/explorer.py`; and bounded
  Markdown validation in `evidence/markdown.py`. The dependency limitation added
  to `docs/SEMANTIC_PERSISTENCE_CONTRACT.md` also belongs to boundary clarification.
- **APPLICATION / EXPERIMENTAL WORK, preserved:** pre-existing edits to
  `program_spine/comparison.py` (exclude snapshot-wide revision from manifestation
  comparison), `semantic_binding/admission.py` (distinct context/property
  maintenance), `tests/test_semantic_delta_selection.py`,
  `tests/test_semantic_persistence.py`, and the new
  `tests/test_maintenance_dependency_conformance.py` and
  `tests/test_design_checkout_granularity.py`. These are not core dependencies.
  The checkout controls demonstrate same-file manifestation noise and the
  blindness of non-manifestation dependencies to callable-body changes; they
  do not justify expanding the spine during this baseline pass.
- **UNRELATED WORKING-TREE CHANGES:** none identified among the non-ignored
  changes at entry. Ignored research artifacts, installed dependencies and
  ignored `experiments/` scripts are not promoted into the core baseline.

The new core files are still untracked until an authorized later commit adds
them. The baseline is the listed working-tree contents, not current `HEAD`.

## Retained implementation debt

| Machinery | Classification | Why retained |
| --- | --- | --- |
| Explicit Purpose compatibility | KEEP AS DEFERRED IMPLEMENTATION DEBT | Supported legacy constructors and `test_purpose_optional.py`; not required to construct a World |
| Contract mixing admission and resolution assessment | KEEP AS DEFERRED IMPLEMENTATION DEBT | Admission is core; existing resolution runtime/tests depend on the other behavior |
| ContractWorldStore obligation/candidate/resolution/adjudication tables | KEEP AS DEFERRED IMPLEMENTATION DEBT | Runtime, explorer and profiles use them; extracting storage requires migration |
| Governance naming collision | KEEP AS DEFERRED IMPLEMENTATION DEBT | Naming cleanup does not strengthen a core guarantee |
| Stable application question/answer/authority reads sharing the explorer | APPLICATION-SPECIFIC BUT CURRENTLY NECESSARY | Existing consumers and stable-read compatibility tests depend on them |
| Recorded resolution versus live current-resolution overlay | NOT ACTUALLY REDUNDANT | Different historical and later-state questions, though neither is core-required |

Nothing meets the bar for REMOVE BEFORE CORE V1 FREEZE. No architectural
cleanup is worth doing before application development on the present evidence.

## Application handoff

**THE APPLICATION MAY RELY ON:** typed relations/referents/assertions;
grounding/origin and derivation/revision inspection; scoped completeness;
explicitly represented unresolvedness; candidate admission; sealed history
through fresh-root publication; and supported read surfaces:
`WorldExplorerAdapter.schema`, `rows` (paginated), `referents`, `assertion`,
`derivation`, `query_semantic`, plus `ConstructionWorld.open(read_only=True)`
and `latest_completeness`. Discover physical columns and relation names; do not
depend on private constructor state. Raw read-only SQL remains available.

**THE APPLICATION MUST OWN:** domain vocabulary and referent conventions,
questions, semantic construction decisions, ambiguity policy, evidence scope
and retention, completeness/dependency adequacy, domain-specific adapters,
authority standing, operational policies, workflow decisions, and the choice
between historical answers and later-state assessment.

**THE APPLICATION MUST NOT REQUIRE CORE MODIFICATION FOR:** domain entities,
classifications, requirements, candidate interpretations, unresolved questions,
domain-specific structure, dependency/support records, or deterministic joins
already honestly expressible through existing referents, relations, assertions,
grounding, derivations, revision and completeness. Program representations,
semantic persistence, maintenance, authority, governance, adequacy and agent
workflows may compose those primitives above the kernel. No fifth layer is
introduced.

**CORE MAY BE REOPENED ONLY IF:** a concrete application requirement cannot be
represented honestly using those primitives without violating a frozen core
guarantee. Present the failing requirement/test first; distinguish missing core
capability from a bad constructor, adapter/fixture limit or application policy.
