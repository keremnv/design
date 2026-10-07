# Target Architecture v0 — Phase 5A ProgramBackend requirements

Status: requirements and executable native behavioral evidence for adversarial
review. No production interface, adapter, consumer migration or Glean evaluation.
This is downstream mechanical program machinery; Core Product v1 stays frozen.

## A. Starting point

Merged Phase 4 `main`: `636946cc43f048d95acf7db9fb0508a62ddfb562`.
Merged-main CI was green at task entry. This branch starts at that exact commit.
The governing evidence is [Phase 4 §I](TARGET_ARCHITECTURE_V0_PHASE4.md#i-capability-demand-ledger),
not the full native producer schema:

1. Produce P1/P2 at fresh retained addresses from declared source/configuration.
2. Open and qualify an exact program occurrence.
3. Establish membership; optionally discover the selected entity by kind/label.
4. Read snapshot identity and source-state revision.
5. Reconstruct the selected entity's exact retained source material.
6. Inspect structural context and the warrant's applicable mechanical facts.
7. Optionally compare P1/P2 for a reconsideration signal.
8. Verify the publication's retained program SOURCE evidence closure.

Consumers audited: `config_routes.binding.construct_config_binding`;
`authority.lifecycle.construct_authority_world`; `AuthorityConstructor` membership,
snapshot, default-warrant and relevance-scope construction;
`authority.validation.verify_construction_boundary`/`verify_authority_publication`;
Phase 4 historical/evidence reads; and `program_spine.compare_spines` as invoked
by Phase 4 Case G. The demonstrated history is W0 → P1 → W1 → P2 → W2,
where W2 needs W0 and P2, and does not need W1 or comparison.

## B. Consumer-demand audit

Derivation begins with what a caller needs to establish. Native surfaces below
are evidence of implementation, not proposed methods. **Core** means required
for this demonstrated read/evidence use; **producer** is separate from reading;
**optional** may be refused without preventing fresh binding construction.

| Consumer / purpose | Required information | Qualification | Meaningful failure / unknown | Classification | Current native mechanism |
| --- | --- | --- | --- | --- | --- |
| Slice setup: produce P1/P2 | Successful indexed occurrence, source/config scope, construction result | Fresh retained occurrence; declared producer | Ingestion/admission failure; no accepted output | Separate producer obligation | `build_typescript_spine`, `TypeScriptBoundary`, receipt, fresh output |
| Authority lifecycle: record consumed program input | Exact occurrence reference, serializable provenance | Verify against the actually opened occurrence, not a local counter | Unavailable or identity mismatch; refuse substitution | Core | `PublicationRef.from_world`, `verify_publication_ref`; `ConstructionBasis` |
| Binding: accept explicitly selected E | Membership in observed program universe | Opened occurrence and its snapshot | Not a member; refuse binding, without asserting global nonexistence | Core | `program_entities()` currently enumerates; `program_entity` |
| Attachment: qualify E's observation state | Snapshot token and source-state revision | One qualified observed snapshot for this construction input | Missing/ambiguous snapshot or mismatched entity snapshot | Core | `_load_snapshot`, `_entity_snapshot`, `program_snapshot`; grounding snapshot id |
| Relevance construction: choose application rules | Declared mechanical kind of E | Same selected entity/snapshot; kind meaning declared | Kind not established; no invented category | Core | `_entity_kind`, `program_entity_kind`; `default_relevance_clauses` is application logic |
| Slice selection: find fixture callable | Mechanical kind and display label | Results are local candidates, not semantic selection | Zero/multiple matches; explicit selection still required | Optional discovery | Retained kind rows joined to `_world_referents`; candidate `program_entities(kind, label)` |
| Default warrant: record structural context | Directed containment roles and ancestor context | All entity endpoints in the same observed snapshot | Unsupported/incomplete context must be disclosed; never fabricate a chain | Core containment view | `structural_context()` traverses parent/child rows |
| Default warrant: record applicable invocation facts | Call-site and target roles, if produced | Snapshot and call-extraction capability | Unsupported differs from supported/no observations | Core qualified fact-read behavior; invocation production not independently mandatory | `invoked_targets`, `program_invokes`; empty for Phase 4 leaf |
| Default warrant: record applicable resolution outcomes | Subject, status, capability, if produced | Snapshot and declared outcome semantics | Unresolved/multiple candidates are not resolved targets; absence is not a negative | Same qualified fact-read behavior; resolution production capability-dependent | `_default_warrant`, `program_resolution`; empty for Phase 4 leaf |
| Constructor discovery / native comparison | Optional identity descriptor | Local mechanical descriptor, never persistent identity | Missing descriptor; discovery/comparison may refuse | Native extra for core reads; native comparison precondition | `program_identity_descriptor`; unfiltered `program_entities()` computes but does not use descriptor filter |
| Historical reads: inspect P1 after P2/W2 | Same descriptor, membership and facts as originally retained | Exact old occurrence; no latest resolution | Old occurrence unavailable must fail explicitly | Core | Independent read-only `ConstructionWorld.open` calls |
| Slice evidence reads: inspect E's text | Nonempty qualified source observations and reconstructed bounded material | Source identity, revision and location agree with observed state | Qualification mismatch, unavailable/corrupt material; no live fallback | Core for selected supported entity | `program_source_observations`, `reconstruct_program_observation` |
| Publication admission / retained authority verification | Closure of declared reconstructible program observations | Retained evidence belonging to this publication | Named verification failures, not empty success | Core evidence verification | `commit` pre-seal check; `verify_retained_program_inputs`; authority boundary verifier |
| Case G: signal reconsideration of historical E1 | Qualified correspondence/change, epistemic basis, evidence, limitations | Exact P1/P2 context plus compatibility | Unsupported, incompatible, partial, ambiguous; no automatic rebind | Optional service | `compare_spines`, correspondence claims and `ProgramDelta` |

The authority lifecycle currently clones the program baseline into the semantic
candidate. The *behavioral* need is to retain the selected mechanical basis and
source evidence so W1/W2 can reconstruct with P1/P2 moved away (Phase 4 Case J).
Copying a complete database is not a backend obligation. Qualified facts,
observations and reconstructible material allow the application/evidence adapter
to retain that basis; retention inside a semantic publication remains its
responsibility. No backend operation constructs a semantic World.

Retained authority verification validates recorded basis/snapshot consistency
and local source closure; it does not reopen absent P1/P2 or prove arbitrary
caller-supplied warrants internally consistent. That inherited admission debt
remains separate. W0 tuple matching, paragraph support, authority standing,
`realized_by` and default relevance policy are entirely application operations.

## C. Accidental implementation details removed

Audited and excluded as universal representation requirements:

- `ConstructionWorld`, SQLite, `world.sqlite`, `_world_referents`, relation table
  names, grounding tables and separate kind/membership rows.
- Filesystem addresses, publication directories, `copytree`, chmod sealing,
  candidate/staging layouts, JSON receipt sidecars and `program_inputs` blobs.
- `PublicationRef`'s particular address/world-id/revision fields. Its exactness
  behavior is retained; that Python class is not the universal reference shape.
- TypeScript entity-id syntax, descriptors, `TypeScriptBoundary`, `tsconfig`,
  compiler API configuration and the producer's closed list of entity kinds.
- TypeScript UTF-16 AST positions, conversion to UTF-8 bytes, filesystem paths,
  SHA-256 addressing and textual `bytes:start:end` locations. The consumer does
  no cross-backend coordinate arithmetic. The Unicode conformance case checks
  reconstructed material, not a universal coordinate unit.
- Config-route vocabulary, authority endpoint resolutions, warrant support,
  semantic currentness, human/agent judgment and realization policy.
- Native comparison's full delta schema and identity-descriptor matching rules.

These exclusions follow actual inspected code, not an investigation of Glean.
No Glean repository, schema, syntax or product documentation was consulted.

## D. Semantic invariants

1. **Mechanical ≠ semantic.** Observation of a callable/context is not approval,
   business meaning, compliance or requirement satisfaction.
2. **Absence ≠ false.** Not observed licenses a negative only under a declared
   capability, its scope, completeness basis and relevant resolution limits.
3. **Occurrence identity ≠ content equivalence.** Identical retained copies are
   different historical inputs, even with equal source-state/snapshot tokens.
4. **Entity identity is snapshot-local.** Dereferencing requires qualified
   snapshot context; matching labels or opaque tokens across contexts is not
   persistent identity.
5. **Correspondence ≠ identity.** `CONTINUED` describes a comparison judgment;
   it does not collapse old/new entity occurrences.
6. **Deterministic computation ≠ epistemic entailment.** Reproducible heuristic
   matching remains heuristic and exposes its basis and limitations.
7. **Historical reads never resolve to latest.** New publication/comparison
   leaves old observations and meanings unchanged.

The backend is trusted to establish mechanically extracted facts under declared
producer/capability semantics, corresponding qualified evidence and retained
occurrence identity. Verification checks these mechanical promises. It proves
neither extractor exhaustiveness beyond the declared universe nor source
authenticity, business truth, semantic correctness or warrant consistency.

## E. Minimal core requirements

### R1 — Exact retained occurrence access and qualification

An occurrence reference must be backend-unambiguous, stable for retained reads,
serializable as construction provenance, distinguish historically distinct
copies, and verifiable against the opened occurrence. Opening never substitutes
another occurrence. Unavailable/mismatched inputs fail explicitly.

Phase 4 needs exact P1/P2 basis entries even when local world-id/revision coincide.
Without this, W1 can appear to consume P2, or a copied P1 can collapse into P1.
Native: `PublicationRef(address, world_id, revision)` plus read-only open and
`verify_publication_ref`. A backend may use an opaque database/occurrence token.
An occurrence-address/content-replacement attack is not universally prevented
by this native triple; content evidence verification remains a separate check.

### R2 — Qualified observed-state descriptor

Within an opened occurrence, expose a stable snapshot/state token, source-state
revision qualification, declared observation scope and producer/capability
meaning sufficient to interpret the reads. The state token qualifies facts;
the source revision qualifies observations. Neither is historical occurrence
identity. Do not impose a cryptographic digest algorithm or ordering/currentness.
Keep the logical distinction exact historical occurrence / observed-state
qualification / source revision / entity local token without over-objectifying
it: no separately globally unique snapshot object, separate SourceState class
or snapshot-bearing entity ID is required. One opaque backend handle/context
may encode several distinctions as long as contradictory supplied
qualification cannot be silently accepted.

Phase 4 records a warrant snapshot and checks source observation revisions.
Without this, valid source bytes could be attached to the wrong observed state.
Native: single `program_snapshot`, snapshot id in grounding/receipt/manifest,
`source_state`, declared boundary, effective inputs and receipt metadata.

### R3 — Exact entity membership and mechanical kind read

Given an opaque entity token and opened snapshot context, establish whether it
is a member of that observed universe and, if so, return its declared mechanical
kind. Facts/evidence for nonmembers must not be returned as local facts. Tokens
remain stable within retained state. IDs need not encode state, language, path,
AST or name. Display labels are optional metadata, never identity. Membership +
kind is core because production Phase 4 relevance construction consumes kind;
display label / label discovery stays optional. No universal cross-language
kind ontology is required; backend adapters may need to expose declared
mechanical category semantics adequate for the consumer or refuse the use.

Phase 4 receives a selected E and constructs kind-based application relevance
rules. Without this, E1 can bind in P2 merely because a label matches. Native:
`program_entity`, `program_entity_kind`, optional referent labels. The current
retained read join is a clean entity-view extraction opportunity, not a mandate
to reproduce the join or to add discovery to core.

### R4 — Typed, qualified mechanical context/fact reads

Expose containment around E sufficient to recover the demonstrated ancestor
context. Applicable additional facts, if produced, preserve typed relation
identity, role names/order, entity versus literal/value types and resolution
qualification. Capability status accompanies or is accessible for the read.
No universal graph engine, flattened prose, or one method per native table.

Phase 4's default warrant records containment and reads invocation/resolution
views. Without roles, parent/child and call-site/target can reverse undetectably;
without qualification, unsupported extraction masquerades as no relations.
Native: `structural_context`, `relation_schema`, typed rows, `program_invokes`
and `program_resolution`. Core requires the containment capability used by this
slice. It does **not** require all backends to extract calls/types/imports or
produce the native descriptor; additional produced facts must be honest.
Containment production is the core demonstrated capability; invocation /
resolution / imports / types / calls production is not universally mandatory.
If invocation/resolution are exposed or consumed, their capability, scope and
unresolved semantics must remain honest. Do not promote them into mandatory
production families.

### R5 — Source observation access and exact reconstruction

The selected entity must expose one or more qualified source observations that
reconstruct its demonstrated source occurrence. Each identifies source,
revision and backend-interpretable bounded location (or whole-input extent).
Reconstruction verifies qualification and observed material, or explicitly
fails. Reading changed live material as retained evidence is forbidden.
R5 promises qualified reconstruction, not omniscient entity-manifestation
proof: reconstruction establishes revision, retained material and requested
valid extent under the declared evidence association. It does not
independently prove that any arbitrarily substituted valid extent is the
entity's true manifestation. A syntactically valid alternate extent within
the same retained revision (for example `bytes:0:6`) may reconstruct
successfully; that is a valid locator whose association to an entity depends
on the producer's declared evidence guarantee, distinct from an
invalid/unreconstructible locator which must fail.

Phase 4 reconstructs E1/E2 after workspaces disappear. Without this, the binding
has only a pointer-shaped program endpoint. Native: `SourceObservation`-shaped
records from referent SOURCE groundings and digest-checked retained bytes.
No universal requirement that every external stub or synthetic fact have a
contiguous body; its actual evidence extent and limitations must be declared.
No universal source-coordinate authentication mechanism is required.

### R6 — Capability, scope and completeness honesty

Expose produced/not-produced capability status, stable capability meaning,
covered scope, completeness basis and known gaps. Incomplete analysis,
boundary-only entities, unavailable inputs and unresolved outcomes must remain
inspectable when relevant. The semantic requirement is
unsupported/not-produced ≠ supported-empty. It does not mandate a universal
serialization such as `rows = None`: an honest `rows = []` with
`NOT_PRODUCED` and no closure/complete interpretation is permitted. Only a
supported + complete + empty presentation (or any closure claim) for an
unproduced relation is dishonest. Missing declarations confer no closure.
Behavioral qualification must distinguish supported complete, supported
incomplete, unsupported/not-produced and known gaps/out-of-scope where
relevant, without universally requiring native `completeness_receipt_refs`,
`descriptor.inputs` or `descriptor.losses` to be nonempty. Supported-empty
(supported capability, declared scope/completeness, zero rows) remains valid
and semantically distinct from incomplete-empty and unresolved.

Phase 4's empty invocation/resolution views must mean only what was observed;
they cannot imply semantic failure or universal absence. Without this, an
adapter silently strengthens a bounded observation into falsehood. Native:
`program_capability`, construction receipt, input dispositions, entity boundary,
resolution outcomes and known losses. Exact status names, enums and schemas
are not universal; test vocabulary projects backend signals into shared cases.

### R7 — Independent history and verification of declared evidence guarantees

Reads and comparisons preserve retained historical state. A later open returns
the same qualified facts/evidence, or explicitly reports unavailability/failure.
Verify occurrence qualification, descriptor/capability consistency and closure
of the observations promised reconstructible in the retained material being
verified. Verification must actually attempt evidence validation and report
failure on missing/tampered material. It is not an omniscient correctness test.

Phase 4 reads all five publications independently and verifies W1/W2 with
original inputs absent. Without this, producing P2 revises P1, or missing
evidence passes admission. Native: retained fresh bundles, read-only opens,
`validate_typescript_spine` and `verify_retained_program_inputs`; authority
verification composes the local closure check. Logical historical immutability
is required; physical bundle immutability, perpetual availability, retention
administration and native sealing mechanics are not universal requirements.

## F. Optional requirements

**O1 — Bounded discovery:** return snapshot-qualified candidate entities by
declared mechanical kind/display metadata, without selecting semantic meaning.
Phase 4 uses label discovery for fixture selection, but an explicitly supplied
E makes it unnecessary. Zero/multiple matches are meaningful. No search language,
globally unique label guarantee or label-based correspondence rule is required.

**O2 — Comparison service:** compare two exact occurrences only under declared
compatibility, expose mechanically qualified changes/correspondences, basis,
supporting evidence, limitations and ambiguity. Phase 4 Case G uses this signal;
W2 does not. Unsupported comparison leaves core conformance intact.

**P1 — Separate producer/indexing contract:** declared source scope/configuration
→ accepted retained occurrence plus inspectable receipt, or explicit failure.
Production is necessary to create the history, but no Phase 4 read consumer
requires ingestion through the same interface. A backend with externally
indexed, already-retained occurrences can satisfy the core read contract.
Producer-specific receipts should disclose scope, effective inputs, producer
semantics/capabilities and failures/gaps; no TypeScript/build-system schema is
universal. Construction/admission and fresh retention do not imply semantic
interpretation. No `BuildProgramSnapshot` operation is added to the reader.

## G. Native extras

| Audited native capability / output | Classification and reason |
| --- | --- |
| Exact membership/kind, snapshot/source revision, containment, selected-entity evidence, declared closure | DEMONSTRATED CORE |
| Kind/label discovery, rename correspondence and mechanical change signal | DEMONSTRATED OPTIONAL |
| Invocation/resolution production | NATIVE EXTRA production; Phase 4 consumes qualified views but the leaf has none; supported/unsupported honesty is core |
| Imports, declared type/extends/implements relations | NATIVE EXTRA; no Phase 4 binding behavior requires their production |
| Resolution candidate enumeration and external endpoint stub taxonomy | NATIVE EXTRA; ambiguity/out-of-scope honesty applies if exposed, not a required taxonomy or relation |
| Deterministic identity descriptors and descriptor-substring discovery | NATIVE EXTRA for reads; used internally by native comparison, no universal identity descriptor |
| `localize_source_range`, byte-offset arithmetic, UTF-16 conversion | NATIVE EXTRA; caller already receives selected E and reconstructs observations |
| Added/removed identity inventory, every relation delta, retargeting | NATIVE EXTRA comparison outputs; a bounded change signal suffices for Case G |
| Manifestation change | DEMONSTRATED OPTIONAL signal; no requirement for the complete native manifestation record schema |
| Split/merge groups, maintenance hooks, all property deltas | NATIVE EXTRA; no Phase 4 reconsideration dependency |
| Component-usage NOT_PRODUCED declaration | Honesty witness, not a required component-usage capability |

No FUTURE CANDIDATE feature is promoted to a requirement. Efficient structured
projection is a design constraint (§R), not speculative SQL/search machinery.

## H. Logical contract sketch

Language-neutral behavioral notation, not a committed interface:

```text
OccurrenceReference := serializable exact retained-occurrence qualifier
OpenedOccurrence := verified read context for that reference
Descriptor := snapshot token + source revision + scope + producer/capability declarations
EntityView := opaque local token + declared kind + optional display/boundary metadata
FactView := typed relation schema/roles + qualified observations + capability context
Observation := qualified source identity + revision + interpretable extent

open_exact(OccurrenceReference) -> OpenedOccurrence | explicit failure
describe(OpenedOccurrence) -> Descriptor
inspect_entity(OpenedOccurrence, entity token) -> EntityView | not-member
read_facts(OpenedOccurrence, selected entity, declared relation view)
    -> FactView | explicitly unavailable capability
source_observations(OpenedOccurrence, selected entity) -> Observation(s) | explicit failure
reconstruct(OpenedOccurrence/evidence context, Observation)
    -> verified observed material | explicit failure
verify_declared_guarantees(OpenedOccurrence/evidence context) -> result + diagnostics

optional discover(OpenedOccurrence, bounded kind/display selector) -> local candidates
optional compare(old exact context, new exact context)
    -> qualified compatibility + correspondence/change result | unsupported/refused
separate produce(declared source/config scope) -> retained reference + receipt | failure
```

These are logical operations; describing capabilities can be folded into a
descriptor or fact result. Verification can compose opening, descriptor checks
and reconstruction instead of being a backend method. Typed views may have
separate schemas, and snapshot context may qualify whole results rather than
every tuple inline. No universal method count or exceptions are settled here.
`read_facts`, `Descriptor`, `EntityView` and `FactView` remain notation, not
committed interface types or production classes. Minimality classifications:
OccurrenceReference KEEP; OpenedOccurrence, Descriptor, EntityView, FactView,
capability declaration and verification outcome FOLD; Observation KEEP;
discovery and comparison OPTIONAL; producer contract SEPARATE/OPTIONAL for
the reader. One opaque handle may encode several folded distinctions.

Each distinction has a concrete falsifier:

| Logical concept | What removal loses / Phase 4 case | Smaller representation permitted |
| --- | --- | --- |
| Occurrence reference / opened context | Copied input collapses; basis cannot name P1 rather than P2 (D/E) | One opaque reference plus verified read context; no persistent ProgramRef |
| Descriptor | Snapshot/revision mismatch undetectable (C/D/J) | One descriptor; source revision is a field, not a separate SourceState object |
| Entity view/token | E1 can be substituted in P2; kind-based relevance loses basis (C/D/E) | Token passed with context or internally qualified; no universal ID encoding |
| Typed fact view | Context loses endpoint direction; empty reads hide missing capability (C/K) | Typed schemas or views; no universal edge/fact record required |
| Observation | Cannot reconstruct E's exact revision/extent after source deletion (B/J) | Backend-native serializable locator; no universal coordinates or blob layout |
| Capability declarations | Empty/unresolved is mistaken for negative (K) | Descriptor/result metadata; no separate ProgramCapabilities class required |
| Verification outcome | Missing local SOURCE material accepted (J plus admission path) | Diagnostics from composed checks; no verification-object hierarchy |
| Optional comparison result | Case G loses a qualified signal | Service result qualified by caller's exact contexts; no new identity object |

Falsification mapping without `ConstructionWorld`, table rows, private labels,
SQLite or program-input directories: select E externally (or O1); R1/R2 record
the exact program basis; R3 validates E and supplies kind; R4 supplies context
and applicable qualified facts; R5 lets the application's evidence adapter
retain/reconstruct its selected basis; R7 verifies it later; O2 supplies the
optional signal. W0 reads and realization judgment stay in the semantic layer.
No config-route knowledge enters any logical operation. Consumer migration,
including materializing this basis instead of cloning the native bundle, is
Phase 5B work and is not implemented here.

## I. Failure / unknown semantics

States are semantic outcomes, not mandatory enums or separate exception classes.

| Situation | Required outcome | Forbidden translation |
| --- | --- | --- |
| Occurrence unavailable | Explicit failure to open exact retained input | Latest or equivalent copy silently substituted |
| Occurrence qualification mismatch | Reject exact-input qualification | Accept because content/snapshot token matches |
| Entity snapshot/occurrence qualification mismatch | Reject/not-member; no facts/observations for contradictory qualification | Accept because native token exists somewhere |
| Entity absent from opened universe | Not-member; reject its local facts/evidence | Resolve same label elsewhere; assert global nonexistence |
| Capability unsupported / not produced | Disclose absence of production and no closure claim; `rows=[]` with `NOT_PRODUCED` and no closure is honest | Supported + complete + empty, or any closure claim |
| Supported capability, fact not observed | Qualified empty result with scope/basis/gaps | Unqualified falsehood |
| Analysis incomplete / input unreadable | Disclose gaps and restrict closure | Complete universe |
| Resolution unknown / unresolved / multiple candidates | Preserve outcome/candidates when exposed; no selected target inferred | No invocation, or guessed unique target |
| Source/entity outside scope | Disclose boundary or lack of coverage; no in-scope exhaustive claim | Fully analyzed source |
| Evidence unavailable or corrupt | Reconstruction unverified/failed; closure verification fails | Live-source fallback or verified empty material |
| Invalid/unreconstructible locator | Fail reconstruction | Return other material as verified |
| Valid locator, entity association via producer guarantee | Reconstruct requested valid extent under declared association; association honesty is producer's guarantee | Claim omniscient entity-manifestation authentication |
| Observation revision/location mismatch | Fail reconstruction | Return another revision or extent |
| Comparison unsupported | Explicit unsupported result/service absence; core reads remain usable | Empty delta meaning no change |
| Comparison incompatible | Refuse or expose which claims/capabilities cannot be compared | Unqualified continuity/no change |
| Comparison ambiguous | Retain competing candidates or unresolved ambiguity; no unique continuation | Arbitrary winner or persistent identity |

The native reconstruct API returns `OK`/`FAILED`, not a rich error taxonomy.
Phase 4 requires verified versus unverified material and fail-closed closure;
missing/corrupt/mismatched evidence may share the latter outcome. Requiring
separate corruption/unavailability exception types would overconstrain the
evidence. Capability unavailability is distinguished before interpreting fact
or observation results. `KNOWN/UNKNOWN/NOT_SUPPORTED/OUT_OF_SCOPE` need not be a
single enum spanning unrelated operations.

## J. Capability / completeness model

Every supported inference from absence is relative to declared production,
scope, completeness basis and known gaps. Declaration can be shared at snapshot
level, with per-view attribution. Kinds and relations use stable declared
identifiers/semantics; there is no universal TypeScript enum. A consumer needing
the demonstrated callable category must recognize a declared equivalent
mechanical category or refuse that use; string equality alone is not adequacy.

Native `COMPLETE` covers its stated recognized source universe, not all program
behavior. `STATIC_COMPLETE` calls means recognized static call sites have
resolution outcomes; an unresolved site is not proof it invokes nobody.
`INCOMPLETE` records diagnostics/unreadable inputs as gaps. Receipt-only
`NOT_PRODUCED` has no completeness references. Missing capability declaration
provides no basis for negative conclusions. Nonempty
`completeness_receipt_refs`, `descriptor.inputs` and `descriptor.losses` are
native shapes, not universal requirements: a valid backend may have no known
losses, encode completeness without a receipt reference, or represent
effective input/scope metadata differently, provided behavioral checks still
distinguish supported complete, supported incomplete, unsupported/not-produced
and known gaps/out-of-scope where relevant.

Scope evidence includes declared boundary, effective input dispositions and
analysis/readability details, entity boundary markers and known losses. The
contract requires enough disclosure to prevent overclaiming, not a universal
build-system model or an exhaustive external inventory of excluded files.
The native source-state includes normalized configuration/boundary, and input
metadata distinguishes in-scope, external-boundary and analysis-support inputs.
An unreadable required evidence input can fail production rather than produce
an incomplete snapshot; either outcome must remain honest.

Current authority `optional_program_rows` can return `[]` for an absent relation;
its docstring correctly grants no semantic disposition, but that helper alone
is **not** a backend capability-honest read boundary. The test projection pairs
rows with production declarations. Extraction must preserve that pairing; this
phase does not alter the existing consumer or pretend it already uses a clean
backend API.

## K. Evidence model

Program facts and their evidence are distinct. The minimum path is selected
entity (or produced fact under a declared evidence guarantee) → qualified
observation(s) → verified reconstructed material. Source identity, revision
and interpretable extent are load-bearing; provider/path/digest spelling is not.
A whole-input occurrence is an extent too. The backend/evidence adapter owns
coordinate interpretation. Consumers need no UTF-8/UTF-16 arithmetic.

Selected source-backed entities must satisfy R5. A valid observation API must
not be reachable through an incorrectly qualified entity merely because the
native token exists somewhere: wrong-qualified entity yields no observations,
correct-qualified yields observations. More generally, verification covers the
backend's **declared** reconstructibility guarantees. Native promises retain
every emitted TypeScript identity/assertion SOURCE observation; its closure
verifier scans those provider-scoped groundings. This is not a universal
promise of a unique source range for every imaginable program fact, nor a new
per-fact witness interface. Native malformed/unrecognized grounding records are
not all authenticated by that closure helper alone; typed producer validation
and the declared provider contract delimit the claim.

Evidence may be retained bytes, indexed revisioned source, or another exact
reconstructible representation. It must remain usable independently of a mutable
workspace. The application's retained W1 evidence must not require P1 to be
available; qualified observed material/locators must permit its evidence adapter
to retain an equivalent reconstruction basis. No database-clone/export method
is forced. Inability must be exposed; a backend unable to reconstruct the
selected entity at all does not satisfy this demonstrated core use merely by
declaring evidence unsupported.

## L. Historical identity model

Use **one exact occurrence reference and one observed-state descriptor**.
There is no need for three new objects named ProgramOccurrence, Snapshot and
SourceState. Their distinctions are retained as context and fields:

- Occurrence identity names the historical retained input actually consumed.
- Snapshot token qualifies the mechanically observed state/entity universe.
- Source-state revision qualifies observed source/configuration state; equal
  revisions do not establish equal extraction semantics or occurrences.
- Entity identity is a local token interpreted within that qualified state and
  exact occurrence context. Labels are facts/display metadata, never identity.

Copied native publications can share snapshot/source-state tokens **and entity
tokens** while remaining distinct occurrences. Changed snapshots can have equal
labels and different local tokens. Neither token inequality on every copy nor
cross-snapshot ID stability is required. An ID may embed context or require it
as an argument, provided membership is verifiable and an unqualified local token
is never treated as universal identity. Compaction/storage changes are allowed
if retained reads preserve behavior; resolving to latest is forbidden.

## M. Comparison model

Optional service, with exact old/new occurrence qualification held in result
context or inline. A valid initial backend may declare it unsupported. Core
construction and evidence reads still run. The demonstrated result needs a
mechanical change signal concerning historical E, not every native delta field.

Native comparison preconditions audited in `_load_snapshot`, `_profile_metadata`,
`_compatibility` and `_capability_compatibility`:

- A valid manifest, one `spine_core/v1` snapshot, valid declared receipt when
  present, member relation endpoints and reconstructible entity source evidence.
- Equal extractor identity/version metadata, declared capability profile sets,
  coordinate conventions and boundary policies, and available identity
  descriptors. Different declared source boundaries are recorded as changed;
  they are not automatically incompatible under equal policies.
- Per-capability presence, production and matching versions; incomplete
  capabilities become partial. Unsupported/unproduced capabilities are not
  comparable. Analyzer/configuration equality is not separately demanded by
  the implementation; do not invent that precondition.

The general obligation is a declared compatibility decision and explicit
refusal/limitations, not those exact native metadata fields. Incompatible native
representation is reported in result context, restricts per-capability deltas
and prevents exhaustive added/removed inference for unmatched entities. Native
matching can still emit heuristic candidates/claims under that explicitly
incompatible context; it does not universally refuse the comparison. Individual
incomparable capabilities are reported even if other comparison remains useful.

Transferable optional comparison semantics (backend-neutral) require only
that a comparison service operates over exact caller-qualified old/new
occurrences, declares compatibility/refusal honestly, exposes the epistemic
basis it actually claims, preserves ambiguity when its own result is ambiguous,
does not collapse correspondence into identity, and does not mutate historical
occurrences. A valid future backend need not manufacture `HEURISTIC /
CONTINUED / RENAME` if it supports only different justified
correspondence/change evidence.

Native comparison regression (algorithm-specific, still tested): native rename
correspondence is `HEURISTIC`, with mechanical supporting rules, changes and
the limitation that heuristic correspondence is not mechanically entailed
identity continuity. `CONTINUED` never aliases E1/E2. Duplicate candidates
remain ambiguous, rather than a deterministic tie-break becoming truth. The
specific rename heuristic, two-candidate ambiguous scenario and native
compatibility behavior are native regression expectations, not universal
contract requirements. No scalar confidence is required. Native
identity/manifestation/relation/maintenance deltas are extras except the
bounded change information Case G actually reads.

Native comparison receipts qualify snapshot tokens, not exact publication
addresses. Therefore a caller must retain the exact opened pair as context;
the test-local fixture verifies those inputs and carries their serialized
references alongside the native result. This supplies missing *context*, not
stronger correspondence evidence. A context-free native comparison sidecar
alone cannot distinguish equivalent copied occurrences. The native result need
not itself duplicate full exact occurrence identity, provided invocation is
over exact verified contexts and the result remains associated with that pair:
`compare(P1-original, P2)` and `compare(P1-copy, P2)` retain distinct
caller-qualified occurrence context even with identical snapshot/entity tokens
and bytes. No persistent cross-snapshot identity is required. Phase 5B must
preserve this qualification without treating the native receipt as a universal
schema.

## N. Native Program Spine mapping

| Requirement | Native realization | Native-specific representation | Contract dependency |
| --- | --- | --- | --- |
| R1 exact open / qualification | Read-only World open, `PublicationRef`, `verify_publication_ref` | Directory address, local world id/counter | Exact serializable/verifiable occurrence identity |
| R2 descriptor | Snapshot row + grounding snapshot id, manifest and construction receipt | World snapshot referent, digest fields, JSON sidecars | Observed-state and source-revision qualification plus declared meaning |
| R3 membership/kind | Snapshot-filtered membership and kind rows; optional referent label | Separate tables and embedded TS snapshot ids | Local membership, stable local token, declared kind; display optional |
| R4 typed facts/context | `structural_context`, relation schemas/rows; invocation/resolution if produced | Typed World n-ary relations, REFERENT/TEXT roles | Direction/roles/types and qualified capability semantics |
| R5 observations/reconstruction | `program_source_observations`, `reconstruct_program_observation` | Provider handles, UTF-8 spans, retained digest-addressed blobs | Exact qualified source material, fail-closed reconstruction |
| R6 capability/scope honesty | Capability rows + receipt completeness references/basis/gaps, effective inputs, boundaries/resolution/losses | Native ids/statuses and sidecar shape | Produced differs from unproduced; scoped limits inspectable |
| R7 history/verification | Fresh publication + independent readers, `validate_typescript_spine`, retained-input verifier | Sealed read-only bundles and provider-specific closure scan | Stable historical behavior and verification of declared mechanical guarantees |
| O1 discovery | Candidate helper; retained membership/kind/label join | Private referent labels in current join | Qualified candidates, no identity/selection inference |
| O2 comparison | `compare_spines`, receipt, claims/delta; exact pair supplied by caller | Native metadata compatibility and full delta schema | Optional qualified signal, basis/evidence/ambiguity/limitations |
| P1 separate producer | `build_typescript_spine` with explicit boundary; validated receipt/publication | TS compiler, config, fresh bundle layout | Declared ingestion result and retained occurrence, independent of reader API |

This is an adapter sketch, not production adapter code. Missing clean entity
reads and comparison occurrence context are extraction tasks, not reasons to
change the frozen kernel or migrate consumers prematurely.

## O. Conformance tests

`tests/test_program_backend_conformance.py` runs behavioral assertions against
production outputs through `tests/program_backend_native_fixture.py`. The latter
contains only native setup, read projection, fault injection and comparison
context; no authority/config-route imports, protocol class or installed API.
Logical fixture role/status spellings are test vocabulary for these
cases, not mandated backend wire formats. Future fixtures can project different
representations into the same cases without changing expected semantics.
Source scenarios and damage mechanisms belong to fixtures; entity IDs remain
opaque in cases. Production extraction/reconstruction/verification/comparison
remain the actual implementations under test.

| Executable case (`test_` prefix omitted) | Dishonest behavior rejected |
| --- | --- |
| `exact_occurrence_is_not_content_equivalence` | Collapse copied occurrences; accept wrong local revision or unavailable occurrence; mismatch opened copy/reference; fail serializable exact-reference round trip |
| `wrong_snapshot_qualification_is_rejected` | Accept correct occurrence + wrong snapshot + valid token in inspect/facts/observations; reach observations through wrong-qualified entity |
| `copied_occurrence_does_not_accept_original_qualified_entity` | Accept original-qualified entity in an equivalent copy sharing snapshot/entity tokens and bytes; collapse EntityToken into QualifiedEntityOccurrence |
| `historical_reads_and_entity_membership_do_not_follow_latest` | Resolve old descriptor/membership/facts/capability/fresh observations/reconstruction to latest; substitute same-label E; depend on deleted workspace |
| `duplicate_labels_do_not_merge_entity_identity` | Treat display label as unique identity |
| `evidence_verifies_qualification_and_retained_closure` (missing/corrupt) | Accept wrong evidence revision; use live workspace to replace missing/tampered retained bytes; claim closure without reconstruction |
| `capability_not_produced_is_not_supported_empty` | Translate not-produced into supported + complete + empty or other closure claim; omit behavioral scope/basis qualification |
| `optional_produced_call_capability_can_be_empty` | Treat a supported empty call view as unproduced or omit its qualification; collapse supported-empty into unsupported/incomplete/unresolved |
| `typed_mechanical_facts_preserve_roles_and_snapshot` | Reverse containment roles, omit observed-state qualification, or lose the demonstrated ancestor source/module/context chain |
| `optional_produced_relations_preserve_entity_and_literal_roles` | Reverse invocation roles; flatten entity/text types; omit resolution qualification |
| `unresolved_and_incomplete_do_not_establish_negative_calls` | Erase unresolved outcomes/gaps while exposing empty invocation facts |
| `core_reads_do_not_require_comparison` | Couple core membership/context/evidence verification to comparison service availability |
| `optional_comparison_is_qualified_heuristic_and_read_only` (native regression) | Unqualified old/new pair; convert deterministic heuristic to entailed identity; lose changes/evidence/limitations; mutate input history |
| `optional_comparison_transferable_semantics_are_qualified_and_honest` | Unqualified pair; dishonest compatibility; hidden basis; correspondence-into-identity collapse; historical mutation; lost ambiguity |
| `optional_comparison_preserves_exact_occurrence_context_for_copies` | Collapse `compare(P1-original, P2)` and `compare(P1-copy, P2)` caller context despite distinct exact occurrences |
| `optional_comparison_preserves_ambiguity` (native regression) | Select one continuation under duplicate candidates |
| `optional_comparison_declares_incompatible_capability` (capability/representation; native regression) | Silently compare mismatched capability or extractor versions |
| `discriminating_assertions_reject_dishonest_empty_and_collapsed_copy` | Negative controls: honest `NOT_PRODUCED` accepts `None`/`[]` without closure; supported + complete + empty and collapsed copies fail |

There are 20 executed cases (evidence and compatibility each have two
parameters). Core cases do not call comparison. Optional comparison cases skip for a fixture declaring
unsupported comparison, while core cases still run. Native tests additionally
exercise produced invocation/resolution as typed/honesty witnesses; these do
not promote their production into required capabilities for all backends.
Discovery and extra relation-production cases explicitly skip when the fixture
declares them unsupported. Core cases receive an explicitly selected entity
from fixture setup; they do not require backend label discovery. The fixture
wraps local tokens with occurrence/snapshot context, allowing other backends
to reuse opaque token spellings across snapshots without creating identity.
A test-only `misqualify`/`forge_entity` constructor builds intentionally
inconsistent qualified references; production never forges. Native comparison
algorithm expectations (`RENAME`/`HEURISTIC`/`CONTINUED`, two-candidate
ambiguity, native compatibility) are classified as native regression; the
transferable optional contract requires only qualified invocation, honest
compatibility, exposed basis, preserved ambiguity, no identity collapse and
no mutation.

Closure status for the adversarial dishonest-backend matrix (all claimed
discriminators are executed above unless marked optional-service):

| Dishonest behavior | Must now reject? | Executable discriminator |
| --- | --- | --- |
| old reference opens latest wholesale | yes | `exact_occurrence_is_not_content_equivalence` |
| historical facts follow latest | yes | strengthened `historical_reads_and_entity_membership_do_not_follow_latest` |
| historical capability context follows latest | yes | same strengthened historical case |
| historical fresh observation lookup follows latest | yes | same strengthened historical case (fresh `observations` + successor locality) |
| copied occurrence collapsed | yes | `exact_occurrence_is_not_content_equivalence` + `copied_occurrence_does_not_accept_original_qualified_entity` |
| original-qualified entity accepted in copy | yes | `copied_occurrence_does_not_accept_original_qualified_entity` |
| entity lookup ignores snapshot | yes | `wrong_snapshot_qualification_is_rejected` |
| unsupported becomes supported-empty | yes | `capability_not_produced_is_not_supported_empty` + discriminating controls |
| incomplete becomes complete | yes | `unresolved_and_incomplete_do_not_establish_negative_calls` |
| evidence reads mutable workspace | yes | `evidence_verifies_qualification_and_retained_closure` + historical workspace deletion |
| wrong evidence revision accepted | yes | `evidence_verifies_qualification_and_retained_closure` |
| comparison ambiguity arbitrarily collapsed | optional-service semantic test | transferable comparison case + native ambiguity regression |

The default gate includes the new cases. Existing focused spine/comparison,
Phase 1 evidence and Phase 4 slice tests retain native-specific coverage,
including external-boundary input behavior; the new cases also exercise
representation incompatibility. The focused comparison run exposed one
pre-existing setup error: the added/removed test produced its second pair at
the first pair's retained addresses. Its second pair now uses a fresh `removed/`
scope. Assertions and production behavior are unchanged; both histories remain
retained.
The unchanged Phase 4 Case J is the production evidence for self-contained W1/W2
after original P1/P2 become unavailable; no new semantic consumer is constructed.

Validation on this branch (counts overlap):

```text
uv sync --locked --extra dev                         PASS
npm ci --prefix frontend                            PASS
new ProgramBackend conformance cases                 20 passed
focused comparison + Phase 1 evidence + Phase 4
  + new conformance cases                            57 passed
default repository gate (includes native TS spine)   156 passed
Core v1 acceptance command                           18 passed
conformance with comparison disabled                 14 passed, 6 skipped
conformance with discovery disabled                  19 passed, 1 skipped
Mutant A (ignore snapshot + latest facts)            3 failed, 17 passed (caught)
Mutant B (no envelope guard + latest facts)          4 failed, 16 passed (caught)
npm run build --prefix frontend                      PASS; no generated asset diff
uv build                                            PASS; sdist and wheel
git diff --check                                     PASS
```

Adversarial closure mutants (temporary `/tmp` monkeypatches, not committed):
Mutant A fails `wrong_snapshot_qualification_is_rejected`,
`historical_reads_and_entity_membership_do_not_follow_latest` and
`core_reads_do_not_require_comparison`. Mutant B additionally fails
`copied_occurrence_does_not_accept_original_qualified_entity`. Both mutants
passed the pre-closure 16-case suite; neither passes the 20-case suite.

Focused command:

```sh
uv run --extra dev pytest -q tests/test_program_backend_conformance.py \
  tests/test_program_spine_comparison.py \
  tests/test_phase1_program_observation_conformance.py \
  tests/test_phase1_program_capture_conformance.py \
  tests/test_phase4_vertical_slice.py
```

No live-model experiments or archived/private artifacts were needed. This is
the default gate plus the named focused regressions, not the entire historical
research suite. No production or bundled-asset changes are included.

## P. Deletion / minimality audit

Delete each retained operation: without exact open, history can substitute;
without descriptor, source/snapshot mismatch passes; without entity inspection,
selection/kind loses its mechanical basis; without typed context, the generated
warrant loses its structural basis; without observation/reconstruction, Case J
loses exact source evidence; without declarations, empty reads become dishonest;
without verification/history guarantees, retained closure/stability is merely
asserted. These dependencies force R1–R7, not seven production methods.
Kept review deletion result: OccurrenceReference KEEP; OpenedOccurrence,
Descriptor, EntityView, FactView, capability declaration and verification
outcome FOLD; Observation KEEP; discovery and comparison OPTIONAL; producer
contract SEPARATE/OPTIONAL for the reader. The language-neutral logical sketch
is not turned into production classes.

Candidates removed from required core during derivation:

| Removed proposal | Why no demonstrated core consumer forces it |
| --- | --- |
| `BuildProgramSnapshot` on reader | Setup needs production, readers need accepted occurrences; separate producer receipt suffices |
| Mandatory search/list-all/label lookup | Binding receives selected E; fixture selection is optional discovery |
| Mandatory label field or globally unique name | Kind and membership suffice; duplicate labels are legitimate |
| Universal `ProgramRef` | No consumer refers to a persistent abstract program; exact occurrence/entity/source references suffice |
| Separate ProgramOccurrence/Snapshot/SourceState object classes | Exact reference/context plus descriptor fields preserve distinctions |
| Universal closed kind enum / TS ID descriptor | Only declared mechanical category meaning is required |
| One method per table / generic graph or SQL query language | Bounded typed context/fact views suffice |
| Giant normalized fact record with all metadata inline | Context/schema can qualify typed tuples without duplication |
| Universal graph edge with two endpoints | Resolution includes typed literals and other views can be n-ary; preserve roles instead |
| Universal source-coordinate arithmetic / path / blob digest | Evidence adapter reconstructs native qualified extents |
| Full publication/database clone/export | Application can retain selected basis through structured reads and evidence; native clone is implementation |
| Rich reconstruction exception hierarchy | Verified versus failed meets demonstrated admission/read dependence; capability distinction remains separate |
| New capability/scope/verification object hierarchy | Descriptor/view metadata and composed verification outcomes suffice |
| Mandatory calls/imports/types/candidates/descriptors | No leaf binding needs their production; honesty governs them if present |
| Comparison in core | W2 is constructed without Case G; service optional |
| Full ProgramDelta, split/merge, maintenance engine, scalar confidence | Case G needs a bounded qualified change/correspondence signal |
| Semantic support/standing/currentness or warrant-consistency validation | These are application admission responsibilities, not mechanical program state |

Overconstraint falsifier: opaque IDs with external snapshot context, revisioned
indexed source instead of blobs, logical retained databases instead of bundles,
and typed views instead of SQLite rows all preserve R1–R7. None is excluded.
Honest `rows = []` with `NOT_PRODUCED` and no closure, empty losses, and
completeness without receipt references are permitted; only supported +
complete + empty for unproduced relations is rejected. Underconstraint
falsifiers are exercised by cases in §O: wrong snapshot/occurrence reads,
copied-occurrence token collision, historical fact/capability/fresh-observation
following latest, live workspace evidence fallback, unsupported-empty
translation, heuristic identity collapse and ancestor-context loss cannot pass.
The test projection does not certify every native API independently; it shows
the existing production outputs contain the required information/behavior.
Every normalized value remains a mechanical projection of native production
state; the fixture was not made smarter merely to pass tests.

## Q. Glean questions generated by the contract

Questions for the later conformance phase, not evaluated here:

- Can an exact retained/indexed occurrence be distinguished from equivalent
  copies and serialized/verifiably reopened without latest substitution?
- Can observed-state/source-revision descriptors and independent historical
  reads preserve the required qualification and capability scope?
- Can a local entity be inspected with membership and declared kind, without
  relying on universal identity or label equality?
- Can typed containment/context and produced mechanical facts retain roles,
  literal types, resolution uncertainty and capability attribution?
- Can selected-entity source observations reconstruct exact retained material,
  fail on mismatch/corruption, and support an application's independent evidence
  retention when the original indexed occurrence is unavailable?
- How are unsupported/not-produced capabilities, incomplete scopes and boundary
  limits distinguished from supported empty observations?
- Can declared evidence closure and descriptor/capability consistency be
  verified mechanically? If optional comparison exists, does it declare
  compatibility, exact contexts, basis/evidence, limitations and ambiguity?

No assumptions about predicates, query syntax, database handles or identifier
layout follow from these questions.

## R. Code Explorer implications

The contract contains only mechanical program state and evidence; it appears
independent enough for a future program-only reader. Preserve structured,
inspectable roles/values so relational projection need not re-extract source.
This is a design constraint, not a SQL API, new product, repository fork or
efficiency guarantee. No Code Explorer work occurs in Phase 5A.

## S. Final verdict

> Has Phase 5A derived a minimal backend-independent behavioral contract from demonstrated program-state demands, with executable native conformance tests, without baking in Ontology Author semantics, TypeScript implementation details, Glean assumptions, or speculative future features?

```text
YES — READY TO EXTRACT PROGRAMBACKEND AND TEST NATIVE CONFORMANCE
```

This verdict means requirements plus executable evidence are ready for
adversarial review. It does not claim a production ProgramBackend exists or
that Glean conforms. Required sequence remains Phase 5A derivation → review →
Phase 5B extraction and native conformance → Phase 6 Glean conformance.
