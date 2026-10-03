# Model evolvability and vestigial architecture audit

Status: independent architecture/product audit, 2026-09-28.
Not architecture authority. Not cleanup authorization. Not an
implementation plan. Frozen product baseline: `e189198f`. No code was
modified, deleted, or committed for this audit; all experiments ran as
`/tmp` probes against real primitives.

Working hypothesis under test: a World is a durable, inspectable
representation of how evidence was understood under one
constructor/profile at one point in time, and model evolution equals
constructor evolution plus fresh immutable publication.

## 1. Executive conclusion

The replaceable-model thesis holds for everything the frozen product
does today. Six experiments (A–F) against real construction primitives
prove constructor correction, constructor expansion, entity split,
entity merge, concept abandonment, and late semantic-identity
introduction each work by publishing a new sealed World, with prior
Worlds untouched and no migration machinery. No experiment required
mutating W0, schema migration, or ontology-evolution machinery.

The repository simultaneously carries substantial vestigial
architecture: three whole packages (`authority/`, `semantic_binding/`,
`governance/`) have zero production importers, a model-backed
governance CLI ships as a first-class console script, every sealed
World carries four empty obligation/adjudication tables because
`Kernel` unconditionally instantiates `ContractWorldStore`, and 121
test files exist against an 8-file default gate. None of this is on
the frozen product path, but the old stack contains genuinely reusable
ideas — above all `program_spine/comparison.py`'s epistemic
correspondence pattern — that must be mined, not deleted with the
machinery.

## 2. Frozen product dependency closure

Traced from `construct_config_world`, `inspect_*`,
`judge_config_world`, `investigate_config_world`, and J0/I0
persist/verify. The live path imports exactly:

```text
config_routes/* (self)
software_governance/* + judgment/* + investigation/* (self)
evidence/{markdown, program_source}
world/core/{model, origins, source} (+ store/kernel/contract via runtime)
world/runtime/{world, commit}
```

Classification of top-level `ontology_author/` packages:

| Package | Classification | Evidence |
|---|---|---|
| `config_routes/` | LIVE PRODUCT | Facades themselves |
| `software_governance/` | LIVE PRODUCT | Construction/reads/validation/judgment/investigation |
| `evidence/` | GENERIC SUPPORT | Only `markdown`, `program_source` imported |
| `world/` (partial) | LIVE + LEGACY MIXED | Live: `runtime/world.py`, `runtime/commit.py`, `core/{store,kernel,model,contract,origins,source}`. Legacy-but-import-coupled: `runtime/{entry,project,purpose,resolution,source_helpers}`, `workspaces`, `explorer`, `cli`, `server`, `core/resolution`, `core/contract_store` (obligation tables), `runtime/construction_receipt`, `runtime/material_support` |
| `program_spine/` | RESEARCH, POTENTIALLY REUSABLE | No production importer; used by tests/fixtures and the repo-only `software_governance_v0` profile |
| `authority/` | LIKELY VESTIGIAL | Zero production importers; tests only |
| `semantic_binding/` | LIKELY VESTIGIAL | Zero production importers; tests + repo-only profile only |
| `governance/` | LIKELY VESTIGIAL | Zero production importers; tests only; ships a model-backed CLI |

Two coupling subtleties. First, `world/__init__.py` and
`world/runtime/__init__.py` eagerly import legacy modules (`entry`,
`project`, `purpose`, `resolution`, `workspaces`), so every live
process loads them even though it never calls them
(`ontology_author/world/runtime/__init__.py:11-20`). Import-coupled,
not behavior-coupled. Second, `ConstructionWorld` wraps `Kernel`,
which unconditionally builds a `ContractWorldStore`
(`ontology_author/world/core/kernel.py:47-54`), so every publication —
including frozen W0s — physically contains empty
`_world_obligations`, `_world_obligation_candidates`,
`_world_resolutions`, `_world_adjudications` tables (verified by
sqlite inspection in Experiment A). Structurally coupled residue.

Packaging (`pyproject.toml`) ships all of `ontology_author*` plus
console scripts `author` (`world/cli.py`, project-local Worlds) and
`governance` (`governance/cli.py`, explicitly "model-backed
GovernanceCase adjudication"), package data for the bundled inspector
(`world/static/**`) and `program_spine/*.js`, and runtime dependencies
`starlette`/`uvicorn`/`requests` that serve only the read-only World
HTTP server. Unused-by-product but not all obsolete: the server and
inspector are legitimate developer convenience; the `governance`
script and spine JS are old-application surface with no frozen-product
consumer.

## 3. What our entities actually are

Inventory from code, frozen product only:

| Identity | Created by | Scope | Sameness | Cross-World? |
|---|---|---|---|---|
| World (address + world_id + revision + fingerprint) | Constructor at fresh address | Publication | Exact resolved address + id + revision + bytes | New address = new publication, always |
| Snapshot `snapshot:{docDigest32}` | Producer (`producer.py`) | Publication | Doc bytes digest | Same bytes → same string; a coincidence, not a promise |
| Subject `route:{digest16}:{routeId}` | Producer (`producer.py:138`) | Snapshot | Doc digest + record id | Deterministic; no continuity promised |
| Manifestation (canonical bytes + digest) | Producer | Publication | Content digest | Content-addressed; comparable, not linked |
| Proposition `proposition:{slug}-route` | Profile rules (`rules.py:141,145`) | Interpretation | Classified route reference | Deterministic from evidence+rules |
| Referent (kernel string + label) | `add_referent` | World | String equality in-World | No |
| Assertion (`assertion_id` stable digest, `store.py:437`) | `assert_tuple` | World | Tuple content hash | Same tuple → same id; enables comparison, promises nothing |
| Case (`case_id`, default P::S) | Judge/assembly | Publication + request | Bound to world address + fact multiset | Reassembled per World, never ported |
| Artifact (method id/version/fingerprint) | Evaluator | Compatible installed code | Exact replay equality | No historical semantics archived |
| Investigation records (question/receipt/proposal ids) | Investigator | Sidecar + World | Deterministic from trigger case | Replay-verified, never established |

Identity-vs-representation separation is clean where it matters:
evidence location (spans/handles) ≠ referent string ≠ manifestation
bytes ≠ assertion (tuple + grounding) ≠ continuity (which does not
exist on the live path). Live-path "correspondence" always means
within-World proposition↔subject correspondence
(`software_governance/construction.py:322`), never cross-revision
lineage — no lineage/correspondence machinery exists outside
`program_spine/comparison.py` and research experiment docs. Known
conflations: subject IDs fuse document digest with record id
(location-flavored identity, but honest and snapshot-local);
proposition IDs bake profile interpretation into the string
(rewording changes identity — correct under the replaceable-model
thesis, wrong under a canonical-ontology theory);
`SemanticRefKind(COMMITMENT/OBLIGATION)` (`model.py:21-25`) hardcodes
one application's vocabulary into the generic kernel enum and is used
only by legacy `project.py`, `contract_store.py`, and two old tests —
historical application residue, not a generic requirement.

## 4. Constructor-as-model-program analysis

The statement "the constructor is the executable current theory of
what entities, relations, and distinctions matter" accurately
describes the frozen path. Model authority locates precisely:

```text
evidence adapter  bytes + spans only, zero meaning (evidence/*)
producer          mechanical records, subject/manifestation IDs, spans (producer.py)
constructor       relation schemas, referents, grounding, completeness, seal
profile rules     meaning: binding rule, evaluator, investigator, proposition slugs
generic machinery establishment mechanics without domain semantics (software_governance/*)
Core              storage primitives + Contract grounding enforcement (BASE needs SOURCE grounding)
```

Nothing above the profile rules assigns semantic standing; nothing
below them understands the domain. The one surprise is how much
meaning already lives in deterministic profile code: proposition
identity, evaluator coverage, and investigation relevance are all
plain functions of evidence, which is exactly why constructor
revision is sufficient for the evolution classes below.

Model revision taxonomy vs. current architecture:

1. Constructor correction — demonstrated (Exp. A). W1 differs in
   asserted values; W0 stays inspectable; nothing missing.
2. Constructor expansion — demonstrated (Exp. B). W1 gains relations;
   W0 valid; readers ignore unknown relations naturally.
3. Interpretation revision — demonstrated (Exp. A is also this: same
   evidence, new verdicts). Nothing missing.
4. Entity-boundary refinement — demonstrated both directions
   (Exps. C, D). W1 must not pretend the old boundary persists; it
   doesn't unless asserted. Nothing missing.
5. Evidence evolution — already the normal case (Phase 3 W0→W1 loop):
   new evidence, fresh address, rediscovered IDs. Nothing missing.
6. Vocabulary/schema revision — demonstrated (Exp. B adds a relation
   and roles). Readers select relations by name; old Worlds unaffected.
7. Persistence promotion/demotion — demonstrated both directions
   (Exps. E, F). Demotion needs no tombstone; no consumer requires one
   today. Promotion needs no prior placeholder.

## 5. Model evolution experiments

All against real primitives (`construct_config_world` with patched
producer functions for A/B; `ConstructionWorld.create/open`,
`add_referent`, `declare_relation`, `assert_tuple`,
`relation_rows` for C–F). No production file modified
(monkeypatching in-process only, restored in `finally`).

- A — constructor correction: buggy producer lowercased handlers →
  W0 judged `DOES_NOT_APPLY` (wrong); corrected constructor, same
  evidence → W1 `APPLIES/CONFORMS`. W0 still inspects and judges.
  No migration mechanism used or needed.
- B — constructor expansion: v1 producer additionally asserted
  `config_owner(subject, owner)` with SOURCE grounding. W1 carries
  the relation plus one row; W0 lacks it entirely; both judge
  identically. "Expand constructor and republish" is sufficient.
  Side finding: the default Contract rejects ungrounded BASE
  assertions (`ContractAdmissionError`), so expansions must ground —
  a genuine Core guarantee doing its job.
- C — split: W0 `serves(svc-billing, invoicing)`; W1 serves rows for
  `svc-billing-api` and `svc-billing-worker`, with no row pretending
  the unitary service persists. W0 intact.
- D — merge: W0 flags on `a` and `b`; W1 flags on `c`. Nothing
  prevents it; W0 intact.
- E — abandonment: W1 simply omits the `dropped` relation. Reads of
  W0 still return its rows; reads of W1 raise unknown-relation. No
  tombstone, no consumer breakage.
- F — late identity: W0 relates evidence to `subj-1` directly; W1
  adds referent `capability:export` plus `realizes` rows. Semantic
  identity introduced with zero W0 cooperation.

Pressure test (§18): "what did W0/W1 believe" is answered today by
opening each World and reading rows. "What did A become in W1" has no
answer anywhere on the live path — no lineage table, no API, no
convention — and constructing one would be new machinery. That gap is
real but currently consumerless: no frozen behavior asks the
became-question.

## 6. Cross-revision correspondence findings

`program_spine/comparison.py` (1976 lines) is the repository's only
implemented correspondence system, and its strongest contribution is
epistemic discipline, not matching code: deterministic sidecar output
(`spine.comparison.json`) that is explicitly "not a sealed World, not
a kernel lineage primitive, and not a second truth system"; continuity
vocabulary `CONTINUED/AMBIGUOUS/UNRESOLVED/NO_MATCH`; outcome
vocabulary through `RENAME/MOVE/SPLIT/MERGE/DELETED/NEW`; basis
classes `DETERMINISTIC/HEURISTIC/OBSERVATIONAL` separating
reproducibility from entailment; validation rules (e.g. AMBIGUOUS
requires candidates, CONTINUED forbids DELETED/NEW). The TypeScript
matcher itself is application-specific and must not become generic
mechanism. Research experiment records
(`CONFIG_ROUTE_CORRESPONDENCE_CONTRACT_EXPERIMENT`,
`SOFTWARE_SUBJECT_CORRESPONDENCE_EXPERIMENT`) already concluded that
subject IDs are snapshot-local, no single key proves continuity, and a
correspondence-coverage rule was never established — consistent with
this audit's verdict: correspondence is NOT YET JUSTIFIED as durable
or Core machinery, and justified at most as optional external
comparison if a real consumer ever needs the became-question.

Default preserved: snapshot-local identity, no global IDs, no stable
UUIDs, no automatic matching. Deterministic IDs (subject strings,
assertion digests) make future comparison easy without promising
continuity — a good accident worth keeping.

## 7. Vestigial architecture inventory

The older stack is real, coherent, and superseded on the product path:

```text
program_spine (mechanical extraction + comparison; imports none of the three)
    ↓ imported by
authority/ (authoritative-source construction over a spine; case/impact/maintenance)
    ↓ imported by
semantic_binding/ (proposal/admission/persistence; also imports governance.model_adjudicator)
governance/ ←→ authority (adjudication, candidates, construction_cycle, obligation_synthesis)
```

vs. the frozen path:

```text
producer → software_governance → config_routes → Inspect/Judge/Investigate
```

These are not complementary layers; the newer path superseded the
older stack for every shipped behavior. The old stack's importers are
tests and the repo-only research profile only.

Per-subsystem classification (vestigial standard: not required by
frozen product, not a Core guarantee, no active compat promise we
care about, embodies a superseded assumption):

| Subsystem | Classification | Disposition |
|---|---|---|
| `governance/` incl. model-backed CLI | LIKELY VESTIGIAL (strongest candidate) | KEEP AS RESEARCH EVIDENCE BUT EXCLUDE FROM PACKAGE; console script is the sharpest contradiction |
| `authority/` | LIKELY VESTIGIAL | KEEP AS RESEARCH EVIDENCE BUT EXCLUDE FROM PACKAGE |
| `semantic_binding/` | LIKELY VESTIGIAL | KEEP AS RESEARCH EVIDENCE BUT EXCLUDE FROM PACKAGE |
| `program_spine/` | RESEARCH, REUSABLE | KEEP CODE (comparison vocabulary is the mine); exclude TS extractor JS from product package |
| `world/core/contract_store.py` obligation tables | ACTIVE BUT MISPLACED (structural residue) | KEEP TEMPORARILY — schema-coupled into every sealed World |
| `SemanticRefKind` COMMITMENT/OBLIGATION | HISTORICAL RESIDUE | KEEP TEMPORARILY — kernel enum, removal is a Core change |
| `world/runtime/purpose.py` | COMPATIBILITY / LEGACY | KEEP TEMPORARILY (self-declared legacy; import-coupled) |
| `world/{cli,server,explorer,workspaces,project,entry}` | OLD APP / DEV SURFACE | Server+inspector: KEEP as dev convenience. CLI/project/workspaces: COMPATIBILITY |
| `world/core/resolution.py`, `runtime/resolution.py` | UNCLEAR — NEEDS EVIDENCE | Not traced deeply; no live-path importer found |
| 113 non-gate test files | MIXED FOSSIL RECORD | See §9 |

## 8. Useful ideas hidden in old subsystems

| Idea | Source | Verdict |
|---|---|---|
| Epistemic correspondence (continuity/outcome/basis + sidecar discipline) | `program_spine/comparison.py` | KEEP THE IDEA (and the schema shape); do not adopt the matcher |
| Comparison-local claims, no permanent lineage identities | same | KEEP THE IDEA — matches the snapshot-local default |
| Split/merge/rename/move event vocabulary with cardinality rules | same | KEEP THE IDEA |
| Ambiguity as explicit candidates, unresolvedness as outcome | comparison + authority case | KEEP THE IDEA (already mirrored in frozen UNRESOLVED) |
| Maintenance/impact assessment over attachment change | `authority/maintenance.py`, `impact.py` | KEEP THE IDEA (prefigures constructor-revision feedback) |
| Proposal vs admission separation (bounded candidates, deterministic admission) | `semantic_binding/admission.py` | KEEP THE IDEA; implementation is application-specific |
| Authority/source-standing distinctions | `authority/schemas.py` | KEEP AS RESEARCH EVIDENCE |
| Model-backed adjudication, adoption lifecycle, construction cycle | `governance/` | NO LONGER JUSTIFIED on product path; evidence only |
| Obligation/candidate/resolution/adjudication kernel tables | `contract_store.py` | NO LONGER JUSTIFIED as generic kernel; kept only by structural coupling |

## 9. Packaging/test/docs fossil record

Packaging contradictions: `governance = ontology_author.governance.cli:main`
ships a model-backed old-application CLI as a first-class entry point;
`ontology_author.program_spine = ["*.js"]` ships extractor JS the
product never executes; `starlette/uvicorn/requests` are runtime
dependencies serving only the inspector server. `include = ["ontology_author*"]`
ships three zero-production-importer packages.

Tests: 121 files; the default gate runs 8 files / 87 tests. Rough
families: current product acceptance (config_routes phases 1–3,
software_governance construction/judgment/investigation, core_v1,
stable surfaces, ~15 files); Core acceptance and compatibility
(world_store, contract kernel/runtime, resolution, purpose,
packaging, ~15 files); research experiments (`*experiment*.py`,
spine, correspondence, ~15 files); legacy architecture lock-in
(authority, semantic_*, governance_*, graph_*, traversal_*,
retrieval, membership, maintenance, ~70 files). The last family
would block removal of old machinery despite no product requirement
— that is precisely what "fossil record" means, and the
`historical` pytest marker plus narrowed `testpaths` already
quarantine the gate from it.

Docs: frozen contracts/reports (CORE_PRODUCT_V1_*,
CONFIG_ROUTE_*_PHASE*, MINIMUM_USABLE_DESIGN_PRODUCT_AUDIT) vs.
architecture boundary docs (ARCHITECTURE, RELEASING) vs. research
baselines (PRE_APPLICATION_RESEARCH_BASELINE,
CONSTRUCTION_AND_APPLICATION_RESEARCH, RESEARCH_DIRECTION) vs. old
application contracts (AUTHORITY_*, GOVERNANCE_*, PROGRAM_SPINE_*,
SEMANTIC_*, DESIGN_*). Live contradiction of the same shape as
packaging: architecture text describes governance/adjudication as
downstream or deferred while the package ships and tests lock it.

## 10. Minimal conceptual model

Justified by the frozen code, nothing more:

```text
Evidence (bytes + spans + digests; no meaning)
Observation (provider handle + revision + location)
Constructor (executable theory: producer + rules + profile code)
Referent (World-local identity string + label)
Relation / Claim (declared roles + grounded asserted tuples)
Grounding (observations + method, Contract-enforced)
World Revision (sealed directory at a fresh address)
Completeness / Unresolvedness (coverage state + explicit gaps/questions)
Derived Judgment Artifact (replay-verified, external, compatible-code)
Investigation Artifact (receipt/question/proposal, external, never established)
```

Explicitly NOT fundamental (application-optional, none required today):
semantic identity, correspondence, authority, admission, decision,
workflow, obligation, adjudication, lineage, current pointer. Semantic
identity in particular is demoted to "introduce when use justifies it"
by Experiment F.

## 11. Cleanup candidates

Eventual (not now, not authorized): exclude `authority/`,
`semantic_binding/`, `governance/` (+ its console script) from the
shipped package while retaining them as research evidence;
stop shipping `program_spine/*.js` or split the TS extractor;
narrow `world/__init__` / `runtime/__init__` eager imports so live
processes stop loading legacy modules; slim runtime dependencies if
the server becomes optional. Never without a migration note: the
obligation tables are schema-coupled into every sealed World, so
their removal changes future publication bytes (old Worlds still
open — `IF NOT EXISTS` only guards creation).

## 12. What must NOT be built yet

No ontology-evolution machinery, no migration framework, no
lineage/correspondence tables in Core, no global entity IDs, no
admission/decision/action/workflow systems, no World comparison
product surface, no current pointer, no semantic-identity framework.
Each would solve a problem no experiment or consumer has yet
demonstrated. The only near-term candidate is an optional external
comparison reader — and only when a real consumer asks a
became-question.

## 13. Recommended next empirical product work

Put the frozen loop into real product use on a second, messier
evidence domain and log every model deficiency through the
classifier: missing evidence / bad adaptation / bad constructor /
bad interpretation / wrong entity boundary / missing relation / bad
persistence choice / insufficient completeness / consumer reasoning
failure. The audit predicts nearly all land in the first eight and
resolve as constructor revisions plus W1 — run that loop until a
deficiency genuinely cannot. In parallel, keep the agent-refinement
prerequisites honest: an agent today can inspect W0, read evidence,
edit constructor code, run tests, construct W1, and compare verdicts
(all demonstrated); what it lacks is failure classification
guidance and a second domain to generalize from, not architecture.

---

## Audit basis

Dependency claims: module-level import traces over
`ontology_author/{config_routes,software_governance,evidence,world}`
plus reverse-import searches for the four old-arch packages.
Identity claims: producer/construction/store source plus sqlite
inspection of a real W0. Evolution claims: `/tmp/exp_ab.py` and
`/tmp/exp_cdef.py` (retained outside the repo for re-runs), all
against real primitives with production files untouched. No
implementation, cleanup, commit, or push was performed.
