# Frozen world-context orientation experiment

Experiment: `grain-traceability-v1-world-context-20260909`

This experiment tests consumption orientation only. It does not modify Ontology
Author, either sealed World, the grain benchmark, the purpose, the questions,
gold, or any prior evaluation artifact.

## Research question

Does a compact deterministic description of a sealed World's semantic interface
reduce the repeated model-context and orientation cost of fresh World
consumption, without reducing semantic performance or increasing false closure?

## Frozen renderer

`world_context_renderer.py` version `world-context-renderer-v1.0.0` renders
only mechanically recoverable World metadata. It reads the four sealed bundle
entry points, the World metadata tables, relation role/type declarations,
derivation metadata, completeness metadata, and grounding/origin counts.

It does not read data rows, referent rows, source evidence, construction
artifacts, transcripts, benchmark files, evaluator files, or gold. It does not
use an LLM. Output is UTF-8 with LF newlines and deterministic sorted ordering.

The output may contain:

* World identity and revision;
* stored purpose text;
* exact relation names, modes, scopes, roles, role types, and assertion counts;
* derivation inputs, state, execution status, and output counts;
* completeness target/universe, status, basis, and explicitly recorded gaps;
* structural unresolvedness relation names, roles, and counts;
* grounding mechanism names and aggregate counts;
* actual bundle entry-point filenames.

It contains no tuples, referent identifiers, source facts, answer examples,
recommended joins, inferred descriptions, construction explanations, or
benchmark/evaluator material.

## Conditions

Each fresh consumer receives the same frozen purpose, downstream question set,
neutral instruction, one copied read-only sealed World, and an isolated writable
Codex home. `DISCOVERY` does not receive `world-context.md`. `SYNOPSIS` receives
the same files plus the generated `world-context.md` at the workspace root.
The consumer prompt and model configuration are identical. No optional verbose
metadata control is used; the two-arm comparison is cleaner and sufficient for
the precommitted hypothesis.

## Replicates and environment

Three fresh replicates are run for each World and condition:

```text
OA1-DISCOVERY-1..3   OA1-SYNOPSIS-1..3
OA2-DISCOVERY-1..3   OA2-SYNOPSIS-1..3
```

Model: `gpt-6-astra`. Reasoning: `medium`. Harness: Codex CLI `0.153.4` via
isolated bwrap workspaces, with writable private Codex homes and the sealed
World copied read-only into each consumer workspace.

## Precommitted hypotheses

* **H1 semantic non-inferiority:** SYNOPSIS does not reduce semantic correctness
  or increase false closure relative to DISCOVERY.
* **H2 input-context reduction:** SYNOPSIS reduces mean fresh-consumer input
  tokens relative to DISCOVERY.
* **H3 orientation-action reduction:** SYNOPSIS reduces explicit schema and
  metadata orientation actions.
* **H4 faster semantic engagement:** SYNOPSIS reduces time/actions before the
  first task-relevant semantic query.
* **H5 representation independence:** any benefit appears for both OA-1 and
  OA-2 despite their different schemas.

No hypothesis requires success for the experiment to be informative.

## Frozen measurements

For every run, preserve the full JSONL transcript, run metadata, workspace file
inventory, final answer, and hashes. Extract the sole final `turn.completed`
usage event using the existing grain token procedure: input, cached input,
non-cached input, output, reasoning output, and reported total.

Record semantic verdicts against the frozen novel gold, tool actions, SQLite and
Python actions, file reads, schema/metadata inspection, semantic-data queries,
time to first task-relevant semantic query, and wall-clock duration.

Observable orientation categories are `WORLD_IDENTITY_DISCOVERY`,
`RELATION_INVENTORY_DISCOVERY`, `ROLE_SCHEMA_DISCOVERY`,
`DERIVATION_DISCOVERY`, `COMPLETENESS_DISCOVERY`,
`UNRESOLVEDNESS_DISCOVERY`, `GROUNDING_DISCOVERY`,
`TASK_SEMANTIC_QUERY`, and `ANSWER_REASONING`. Classification is based only on
observable tool/file/query actions, never hidden reasoning.

## Freeze boundary

The renderer, generated contexts, protocol, prompts, evaluator, and telemetry
extraction are frozen before the first consumer is launched. No context or
prompt is revised after observing a run. If a defect is found, this frozen
version is retained and any correction receives a new experiment version.
