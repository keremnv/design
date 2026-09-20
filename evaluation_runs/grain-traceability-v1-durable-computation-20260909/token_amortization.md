# Application-layer token amortization

Cursor result usage supplied `inputTokens`, `outputTokens`, `cacheReadTokens`, and `cacheWriteTokens`. No separate reasoning-output or provider-certified non-cached-input field was present, so this report does not derive a billable/non-cached sensitivity curve. Reported total is the descriptive sum `inputTokens + outputTokens`, matching the prior experiment’s descriptive convention but not a billing receipt.

| World | Author input | Author output | Author reported total | Synopsis mean total | Durable mean total | Durable mean input | Synopsis mean input | Break-even total n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OA-G1 | 110409 | 24952 | 135361 | 134688.7 | 143058.7 | 134008.7 | 124791.0 | none |
| OA-G2 | 206880 | 29114 | 235994 | 137867.0 | 134229.7 | 125882.0 | 128854.7 | 64.88 |

## Curves

| n | OA-G1 Synopsis | OA-G1 Durable | OA-G2 Synopsis | OA-G2 Durable |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 134688.7 | 278419.7 | 137867.0 | 370223.7 |
| 2 | 269377.3 | 421478.3 | 275734.0 | 504453.3 |
| 5 | 673443.3 | 850654.3 | 689335.0 | 907142.3 |
| 10 | 1346886.7 | 1565947.7 | 1378670.0 | 1578290.7 |
| 25 | 3367216.7 | 3711827.7 | 3446675.0 | 3591735.7 |
| 100 | 13468866.7 | 14441227.7 | 13786700.0 | 13658960.7 |

OA-G1 durable consumers used more reported tokens than synopsis consumers, so there is no break-even. OA-G2 durable consumers used slightly fewer reported tokens than synopsis consumers; the one-time application authoring cost yields an empirical break-even of approximately 64.9 repeated uses. This is descriptive token amortization only, not monetary amortization.
