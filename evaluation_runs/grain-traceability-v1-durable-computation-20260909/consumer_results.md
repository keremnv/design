# Fresh held-out consumer results

Three fresh Cursor CLI consumers were run per World and condition. Native evidence was physically unavailable in all twelve workspaces; native-source reads were zero.

| Metric | OA-G1 Synopsis | OA-G1 Durable | OA-G2 Synopsis | OA-G2 Durable |
| --- | ---: | ---: | ---: | ---: |
| Correct | 25 | 25 | 28 | 25 |
| Partial | 5 | 5 | 2 | 5 |
| Unsupported closure | 0 | 0 | 0 | 0 |
| Mean input tokens | 124791 | 134008.7 | 128854.7 | 125882 |
| Mean reported total | 134688.7 | 143058.7 | 137867 | 134229.7 |
| Mean tool actions | 22.33 | 28.67 | 20 | 22.67 |
| Mean ad hoc semantic queries | 5 | 2 | 3.67 | 2.67 |
| Mean computation invocations | n/a | 8.33 | n/a | 2.67 |

## Per-run results

| Run | Condition | Correct | Partial | Input | Output | Reported total | Tools | Ad hoc queries | App invocations | Reuse class |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| OA-G1-DURABLE-1 | DURABLE | 8 | 2 | 151062 | 9438 | 160500 | 27 | 2 | 4 | DURABLE_PLUS_WORLD |
| OA-G1-DURABLE-2 | DURABLE | 8 | 2 | 76356 | 9189 | 85545 | 29 | 2 | 10 | DURABLE_PLUS_WORLD |
| OA-G1-DURABLE-3 | DURABLE | 9 | 1 | 174608 | 8523 | 183131 | 30 | 2 | 11 | DURABLE_PLUS_WORLD |
| OA-G1-SYNOPSIS-1 | SYNOPSIS | 8 | 2 | 85942 | 8812 | 94754 | 26 | 5 | 0 | n/a |
| OA-G1-SYNOPSIS-2 | SYNOPSIS | 9 | 1 | 118699 | 12208 | 130907 | 21 | 6 | 0 | n/a |
| OA-G1-SYNOPSIS-3 | SYNOPSIS | 8 | 2 | 169732 | 8673 | 178405 | 20 | 4 | 0 | n/a |
| OA-G2-DURABLE-1 | DURABLE | 8 | 2 | 182205 | 9733 | 191938 | 26 | 3 | 4 | DURABLE_PLUS_WORLD |
| OA-G2-DURABLE-2 | DURABLE | 8 | 2 | 79310 | 8286 | 87596 | 23 | 4 | 3 | DURABLE_PLUS_WORLD |
| OA-G2-DURABLE-3 | DURABLE | 9 | 1 | 116131 | 7024 | 123155 | 19 | 1 | 1 | DURABLE_PLUS_WORLD |
| OA-G2-SYNOPSIS-1 | SYNOPSIS | 10 | 0 | 220681 | 9619 | 230300 | 25 | 5 | 0 | n/a |
| OA-G2-SYNOPSIS-2 | SYNOPSIS | 9 | 1 | 94411 | 8390 | 102801 | 20 | 4 | 0 | n/a |
| OA-G2-SYNOPSIS-3 | SYNOPSIS | 9 | 1 | 71472 | 9028 | 80500 | 15 | 2 | 0 | n/a |

All durable runs adopted the bundle at least once, but all were `DURABLE_PLUS_WORLD`: they invoked computations and also inspected the World or authored additional semantic queries. No run qualified as `PURE_DURABLE`; no run was `WORLD_FALLBACK`.

The gold-sensitive partials are concentrated in ownership/custody scope and South House 14 inspection linkage. No unsupported closure was observed in manual review.
