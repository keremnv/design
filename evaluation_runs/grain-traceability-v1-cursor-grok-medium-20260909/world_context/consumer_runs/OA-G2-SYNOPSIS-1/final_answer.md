I'll start by reading the instruction file and the questions, then work through them with the files in this workspace.The SQLite world is in `world/world.sqlite`. I'll dump the relations and query them against each question.Answers below use only `world/world.sqlite` and the declared purpose (trace grain when evidence establishes links; keep identity, ownership, and linkage unresolved otherwise). Identifiers are as recorded.

---

### NQ-01. Inbound loads for PGE-OUT-5002

**Established contributors (named, not quantity-split):** scale tickets **WB-390** (intake `ER-7721`, Willow Bend Farms, 23850 kg) and **EF-18** (`ER-7729`, East Fork Co-op, 17900 kg).

Evidence: `hopper_names_ticket` BM-004 / work order OUT-5002 names both tickets; `storage_move` BM-004 (2025-09-04T13:02, BIN-12 → LOAD-PIT-2, 26000 kg, note `WB-390 / EF-18`); `loadout_from_bin` / `loadout_event` LD-19 load PGE-OUT-5002 from BIN-12 (North House 12) at 26000 kg.

**Not established:** how the 26000 kg splits between WB-390 and EF-18 (`purpose_requirement_failure` `out_5002_quantity_split`). **DR-44** was already in BIN-12 (`ticket_into_bin` BM-001) and is **not** named on the OUT-5002 hopper sheet; any contribution from DR-44 is not asserted.

---

### NQ-02. Downstream shipments of BIN-12 material; individual source allocation

BIN-12 aliases: BIN-12, North House 12, B-12. Tickets into BIN-12: DR-44, WB-390, EF-18.

**Shipments that loaded from BIN-12:** **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20). Further mill chain is established only for 5001 → HFM-IN-601 → FEED-2206 and 5002 → HFM-IN-602 → FEED-2207. PGE-OUT-5004 is from BIN-14, not BIN-12.

**Individual source allocation:** **none** of the three have a quantity allocation back to a single inbound ticket.

- 5001: bin already held DR-44, WB-390, and EF-18; loadout does not allocate (`out_5001_ticket_composition`).
- 5002: hopper **names** WB-390 and EF-18 but does not split 26000 kg (`out_5002_quantity_split`).
- 5003: hopper note “no ticket on hopper sheet” (`out_5003_material_identity`).

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 -05:00

**Received in window:** **WB-390** (`ER-7721`, 09:20, Lane 1, assigned B-12) and **EF-18** (`ER-7729`, 11:05, Lane 1, assigned B-12).

**Then established:** both moved into BIN-12 (BM-002 09:47; BM-003 11:28). They occupied BIN-12 together with earlier DR-44.

**Later, with uncertainty:**
- PGE-OUT-5001 (09-04 09:40) pulled from the same mixed bin **without** ticket allocation — whether this window’s grain was on that truck is **not** established.
- PGE-OUT-5002 hopper **names** WB-390 and EF-18 as a blend (26000 kg); split **unresolved**. That truck is established as NS-8848 / HFM-IN-602 / mill run MILL-2207 → **FEED-2207**.
- Remaining BIN-12 inventory later fed PGE-OUT-5003 **without** a recorded source ticket.

WB-390 title to GrainLink Merchants is recorded at 09-03 15:00 (TR-102), after this intake window.

---

### NQ-04. Processor receipts with complete upstream provenance to inbound load(s)

`mill_receipt` rows: **HFM-IN-601**, **HFM-IN-602**, **HFM-IN-604** (all HFM-N).

Dispatch ↔ manifest ↔ mill slip is established for all three via `outbound_same_movement` + `inbound_same_movement` (BOL = mill `bill_reference`).

**None** have complete ticket-level provenance:

| Receipt | Upstream dispatch | Gap |
|---|---|---|
| HFM-IN-601 | PGE-OUT-5001 | Mixed BIN-12; no ticket allocation |
| HFM-IN-602 | PGE-OUT-5002 | Named WB-390 **and** EF-18; **no** kg split |
| HFM-IN-604 | PGE-OUT-5004 | Mixed BIN-14 (MCR-118, S-52); no mill run (`established_shipment` output_batch empty; completeness gap) |

HFM-IN-602 is the only receipt with **identified** inbound tickets; that is still not **complete** allocation.

---

### NQ-05. Unresolved chains and which part is unresolved

From `purpose_requirement_failure` plus `_world_completeness`:

1. **MCR-118 / M. Creek** (`m_creek_account`): grower/account identity — Meadow Creek Farms vs Meadow Creek Grain; no selecting account key.
2. **PGE-OUT-5001**: source-ticket composition from mixed BIN-12.
3. **PGE-OUT-5002**: quantity split of named WB-390 / EF-18 blend.
4. **PGE-OUT-5003 material**: no hopper ticket; cargo mark `N3 / EF-18?` is not a validated ticket (N3 is a route code elsewhere).
5. **PGE-OUT-5003 mill**: manifest NS-8910 with **no** mill slip in extracts; consignee HFM-E.
6. **PGE-OUT-5004**: which of MCR-118 vs S-52 supplied the truck.
7. **SMP-UNLISTED**: source ticket not recorded; route-packet note not treated as a ticket.
8. **Ownership export**: recorded changes only — does not prove an unrecorded agreement did not exist.
9. **HFM-IN-604 processing**: no mill run in supplied `mill_process` (completeness gap).

---

### NQ-06. Missing linkage for PGE-OUT-5003 provenance

Two recorded gaps, both required for complete provenance:

1. **Upstream identity:** BM-006 material_note `no ticket on hopper sheet`; manifest cargo_mark `N3 / EF-18?` is **not** a validated source ticket (`out_5003_material_identity`).
2. **Processor link:** `outbound_same_movement` ties PGE-OUT-5003 to manifest **NS-8910** (vehicle/weight; cargo_mark is not the dispatch id), but there is **no** `inbound_same_movement` / `mill_receipt` row (`out_5003_mill_receipt`; completeness: “PGE-OUT-5003 has a manifest and no mill slip in the extracts”).

---

### NQ-07. Ownership and custody of WB-390 at 2025-09-04 13:10:00-05:00

**Recorded owner: GrainLink Merchants.** TR-102 (`title_change`, scope WB-390) from 09-03 15:00 through 09-05 10:50: owner_after GrainLink, basis broker release GL-88. TR-104 (scope OUT-5002) also owner_after GrainLink.

**Recorded custody for the OUT-5002 movement: Northstar Bulk Transport.** TR-104 `custody_change` starts **13:05** (basis dispatch handoff NS-8848): holder_after Northstar. At 13:10 that interval is open.

**Physical move at 13:10:** after BM-004 (13:02, into LOAD-PIT-2) and before BM-005 (13:14, onto TRUCK-NS204) and LD-19 (13:15).

**Caveats (do not over-commit):** WB-390 in this movement is blended with EF-18 (kg split unresolved). TR-102 still lists holder_after Prairie Gate Elevator on the title row that has not yet ended; the later custody row is the dispatch handoff. `unrecorded_ownership`: recorded events are not a proof that no other agreement existed. EF-18 has **no** ownership_event of its own.

---

### NQ-08. Downstream material affected by SMP-602B

SMP-602B (LAB-4419, 09-05 13:10) is a **combined truck** aflatoxin sample; `material_hint` = receiving slip **HFM-IN-602**; `local_lot` = `WB390 / EF18`.

**Affected established material:** mill receipt **HFM-IN-602** (silo S-5, 25500 kg) and mill output **FEED-2207** (MILL-2207, grower feed), i.e. the PGE-OUT-5002 / NS-8848 truck. Result: aflatoxin below limit (ppb).

It does **not** by itself allocate the finding to WB-390 vs EF-18 individually.

---

### NQ-09. Apparent identity matches that should not be committed

Do **not** treat as established:

- **M. Creek** = Meadow Creek Farms **or** Meadow Creek Grain (TR-107 party_claim; `m_creek_account`).
- Cargo/lab string **`N3 / EF-18?`** as ticket EF-18, as ticket N3, or as PGE-OUT-5003 composition (`out_5003_material_identity`, `smp_unlisted_source_ticket`; N3 is a route code elsewhere).
- **SMP-UNLISTED** lot label as a receiving ticket.

Documented aliases in `identifier_alias` (e.g. BIN-12 / North House 12 / B-12, PG-OUT-5002 / PGE-OUT-5002, DR44 / DR-44) **are** committed spellings, not in this “do not commit” set.

---

### NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** There is **no** `mill_receipt` (and no `inbound_same_movement`) for PGE-OUT-5003 / NS-8910 / BOL NS-5003-C. The three North slips are HFM-IN-601/602/604. `extract_coverage` claims the HFM receiving log is **complete for HFM-N** in 2025-09-05/2025-09-07. That supports: **no North receiving record for this shipment in the supplied complete North log.** Consignee on the manifest is **HFM-E**, not HFM-N.

**HFM-E:** The same coverage claim is explicit: **“no conclusion about other HFM sites.”** `out_5003_mill_receipt`: North-log completeness **does not speak to East**. Missing East extracts are **absence of evidence**, not a justified negative that HFM-E has no receiving record.
