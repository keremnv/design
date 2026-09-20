I'll start by reading the instruction file and the questions, then work through them with the files in this workspace.The grain world is in SQLite. I'll inspect the schema and dump the tables next.Answers use only `world/world.sqlite` and the declared purpose (trace grain when evidence establishes links; keep identity and linkage unresolved otherwise). Identifiers below are relation keys and assertion ids from that database.

---

**NQ-01.** Established contributing inbound loads for **PGE-OUT-5002** are scale tickets **WB-390** (receipt **ER-7721**) and **EF-18** (receipt **ER-7729**). Not established: how much of the 26 000 kg came from each ticket, or that any other BIN-12 ticket supplied this truck.

Evidence: `loadout_from_bin` PGE-OUT-5002 ← BIN-12 / LD-19; `storage_move` BM-004 (BIN-12 → LOAD-PIT-2, note `WB-390 / EF-18`, work_order OUT-5002); `hopper_names_ticket` BM-004 names WB-390 and EF-18; those tickets entered BIN-12 via `ticket_into_bin` BM-002 / BM-003. `purpose_requirement_failure` **out_5002_quantity_split** records that the hopper names the pair without allocating the blend. DR-44 also occupied BIN-12 (`ticket_into_bin` BM-001) but is not named on this hopper sheet.

---

**NQ-02.** Downstream shipments that loaded material from **BIN-12**: **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20) — all `loadout_from_bin` with bin BIN-12 (alias North House 12). **PGE-OUT-5004** is from BIN-14, not BIN-12.

None of those three have individual source allocation: 5001 `out_5001_ticket_composition` (BIN-12 already held DR-44, WB-390, EF-18; loadout does not allocate); 5002 names WB-390 and EF-18 but `out_5002_quantity_split` (no kg split); 5003 `out_5003_material_identity` (no hopper ticket).

---

**NQ-03.** In that window two intakes are recorded, both hard red wheat into BIN-12:

| Receipt | Ticket | Arrived | Grower | Net kg | Then |
|---|---|---|---|---|---|
| ER-7721 | WB-390 | 2025-09-03T09:20:00-05:00 | Willow Bend Farms | 23850 | BM-002 09:47 INTAKE-1 → BIN-12 |
| ER-7729 | EF-18 | 2025-09-03T11:05:00-05:00 | East Fork Co-op | 17900 | BM-003 11:28 INTAKE-1 → BIN-12 |

After that, both tickets sit in the same house as DR-44. Later BIN-12 loadouts: PGE-OUT-5001 (39 000 kg, unallocated), PGE-OUT-5002 (hopper names WB-390 / EF-18, unallocated blend), PGE-OUT-5003 (no ticket). Title of WB-390 later recorded to GrainLink Merchants (TR-102, 15:00 same day); no ownership_event is scoped to EF-18. You cannot say which kilograms of these two receipts went on which outbound truck.

---

**NQ-04.** **None** of the mill slips have complete ticket-level upstream provenance.

- **HFM-IN-601** (`inbound_same_movement` RL-8841 / bill RL-5001-A) traces to PGE-OUT-5001, but BIN-12 composition is unresolved (`out_5001_ticket_composition`).
- **HFM-IN-602** traces to PGE-OUT-5002 and is the only slip whose hopper **names** inbound tickets (WB-390, EF-18); kg split remains unresolved (`out_5002_quantity_split`).
- **HFM-IN-604** traces to PGE-OUT-5004 from BIN-14 (MCR-118 and S-52 unallocated: `out_5004_ticket_composition`). No mill run names this slip (`established_shipment` output_batch empty; completeness gap).

There is no mill receipt linked to PGE-OUT-5003.

---

**NQ-05.** Unresolved chains (`purpose_requirement_failure` plus `extract_coverage` / completeness):

1. **MCR-118 / m_creek_account** — grower string is `M. Creek`; commercial desk has Meadow Creek Farms and Meadow Creek Grain with no account key (TR-107 party_claim; owner_after empty).
2. **PGE-OUT-5001** — which BIN-12 tickets (DR-44, WB-390, EF-18) supplied the truck.
3. **PGE-OUT-5002** — named tickets known; quantity split unknown.
4. **PGE-OUT-5003 material** — no hopper ticket; cargo_mark `N3 / EF-18?` is not a validated ticket.
5. **PGE-OUT-5003 mill intake** — manifest NS-8910 exists; no `inbound_same_movement` / `mill_receipt`.
6. **PGE-OUT-5004** — BIN-14 tickets MCR-118 vs S-52 not allocated.
7. **HFM-IN-604 processing** — mill receipt established; no `mill_process` run.
8. **SMP-UNLISTED** — lab lot `N3 / EF-18?`; comment “source ticket not recorded”.
9. **Ownership generally** — export is recorded changes only (`unrecorded_ownership`; extract_coverage on ownership export).

---

**NQ-06.** Two missing links, both explicit:

- **Material identity:** BM-006 hopper “no ticket on hopper sheet”; manifest NS-8910 cargo_mark `N3 / EF-18?` is not treated as a source ticket (`out_5003_material_identity`).
- **Processor receipt:** consignee **HFM-E**; no mill slip in extracts; no `inbound_same_movement` for NS-8910 (`out_5003_mill_receipt`). Elevator-to-carrier link *is* established (`outbound_same_movement` PGE-OUT-5003 / NS-8910 on vehicle NST-219 and 12 000 kg).

---

**NQ-07.** At **2025-09-04T13:10:00-05:00**:

- **Owner of WB-390 (recorded):** **GrainLink Merchants** — TR-102 title_change, scope WB-390, 2025-09-03T15:00 through 2025-09-05T10:50.
- **Custody of all WB-390:** not uniquely established. TR-102 still lists holder **Prairie Gate Elevator** for scope WB-390. TR-104 (13:05) lists holder **Northstar Bulk Transport** for scope **OUT-5002** (alias of PGE-OUT-5002), not the whole ticket.
- **Physical position of the named 26 000 kg blend:** **LOAD-PIT-2** (BM-004 at 13:02; BM-005 to TRUCK-NS204 only at 13:14; loadout LD-19 at 13:15). How much of that pit lot is WB-390 vs EF-18, and whether any WB-390 remained in BIN-12 after unallocated PGE-OUT-5001, is unresolved. Ownership export is not a closed universe (`unrecorded_ownership`).

---

**NQ-08.** **SMP-602B** is a combined-truck aflatoxin result (`below limit`) on local_lot `WB390 / EF18` with hint **HFM-IN-602**. Downstream material established from that slip: mill run **MILL-2207** → output batch **FEED-2207** (grower feed); shipment chain PGE-OUT-5002 / NS-8848 / HFM-IN-602 (`established_shipment`). It does not allocate the result to WB-390 vs EF-18, and it does not attach to other mill receipts or to PGE-OUT-5003.

---

**NQ-09.** Do **not** treat as established identity:

- Cargo / lab strings **`N3 / EF-18?`** as ticket **EF-18** (N3 is a route code elsewhere; `out_5003_material_identity`, SMP-UNLISTED `smp_unlisted_source_ticket`).
- Intake grower **M. Creek** as **Meadow Creek Farms** or **Meadow Creek Grain** (`m_creek_account`, TR-107).
- **SMP-UNLISTED** as a ticketed lot.

Documented aliases that *are* committed: e.g. North House 12 / B-12 → BIN-12; DR44 → DR-44; WB390 → WB-390; EF18 → EF-18; MC-118 → MCR-118; OUT-5002 / PG-OUT-5002 → PGE-OUT-5002.

---

**NQ-10.** There is **no** processor receiving record for PGE-OUT-5003 at **HFM-N**. Mill receipts in the world are only HFM-IN-601/602/604, all `mill_code` HFM-N, none linked to manifest NS-8910. The HFM receiving-log extract is claimed **complete for HFM-N** in 2025-09-05/2025-09-07 (`extract_coverage`), which covers this departure date, so absence at North is a **justified negative** for that log—and the truck was consigned to **HFM-E**, not North.

That same completeness claim **does not** support “HFM-E has no such record.” Missing East slip is an **absent assertion** in the extracts (`out_5003_mill_receipt`: “North-log completeness does not speak to East”), not a proof that East never received the load.
