# Grain traceability held-out answers

World: `v0` revision 242, sqlite sha256 `b2053bcf7c9e02a39b64a77065ff952c4357e494b024292c08eb9a6ff9481a4c`.
Computations were run via `application/run.py` and checked against World relations. Where a computation omitted a link that World records (notably inspection sample `SMP-602B` naming mill receipt `HFM-IN-602`), the World record is used. Unsupported identity, blend allocation, and missing receiving evidence are left unresolved.

---

## EVAL-SRC-001 — PGE-OUT-5002

**Established contributing inbound identities:** `WB-390` (`ticket:wb-390`, receipt `ER-7721`) and `EF-18` (`ticket:ef-18`, receipt `ER-7729`). Both are named on hopper move `BM-004` (`material_note` `WB-390 / EF-18`, work order `OUT-5002`, 26000 kg from North House 12 to LOAD-PIT-2). Naming is identity association, not a kilogram split.

**Established source location:** Prairie Gate Elevator, North House 12 (`bin:north-house-12`). Loadout `LD-19` at 2025-09-04T13:15:00-05:00, 26000 kg, truck `nst-204`. Carrier manifest `NS-8848`, bill `NS-5002-B`.

**Individual source allocation:** Quantity split between `WB-390` and `EF-18` is **not established**. There is no `physical-ticket-allocation-PGE-OUT-5002` purpose failure; contributing identities are named, but `quantity_allocation_established` is false. Prior bin occupants also include `DR-44`; that ticket is **not** named on this move and is not treated as a contributing identity for OUT-5002.

**Other unresolved (same movement, not a different shipment):** mill weigh-in `HFM-IN-602` is 25500 kg vs 26000 kg loadout (`quantity-differences-on-established-movements`). Consignee code `HFM-N` is not itself a mill receipt.

---

## EVAL-SRC-002 — PGE-OUT-5003

**Established source location:** Prairie Gate Elevator, North House 12 (`bin:north-house-12`). Loadout `LD-20` at 2025-09-05T07:10:00-05:00, 12000 kg. Carrier manifest `NS-8910`, bill `NS-5003-C`, consignee `HFM-E`.

**Established inbound material identity:** **none**. Hopper move `BM-006` note is `no ticket on hopper sheet`. Handwritten cargo mark `N3 / EF-18?` is **not** a validated source ticket; `N3` is a route code elsewhere (`physical-ticket-allocation-PGE-OUT-5003`).

**Unresolved source linkage:**
- Physical ticket allocation for PGE-OUT-5003 (hopper unnamed; cargo mark not a scale ticket).
- No mill receiving slip in the World (`mill-receipt-absent-PGE-OUT-5003`). HFM-North log completeness does not support a conclusion about East mill receiving. `mill_intake` is absent for this movement.
- Bin occupants before loadout were `DR-44`, `WB-390`, and `EF-18`; occupancy is not an allocation to this truck.

---

## EVAL-SRC-003 — PGE-OUT-5004

**Established contributing inbound identities:** **none**. Hopper move `BM-009` note is `no individual ticket`.

**Bin occupants before loadout (not allocated):** `MCR-118` (`ER-7744`, grower recorded `M. Creek`) and `S-52` (`ER-7750`, Sunnyside Acres), both assigned to South House 14.

**Individual allocation:** **unresolved** (`physical-ticket-allocation-PGE-OUT-5004`). Loadout `LD-21` left South House 14 at 2025-09-07T10:30:00-05:00 (19000 kg) without recording which delivery supplied which part of the truck.

Source location of the truck (not asked as a contributing identity): South House 14. Mill receipt `HFM-IN-604` exists (18800 kg); kilogram difference is unexplained but the movement identity is established.

---

## EVAL-PROV-001 — HFM-IN-602

**Upstream dispatch:** `PGE-OUT-5002` / movement `movement:PGE-OUT-5002`. Loadout `LD-19` from North House 12, 26000 kg; carrier `NS-8848` / `NS-5002-B`; mill dock N-1, silo S-5, 25500 kg at 2025-09-05T10:50:00-05:00, site Hearthland Feed Mill - North.

**Inbound material identities:** `WB-390` and `EF-18` named on hopper `BM-004` for OUT-5002. Commercial scopes `TR-104` and `TR-105` attach to the **movement**, not to those tickets (`not_a_bin_allocation`).

**Downstream processing output:** mill run `MILL-2207` (`mill-run:MILL-2207`) started 2025-09-05T15:10:00-05:00; output batch `FEED-2207`, output name `grower feed`.

**Unresolved allocation detail:** kilogram split between `WB-390` and `EF-18` is not recorded (`named_not_quantity_allocation`). Unexplained 26000 vs 25500 kg difference on the same bill-of-lading movement.

---

## EVAL-PROV-002 — HFM-IN-604

**Upstream dispatch and source status:** `PGE-OUT-5004` from South House 14 (`bin:south-house-14`), loadout `LD-21`, 19000 kg, carrier `RL-9127` / `RL-5004-Q`. Mill intake at 2025-09-07T13:02:00-05:00, 18800 kg, dock N-3, silo S-7.

**Identified inbound load:** **not established**. Hopper: `no individual ticket`. Occupants `MCR-118` and `S-52` remain unallocated (`physical-ticket-allocation-PGE-OUT-5004`). No commercial ticket scopes on this movement.

**Processing output:** **not recorded**. No `mill_process` row has `input_receipt_id` `mill-receipt:HFM-IN-604`.

**Also unresolved:** 19000 vs 18800 kg difference on the established movement; grower identity of `MCR-118` is separately unresolved (`mcr-118-grower-identity`) if that ticket were used as a source, but it is not established as the inbound load.

---

## EVAL-CUST-001 — WB-390 at 2025-09-04T13:10:00-05:00

**Owner:** GrainLink Merchants (established).  
**Custodian (holder):** Prairie Gate Elevator (established).

Covering ownership event: `ownership:TR-102` (title change), effective 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00, scoped to `ticket:wb-390`. Basis: broker release GL-88.

`TR-104` (movement `PGE-OUT-5002` custody to Northstar from 13:05) is commercially scoped to the **movement**, not to ticket `WB-390`, and is not treated as ticket-level custody or bin allocation. Physical hopper `BM-004` naming `WB-390 / EF-18` logged at 13:02 does not replace the covering ticket ownership record.

No purpose-requirement failure attaches to `WB-390` at this instant.

---

## EVAL-CUST-002 — EF-18 at 2025-09-03T12:00:00-05:00

**Recorded owner from covering ownership events:** **not established**.  
**Recorded custodian from covering ownership events:** **not established**.

There is no `ownership_event` whose commercial scope or `scope_ref` is `EF-18` / `ticket:ef-18`. Covering-event query returns empty. Ownership export coverage states recorded changes only, not that an unrecorded agreement did not exist.

**Intake facts (not covering title/custody events):** elevator intake `ER-7729` at 2025-09-03T11:05:00-05:00 lists `owner_recorded` East Fork Co-op and assigned bin North House 12 at Prairie Gate. Those fields are not treated as `owner_after` / `holder_after` for this timestamp.

---

## EVAL-INSP-001 — SMP-602B

Lab result `LAB-4419` at 2025-09-05T13:10:00-05:00: combined truck sample, local lot `WB390 / EF18`, material hint `receiving slip HFM-IN-602`, aflatoxin below limit.

The parameterized computation reported no downstream because it requires a **unique** source ticket and `WB390 / EF18` resolves to two tickets. World evidence names mill receipt `HFM-IN-602` on the sample; that receipt is used here.

**Established downstream shipment:** `PGE-OUT-5002` (mill intake `HFM-IN-602.movement_id`).

**Established processor receipt:** `HFM-IN-602` (`mill-receipt:HFM-IN-602`).

**Established processed output:** `FEED-2207` from run `MILL-2207` (input receipt `HFM-IN-602`).

**Attribution to individual inbound material:** **unresolved**. Combined sample of `WB-390` and `EF-18`; both named on OUT-5002 hopper `BM-004`; no kilogram allocation between them.

---

## EVAL-INSP-002 — SMP-604Q

Lab result `LAB-4422` at 2025-09-07T14:10:00-05:00: customer hold review, local lot `MC-118`, material hint `South House 14 cargo`, moisture 14.8%.

`MC-118` is an alias of ticket `MCR-118`, but World explicitly does not treat that as allocating the cargo after both `MCR-118` and `S-52` were placed in South House 14 (`lab-sample-SMP-604Q-ticket`).

**Established downstream shipment:** `PGE-OUT-5004` — only recorded loadout from South House 14 (`LD-21`), the cargo that left that bin.

**Established processor receipt:** `HFM-IN-604` — mill intake of `PGE-OUT-5004` (received 2025-09-07T13:02:00-05:00, before this hold-review test).

**Processed output:** **not recorded** (no `mill_process` for `HFM-IN-604`).

**Unresolved source attribution:** individual inbound identity among `MCR-118` and `S-52`; local lot `MC-118` / hint `South House 14 cargo` does not select one delivery (`lab-sample-SMP-604Q-ticket`, `physical-ticket-allocation-PGE-OUT-5004`). Grower identity of `MCR-118` remains unresolved if that ticket is considered.

The computation returned empty downstream because the lab-sample ticket failure blocks unique-ticket resolution. World still supports the bin-cargo → unique outbound `PGE-OUT-5004` → `HFM-IN-604` chain without selecting a ticket.

---

## EVAL-INSP-003 — SMP-UNLISTED

Lab result `LAB-4428` at 2025-09-08T09:00:00-05:00: local lot `N3 / EF-18?`, material hint `route packet note`, comment `source ticket not recorded`.

**Validated downstream shipment:** **not established**.  
**Validated processor receipt:** **not established**.  
**Validated inbound source identity:** **not established**.

**Unresolved linkage (preserved, not treated as proof):**
- `lab-sample-SMP-UNLISTED-source-ticket`: source ticket not recorded; route packet note is not a validated source ticket.
- String overlap with cargo mark `N3 / EF-18?` on `PGE-OUT-5003` / manifest `NS-8910` does **not** validate that shipment or ticket `EF-18` (`physical-ticket-allocation-PGE-OUT-5003`).
- No mill intake for PGE-OUT-5003 (`mill-receipt-absent-PGE-OUT-5003`).

---

## Answer index

| task_id | family | established core | unresolved |
|---|---|---|---|
| EVAL-SRC-001 | shipment_source_status | contributors WB-390 and EF-18; source North House 12 | kg split between those tickets; 26000/25500 kg |
| EVAL-SRC-002 | shipment_source_status | source North House 12 | inbound ticket; mill receipt |
| EVAL-SRC-003 | shipment_source_status | no named inbound tickets | MCR-118 vs S-52 allocation |
| EVAL-PROV-001 | processor_receipt_provenance | PGE-OUT-5002; WB-390 and EF-18 named; FEED-2207 | kg split; weigh difference |
| EVAL-PROV-002 | processor_receipt_provenance | PGE-OUT-5004 from South House 14; no process output | inbound load identity |
| EVAL-CUST-001 | custody_owner_at | owner GrainLink Merchants; custodian Prairie Gate Elevator | none for this instant |
| EVAL-CUST-002 | custody_owner_at | none from covering ownership events | owner and custodian |
| EVAL-INSP-001 | inspection_downstream_scope | PGE-OUT-5002, HFM-IN-602, FEED-2207 | individual inbound ticket |
| EVAL-INSP-002 | inspection_downstream_scope | PGE-OUT-5004, HFM-IN-604; no process output | MCR-118 vs S-52 |
| EVAL-INSP-003 | inspection_downstream_scope | none | sample source ticket; N3/EF-18? note |
