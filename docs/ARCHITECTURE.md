# Ontology Author architecture

Smallest coherent account of the mechanisms the experiments actually needed.
Code is authoritative for implementation; this note is the boundary record
against which later refactoring is judged. Core acceptance is governed by the
[frozen completion contract](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md), with the
[baseline and application handoff](CORE_PRODUCT_V1_BASELINE.md) identifying the
canonical publication path and supported guarantees.

CORE TECHNICAL THESIS: the golden scenario demonstrates construction of
inspectable relational knowledge from heterogeneous evidence, retaining
recorded provenance, derivation, origin, scope and revision. These are not
claims of objective truth or of exhaustive semantic dependency capture.
Authority standing and governance are optional application concerns.

APPLICATION HYPOTHESIS: a complete bounded application can use this capability
for useful end-to-end work. VALUE HYPOTHESIS: doing so justifies its construction
and maintenance cost. Neither follows from core acceptance; neither is settled.

Primitive epistemic guarantees: structural integrity, identity/revision,
provenance, origin/status, scoped completeness, explicit unresolvedness,
historical immutability. Reusable does not imply core: anything that
would not make sense for a wholly different evidence domain belongs above
the core, in generic runtime support or application machinery.

```text
EXTERNAL SOURCES ── observed/structured by ──► EVIDENCE ADAPTERS
                                                      │ read
APPLICATION ── bounded demand ──► ONTOLOGY ◄──────────┘
   │                              │  │
   │ reads admitted knowledge     │  │ stores through
   │ makes operational decisions  │  ▼
   └────────────────────────► WORLD KERNEL
                              (generic storage +
                               mechanical validation)
```

## 1. System boundaries

Four regions. No fifth subsystem is required; maintenance and inspection are
read-side assessment and read surfaces, not layers with write authority.

| Region | May observe | May establish | May mutate/create | Must NOT know |
|---|---|---|---|---|
| APPLICATION | admitted knowledge, optional support/currentness assessments | operational decisions, questions, authority standing where needed | policies, workflows, application records | kernel internals beyond the read surface |
| ONTOLOGY / CONSTRUCTION | evidence (via adapters) | interpreted identities/relations submitted for admission | candidate Worlds; validated sealed revisions through the runtime | operational execution/adoption decisions; no objective-truth oracle |
| EVIDENCE ADAPTERS | external reality | structured observations, addresses, reconstructions | observations and material snapshots only | semantic truth, authority standing |
| WORLD KERNEL | nothing outside the SQLite file | nothing semantic; only mechanical validity | referents, typed relations, assertions, grounding, derivations, revisions, scoped completeness | PaymentProvider, checkout, policy, actions |

Obligation/candidate/resolution/adjudication tables also physically reside in
the kernel package; that is deferred implementation debt (§9), not a Core v1
requirement. Unknown correspondence can be expressed with ordinary relations.

- Package layout does not define regions, but it now follows them:
  `ontology_author/evidence/` holds source adapters (Markdown and program
  source addressing/reconstruction); `ontology_author/semantic_binding/`
  and `ontology_author/governance/` are application-owned;
  `ontology_author/program_spine/` is mechanical program-snapshot
  machinery (spine construction plus cross-World comparison/delta),
  which assigns no standing and makes no workflow decisions.
- Verified: Python under `ontology_author/world/` imports nothing from
  `authority`, `semantic_binding`, `governance`, `profiles`, or
  `program_spine` (enforced by `tests/test_architecture_boundaries.py`).

## 2. Allowed dependencies

```text
APPLICATION  →  ONTOLOGY READ SURFACES (explorer, SQL, sidecars)
APPLICATION  →  ONTOLOGY CONSTRUCTION (demand, construction programs)
ONTOLOGY     →  EVIDENCE ADAPTERS (reads)
ONTOLOGY     →  WORLD KERNEL (stores through)
EVIDENCE     →  EXTERNAL SOURCES (inspects)
```

Forbidden imports checked by the architecture tests: none. Evidence helpers may
read stored observation pointers and retained source blobs through World read
interfaces; this does not assign semantic meaning or authority. Application
packages composing each other (`governance` ↔ `semantic_binding`,
`authority`, `program_spine`) is application composition, not a
violation. Test-only edges are expected.

## 3. Ontology lifecycle

Canonical Core v1 lifecycle:

```text
SOURCES → EVIDENCE ADAPTERS → CONSTRUCTION → CANDIDATE RELATIONAL KNOWLEDGE
→ MECHANICAL VALIDATION / ADMISSION → SEALED REVISION → INDEPENDENT CONSUMPTION
```

`profiles/core_v1/build.py` defines the tested append-only publication pattern:
reserve a fresh revision root, then invoke `Project.run()` there. Reconstruct
into another root; retain both prior and new bundles. The bundle path, not the
runtime's reused local `v0` identifier or a mutable current pointer, is the
independent revision address. This profile is a repository reference workflow,
not a newly packaged history service.

Legacy in-place `Project.run()`, `rebuild()` and `author rebuild` replace their
current bundle and do **not** retain successful prior revisions. They remain
supported compatibility paths, but do not define Core v1 history semantics.
Sealing and read-only reads protect the supported workflow; they are not a
malicious-constructor/filesystem-owner sandbox or a power-loss durability proof.

Applications may additionally use warrants, authority standing, obligation
resolution, currentness overlays or explicit reconstruction. These are not
mandatory stages of core construction; a live LLM is likewise not required.
Adequacy is orthogonal: `QUESTIONS + WORLD → ADEQUACY` (application tests).

- Admission ≠ resolution. Admission gates tuple publication;
  resolution evaluates one obligation over recorded candidates.
- Three different "candidates" exist and must not be merged: kernel
  candidate association (obligation↔commitment link), `SemanticCandidate`
  (pre-World bounded proposal), governed/Git candidate (candidate source
  state).
- Authority content (bindings, classes) is application-owned; assessment
  mechanics (`assess_warrant` interface, `Contract` standards) are ontology.
- Material support is an ontology-generic pattern (recorded region +
  deterministic reproduction); source reading belongs to evidence.
- Construction receipts are ontology run provenance, not kernel metadata;
  the kernel never reads them.

## 4. Authoritative artifacts

| Question | Authority |
|---|---|
| External reality | selected, revisioned evidence itself |
| Which questions matter | application questions; optionally law, gap synthesis and obligations |
| How knowledge is built | construction programs (`construction.py`, authority/binding/spine constructors) |
| What may enter | integrity: kernel mechanical rules + `Contract` + admission profiles |
| Whether it is enough | adequacy: executable application tests |
| What was established | independently addressed sealed bundle: `world.sqlite` + applicable sidecars |
| What supports a claim | recorded grounding/origin/derivation; optional application warrants and authority assessments |
| Which run produced it | run provenance: generated construction receipts |
| How recorded support/dependencies compare with later inputs | generated maintenance/material/comparison assessments; not exhaustive semantic truth |
| Resolution inputs | conflict rules + authority configs (application) |
| Why it exists | purpose/design rationale: orientation only, never a correctness oracle |

## 5. Currentness model

Four optional runtime/application assessment dimensions. None mutate the sealed
World. No generic `Staleness` exists
(`is_stale` is derivation-only) and none should be introduced.

| Dimension | Owner | Inputs | Representation |
|---|---|---|---|
| SOURCE CURRENT | maintenance assessment | recorded observation + current source | `PRESERVED/CHANGED/MISSING/UNKNOWN`, `GROUNDS_*` |
| CONSTRUCTION CURRENT | receipt comparison | receipt + checked-out `construction.py` | digest match |
| RECORDED SUPPORT / DEPENDENCIES CURRENT | claim-support overlay | warrant + authority config + current source/comparison | `claim_support`, `current_resolution`, dependency maintenance |
| APPLICATION CURRENT | application workflow | case + readiness + policy | readiness, adoption outcomes |

Preserved distinctions: source revision change ≠ support change;
construction change ≠ all claims stale; historical resolution ≠ current
resolution; absent knowledge ≠ negative knowledge. Core records and exposes
scoped completeness; supported reasoning/application logic must consult it.
Raw SQL is an escape hatch and can misinterpret absence.

`PRESERVED` means preservation of the **recorded maintenance basis**. The
system can inspect and reassess explicitly recorded dependencies; it does not
generally prove they exhaust every condition on which an interpretation
depends. A preserved basis is not exhaustive proof that semantic truth holds.

Sealed World = immutable statement relative to construction inputs.
Currentness = deterministic/live assessment that never rewrites it.
Reconstruction = publication at a new retained address when renewed durable
knowledge is required through the Core v1 lifecycle.

## 6. Stable read surfaces

Raw schema (relation names, rows, SQL) is inspectable, discoverable, and
allowed to evolve. Core consumption uses `WorldExplorerAdapter.schema()`,
`rows()`, `referents()`, `assertion()`, `derivation()`, and `query_semantic()`;
`ConstructionWorld.open(..., read_only=True)` exposes full completeness
receipts through `latest_completeness()`. SQL/Python inspection is supported.
Schema roles/types/mode, assertion identity, grounding and origin are
inspectable without private constructor state. Opening a sealed bundle does
not change permissions, initialize schema, or migrate history.

Existing application-facing compatibility surfaces additionally expose
obligations, selected-obligation reads, recorded/current resolution, governance
and authority identity, structure, and construction receipts. Their presence
does not make question/answer or authority semantics core requirements.

`resolution()` (recorded history) and `current_resolution()` (live overlay)
are distinct by design, not duplicates. No generic stable-view framework.
Shape (not serialization) is pinned by `tests/test_stable_read_surfaces.py`;
import direction by `tests/test_architecture_boundaries.py`.

## 7. Application-specific extensions

Core v1: referents, typed relations, assertions, grounding, derivations,
identity/revision, origin and scoped completeness, composed with evidence
adaptation, executable construction, candidate admission, retained publication
and supported reads. Explicit unresolvedness can use ordinary relations.

Optional runtime/application machinery: program representations/comparison,
semantic persistence and maintenance warrants, authority, governance,
obligation/candidate/resolution/adjudication semantics, `resolve_world`,
material-support/currentness patterns and agent workflows. Reusable mechanics
need not become kernel primitives. No live model is required by core.

Application-only (do not generalize): checkout law and dimensions,
`PaymentProvider`, provider-boundary invariant, membership profiles,
authority classes/bindings, conflict rules, `GovernanceCase`, adoption and
execution policies, Git candidate materialization, model transports.

## 8. Terminology

- AUTHORITY: standing to establish a class of knowledge (application-owned).
- SUPPORT: material evidence backing a particular claim. Kernel
  `warrant_for_assertion` ≠ `SemanticCommitmentWarrant` ≠ `authority_claim`;
  same word, three owned records.
- RESOLUTION: disposition of a semantic question/obligation. Distinct from
  referent resolution (identity) and `ScopedInvariantEvaluation` (snapshot
  truth assessment).
- ADJUDICATION: application/workflow decision or interpretation. The kernel
  adjudication record is a generic durable input shape, not the decision.
- CONTRACT: an executable boundary constraining whether a transition or
  state is permitted — nothing else. Construction code and adapters are
  PROGRAMS; receipts and assessments are RECORDS; payload tags are SCHEMAS
  (structural identity/version); run provenance is a RECEIPT.
- WORLD: the sealed relational knowledge bundle unless explicitly qualified
  (`ConstructionWorld` and `SemanticWorld` are construction handles).
- CURRENTNESS: live assessment relative to later state/evidence; never a
  rewrite of sealed history.
- CONSTRUCTION: the executable process/program that builds candidate World
  knowledge inside ontology machinery.
- PROFILE: `GovernanceProfile` (adopted law) ≠ admission profile
  (executable entry rules) ≠ `profiles/` (application packages).
- CANDIDATE (three, never merged): kernel candidate association (a claim
  candidate FOR an obligation), `SemanticCandidate` (a proposal candidate
  FOR a `ConstructionObligation`), governed/Git candidate (a source state
  candidate FOR adoption).

Contracts belong at transitions that increase epistemic or operational
standing:

```text
observation → candidate claim ............ construction/program
candidate claim → admitted assertion ..... admission contract
question + candidates → disposition ...... resolution contract/standard
questions + World → adequate/inadequate .. adequacy contract
application case → adopted action ........ workflow policy/authorization
```

A new concept needs a Contract only if it gates such a transition.

## 9. Known implementation mismatches

CURRENT IMPLEMENTATION, not architecture. Do not generalize from these:

- Obligation/Candidate/Resolution/Adjudication shapes live in
  `world/core` (`ContractWorldStore`). Semantically they are application
  question/answer patterns; only their storage is generic. Blast radius
  spans core schema, runtime, explorer, server, frontend, profiles, and
  tests — extraction needs a migration seam and is explicitly deferred.
- `Contract` mixes per-tuple admission with per-obligation resolution
  assessment. Admission is the trusted boundary; resolution assessment
  is application-facing. Split deferred.
- `Purpose`/`PURPOSE.md` compat (`Purpose.require_*`, `demand()`,
  PURPOSE scope, explicit `purpose=`) remains as legacy orientation
  machinery. A World needs no purpose to qualify as a World; no
  replacement construction surface is designed yet, so the explicit-only
  path stays.
- `profiles/*/governance.py` (law/authority bindings) and
  `ontology_author/governance/` (workflow decisions) share a name for
  different responsibilities. Renaming deferred.
- Stable question/answer/authority inspection shares the explorer with generic
  reads. Existing application consumers depend on it; separation is deferred.

## Claims and hypotheses

SETTLED: source authority ≠ material claim support; adequacy accepts
explicit unresolvedness; sealed Worlds are immutable; construction code
is a program, not a declarative contract; reusable does not imply core;
purpose is not constitutive of World.

DEMONSTRATED CORE PATH: independently retained sealed revisions, read-only
consumption and explicit reconstruction. Legacy replacement APIs are the
documented exception to retention, not evidence for a universal history claim.

OPEN: when an application must require currentness vs historical state;
source `AuthorityDelta`; semantic referent carriage across revisions;
durable-structure vs case-local placement; single-answer cardinality;
obligation/resolution extraction seam; Purpose API replacement.
