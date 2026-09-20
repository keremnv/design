I'll start by reading the instruction file and the questions, then work through every item using only what's in this workspace.The world is in SQLite. Next I’ll inspect the schema and dump the relations that the questions depend on.Answers use only `world/world.sqlite` and the declared purpose (trace grain when evidence establishes links; keep identity/linkage unresolved otherwise). Evidence citations are relation rows and `purpose_requirement_failure` / UNRESOLVED notes.

---

### NQ-01. Inbound loads into PGE-OUT-5002

**Established contributing inbound tickets (named, not quantity-allocated):**  
**WB-390** (`intake_receipt` ER-7721, 23 850 kg, 2025-09-03T09:20-05:00) and **EF-18** (`intake_receipt` ER-7729, 17 900 kg, 2025-09-03T11:05-05:00).

Facts: `loadout_from_bin` PGE-OUT-5002 ← BIN-12 (LD-19, 26 000 kg). `hopper_names_ticket` BM-004 / OUT-5002 names **WB-390** and **EF-18**. `storage_move` BM-004 material_note `WB-390 / EF-18`. `ticket_into_bin` placed both tickets in BIN-12 (BM-002, BM-003). `outbound_same_movement` PGE-OUT-5002 ↔ NS-8848.

**Not established:** a kg split between WB-390 and EF-18 (`purpose_requirement_failure` `out_5002_quantity_split`). **Not established** that **DR-44** (also in BIN-12 via BM-001) is in this truck; the 5002 hopper names only WB-390 and EF-18.

---

### NQ-02. Downstream shipments that held BIN-12 material; individual source allocation

**Shipments loaded from BIN-12** (`loadout_from_bin`): **PGE-OUT-5001**, **PGE-OUT-5002**, **PGE-OUT-5003**.

Further established mill-side for the first two (`established_shipment`):  
- 5001 → RL-8841 → **HFM-IN-601** → **FEED-2206**  
- 5002 → NS-8848 → **HFM-IN-602** → **FEED-2207**  
5003 has a manifest (NS-8910) but **no** mill receipt.

BIN-12 occupants (`ticket_into_bin`): DR-44, WB-390, EF-18.

**Individual source allocation:** **none**.  
- 5001: bin already held all three tickets; loadout does not allocate (`out_5001_ticket_composition`).  
- 5002: both tickets named; **no** per-ticket kg (`out_5002_quantity_split`).  
- 5003: hopper BM-006 “no ticket on hopper sheet” (`out_5003_material_identity`).

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 -05:00

**Received in window:** only **WB-390** (ER-7721, 09:20) and **EF-18** (ER-7729, 11:05), both hard red wheat into assigned B-12 = BIN-12.

**Then:** BM-002 (09:47) WB-390 INTAKE-1 → BIN-12; BM-003 (11:28) EF-18 INTAKE-1 → BIN-12. Title on WB-390 later that day: TR-102 (15:00) owner GrainLink Merchants, holder Prairie Gate Elevator.

**Later BIN-12 loadouts (composition not fully allocated):**  
- 04 Sep 09:40 **PGE-OUT-5001** 39 000 kg — DR-44 + WB-390 + EF-18 already in house; no ticket split.  
- 04 Sep 13:02–13:15 **PGE-OUT-5002** 26 000 kg — hopper names WB-390 / EF-18; no kg split; mill **HFM-IN-602** / **FEED-2207**.  
- 05 Sep 07:02–07:10 **PGE-OUT-5003** 12 000 kg — no hopper ticket; cargo_mark `N3 / EF-18?` not a validated ticket; no mill slip.

No other intakes in that clock window.

---

### NQ-04. Processor receipts with complete upstream provenance to inbound load(s)

Mill slips: **HFM-IN-601**, **HFM-IN-602**, **HFM-IN-604** (all HFM-N). Dispatch links exist for 601←5001, 602←5002, 604←5004.

**None** have **complete** provenance to allocated inbound ticket(s):  
- 601: BIN-12 commingle, no ticket allocation (`out_5001_ticket_composition`).  
- 602: named WB-390 and EF-18, **unallocated** blend (`out_5002_quantity_split`).  
- 604: BIN-14 held MCR-118 and S-52; no which-part record (`out_5004_ticket_composition`). Also no `mill_process` for 604 (`_world_completeness` gap).

Closest named upstream: **HFM-IN-602** only.

---

### NQ-05. Unresolved chains and the broken part

| Chain | Unresolved part |
|---|---|
| MCR-118 / ER-7744 | Grower **M. Creek** vs Meadow Creek Farms vs Meadow Creek Grain; no account key (`m_creek_account`) |
| PGE-OUT-5001 | Ticket composition of BIN-12 load (`out_5001_ticket_composition`) |
| PGE-OUT-5002 | Quantity split WB-390 vs EF-18 (`out_5002_quantity_split`) |
| PGE-OUT-5003 identity | Hopper has no ticket; `N3 / EF-18?` is not a source ticket (`out_5003_material_identity`) |
| PGE-OUT-5003 mill | Manifest NS-8910, consignee HFM-E; **no** `inbound_same_movement` / mill slip (`out_5003_mill_receipt`) |
| PGE-OUT-5004 | Ticket composition MCR-118 vs S-52 (`out_5004_ticket_composition`) |
| HFM-IN-604 | No mill run / output batch (completeness: empty `output_batch`) |
| SMP-UNLISTED | Source ticket not recorded; route-packet note ≠ ticket (`smp_unlisted_source_ticket`) |
| Ownership generally | Export is recorded changes only (`unrecorded_ownership`) |

`established_shipment` vs `outbound_same_movement` is **INCOMPLETE** (5003; 604 has no run).

---

### NQ-06. Missing linkage for complete PGE-OUT-5003 provenance

Two recorded gaps, both required for a full chain:

1. **Upstream identity:** BM-006 / loadout LD-20 from BIN-12 with **no hopper ticket**; manifest cargo_mark `N3 / EF-18?` is **not** a validated ticket (`out_5003_material_identity`). Vehicle/weight still ties LD-20 to NS-8910 (`outbound_same_movement`).  
2. **Downstream mill:** **no** `inbound_same_movement` for NS-8910; no mill_receipt for this dispatch; consignee **HFM-E** (`out_5003_mill_receipt`).

Either gap alone blocks complete provenance.

---

### NQ-07. Owner and custody of WB-390 at 2025-09-04 13:10:00-05:00

**Owner (recorded for scope WB-390):** **GrainLink Merchants** — TR-102 title_change, 2025-09-03T15:00 through 2025-09-05T10:50, `owner_after` GrainLink Merchants.

**Custody is not a single established holder:**  
- TR-102 `holder_after` **Prairie Gate Elevator** for scope **WB-390** (still open at 13:10).  
- TR-104 custody_change for scope **OUT-5002** from **13:05**: `holder_after` **Northstar Bulk Transport**, same owner GrainLink.  
- Physical: BM-004 at **13:02** put named `WB-390 / EF-18` 26 000 kg in **LOAD-PIT-2**; BM-005 to TRUCK-NS204 is **13:14**; loadout LD-19 is **13:15**. So at 13:10 the named blend is still in the elevator pit.

**Not established:** that all WB-390 is in OUT-5002 (5001 already loaded from the same house; 5002 split unresolved). **Not established:** absence of other title/custody deals (`unrecorded_ownership`).

---

### NQ-08. Downstream material affected by SMP-602B

SMP-602B (`lab_test`): aflatoxin “below limit”, `material_hint` **HFM-IN-602**, `local_lot` `WB390 / EF18`, comment “combined truck sample”.

**Affected, as linked:** receiving slip **HFM-IN-602**; mill run MILL-2207 → **FEED-2207** (grower feed); shipment **PGE-OUT-5002** / NS-8848 / NS-5002-B. Named lot labels alias to tickets WB-390 and EF-18 (`identifier_alias`), matching the 5002 hopper names — **without** a kg split.

Does **not** by itself allocate which of WB-390 vs EF-18 drove the result, and does **not** attach to 5001/5003/5004 or other mill slips.

---

### NQ-09. Apparent identity matches not to treat as established

Do **not** commit:

- **M. Creek** = Meadow Creek Farms **or** Meadow Creek Grain (`m_creek_account`; TR-107 party_claim, empty `owner_after`).  
- **`N3 / EF-18?`** = ticket **EF-18**, or N3 as a source ticket (route-style mark; `out_5003_material_identity`).  
- **SMP-UNLISTED** lot `N3 / EF-18?` / “route packet note” = a receiving ticket (`smp_unlisted_source_ticket`).  
- Cargo_mark of NS-8910 as if it were dispatch id **PGE-OUT-5003** (link is vehicle+weight, not cargo_mark equality).  
- **Hearthland Feed Mill** (ownership holder text) as a specific mill **site** interchangeable with HFM-N vs HFM-E.

Contrast — these **are** asserted aliases: B-12 / North House 12 = BIN-12; DR44=DR-44, WB390=WB-390, EF18=EF-18, MC-118=MCR-118; PG-OUT-5001/5002/5004 = PGE-OUT-*; OUT-5002/5003/5004 = PGE-OUT-*.

---

### NQ-10. Processor receipt for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** **No** mill receiving record for this shipment. `mill_receipt` at HFM-N is only HFM-IN-601/602/604 (BOLs RL-5001-A, NS-5002-B, RL-5004-Q). No row for NS-5003-C / NS-8910. `extract_coverage` claims the HFM-N receiving log is **complete** for 2025-09-05/2025-09-07, with **no conclusion about other HFM sites**. Consignee on NS-8910 is **HFM-E**, not HFM-N. That supports a **justified negative** for **HFM-N**.

**HFM-E:** There is **no** HFM-E slip in the extracts, but that is **absence of assertion**, not a justified “none exist.” Completeness is North-only; `out_5003_mill_receipt` states North-log completeness **does not speak to East**.
