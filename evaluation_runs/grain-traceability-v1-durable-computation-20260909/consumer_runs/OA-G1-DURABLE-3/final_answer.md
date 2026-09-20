# Grain traceability held-out answers

World binding: `v0` revision 242, hash `dc2e7e45c1327fc997691b4fa4071c5fd44edb6aed2b57e2d1e4e4c70a471eb8`.
Computations were used as parameterized queries and checked against World relations. Where a computation omitted a link that World assertions already establish, the World record is used. Unsupported identity and allocation stay unresolved.

---

## EVAL-SRC-001 — shipment_source_status (`PGE-OUT-5002`)

**Established contributing inbound identities:** `WB-390` (receipt `ER-7721`) and `EF-18` (receipt `ER-7729`). Hopper move `BM-004` (`work_order` `OUT-5002`) names both tickets (`material_note` `WB-390 / EF-18`). That is identity association, not a kilogram split (`quantity_allocation_established` false).

**Established source location:** Prairie Gate Elevator, **North House 12** (`bin:north-house-12`). Loadout `LD-19` at `2025-09-04T13:15:00-05:00`, 26,000 kg, truck `nst-204`, manifest `NS-8848` / bill `NS-5002-B`. Mill intake `HFM-IN-602` is the same movement (consignee code is not a mill receipt).

**Individual source allocation:** **Unresolved as a quantity split.** The two named tickets are established as contributing; World does not allocate 26,000 kg between them. There is no `physical-ticket-allocation-PGE-OUT-5002` failure. `DR-44` had also been assigned to North House 12 earlier but is not named on this hopper move and is not treated as a contributing identity for this dispatch.

**Also unresolved (not a different movement):** loadout 26,000 kg vs mill 25,500 kg on this established bill of lading (`quantity-differences-on-established-movements`).

---

## EVAL-SRC-002 — shipment_source_status (`PGE-OUT-5003`)

**Established source location:** Prairie Gate Elevator, **North House 12**. Loadout `LD-20` at `2025-09-05T07:10:00-05:00`, 12,000 kg, truck `nst-219`, manifest `NS-8910` / bill `NS-5003-C`, consignee `HFM-E`.

**Established inbound material identity:** **None.** Hopper `BM-006` is `no ticket on hopper sheet`. Handwritten cargo mark `N3 / EF-18?` is not a validated scale ticket (`N3` is used as a route code).

**Unresolved source linkage:**
- `physical-ticket-allocation-PGE-OUT-5003` — no hopper ticket; cargo mark is not a source identity.
- `mill-receipt-absent-PGE-OUT-5003` — carrier departure is recorded; no `mill_intake` row exists. HFM-North receiving-log completeness does not support a conclusion about East mill receiving.

North House 12 occupants before loadout (`DR-44`, `WB-390`, `EF-18`) are bin history only, not established contributing identities.

---

## EVAL-SRC-003 — shipment_source_status (`PGE-OUT-5004`)

**Established contributing inbound identities:** **None.** Hopper `BM-009` is `no individual ticket`.

**Bin occupants before loadout (not established as contributing):** `MCR-118` (`ER-7744`, grower recorded `M. Creek`) and `S-52` (`ER-7750`, Sunnyside Acres), both assigned to **South House 14**.

**Individual allocation:** **Unresolved** (`physical-ticket-allocation-PGE-OUT-5004`). Loadout `LD-21` left South House 14 at `2025-09-07T10:30:00-05:00` (19,000 kg) without recording which delivery supplied which part of the truck.

Source location of the truck (South House 14) is established. Mill intake `HFM-IN-604` is the same movement. Kilogram difference 19,000 vs 18,800 remains unexplained, not a different movement.

---

## EVAL-PROV-001 — processor_receipt_provenance (`HFM-IN-602`)

**Upstream dispatch:** `PGE-OUT-5002` (`movement:PGE-OUT-5002`), loadout `LD-19` from North House 12, carrier `NS-8848` / `NS-5002-B`, received at Hearthland Feed Mill - North dock `N-1` into silo `S-5` at `2025-09-05T10:50:00-05:00` (25,500 kg HRW).

**Inbound material identities:** `WB-390` and `EF-18`, named on hopper move `BM-004`. Commercial scopes `TR-104` / `TR-105` cover the **movement**, not individual tickets, and are not bin allocation.

**Downstream processing:** **Recorded.** Run `MILL-2207` started `2025-09-05T15:10:00-05:00`, input `HFM-IN-602`, output batch **`FEED-2207`** (`grower feed`).

**Unresolved allocation / quantity:**
- Named tickets are not a quantity split between `WB-390` and `EF-18`.
- 26,000 kg loadout vs 25,500 kg mill on the same bill of lading.

---

## EVAL-PROV-002 — processor_receipt_provenance (`HFM-IN-604`)

**Upstream dispatch and source status:** Dispatch **`PGE-OUT-5004`**, loadout `LD-21` from **South House 14**, carrier `RL-9127` / `RL-5004-Q`. Source location is established; physical ticket allocation of that truck is not.

**Identified inbound load:** **Not established.** No hopper-named tickets; `MCR-118` and `S-52` remain unallocated bin occupants. Grower identity on `MCR-118` is separately unresolved (`mcr-118-grower-identity`: Meadow Creek Farms vs Meadow Creek Grain).

**Processing output:** **Not recorded.** No `mill_process` row for `HFM-IN-604`.

**Also unresolved:** 19,000 kg loadout vs 18,800 kg mill on the established movement.

---

## EVAL-CUST-001 — custody_owner_at (`WB-390` at `2025-09-04T13:10:00-05:00`)

Covering ownership event: **`TR-102`** (title change, `scope_ref` `WB-390`, commercial scope ticket `ticket:wb-390`), effective `2025-09-03T15:00:00-05:00` through `2025-09-05T10:50:00-05:00`.

| Role | Established | Party | Event |
| --- | --- | --- | --- |
| Owner | yes | **GrainLink Merchants** | `ownership:TR-102` |
| Custodian (holder) | yes | **Prairie Gate Elevator** | `ownership:TR-102` |

`TR-104` (holder Northstar Bulk Transport from `2025-09-04T13:05:00-05:00`) is scoped to **movement** `PGE-OUT-5002`, not to ticket `WB-390`, so it is not used as the ticket’s covering custodian. Hopper `BM-004` at `13:02` names `WB-390` on `OUT-5002`; that does not retarget `TR-104` onto the ticket.

No purpose-requirement failure is attached to `WB-390` at this instant.

---

## EVAL-CUST-002 — custody_owner_at (`EF-18` at `2025-09-03T12:00:00-05:00`)

**Recorded owner:** **Not established** from covering `ownership_event` rows. No event is scoped to `EF-18` / `ticket:ef-18`.

**Recorded custodian:** **Not established** from covering `ownership_event` rows.

Intake at `2025-09-03T11:05:00-05:00` records grower/owner **East Fork Co-op** and assigns **North House 12** at Prairie Gate. Ownership-export coverage is recorded changes only, not a guarantee that an unrecorded agreement did not exist. Those intake fields are not treated as covering title/custody events.

Physical location at the timestamp (in North House 12 after `BM-003`) is recorded; it is not a `holder_after` on a covering ownership event.

---

## EVAL-INSP-001 — inspection_downstream_scope (`SMP-602B`)

Lab `LAB-4419` at `2025-09-05T13:10:00-05:00`: combined truck sample, local lot `WB390 / EF18`, **material hint `receiving slip HFM-IN-602`**.

The catalog computation returned empty downstream because it requires a single source ticket; World still links the sample to the mill slip.

**Established downstream shipment:** **`PGE-OUT-5002`** (`NS-8848` / `NS-5002-B`), via mill intake of `HFM-IN-602`.

**Established processor receipt:** **`HFM-IN-602`**.

**Established processed output:** **`FEED-2207`** from run `MILL-2207` (`grower feed`).

**Attribution to individual inbound material:** **Unresolved.** Local lot names both `WB-390` and `EF-18`, matching the hopper note on `OUT-5002`. That is a combined-truck association, not an allocation to one receiving ticket.

---

## EVAL-INSP-002 — inspection_downstream_scope (`SMP-604Q`)

Lab `LAB-4422` at `2025-09-07T14:10:00-05:00`: moisture 14.8%, local lot `MC-118`, material hint **South House 14 cargo**, comment customer hold review.

**Established downstream shipment:** **`PGE-OUT-5004`** — only recorded loadout from South House 14 after `MCR-118` and `S-52` were placed there (`LD-21` / `RL-9127`).

**Established processor receipt:** **`HFM-IN-604`** (same movement; mill received `2025-09-07T13:02:00-05:00`, before this lab time).

**Processed output:** **Not recorded.**

**Unresolved source attribution:** `lab-sample-SMP-604Q-ticket` and `physical-ticket-allocation-PGE-OUT-5004`. Label `MC-118` / `MCR-118` is not a validated single-delivery allocation after both `MCR-118` and `S-52` were in BIN-14. Hopper note is `no individual ticket`.

---

## EVAL-INSP-003 — inspection_downstream_scope (`SMP-UNLISTED`)

Sample **exists** (`LAB-4428`, protein 12.5% at `2025-09-08T09:00:00-05:00`). Comment: source ticket not recorded. Local lot `N3 / EF-18?`; material hint `route packet note`.

**Validated downstream shipment:** **Not established.**

**Validated processor receipt:** **Not established.**

**Validated inbound source identity:** **Not established.**

**Unresolved linkage to preserve:**
- `lab-sample-SMP-UNLISTED-source-ticket` — route packet note is not a validated source ticket.
- The same string `N3 / EF-18?` appears as cargo mark on `PGE-OUT-5003`; that coincidence is **not** a validated shipment or ticket link (`physical-ticket-allocation-PGE-OUT-5003`; `N3` is a route code). `PGE-OUT-5003` also has no mill receiving slip.

Do not treat `EF-18` as the source of this sample.
