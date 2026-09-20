# Frozen consumer protocol

Four conditions use identical model, harness, reasoning configuration, purpose,
question wording, and neutral consumer instruction. Each run is a fresh isolated
context. Two replicates per condition are used because three per condition was
not practical within the execution budget.

- RAW: host-visible evidence, frozen purpose, neutral questions and instruction.
- REFERENCE: evaluator-side materialized comparator (`model.json` + `instance.json`), frozen purpose, neutral questions and instruction. Native evidence, mappings, canonical truth, gold, and evaluator questions are excluded.
- OA-1: sealed OA-1 World, frozen purpose, neutral questions and instruction. Native evidence, construction artifacts, transcripts, evaluator/reference artifacts, and OA-2 are excluded.
- OA-2: sealed OA-2 World, frozen purpose, neutral questions and instruction. Native evidence, construction artifacts, transcripts, evaluator/reference artifacts, and OA-1 are excluded.

Consumer scoring is performed only after all runs are sealed. Construction
transcripts are not consulted during consumer scoring.
