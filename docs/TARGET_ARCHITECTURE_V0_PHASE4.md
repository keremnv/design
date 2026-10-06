# Target Architecture v0 — Phase 4 vertical slice

## A. Starting state

Merged `main` after Phase 3:

```text
8fd1200d43fbfae2753d1fe625c8886016a2bcc3
Phase 3: separate construction basis from semantic warrant (#3)
```

Main CI (`Core v1 baseline gate`) was green on that SHA before the Phase 4
branch was created. Phase 4 starts from it and preserves all Phase 1–3
guarantees: provenance-qualified evidence, retained immutable publication
history, and the construction boundary
(`ConstructionBasis ≠ SemanticSupport`,
`ConstructionMethod ≠ SemanticSupport`,
`MechanicalAdmission ≠ SemanticTruth`).

## B. Exact vertical-slice history

```text
policy.md ("Customer export must use the approved customer-export route.")
→ W0   (semantic-only publication, no program state)
routes.ts v1 (export function customerExport(): string ...)
→ P1   (TypeScript spine publication)
W0 + P1 + explicit entity selection
→ W1   (binding publication: requirement realized by exact P1 callable)
routes.ts v2 (export function customerExportV2(): string ...)
→ P2   (fresh spine publication; P1 untouched)
W0 + P2 + fresh explicit entity selection
→ W2   (fresh binding publication: requirement realized by exact P2 callable)
```

Observed identity shapes (addresses vary per run; structure is stable):

```text
W0: PublicationRef(address=.../W0, world_id='config.routes/requirements/v1', revision=11)
P1: PublicationRef(address=.../P1, world_id='v0', revision=82)
E1: program:ts:<p1-snapshot-id>:callable:0c291d4037fb04a25c4496e9
W1: PublicationRef(address=.../W1, world_id='v0', revision=102)
P2: PublicationRef(address=.../P2, world_id='v0', revision=82)
E2: program:ts:<p2-snapshot-id>:callable:30c104768c712aad6fed1583
W2: PublicationRef(address=.../W2, world_id='v0', revision=102)
```

P1 and P2 share `world_id`/`revision`; only the exact publication address
distinguishes the occurrences. Entity IDs embed their snapshot id, so E1 and
E2 are structurally snapshot-local. W1/W2 inherit `world_id='v0'` from their
copied program baselines; their construction identity lives in the receipt
(`config.routes/binding/v1`, constructor `config.routes.binding/v1`) and in
their fresh addresses — never in a shared counter.

Historical properties demonstrated by test:

```text
W0 byte-identical throughout; P1 byte-identical after P2 exists.
W1 byte-identical after P2, comparison and W2 exist; still binds E1.
P2 changes nothing about W1; W2 is a fresh publication binding E2.
No publication asserts currentness, supersession or replacement.
```

## C. W0

W0 is published through the unchanged Phase 3 production path
(`construct_config_requirements`). It contains the `config_requirement`
assertion, its paragraph support, `ConstructionBasis`, constructor
`config.routes.requirements/v1`, the mechanical `PASS` admission record and
an exact `PublicationRef`. It contains no `program_%` relation, no
`realized_by`, no attachment warrant, no snapshot id and no implementation
status. The requirement is therefore valid semantic information — a
grammatically licensed reading of retained source bytes — before any code
exists. Case A re-verifies this inside the slice.

## D. P1/P2

The program side is a real TypeScript spine publication built by
`build_typescript_spine` over `src/routes.ts` plus `tsconfig.json`. The
smallest genuinely understood source shape was one exported function, which
the spine observes as `module`, `source_unit`, `callable` and `signature`
entities. No extractor change was needed; no business concept was taught to
the spine.

Spine facts actually consumed by the slice:

```text
program_snapshot        snapshot referent, source_state revision, digests
program_entity          snapshot membership of each entity
program_entity_kind     kind per entity (callable discovery)
_world_referents        mechanical labels (customerExport / customerExportV2)
structural_context      module → source_unit → callable chain (warrant context)
program_inputs blobs    retained TS bytes behind REFERENT SOURCE groundings
program_identity_descriptor / program_invokes / program_resolution
                        read by warrant/relevance machinery (empty for this leaf)
compare_spines          RENAME correspondence + program delta (Case G only)
```

P1 contains no `authority_%`/`semantic%`/`realized_by`/`config_requirement`
relation, and the semantic sentence never appears in its bytes (Case B).
The spine decides nothing about realization; `P1 = mechanically observed
program state`.

## E. W1/W2 binding representation

W1 and W2 reuse the existing production authority binding seam — the same
seam the checkout governance construction uses for `realized_by` — rather
than the semantic-binding obligation/catalog path. `semantic_binding`'s
`PROGRAM_REALIZATION` flow is a trusted-mapping obligation workflow
(obligation + catalog + candidate + admission decision + delta
maintenance) shaped for payment/invariant/membership commitments. Forcing
the slice's singular explicit judgment through obligation/catalog shapes
would add machinery the slice does not need. The authority seam already
provides exactly the required semantics:

```text
realized_by {requirement: semantic:proposition:customer-export-route,
             program: <exact P1/P2 callable>}
  claim_kind SEMANTIC_PROGRAM, support CROSS_EVIDENCE_INFERRED
  requirement endpoint SOURCE_DEFINED (grammar-derived)
  program endpoint AGENT_RESOLVED (explicit selection judgment)
  method config.routes.binding/v1:explicit-selected-realization
  support: the requirement paragraph observation (grouped SupportPath)
authority_attachment_warrant → exact entity + program_snapshot_id
  + structural chain + endpoint resolutions (justifying program
  relations/outcomes honestly empty for this leaf callable)
authority_relevance_scope → persisted DEFAULT_KIND_RULE clauses
  (ATTACHED_IDENTITY, IDENTITY_MANIFESTATION, ENDPOINT_RELATION)
config_requirement → re-materialized from the same governance bytes,
  deterministic semantic id shared with W0 by application convention
ConstructionBasis → exact W0 + P1/P2 PublicationRefs, qualified program
  snapshot, candidate_baseline = program publication
constructor config.routes.binding/v1, contract authority-construction-boundary/v1
fresh PublicationRef at a fresh address
```

New code is one thin caller, `construct_config_binding`, plus sharing the
requirement materialization helper with the Phase 3 entrypoint. The
constructor additionally requires the selected requirement to be present
with identical statement text in the first exact semantic input (W0),
which makes "judgment over W0" load-bearing at construction time while
keeping the retained bundle self-contained: support stays W1-local, and
the basis entry grants no support (Phase 3 invariant preserved, Case L).

## F. Historical behavior

W1 is built over the P1 baseline with W0 as an exact publication input;
W2 is built fresh over the P2 baseline with W0 as input — never by copying
W1 and swapping an id. Fingerprint comparisons prove W0, P1 and W1 are
byte-identical after every later stage, W1 still binds E1 after W2 exists,
and W2 binds E2. Neither binding publication asserts supersession,
correction, obsolescence or currentness (relation-name sweeps in Cases C,
H, I, K). W1 and W2 coexist as independent judgments:
`W1 = judgment over W0 + P1`, `W2 = judgment over W0 + P2`.

## G. Program change behavior

`compare_spines(P1, P2)` mechanically reports the rename:

```text
old_entity E1 → new_entity E2
outcome RENAME, basis_class HEURISTIC, continuity CONTINUED
changes: name CHANGED, source_location/manifestation CHANGED,
         boundary/identity_kind/signature/structural_context PRESERVED
limitations: heuristic correspondence is not mechanically entailed identity continuity
```

This signal justifies only "the historical binding may deserve
reconsideration." It explicitly did NOT establish: that W1 is invalid,
that E1 and E2 are identical, that W1 must be rebound, or that W2 exists.
Comparison is a pure read: P1/P2/W1 fingerprints are unchanged by it, no
correspondence is written into any world, and W1 still verifies (Case G).
`affected ≠ relevant ≠ invalid ≠ false` is preserved: before W2 exists,
the state is exactly "W1 judges P1; P2 exists; no W2 judgment published"
(Case K).

## H. Provenance/reconstruction

After deleting the governance, P1 and P2 workspaces (and confirming no
candidate/staging leftovers), every publication keeps its promises:

```text
W0 semantic support reconstructs; publication verifies
P1/P2 program observations reconstruct from their own program_inputs
W1/W2 semantic support reconstructs from their own authority_evidence
W1/W2 program observations for E1/E2 reconstruct from their own
  program_inputs (copied with the program baseline)
W1/W2 still verify with the P1/P2 bundles moved away
```

The binding contract is therefore self-contained: exact P1/P2
qualification stays inspectable in the basis and warrant, while
reconstruction never requires the referenced program publication to be
present. No transitive copying was invented; the program bytes arrive
through the ordinary baseline-copy mechanism.

## I. Capability-demand ledger

Only operations the implemented slice actually uses, stated as demands —
not an interface.

```text
1. Build a sealed program publication from a source workspace.
   Why: produce P1/P2 as retained occurrences.
   Surface: program_spine.build_typescript_spine + TypeScriptBoundary.
   Qualification: fresh address; receipt names snapshot id and digests.

2. Open an exact retained publication and read its identity.
   Why: qualify W0/P1/P2 occurrences; read W0 requirement content.
   Surface: ConstructionWorld.open(read_only) + PublicationRef.from_world /
   verify_publication_ref + relation_rows.
   Qualification: (address, world_id, revision) triple; P1/P2 share
   world_id/revision, so address is load-bearing.

3. Enumerate program entities with kind and mechanical label.
   Why: discover the E1/E2 callable without manufacturing ids.
   Surface: program_entity_kind rows + _world_referents labels;
   constructor-side AuthorityConstructor.program_entities(kind, label).
   Qualification: rows are snapshot-local; ids embed the snapshot id.

4. Read one snapshot's identity and revision.
   Why: bind and verify against an exact snapshot, not "the program".
   Surface: program_snapshot row (snapshot referent, source_state).
   Qualification: exactly one snapshot per governed world; program
   observations fail closed unless their revision equals source_state.

5. Recover an entity's exact source occurrence bytes from the bundle.
   Why: reconstruct what the bound entity textually was.
   Surface: evidence.program_source.program_source_observations(entity)
   + reconstruct_program_observation from sealed program_inputs blobs.
   Qualification: handle digest + byte range + snapshot-revision match.

6. Read mechanical structural relations around an entity.
   Why: warrant context and relevance scoping for the binding.
   Surface: structural_context (+ program_invokes / program_resolution /
   program_identity_descriptor, empty for this leaf).
   Qualification: snapshot-local rows; warrant requires non-empty
   structural context.

7. Compare two snapshots for a named old entity.
   Why: mechanical reconsideration signal for the historical binding.
   Surface: program_spine.compare_spines → correspondence_claims
   (outcome/basis_class/continuity/changes/limitations) + program_delta.
   Qualification: correspondence is HEURISTIC, qualified per claim, and
   explicitly not identity; E1 ≠ E2 always.

8. Verify retained program evidence closure of a bundle.
   Why: admission and retained verification of P1/P2/W1/W2.
   Surface: evidence.program_source.verify_retained_program_inputs.
   Qualification: every TypeScript SOURCE grounding must reconstruct
   from that bundle's own blobs.
```

## J. Architectural pressure discovered

No actual blockers. The slice ran entirely on existing production
surfaces. Two observations for future optimization (not gaps):

```text
- Retained-world entity discovery hand-joins program_entity_kind with
  _world_referents labels; only the candidate-side constructor offers
  program_entities(kind, label). A tiny retained-read helper would
  remove duplication. Future optimization.
- W1/W2 inherit world_id 'v0' from their copied program baselines, so
  world_id alone never names a binding construction; the receipt
  construction_id and the (address, world_id, revision) triple do.
  Observed behavior, worked without confusion. Not a problem to solve.
```

Nothing in the slice required teaching the spine business concepts,
adding explorer/SQL APIs, or generalizing any engine.

## K. Tests

`tests/test_phase4_vertical_slice.py` (in the default gate) builds the
history through production seams only. Map to invariants:

```text
A  W0 semantic-only            intent exists before code; exact ref verifies
B  P1 mechanical-only          real callable; evidence reconstructs; no semantics leak
C  W1 exact binding            basis [W0,P1]; warrant names snapshot/E1; both sides reconstruct
D  substitution rejected       wrong entity/snapshot, wrong W0 revision, mismatched W0
                               content fail closed; copied bytes identify the copy
E  P2 fresh/distinguishable    P1 unchanged; E1≠E2; address distinguishes occurrences
F  W1 does not move            fingerprint stable; still binds E1; no P2 content appears
G  mechanical signal            RENAME/HEURISTIC/CONTINUED read; nothing created or invalidated
H  W2 fresh binding            basis [W0,P2]; binds E2; W1 still binds E1; both verify
I  read matrix                  all five open independently with exact meanings
J  workspace deletion           all reconstruction promises hold; P1/P2 bundles optional
K  no absence inference         P2-without-W2 changes nothing about W1; no negative semantics
L  basis≠binding                unselected callable/paragraph never become binding support
```

## L. Scope exclusions

Phase 4 introduced none of:

```text
ProgramBackend
Glean / Angle / Glean schema or identifiers
ProgramWitness
currentness / latest-wins / supersession
generic correspondence or change-impact engine
investigation planning / search / working sets
reasoning traces / prompts / chain-of-thought persistence
confidence scoring
SQL code explorer or product projections
workflow / reconsideration / case orchestration engines
```

The change is one config-routes caller (`construct_config_binding`), one
shared materialization helper, twelve integration tests, and this report.
The coupled `construct_config_world` path and all historical
config-routes/governance experiments are untouched. No abstraction was
added that the slice did not demonstrate necessary.

## M. Final verdict

> Does the repository now demonstrate one complete production-backed flow in which semantic information exists before code, is later bound to exact mechanically observed program state, survives program evolution as historical judgment, and can be freshly reconstructed against a new program snapshot without mutation, implicit currentness or automatic semantic inference?

```text
YES — VERTICAL SLICE COMPLETE; READY TO EXTRACT PROGRAMBACKEND CONTRACT
```
