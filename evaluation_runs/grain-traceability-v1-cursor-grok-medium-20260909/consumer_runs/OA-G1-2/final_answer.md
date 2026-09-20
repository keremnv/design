I'll start by reading the instruction file and the questions, then work through each one with the workspace files.The workspace has a SQLite world database. I’ll inspect its schema and query the grain-flow tables next.Checking lab rows and whether any mill intake is tied to OUT-5003.Answers below use only the workspace world (`world/world.sqlite` and purpose/admission notes). Established links are stated separately from absent or unresolved ones.

---

**NQ-01. Which inbound loads contributed to outbound shipment PGE-OUT-5002?**

**Established:** inbound scale tickets **WB-390** (`ticket:wb-390`, ER-7721) and **EF-18** (`ticket:ef-18`, ER-7729).

**Evidence:** `elevator_loadout` LD-19 loads **PGE-OUT-5002** from `bin:north-house-12` (BIN-12) onto NST-204 (26,000 kg). Hopper move **BM-004** (`work_order` OUT-5002) pulls 26,000 kg BIN-12 → LOAD-PIT-2 with `material_note` `WB-390 / EF-18`. `ticket_named_on_move` names those two tickets on BM-004. BM-005 then loads the pit onto NST-204. Both tickets were previously received into BIN-12 (WB-390 2025-09-03 09:20; EF-18 11:05) via BM-002 / BM-003.

**Not established:** kilogram split between WB-390 and EF-18 (`ticket_named_on_move` is naming, not quantity allocation). **DR-44** also occupied BIN-12 before this loadout but is **not** named on the OUT-5002 hopper sheet, so a DR-44 contribution is not established. Commercial ownership of OUT-5002 (TR-104/TR-105) is movement-scoped, not a ticket allocation.

---

**NQ-02. Which downstream shipments contain material that occupied BIN-12, and which of those have individual source allocation?**

**Shipments loaded from BIN-12** (`elevator_loadout.bin_id` = `bin:north-house-12`): **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20). Grain that occupied BIN-12 is therefore in those three outbound movements. Corresponding mill receipts exist only for 5001 and 5002 (**HFM-IN-601**, **HFM-IN-602**).

**Individual source allocation:** **none** of the three has a single-ticket quantity allocation.

- **5001:** UNRESOLVED `physical-ticket-allocation-PGE-OUT-5001` — BIN-12 already held DR-44, WB-390, and EF-18 before LD-18; no hopper ticket names; ownership of DR-44 on RL-8841 / HFM-IN-601 is commercial, not bin allocation.
- **5002:** hopper **names** WB-390 and EF-18 **jointly** on BM-004; that is not an individual/quantity allocation.
- **5003:** hopper BM-006 `material_note` is `no ticket on hopper sheet`.

---

**NQ-03. What happened to grain received 2025-09-03 09:00:00-05:00 through 2025-09-03 12:00:00-05:00?**

**Received in window** (`elevator_intake`):

| Ticket | Time | kg | Lane | Assigned bin |
|---|---|---|---|---|
| WB-390 | 09:20 | 23,850 | Lane 1 | BIN-12 |
| EF-18 | 11:05 | 17,900 | Lane 1 | BIN-12 |

**Established next steps:** BM-002 (09:47) and BM-003 (11:28) put both lots into BIN-12, co-mingled with DR-44 already there (BM-001, 2025-09-02). Combined WB-390+EF-18 = 41,750 kg.

**Later BIN-12 loadouts:** PGE-OUT-5001 (39,000 kg, 09:40 on 09-04, **before** the named 5002 pull), PGE-OUT-5002 (26,000 kg hopper-named WB-390/EF-18), PGE-OUT-5003 (12,000 kg, no ticket). 5002 was received at HFM-N as **HFM-IN-602** and processed as **MILL-2207 → FEED-2207**.

**Not established:** how WB-390 / EF-18 mass was split among 5001, 5002, and 5003. Only 5002’s hopper names those tickets; 26,000 kg cannot be their entire 41,750 kg.

---

**NQ-04. Which processor receipts have complete upstream provenance back to identified inbound load(s)?**

**Only HFM-IN-602** has inbound loads identified: mill slip ↔ PGE-OUT-5002 (BOL NS-5002-B) ↔ LD-19 / BM-004 hopper names **WB-390** and **EF-18**. Movement identity is established; the kg difference 26,000 loadout vs 25,500 mill is recorded and unexplained, not a different movement.

**Not complete:**

- **HFM-IN-601** ↔ PGE-OUT-5001 from BIN-12 with **no** hopper tickets. TR-101/103/106 commercially scope **DR-44** to that truck/receipt; purpose states that is **not** a bin allocation.
- **HFM-IN-604** ↔ PGE-OUT-5004 from BIN-14 after **MCR-118** and **S-52**; hopper “no individual ticket.”
- **No mill receipt** for PGE-OUT-5003, so no processor-receipt chain at all.

---

**NQ-05. Which traceability chains remain unresolved, and what part of each is unresolved?**

From `purpose_requirement_failure` / purpose UNRESOLVED:

1. **PGE-OUT-5001 physical tickets** — blended BIN-12; no hopper ticket names.
2. **PGE-OUT-5003 physical tickets** — no hopper ticket; cargo mark `N3 / EF-18?` not a validated ticket (N3 is a route code).
3. **PGE-OUT-5003 mill receipt** — 12,000 kg left on NS-8910; no HFM receiving slip in extracts; consignee HFM-E.
4. **MCR-118 grower identity** — intake “M. Creek”; commercial claims Meadow Creek Farms and Meadow Creek Grain; no selecting account key (TR-107).
5. **PGE-OUT-5004 physical tickets** — BIN-14 held MCR-118 and S-52; loadout did not record which supplied the truck.
6. **SMP-UNLISTED source ticket** — source not recorded; route-packet note is not a ticket.
7. **SMP-604Q ticket** — labeled South House 14 / MC-118; after both deliveries in BIN-14, cargo is not allocated to one delivery.
8. **Quantity differences** on established movements 5001/5002/5004 (39,000/38,700; 26,000/25,500; 19,000/18,800 kg).

---

**NQ-06. What specific missing linkage prevents complete provenance for PGE-OUT-5003?**

**Origin:** BM-006 hopper has **no ticket**. Carrier `cargo_mark` `N3 / EF-18?` is **not** a validated source ticket (`carrier_departure.route_note`; UNRESOLVED `physical-ticket-allocation-PGE-OUT-5003`). N3 is used as a route code (loadout route EAST-1), not as a ticket id.

**Downstream (separate gap):** no `mill_intake` row for `movement:PGE-OUT-5003` (UNRESOLVED `mill-receipt-absent-PGE-OUT-5003`). Consignee HFM-E is a destination code (`consignee_is_not_receipt`), not a receiving slip.

---

**NQ-07. At 2025-09-04 13:10:00-05:00, who owned and who had custody of the WB-390 material?**

**Ticket-scoped (TR-102, `commercial_scope` = `ticket:wb-390`):** owner **GrainLink Merchants**, holder **Prairie Gate Elevator**. Effective 2025-09-03 15:00 through 2025-09-05 10:50 (broker release GL-88). That interval covers 13:10.

**Physical location at 13:10:** after BM-004 (13:02) BIN-12 → LOAD-PIT-2, before BM-005 (13:14) onto NST-204 / LD-19 (13:15). Still on elevator grounds.

**Do not collapse scopes:** TR-104 (13:05) is a **movement**-scoped custody change for **OUT-5002** (not WB-390): owner GrainLink, holder **Northstar Bulk Transport**. It is not a ticket-scoped WB-390 custody record. Ownership export completeness does not prove unrecorded agreements are absent.

---

**NQ-08. Which downstream material is affected by inspection result SMP-602B?**

SMP-602B (LAB-4419, 2025-09-05 13:10) is a **combined truck sample** of receiving slip **HFM-IN-602**, local_lot `WB390 / EF18`, aflatoxin below limit.

**Affected established downstream:** mill receipt **HFM-IN-602** (silo S-5), then **MILL-2207** consuming that slip into output batch **FEED-2207** (grower feed, started 15:10). Upstream naming matches the OUT-5002 hopper (WB-390 / EF-18); that does not allocate kg between those tickets.

---

**NQ-09. Which apparent identity matches should not be committed as established?**

- **`N3 / EF-18?`** (carrier cargo mark, SMP-UNLISTED local_lot) as scale ticket **EF-18**. N3 is a route code; mark is unvalidated.
- **Intake “M. Creek”** as **Meadow Creek Farms** or **Meadow Creek Grain** (TR-107 / `mcr-118-grower-identity`).
- **SMP-604Q** local_lot **MC-118** as exclusively **MCR-118** after MCR-118 and S-52 both sat in BIN-14.
- **Consignee HFM-N / HFM-E** as a mill receiving slip (`consignee_is_not_receipt`).
- **Commercial DR-44 ↔ RL-8841 / HFM-IN-601** as physical BIN-12 ticket allocation for PGE-OUT-5001.

Recorded aliases in `known_as` (e.g. PGE-OUT-5002 / PG-OUT-5002 / OUT-5002, BIN-12 / B-12 / North House 12) are asserted identifiers, not these unresolved matches.

---

**NQ-10. Is there a processor receiving record for PGE-OUT-5003 at HFM-N, and can the evidence justify saying HFM-E has no such record?**

**HFM-N:** **No.** `mill_intake` has no row for `movement:PGE-OUT-5003`. The HFM-North receiving log is claimed **complete** for 2025-09-05 through 2025-09-07 (`extract_coverage`). 5003 departed 2025-09-05 07:24, so absence at HFM-N in that window is a **justified negative**, not a missing extract. (The truck was consigned to HFM-E anyway.)

**HFM-E:** **Cannot** justify “no such record.” There is no East-mill completeness claim. Purpose: HFM-North log completeness **does not** support a conclusion about East mill receiving. No `mill_intake` at `site:hfm-east` is **absence in this workspace**, not a proof that HFM-E never received the truck.
