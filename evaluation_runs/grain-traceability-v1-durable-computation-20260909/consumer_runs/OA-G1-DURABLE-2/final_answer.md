# Grain traceability held-out answers

World binding: id `v0`, revision `242`, hash `dc2e7e45c1327fc997691b4fa4071c5fd44edb6aed2b57e2d1e4e4c70a471eb8`. Catalog computations were used as parameterized queries and checked against World relations. Where a computation omitted a World-grounded link (notably lab `material_hint` on SMP-602B), the World record is treated as authoritative. Unsupported identity and blend allocation are left unresolved.

---

## EVAL-SRC-001

family: `shipment_source_status`  
query: dispatch `PGE-OUT-5002`

**Established contributing inbound identities**
- `WB-390` (`ticket:wb-390`, receipt `ER-7721`)
- `EF-18` (`ticket:ef-18`, receipt `ER-7729`)

Basis: hopper/bin transfer `move:BM-004` (`work_order` `OUT-5002`, note `WB-390 / EF-18`) with `ticket_named_on_move` spans for both tickets. North House 12 also held `DR-44` before this loadout; `DR-44` is not named on this move and is not established as contributing to this dispatch.

**Established source location**
- Prairie Gate Elevator, bin **North House 12** (`bin:north-house-12`)
- Loadout `LD-19` at `2025-09-04T13:15:00-05:00`, 26000 kg, truck `nst-204`, carrier manifest `NS-8848` / BOL `NS-5002-B`

**Individual source allocation**
- Which tickets contribute is established (both named).
- Quantity split between `WB-390` and `EF-18` is **not** established (`named_not_quantity_allocation`).
- World does **not** record `physical-ticket-allocation-PGE-OUT-5002`; `source_allocation_unresolved` for this dispatch is **false**.

**Other unresolved (not a different movement)**
- Loadout 26000 kg vs mill intake 25500 kg on `HFM-IN-602` (`quantity-differences-on-established-movements`).

---

## EVAL-SRC-002

family: `shipment_source_status`  
query: dispatch `PGE-OUT-5003`

**Established source location**
- Prairie Gate Elevator, bin **North House 12** (`bin:north-house-12`)
- Loadout `LD-20` at `2025-09-05T07:10:00-05:00`, 12000 kg, truck `nst-219`, manifest `NS-8910` / BOL `NS-5003-C`, consignee code `HFM-E`

**Established inbound material identity**
- **None.** Hopper note is `no ticket on hopper sheet`. Handwritten cargo mark `N3 / EF-18?` is not a validated source ticket (`N3` is used as a route code elsewhere). Bin occupants before loadout (`DR-44`, `WB-390`, `EF-18`) are not allocated to this truck.

**Missing / unresolved source linkage**
- `physical-ticket-allocation-PGE-OUT-5003`: no validated inbound ticket.
- `mill-receipt-absent-PGE-OUT-5003`: carrier departure is recorded; no Hearthland receiving slip is in the extracts. HFM-North log completeness does not support a conclusion about East mill receiving. Consignee code is not a mill receipt.

`source_allocation_unresolved`: **true**.

---

## EVAL-SRC-003

family: `shipment_source_status`  
query: dispatch `PGE-OUT-5004`

**Established contributing inbound identities**
- **None** (hopper note `no individual ticket`; no `ticket_named_on_move` on the outbound work order).

Bin occupants before loadout (candidates, not allocated):
- `MCR-118` (`ER-7744`, grower recorded `M. Creek`)
- `S-52` (`ER-7750`, Sunnyside Acres)

**Source location (established, not asked as identity)**
- Prairie Gate Elevator, **South House 14**; loadout `LD-21`, 19000 kg.

**Individual allocation**
- **Unresolved** (`physical-ticket-allocation-PGE-OUT-5004`): two deliveries in South House 14; loadout desk did not record which supplied which part of the truck. `source_allocation_unresolved`: **true**.

**Other unresolved**
- Loadout 19000 kg vs mill 18800 kg on `HFM-IN-604` (`quantity-differences-on-established-movements`).
- Grower identity of `MCR-118` remains `mcr-118-grower-identity` (Meadow Creek Farms vs Meadow Creek Grain); that does not allocate the truck.

---

## EVAL-PROV-001

family: `processor_receipt_provenance`  
query: processor_receipt `HFM-IN-602`

**Receipt**
- `mill-receipt:HFM-IN-602` at Hearthland Feed Mill - North, dock `N-1`, silo `S-5`, 25500 kg HRW, `2025-09-05T10:50:00-05:00`, BOL `NS-5002-B`, origin label `PG-OUT-5002`.

**Upstream dispatch**
- Movement `PGE-OUT-5002` (`NS-8848` / `NS-5002-B`), loaded from **North House 12**.

**Inbound material identities**
- Established as named on the outbound hopper move: `WB-390` and `EF-18`.
- Not a quantity allocation between those tickets.
- Commercial custody events `TR-104` / `TR-105` scope the **movement**, not individual tickets (not a bin allocation).

**Downstream processing output**
- Established: run `MILL-2207` → batch `FEED-2207` (`grower feed`), started `2025-09-05T15:10:00-05:00`.

**Unresolved allocation / quantity**
- Ticket quantity split on the 26000 kg loadout: unresolved.
- 26000 kg loadout vs 25500 kg mill: recorded unexplained difference; same movement identity.

---

## EVAL-PROV-002

family: `processor_receipt_provenance`  
query: processor_receipt `HFM-IN-604`

**Upstream dispatch and source status**
- Dispatch `PGE-OUT-5004` from **South House 14** (Prairie Gate), manifest `RL-9127` / BOL `RL-5004-Q`, mill 18800 kg at North dock `N-3` silo `S-7` on `2025-09-07T13:02:00-05:00`.
- Physical source tickets for that truck: **unresolved** (`physical-ticket-allocation-PGE-OUT-5004`; deliveries `MCR-118` and `S-52`).

**Identified inbound load**
- **Not established.** No named hopper tickets; commercial ticket scopes empty.

**Processing output**
- **Not recorded** (`mill_process` has no row for `HFM-IN-604`).

**Other unresolved**
- 19000 vs 18800 kg on an established BOL identity.

---

## EVAL-CUST-001

family: `custody_owner_at`  
query: material `WB-390`, timestamp `2025-09-04T13:10:00-05:00`

Covering ownership event: `ownership:TR-102` (title change, broker release `GL-88`), effective `2025-09-03T15:00:00-05:00` through `2025-09-05T10:50:00-05:00`, scoped to ticket `WB-390`.

| Role | Established | Party | From event |
| --- | --- | --- | --- |
| Owner | yes | **GrainLink Merchants** | `TR-102` |
| Custodian (holder) | yes | **Prairie Gate Elevator** | `TR-102` |

Notes: `TR-104` (handoff to Northstar at `2025-09-04T13:05:00-05:00`) is scoped to movement `PGE-OUT-5002`, not to ticket `WB-390`, so it does not replace ticket-level custody at this instant. Loadout `LD-19` is at `13:15`. No related purpose-requirement failure for this material.

---

## EVAL-CUST-002

family: `custody_owner_at`  
query: material `EF-18`, timestamp `2025-09-03T12:00:00-05:00`

**Covering ownership events:** none.

| Role | Established | Party |
| --- | --- | --- |
| Owner | **no** | unresolved |
| Custodian | **no** | unresolved |

World context that is **not** treated as a covering ownership/custody event at this instant:
- Intake `ER-7729` arrived `2025-09-03T11:05:00-05:00` into North House 12 with `owner_recorded` / `grower_recorded` **East Fork Co-op**.
- Ownership export records changes; absence of an `EF-18` event is not a proof that no unrecorded agreement existed, and it is also not an established covering owner/holder.

Conclusion: recorded owner and custodian from covering ownership events are **unresolved / not established**.

---

## EVAL-INSP-001

family: `inspection_downstream_scope`  
query: sample `SMP-602B`

Lab `LAB-4419` (`2025-09-05T13:10:00-05:00`): local lot `WB390 / EF18`, material hint **receiving slip HFM-IN-602**, comment `combined truck sample`. Catalog helper did not walk downstream because two tickets match; World `lab_result.material_hint` still names the mill receipt.

**Established affected downstream**
- Processor receipt: **`HFM-IN-602`**
- Shipment: **`PGE-OUT-5002`** (mill intake of that receipt; BOL `NS-5002-B`)
- Processed output: **`FEED-2207`** via `MILL-2207` (`grower feed`)

**Attribution to individual inbound material**
- **Unresolved.** Combined truck sample names both `WB-390` and `EF-18`; neither is uniquely attributed. No `lab-sample-SMP-602B` purpose failure; the blend itself is the unresolved allocation.

---

## EVAL-INSP-002

family: `inspection_downstream_scope`  
query: sample `SMP-604Q`

Lab `LAB-4422` (`2025-09-07T14:10:00-05:00`): local lot `MC-118` (alias of `MCR-118`), material hint **South House 14 cargo**, comment `customer hold review`.

**Must not treat as a unique inbound ticket:** `lab-sample-SMP-604Q-ticket` — after `MCR-118` and `S-52` were both placed in South House 14, the cargo is not allocated to one delivery.

**Established affected downstream (bin cargo, not ticket)**
- Only loadout from South House 14 in the World: **`PGE-OUT-5004`** (`LD-21` / `RL-9127`).
- Processor receipt of that movement: **`HFM-IN-604`**.
- Sample time is after mill intake (`13:02`); hint is house cargo, not a receiving-slip id, but it is the only recorded outbound cargo from that bin.

**Processed output**
- **Not recorded** for `HFM-IN-604`.

**Unresolved source attribution**
- Individual delivery `MCR-118` vs `S-52` (`lab-sample-SMP-604Q-ticket` and `physical-ticket-allocation-PGE-OUT-5004`).
- `MC-118` is not a validated exclusive allocation to `MCR-118`.

---

## EVAL-INSP-003

family: `inspection_downstream_scope`  
query: sample `SMP-UNLISTED`

Sample **exists** (`LAB-4428`, protein 12.5%, `2025-09-08T09:00:00-05:00`), local lot `N3 / EF-18?`, material hint `route packet note`, comment `source ticket not recorded`.

**Validated downstream shipment:** not established.  
**Validated processor receipt:** not established.  
**Validated inbound source identity:** not established.

**Unresolved linkage (preserve)**
- `lab-sample-SMP-UNLISTED-source-ticket`: source ticket not recorded; route packet note is not a validated source ticket.
- Same cargo-mark string appears on `PGE-OUT-5003` (`physical-ticket-allocation-PGE-OUT-5003`); that coincidence does **not** validate the sample-to-dispatch link.
- `PGE-OUT-5003` also has `mill-receipt-absent-PGE-OUT-5003`; no mill receipt follows from this sample.

---

## Task answer index

| task_id | established core | unresolved |
| --- | --- | --- |
| EVAL-SRC-001 | contributors `WB-390`, `EF-18`; location North House 12 | quantity split; kg vs mill |
| EVAL-SRC-002 | location North House 12 | inbound ticket; mill receipt |
| EVAL-SRC-003 | no contributing tickets | `MCR-118`/`S-52` allocation |
| EVAL-PROV-001 | `PGE-OUT-5002`; `WB-390`+`EF-18` named; `FEED-2207` | qty split; 26000/25500 kg |
| EVAL-PROV-002 | `PGE-OUT-5004`; South House 14; no process output | inbound load identity |
| EVAL-CUST-001 | owner GrainLink Merchants; custodian Prairie Gate Elevator | none |
| EVAL-CUST-002 | none from covering events | owner and custodian |
| EVAL-INSP-001 | `PGE-OUT-5002`, `HFM-IN-602`, `FEED-2207` | which of `WB-390`/`EF-18` |
| EVAL-INSP-002 | `PGE-OUT-5004`, `HFM-IN-604`; no process output | which of `MCR-118`/`S-52` |
| EVAL-INSP-003 | sample recorded only | shipment, receipt, source ticket |
