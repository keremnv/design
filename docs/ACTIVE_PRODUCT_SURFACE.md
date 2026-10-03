# Active product surface

Orientation for fresh agents. Status: working record, not architecture
authority. Baseline: `e189198f` (frozen minimum bounded Design product:
CONSTRUCT → INSPECT → JUDGE → INVESTIGATE → STOP).

## Active product path

This code defines the current product. Build on it:

```text
ontology_author/config_routes/        product facades (construct/inspect/judge/investigate)
ontology_author/software_governance/  construction, reads, validation, judgment, investigation
```

Proven operations: `construct_config_world`, `inspect_*`,
`judge_config_world`, `investigate_config_world`, J0/I0 persist/verify.
Acceptance: `tests/test_config_routes_phase{1,2,3}.py` plus the
`software_governance` construction/judgment/investigation suites.

## Generic OA support

Required machinery with no domain meaning. Use, do not extend
semantically:

```text
ontology_author/evidence/{markdown, program_source}   adapters: bytes, spans, digests
ontology_author/world/core/{store,kernel,model,contract,origins,source}
ontology_author/world/runtime/{world,commit}          ConstructionWorld, seal/publish
```

## Quarantined packages — do not use as precedent

Not on the product path. Zero production importers. Read and learn
from them; do not import them from new product code:

```text
ontology_author/authority/         authoritative-source construction over a spine
ontology_author/semantic_binding/  proposal/admission/persistence of bindings
ontology_author/governance/        adjudication, candidates, construction cycle
```

Rule: **new product code must not depend on quarantined architecture
unless a new experiment independently demonstrates the need for the
concept.** A large test suite or a console script is not such a
demonstration.

`ontology_author/program_spine/` is quarantined differently: not
product architecture, but its `comparison.py` correspondence
epistemics (continuity/outcome/basis vocabularies, sidecar
discipline) are findings worth mining. Do not adopt the matcher.

## Structural residue warning

These live inside Core-adjacent code but are historical residue, not
requirements. Do not build on them, do not remove them (a Core-format
decision must be earned separately):

```text
ContractWorldStore + _world_obligations/_world_obligation_candidates/
  _world_resolutions/_world_adjudications (empty in every product World)
SemanticRefKind(COMMITMENT/OBLIGATION)
world/runtime/purpose.py (self-declared legacy compatibility)
world/{cli,server,explorer,workspaces,project,entry} (old app / dev surfaces)
```

Importing anything under `ontology_author.world` currently also loads
several legacy modules through eager package `__init__` files. Loaded
is not used: the product path never calls them.

## Context hazards

A fresh agent will infer the wrong architecture from: the `governance`
console script (model-backed adjudication CLI — old application, not
product); the `author` console script (project-local Worlds, old
surface); ~70 fossil test files outside the 8-file default gate;
old `*_CONTRACT.md` docs; package names (`governance`,
`semantic_binding`) that imply active ownership; `ARCHITECTURE.md`
application-extension language that predates the frozen slices. Volume
is not authority. When in doubt, trace production importers: the
quarantined packages have none.

## How model revision is expected to happen

```text
evidence → model program (producer + constructor + profile/rules)
  → sealed World → real use → deficiency → change the model program
  → new sealed World at a fresh address
```

Prior Worlds stay valid and inspectable. No ontology migration, no
lineage tables, no global IDs, no admission/decision/action/workflow
machinery exists on this path, and none should be added without a
failing experiment that honest constructor revision cannot satisfy.

## Where to look

- Product behavior: `docs/CONFIG_ROUTE_DESIGN_SLICE_PHASE{1,2,3}_IMPLEMENTATION.md`
- Quarantine evidence: `docs/MODEL_EVOLVABILITY_AND_VESTIGIAL_AUDIT.md`
- Reusable ideas: comparison epistemics, proposal≠establishment,
  support≠authority, judgment≠decision≠action (see the audit §8)
- Next empirical work: `docs/SECOND_DOMAIN_MODEL_REFINEMENT_EXPERIMENT.md`
