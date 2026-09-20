# Grain traceability v1: token-usage analysis

Status: frozen post hoc analysis. No construction, consumer, World, benchmark,
gold, question, reference, or transcript artifact was modified.

## Result

The archived Codex usage counters support a descriptive comparison of reported
model tokens, but they do not support a token-amortization result for this
experiment. Both Worlds cost substantially more reported tokens per fresh
consumer than RAW, before adding their one-time construction costs. This
direction is unchanged when only non-cached input plus output is used as a
sensitivity measure.

The result is not a monetary-cost claim. No pricing model was applied.

## Frozen scope and source artifacts

Benchmark: `grain-traceability-v1`, commit
`17e1314f10d8b491b4462f821876a0a42642f1f8`.

Ontology Author: `0.1.0`, product commit
`17e1314f10d8b491b4462f821876a0a42642f1f8`.

Construction transcripts were read from:

* `/tmp/grain-traceability-v1-experiment-final-20260908/transcripts/OA-1.jsonl`
* `/tmp/grain-traceability-v1-experiment-final-20260908/transcripts/OA-2.jsonl`

Construction metadata was read from:

* `/tmp/grain-traceability-v1-experiment-final-20260908/metadata/construction_result_report.json`

Consumer transcripts were read from:

* `evaluation_runs/grain-traceability-v1-consumer-20260909/consumer_runs/<run>/transcript.jsonl`

The consumer campaign used two replicates per condition, not three. The
existing frozen harness record identifies the scored infrastructure attempt as
attempt 3; attempts 1 and 2 were not scored because of launcher isolation
problems.

## Extraction and validation rule

The current Codex CLI transcripts contain one `turn.completed` event with a
usage object per completed run. There are no per-tool usage objects and no
second terminal usage aggregate in any of the eight consumer transcripts or
the two construction transcripts. The first construction transcript line is a
non-JSON stdin notice and was ignored; all subsequent event records parse as
JSON.

The extraction rule was therefore:

1. parse the JSON event stream;
2. select the sole `turn.completed` usage object;
3. do not sum event snapshots or duplicate metadata copies;
4. record `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`,
   `output_tokens`, and `reasoning_output_tokens` exactly as reported;
5. calculate `noncached_input = input_tokens - cached_input_tokens`;
6. calculate `reported_total = input_tokens + output_tokens` because the
   transcript has no `total_tokens` field;
7. retain reasoning output separately and do not add it to `output_tokens`.

`input_tokens` is treated as total presented input, including the reported
cached component. `noncached_input` is a non-cached-input sensitivity measure,
not a monetary billing measure. `reasoning_output_tokens` is reported as a
diagnostic field; the archived product metadata does not establish that it is
additive to `output_tokens`.

The counters pass the following checks:

* exactly one terminal usage aggregate per run;
* cached input is no greater than input;
* cache-write input is zero in every recorded run;
* values are consistent with the number of turns, tool actions, and run
  duration;
* construction input is larger than consumer input, as expected for the
  longer multi-step construction sessions;
* the input values are not the implausible 21--48-token values documented in
  earlier truncated campaigns;
* no final run has an error exit code.

Accordingly, the grain counters are classified **TRUSTWORTHY for descriptive
reported-token accounting**. They are not asserted to be provider billing
receipts, and no dollar value is inferred. The classification does not make
the result portable across models, CLI versions, or billing systems.

## Construction usage

| Run | Duration (s) | Input | Cached input | Non-cached input | Output | Reasoning output | Reported total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OA-1 | 341.0 | 446,817 | 388,096 | 58,721 | 9,639 | 365 | 456,456 |
| OA-2 | 327.0 | 559,288 | 514,176 | 45,112 | 8,822 | 499 | 568,110 |

OA-1 had 10 rebuilds and OA-2 had 12 rebuilds. Both converged autonomously;
the construction report records no human semantic intervention. The two
construction totals are kept separate because they are replication costs for
different Worlds, not costs to be pooled into one World.

## Consumer usage: individual runs

| Condition | Run | Input | Cached input | Non-cached input | Output | Reasoning output | Reported total | Native source reads | Tool actions | Duration (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RAW | RAW-1 | 64,305 | 50,688 | 13,617 | 1,962 | 116 | 66,267 | yes | 4 | 71.3 |
| RAW | RAW-2 | 64,373 | 55,808 | 8,565 | 2,159 | 121 | 66,532 | yes | 5 | 78.6 |
| REFERENCE | REFERENCE-1 | 136,811 | 112,384 | 24,427 | 2,725 | 36 | 139,536 | no | 6 | 106.8 |
| REFERENCE | REFERENCE-2 | 136,108 | 112,384 | 23,724 | 2,522 | 34 | 138,630 | no | 6 | 96.5 |
| OA-1 | OA-1-1 | 184,509 | 144,128 | 40,381 | 2,551 | 17 | 187,060 | no | 8 | 98.6 |
| OA-1 | OA-1-2 | 199,451 | 150,656 | 48,795 | 2,482 | 11 | 201,933 | no | 8 | 97.5 |
| OA-2 | OA-2-1 | 163,545 | 131,968 | 31,577 | 2,716 | 36 | 166,261 | no | 8 | 104.0 |
| OA-2 | OA-2-2 | 160,738 | 123,648 | 37,090 | 2,667 | 40 | 163,405 | no | 8 | 102.7 |

The harness metadata uses `OA1-C1`, `OA1-C2`, `OA2-C1`, and `OA2-C2` for the
same four transcript snapshots whose directory/run IDs are shown above.

## Consumer aggregates

| Condition | Input mean / median / min--max | Cached mean | Non-cached input mean | Output mean / median / min--max | Reasoning mean | Reported total mean / median / min--max |
| --- | --- | ---: | ---: | --- | ---: | --- |
| RAW | 64,339 / 64,339 / 64,305--64,373 | 53,248 | 11,091 | 2,060.5 / 2,060.5 / 1,962--2,159 | 118.5 | 66,399.5 / 66,399.5 / 66,267--66,532 |
| REFERENCE | 136,459.5 / 136,459.5 / 136,108--136,811 | 112,384 | 24,075.5 | 2,623.5 / 2,623.5 / 2,522--2,725 | 35 | 139,083 / 139,083 / 138,630--139,536 |
| OA-1 | 191,980 / 191,980 / 184,509--199,451 | 147,392 | 44,588 | 2,516.5 / 2,516.5 / 2,482--2,551 | 14 | 194,496.5 / 194,496.5 / 187,060--201,933 |
| OA-2 | 162,141.5 / 162,141.5 / 160,738--163,545 | 127,808 | 34,333.5 | 2,691.5 / 2,691.5 / 2,667--2,716 | 38 | 164,833 / 164,833 / 163,405--166,261 |

The reference representation is not a construction-cost curve here: its
deliberate semantic engineering was performed before this frozen consumer
campaign and no comparable reference-construction usage total was recorded in
this artifact set.

## Observed amortization model

Using reported input plus reported output, the empirical curves are:

```text
RAW(n) = 66,399.5 n

OA-1(n) = 456,456 + 194,496.5 n
OA-2(n) = 568,110 + 164,833 n
```

For OA-1, the World-consumer slope is already greater than the RAW slope:

```text
194,496.5 > 66,399.5
```

For OA-2 the same holds:

```text
164,833 > 66,399.5
```

Thus neither curve has a non-negative break-even point. Algebraically, the
linear intersections are `n = -3.56` for OA-1 and `n = -5.77` for OA-2. These
are mathematical extrapolations, not usable reuse counts.

| n downstream consumers | RAW(n) | OA-1(n) | OA-2(n) |
| ---: | ---: | ---: | ---: |
| 1 | 66,399.5 | 650,952.5 | 732,943 |
| 2 | 132,799 | 845,449 | 897,776 |
| 5 | 331,997.5 | 1,428,938.5 | 1,392,275 |
| 10 | 663,995 | 2,401,421 | 2,216,440 |
| 25 | 1,659,987.5 | 5,318,868.5 | 4,688,935 |
| 100 | 6,639,950 | 19,906,106 | 17,051,410 |

The non-cached-input-plus-output sensitivity check is also unfavorable to the
Worlds:

```text
RAW(n)  = 13,151.5 n
OA-1(n) = 68,360 + 47,104.5 n
OA-2(n) = 53,934 + 37,025 n
```

The corresponding intersections are `n = -2.01` and `n = -2.26`. This check
does not turn the result into a billing claim; it shows that the direction is
not caused by counting cached input as if it were fresh input.

The reference consumer slope, 139,083 reported tokens, is also above RAW in
this protocol. That observation is descriptive and does not make the
deliberately engineered reference semantically worse: token use and semantic
adequacy are separate dimensions.

## Evidence-reading burden and work character

The existing frozen consumer telemetry records the qualitative split that the
token analysis must not erase:

| Condition | Native source files | World/reference sidecar reads | Source-specific parsing/reconciliation | Semantic queries | Tool actions |
| --- | ---: | ---: | --- | --- | ---: |
| RAW | 10--20 per run in the detailed audit | 0 | yes | not applicable | 4--5 |
| REFERENCE | 0 | 2--3 | no | yes | 6 |
| OA-1 | 0 | 2--3 | no | yes | 8 |
| OA-2 | 0 | 2--3 | no | yes | 8 |

RAW repeatedly opened native operational files and reconstructed aliases and
cross-source meaning. World consumers used more small schema/query actions,
but did not read native evidence. A higher token count for a World consumer
therefore coexists with the already demonstrated source-independence and work-
character shift. Tool calls, wall-clock, source reads, and tokens are not one
efficiency measure.

## Prior token evidence

The archived research corpus was searched beyond the named campaigns. The
following classifications use the same standard as this report and are not
pooled numerically across models or harnesses.

| Campaign | Model / condition | Archived token observation | Classification | Use in present claim |
| --- | --- | --- | --- | --- |
| Philips `reuse_raw_vs_product_v1` | Composer 2.5; RAW × 3, PRODUCT × 3 | Complete-looking per-run input/output/total fields were retained. RAW totals were 121,901--138,613; PRODUCT totals were 68,509--91,867. The report explicitly declined to make token cost the claim and did not include one-time construction cost. | PARTIAL | Supports that a consumer-side direction can be observed, not amortization. |
| Philips `frontier_organic_reuse_v1` | GPT-5.6 Sol Medium | Reported input values were 21--48 for consumers and 141/135 for construction; the frozen report calls the stream-JSON usage truncated and not a full budget. | TRUNCATED | Excluded from quantitative token conclusions. |
| BOM `llm_world_programming_v3` | GPT-5.6 Sol High | Median inputs 22.5 RAW and 27 WORLD; the report says these cannot be full-context usage and marks H4 token savings not measured. | TRUNCATED | Excluded. |
| BOM `llm_world_programming_composer25` | Composer 2.5 | Provider input/output/cache fields were retained, but the report explicitly classifies them as incomplete session accounting and records no monetary cost. | PARTIAL | Qualitative corroboration only; not pooled. |
| Capability `end_to_end_v1` | Composer 2.5; 18 consumers plus construction runs | Per-run input/output/total fields are present and usable descriptively, but the campaign did not freeze a construction-plus-repeated-consumption token amortization analysis. | PARTIAL | Supports availability of descriptive telemetry, not a pooled amortization result. |
| Capability `world_read_programming_v1`, `autonomous_world_exploration_v1`, NPDES, NIH | varied | Relevant reuse/source-independence findings exist, but no comparable validated token-amortization pair was frozen. | UNAVAILABLE for this claim | No numerical pooling. |

Prior evidence therefore supports source-independent World consumption and a
change in work character. It does not establish a general token-saving result.
The grain experiment is the first of this set in which construction and fresh
consumer counters are available in the same current-product experiment with
non-truncated-looking values. In this specific setting, those values run
against token amortization.

## Semantic versus token amortization

Semantic amortization is **supported**: fresh World consumers avoided repeated
native-source interpretation and reconciliation, while RAW consumers repeated
that work. The consumer comparison also showed that REFERENCE, OA-1, and OA-2
could be used without native source access.

Token amortization is a different claim. It would require the one-time
construction cost plus repeated World-consumption cost to fall below repeated
RAW-consumption cost at some non-negative reuse count. The observed curves do
not satisfy that condition for either independently constructed World, and the
non-cached sensitivity check agrees.

Monetary amortization is not demonstrated. No stable applicable price schedule
or provider billing receipt is present in the frozen artifacts.

TOKEN AMORTIZATION: NOT_SUPPORTED

SEMANTIC AMORTIZATION: SUPPORTED
