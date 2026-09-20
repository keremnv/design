# Governance mapping onto the Ontology Author kernel

This is an anti-footgun guide for future governance work. The current kernel
is a generic durable semantic-world substrate. Similar names do not imply
identical architectural meaning. Governance may use the substrate, but these
notes define the limits of each reuse.

## Mapping table

| Kernel concept | What it actually provides | Governance use | What governance must not infer |
|---|---|---|---|
| `REFERENT` | A thin stable string handle. Relation roles of type `REFERENT` are foreign-key checked. | Store constructed semantic referents and mechanically derived program referents. Store source-native referents only when the provider supplies useful object identity. | Generic storage does not make source, semantic, and program identities interchangeable. An addressable source region need not be a referent. A referent is not a property-bearing object or a real-world entity by default. |
| native spine core and capabilities | The application-level spine contracts define the meaning and integrity obligations of mechanically recovered program identities and relations; the World supplies storage and admission. | Encode declared spine capabilities with ordinary referents, typed relations, grounding, capability records, and construction receipts. | A profile or receipt does not make unsupported program facts true, complete beyond its declared basis, or adequate for every governance purpose. |
| `SourceObservation` | A provider, native handle, source revision, native location, and optional payload describing an observation. | Address the exact source evidence region that supports a claim or describes a source-native object, and make reconstruction possible. | It primarily addresses evidence. It is not automatically the persistent identity of the source-side thing, and it does not create a source referent merely by being addressable. |
| `AssertionGrounding` / `Grounding` | Grounding stores compact pointers on referents or assertions. `Grounding` has `SOURCE`, `WORLD`, `ASSERTION`, and `DERIVATION` kinds. `AssertionGrounding` packages observations, construction method, and extra metadata. | Preserve evidence for claims, identity-resolution context, construction/support context, and later derivation or assertion links. | Grounding does not confer governance authority or prove a proposition. A `WORLD` grounding is not a source authority declaration. |
| governance claim / proposition | The generic kernel has no separate `Claim` primitive. A claim is currently represented by an assertion tuple in a named typed relation, with its grounds stored separately. | Treat propositions as conceptually distinct from the source, semantic, and program identities that participate in them. Preserve precise relation names and n-ary roles. | A relation row is not an entity, and a source region that grounds a claim is not thereby one of the claim's referents. |
| `ConstructionOrigin.MECHANICAL` | One support/construction path was marked mechanical by the constructor. | Record a coarse support-path summary where useful. | It is not proof that the external fact is true or source-native in the governance sense. |
| `ConstructionOrigin.SEMANTIC` | One support/construction path was marked semantic; the current kernel treats this as a coarse path origin. | Use as a compatibility/storage signal alongside finer governance metadata. | It is not the complete epistemic classification. It must not erase `source_explicit`, `cross_evidence_inferred`, `hypothesized`, or referent-resolution detail. |
| `ConstructionOrigin.DERIVED` | A relation row was materialized by a registered deterministic derivation. | Preserve the derivation path and its inputs. | Deterministic computation from an inferred premise is not independent mechanical truth about reality. |
| `ConstructionOrigin.ADJUDICATED` | A constructor can label a support path as adjudicated. The current kernel does not turn this into a general adjudication record or authority model. | Treat as a coarse compatibility label only. Case-local interpretation is `GovernanceAdjudication` in [`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md). | The label does not establish who adjudicated, what authority they had, or what bounded case they saw. |
| `BASE` assertion | A manually asserted tuple in a `BASE` relation. The tuple is stored in a typed relation and receives `ASSERTED` assertion bookkeeping. | Store durable claims, including claims relating source-native, semantic, and program identities. | `BASE` does not mean source-native, authoritative, true, normative, or globally complete. |
| `DERIVED` relation | A relation that cannot be manually asserted; a registered `SELECT`/`WITH` query materializes it from declared inputs. | Compute repeatable selections and consequences after their premises are persisted. | `DERIVED` does not mean mechanically obtained from external reality, and it does not remove the provenance of inferred inputs. |
| `WORLD` scope | In the current runtime, an admission scope in `ConstructionWorld.admission`, persisted in `world.admission.json`; it is not a generic relation field in the core SQLite schema. | Mark records admitted as part of the reusable semantic World. | It does not mean global truth, authoritative material, program-spine state, or corpus-wide coverage. |
| `PURPOSE` scope | The other current runtime admission scope. Purpose checks are ordinary application relations and may be emitted by `Purpose`. | Keep purpose-specific requirements or unresolved records separate from reusable World content where that is the construction choice. | It does not automatically mean ephemeral adjudication state. A purpose-scoped record can still be durable within a World. |
| `COMPLETE` / `INCOMPLETE` / `UNKNOWN` | A derivation run records a completeness receipt relative to a named universe, basis, known gaps, inputs, and execution state. A derived universe must itself be current and explicitly complete before supporting exhaustive negative reasoning. | State exactly what a deterministic computation covered and prevent unsupported negative conclusions. | `COMPLETE` is only relative to its declared universe and run. It does not mean every authoritative file or source region was semantically processed. |
| unresolvedness | The generic kernel has no universal unresolved proposition primitive. The current `Purpose.unresolved` helper records an ordinary `PURPOSE` relation, commonly `purpose_requirement_failure`, with explicit failure data. | Preserve insufficient evidence, ambiguity, and purpose-relevant missing distinctions explicitly. | An empty query is not an unresolved record by itself, and unresolvedness must not be silently converted to false, irrelevant, or a forced entity match. |
| staleness | The kernel detects stale derived relations from relation versions, derivation definitions, and recorded input dependencies. | Recompute deterministic relations when their World inputs change. | Relation-level staleness does not detect every source, program, adapter, resolver, or semantic invalidation governance will need. |
| World revision | A monotonically increasing mutation counter in `_world_meta`; relation versions support derivation dependency checks. | Identify changes within one construction/database artifact and support reproducibility diagnostics. | It is not a source revision, program revision, adapter revision, semantic lineage identifier, or external validity timestamp. |
| sealed World | A validated candidate directory is copied, made read-only, and atomically replaces the current bundle; consumers read the sealed artifact. | Preserve candidate -> validate -> sealed lifecycle and failed-rebuild isolation. | Sealed means immutable and accepted as an artifact. It does not mean current relative to external state. |
| assertion identity | A content-addressed ID derived from the relation name and complete normalized tuple. Multiple grounds can converge on one assertion ID. | Treat claim identity as stable within the chosen relation representation and retain multiple support paths. | It is not necessarily independent real-world proposition identity, source identity, semantic identity, or program identity. Changing tuple representation changes the assertion identity. |
| experimental `Contract` | A small executable admission policy bound to a World revision. It currently checks provenance, scope, selected origins, and some semantic-reference permissions; it is not a general contract language. | Reuse the idea of a fail-closed admission seam if an application needs one. | Do not silently turn its terminology or fields into the future source/adapter contract model. Its `contract_revision` is not source or program revision. |
| experimental `Obligation` | A durable question with a Contract identity and optional reason. | It may be useful as an application record for a governance question or case demand. | It is not automatically a source requirement, policy obligation, adjudication case, or program-spine fact. |
| experimental `Commitment` | Provisionally, an addressable assertion ID used as a candidate answer. | Use the content-addressed assertion as a candidate semantic claim only if the governance application chooses that representation. | A Commitment is not a new independent proposition identity and must not be confused with a source commitment, implementation commitment, or adjudicated decision. |
| experimental `Candidate` association | Kernel bookkeeping connects an Obligation to an existing assertion without making a semantic relation. | Keep candidate selection metadata separate from domain relations when appropriate. | Candidate association is not semantic correspondence, authority, adjudication, or proof of applicability. |
| experimental `Resolution` | Runtime-derived current read state for an Obligation, with candidate assessments and status; the public World layers do not expose a general resolution writer. | Study the separation of selection/evaluation from construction. | It is not the future adjudicator, policy engine, or authoritative governance decision model. |
| experimental `Adjudication` | An immutable recorded selection of an existing candidate, with an external `source_id` in its authority basis; standing is assessed from separate configuration. | Reuse the separation between a recorded decision and the authority used to assess it. | Recording a kernel adjudication does not grant authority, establish truth, or define `GovernanceAdjudication`. Do not retrofit the governance-adjudication contract onto this type. |

## What is especially valuable to preserve

The following kernel properties align closely with governance needs:

- generic thin referents, so identity planes can remain application-defined;
- typed n-ary relations, including precise domain-specific relation names;
- content-addressed assertion identity;
- multiple grounds for one semantic assertion;
- reconstructible source observations rather than copied source bodies as the
  only evidence path;
- deterministic derivations with declared inputs;
- dependency and staleness handling for those derivations;
- explicit completeness receipts with a declared universe;
- explicit unresolvedness as an ordinary but inspectable construction result;
- candidate -> validate -> sealed World lifecycle with failed-rebuild
  isolation; and
- direct SQLite/Python computation for inspection and deterministic selection.

Also preserve the current separation between exact derivation dependencies and
candidate supporting evidence. A derivation's declared inputs determine what
must be recomputed; supporting grounding explains why a claim was accepted.
Those are related but different graphs.

## Exact, partial, and absent mappings

### Maps closely or exactly

The current kernel can represent durable thin referents, typed precise
relations, claim tuples with assertion identity, multiple groundings, source
observation pointers, deterministic SQL derivations, input-dependent
staleness, completeness receipts, open-world absence, explicit
construction-time unresolved records, revision counters, and immutable sealed
artifacts.

These are substrate capabilities. Their governance interpretation still needs
the identity-plane and authority boundaries in the foundations document.

### Maps only partially

Identity-plane separation, original-authority preservation, epistemic origin,
referent-resolution status, intelligent inference lineage, maintenance against
external state, and case-selection support can be represented using generic
referents, relations, groundings, and sidecars, but the current kernel does not
enforce their complete semantics.

Program-universe membership is also application structure rather than generic
referent existence. The kernel can store an explicit `program_entity` relation
and enforce its referent endpoints, but `_world_referents` alone is not a
complete program universe. Existing completeness receipts attach to derivation
runs, so base mechanical enumeration needs a governance admission receipt or a
derived materialization strategy.

`WORLD` and `PURPOSE` scope are runtime admission metadata rather than generic
kernel semantics. `COMPLETE` is scoped to a computation's declared universe.
`SEMANTIC` is a coarse support origin. Relation staleness covers deterministic
World dependencies only.

### Does not exist yet

The program spine exists as application contracts and a TypeScript extractor.
Cross-snapshot comparison exists as an application sidecar. Authoritative-source
construction exists as an application contract in
[`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md)
and a v0 implementation in `ontology_author.authority`. Attachment maintenance
and governance-case assembly exist as application contracts and v0 sidecar
writers in
[`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md) and
[`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md). They are not
kernel primitives. Change-impact (`AuthorityChangeImpact`) is part of that
case-assembly design, not a kernel relevance score. Governance adjudication
exists as an application contract in
[`GOVERNANCE_ADJUDICATION_CONTRACT.md`](GOVERNANCE_ADJUDICATION_CONTRACT.md).
It is not implemented in this milestone and is not a kernel primitive.
Experimental kernel `Adjudication` is not that contract.

The current implementation does not provide additional source drivers, an
autonomous constructor, source revision comparison for governance, semantic
traversal, an adjudicator runtime, governance policy, or a universal identity
reconciliation service. The kernel still has no Claim primitive,
authority-standing field, or lineage primitive, and those remain application
concerns until a concrete correctness need appears.

Those absences are deliberate at this milestone.

## Terminology hazards

Future agents should stop and check the mapping before reusing any of these
words:

- `referent` is a generic storage handle, not automatically a source region,
  source-native object, semantic identity, or program identity;
- `source` in `SourceObservation` identifies an evidence provider and
  addressable observation, not governance authority or a persistent source
  referent;
- `claim` or `proposition` is conceptually distinct from the identities that
  participate in it, even though the current kernel stores it as an assertion
  tuple;
- `grounding` means support addressing, not truth or normativity;
- `mechanical` in `ConstructionOrigin` is a construction-path label, not a
  guarantee about external reality;
- `semantic` in `ConstructionOrigin` is not the governance epistemic model;
- `derived` means derived from recorded World inputs, not independent machine
  observation;
- `WORLD` sounds global but is only current runtime admission scope;
- `PURPOSE` sounds temporary but may be durable purpose-relative state;
- `complete` sounds corpus-wide but is relative to one declared universe and
  receipt;
- `stale` currently describes derivation dependency state, not all external
  semantic drift;
- `revision` is a World mutation revision, not a source or program revision;
- `sealed` means immutable artifact, not current model;
- `assertion_id` is a semantic tuple hash, not necessarily a real-world
  proposition ID; and
- `Contract`, `Obligation`, `Commitment`, `Resolution`, and `Adjudication` are
  experimental application terminology and must not silently define future
  governance contracts or policy objects.

## Deliberate non-changes at this milestone

No generic kernel schema or lifecycle was changed. In particular, this task
does not add identity-plane columns, authority fields, epistemic-origin
primitives, referent-resolution primitives, external-validity state, source or
program revision fields, adapter tables, traversal APIs, case tables, or
adjudication policy. The governance layer should first demonstrate a concrete
correctness need before promoting any of these to generic primitives.
