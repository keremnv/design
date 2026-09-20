I'll read the instruction file and the questions, then work through each item with the local workspace files.The world lives in SQLite. I'll inspect the schema and dump the relations needed for the traceability questions.Answers below use only `world/world.sqlite` and the declared purpose. Identifiers are as recorded.

---

### NQ-01. Inbound loads contributing to PGE-OUT-5002

**Established contributors (named, not quantity-split):** scale tickets **WB-390** (intake `ER-7721`) and **EF-18** (`ER-7729`).

Evidence:
- `loadout_from_bin`: PGE-OUT-5002 / BIN-12 / LD-19
- `hopper_names_ticket`: BM-004 / OUT-5002 names both WB-390 and EF-18
- `storage_move` BM-004: BIN-12 → LOAD-PIT-2, note `WB-390 / EF-18`, 26000 kg
- `ticket_into_bin`: those tickets entered BIN-12 on BM-002 and BM-003

**Not established:** how the 26000 kg splits between tickets (`purpose_requirement_failure` `out_5002_quantity_split`). DR-44 also occupied BIN-12 but is **not** named on this hopper sheet; it is not an established contributor to this dispatch.

---

### NQ-02. Downstream shipments that held BIN-12 material, and source allocation

**Shipments from BIN-12** (`loadout_from_bin`):
| Dispatch | Allocation |
|---|---|
| **PGE-OUT-5001** (LD-18) | **No** individual source allocation (`out_5001_ticket_composition`: BIN-12 already held DR-44, WB-390, EF-18) |
| **PGE-OUT-5002** (LD-19) | Tickets **named** (WB-390, EF-18) but **no** kg split (`out_5002_quantity_split`) |
| **PGE-OUT-5003** (LD-20) | **No** ticket on hopper (`out_5003_material_identity`) |

Further established destinations: PGE-OUT-5001 → HFM-IN-601 → **FEED-2206**; PGE-OUT-5002 → HFM-IN-602 → **FEED-2207** (`established_shipment`). PGE-OUT-5003 has no mill slip. PGE-OUT-5004 is from BIN-14, not BIN-12.

**None** of the BIN-12 dispatches have individual source allocation.

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 −05:00

Two intakes fall in the window:

1. **ER-7721 / WB-390** — 09:20, 23850 kg, Willow Bend Farms → assigned B-12; **BM-002** 09:47 INTAKE-1 → BIN-12.
2. **ER-7729 / EF-18** — 11:05, 17900 kg, East Fork Co-op → assigned B-12; **BM-003** 11:28 INTAKE-1 → BIN-12.

Later established movement of **named** (unallocated) blend: BM-004/BM-005 → PGE-OUT-5002 / manifest **NS-8848** / mill **HFM-IN-602** / run **MILL-2207** → **FEED-2207**. Title on WB-390 moved to GrainLink Merchants at 15:00 the same day (TR-102); holder remained Prairie Gate until later custody events.

**Not established:** kg of each ticket on the 26000 kg truck; whether residual BIN-12 grain (possibly including remainder of these tickets and/or DR-44) later left on PGE-OUT-5003.

---

### NQ-04. Processor receipts with complete upstream provenance to inbound load(s)

**None.**

| Mill receipt | Dispatch link | Upstream gap |
|---|---|---|
| HFM-IN-601 | PGE-OUT-5001 / RL-8841 | BIN-12 ticket mix unresolved |
| HFM-IN-602 | PGE-OUT-5002 / NS-8848 | WB-390 vs EF-18 split unresolved |
| HFM-IN-604 | PGE-OUT-5004 / RL-9127 | MCR-118 vs S-52 unresolved; also **no mill run** (`_world_completeness`) |

Dispatch↔manifest↔North mill slip **is** established for those three. Ticket-level provenance is not. There is no mill receipt for PGE-OUT-5003.

---

### NQ-05. Unresolved chains

From `purpose_requirement_failure` and completeness:

| ID | Subject | Unresolved part |
|---|---|---|
| `m_creek_account` | MCR-118 | Grower/account: intake “M. Creek” vs Meadow Creek Farms vs Meadow Creek Grain; no selecting key |
| `out_5001_ticket_composition` | PGE-OUT-5001 | Which BIN-12 tickets (DR-44, WB-390, EF-18) supplied the truck |
| `out_5002_quantity_split` | PGE-OUT-5002 | How 26000 kg splits between named WB-390 and EF-18 |
| `out_5003_material_identity` | PGE-OUT-5003 | Source ticket; cargo mark `N3 / EF-18?` is not a validated ticket |
| `out_5003_mill_receipt` | PGE-OUT-5003 | No mill receiving slip; consignee HFM-E |
| `out_5004_ticket_composition` | PGE-OUT-5004 | Which of MCR-118 / S-52 supplied BIN-14 loadout |
| `smp_unlisted_source_ticket` | SMP-UNLISTED | Source ticket not recorded |
| `unrecorded_ownership` | ownership export | Recorded changes only; does not prove no unrecorded agreement |
| completeness | HFM-IN-604 | No mill run in `mill_process` (empty `output_batch` on `established_shipment`) |

---

### NQ-06. Missing linkage for PGE-OUT-5003 provenance

Two recorded gaps, both required for complete provenance:

1. **Source identity** (`out_5003_material_identity` / `manifest_event`): BM-006 note “no ticket on hopper sheet”; cargo mark `N3 / EF-18?` is not treated as a ticket (N3 is a route code elsewhere).
2. **Processor inbound** (`out_5003_mill_receipt` / `inbound_same_movement`): outbound link exists (NST-219, 12000 kg, manifest **NS-8910**), but **no mill slip** in extracts. Consignee is **HFM-E**.

Movement identity of the truck (loadout↔manifest) **is** established via vehicle and weight, not cargo mark.

---

### NQ-07. Ownership and custody of WB-390 at 2025-09-04 13:10:00−05:00

**Owner (recorded for ticket WB-390):** **GrainLink Merchants** — TR-102 title change, effective 2025-09-03 15:00 through 2025-09-05 10:50; `owner_after` GrainLink, `holder_after` Prairie Gate Elevator.

**Custody:** not a single established holder for “all WB-390”:
- On **TR-102** (scope WB-390), holder is still **Prairie Gate Elevator** at 13:10.
- On **TR-104** (scope **OUT-5002**, not the ticket), from 13:05 holder is **Northstar Bulk Transport**, owner GrainLink.
- Bin log: at 13:10 the 26000 kg blend is in **LOAD-PIT-2** (BM-004 13:02; BM-005 onto TRUCK-NS204 only at 13:14).

Because the OUT-5002 blend is unallocated, it is **not** established that all WB-390 had moved into the Northstar/OUT-5002 custody scope. Unrecorded ownership agreements are also not ruled out (`unrecorded_ownership`).

---

### NQ-08. Downstream material affected by SMP-602B

SMP-602B (`lab_test`): aflatoxin “below limit”; `local_lot` `WB390 / EF18`; hint **receiving slip HFM-IN-602**; comment “combined truck sample”.

**Affected downstream:** mill receipt **HFM-IN-602** (silo S-5) and mill output **FEED-2207** (MILL-2207, input HFM-IN-602). That receipt is the PGE-OUT-5002 / NS-8848 truck.

WB-390 and EF-18 are **upstream** named lots of the sample, not downstream products.

---

### NQ-09. Apparent identity matches that must not be treated as established

Do **not** commit these:

1. **M. Creek** = Meadow Creek Farms **or** Meadow Creek Grain (`m_creek_account`).
2. Cargo / lab string **`N3 / EF-18?`** = ticket **EF-18**, route **N3/EAST-1**, or dispatch **PGE-OUT-5003** (`out_5003_material_identity`; outbound 5003 was linked by vehicle+weight **because** cargo_mark is not the dispatch id).
3. **SMP-UNLISTED** lot `N3 / EF-18?` = a source scale ticket (`smp_unlisted_source_ticket`).

**Are** established as aliases (`identifier_alias`): B-12/North House 12 → BIN-12; PG-OUT-500x / OUT-500x → PGE-OUT-500x; DR44→DR-44; WB390→WB-390; EF18→EF-18; MC-118→MCR-118; TRUCK-NS204→NST-204.

---

### NQ-10. Processor receipt for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** **No** receiving record. `mill_receipt` has HFM-IN-601/602/604 only (origin labels PG-OUT-5001/5002/5004). Extract coverage: HFM receiving log is **complete for HFM-North** in 2025-09-05/2025-09-07 and **does not conclude about other HFM sites**. That supports **absence at HFM-N**, not a global absence.

**HFM-E:** Evidence **does not** justify “HFM-E has no such record.” Consignee on NS-8910 is HFM-E; North-log completeness **does not speak to East** (`out_5003_mill_receipt`). No East slips are in the supplied mill log; that is missing coverage, not a negative proof.
