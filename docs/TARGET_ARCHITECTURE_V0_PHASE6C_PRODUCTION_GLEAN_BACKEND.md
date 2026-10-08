# Phase 6C — Production GleanProgramBackend

This phase adds an installed, bounded Glean reader over the standalone C++ basis
proved in [Phase 6B](TARGET_ARCHITECTURE_V0_PHASE6B_GLEAN_BASIS_AND_CPP_CONFORMANCE.md).
Remote main was fetched and verified at
`b548718fcd62306d374765ba5b90e34d10caa312` before creating this branch.

The frozen `ProgramBackend`, native implementation, Phase 5 contracts and
semantic publication are unchanged. There is no backend registry, universal
occurrence reference, second program graph, SQL projection or exploration product.

## Installed implementation

- `ontology_author/program_backend/glean.py`: exact read-only CLI transport,
  two explicit opening paths and `GleanProgramBackend`.
- `ontology_author/program_backend/glean_basis.py`: Glean-specific retained
  identity/manifest/recipe record and digest-checked source bytes. Its JSON shape
  and digest computation are compatible with retained Phase 6B records.

No Glean Python package, graph/agent dependency, bundled binary or new executable
entrypoint is installed. A deployment supplies its trusted CLI endpoint, logical
retained namespace and blob-store location. The CLI prefix is an argv tuple,
including store/schema configuration, optionally wrapped by a container runner.
The adapter appends read-only status/query commands and exact Repo selection.
The pinned CLI exhausts query continuations without a result limit. It launches
a CLI process per operation; this phase establishes correctness, not throughput.

The initial recipe pins Glean commit
`4e576957778b721f28cec21556066a02c3ed84d0`, stored schema
`66a80a62611346b34e2dcaba40d0d58b`, the Phase 6B executable fingerprints,
Clang/LLVM 15.0.7, C++17/no-standard-includes argv, source-range dialect and the
standalone cpp-cmake recipe. Predicate interpretations are explicit:
`cxx1.*.5`, `codemarkup.cxx.CxxDeclKind.5`, `src.*.1`,
`digest.FileDigest.1` and `buck.TranslationUnit.4`.
Other schema, binary, indexing recipe or dependency forms fail qualification.

## Exact opening and independent admission

Identity remains:

```text
logical retained namespace + exact Repo(name/hash) + expected glean.guid
```

Stored schema, indexed-input manifest, recipe and retained source bytes separately
qualify that occurrence. Standalone records must declare no dependencies; native
status carrying stacked/pruned dependencies is refused. Every public mechanical
read checks the exact DB's namespace, Repo, GUID, COMPLETE state, stored schema,
server build revision and producer manifest/recipe properties. A lost or recreated
Repo fails; no latest lookup, reindex or content-equality substitution exists.
Accepted retention/no key reuse/no unfinish remains the application covenant.
These checks are not a malicious storage-owner sandbox or an atomic retention
transaction across processes.

`open_glean_occurrence(basis, client=..., blobs=...)` checks candidate consistency
and retained inputs. It confers no accepted-publication admission.

`open_admitted_glean_occurrence(..., admitted_digest=...)` additionally requires
a digest independently obtained from the admitting application's retained record.
Missing or mismatched qualification fails. The strict path never falls back to
the candidate's own digest. Tests save a trusted pin separately and reformat a
candidate's serialized recipe: normalized recipe/state qualification remains
equal, while the candidate record digest changes. Consistency succeeds; strict
opening against the original pin fails; the original record succeeds.
This models independent admission, not integration with Ontology Author's
accepted-publication system.

Example composition (paths and trusted inputs are deployment-owned):

```python
from pathlib import Path
from ontology_author.program_backend.glean import GleanCLI, open_admitted_glean_occurrence
from ontology_author.program_backend.glean_basis import GleanBasis

basis = GleanBasis.from_json(Path(basis_record_address).read_text())
client = GleanCLI(
    [glean_executable, "--db-root", retained_db_root, "--schema", pinned_schema_source],
    namespace=independently_resolved_namespace,
)
with open_admitted_glean_occurrence(
    basis, client=client, blobs=retained_blob_root,
    admitted_digest=independently_retained_admission_digest,
) as reader:
    assert reader.is_member(selected_local_token)
    material = [reader.reconstruct(handle) for handle in reader.observations(selected_local_token)]
```

The namespace/transport are trusted application configuration. Remote service
authentication and deployment-wide retention enforcement are not supplied here.

## Frozen method mapping

| Method | Production behavior |
| --- | --- |
| snapshot | Stable opaque input/recipe/schema state digest; distinct from occurrence identity |
| is_member | Selected typed lookup for function, file or translation-unit tokens; wrong/unknown types are nonmembers |
| kind | Native function kind ordinal 13 or verified file/unit predicate type; no filename/text inference |
| containment | Selected declaration/trace/main-file joins; unit → file → function ownership; selected file → unit parent read; unit is a root |
| capability | Requested-family status/scope/basis/gaps; kind/containment/evidence INCOMPLETE |
| observations | JSON-roundtrippable opaque selected declaration handles; file/unit members may have no observations |
| reconstruct | Exact retained UTF-8 byte-column inclusive range; entity/file/range/basis checked against the opened DB; (material, verified) |
| verify | Exact occurrence plus native input inventory/failure records and all retained blobs; named violations on failure |
| invocations / resolutions | Frozen defaults: NOT_PRODUCED with empty reads; no xref-to-call mapping |
| discover | Frozen OptionalUnsupported default; explicit fixture selection occurs outside the reader |
| close | Handle becomes closed; subsequent mechanical reads fail explicitly |

Local tokens are opaque hashable `(predicate, local_fact_id)` tuples. The adapter
admits only the three proven categories, not every Glean fact. Qualified identity
is the opened occurrence plus the token; equal numeric or typed tokens in two
independent indexes do not collapse those occurrences. Containment preserves those
exact typed endpoints in parent/child roles, and public membership/kind qualify
every returned endpoint. The edges express compiler/source ownership, not lexical
namespace/record ancestry. Header/multi-unit context is incomplete or explicitly
refused rather than assigned an invented unique ancestor.

Opening and verify independently query `src.IndexFailure.1` and
`digest.FileDigest.1`. The native producer's SHA-1/byte sizes and indexed path
inventory must match all retained SHA-256 blobs, including generated headers.
Producer properties alone are insufficient. This preserves the admitted
controlled immutable workspace scope; it is not arbitrary mutable-build capture.

Reconstruction rechecks the selected native declaration association and uses only
its retained blob, with no checkout fallback. CRLF and Unicode prefixes retain
their exact bytes. Wrong revision/range/file/blob, corruption, missing bytes or
symlink indirection cannot reconstruct as verified. Opening/verify check the whole
retained input closure; reconstruction verifies the selected material. Query or
DB failure remains an explicit BackendError, distinct from invalid evidence's
`("", False)`. A verified observation for E2 still cannot satisfy E1's independently
expected manifestation; production tests retain that dishonest substitution.

Requested-family qualification includes the requested family, recipe and stored
schema. Valid metadata for another family fails the independent association
check. COMPLETE storage never confers analysis completeness; a COMPLETE DB with
IndexFailure is refused by this successful-input recipe. Unknown families fail
qualification. Wrong-type/missing-fact CLI output is the only native error
normalized to nonmembership; zero exit with other `glean:` error output, malformed
JSON, partial rows with an error, schema errors and transport failures stay errors.

## Verification and reproducibility

`tests/test_program_backend_glean.py` contains portable production adapter tests
using modeled native-shaped responses, including dishonest dispatch, evidence,
family, occurrence/admission and retention controls. It is included in default
CI. It does not claim Glean runtime execution.

`tests/phase6c_glean_backend_probe.py` independently exercises the installed
production reader against retained P1/P2 and the recreated independent Repo in
the existing fingerprinted runtime. It leaves those artifacts unchanged and
checks workspace absence, selected evidence/context, all typed endpoints, optional
families, both valid substitutions, native errors and the separate admission pin.
It also observes the retained missing-header COMPLETE/IndexFailure control.
This manual probe is outside default CI and requires external runtime artifacts.

```sh
uv sync --locked --extra dev
npm ci --prefix frontend
uv run --extra dev pytest -q tests/test_program_backend_glean.py tests/test_phase6b_glean_basis.py
uv run --extra dev pytest -q tests/test_core_v1_acceptance.py
uv run --extra dev pytest
uv run python -m tests.phase6c_glean_backend_probe \
  --work "$HOME/.cache/design-phase6b-runtime" \
  --store "$HOME/.cache/design-phase6b-runtime/spike/deedaf9cd15c4e128aab182fb8168495"
npm run build --prefix frontend
uv build
git diff --check
```

For a fresh retained store, execute the Phase 6B build/probe instructions and pass
its reported store to the production probe. Building, indexing and selected-entity
selection remain separate from the read-only production backend.

Broader C++, arbitrary build systems, stacked/pruned runtime, backup/restore,
deployment retention enforcement and semantic publication migration remain
outside this phase. No full program graph or native publication clone is exported
or replaced here.

### Executed validation record (2026-10-08)

- Production adapter tests with modeled native responses: **68 passed**.
- Preserved Phase 6B experimental tests: **28 passed**.
- Core acceptance: **18 passed**. The combined focused command passed 114;
  these overlap the default gate and must not be added as unique coverage.
- Expanded default gate: **276 passed** (the original 208 plus 68 Glean cases).
- Manual production probe against the fingerprinted retained store: **PASS**.
  This is newly reproduced production-reader execution, not a replay of a past
  experimental success. The existing binaries were fingerprint-verified, not
  rebuilt. P1 unit/file/function tokens were respectively
  `(buck.TranslationUnit.4, 1043)`, `(src.File, 1025)` and
  `(cxx1.FunctionDeclaration, 1035)`; public membership and kind qualified every
  endpoint. File/unit ancestor reads and exact declaration material also passed.
  The equal local unit token in an independent index retained a different
  qualified identity. P1 was unchanged after P2 and all source workspaces were
  already absent. Both valid-evidence and valid-family substitutions were rejected.
- Frontend build: passed with no bundled asset diff. Final wheel/sdist build:
  passed; the wheel imported GleanProgramBackend in an isolated interpreter with
  no checkout/tests/profiles imports. Dependency synchronization, syntax and
  whitespace checks passed.

The first full native-probe attempt stopped at metadata lookup on the native
CLI error `waitForProcess: does not exist (No child processes)`. The production
adapter raised BackendError; it returned no empty result and substituted no DB.
The cause was not established. A subsequent complete invocation against the same
retained store passed without code-level retry or recovery to latest. That is
explicit failure-boundary evidence, not production service-availability proof.

Runtime output remains outside the repository at
`$HOME/.cache/design-phase6b-runtime/phase6c-probe.json`; retained input records,
the modeled independent admission pin and blobs remain in the store above.
No binaries, DBs, credentials or raw run transcripts are committed. Default CI
now executes the modeled production tests, not the external manual runtime probe.
