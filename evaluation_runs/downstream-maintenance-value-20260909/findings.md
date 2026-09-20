# Downstream value of same-purpose maintenance — 2026-09-09

**Status:** isolated Composer 2.5 run. Product not changed.

**Question:** Does semantic maintenance during one task produce durable state that improves a fresh agent's performance on different later same-purpose work?

**Model:** every `system/init.model` was `Composer 2.5`.

## Design

One coarse `yard-trace` World (hopper/`bin_movements` omitted; `PGE-OUT-5004` allocation not recorded as unresolved). Two isolated copies.

| Condition | Upstream | Intended World |
|---|---|---|
| A unmaintained | Ordinary U1 then U2; no maintenance sentence | Unchanged coarse World |
| B maintained | Same tasks plus “keep the existing World adequate for future work within its declared purpose” | Same named World, rebuilt |

U1: hopper tickets on the 26,000 kg OUT-5002 move.  
U2: which ticket supplied PGE-OUT-5004.

Downstream agents received **only** `.worlds/yard-trace/world/` (sqlite + sidecars), attached capability, and a short README. No evidence tree, no `construction.py`, no PURPOSE.md, no upstream transcripts or answers.

Later tasks (not the upstream wording):

| ID | Case | Later question |
|---|---|---|
| D1 | Positive reuse | Which Prairie Gate tickets were named as sources of mill batch **FEED-2207**? |
| D2 | Uncertainty reuse | Can **MCR-118** be certified as the sole Prairie Gate source of **HFM-IN-604**? |
| D3 | Unrelated control | Mill slip/run for **PGE-OUT-5001** |

## Upstream

| Run | Rebuild? | Result |
|---|---|---|
| A-U1 | No | Correct from CSV (`WB-390`, `EF-18`). World unchanged. |
| A-U2 | No | Correct refusal. World unchanged. |
| B-U1 | `author rebuild yard-trace` | Added `bin_movement` and `hopper_ticket_named`; recorded `out_5003_hopper_tickets` and `out_5004_hopper_tickets`. |
| B-U2 | No further rebuild | Answered from the already-maintained World; cited `out_5004_hopper_tickets`. |

Condition A tables remain intake/loadout/manifest/mill/`dispatch_to_mill`. Condition B adds hopper structure plus explicit unresolvedness for BM-009 / OUT-5004. PURPOSE.md was not broadened. No second World. No sqlite patch.

## Downstream (judged by answer text, not the crude string scorer)

Automatic `score_summary.json` over-flagged D2 because the prompt itself contains “certified” / “sole source”. Judged results:

| Consumer | Distinction materializable in World? | Answer | Notes |
|---|---|---|---|
| **A-D1** | Named hopper association **absent** | WB-390 and EF-18 via **FIFO quantity matching**, plus an **unsupported kg split** (2,150 kg of EF-18). Timed out (124) after ~25 min. | Not World-native named tickets. Invented allocation quantities the hopper note does not give. Then hunted missing source files (hash-brute-force of CSVs, search of the installed package, `author open --help`). |
| **B-D1** | `hopper_ticket_named` / BM-004 **present** | WB-390 and EF-18 from hopper paperwork for OUT-5002 → HFM-IN-602 / MILL-2207. | Queried `hopper_ticket_named` and `bin_movement`. No kg split. Exit 0. |
| **A-D2** | Explicit OUT-5004 unresolved **absent** | **No** — two tickets in B-14, loadout does not name tickets. | Re-derived unresolvedness from intake+loadout. Did not pick MCR-118. |
| **B-D2** | `out_5004_hopper_tickets` + BM-009 **present** | **No** — BM-009 `no individual ticket`; purpose leaves allocation unresolved. | World-native unresolvedness. |
| **A-D3** | Control already in both Worlds | HFM-IN-601 / MILL-2206 | |
| **B-D3** | Same | HFM-IN-601 / MILL-2206 | Equivalent |

Raw evidence files were not in the workspace. “evidence/…” strings in some transcripts are SOURCE grounding locators inside sqlite, not recovered CSVs.

## Token usage (secondary)

| ID | input | output | cache read |
|---|---|---|---|
| A-D1 | (timeout; none recorded) | | |
| B-D1 | 10529 | 2389 | 163936 |
| A-D2 | 19283 | 5090 | 286272 |
| B-D2 | 15383 | 3253 | 158912 |
| A-D3 | 10552 | 1156 | 107859 |
| B-D3 | 10634 | 1194 | 91486 |

Maintained D1/D2 used fewer tokens and finished cleanly. Unmaintained D1 spent the timeout searching for evidence the World does not contain.

## What this shows

**Positive reuse: yes, with a caveat.** The maintained World lets a later agent *compute* hopper-named sources of FEED-2207 from World relations. The unmaintained World does not preserve that named association. A capable consumer can still *guess* the same two tickets from bin occupancy and loadout weights (FIFO), and then over-commit on quantities. Maintenance replaced that reconstruction with a durable, queryable distinction.

**Uncertainty reuse: weaker contrast than the cartoon.** Composer 2.5 refused MCR-118 as sole source of HFM-IN-604 on **both** Worlds. The coarse World still contains two B-14 intakes and a ticket-less loadout, which is enough for this model to refuse. The maintained World made that refusal **explicit and hoppersheet-grounded** (`purpose_requirement_failure` + BM-009) rather than re-derived.

**Control: equivalent.** Maintenance did not disturb mill dispatch→receipt→run for PGE-OUT-5001.

## Friction (not a product-change trigger)

1. **Sealed-World-only consumption vs provenance pointers.** A-D1 saw SOURCE locators such as `evidence/loadout_log.csv` and tried to reconstruct the missing files (hash search, package search under the bound `~/.local` install). Capability already says project evidence is needed for provenance verification. The harness also ro-binds `~/.local` so `author` works; that made the install searchable. Do not add a kernel “sealed consumer mode” from one timeout.
2. **`author open` remains a timeout risk.** A-D1 called `author open yard-trace --help` among other recovery steps. The earlier probe hung on `author open` itself.
3. **String scoring of “certified” in the prompt is useless.** Judge D2 from whether the agent affirms sole-source certification.

## Product implication

**No product change.**

Maintenance during upstream work **did** produce durable state a later agent used: `hopper_ticket_named` answered a mill-side question that was never asked upstream. Explicit unresolvedness was used when present, and was not required for this model to refuse D2.

The unmaintained World is not empty of related facts (intakes, loadouts, mill joins). Same-purpose maintenance is valuable where the missing carving is **not reconstructible** from those remaining facts without extra assumptions. D1 is that case (named hopper association vs FIFO). D2 was reconstructible as underdetermination, so both consumers refused.

A later probe could withhold mill joins as well, or use a weaker model, if the goal is a sharper D2 gap. That is not a reason to add revision machinery.
