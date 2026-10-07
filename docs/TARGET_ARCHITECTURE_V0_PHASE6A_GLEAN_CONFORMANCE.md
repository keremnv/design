# Target Architecture v0 — Phase 6A: Glean capability and conformance study

Status: source-backed study plus a real, deliberately partial executable probe.
Phase 5B and Core Product v1 remain frozen. No production interface, semantic
alignment, RAG, Code Explorer, registry, or publication architecture is changed.
Glean is a possible implementation of ProgramBackend, not its definition.

## A. Exact merged starting point

This branch starts at merged `main`
`b1bbbf8a1e54fdd900bfe9ff245dcdb2bab33671`, Phase 5B PR #6. The previous local
checkout was clean; remote main was fetched and its commit verified before
creating `phase6a/glean-conformance-study` at that exact commit.

Read in order: [Core baseline](CORE_PRODUCT_V1_BASELINE.md),
[completion contract](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md),
[architecture](ARCHITECTURE.md). The independent hypothesis is
[Phase 5A R1–R7](TARGET_ARCHITECTURE_V0_PHASE5A_PROGRAM_BACKEND_REQUIREMENTS.md)
and [Phase 5B's corrected surface and associations](TARGET_ARCHITECTURE_V0_PHASE5B_PROGRAM_BACKEND_EXTRACTION.md).
Native representation is evidence of demonstrated behavior, not a schema that
Glean must imitate. `OccurrenceIdentity != ContentEquivalence` and
`EntityToken != QualifiedEntityOccurrence` remain load-bearing.

## B. Versions, sources, and evidence labels

Study performed 2026-10-07. Current official repository HEAD was fetched and
pinned to **`4e576957778b721f28cec21556066a02c3ed84d0`**, commit title
“Angle compiler cleanups (#707)”, commit timestamp `2026-10-07T09:07:42-07:00`.
All S-links below refer to that immutable commit, including documentation
source. The public documentation site was consulted, but has no displayed
build revision; where it differs, pinned source wins. For example, the C++
indexer page still mentions older Clang versions and installation restrictions;
current CI/build instructions are the stronger installation evidence.

Evidence labels throughout:

- **Documented:** an official documentation claim, pinned when available.
- **Source-inspected:** actual implementation/schema behavior read at the pinned
  commit. This is observed implementation structure, not an executed result.
- **Runtime-observed:** real Glean/Flow results from the pinned image below.
- **Inferred:** proposed adapter/composition behavior derived from that evidence.
- **Untested/open:** no executable proof or adequate source evidence yet.

A separately pinned executable environment was available:

```text
ghcr.io/facebookincubator/glean/demo@sha256:
  eec9d45a51f7c0bcc8d2260b3e519cd633034851b84cda0bf9d0f91bc8ba6a10
image created: 2024-06-10T02:37:31.73158604Z
Flow: 0.219.0
stored schema ID: ac4458f8637ec8fe73187e04b8ad1df1
glean.server.build_revision: <unknown>
```

The image's exact digest is known; its Glean build commit is **unknown**. A
`glean --version` attempt did not provide one. It is not the 2026 source build.
Its shipped schema also lacks `src.FileContent`, which exists in current source.
Runtime claims must not be extrapolated to the pinned current binary. Docker
29.4.1 was available; Glean, GHC/Cabal and Stack were not installed on the host.
Building current Glean and clang-index would require the Haskell environment,
hsthrift and C++ dependencies; this study used the official executable image
instead of making that large environment change. Current C++ execution is
**deferred**, not reported as an installation failure or successful conformance.
See [official build instructions](https://glean.software/docs/building/) and [S18].

Pinned primary sources (each link includes its revision):

- [S01 — database documentation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/website/docs/databases.md)
- [S02 — Thrift DB/query/schema/lifecycle API](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/if/glean.thrift)
- [S03 — DB creation, GUID and stacked creation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Create.hs)
- [S04 — actual scoped query implementation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Query/UserQuery.hs)
- [S05 — retention policy and dependency closure](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Retention.hs)
- [S06 — finish/unfinish implementation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Finish.hs)
- [S07 — source schema, ranges, content, failures](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/src.angle)
- [S08 — C++ declarations, scope, xref targets, ranges](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/cxx.angle)
- [S09 — C++ code entity union and declaration/definition mapping](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/code.cxx.angle)
- [S10 — C++ kind and containment implementations](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/codemarkup.cxx.angle)
- [S11 — Flow schema and selected declaration locations](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/flow.angle)
- [S12 — Flow kind/parent/evidence mapping](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/codemarkup.flow.angle)
- [S13 — generic location/kind/parent/call dispatch](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/codemarkup.angle)
- [S14 — clang file digest and line production](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/lang/clang/db.cpp)
- [S15 — clang expression/xref production](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/lang/clang/ast.cpp)
- [S16 — Hack calls, target sets and dynamic occurrences](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/hack.angle)
- [S17 — Python calls and declarations](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/python.angle)
- [S18 — current build documentation](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/website/docs/building.md)
- [S19 — query documentation and client convenience behavior](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/website/docs/query/intro.md)
- [S20 — Angle key-prefix query behavior](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/website/docs/angle/efficiency.md)
- [S21 — stored/on-demand derived predicates](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/website/docs/derived.md)
- [S22 — HIE source-content production](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/lang/haskell/HieIndexer/Index.hs)
- [S23 — HIE source storage option](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/lang/haskell/HieIndexer/Options.hs)
- [S24 — indexer configuration predicate](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/indexer.angle)
- [S25 — fact ID starting boundary](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/rts/id.h)
- [S26 — digest schema](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/digest.angle)
- [S27 — catalog dependency GUID checks](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/db/Glean/Database/Catalog.hs)
- [S28 — actual translation-unit identity schema](https://github.com/facebookincubator/Glean/blob/4e576957778b721f28cec21556066a02c3ed84d0/glean/schema/source/buck.angle)

## C. Relevant architecture

**Documented/source-inspected:** Glean stores typed facts in DBs. Fact keys are
unique within their predicate; key/value predicates enforce one value for a key.
Schemas are stored with DBs. Angle matches/join queries over those facts; stored
and on-demand derivations differ. Thrift provides explicit `Repo` arguments for
`getDatabase`, `getSchemaInfo`, `userQueryFacts` and `userQuery` [S02, S04, S21].
The documented open-source client is Haskell; the raw wire API and the CLI make
this study possible without pretending there is an official Python client
[S19]. API auth/error qualification must also be checked in a future adapter.

Facts need not first be copied into a native Program World. Reader operations
can query the selected Glean DB directly. Typed predicates, tagged entity
unions, and location relations establish mechanical behavior. They do not
establish semantic standing or requirement satisfaction.

**Inferred:** a scoped adapter is natural for languages with adequate typed
entities and parent/source relations. DB retention, source retention and
publication admission are separate composition obligations. No query result,
count, predicate spelling or successful DB finalization certifies all program
analysis.

## D. Exact occurrence and observed-state semantics

**Documented:** DB identity is `(name, hash)` in a selected service/storage
namespace. `hash` is an arbitrary instance string; treating it as a Git commit
is a convention, not enforced source identity [S01, S02].

**Source-inspected:** creation generates `glean.guid`, records
`glean.schema_id`, and detects an existing catalog entry rather than blindly
creating over it. Creation code explicitly recognizes that recreating deleted
keys is possible and undesirable [S03]. Catalog dependency checks compare
expected base GUIDs [S27]. Therefore a bare name/hash is insufficient protection
against deleted-key reuse. A source revision and DB instance must remain distinct.

**Runtime-observed:** `phase6a/P1`, `phase6a/P2`, and `phase6a/P1equivalent` coexist.
P1equivalent ingests exactly P1's Flow facts, retains the same controlled
source-state digest and local IDs, but has another name/hash and GUID. Equivalent
content does not collapse independently created index instances. Opening a
missing DB fails; queries never use the name-only latest helper.

**Inferred:** choose unique instance hashes even for repeat indexing of one
source revision. Pin the namespace, Repo, expected GUID, stored schema and a
recorded input/index recipe qualification. Every call, continuation and nested
fact must use that same DB. Do not invoke `db-latest`, name-only query options,
or clients that select latest as a convenience [S19]. Check exact DB metadata
at opening; unavailable/GC'd history is explicit failure or exact restore,
never substitution.

`snapshot()` can be a stable opaque string encoding the qualified indexed
state: GUID plus stored schema and a retained input/config manifest. It need
not equal a source Git SHA or content digest. The executable probe deliberately
uses a controlled source-manifest SHA-256 as state and a distinct GUID as
occurrence qualification; this illustrates that the two need not be the same.
The scope is the **observed indexed input**, not every file in an external repo.

Historical support classification: **ADAPTER-COMPOSABLE**. Explicit exact reads
are native; independent occurrence qualification and retention are composition.
There is no evidence of a need to reproduce `PublicationRef`.

## E. Entity identity and local membership

**Source-inspected:** facts have numeric IDs; standalone allocation begins at
1024 [S25]. `code.Entity`/`code.cxx.Entity` are tagged sum types, not a promise of
one globally stable entity ID [S09, S13]. C++ USRs are separate symbol information,
not a replacement for occurrence-qualified fact identity. Stacked DBs expose
base facts; membership is in the opened DB's visible view, not just its top-layer
storage. Pruned ownership must be honored [S02, S03, S04].

`userQueryFacts(Repo, [FactQuery])` looks up selected IDs through that DB's lookup
and schema. Its positional results/error behavior must be decoded, including
missing-fact sentinel behavior, predicate type, schema and authorization. Do
not treat any well-formed integer or predicate name as a local entity. No
repository-wide enumeration is required [S02, S04].

**Runtime-observed:** selected typed Angle lookups work. Unknown/wrong-type IDs
can cause `fact has the wrong type`; the old CLI can print errors yet exit zero.
The probe recognizes this particular lookup failure as nonmembership and
propagates other errors. A real wire adapter should use the native fact lookup
API and map only its documented missing/type outcomes, not arbitrary failures,
to false. Network/auth/schema errors must remain explicit failures.

P1/P2 produce an actual collision: a numeric ID dereferences to different local
Flow declarations in the two DBs. Both raw local membership answers can be true.
This is honest: a token has meaning only with an opened handle. The probe's
qualified-membership control rejects the foreign Ref before lookup. Likewise,
P1equivalent accepts an equal raw token locally but rejects P1's qualified
occurrence/evidence. Requiring the raw integer alone to prove foreign origin
would contradict Phase 5B's corrected distinction.

**Inferred:** use backend-local tagged tokens such as `(predicate/version, ID)`
for admitted program-entity predicates, with explicit sum variants for composite
entities. Source-file nodes may use `src.File` facts. Qualified references pair
them with the exact opened occurrence. Do not expose every stored fact as a
program entity. Do not persist IDs of on-demand derived result rows as entity
identities: the old runtime repeatedly used an ephemeral result ID for different
queries; persist underlying entity facts/structural handles [S21].

## F. Mechanical kind/type mapping

**Source-inspected:** C++ `FunctionDeclaration`, record/namespace declarations,
`src.File`, and tagged definition alternatives provide adequate mechanical
categories directly. `CxxDeclKind` distinguishes Function/Method/Constructor,
records, namespaces and other categories [S08–S10]. A narrow normalization of
compiler-declared functions to `callable` and files to `source_unit` is adapter
work, not invented semantics. Keep category-specific qualifications; C++
namespaces are not source files or universal modules.

**Runtime-observed:** Flow ordinary declarations, including these functions,
receive numeric generic kind 20 (`Object` in the image schema). Current
`FlowEntityKind` still explicitly marks its broad Object/Property classifications
as inaccurate [S12]. Predicate `flow.Declaration` identifies a declaration,
but not whether it is a function, variable or parameter. The probe exposes this
limit; it does **not** parse a pretty-printed function type into a guaranteed
callable-declaration kind. Its type strings are useful evidence, not sufficient
proof of syntax category.

**Conclusion:** adequate kind is **THIN_ADAPTER for typed C++ entities**,
source-backed and unexecuted on current C++; **UNCLEAR/insufficient for this
Flow path's callable distinction**. Native indexed Flow modules and source files
are available. This is a language/indexer limitation (A/E), not evidence (D)
against an adequate mechanical-kind requirement. Do not offer this Flow probe
as a complete production backend for the Phase 4 consumer.

## G. Scoped containment

**Runtime-observed:** for selected E, the real query

```angle
codemarkup.flow.FlowContainsParentEntity {
  child = { decl = { localDecl = $E } }
}
```

returns that declaration's owning Flow module; its `file` alternative identifies
one exact `src.File`. E1 is in `alpha.js`, E2 in `beta.js`; swapping E2's valid
parent context fails E1's independent expected-context assertion. This is
file-module ownership, **not** a general lexical nesting relation [S11, S12].

**Inferred analogue:** the facts support an adapter view of
`file-backed module → source unit → declaration`. Module→file comes from the
selected module's key; file→declaration comes from E's loc/ownership query. Each
endpoint is distinct and in the same DB; source unit is the file fact. For these
fixture functions the declaration is syntactically a callable, but Glean Flow
kind alone has not established that last category. Thus the executable chain
establishes ownership/context only, not the full required callable-kind chain.

**Source-inspected C++ alternative:** obtain a selected function's source file
through `DeclarationSrcRange`, and its mechanically declared scope through
`DeclarationScope`. Record member parent queries use `DeclInRecord`/`DefnInRecord`
via `CxxContainsParentEntity`. The generic C++ parent predicate explicitly lacks
namespace parent coverage; using it alone would lose ancestors [S08, S10].
A function/file ownership edge and a namespace/record lexical edge are different
relationships. Do not invent `namespace → file` merely because both are returned
for one function: namespaces span files and files can contain many namespaces.
For a simple C++ fixture, actual `buck.TranslationUnit` stores the main source
file, build locator and optional platform; `ClangDB::finish` emits it and links
it to traces [S14, S28]. A selected main-file function therefore has a plausible
`compilation unit → source file → function` analogue using actual typed endpoints,
without inventing a repository-as-module root. Bind the unit through trace/file
identity; included headers and multiple build configurations cannot be collapsed
into one arbitrary unit. A C++ namespace hierarchy must retain its own genuine
scope identity. This analogue is **source-backed, inferred and unexecuted**;
the exact category spelling is language-specific, not a universal module type.

Bound the traversal, detect cycles/multiple parents, preserve parent/child
roles, and disclose truncation/unsupported parent forms. Prefer repeated
selected-node queries; no recursive Angle transitive closure is needed for the
demonstrated short chain, and none was executed. A scoped query may still scan
internally if the filter is not on an indexed key prefix; inspect query stats
before claiming scaling [S20]. Public API boundedness and efficient execution
are separate claims. No full graph dump is a reader requirement.

## H. Calls and resolution outcomes

The evidence distinguishes references from syntactic calls and analysis results
from runtime dispatch:

| Language/path | Actual mechanism | Honest interpretation |
| --- | --- | --- |
| Executed Flow | `LocalDeclarationReference`, imports/export resolution and locations | Reference occurrence, not proof of invocation; invocation/resolution families for call sites NOT_PRODUCED |
| Current C++ | `XRefTarget` declaration/unknown/indirect alternatives, `XRefTargets`, `FileXRefs` | Typed references/candidates; no examined C++ call-site predicate establishes every xref as a call |
| Current Hack | `FileCall` file/callee span, `callee_xrefs` set, dispatch argument, receiver type | Actual indexed call occurrence with zero/one/many recorded targets; retain unknown/dynamic occurrence alternatives |
| Current Python schema | `FileCall` file/callee span/arguments, `CalleeToCaller` names | Call syntax exists; generic `FileCall` supplies no callee entity for Python; name pairs are not qualified unique entity resolution |

**Source-inspected:** clang visits declaration/member references, emits all
functions in an overload set, and handles dependent/unknown targets. Selecting
the first returned function would erase ambiguity [S08, S15]. Generic location
mapping omits some unknown/indirect cases, so querying only its entity results
can hide unknowns [S10]. Hack has genuine call-site fields, multiple target sets,
and dynamic method occurrences that lack a known container [S16]. Python's
generic call dispatcher explicitly leaves callee absent [S13, S17]. None of
these prove all runtime targets or all unresolved syntax was indexed.

**Inferred policy:** a Hack site token could be its stored FileCall fact, with
outgoing rows only for mechanically backed targets. One recorded static target
may be reported as a resolved static analysis result only with that exact scope;
never as complete dynamic dispatch. A nonempty candidate set may represent
possible targets, not a unique resolution. An occurrence/unknown target is not
resolved to a local declaration by guessing its name. Zero targets establishes
unresolved analysis only if the indexer documents/records that outcome; otherwise
report an incomplete outcome or decline production. Calls absent because a
language/indexer has no call extraction are NOT_PRODUCED, not resolved-empty.

The probe compares P1/P2 real reference data and retains P1 reference results
unchanged after P2. It cannot perform a wrong-**call-site** falsifier because it
has no produced call sites. Hack/C++ resolution and dispatch controls are
**untested**, with source-backed distinctions identified for later execution.
Both optional families may remain NOT_PRODUCED in an initial C++ reader.

## I. Capability and completeness honesty

Glean supplies ingredients, not the ProgramBackend honesty record:

| Ingredient | What it establishes | What it does not establish |
| --- | --- | --- |
| DB Complete/Broken/Incomplete/Missing, dependencies [S02] | Storage/indexing lifecycle and availability | Completeness of calls, kind, containment or source scope |
| Stored schema/predicate IDs and statistics [S02] | Representation availability and population | That a zero population is exhaustive absence |
| `completePredicates`, derivation dependencies [S02, S21] | Production/derivation lifecycle over supplied facts | Exhaustiveness of external inputs or analysis |
| `src.IndexFailure` [S07], clang compile diagnostics | Recorded file failures | Absence of every unrecorded failure/missing dependency |
| `indexer.Config` and DB properties [S24, S02] | Recorded recipe/config if producer populated it | That all clients/indexers record adequate provenance |
| Explicit indexed-input manifest (composition) | Finite declared input boundary and retained basis | Whole-repository or runtime completeness |

**Inferred conservative mapping, separately keyed by requested family:**

| Family | Initial status/basis | When stronger claims become possible |
| --- | --- | --- |
| Membership/kind | INCOMPLETE for external repository; lookup/category backed by selected facts | COMPLETE only for a precisely declared admitted-entity universe and adequate typed categories |
| Containment | INCOMPLETE; named language parent/ownership rules, known absent parent forms | COMPLETE for a bounded specified ownership/context scope only after recipe/coverage evidence |
| Invocation (Flow or examined C++ path) | NOT_PRODUCED; no proven syntactic call production | Different indexer/schema with real site extraction and qualified coverage |
| Resolution (same paths) | NOT_PRODUCED for call-site outcome family | Documented outcomes with ambiguity/unknown retention, not just xref entity results |
| Evidence/reconstruction | INCOMPLETE until locations and retained bytes are associated/available | COMPLETE within the retained selected-source scope, not all source material |

Missing recipe, unresolved references, missing dependencies, dropped files,
unknown derived-predicate status, auth filtering, timeouts/truncation, and
uncertain source retention are gaps. Refuse qualification or mark INCOMPLETE;
never silently turn those into complete empty results. Drain/validate
continuations for a requested scope; a timeout/error is not zero matches.

`capability(containment)` must select the containment policy and producer basis
for this DB/schema/recipe. A calls qualification is individually valid but wrong
for that request. The probe's independent wrong-family policy comparison rejects
substitution; **this is an adapter-policy discriminator, not native Glean
capability metadata or a complete conformance test**. The frozen public
`Capability(status, scope, basis, gaps)` is sufficient; no inventory API or
Glean predicate names need become universal. Zero results alone licenses
**none** of the above stronger claims.

## J. Entity evidence and historical reconstruction

**Source-inspected:** `DeclarationSrcRange`, `DeclarationNameSpan`, language
location predicates and `codemarkup.EntityLocation` join selected entities to
files/extents [S07–S13]. Location meaning differs: a name span, declaration
range, definition location and full declaration span are not interchangeable.
Multiple declaration/definition locations may be legitimate; preserve them
rather than arbitrarily asserting one canonical source manifestation.

`src.ByteSpan` is byte start/length without source conversion; CRLF counts as
two bytes. `src.Range` uses 1-based inclusive lines/columns with Unicode code
point columns. `FileLines` stores byte lengths and flags, not all text needed
to convert Unicode columns exactly. Never use character offsets as byte offsets
or strip newlines before slicing [S07]. The adapter may retain those Glean-native
coordinates inside an opaque handle. No native source locator translation is
required by the contract.

**Runtime-observed:** `flow.DeclarationLocation` joins E1/E2 to full declaration
spans. E1 reconstructs `function first...x + 11`, E2 reconstructs a different
function containing `first(x) + 22`. The independent fixture strings discriminate
E1 from E2 even though both handles individually verify. Probe checks selected
entity ID, DB Ref, file/span, source manifest and retained SHA-256 before slicing.
Substituting E2's material for E1 fails the expected E1 manifestation assertion;
merely verifying the returned handle would not suffice.

**Source-inspected source storage:** current `src.FileContent : File -> string`
exists with explicitly optional population [S07]. HIE writes it under `storeSrc`
(the `--store-src` option); that implementation uses lenient UTF-8 decoding
[S22, S23]. Invalid byte sequences therefore need a separate retained-byte path
for exact byte reconstruction. The examined clang file producer writes SHA-1
plus size in `digest.FileDigest` and line information, not FileContent [S14,
S26]. `src.FileDigest` alone specifies no hash algorithm. A digest is identity
material, not retained bytes or a retrieval/availability guarantee.

Reconstruction classification:

- **NATIVE, conditionally:** DB contains associated FileContent and the indexer
  preserves the exact required text under known encoding/range semantics.
  Check actual population, not schema existence. Current HIE is source-backed,
  unexecuted here, and invalid UTF-8 preservation is not established.
- **COMPOSABLE WITH EXTERNAL RETAINED SOURCE STORE:** for clang and this Flow
  probe. Capture the exact indexed file bytes and manifest, or fetch a retained
  exact revision/blob with verified digest/size/algorithm and generated/untracked
  files covered separately. Repository name, path or an arbitrary DB hash does
  not establish this provenance. A Git revision is insufficient for files
  generated or modified outside that revision.
- **UNSUPPORTED for verified reconstruction:** if only ranges remain and neither
  associated content nor an exact retained external source exists. Return an
  explicit reconstruction failure, not a current-workspace fallback.

The probe's external store survives removal of the index workspace. Wrong DB,
wrong source revision/digest, corrupt retained bytes and missing retained bytes
are rejected. This proves a controlled composition, **not** that Glean always
stores source bytes or that arbitrary source revisions supplied as properties
are truthful. Source provenance/retention is owned by the indexing composition.

## K. History, incremental indexes, and retention

**Source-inspected:** retention can expire/delete old DBs according to age/count/
properties policies. Retention computes dependency closure for stacked/pruned
DBs. Missing dependencies are recognized; preserving only a top DB identity is
not sufficient [S02, S05, S27]. Pruned DBs view selected ownership units from a
base and new facts above it; the view, its GUID and its full dependency closure
qualify the state. In-place edits to old accepted DBs are not the proposed
incremental workflow [S02, S03].

Native lifecycle finalization prevents normal writes, but local `unfinish`
exists when backup policy permits it and is explicitly a testing-only operation
[S06]. `updateProperties` is also restricted to Incomplete DBs and refuses a
read-only server [S03]; finalized properties are not freely mutable through that
supported API.
Therefore “Complete” plus GUID alone is not a malicious-owner immutability proof.
The exact-read contract, like native sealing, needs a retention policy that
forbids reusing/unfinishing accepted DBs and changing their authoritative
qualification. Pin recipe/source metadata in an immutable composition record;
checking a fresh status response does not detect every prohibited past edit.
A read-only local root or controlled service with durable backups is plausible;
no such production deployment/GC lease was implemented or tested.

**Runtime-observed:** old scoped membership/context/reference/source reads remain
P1-local after P2. The fixtures visibly differ in entity population, file context,
source material and reference behavior. P2 changes `first` from a function to a
string-valued const, moves `second` to another file and adds `added`. Flow's broad
kind does not distinguish the function/const change; that is a measured gap.
Calls themselves are not produced, so the requested call-history falsifier is
unexecuted. Missing historical DB refuses opening while P2 still exists; actual
server GC/restore and stacked/pruned history were not executed.

**Conclusion:** Glean can retain distinct exact DB states; it is not restricted
to latest. Long-lived accepted-history retention must be arranged at composition,
including base dependencies and source bytes. Loss of required history is a
visible verification/open/reconstruction failure. No full second program graph
is implied by this requirement.

## L. Verification and executable evidence

The manual [probe](../tests/phase6a_glean_spike.py) runs real Flow indexing and real
Glean create/derive/finish/query/status commands, through a pinned official
container. It imports no native graph fixture and subclasses no production
backend. It uses an isolated temporary DB root, explicitly named DBs and a
controlled retained source manifest. It does not use fabricated query responses.
Diagnostic enumeration finds ID collisions; ordinary selected membership and
context/evidence reads are keyed. The runner cleans its container and temporary
root; it writes no tracked run transcript or credentials.

```sh
docker pull ghcr.io/facebookincubator/glean/demo@sha256:eec9d45a51f7c0bcc8d2260b3e519cd633034851b84cda0bf9d0f91bc8ba6a10
uv run python tests/phase6a_glean_spike.py
```

**Runtime-observed final probe result:** PASS for its declared subset, process
exit 0. An initial run completed its assertions but failed temporary-directory
cleanup because container files were root-owned; the runner now restores task
mount ownership before removing the container, and the complete rerun passed.
The old image's CLI logs some query failures with exit 0, so the runner checks
error output too. No blanket error-to-nonmembership conversion is allowed.

A future composed `verify()` should check exact Ref/GUID/schema/input recipe,
finalized availability and dependency closure, relevant selected membership and
endpoint associations, per-family qualification and retained evidence digests/
extents. It should return named violations for unavailable source/history,
malformed locators, mismatched family or scope. Storage `glean validate` may
assist but is not proof of semantic correctness, producer coverage, or source
association. Full current DB storage validation was not executed in this probe.

### Existing tests: portability classification

No Phase 5A/5B test was modified. Existing tests were run as **native regression
checks**, not represented as Glean conformance. Their fixture wiring and native
copy/damage helpers cannot simply be parametrized with a remote Glean handle.

| Existing tests/assertions | Classification | Reuse decision |
| --- | --- | --- |
| Direct state, membership, context, selected evidence, requested-family and unsupported-empty assertions in `test_program_backend_production.py`; lazy core without enumeration | Backend-neutral semantics, directly reusable after independent Glean expectations/qualification wiring | Best Phase 6B core target; probe exercises a subset with actual Glean responses |
| Phase 5A exact occurrence, wrong snapshot, copied qualification, historical reads and evidence qualification cases | Neutral guarantees with composition-specific fixture construction/copy/damage | Retarget factory/fixture, not frozen semantics; no forced native PublicationRef |
| Phase 5A duplicate labels, typed facts and unresolved/incomplete negative conclusions | Neutral semantics, but discovery/optional produced-family fixture assumptions | Use selected tokens where available; optional calls require a producing language |
| Direct native receipt, blob corruption, missing receipt, native chain/state expectations, constructor/native candidate mutants | Native-adapter/application-specific | Keep native regressions; do not require SQLite rows/receipts on Glean |
| Constructor migration, retained publication and Phase 4 vertical slice | Composition/publication-specific | Glean reader alone cannot run unchanged through native cloning/validation |
| Phase 5A `optional_comparison_*`, comparison-correspondence controls, discovery helpers | Optional discovery/comparison-specific | Outside Phase 6A core mapping; no Glean discovery/comparison implementation |
| Dishonest empty/collapsed copy and wrong-member/wrong-family controls | Transferable discriminators, native production/fixture plumbing | Preserve independent expected-answer oracle; do not just compare backend getters |

Even `ancestor_chain` in Phase 5A uses an unscoped test projection of containment;
production core already requires only selected ancestor reads. Its test harness
shape is a portability finding, not a demand for Glean graph enumeration or a
reason to alter frozen tests. Likewise fixture Unicode and labels are fixtures,
not required Glean entity spelling.

Repository validation at this phase:

| Check | Result |
| --- | --- |
| `uv sync --locked --extra dev` | PASS |
| `npm ci --prefix frontend` | PASS; npm reported existing dependency audit findings; no dependency changes |
| ProgramBackend production + Phase 5A + Phase 4 focused regressions | 89 passed |
| Manual real Glean/Flow probe | PASS for declared subset; full conformance explicitly unproven |
| Default gate `uv run --extra dev pytest` | 208 passed; no skips; counts overlap focused regressions |
| Core acceptance separately | 18 passed |
| `git diff --check` | PASS |

The initial default/core commands encountered `OSError: [Errno 122] Disk quota
exceeded` in `/tmp` while constructing fixtures. Both gates were rerun with
fresh `--basetemp` directories on the main filesystem; no code/test changes were
needed. These are the successful commands (same configured test selection):

```sh
uv run --extra dev pytest -q --tb=short \
  --basetemp /home/kerem/.cache/design-phase6a-default-20261007
uv run --extra dev pytest -q tests/test_core_v1_acceptance.py --tb=short \
  --basetemp /home/kerem/.cache/design-phase6a-core-20261007
```

No frontend/packaging code changed; their additional build gates are not needed.
The default gate is not the entire historical test inventory.

## M. Required conformance matrix

Statuses classify the mechanism, not a claim that every cell was executed.
Confidence/evidence distinguish current-source support from the older runtime.

| Requirement | Native meaning | Glean mechanism | Status | Adapter work | Evidence |
| --- | --- | --- | --- | --- | --- |
| Exact occurrence open | Exact retained address; no latest fallback; distinct equal copies | Namespace + Repo + generated GUID; exact DB API | COMPOSITION_REQUIRED | Unique index instances, expected GUID/schema, no key reuse, exact restore/retention | S02–S05; runtime P1/P2/equivalent and missing-ref controls |
| Observed-state token | Stable recorded observed state, separate from occurrence | Indexed DB GUID/schema + qualified recipe/input state | THIN_ADAPTER | Stable opaque encoding; exclude mutable/latest metadata | S02–S04; runtime controlled manifest and wrong-state qualification |
| Entity membership | Local token under opened state, no enumeration | DB-scoped fact lookup and predicate type; visible base/pruned view | THIN_ADAPTER | Typed admitted token set, handle qualification, normalize missing only | S02, S04, S25; real selected lookup and ID reuse |
| Mechanical kind | Adequate declared category, no universal ontology | C++ function/file/record/namespace predicates and kind derivation | THIN_ADAPTER | Narrow normalization; Flow callable distinction remains insufficient | S08–S12; current C++ source only; runtime Flow kind gap |
| Scoped containment | E's ancestor edges, direction/endpoints/category/state | Flow owning module/file; C++ translation-unit/file/scope/member parents | THIN_ADAPTER | Preserve ownership vs lexical scope; bounded walk; fill only mechanically established edges | S08, S10–S12, S14, S28; runtime selected Flow ownership; C++ full chain untested |
| Scoped invocation | Optional call-site outgoing targets or NOT_PRODUCED | Hack FileCall; Python syntax; Flow/C++ references do not prove sites | THIN_ADAPTER | First reader can decline optional production; Hack mapping must retain target sets | S13, S15–S17; call-site execution untested |
| Resolution honesty | No false unique/complete-empty; optional production | C++ candidate/unknown references; Hack sets/dynamic occurrence; Python missing callee | THIN_ADAPTER | Decline call resolution initially; never select first candidate; label static scope honestly | S08, S13, S15–S17; producing-language execution untested |
| Per-family capability | COMPLETE/INCOMPLETE/NOT_PRODUCED plus scope/basis/gaps for requested family | Lifecycle, schema/stats, derivation state, failures/config + producer manifest | THIN_ADAPTER | Conservative family-specific recipe policy; lifecycle Complete is insufficient | S02, S07, S21, S24; runtime only policy discriminator |
| Entity-associated evidence | Evidence for selected E, not any valid source | Selected entity location/name/declaration/definition predicates | THIN_ADAPTER | Opaque handle binds entity/DB/file/extent; retain independent association oracle | S07–S13; real E1/E2 full declaration discriminator |
| Historical reconstruction | Exact retained material or explicit failure | Optional FileContent; otherwise digest/revision plus retained external bytes | COMPOSITION_REQUIRED | Capture/retain indexed sources, encoding/digest checks, no live fallback | S07, S14, S22–S26; external-store probe without workspace |
| Verification | Inspectable failure of promised closure/qualification | DB/schema/status/dependency APIs plus source/association checks | THIN_ADAPTER | Compose checks; require retention basis; not merely storage validity | S02–S06, S27; partial runtime negative controls |

For kind/containment the table identifies a credible C++ adapter route, not
proof that the executed Flow subset satisfies the demonstrated callable consumer.
The overall partial verdict is conditional on executing that route. No required
core behavior has been proven universally unsupported, and no independent
contract falsifier has appeared.

### Native predicate/query mapping (adapter implementation only)

| ProgramBackend behavior | Candidate Glean facts/query | Qualification | Confidence |
| --- | --- | --- | --- |
| Open/state | `Repo`, `getDatabase`, `glean.guid`, `glean.schema_id`, indexed input record | Exact namespace/DB instance, terminal status, retained dependencies | High source + older runtime |
| Membership | `userQueryFacts(Repo, IDs)`; typed selected Angle lookup in probe | Predicate/version + local fact ID; qualified occurrence external to token | High source + older Angle runtime; raw Thrift missing outcomes unexecuted |
| Kind | `cxx1.FunctionDeclaration`, `codemarkup.cxx.CxxDeclKind`, `src.File` | Language/schema; do not trust Flow Object as callable category | High schema; current C++ runtime untested |
| Containment | `buck.TranslationUnit`, `cxx1.TranslationUnitTrace`, `DeclarationScope`, `DeclarationSrcRange`, `DeclInRecord`, `DefnInRecord`; Flow parent/module key | E-specific unit/file ownership and ancestry semantics, not arbitrary range overlap | Medium; Flow ownership executed, C++ missing-parent/configuration coverage open |
| Calls | `hack.FileCall`, `python.FileCall`, generic `codemarkup.FileCall` branches | Actual stored site, language/config, static targets and dispatch gaps | Medium schema; not executed |
| Resolution | `hack.XRefTarget`/`callee_xrefs`, `cxx1.XRefTarget`/`XRefTargets` | Unknown/indirect/candidate alternatives; reference vs call kept separate | Medium schema; outcomes policy/indexer coverage open |
| Source evidence | `DeclarationSrcRange`, `DeclarationNameSpan`, `flow.DeclarationLocation`, `codemarkup.EntityLocation` | Selected entity, exact DB/file, precise locator meaning | High source + Flow runtime |
| Reconstruction | `src.FileContent`; clang `digest.FileDigest`; retained source manifest/store | Verified exact indexed bytes/text and algorithm/encoding | High conditional source + external-store runtime |
| Capability | `indexer.Config`, `src.IndexFailure`, stored schema/stats, completion APIs, retained recipe | Requested family, exact state and finite declared scope | Medium; no universal native completeness record |

## N. Required epistemic-failure matrix

“Can reject” means the proposed mapping **with its stated composition**, not
that bare Glean APIs enforce every guarantee. Untested rows are explicit.

| Dishonest behavior | Can proposed mapping reject it? | How? |
| --- | --- | --- |
| Latest substituted for requested historical DB | Yes; subset executed | Pin Repo/GUID/schema/namespace; missing-ref and wrong-GUID opening fail while P2 exists; no name-only helper |
| Foreign entity treated as local member | Yes for qualified entity; raw token collision is legitimate | Check originating Ref before lookup; collision actually observed; token-only foreign-origin rejection is impossible and not required |
| Wrong ancestor returned | Yes for observed file context; general lexical mapping untested | Selected-child query plus independent expected alpha/beta owning module/file; validate edge direction/local endpoints |
| Wrong-site call returned | Proposed yes; NOT executed | Real site token must bind file/extent; outgoing query and assertion pin requested site; optional Flow path declines production |
| Unresolved treated as resolved | Proposed yes; NOT executed on producing indexer | Preserve unknown/occurrence and multi-target alternatives; no first-row uniqueness; decline unsupported resolution |
| Unsupported treated as complete-empty | Yes by conservative policy; native completeness absent | Family policy NOT_PRODUCED for absent call extraction; query zeros cannot change that status; missing coverage stays INCOMPLETE |
| Evidence from another entity returned | Yes; executed independent material control | E1 expected full declaration differs from valid E2 material; locator query pins E; handle validity alone insufficient |
| Evidence from wrong revision accepted | Yes; executed controlled composition | Ref/state/file manifest/digest equality then retained-byte verification; wrong-state handle/source digest rejected |
| Live mutable source accepted as historical evidence | Yes; executed external-store path | No workspace read in reconstruct; workspace deleted; missing/corrupt blob fails; never fallback to checkout |
| Capability from wrong family returned | Yes by family policy; policy-only control executed | Compare requested full qualification with independently declared family expectation; calls qualification differs from containment; no native family record claimed |

Coverage caveat: an adapter returning a consistent but wrong evidence handle for
E1 cannot be caught by a reconstruction-validity test alone. The independent
manifestation oracle is essential. The same applies to a valid wrong-family
capability. This preserves the final Phase 5B association distinction.

## O. Language/indexer dependence

Generic Glean supplies DB/fact/schema identity, keyed querying, derivation and
retention mechanisms. Languages supply typed declarations, containment and
location relations. Indexers determine actual population, success, flags,
source storage and coverage. These are three different evidence levels.

The mature **Flow** path was executable in the official image and was actually
indexed here. It proves a useful subset, with a clear kind/call gap. **C++/clang**
is the principal source-backed candidate for the adequate callable/category
reader, with missing namespace/generic parent coverage requiring careful scoped
mapping. **Hack** is the stronger source-backed call-site candidate. **Python**
call syntax cannot be assumed to imply resolved callee entities. **Haskell/HIE**
has an explicit source-storage option. SCIP/LSIF support mentioned in Glean's
README does not prove equal behavior or full parent/call capability. No universal
language support is claimed, and no indexer feature parity table substitutes
for epistemic conformance.

## P. Smallest exact-reference/factory sketch

This is a sketch, not an implemented public type or registry:

```text
GleanOccurrenceRef:
    service/storage namespace identity
    Repo(name, hash)                       # exact DB instance, not latest
    expected glean.guid
    pinned stored schema qualification
    retained indexing input/recipe record  # state + coverage/source basis
    dependency/source retention basis      # composition, not query syntax

open_glean_occurrence(ref):
    resolve exact namespace/Repo
    require promised immutable, finalized occurrence or fail
    compare expected GUID/schema and retained state record
    require visible dependency closure and declared retention qualification
    return reader whose EVERY operation is bound to that Repo/schema
```

Storage namespace is not automatically a server hostname: a replicated service
may expose one retained DB through different hosts. Conversely two independent
stores might have the same name/hash. Composition decides and records the
namespace identity. The GUID is a useful native discriminator; an imported
backup/copy preserving a GUID is not automatically a separately published
occurrence. Independently retained occurrences can use distinct exact names/
instances or declared namespaces; the reference must not deduplicate by content.

Reader implementation can own local typed tokens, selected queries, a narrow
category map, per-family conservative policy and opaque evidence handles.
It needs no native table names, TypeScript IDs, receipt JSON, bundle layout,
full enumeration, comparison or schema translation framework. The manifest/
source retention fields can remain composition-owned records rather than new
reader methods. There is no proposed universal occurrence class.

## Q. Composition/retention gap forced by Glean

Current native lifecycle in `ontology_author/authority/lifecycle.py` opens a
native World, creates PublicationRef inputs and copies native program artifacts.
`authority/validation.py` expects native `program_entity`/`program_snapshot`
qualification and native retained support. A conforming Glean reader would not
make those mechanisms disappear automatically. Phase 5B extraction debt is real
**category C**, independent of whether Glean implements selected reads.

The concrete decision is: **what exact program/evidence basis is admitted and
retained by semantic publication when it no longer clones a native program World?**
The basis must validate selected membership, state, context and evidence in
independent historical reads, and retain its Glean dependency/source closure.

| Hypothesis | What Glean evidence supports | Remaining decision |
| --- | --- | --- |
| Exact retained Glean DB reference | Native Repo/GUID/schema, backups, dependency closure and exact reads | Durable service/archive availability, no reuse/unfinish; candidate basis validation above reader |
| Content-addressed exported evidence | DB/selected fact queries and source digests | Canonical content identity, predicate/schema/association qualification; digest alone does not retain bytes |
| Bounded retained witness material | Selected entity/context/evidence queries avoid full graph copy | Which finite claims can be validated/reconstructed from witness; never claim whole-DB absence/membership beyond witness |
| External retained source store | clang digest/size and entity locations; real probe demonstrates controlled source retention | Capture exact indexed generated/untracked/dependency bytes and authenticate association to input recipe |

Preferred hypothesis is a retained exact Glean DB reference plus retained source
store when needed, with bounded evidence witnesses if publication requirements
justify them. This is **inference**, not a chosen/implemented publication design.
Content-equivalent exports are evidence material; they cannot replace occurrence
identity. A source-only witness cannot prove program analysis membership or
calls. No requirement to clone a second authoritative program graph follows.
Phase 6B needs a specific composition decision or must explicitly remain a
reader-only implementation with native end-to-end publication still unavailable.

## R. Native deletion opportunities (no deletions in Phase 6A)

| Current component | Classification | Reason/condition |
| --- | --- | --- |
| `program_spine/typescript_extractor.js` compiler extraction and local fact production | Likely replaced by Glean | Only for selected language/indexer coverage that actually conforms; this study does not prove TypeScript parity |
| `program_spine/typescript.py` projection/IDs/schema materialization and `schemas.py` program tables | Likely replaced by Glean | Direct adapter reads should remove a second authoritative full program graph |
| Native capture receipts/source manifest/closure validation in `typescript.py` | Still needed above Glean as guarantees; native encoding replaceable | Indexed input provenance, coverage and retained source association remain necessary |
| `evidence/program_source.py` native observation reconstruction | Native-only compatibility implementation; guarantee still needed above Glean | Glean opaque evidence provider/store can replace encoding but not exact reconstruction |
| `program_backend/native.py` and `open_native_occurrence` | Native-only compatibility | Keep for historical bundles/reference regressions; production Glean would be a separate implementation |
| `program_backend/__init__.py` logical scoped contract | Still needed above Glean | Independent consumer boundary, no evidence of overconstraint |
| Native lifecycle clone, PublicationRef program basis, native candidate checks | Native-only compatibility; future composition redesign required | A reader adapter does not satisfy those accepted-history/admission obligations |
| `program_spine/comparison.py` correspondence/maintenance comparison | Still needed above Glean if application requires it | Policy/evidence of cross-state correspondence not supplied merely by DB fact IDs; native table access may later change |
| Authority construction, semantic binding, governance, maintenance/application policies | Independent semantic/application machinery | Glean supplies mechanical facts, not standing or semantic association |
| World kernel, retained semantic Worlds, generic grounding/admission | Independent semantic/application machinery and frozen core | No Glean requirement falsifies core primitives |

This is a conditional deletion inventory, not authorization for Phase 6B to
remove native history, tests or research. ProgramSpine/ProgramBackend remain
logical contracts; Glean is the candidate provider.

## S. Code Explorer implications — informational only

Angle can project/join facts and return JSON or Thrift; stored derived predicates
can provide useful keyed access paths [S02, S20, S21]. That may later support a
relational/SQL **read projection** for consumers. Such a projection would need
explicit snapshot/schema/language/coverage qualification and would be derived
from Glean, not a competing authoritative graph. No SQL export format, UI,
repository split, graph product or query product was designed or built here.
No semantic search, embeddings, retrieval, candidate association, binding judgment
or requirements-to-code discovery work is part of this phase.

## T. Contract challenges and mismatch classification

| Mismatch/failing case | Category | Consequence |
| --- | --- | --- |
| Flow Object kind does not distinguish indexed function vs const | A for the observed classification; E for a stronger natural Flow path | Do not invent callable semantics; use typed language or obtain additional mechanical evidence |
| Flow/inspected C++ xrefs do not establish a produced call-site family | A for this path; optional behavior permits NOT_PRODUCED | Do not weaken optional-family honesty or turn xrefs into calls |
| C++ generic parent predicate omits namespace context | B for scope/file mapping; E for complete selected namespace identity coverage | Prove scoped mapping on a current C++ fixture before claiming full consumer context |
| DB Complete is not analysis completeness | B | Derive conservative requested-family policy with explicit scope/recipe/gaps |
| Same integer ID resolves in two DBs | B plus C qualification boundary | Handle-scoped local tokens and qualified occurrence references; no global ID requirement |
| Old DB deletion, dependent base loss, accepted DB unfinish/reuse | C | Durable retention/immutable-publication covenant, exact failure/restore |
| clang omits source bytes; arbitrary DB hash not necessarily Git revision | C | Exact retained indexed source manifest/store; no mutable checkout substitution |
| Native lifecycle/validation requires program World/PublicationRef | C | Separate composition decision, not ProgramBackend redesign |
| Current-source executable not built; producing call/resolution language unexecuted | E | Keep source-backed mapping distinct from runtime proof |

No **D** case has been demonstrated. An honest non-Glean reader is not harmed
by selected membership, adequate category, bounded context, family qualification
or associated retained evidence. Phase 5B's lazy non-filesystem test remains an
independent counterexample to representation-based objections. Thus there is no
basis to alter the production interface or Phase 5A/5B tests. A genuine D case
would require a separately documented non-Glean falsifier and separate review.

## U. Final verdict

Glean naturally supplies exact selected-DB queries, typed local facts and
entity-associated locations. The current source presents a plausible thin C++
reader path; real Flow execution establishes historical identity/locality and
retained evidence composition, but also demonstrates that one mature indexer
does not establish every consumer category. Native generic completeness and
unconditional source/history retention are not provided. The required work is
conservative adapter qualification plus an explicit retained DB/source/publication
basis, followed by current C++ executable conformance. No interface weakening
or second full authoritative program graph is justified.

```text
PARTIAL — GLEAN SUPPORTS THE CORE WITH SPECIFIC
COMPOSITION / RETENTION WORK
```

Should Phase 6B implement a production Glean adapter?

```text
YES, AFTER SPECIFIC COMPOSITION DECISION
```

Decide the admitted retained DB/source basis and independence of candidate
validation from native bundle cloning; then prove the selected C++ typed kind/
context path against a pinned current runtime before calling an adapter
production-conformant. Optional invocation/resolution may initially remain
NOT_PRODUCED. The Flow probe alone is insufficient to green-light its own
production adapter. Phase 6B is not implemented here. This branch is for a draft
PR only; no automatic merge.
