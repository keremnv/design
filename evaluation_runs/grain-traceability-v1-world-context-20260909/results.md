# Grain traceability v1: World context orientation results

Status: frozen consumer results. No World, benchmark, gold, question, prior evaluation, or Ontology Author artifact was modified.

## Protocol integrity

Twelve fresh consumers completed successfully: three DISCOVERY and three SYNOPSIS runs for each of OA-1 and OA-2. Each workspace contained one copied read-only sealed World, the frozen purpose, the frozen NQ-01..NQ-10 questions, the neutral instruction, and—only in SYNOPSIS—the frozen deterministic `world-context.md`. Native evidence was absent from every workspace.

The sole final `turn.completed` usage event was extracted per run using the existing grain token procedure. There were no duplicate usage snapshots. Per-action timestamps are not present in Codex JSONL, so time-to-first-query is reported as unavailable; action index is reported instead.

## World-context artifacts

| World | Relations / referents / assertions | Context bytes | Context words | Model-tokenizer tokens | Context SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| OA-1 | 19 / 85 / 293 | 4,118 | 488 | N/R | `121b037b7474bdee6b7f75f2bf31035fd05f78983ec2c69fa1110ff16a7e91af` |
| OA-2 | 17 / 66 / 185 | 3,773 | 464 | N/R | `eff6c43e90fd7aafee645d6bef5a7edf0675a2c34796fbccc7e7ad351cd97ca4` |

The renderer is deterministic, non-LLM, and emits only stored purpose/interface metadata, structural derivation/completeness/unresolvedness/grounding mechanisms, and access filenames. Manual audit found no question IDs, source identifiers, source filenames, sample tuples, evaluator terms, or benchmark answers in either context. No reliable local tokenizer for `gpt-6-astra` was available, so model-tokenizer counts are N/R rather than estimated.

## Primary scorecard

| Metric | OA1 Discovery | OA1 Synopsis | OA2 Discovery | OA2 Synopsis |
| --- | ---: | ---: | ---: | ---: |
| Correct questions | 9/10 | 9/10 | 9/10 | 9/10 |
| Partial questions | 1/10 | 1/10 | 1/10 | 1/10 |
| Unsupported closure | 0 | 0 | 0 | 0 |
| Mean input tokens | 192,037.67 | 189,328 | 167,479 | 141,240.33 |
| Mean cached input | 143,616 | 147,456 | 129,578.67 | 117,248 |
| Mean non-cached input | 48,421.67 | 41,872 | 37,900.33 | 23,992.33 |
| Mean reported total | 194,789.33 | 191,943.67 | 170,199.33 | 143,923 |
| Mean tool actions | 7 | 7 | 7 | 6.33 |
| Mean orientation actions | 3.33 | 4 | 4 | 3.33 |
| First semantic query action | 6 | 6 | 6 | 6 |
| Time to first semantic query | N/R | N/R | N/R | N/R |

All 12 runs had the same question-level semantic result: NQ-01 was PARTIAL because the frozen World did not materialize the evaluator's 15,000/11,000 kg contributor split; NQ-02 through NQ-10 were CORRECT. No run made an unsupported closure or incorrectly resolved a frozen ambiguity. The NQ-01 evidence-grounding caveat remains the same as in the frozen direct evaluation: the visible operational evidence establishes contributors and combined mass, not the individual split.

## Individual runs

| Run | Input | Cached | Non-cached | Output | Reasoning | Total | Tools | Orientation | First semantic action | Duration (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OA-1-DISCOVERY-1 | 186,513 | 145,792 | 40,721 | 2,947 | 72 | 189,460 | 7 | 4 | 6 | 115.0 |
| OA-1-DISCOVERY-2 | 202,184 | 157,312 | 44,872 | 2,687 | 10 | 204,871 | 7 | 3 | 6 | 109.7 |
| OA-1-DISCOVERY-3 | 187,416 | 127,744 | 59,672 | 2,621 | 10 | 190,037 | 7 | 3 | 6 | 110.7 |
| OA-1-SYNOPSIS-1 | 188,744 | 142,080 | 46,664 | 2,660 | 22 | 191,404 | 7 | 4 | 6 | 103.3 |
| OA-1-SYNOPSIS-2 | 189,617 | 150,144 | 39,473 | 2,616 | 21 | 192,233 | 7 | 4 | 6 | 103.1 |
| OA-1-SYNOPSIS-3 | 189,623 | 150,144 | 39,479 | 2,571 | 23 | 192,194 | 7 | 4 | 6 | 109.1 |
| OA-2-DISCOVERY-1 | 166,089 | 129,024 | 37,065 | 2,701 | 12 | 168,790 | 7 | 4 | 6 | 107.0 |
| OA-2-DISCOVERY-2 | 175,066 | 127,616 | 47,450 | 2,650 | 15 | 177,716 | 7 | 4 | 6 | 105.1 |
| OA-2-DISCOVERY-3 | 161,282 | 132,096 | 29,186 | 2,810 | 53 | 164,092 | 7 | 4 | 6 | 105.2 |
| OA-2-SYNOPSIS-1 | 128,137 | 104,064 | 24,073 | 2,697 | 43 | 130,834 | 6 | 3 | 6 | 100.2 |
| OA-2-SYNOPSIS-2 | 115,874 | 94,208 | 21,666 | 2,708 | 61 | 118,582 | 6 | 3 | 6 | 101.0 |
| OA-2-SYNOPSIS-3 | 179,710 | 153,472 | 26,238 | 2,643 | 41 | 182,353 | 7 | 4 | 6 | 112.2 |

## Token comparison

Mean input and reported total tokens were lower with SYNOPSIS for both Worlds:

* OA-1 input: 192,037.7 → 189,328.0, a 1.41% reduction; reported total reduction 1.46%.
* OA-2 input: 167,479.0 → 141,240.3, a 15.67% reduction; reported total reduction 15.44%.

The OA-1 reduction is small and not consistent in paired replicates: two synopsis runs were slightly higher than their same-number discovery counterparts. OA-2 shows a larger mean reduction, but one synopsis replicate was higher than discovery. The result supports a descriptive orientation-token effect, not a precise universal savings rate.

## Observable orientation work

The evaluator classified completed shell/Python actions by mechanically observable command content. An action can receive multiple category labels. Orientation actions are distinct commands carrying at least one of the seven orientation categories; semantic-query actions are counted separately. No hidden reasoning was classified.

| Category | OA1 Discovery mean | OA1 Synopsis mean | OA2 Discovery mean | OA2 Synopsis mean |
| --- | ---: | ---: | ---: | ---: |
| WORLD_IDENTITY_DISCOVERY | 1.00 | 1.00 | 1.00 | 1.00 |
| RELATION_INVENTORY_DISCOVERY | 1.33 | 1.00 | 1.33 | 1.33 |
| ROLE_SCHEMA_DISCOVERY | 1.00 | 1.00 | 1.00 | 1.00 |
| DERIVATION_DISCOVERY | 0.67 | 0.00 | 1.00 | 0.00 |
| COMPLETENESS_DISCOVERY | 0.67 | 0.00 | 1.00 | 0.00 |
| UNRESOLVEDNESS_DISCOVERY | 1.00 | 1.00 | 1.00 | 1.00 |
| GROUNDING_DISCOVERY | 2.00 | 2.00 | 2.00 | 1.00 |

The mean distinct orientation-action count was OA-1 3.33 DISCOVERY versus 4.00 SYNOPSIS, and OA-2 4.00 DISCOVERY versus 3.33 SYNOPSIS. Pooled across Worlds there is no reduction. The first semantic-query action was action 6 in every run. Codex JSONL has no per-action timestamps, so a wall-clock H4 result cannot be claimed.

SYNOPSIS consumers still inspected SQLite schema and World sidecars, and they continued to perform semantic-data queries. The synopsis was used as an orientation aid, not as a replacement for checking the World.

## Source independence and run integrity

* Native evidence reads: 0/12; no `evidence/` directory was mounted.
* World bundles were copied read-only into each workspace; the original sealed Worlds were not mounted as writable targets.
* All 12 runs exited 0 and produced one terminal usage event.
* All workspaces contained only the intended purpose, questions, instruction, World bundle, and optional synopsis, plus any consumer-created files captured by the workspace inventory.
* Full transcripts, run metadata, workspace inventories, the run index, renderer, contexts, and freeze manifest are preserved beside this report.

## Hypothesis judgments

* H1 semantic non-inferiority: SUPPORTED. Semantic verdicts and false-closure behavior were identical across paired conditions.
* H2 input-context reduction: SUPPORTED DESCRIPTIVELY. Both World means declined, but OA-1 was small and paired variability was substantial.
* H3 orientation-action reduction: NOT SUPPORTED. No pooled reduction; OA-1 increased and OA-2 decreased.
* H4 faster semantic engagement: NOT SUPPORTED on observable action index; wall-clock time is unavailable at action granularity.
* H5 representation independence: PARTIALLY SUPPORTED. Mean input reduction appeared for both materially different Worlds, while action reduction did not replicate for both.

SEMANTIC NON-INFERIORITY: SUPPORTED

ORIENTATION TOKEN REDUCTION: SUPPORTED

ORIENTATION ACTION REDUCTION: NOT_SUPPORTED
