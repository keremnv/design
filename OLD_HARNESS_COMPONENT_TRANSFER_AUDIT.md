# Old-Harness Component Transfer Audit (Zero-Model, No-Implementation)

**Date:** 2026-09-17 UTC · **Scope:** spreadsheet-agent research program ·
**Method:** static repository archaeology, artifact analysis, git history; no model
inference, no benchmark changes, no implementation ·
**Machine-readable companion:** [`architecture_transfer_audit/`](architecture_transfer_audit/)

## Headline finding

**The spreadsheet harness described in the audit brief does not exist in this
workspace.** No implementation, experiment artifact, trajectory, or benchmark
scaffold for any of the ~29 named mechanisms was found. Every empirical claim
in the brief's background (capability losses, fingerprint compression, closure
results, `calc_*` adoption, task-specific outcomes) is therefore
**unverifiable from this repository** and is treated below as an
`UNVERIFIED_ASSERTION`, never as evidence.

This is a negative-result audit. Its value is elimination and honesty: it maps
exactly what is missing, records the nearest in-repo analogues (which prove
buildability only, never benchmark value), marks all 29 components
`ARCHAEOLOGY_ONLY`, and identifies the single probe that would unblock every
downstream question.

**How absence was established** (details in `evidence_index.json`):

- Case-insensitive search for `openpyxl|libreoffice|spreadsheet|calc_apply|
  calc_query|programgroup` over `*.py`/`*.md`/`*.json` (excluding `.venv`):
  zero code hits. The only "spreadsheet" mentions are vendored `d3-dsv` README
  prose about CSV/Excel.
- `fingerprint` hits in `ontology_author/` are world-content hashes
  (`fingerprint_world`, `result_fingerprint`) — name-only resemblance to formula
  fingerprints.
- `experiments/` holds only semantic-persistence and governance-product runs;
  `evaluation_runs/` holds grain-traceability consumers, authority probes, and
  maintenance-value runs — no workbook tasks, no control trajectories.
- All git branches and full history contain zero spreadsheet-related commits.
- `tests/` covers the Ontology Author product and legacy graph/world behavior;
  per audit rules, tests prove implementation properties, not benchmark value —
  and none exercise spreadsheet mechanisms anyway.

## Phase 3 — revisiting the major historical positives

Because no artifacts exist here, each subsection separates **what the brief
asserts** from **what this repo supports** (nothing, in every case) and states
the discriminating probe. The ledger rationale is preserved so the analysis is
useful the moment the evidence corpus is located.

### A. Formula fingerprints — UNRESOLVED (no corpus)

- *Asserted, unverified:* fingerprints established structural regularity of
  formulas and achieved compression, but never themselves improved end-to-end
  capability.
- *Standing hypothesis:* strongest future role is **runtime-internal** (pattern
  grouping for a translation-lowering pass, anomaly flags), not model-facing.
  `same fingerprint ≠ same business meaning` must be enforced by keeping
  fingerprints out of model-facing semantic evidence.
- *Deciding probe:* transfer test — fingerprint-grouped translation vs
  per-cell synthesis on cost at equal capability.

### B. Dependency graph — UNRESOLVED, role-separated

| Role | Asserted status | Hypothesized placement |
|------|----------------|------------------------|
| 1. Reference representation | high fidelity (unverified) | L0 substrate |
| 2. Model-facing semantic evidence | negative missing-formula probe (unverified) | **exclude** pending dedicated probe |
| 3. Retrieval substrate | improvements (unverified) | L0-internal completeness primitive only |
| 4. Execution coordination/closure | old positives + zero T3 transfer under loose agent (both unverified) | advisory preview, never silent auto-expansion |

Answer to "dead, partially alive, or useful elsewhere": **cannot be determined
here.** The role separation above is the audit's durable contribution: roles 1,
3-internal, and 4-advisory carry no semantic authority and are jointly
testable; role 2 is the risky one and must pass its own injection-vs-lookup
probe. Collapsing the four roles into one verdict is what made the historical
argument ambiguous.

### C. ProgramGroups / translation — UNRESOLVED

*Asserted, unverified:* mechanically correct; reduced repeated synthesis; helped
when the canonical formula was right; ignored when optional
(`calc_translate_fill` never adopted); default agent did equivalent Python
fills (`08_03`). The provisional reading — **efficiency/reliability primitive,
not capability mechanism** — is coherent but ungrounded here. Deciding probes:
correctness suite + optional-adoption probe + translation efficiency replay.

### D. Hybrid retrieval / SQL / working sets — UNRESOLVED, three sub-questions

- *As model cognition?* Doubtful even on the brief's telling (projection
  failures); needs push-vs-pull capability comparison.
- *As optional query accelerator?* Plausible; needs efficiency replay vs
  agent-Python.
- *As internal index with SQL hidden?* Strongest hypothesis; SQL as L0
  implementation detail requires no agent learning.

Methodological precedent found in-repo: the graph-vs-SQL experiment design doc
explicitly diagnoses forced-bundle ambiguity (seed-53/54) and proposes freezing
the substrate while varying only the access model — exactly the design the L1
transfer tests should copy.

### E. Temporal structure — UNRESOLVED

*Asserted, unverified:* one historical authority correction vs later
no-headroom results. Narrowest surviving hypothesis: exact
period-coordinate lookup with provenance and explicit unknown-state, never
auto-correction. Requires a precision/recall suite on period detection before
any agent exposure.

### F. Writer / persistence / LibreOffice bridge — infrastructure, pending suite

Least controversial hypothesis in the audit: atomic write, structure
preservation, recalc, and exact diff/receipt are pure infrastructure with no
authority risk. Still untested here (no workbook persistence suite exists);
shared-formula masters are the named edge case. This is the one component class
that can be built and hardened without any capability experiment.

### G. Commit-gate / mechanical verification — UNRESOLVED

*Asserted, unverified:* precise findings that assisted repairs, but no
end-to-end capability conversions. Provisional reading: **observation layer
(L5), not semantic gate** — block only checks with measured near-zero false
positives. Deciding probes: per-check precision/recall + findings-shown vs
not-shown repair comparison.

## Phase 4 — architecture-induced failures (all UNRESOLVED)

All four candidate pairs (per-cell synthesis→translation; isolated
execution→closure; pushed packets→working sets; generated authority→intersection)
lack the logs, ablations, or counterfactuals needed for classification in this
workspace. Each has a named deciding experiment in
`architecture_induced_failures.json`. The structural warning stands regardless:
**a repair mechanism for a self-inflicted failure is not transferable
evidence.** Push-vs-pull, advisory-vs-auto-expansion, and grouped-vs-per-cell
ablations must precede any transfer.

## Phase 8 — challenging the Mutation IR assumption (UNTESTED, no corpus)

No control trajectories exist here, so none of the heterogeneity questions
(loops, state-carrying iteration, program-built formulas, conditional
selection, XML edits, read-back-dependent sequences, sheet ops) can be
answered. The audit contributes the mechanical rubric and counter set in
`control_mutation_census.json`. The central falsifier is stated plainly: **if a
minimal IR cannot cover normal control behavior, Architectures B and C fall and
D (transparent interception) becomes the leading structured option.**

## Phases 6–7 — independent architecture review (evidence-free zone, tradeoffs only)

No architecture can be confirmed or refuted from this workspace. The
tradeoffs in `architecture_tradeoffs.json` reduce to structural facts plus
labeled hypotheses:

- **A (raw control + hardened I/O):** lowest risk and complexity, shippable
  alone (writer/recalc/diff + L5 diagnostics). Forfeits any capability that
  required harness structure. Baseline against which B–D must justify
  themselves.
- **B (structured mutation thin waist):** viability is *entirely* conditional
  on the representability probe. Best intent record (declarative batch is
  auditable), strongest scope safety — if the IR covers behavior.
- **C (current proposal, B + optional queries):** fullest substrate use, but
  two new surfaces to learn and the forced-vs-optional adoption hazard.
  Complexity is justified only if both layers pass independent transfer tests;
  do not bundle them into one experiment (the seed-53/54 moral).
- **D (transparent interception):** preserves the Python surface; risk
  concentrates in capture completeness, where silent misses are worse than IR
  rejection. Deployable as observer first (receipts only), enforcement later —
  the cheapest safe sequencing available.
- **E:** none proposed; manufacturing one is forbidden. Nearest unendorsed
  seed: D-observer now, C-queries only where efficiency replay justifies — a
  deployment sequence, not a new architecture.

No winner is ranked. The experiments that distinguish them: representability
probe (B/C viability), observe-only capture-completeness probe (D viability),
optional-adoption + efficiency replays (L1 justification), hardened-I/O delta
vs raw control (A baseline).

## Phase 9 — efficiency census (no corpus, method only)

`control_efficiency_census.json` fixes the mechanical-first classification rule
(semantic reasoning = residual after mechanical matchers, never LLM labels) and
the counter list. The brief's implied ranking (translation loops, search loops,
verification re-opens, reference walks) is recorded as **conjecture, not a
finding**. Running the census on the located corpus is prerequisite to any
efficiency claim.

## Phase 10 — narrow transfer candidates (pending evidence)

Five candidates meet the *shape* of the eligibility rule (mechanical
capability + authority-free role + cost center) but none meets its *evidence*
bar here. Each entry in `narrow_transfer_candidates.json` carries its cheapest
discriminating experiment: translation lowering, advisory closure, narrow
lookups, atomic writer+receipt, L5 diagnostics. **Build order by risk, not
elegance:** writer/recalc/diff correctness suite first (infrastructure, no
capability experiment needed), everything else after its probe.

## The 15 direct answers

1. **Strong isolated evidence?** None verifiable in this workspace — for any
   component.
2. **Actual capability evidence?** None verifiable here.
3. **Only efficiency/reliability evidence?** None verifiable here; translation
   is the *hypothesized* efficiency primitive.
4. **Repairs of architecture-induced failures?** Unresolved for all four pairs;
   ablations specified but not runnable here.
5. **Useful with semantic authority held by the agent?** Hypothesized: L0
   substrate pieces, translation lowering, advisory closure, narrow lookups,
   writer/receipt, L5 flags. All pending probes.
6. **Dependency graph's role?** L0 representation + internal coordination;
   L1 exposure only as narrow on-demand facts; model-facing semantic injection
   excluded pending its own probe.
7. **Fingerprints' role?** Runtime-internal grouping keys (L0/L4); never
   model-facing business semantics.
8. **SQL justified?** Only as hidden L0 implementation; model-facing SQL needs
   a transfer win over agent Python.
9. **Is Mutation IR the best thin waist?** Undetermined — the audit's largest
   open question; the representability probe decides.
10. **Would transparent interception preserve capability better?** Unknown, but
    it is the correct hedge: zero agent-surface change, observer-first
    deployment, capture-completeness probe as gate.
11. **Where does the default agent spend stochastic work on mechanics?**
    Unknown here; conjectured centers are translation loops, search loops,
    verification re-opens, reference walks.
12. **Best-positioned old component per center?** Translation lowering,
    text/reference indexes, receipts/diagnostics, dependency lookups —
    respectively, all pending census confirmation.
13. **Evidence contradicting the proposal?** None *in* the workspace; the
    contradiction is the workspace itself — every supporting claim is
    unverifiable here, so proceeding on narrative alone is ungrounded. The
    eight falsifiers in `falsification_findings.json` stand open.
14. **What survives independent review?** The principle
    (harness = computation/invariants, model = semantic choice), the L0–L5
    layering as a test plan, hardened I/O as the safe first build, and the
    elimination logic (advisory-not-auto, pull-not-push, lower-not-synthesize).
15. **Single next experiment?** The zero-model **Mutation IR representability
    probe** over the located control-trajectory corpus
    (`next_experiment.json`) — capability gate first, unblocks B/C-vs-D and
    the Phase 9 census simultaneously. If the corpus is unlocatable, declare
    the program evidence-orphaned before any architecture decision.

## Final synthesis

### WHAT SURVIVED

- The design principle: harness owns computation and invariants; the model
  owns semantic choice (as a constraint on future work, not a finding).
- The layering (L0 substrate → L1 optional queries → L2 agent → L3 IR →
  L4 runtime → L5 diagnostics → L6 research-only) as an evaluation plan.
- Five narrow candidate roles with named discriminating experiments, in
  risk-order: writer/receipt infrastructure first.
- Three reusable methodological precedents from this repo: validated bounded
  retrieval programs (`retrieval_program.py`), read-only explorer boundaries,
  and the freeze-substrate/vary-access experiment design.

### WHAT DIED

- Nothing could be *confirmed* dead — and that is the point. Task IR, Edit
  Plan, generated authority, push grounding, harness synthesis, and
  auto-expanding closure are marked `ARCHAEOLOGY_ONLY` with a do-not-rebuild
  presumption, but burial requires the evidence corpus, not this audit.
- The idea that architectural elegance substitutes for transfer tests.
- Any efficiency ranking of agent work centers (conjecture only, census
  pending).

### WHAT MOVED TO A LOWER LAYER

Hypothetically, pending probes — nothing has moved in code, because nothing
spreadsheet exists in code:

- Dependency graph: semantic evidence → L0 representation + advisory use.
- Fingerprints: retrieval/translation driver → runtime-internal grouping keys.
- SQL: model-facing API → hidden L0 implementation.
- Translation: capability mechanism → explicitly-requested L4 lowering.
- Verifier: semantic gate → L5 observation layer.
- Closure: auto-expansion → advisory preview.
- Task IR / Edit Plan / scheduler: control path → L6 or dropped.

### WHAT WE STILL DO NOT KNOW

- Whether any background empirical claim is true (corpus absent).
- Whether a minimal Mutation IR covers real agent behavior (probe specified,
  unrunnable here).
- Whether interception captures completely, queries beat Python, or mechanics
  dominate agent cost (all probes specified, all unrunnable here).
- Where the spreadsheet evidence corpus lives, if it survives at all.

## Evidence-supported architecture (provisional — every box but L2/A-baseline is a hypothesis)

```text
                    ┌─────────────────────────────────┐
                    │  L2  GENERAL CODING AGENT       │
                    │  all semantic choice; raw task  │
                    │  Python/openpyxl surface kept   │
                    └───────────────┬─────────────────┘
                                    │ optional narrow reads (pull only,
                                    │ agent-named seeds, provenance back)
                    ┌───────────────▼─────────────────┐
                    │  L1  OPTIONAL MECHANICAL QUERIES│  ← transfer test gated
                    │  dependents/antecedents, text→  │
                    │  addresses, period coords       │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                    │  L0  COMPILED SUBSTRATE (hidden)│  ← build once, expose
                    │  cells · formulas · refs · dep  │     narrowly or never
                    │  graph · fingerprints · periods │
                    │  text index · provenance (SQL   │
                    │  inside, not model-facing)      │
                    └─────────────────────────────────┘

  Mutation path (B/C *or* D — representability probe decides):

   B/C: agent ──► L3 declared MutationBatch ──► L4 runtime ──► workbook
   D:   agent ──► familiar Python ──► capture ──► internal IR ──► L4 ──► workbook

                    ┌─────────────────────────────────┐
                    │  L4  DETERMINISTIC RUNTIME      │  ← build first: atomic
                    │  validate · lowering (explicit) │     write + recalc +
                    │  · atomic write · recalc · diff │     diff/receipt
                    │  / receipt · scope check        │
                    └───────────────┬─────────────────┘
                    ┌───────────────▼─────────────────┐
                    │  L5  DIAGNOSTICS (observe)      │
                    │  error flags · uniformity flags │
                    │  · affected diff; gate only on  │
                    │  near-zero-FP checks            │
                    └─────────────────────────────────┘
  L6: Task IR / Edit Plan / scheduler live here or nowhere (research-only).
```

*Reading rule for this diagram: L2 and the A-baseline (agent + L4-write +
L5-observe) are the only committable builds. Every other box is a labeled
hypothesis awaiting the probe named in its ledger row.*
