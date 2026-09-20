I'll start by reading the instruction file and the questions, then work through each one with the files in this workspace.The grain world is in SQLite. I'll inspect the schema and dump the relations that the questions depend on.Answers below use only `world/world.sqlite` plus purpose/admission notes. Established means a recorded relation; unresolved means an explicit gap or an unsupported identity.

---

**NQ-01. Which inbound loads contributed to outbound shipment PGE-OUT-5002?**

**Established contributors:** scale tickets **WB-390** (`ticket:wb-390`, ER-7721) and **EF-18** (`ticket:ef-18`, ER-7729).

Evidence:
- `elevator_loadout` LD-19: `movement:PGE-OUT-5002` from `bin:north-house-12` (BIN-12), 26,000 kg, 2025-09-04T13:15-05:00.
- `bin_transfer` BM-004 (`work_order` OUT-5002): BIN-12 → `pit:load-2`, 26,000 kg, material note `WB-390 / EF-18`, 13:02; BM-005 then pit → `truck:nst-204`.
- `ticket_named_on_move`: both tickets named on BM-004.

**Not established:** kilogram split between WB-390 and EF-18 (`ticket_named_on_move` is not quantity allocation). **DR-44** was already in BIN-12 but is not named on BM-004; commercial scoping of DR-44 to RL-8841 / HFM-IN-601 is not a bin allocation for 5002.

---

**NQ-02. Downstream shipments from BIN-12, and which have individual source allocation?**

Shipments loaded from `bin:north-house-12` (BIN-12 / North House 12):

| Shipment | Loadout | Individual source allocation |
|---|---|---|
| **PGE-OUT-5001** | LD-18 | **No.** Hopper does not name tickets (`physical-ticket-allocation-PGE-OUT-5001`). |
| **PGE-OUT-5002** | LD-19 | **Named blend only:** WB-390 and EF-18 on BM-004. Not a per-ticket quantity allocation. |
| **PGE-OUT-5003** | LD-20 | **No.** Hopper note `no ticket on hopper sheet`; cargo mark `N3 / EF-18?` is not a validated ticket (`physical-ticket-allocation-PGE-OUT-5003`). |

PGE-OUT-5004 is from BIN-14, not BIN-12.

---

**NQ-03. Grain received 2025-09-03 09:00–12:00 -05:00?**

Two intakes fall in that window, both hard red wheat at Prairie Gate, lane 1, assigned BIN-12:

1. **WB-390** (ER-7721), 23,850 kg, Willow Bend Farms, arrived 09:20. BM-002 at 09:47: intake-1 → BIN-12, note `WB-390`.
2. **EF-18** (ER-7729), 17,900 kg, East Fork Co-op, arrived 11:05. BM-003 at 11:28: intake-1 → BIN-12, note `EF-18`.

BIN-12 already held **DR-44**. Later: TR-102 (15:00) titles WB-390 to GrainLink Merchants with Prairie Gate still holding; 26,000 kg of the WB-390/EF-18 blend is named onto **PGE-OUT-5002**; remaining BIN-12 inventory also fed **PGE-OUT-5001** and **PGE-OUT-5003** without individual ticket allocation. EF-18 has no later ownership_event.

---

**NQ-04. Processor receipts with complete upstream provenance to identified inbound load(s)?**

**HFM-IN-602** (`mill-receipt:HFM-IN-602`) is the only mill receipt whose physical chain names inbound loads: PGE-OUT-5002 → BM-004 → **WB-390 and EF-18**. BOL identity is established (NS-5002-B); the 26,000 vs 25,500 kg difference is recorded and unexplained, not a different movement.

**Not complete:**
- **HFM-IN-601:** movement PGE-OUT-5001 is established, but physical tickets for that truck are unresolved. DR-44 scoped to RL-8841 / HFM-IN-601 is commercial, not bin allocation.
- **HFM-IN-604:** PGE-OUT-5004 from BIN-14 after MCR-118 and S-52; no individual ticket (`physical-ticket-allocation-PGE-OUT-5004`).
- No mill_intake row for PGE-OUT-5003.

---

**NQ-05. Unresolved chains and what is missing?**

From `purpose_requirement_failure` (all `EXPLICIT_UNRESOLVED`):

1. **PGE-OUT-5001 physical tickets** — BIN-12 already held DR-44, WB-390, EF-18; hopper does not name tickets for OUT-5001.
2. **PGE-OUT-5003 physical tickets** — hopper has no ticket; mark `N3 / EF-18?` is not a validated source ticket.
3. **PGE-OUT-5003 mill receipt** — carrier left (NS-8910, 12,000 kg, consignee HFM-E); no HFM receiving slip in extracts.
4. **MCR-118 grower identity** — intake name `M. Creek`; desk claims Meadow Creek Farms and Meadow Creek Grain; no account key.
5. **PGE-OUT-5004 physical tickets** — BIN-14 after MCR-118 and S-52; hopper `no individual ticket`.
6. **SMP-UNLISTED source ticket** — source ticket not recorded; route-packet note is not a ticket.
7. **SMP-604Q ticket** — labeled South House 14 / MC-118 after both deliveries were in BIN-14; not allocated to one delivery.
8. **Quantity differences** on established movements 5001 (39,000/38,700), 5002 (26,000/25,500), 5004 (19,000/18,800) — unexplained kg, same BOL identity.

---

**NQ-06. Missing linkage for complete provenance of PGE-OUT-5003?**

**Primary gap:** no validated source-ticket link. BM-006 hopper note is `no ticket on hopper sheet`. Carrier `cargo_mark` `N3 / EF-18?` is not a validated scale ticket; `route_note` states N3 is a route code (`physical-ticket-allocation-PGE-OUT-5003`, `carrier_departure` NS-8910).

**Second gap:** no `mill_intake` for `movement:PGE-OUT-5003` (`mill-receipt-absent-PGE-OUT-5003`). Consignee HFM-E is not a receiving slip (`consignee_is_not_receipt`).

---

**NQ-07. At 2025-09-04 13:10:00-05:00, owner and custody of WB-390 material?**

**Owner (ticket WB-390):** **GrainLink Merchants**. TR-102 (`ownership:TR-102`, `commercial_scope` `ticket:wb-390`), title change 2025-09-03T15:00 through 2025-09-05T10:50, `owner_after` GrainLink Merchants.

**Custody is not uniform** because WB-390 is not fully allocated to one holder at that minute:
- Ticket-scoped holder on TR-102 remains **Prairie Gate Elevator** until 2025-09-05T10:50.
- TR-104 (effective 13:05) is scoped to **movement PGE-OUT-5002**, not the WB-390 ticket: `holder_after` **Northstar Bulk Transport**, owner still GrainLink.
- Physically: BM-004 at 13:02 put 26,000 kg labeled `WB-390 / EF-18` in `pit:load-2`; BM-005 onto the truck is 13:14, so that portion is still in the load pit at 13:10. WB-390 net was 23,850 kg; the 26,000 kg move is a two-ticket blend, so leftover WB-390 in BIN-12 is not quantity-established.

Do not treat TR-104 as custody of the entire WB-390 lot.

---

**NQ-08. Downstream material affected by SMP-602B?**

Sample `sample:SMP-602B` (LAB-4419, 2025-09-05T13:10-05:00): aflatoxin below limit; `material_hint` receiving slip **HFM-IN-602**; `local_lot` `WB390 / EF18`; comment `combined truck sample`.

**Affected, as established:** mill receipt **HFM-IN-602** (PGE-OUT-5002, silo S-5) and mill output **FEED-2207** via **MILL-2207**, which consumes HFM-IN-602 (started 15:10, after the sample).

**Not established:** that remaining BIN-12 inventory or other shipments are in the sample; that WB-390 vs EF-18 can be tested separately (combined truck sample).

---

**NQ-09. Apparent identity matches that should not be committed?**

Do not treat as established:

- **`M. Creek` / MCR-118 = Meadow Creek Farms or Meadow Creek Grain** (no account key).
- **`N3 / EF-18?` = ticket EF-18**; **N3 = a cargo identity** (N3 is a route code).
- **SMP-UNLISTED lot `N3 / EF-18?` = a source ticket**.
- **SMP-604Q `MC-118` / South House 14 cargo = solely MCR-118** (BIN-14 also held S-52). Token alias MC-118 → `ticket:mcr-118` does not allocate that sample.
- **Consignee HFM-N / HFM-E = a mill receiving slip**.
- **DR-44 commercial scope to RL-8841 / HFM-IN-601 = physical BIN-12 allocation onto PGE-OUT-5001**.
- **Kilogram mismatches = different truck movements**.

Recorded `known_as` aliases such as PGE-OUT-5002 / PG-OUT-5002 / OUT-5002, BIN-12 / North House 12 / B-12, DR-44 / DR44 / ER-7714 are system tokens, not the matches above.

---

**NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N? Can we say HFM-E has none?**

**HFM-N:** There is **no** `mill_intake` row for `movement:PGE-OUT-5003`. The three receipts are HFM-IN-601/602/604 at `site:hfm-north` for 5001/5002/5004. `extract_coverage` on `HFM-North receiving_log` claims completeness for **2025-09-05 through 2025-09-07**. PGE-OUT-5003 departed 2025-09-05T07:24. Absence **at HFM-N in that log window** is therefore supported. That is not a claim about later dates or other sites.

**HFM-E:** Evidence **does not** justify “HFM-E has no such record.” Consignee is HFM-E (`manifest:NS-8910`); North-log completeness “does not support a conclusion about East mill receiving” (`mill-receipt-absent-PGE-OUT-5003`); workspace extracts are a bounded set, not a claim that every organizational record exists here. Missing slip in this world ≠ proof East never received the truck.
