# Authoring report

## Interface

`application/` is a sealed-World computation bundle. Callers use `application/run.py` and `application/catalog.json`; they do not need to read Python sources.

```
python3 application/run.py --list
python3 application/run.py <computation_id> --param NAME=VALUE [--pretty]
python3 application/run.py <computation_id> --params-json '{"dispatch":"PGE-OUT-5001"}'
```

Each computation is parameterized, read-only on `world/world.sqlite`, and prints one JSON object with `sort_keys=True`. Results include `world_binding` (world id, revision, sqlite sha256 check against the bound World).

Four computations cover the reusable grain-trace questions:

| id | parameters | what it establishes vs leaves unresolved |
|---|---|---|
| `shipment_source_status` | `dispatch` | Loadout bin as source location; hopper `ticket_named_on_move` as named contributors (not quantity splits); commercial ownership scopes marked as not bin allocation; `purpose_requirement_failure` rows for physical allocation / missing mill receipt / kg differences |
| `processor_receipt_provenance` | `processor_receipt` | `mill_intake` → movement/loadout/carrier; named tickets and commercial ticket scopes; `mill_process` output if present; same unresolved attachments |
| `custody_owner_at` | `material`, `timestamp` | Covering `ownership_event` rows (`start <= t < end`, open end if empty); owner from latest non-empty `owner_after`; custodian from latest non-empty `holder_after` |
| `inspection_downstream_scope` | `sample` | Ticket only if lab local lot / hint resolves uniquely and there is no lab unresolved failure; downstream shipment/receipt/output only via ownership basis that names a manifest or mill receipt; later loadouts from the intake bin listed as physical candidates, not as established allocation |

Shared rules used across families:

- Tokens resolve through `known_as`, referent labels/ids, and a few typed columns (`dispatch_ref`, receipt numbers, bills of lading).
- Consignee codes are not treated as mill receipts (`consignee_is_not_receipt`).
- Unresolved rows attach when a requirement id, affected identity, or structured subject field (not the prose `reason`) names the queried identity.

World binding: `v0` revision 242, sqlite sha256 `b2053bcf7c9e02a39b64a77065ff952c4357e494b024292c08eb9a6ff9481a4c`. Connections open `mode=ro` with `PRAGMA query_only`.

## Tests

Ran `python3 application/tests/run_dev_tasks.py`, which invokes the catalog entrypoint twice per development task and requires identical JSON.

- **DEV-SRC-001** `dispatch=PGE-OUT-5001`: source location North House 12; no hopper-named contributing tickets; bin occupants DR-44 / WB-390 / EF-18 before loadout; commercial DR-44 scopes on RL-8841 / HFM-IN-601 not treated as allocation; `source_allocation_unresolved` true with `physical-ticket-allocation-PGE-OUT-5001` (and recorded kg difference on the established movement).
- **DEV-PROV-001** `processor_receipt=HFM-IN-601`: upstream movement PGE-OUT-5001 / RL-5001-A / North House 12; process MILL-2206 → FEED-2206 starter feed; same physical-allocation and quantity-difference unresolved rows.
- **DEV-CUST-001** `material=DR-44` at `2025-09-03T12:00:00-05:00`: covering TR-101; owner and custodian Prairie Gate Elevator; no unresolved ownership identity at that instant.
- **DEV-INSP-001** `sample=SMP-7714A`: source ticket DR-44 established from lab lot/hint; established downstream PGE-OUT-5001, HFM-IN-601, FEED-2206; physical BIN-12 loadouts 5001–5003 listed without treating them as allocated; unresolved physical allocation on 5001 and 5003 (and absent East mill receipt on 5003).

Additional parameterized calls (not gold, interface checks):

- `PGE-OUT-5002`: named contributors EF-18 and WB-390; no physical-allocation failure.
- `PGE-OUT-5003`: location established; no named tickets; mill-receipt-absent and physical-allocation unresolved.
- `HFM-IN-604`: upstream OUT-5004 with no mill_process row; physical-allocation-5004 unresolved.
- `SMP-604Q`: source ticket not established; `lab-sample-SMP-604Q-ticket` preserved; no established downstream.

Missing required parameters and unknown computation ids exit 2. Repeat invocations of each development task were byte-identical.
