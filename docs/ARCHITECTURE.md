# Ontology Author architecture

Smallest coherent account of the mechanisms the experiments actually needed.
Code is authoritative for implementation; this note is the boundary record
against which later refactoring is judged.

Product thesis (SETTLED): construct operational knowledge from evidence
while preserving the conditions under which it may legitimately be relied
upon. A World makes mechanically inspectable claims about
knowledge-evidence relationships — provenance, derivation, scope,
revision, standing — not claims of objective truth. Governance is
downstream of those guarantees.

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
   │ reads governed knowledge     │  │ stores through
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
| APPLICATION | governed knowledge, currentness state | operational decisions, demand, authority standing | cases, policies, adoption/execution decisions, application records | kernel internals beyond the read surface |
| ONTOLOGY | evidence (via adapters) | governed knowledge: admitted tuples, resolutions | candidate Worlds, sealed Worlds (via kernel writes) | application actions, domain semantics of truth |
| EVIDENCE ADAPTERS | external reality | structured observations, addresses, reconstructions | sidecar observations only | semantic truth, authority standing |
| WORLD KERNEL | nothing outside the SQLite file | nothing semantic; only mechanical validity | generic epistemic rows (referents, relations, assertions, grounding, obligations, candidates, resolutions) | PaymentProvider, checkout, policy, actions |

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

Reverse or cross-layer edges found: none in product code. Application
packages composing each other (`governance` ↔ `semantic_binding`,
`authority`, `program_spine`) is application composition, not a
violation. Test-only edges are expected.

## 3. Ontology lifecycle

```text
DEMAND ──► CONSTRUCTION ──► CANDIDATE KNOWLEDGE ──► SUPPORT + AUTHORITY
   application        program        assertions +         recorded warrants +
   questions                         candidate links      external standing
                                                        │
                         ┌──────────────────────────────┘
                         ▼
              ADMISSION (per tuple) + RESOLUTION (per obligation)
                         │  both pre-seal; distinct records
                         ▼
                  SEALED WORLD ──► CURRENTNESS ──► INSPECTION / RECONSTRUCTION
                   immutable        live overlays    read; rebuild to renew
```

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
| Which questions matter | demand: law + structure + gap synthesis; generated obligations |
| How knowledge is built | construction programs (`construction.py`, authority/binding/spine constructors) |
| What may enter | integrity: kernel mechanical rules + `Contract` + admission profiles |
| Whether it is enough | adequacy: executable application tests |
| What was established | sealed bundle: `world.sqlite` + sidecars (incl. adjudication records) |
| Why a claim stands | claim basis: warrant/grounding + authority assessments + material records |
| Which run produced it | run provenance: generated construction receipts |
| Whether it still holds | currentness: generated maintenance/material/comparison assessments |
| Resolution inputs | conflict rules + authority configs (application) |
| Why it exists | purpose/design rationale: orientation only, never a correctness oracle |

## 5. Currentness model

Four owned dimensions. All are live assessments; none mutate the sealed
World; all are explicitly represented. No generic `Staleness` exists
(`is_stale` is derivation-only) and none should be introduced.

| Dimension | Owner | Inputs | Representation |
|---|---|---|---|
| SOURCE CURRENT | maintenance assessment | recorded observation + current source | `PRESERVED/CHANGED/MISSING/UNKNOWN`, `GROUNDS_*` |
| CONSTRUCTION CURRENT | receipt comparison | receipt + checked-out `construction.py` | digest match |
| KNOWLEDGE CURRENT | claim-support overlay | warrant + authority config + current source | `claim_support`, `current_resolution` |
| APPLICATION CURRENT | application workflow | case + readiness + policy | readiness, adoption outcomes |

Preserved distinctions: source revision change ≠ support change;
construction change ≠ all claims stale; historical resolution ≠ current
resolution; absent knowledge ≠ negative knowledge (completeness-gated).

Sealed World = immutable statement relative to construction inputs.
Currentness = deterministic/live assessment that never rewrites it.
Reconstruction = a new build when renewed durable knowledge is required.

## 6. Stable read surfaces

Raw schema (relation names, rows, SQL) is inspectable, discoverable, and
allowed to evolve. Deliberately compatibility-sensitive for consumers:

obligations + selected-obligation read, recorded and current resolution,
warrant/grounding/origin inspection, schema roles/types/mode (not relation
names), governance and authority identity, structure, construction receipt.

`resolution()` (recorded history) and `current_resolution()` (live overlay)
are distinct by design, not duplicates. No generic stable-view framework.
Shape (not serialization) is pinned by `tests/test_stable_read_surfaces.py`;
import direction by `tests/test_architecture_boundaries.py`.

## 7. Application-specific extensions

Generic: storage, typed relations, grounding, observations, completeness,
unresolvedness, obligation/candidate/resolution/adjudication shapes
(storage only — their question/answer semantics are application-owned;
see §9), admission mechanics, `resolve_world` mechanics,
material-support pattern, receipt pattern, read primitives.

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
- WORLD: the sealed governed knowledge bundle unless explicitly qualified
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

## Claims and hypotheses

SETTLED: source authority ≠ material claim support; adequacy accepts
explicit unresolvedness; sealed Worlds are immutable; construction code
is a program, not a declarative contract; reusable does not imply core;
purpose is not constitutive of World.

WORKING HYPOTHESIS: history is immutable, currentness is computed,
renewed durable knowledge is reconstructed. No falsifier found in the
repository.

OPEN: when an application must require currentness vs historical state;
source `AuthorityDelta`; semantic referent carriage across revisions;
durable-structure vs case-local placement; single-answer cardinality;
obligation/resolution extraction seam; Purpose API replacement.
