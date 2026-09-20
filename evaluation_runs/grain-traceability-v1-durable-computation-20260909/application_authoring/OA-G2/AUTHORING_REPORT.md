# Authoring report

Reusable grain-trace computations live in `application/`. They read only `world/world.sqlite` (read-only URI) plus caller parameters. They do not use native evidence, network, or an LLM, and they do not write the World.

## Interface

Call without reading Python:

```
application/run COMPUTATION --param value
```

`application/catalog.json` lists every computation. `application/manifests/<id>.json` names parameters and result fields.

| id | parameters | reuse |
| --- | --- | --- |
| `identifier_canonical` | `identifier` | alias map |
| `unresolved_failures` | optional `identity` | purpose gaps |
| `bin_tickets_before` | `bin`, `timestamp` | house occupancy before an event |
| `shipment_source_status` | `dispatch` | inbound tickets vs loadout bin |
| `processor_receipt_provenance` | `processor_receipt` | mill path + upstream source |
| `custody_owner_at` | `material`, `timestamp` | recorded owner/holder |
| `inspection_downstream_scope` | `sample` | forward links from a lab row |

Rules that are shared rather than task-specific:

- Identifier spellings go through `identifier_alias` (dispatch `PG-OUT-*` / `OUT-*`, lots `DR44`, bins `B-12` / `North House 12`).
- A hopper-named ticket is an established contributing identity. Quantity shares are not invented: `purpose_requirement_failure` and unnamed bin occupants stay unresolved.
- Ownership uses `[effective_start, effective_end)` with an empty end as open; `owner_after` / `holder_after` are owner and custodian. The `unrecorded_ownership` caveat is always attached.
- Sample downstream: mill receipt named in `material_hint` uses mill_process; otherwise tickets in `local_lot` are followed into later loadouts from their house.

World binding: hash `24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220`, sqlite sha256 `fdd4f332b7b5372bdfc1da6f0e9e1a33b96aa6c12c129768bec30e11f80f4586`, revision 95.

## Tests

`python3 application/tests/run_dev_tasks.py` passed 4 development tasks and 12 extra parameterized calls. The same four families were also invoked through `application/run`.

DEV-SRC-001 (`PGE-OUT-5001`): source location established as BIN-12 / Prairie Gate Elevator (LD-18). No hopper-named contributing tickets. Candidates in the house before loadout: DR-44, EF-18, WB-390. Allocation unresolved (`out_5001_ticket_composition`).

DEV-PROV-001 (`HFM-IN-601`): established path PGE-OUT-5001 / RL-8841 / HFM-IN-601; process MILL-2206 output FEED-2206. Upstream ticket allocation remains unresolved.

DEV-CUST-001 (`DR-44` at `2025-09-03T12:00:00-05:00`): covering TR-101; recorded owner and custodian Prairie Gate Elevator.

DEV-INSP-001 (`SMP-7714A`): sampled identity DR-44. No established downstream shipment, mill receipt, or output. Unresolved possible scope includes PGE-OUT-5001 (and therefore HFM-IN-601 / FEED-2206) and PGE-OUT-5003 (no mill slip in extracts). PGE-OUT-5002 is omitted because the hopper names WB-390 and EF-18, not DR-44.

Extra checks: PGE-OUT-5002 names EF-18 and WB-390 with quantity split unresolved; HFM-IN-604 has an established inbound path from PGE-OUT-5004 and no mill run; DR-44 at the 09:32 handoff is still owned by Prairie Gate with custodian Redline Haulage, then Hearthland after mill acceptance; SMP-602B (mill hint HFM-IN-602) established processed output FEED-2207; aliases `DR44` and `North House 12` resolve.
