I'll start by reading the instruction file and the questions, then work through them with the files in this workspace.The SQLite world is present. I’ll dump tables and rows next so each question can be answered from the recorded evidence.**NQ-01.** Established contributing inbound loads for **PGE-OUT-5002** are **WB-390 (ER-7721)** and **EF-18 (ER-7729)**. Individual kilogram allocation is not established. **DR-44** is not established as a contributor.

Evidence: `hopper_names_ticket` names WB-390 and EF-18 on BM-004 / OUT-5002 (alias of PGE-OUT-5002); `storage_move` BM-004 BIN-12 → LOAD-PIT-2 with note `WB-390 / EF-18`, 26000 kg; `loadout_from_bin` LD-19 from BIN-12; `intake_receipt` ER-7721 / ER-7729. Unresolved `out_5002_quantity_split`: hopper names both tickets but the 26000 kg blend is not allocated. DR-44 occupies BIN-12 via BM-001 but is not named on this hopper sheet.

**NQ-02.** Downstream shipments that drew from **BIN-12** (alias North House 12 / B-12): **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20). **None** have individual source allocation.

Evidence: `loadout_from_bin` for those three dispatch refs; `ticket_into_bin` DR-44, WB-390, EF-18 into BIN-12. 5001: `out_5001_ticket_composition` — BIN-12 already held all three tickets; loadout does not allocate. 5002: tickets named together, no quantity split. 5003: `out_5003_material_identity` — no hopper ticket. PGE-OUT-5004 is from BIN-14, not BIN-12.

**NQ-03.** In that window two intakes are recorded, both hard red wheat into BIN-12:

| Receipt | Ticket | Arrived | Grower | Net kg | Next established moves |
|---|---|---|---|---|---|
| ER-7721 | WB-390 | 2025-09-03T09:20:00-05:00 | Willow Bend Farms | 23850 | BM-002 09:47 into BIN-12 |
| ER-7729 | EF-18 | 2025-09-03T11:05:00-05:00 | East Fork Co-op | 17900 | BM-003 11:28 into BIN-12 |

Established later path for the **named blend**: BM-004/BM-005 and LD-19 as PGE-OUT-5002 → manifest NS-8848 → mill slip HFM-IN-602 (BOL NS-5002-B) → mill run MILL-2207 → **FEED-2207**. Title on WB-390 to GrainLink Merchants at 15:00 the same day (TR-102); custody of OUT-5002 later to Northstar then Hearthland (TR-104, TR-105). Lab **SMP-602B** is a combined-truck aflatoxin check on HFM-IN-602.

Not established: how much of each ticket is in the 26000 kg; whether leftover BIN-12 grain after 5002 (including any remaining WB-390/EF-18, and DR-44 still in the house) is in PGE-OUT-5003 (hopper: “no ticket”).

**NQ-04.** **None** of the mill receipts have complete upstream provenance to allocated inbound loads.

- **HFM-IN-601**: linked to PGE-OUT-5001 / RL-8841 / FEED-2206 (`established_shipment`), but 5001 has no ticket allocation from BIN-12.
- **HFM-IN-602**: linked to PGE-OUT-5002 / NS-8848 / FEED-2207; inbound tickets **identified** as WB-390 and EF-18, but quantity split unresolved — not complete.
- **HFM-IN-604**: linked to PGE-OUT-5004 / RL-9127 with empty `output_batch`; BIN-14 held MCR-118 and S-52 without allocation (`out_5004_ticket_composition`); completeness gap: no mill run for HFM-IN-604.

No mill slip is linked to PGE-OUT-5003.

**NQ-05.** Unresolved chains (`purpose_requirement_failure` + completeness gaps):

1. **MCR-118 / m_creek_account** — grower account: intake “M. Creek” vs claims Meadow Creek Farms and Meadow Creek Grain; no selecting key (TR-107 `owner_after` empty).
2. **PGE-OUT-5001 / out_5001_ticket_composition** — truck not allocated among DR-44, WB-390, EF-18 in BIN-12.
3. **PGE-OUT-5002 / out_5002_quantity_split** — named WB-390 and EF-18; 26000 kg not split.
4. **PGE-OUT-5003 / out_5003_material_identity** — no hopper ticket; cargo mark `N3 / EF-18?` not a validated ticket.
5. **PGE-OUT-5003 / out_5003_mill_receipt** — carrier manifest NS-8910, no mill slip in extracts.
6. **PGE-OUT-5004 / out_5004_ticket_composition** — BIN-14 MCR-118 vs S-52 not allocated.
7. **SMP-UNLISTED / smp_unlisted_source_ticket** — source ticket not recorded; route-packet note not a ticket.
8. **ownership export / unrecorded_ownership** — recorded changes only; silence is not a negative on unrecorded agreements.
9. **HFM-IN-604** — received, no mill run in `mill_process` (`established_shipment.output_batch` empty).

**NQ-06.** Two missing links, both explicit:

1. **Source identity:** BM-006 material note “no ticket on hopper sheet”; manifest cargo_mark `N3 / EF-18?` is not treated as a ticket (N3 is a route code elsewhere).
2. **Processor inbound:** `inbound_same_movement` has no row for NS-8910; consignee **HFM-E**; completeness: “PGE-OUT-5003 has a manifest and no mill slip.” Dispatch↔manifest is established only by vehicle NST-219 and 12000 kg weight (`outbound_same_movement`), not cargo_mark.

**NQ-07.** At **2025-09-04 13:10:00-05:00**:

- **Recorded owner of WB-390:** **GrainLink Merchants** (TR-102, 2025-09-03T15:00 through 2025-09-05T10:50; `holder_after` Prairie Gate Elevator).
- **Custody is not unique:** TR-104 (scope **OUT-5002**, start 13:05) lists holder **Northstar Bulk Transport**, owner GrainLink. At 13:10 the hopper-named blend is physically at **LOAD-PIT-2** (BM-004 13:02; BM-005 to TRUCK-NS204 only at 13:14; loadout LD-19 13:15). Remainder of WB-390, if any, is not allocated (quantity split unresolved) and would still be BIN-12 under Prairie Gate. Do not treat TR-102’s Prairie Gate holder and TR-104’s Northstar holder as the same scoped fact. Ownership export does not prove no other agreement existed.

**NQ-08.** SMP-602B is a combined-truck aflatoxin result (`below limit`) on **HFM-IN-602**, local lot WB-390 / EF-18. Established downstream: mill input HFM-IN-602 → **MILL-2207 / FEED-2207** (grower feed), shipment PGE-OUT-5002 / NS-8848. It does not, on this evidence, speak to leftover BIN-12 grain or PGE-OUT-5003.

**NQ-09.** Do not commit as identity:

- **M. Creek = Meadow Creek Farms = Meadow Creek Grain** (no account key).
- **`N3 / EF-18?` as a source ticket** for PGE-OUT-5003 or SMP-UNLISTED (handwritten/route-packet; N3 is a route code, not a validated ticket).
- **PGE-OUT-5003 cargo_mark = dispatch id** (explicitly not; link is vehicle+weight only).

Established aliases that **may** be used: B-12/North House 12 → BIN-12; DR44→DR-44, WB390→WB-390, EF18→EF-18, MC-118→MCR-118; PG-OUT-5001/5002/5004 → PGE-OUT-*; OUT-5002/5003/5004 → PGE-OUT-*; TRUCK-NS204→NST-204, TRUCK-RL091→RLT-091.

**NQ-10.** **No HFM-N receiving record** is linked to PGE-OUT-5003: all `mill_receipt` rows are HFM-N (HFM-IN-601/602/604) with bills RL-5001-A, NS-5002-B, RL-5004-Q, none NS-5003-C. `extract_coverage` claims the HFM receiving log is **complete for HFM-North** in 2025-09-05/2025-09-07, so absence **at HFM-N in that window** is supported.

That **does not** justify “HFM-E has no such record”: consignee is HFM-E; coverage states **no conclusion about other HFM sites**; `out_5003_mill_receipt` says North-log completeness does not speak to East. Missing East slip is an extract gap, not a proved negative for HFM-E.
