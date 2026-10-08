# Target Architecture v0 — Phase 6B: retained Glean basis and C++ conformance

Status: experimental composition decision and executable proof, subject to draft
PR review. ProgramBackend and Core Product v1 remain frozen. No production Glean
adapter, publication migration, Code Explorer, SQL projection, semantic discovery,
RAG, registry, provider hierarchy, or repository split is introduced.

Labels: **runtime-proven** means executed on the pinned current build;
**source-backed** means supported by inspected official source;
**composition decision** means a declared contract owned by this application;
**inferred** means a proposed consequence; **untested** means no executable proof.
Offline prototype tests are explicitly labeled as modeled composition evidence,
not current Glean runtime proof.

## A. Merged Phase 6A starting point

**Runtime-proven (repository verification):** fetched remote main and verified
`17ec327e834a15737bd1848c1b5c6e8867b2fd4c`, the merged Phase 6A PR #7 commit.
GitHub reported PR #7 MERGED at `2026-10-07T20:13:23Z`; the working tree was clean.
The four checks were reported before creating
`phase6b/glean-basis-cpp-conformance` at that exact commit. The old Phase 6A branch
was not used as the base. No automatic merge is authorized.

Read the frozen [baseline](CORE_PRODUCT_V1_BASELINE.md),
[completion contract](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md) and
[architecture](ARCHITECTURE.md). This continues the
[Phase 6A study](TARGET_ARCHITECTURE_V0_PHASE6A_GLEAN_CONFORMANCE.md), preserving
`ProgramBackend != Glean` and `ProgramBackend != PublicationBasis`.

## B. Exact current Glean runtime/build

**Source-backed build selection:** use the exact current-source commit reviewed
in Phase 6A, `4e576957778b721f28cec21556066a02c3ed84d0`. Its official CI passed;
the exposed CI artifact is only a VS Code extension, not Glean/clang binaries.
The old June 2024 demo image is excluded from Phase 6B C++ proof.

Build inputs:

| Input | Qualification |
| --- | --- |
| Glean | `4e576957778b721f28cec21556066a02c3ed84d0` |
| hsthrift | `e3c575885f9eda98e3c3aa9a1edd5011b6b14373` |
| Ubuntu container base | `ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55` |
| GHC | 9.4.7 |
| Cabal | 3.10.3.0; official bindist SHA-256 `12d018bdd07efed470f278f22d94b33655c4fcbc44d28d97b5ebb7944d5607c5` |
| Clang/LLVM | 15.0.7 |
| Build | `MODE=dev`, `CXX_MODE=cabal` (upstream C++20), GHC `-O0 -optl-Wl,--no-as-needed -optl-lboost_context -optl/work/hsthrift-installed/lib/libfmt.so`, package-local glean-clang `-pgmcxx /usr/bin/clang++-15 -optcxx-O0 -optcxx-g0 -optcxx-fno-addrsig`, `-f-bundled-folly`, `-f-hack-tests`, one Cabal/build job; locale `C.UTF-8` |
| Hackage index-state | `2025-04-14T00:00:00Z`, the pinned upstream project default |
| Resource bound | Docker two CPUs, 3 GiB memory, no container swap |

**Runtime-proven build:** the pinned CLI and both clang tools completed on
2026-10-08 Europe/London (2026-10-07 UTC). Exported SHA-256 fingerprints:

| Binary | SHA-256 |
| --- | --- |
| glean | `e3a41876326327056120381432cf0287a24a391bdaed29c5ce343462fc2abe63` |
| clang-index | `d3714fd79c46372306bcfdb6a48c518c98505a735a8e3b884cf951f268a71f5f` |
| clang-derive | `e3f3ab7a6fe5fac8fcbd5aec14737b66b6fb8afc78f85d4ede1bc93efbece11d` |

The exporter also records every resolved shared library fingerprint in the
external `runtime.json`; the probe verifies those and the binaries before use.
Clang source/schema inputs have no tracked edits. This is a locally built
artifact with exact source/binary qualification, not the old demo image or a
claim of bit-identical rebuilds from unpinned apt mirrors. Actual stored schema
ID is `66a80a62611346b34e2dcaba40d0d58b`; the schema source revision is the pinned
Glean commit. The canonical runtime-record digest (including resolved libraries)
is `6dfff4f1f88e52cf751ac251d40a91e4edadd2fe4ac965191f26a6f1e50c0581`.

**Source-backed references:** all Glean links below are immutable at the build
commit. [Build documentation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/website/docs/building.md),
[CI recipe](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/.github/workflows/ci.yml),
[compiled build identity](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/github/Glean/BuildInfo.hs),
[DB/query API](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/if/glean.thrift),
[creation/properties](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Create.hs),
[finish/unfinish](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Finish.hs),
[retention/dependency closure](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Retention.hs),
[C++ schema](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/cxx.angle),
[C++ kind](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/codemarkup.cxx.angle),
[translation-unit schema](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/buck.angle),
[clang range/digest/unit production](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/lang/clang/db.cpp),
[index runner](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/lang/clang/Glean/Indexer/Cpp.hs),
[index CLI lifecycle](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/tools/gleancli/GleanCLI/Index.hs).

## C. Chosen exact occurrence qualification

**Composition decision:** exact occurrence identity is a Glean-specific triple:

```text
(logical retained-store namespace, exact Repo(name/hash), expected glean.guid)
```

The namespace identifies the retention authority, not a hostname, query server,
current filesystem location, source repository or content hash. An authenticated
replica/restore within that namespace can serve the same occurrence. An
independent retained store is another namespace even if its imported DB has the
same Repo spelling and GUID. The local prototype uses a namespace marker; the
marker is trusted composition metadata, not a hostile-owner security mechanism.

Field deletion falsifiers:

| Qualification | Substitution possible without it | Ownership |
| --- | --- | --- |
| Namespace | An unrelated store/copy with matching native metadata is accepted as the admitted occurrence | Exact reference/composition |
| Exact Repo | A newest or different index instance is substituted for requested history | Factory/query routing |
| Expected GUID | A deleted Repo key recreated as another DB is accepted | Exact reference/composition |
| Stored schema qualification | Saved predicate/token/query interpretations are checked under the wrong stored representation or query schema | Indexed-basis qualification; not another occurrence identity |
| Input manifest | Arbitrary source revision/path spelling is treated as the exact indexed bytes; missing generated inputs go unnoticed | Source/input qualification |
| Recipe | Equal source bytes analyzed with another configuration/build are treated as the admitted analysis basis | Analysis qualification |
| Required dependency closure | A top DB is retained while base facts/pruned view dependencies are lost or substituted | Retention qualification |
| Retained source bytes | Digests/ranges appear valid but no historical material can reconstruct | Evidence closure |

**Composition decision:** schema/recipe/input/closure are recorded in the durable
basis, not appended to ProgramBackend. The triple establishes identity; the rest
establishes what that identity qualifies and retains. Dependency refs contain the
same exact triple, with each base's native identity checked. In the first admitted
runtime recipe dependencies must be empty: unexpected stacked/pruned indexes
are explicitly refused. The prototype separately models exact dependency closure
checks so a missing base cannot disappear into complete empty reads.

## D. Chosen indexed-input qualification

**Composition decision:** retain an ordered manifest of source identities as
indexed, each with SHA-256 and byte size. Paths are
repository-relative indexed identities; their live filesystem locations are
not reconstruction targets. Retain the compiler/indexer recipe, normalized
argv/path mapping, Glean/clang build identity and declared compilation inputs.
The source-state token is the manifest digest. The opaque observed-index-state
token also includes recipe and stored schema qualification. Neither is the exact
DB occurrence or an assertion of global currency/completeness.
Equal tokens qualify equal admitted indexing inputs/recipe/schema, not a proof
that independently produced fact populations are byte-identical. Exact opened
DB qualification remains separate.

**Composition decision, minimality:** file identity rejects another file's
material; SHA-256 rejects changed/missing retained bytes; size preserves the
native indexed digest/extent qualification and permits explicit size checks.
A per-file source/generated classification was removed from the prototype:
verification needs every admitted input regardless of its Git standing, not a
category label. Git revision and live workspace path are also omitted from
identity. The fixture explicitly produces the generated header and admits its
exact bytes alongside the main source files.

**Composition decision:** the initial capture uses a controlled immutable input
workspace with explicit compilation commands, no standard include directories,
and a generated header. Compare retained bytes before/after indexing and compare
every admitted file's native clang SHA-1/size with the captured bytes. The adapter
must not assume Glean's unspecified generic digest uses SHA-256. SHA-256 qualifies
the retained store; the native digest ties that store to actual indexed files.

**Inferred future rule:** real builds need either an immutable compiler input
closure or captured bytes for every observed input, including generated files,
untracked files, dependencies and indexer transformations. A before/after hash
alone on a mutable workspace cannot exclude transient changes during indexing.
Reject publication scope that cannot honestly establish the indexed-input link;
do not substitute Git checkout identity. No general filesystem monitor or build
capture service is implemented here.

## E. Retained source basis

**Composition decision:** choose exact retained DB occurrence + manifest/recipe
+ content-addressed source byte blobs. Blobs are indexed input material only.
They contain no entity graph, call graph or duplicate Glean facts.

For an observation, retain the selected typed local token, exact basis digest,
indexed file identity, locator dialect/meaning, range and retained blob digest.
Admission verifies entity→file/range association against the exact DB. Independent
material assertions remain necessary: a valid E2 handle can reconstruct valid E2
text while still being dishonest evidence for E1.

**Composition decision:** reconstruction has no workspace fallback. Missing,
corrupt, wrong-size or indirect/symlink blob addresses fail explicitly. The
prototype reconstructs UTF-8 declaration material from retained bytes; malformed
encoding/ranges are explicit failures. Standardize neither opaque handles nor
C++ coordinates into native Program Spine locator fields.

## F. Dependency and accepted-history retention policy

**Composition decision:** while any accepted semantic publication retains this
basis, its DB, required transitive base closure, recipe/schema qualification,
source manifests and source blobs must remain retained. Accepted Repo keys cannot
be reused; accepted DBs cannot be unfinalized/unfinish-ed or mutated. Producers
publish a fresh unique DB instance for new analysis. The store may remove these
artifacts only after all publication retention obligations are released by an
explicit application policy, outside this phase.

**Source-backed:** Glean recognizes Complete/Missing and exact base GUIDs;
retention can delete old versions and computes stacked/pruned dependency closure.
Local unfinish exists for testing, so storage finalization is not the entire
accepted-history contract. Normal property updates are restricted to Incomplete
DBs. Read-only service/storage access and the declared deployment covenant
establish the supported historical boundary; no global retention manager or
malicious-storage-owner sandbox is introduced.

**Composition decision:** initial accepted recipe is standalone only. Extending
it to stacked/pruned DBs requires exact base refs, view/ownership configuration
and full closure retention; merely listing a top DB or supplying some available
base is insufficient. The modeled verifier compares the actual declared closure
with the retained expected closure and checks each exact base GUID/availability.

## G. Restore and explicit unavailability

**Source-backed:** native backup records DB metadata; restore inspects that
metadata and feeds it to catalog restoration. The native mechanism can preserve
Repo/GUID. [Backup implementation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Backup.hs),
[restore implementation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Restore.hs).

**Composition decision:** a restore is the same retained occurrence only when
it comes from the authenticated retained artifact within the same logical
namespace and preserves Repo/GUID, stored schema, admitted recipe/input state
and dependency closure. New physical placement alone does not make it new;
content equality alone does not make it old. An independent reindex or import
under another logical namespace is another occurrence. A renamed/recreated DB
with a new GUID is not an exact restore.

**Untested:** remote S3 backup/restore and physical relocation have not been
executed. Initial proof uses retained local DBs and retained source blobs, with
no backup dependency. Restore remains a source-backed protocol/covenant, not a
runtime claim. Lost/missing/broken/restoring dependencies, denied access and
unavailable exact DBs produce explicit unavailable qualification. No automatic
latest lookup, substitute revision or reindex is accepted as historical recovery.

## H. Future semantic-publication basis record

**Composition decision:** persist one Glean-specific basis record and its digest
inside the semantic publication's construction input record. The record contains:

```text
exact occurrence triple
stored schema qualification
indexed source manifest
compiler/indexer recipe
exact required base references (empty for the admitted standalone recipe)
retained source store addresses/digests
```

The source-store lookup location is a composition resolution detail; content
identity and retention authority must not depend on an original workspace path.
The test prototype separates `open_consistent(candidate)` from
`open_admitted(candidate, admitted_digest)`. Consistency opening checks the
candidate's own derived metadata and confers no accepted-publication admission.
Admission-qualified opening requires an independently retained digest; missing
or mismatched qualification fails. The executable experiment models that trusted
input with a separately saved `trusted-admission.json`, while the candidate
record remains independently replaceable. Neither path proves integration with
Ontology Author's accepted-publication system. Blob-root/store resolution is
separate, and the record serializes/reopens without native PublicationRef or a
program World clone. Metadata hashes in the DB bind the declared recipe/input
record to the producer's exact finished index. Trusted indexing/admission must
check these declarations; setting a property is not proof they are true.

The admission falsifier reformats the serialized recipe without changing its
normalized recipe digest or observed-state token. Its record digest changes.
Consistency opening succeeds, admission opening without a trusted digest fails
with `independent admission digest required`, and opening against the separately
saved original digest fails with `admitted basis record mismatch`. The original
record opens successfully against that same saved digest. This models the
admission trust boundary, not an authority system or publication migration.

**Composition decision:** retain selected evidence handles/material digests as
bounded witnesses where semantic commitments depend on them. They permit exact
source reconstruction during query-service outages and preserve what admission
checked. Do not retain a mandatory second entity/context/call table. Containment
witnesses may be recorded later for a particular commitment's finite verification
need, not as a general graph export or whole-DB absence proof. With the DB
unavailable, evidence material can still reconstruct; current mechanical
membership/context verification is unavailable, not silently certified by the
witness. The original admitted judgment is not rewritten.
**Untested:** witness-only reconstruction during a remote query outage is a
future admission/read mode. This probe rechecks the retained DB on reconstruction;
it proves workspace independence and durable witness round-tripping, not a
production offline-witness service.

**Inferred minimum future admission adaptation:** validate the Glean basis through
its exact factory, check selected typed membership/state/context and associated
evidence used by the semantic candidate, verify requested-family scope/basis,
and check retained closure before sealing. For the admitted successful-input
recipe, independently re-read `src.IndexFailure` and `digest.FileDigest` against
the retained manifest/bytes; DB properties alone are producer declarations.
These checks were also executed from serialized P1 after its workspace was gone.
Keep generic semantic shape, grounding,
origin and standing checks. Replace native-only program basis checks:

- `authority/lifecycle.py`: path-based native opener, full program World clone,
  native PublicationRef/candidate baseline and native snapshot referent plumbing.
- `authority/validation.py`: `program_entity` inventory and `program_snapshot`
  joins for attachments/warrants; construction-boundary program qualifiers;
  native `verify_retained_program_inputs` closure traversal.
- Program observation reconstruction: native receipt/blob locator assumptions
  must give way to Glean-specific evidence verification at composition.

No part of this admission migration or AuthorityConstructor integration is
implemented in Phase 6B. The record carries mechanical input qualification,
not semantic authority, realizes-a-requirement judgment, global analysis
completeness, currentness or a universal provider abstraction.

## I. C++ fixture and index recipe

**Runtime-proven:** `tests/phase6b_glean_cpp_spike.py` executed P1 with two
main-file global functions and one generated header. Target has a distinct
`x + 1` body, CRLF and a Unicode comment. P2 moves target to another file with
`x + 41`, changes the generated header, and adds an extra function. A third
independent index repeats P1 bytes. Explicit compile commands use Clang++ 15,
C++17, `-nostdinc -nostdinc++`, one worker and the pinned native clang-index/
clang-derive binaries. The first target has no namespace/template/macro semantics.
The second file includes a generated header to test retention beyond Git source.
Native `digest.FileDigest` inventory matched exactly the admitted inputs,
including the generated header, with matching clang SHA-1 and byte sizes. No
`src.IndexFailure` or `src.FileContent` rows existed in successful fixtures.
The latter result is bounded to this executed clang recipe; it does not prove
that no Glean indexer stores source bytes. External retained bytes are therefore
the chosen evidence basis.

| P1 indexed file | Bytes | Retained SHA-256 |
| --- | --- | --- |
| generated.h | 37 | `45263c5c33217f203fa5c57c9d4f5424eb682f6ddfa01b469a89137660ed3e9a` |
| second.cpp | 74 | `1f3f47feb099a0ed7b8258acf58cceca60f1ea7d20c9b3a9c5bffbe9059a3016` |
| target.cpp | 54 | `6188e631c0b480016bf2290ff91188fbc91ffb8e4e178b6a313c73773bdeb226` |

The actual DB property `glean.server.build_revision` matched the complete
40-character pinned commit. The recipe records the tools/configuration, source
range dialect and normalized compilation path mapping, not merely source text.

## J. Entity identity and selected membership

**Runtime-proven:** used typed selected FunctionDeclaration lookup;
public local tokens are opaque hashable `(predicate, local_fact_id)` tuples.
Qualified identity pairs the opened exact occurrence/state with that token.
Dispatch admits only FunctionDeclaration, src.File and buck.TranslationUnit.4.
Unknown/wrong-type lookup is distinguished from DB/query/schema/transport failure.
No entity-universe enumeration is needed. Foreign qualified entities are rejected
even when an integer is meaningful in another DB. Numeric collision is not a
reason to require global entity IDs.

The public `member` and `kind` helpers consume the actual endpoint tokens returned
by context, with these independently checked results:

| Returned P1 token | member | kind |
| --- | --- | --- |
| Translation-unit token (`buck.TranslationUnit.4`) | True | translation_unit |
| File token (`src.File`) | True | source_unit |
| Function token (`cxx1.FunctionDeclaration`) | True | callable |
| Unknown, wrongly typed or unadmitted category | False | None |

The containment rows preserve precisely these same tokens in parent/child roles.
Unit/file membership and kind do not require declaration observations: this
bounded recipe returns no observations for those members. A function-only
membership or kind implementation fails the shared endpoint-closure assertions;
reversing roles or dropping an endpoint's type also fails. Those dishonest reader
substitutions are offline modeled controls, distinct from the real typed runtime
queries and endpoint checks. No universal entity class or all-fact admission is
introduced.

In the initial run the selected target's local fact ID was `1035` in both
independently indexed P1 DBs, and P2 target was `1055`. Fact allocation is not
assumed deterministic: the closure probe requires and records an equal typed
local token from the actual returned E1/E2 endpoint chains. These are selected
fixture reads, not entity-universe enumeration. Direct typed lookup
succeeds in both DBs, while occurrence-qualified substitution fails with
`entity occurrence mismatch`. A nonexistent ID
returned nonmembership; the valid file ID `1025` did not pass as a function.
The experiment distinguishes the specific wrong-fact-type outcome from
schema/query/DB failures, which remain explicit errors.

Representative keyed lookup (predicate identity is adapter-private):

```angle
D where D = ($1035 : cxx1.FunctionDeclaration);
  D = cxx1.FunctionDeclaration _
```

## K. Adequate mechanical kind

**Runtime-proven:** queried actual `cxx1.FunctionDeclaration` and
`codemarkup.cxx.CxxDeclKind` for the selected ID. `Function` can be narrowly
normalized to callable. No source-text or pretty-type inference is allowed.
For E=`1035`, `codemarkup.cxx.CxxDeclKind { decl = { function_ = $1035 } }`
returned the same selected declaration and SymbolKind ordinal `13` (`Function`).
`cxx1.FunctionDefinition { declaration = $1035 }` independently linked its
definition to that declaration. Source-unit/outer categories come from actual
`src.File` and `buck.TranslationUnit.4` predicate typing.

## L. Source-unit and bounded outer context

**Runtime-proven:** obtained the selected declaration's source
file from `DeclarationSrcRange`, membership in its `Trace` via
`DeclarationInTrace`, and actual translation unit via `TranslationUnitTrace`.
Validate all shared file identities, then expose compilation-unit → source-file
→ selected-function ownership. The categories are translation_unit/source_unit/
callable, not invented namespace→file or repository→module edges. Header
participation, multi-target builds and lexical scope remain separate relations.

Actual bounded chain in the passing run:

```text
buck.TranslationUnit.4(1043)
    → src.File(1025, "target.cpp")
    → cxx1.FunctionDeclaration(1035)
```

`DeclarationSrcRange` gave file `1025`; `DeclarationInTrace` selected the trace;
`TranslationUnitTrace` returned the unit whose file and trace file both matched
`1025`. Direct typed unit/file lookups succeeded. The two exported edges retain
parent/child direction and typed endpoint identity under P1. They express
compilation/file ownership, not C++ lexical namespace ancestry. Returning E2's
otherwise valid context failed the independently expected E1 context assertion.

**Inferred consumer assessment:** Phase 4's structural ancestor walk uses
parent/child roles; a mechanically backed compilation/file ownership chain can
provide that context with language-specific outer category. Literal native
`module` test spelling is not a universal requirement. Full native lifecycle/
consumer migration is separate, and must not be claimed from this reader probe.
The actual ancestor walk in `authority/construction.py::structural_context`
uses the parent/child roles; it does not require an outer node literally called
module. No independent contract falsifier is demonstrated.

## M. Evidence and exact reconstruction

**Runtime-proven:** full declaration manifestation came from
`DeclarationSrcRange` of the supplied function definition; separately inspect
`DeclarationNameSpan` and do not substitute it for body evidence. Current clang's
range implementation uses SourceManager byte columns and inclusive end position,
whereas generic src.Range documentation specifies code-point columns. The
recipe/opaque handle preserves the actual C++ dialect. These fixture ranges are
reconstructed over exact retained bytes, without newline normalization.

E1 range was `(lineBegin=1,columnBegin=14,lineEnd=3,columnEnd=1)`, inclusive
clang byte columns. The Unicode comment establishes why treating column 14 as
a code-point count would select the wrong material. Verified E1 reconstruction
was exactly `int target(int x) {\r\n  return x + 1;\r\n}`. The independently
expected E2 manifestation was `int second(int x) { return x + generated_offset; }`.
E2's valid evidence reconstructed E2 and failed E1's material discriminator.
The name span separately selected exactly six bytes `target` in the same file;
it was not used as full declaration evidence.

After altering the live target to return `-999`, then deleting all three
original workspaces, E1 still reconstructed unchanged. The serialized basis and
selected witness reopened and reconstructed to its saved material SHA-256
`85628ae15a12e07c192c3660f9b2860d3364477b342aa0f4b716ffb0d56b86a1`.
Wrong source qualification, corrupt blob and missing blob all failed, including
when a newly created live checkout contained the correct original bytes. A
modeled symlink-to-live-source control also fails; no fallback is permitted.

## N. P1/P2 and equivalent-index history

**Runtime-proven:** reopened/queried P1 after P2 and the equal-input
independent index exist. Verify state, membership, typed kind, context,
associated observations and reconstructed material remain P1-local. Equal
indexed bytes/state do not imply equal Repo/GUID occurrence qualification.

All refs below share retained namespace
`phase6b-retained-332d7207f3b94de08eb08b491d03da34` and the stored schema above:

| Exact Repo | Expected GUID | Result |
| --- | --- | --- |
| phase6b/P1 | `a079e714-77df-4d17-baf5-34774554a16b` | Original target/file/context/material retained after P2 |
| phase6b/P1independent | `8d349e66-7355-4680-9e81-7940ef0dccf4` | Independently indexed P1 bytes, same input/observed-state tokens, distinct occurrence |
| phase6b/P2 | `92c7e6ec-2a3c-48e4-916f-8a28428da5bf` | Target moved to moved.cpp, body +41, new extra function |
| phase6b/P1independent (recreated unpublished control) | `baa0c7e2-0111-440c-bfed-3689da77133a` | Same Repo/input bytes, new GUID; old ref refused |

P1 input token was `0aa90d63ffcfc015f4212e6c9c918bc7de0567de8eb55fbbad9ea0a8376cd45c`;
P2 was `3e44d1db1440e69c76710809eeb8e26905cb44df83fabce028b0dd5e732309d9`.
P1's observed token remained
`fcf8377e020dcfc9744dd051c94a2f01ab551e82e8e79b4b2e21cbc878b23cb3`.
No `extra` declaration appeared in the selected P1 query. Passing P2's entirely
valid basis against admitted P1's record digest failed. Deleting the unpublished
independent DB produced explicit historical unavailability while P2 existed;
recreating its Repo with new GUID did not repair the old reference.

## O. Conservative per-family capability policy

**Composition decision:** useful facts do not imply analysis completeness.

| Family | Initial policy | Qualification/gaps |
| --- | --- | --- |
| kind | INCOMPLETE | Typed global functions in declared compilation inputs; other AST categories not normalized |
| containment/context | INCOMPLETE | Main-file unit/file/function ownership; headers/multiple units/lexical scopes are not one tree |
| evidence/reconstruction | INCOMPLETE | Selected declaration ranges and retained indexed UTF-8 bytes; other locator/encoding forms unproven |
| invocation | NOT_PRODUCED | Xrefs are not syntactic call proof |
| resolution | NOT_PRODUCED | Call-resolution outcomes not produced by this initial recipe |

Recipe/schema and requested family qualify every returned policy record. The
indexer status, declared compilation inputs, native file digests and recorded
failures support this bounded basis. DB Complete, empty IndexFailure queries,
empty result sets and predicate availability never independently license
complete absence. Explicit family production is separate from storage lifecycle.

## P. Dishonest mapping and composition falsifiers

**Runtime-proven and modeled composition evidence:** current C++ probe passed;
28 offline prototype cases pass (14 original basis cases plus 14 closure cases).
Evidence levels below distinguish
native execution from modeled stacked/pruned closure checks.

| Substitution/failure | Required rejecting discriminator | Evidence level |
| --- | --- | --- |
| Same source, wrong GUID/recreated Repo | Compare expected GUID with exact DB | Runtime-proven, including actual delete/recreate |
| Correct native spelling, wrong store | Compare logical retained namespace | Runtime-proven composition marker rejection; independent remote service authentication untested |
| Latest for missing historical DB | Exact Repo lookup fails even if latest exists | Runtime-proven; valid P2 basis also rejected against admitted P1 digest |
| Missing stacked/pruned base | Compare/verify complete required closure and each base GUID | Modeled; native stacked/pruned runtime untested |
| Wrong stored schema | Compare stored qualification before interpreting facts | Runtime-proven record mismatch; modeled wrong DB schema metadata |
| Wrong input manifest/recipe | Admitted record digest and DB-bound input/recipe digests | Runtime-proven record/DB qualification; modeled altered DB metadata |
| Foreign entity treated as local | Qualify typed local token with exact occurrence/state | Runtime-proven, including actual numeric ID collision |
| Function-only membership/kind with typed parent endpoints | Check every actual returned endpoint through the public helpers | Runtime endpoint closure; modeled dishonest dispatch rejection |
| Self-consistency promoted to independent admission | Require separately retained original record digest | Runtime metadata checks with modeled trusted admission; missing/mismatched pin rejected |
| Wrong ancestor | Selected declaration/trace/file/unit joins and independent expected E1 context | Runtime-proven |
| Valid E2 evidence for E1 | Independent expected full E1 manifestation rejects E2 material | Runtime-proven |
| Wrong source revision/content | Basis/file/locator qualification plus retained and indexed digest checks | Runtime-proven |
| Missing generated input | Manifest/blob closure includes generated header | Runtime-proven capture/inventory; modeled missing-generated-blob rejection |
| Live checkout substitution | No live fallback; missing/corrupt/indirect retained blob fails | Runtime-proven workspace deletion/missing/corrupt/live file; modeled symlink rejection |
| Another family's valid capability | Independent requested-family full policy assertion | Runtime-proven for all five families |
| Unsupported calls treated complete-empty | NOT_PRODUCED optional families | Runtime-proven policy and empty optional reads, not native call extraction |
| Wrong-site call or unresolved treated resolved | Decline production; make no xref→call/unique-result mapping | Optional NOT_PRODUCED; produced call/resolution discriminator untested |

## Q. Reader versus publication-basis decision matrix

Statuses are restricted to the requested Phase 6B vocabulary. The current
reader rows below were actually executed; source-only broader mappings receive
no straightforward-adapter classification.

| Core behavior | Reader mechanism | Composition obligation | Current classification |
| --- | --- | --- | --- |
| Exact occurrence open | Exact DB lookup | Namespace/Repo/GUID and retained availability | COMPOSITION_PROVEN (current runtime plus exact-store covenant) |
| Observed-state token | Stable qualified indexed state | Input/recipe/schema record, separate from occurrence | COMPOSITION_PROVEN (current indexed inputs and historical read) |
| Membership | Keyed typed fact lookup | Exact occurrence-qualified token | CURRENT_CPP_RUNTIME_PROVEN |
| Adequate kind | FunctionDeclaration/CxxDeclKind plus typed file/unit dispatch | Language-specific normalization | CURRENT_CPP_RUNTIME_PROVEN |
| Scoped context | Declaration/trace/file/unit joins | Explicit ownership scope, no invented lexical tree | CURRENT_CPP_RUNTIME_PROVEN |
| Entity evidence | Selected declaration range | Retained indexed source association | CURRENT_CPP_RUNTIME_PROVEN |
| Historical reconstruction | Retained bytes; no native FileContent rows in this recipe | Source manifest/digest/extent verification | COMPOSITION_PROVEN (current DB association plus retained bytes after workspace deletion) |
| Per-family qualification | Conservative family policy | Recipe/producer-bound scope and gaps | COMPOSITION_PROVEN (executed policy/association controls) |
| Optional invocations/resolutions | No call extraction | NOT_PRODUCED, no absence inference | OPTIONAL_NOT_PRODUCED |
| Verification | Exact DB plus selected evidence/qualification checks | Retained closure and explicit failure | COMPOSITION_PROVEN (standalone runtime; dependency closure modeled) |
| Packaging the executed scoped reads behind the frozen interface | Typed token encoding, row roles, opaque observations, return/error normalization | Exact opener supplies admitted basis | THIN_ADAPTER_STRAIGHTFORWARD (execution demonstrated; production integration not implemented) |

**Runtime-proven reader answer: YES, for the selected current C++ core.** Kind,
selected membership, bounded context and entity-associated source location come
from actual typed facts. Optional families honestly decline production.

**Composition decision exercised against current runtime: publication-basis
answer YES, for the admitted standalone retained-store recipe.** An exact
Glean-specific record plus retained input bytes can survive workspace loss and
verify independently without a full program World clone or second graph.
Accepted-history availability still depends on the explicit retention covenant;
violation causes exact failure, never latest substitution. Existing native
publication is not thereby migrated. Native stacked/pruned and restore support
remain outside the admitted first recipe, with UNCLEAR runtime conformance.

## R. Failures and remaining unsupported/untested behavior

**Runtime-observed build failures:** base image had no CA bundle, preventing
HTTPS apt metadata verification; provisioned trusted certificates. Distribution
Cabal 3.8.1.0 failed Hackage root-key verification; switched to the checksum-pinned
official 3.10.3.0 binary. No Glean contract failure follows from either bootstrap
problem. Build/query/indexer failures below remain explicit.

**Runtime-observed build fixes:** the container's default locale rejected a
Unicode comment in an upstream Thrift file; `C.UTF-8` fixed schema generation.
The make-based dev path selected C++17, incompatible with current Folly headers;
an explicit C++20 compiler flag matches Glean's current Cabal C++ configuration.
Neither fix changes Glean/clang-index source or the ProgramBackend contract.

**Runtime-observed build fix:** GCC's sequence-point diagnostic in the RTS
syscall argument pack was promoted to an error by the make dev path. The source
uses braced tuple initialization and documents its sequencing guarantee. The
first experimental retry kept this diagnostic as a warning; a subsequent signed/
unsigned comparison warning in `ffi.cpp` was also promoted to error. The final
make-library override reports `-Wall` warnings without promotion to errors,
matching the upstream Cabal C++ configuration's lack of that make-path `-Werror`
gate. The upstream local Haskell `-Werror` settings remain unchanged. These flags
and failures are recorded; no source edits or reader-requirement changes result.

**Runtime-observed build failure:** the make-library path lacked the bundled
LMDB include directory; adding the pinned header path passed compilation. Its
schema-generator link then had unresolved bundled LMDB and Boost.Context symbols.
The final build uses upstream Cabal C++ library compilation/LMDB dependency
handling, plus an explicit Boost.Context linker flag. The make-path retries are
failure evidence, not the final artifact's compiler configuration.

**Runtime-observed build failure:** installed Folly/fmt headers reference fmt
12.1.0 while the link searched the system fmt library first, leaving unresolved
`fmt::v12` symbols. The recorded link flag names the installed matching fmt
library explicitly. Final runtime fingerprinting includes executable and shared
library hashes, rather than recording only a mutable image tag.

**Runtime-observed resource failures:** GCC compiling the clang indexer's large
`index.cpp` exceeded the 3 GiB container limit (Docker recorded OOMKilled). A
retry with native optimization/debug info disabled still approached that limit.
Switching this package's C++ compiler to Clang++ 15 retained the upstream C++20
source contract. Cabal's concurrent package-planning heap still used about
1.5 GiB; a 768 MiB Cabal heap cap failed during configuration. The final recipe
separates `cabal build --only-configure glean-clang` from the generated Setup
builder's compilation, so that heap exits before Clang starts. These are build
failures, not evidence of DB availability or family completeness.

**Runtime-observed toolchain failure:** Clang emitted `.addrsig` assembly
directives that GHC's selected GNU assembler rejected. Package-local
`-fno-addrsig` disables that optional address-significance table; it does not
change indexed C++ categories or the input recipe. The final flags record it.
The resulting GNU assembler also warned about Clang's optional
`.linker-options` section type; object generation and final linking succeeded.
GHC rendered those assembler warnings with an `error:` prefix, but the build
exit status was successful. They are retained as toolchain-warning evidence.

**Runtime-observed query failure:** the proposed unversioned
`buck.TranslationUnit` direct type lookup was not in default query scope.
`buck.TranslationUnit.4`, imported by current `cxx1.5`, successfully resolved
the already selected unit. The experimental mapping pins that actual predicate
version. The initial query failure was explicit, not normalized to nonmembership
or complete absence; other query/schema/transport errors retain that behavior.

**Runtime-observed availability interruption:** the completed query container
was stopped when an additional independent P1 verification began. The exact
opener reported historical DB unavailable. Restarting the completed container
without rebuilding/querying latest allowed the same serialized P1 basis, native
input digests and selected material to verify with its workspace absent. The
stop cause was not established; this is query-runtime restart evidence, not
native backup/restore or production retention-enforcement proof.

**Runtime-proven indexer failure:** a source file including missing
`absent_generated.h` produced `src.IndexFailure` (reason ordinal `0`, details
reporting one indexing error and header not found). The DB nevertheless had
status `COMPLETE`. The initial successful-input recipe refused this fixture.
This failure affects analysis/family scope, not necessarily DB availability.
Selected evidence from a failed input is not admitted as success merely because
some declaration facts exist. Missing compile commands/generated input closure
are explicit recipe/admission failures, not complete-empty conclusions.

**Runtime inventory:** successful fixtures indexed every declared file without
IndexFailure; no query timeout/truncation was observed. CLI query pagination
exhausts continuations with no explicit result limit in this probe. No broad
claim follows about repositories with omitted build targets, missing dependencies,
unsupported AST forms or other query/service configurations.

**Untested:** broad C++/all build systems; macros/templates/dynamic dispatch;
headers participating in multiple translation units; lexical namespace ancestry;
invalid source encodings; current stacked/pruned indexing and backups/restores;
production service outages/GC enforcement; actual Ontology Author Glean admission.
Calls/resolution are explicitly outside the initial produced scope.

## S. Native clone deletion implications

**Inferred:** once future admission validates exact Glean basis plus bounded
selected evidence, semantic publication need not clone a full native program
World. Native extraction/projection/capture remains compatibility until that
migration is proven; source bytes/recipe/retention obligations remain above
Glean. Do not replace the clone with a second exported full entity/call graph.
No native code, accepted history, fixtures or research is deleted here.

## T. Production-adapter requirements now forced

**Composition decision:** a future Phase 6C reader must bind every operation to
one exact opened DB/schema, qualify local typed tokens, perform selected queries,
normalize only proven mechanical categories, retain genuine context roles,
associate evidence with E, reconstruct retained qualified bytes, preserve the
per-family policy and optional NOT_PRODUCED behavior, and expose explicit errors.
The Glean-specific exact opener composes the retained basis; no retention fields
are added to ProgramBackend. Publication migration remains a separately bounded
application change, not an implicit backend registry or kernel extension.

**Composition decision:** Phase 6C may implement the thin production reader for
this admitted standalone C++ basis, after review of this draft. It must initially
refuse other recipes/dependency forms or explicitly qualify them as unsupported;
the successful fixture does not license a universal C++ adapter. Pin predicate
versions/query-schema interpretation and reproduce the selected evidence/history
and family-association controls in production-facing tests. Retention covenant
deployment and future admission adaptation remain application composition work;
do not smuggle them into the frozen reader interface.

## U. Final verdict and validation

**Runtime-proven + composition decision:**

```text
YES — GLEAN RETAINED BASIS DECIDED AND CURRENT C++ CORE
CONFORMANCE PROVEN; READY FOR PRODUCTION GLEAN ADAPTER
```

Should the next phase implement `GleanProgramBackend` in production? **YES**,
for the admitted standalone C++ core and conservative family policy above.
Phase 6B implements no production adapter. No independent executable evidence
falsifies ProgramBackend, and no frozen interface/core/Phase 5 test is changed.
Stacked/pruned inputs, backup restore, broader C++ coverage and publication
migration require separate evidence before expanding this bounded scope.

**Initial runtime-proven validation record (2026-10-07 UTC / 2026-10-08 London):**

- `uv sync --locked --extra dev`: passed.
- `npm ci --prefix frontend`: passed; reported five existing audit findings;
  no dependency changes.
- Core acceptance plus new modeled basis tests: **32 passed** (18 + 14).
- Default frozen repository pytest gate: **208 passed**; overlaps core acceptance.
- Targeted modeled basis suite: **14 passed**. It is explicitly invoked because
  the default gate lists its test modules and excludes this new manual study.
- Current-source C++ spike: **PASS**, including actual independent indexing,
  P1/P2, Repo delete/recreation, workspace deletion, source corruption/missing
  source, typed membership/kind/context and both association discriminators.
- Python compilation, shell syntax and whitespace validation: passed.

The successful runtime store is outside the repository at
`$HOME/.cache/design-phase6b-runtime/spike/cede868cc93f41018f9e5c0ff743841d`.
It retains exact DBs, GUID-named basis records, source blobs and the selected
evidence witness for inspection. Logs, raw run output, generated DBs and tool
artifacts are not committed. Counts above distinguish modeled tests from the
current Glean execution and do not add overlapping suites as unique coverage.

### Reproduction (experimental container, not a host installation)

Build/runtime artifacts stay outside this repository. Create an empty task cache
and obtain the pinned public sources and tool bindist:

```sh
phase6b_work="$HOME/.cache/design-phase6b-runtime"
mkdir -p "$phase6b_work"
git clone https://github.com/facebookincubator/Glean.git "$phase6b_work/Glean"
git -C "$phase6b_work/Glean" checkout 4e576957778b721f28cec21556066a02c3ed84d0
git clone https://github.com/facebookincubator/hsthrift.git "$phase6b_work/Glean/hsthrift"
git -C "$phase6b_work/Glean/hsthrift" checkout e3c575885f9eda98e3c3aa9a1edd5011b6b14373
curl --fail --location https://downloads.haskell.org/~cabal/cabal-install-3.10.3.0/cabal-install-3.10.3.0-x86_64-linux-deb11.tar.xz --output "$phase6b_work/cabal-3.10.3.0.tar.xz"
cp /etc/ssl/certs/ca-certificates.crt "$phase6b_work/bootstrap-ca.crt"
cp tests/phase6b_build_glean.sh "$phase6b_work/build.sh"
docker run -d --name design-phase6b-build --cpus 2 --memory 3g --memory-swap 3g --entrypoint /bin/bash -v "$phase6b_work:/work" ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55 -c 'bash /work/build.sh > /work/build.log 2>&1'
```

The CA file is the host's public trust bundle, not credentials. The builder
checks source and Cabal pins before compiling; `BUILD_SUCCESS` denotes completed
build only. Inspect `build.log` until completion; bootstrap warnings/failures
must not be reported as conformance. After completion:

```sh
uv run python -m tests.phase6b_export_runtime --work "$phase6b_work"
uv run python -m tests.phase6b_glean_cpp_spike --work "$phase6b_work"
uv run --extra dev pytest -q tests/test_phase6b_glean_basis.py
```

The exporter fingerprints all three binaries and resolved shared libraries; the
probe verifies these before querying. Fresh probe runs use independent retained
namespace/store directories, preserve the basis records and bounded witness,
and deliberately destroy only their unpublished fixtures. Source cloning,
dependency downloads and building are not part of the default pytest gate.

## V. Final review closure (2026-10-08)

**Newly executed on the existing fingerprinted runtime:** the complete updated
C++ probe passed, including both closure controls and all earlier historical,
input/evidence, capability and failure controls. The binaries were not rebuilt.
Stored schema remains `66a80a62611346b34e2dcaba40d0d58b`.

The successful closure store is
`$HOME/.cache/design-phase6b-runtime/spike/deedaf9cd15c4e128aab182fb8168495`,
under namespace `phase6b-retained-e6b5f0ff0092479da19c245b854d8291`:

| Repo | GUID |
| --- | --- |
| phase6b/P1 | `86706e6f-96e9-45ff-b067-7d1810644441` |
| phase6b/P1independent | `5a664ed2-3863-4449-9e0c-ce3c9c668069` |
| phase6b/P2 | `35cf3507-08d7-4267-8756-c8b33c84579f` |
| phase6b/P1independent (recreated unpublished control) | `90066cc6-1e67-41e1-871c-e01d763fbf72` |

P1's actual returned tokens were `(buck.TranslationUnit.4, 1043)`,
`(src.File, 1025)` and `(cxx1.FunctionDeclaration, 1035)`. Public membership
returned True for all three, and kinds were translation_unit/source_unit/callable.
The exact parent/child token rows and these results survived workspace deletion.
The independent index had the same local translation-unit token but a different
qualified occurrence; cross-occurrence substitution failed.

The separately retained modeled admission digest was
`d875306562c857685e9ccf8277d3daa8d23d8c429516230985c40061b79a45de`.
The reformatted candidate passed consistency checks while missing and mismatched
admission pins failed; original P1 opened against that saved pin. This is a model
of independent admission, not accepted-publication integration. The missing-header
control again recorded COMPLETE plus `src.IndexFailure` for absent_generated.h.

An earlier closure attempt incorrectly required identical selected-function IDs
across independent indexing. Actual fact allocation differed and that assertion
failed. The final discriminator requires an actual equal typed endpoint from the
bounded E1/E2 context chains, without assuming deterministic function IDs or
enumerating the repository. The successful run above is a subsequent execution.

**Closure validation:** 28 experimental tests passed (14 original + 14 closure);
core acceptance passed 18; the unchanged default gate passed 208 (overlapping
core coverage). Python compilation, shell syntax and `git diff --check` passed.
The manual Glean probe and experimental suite remain outside default CI.
Production contracts, native implementation and publication remain unchanged;
Phase 6C is not implemented and the PR remains a draft, unmerged.
