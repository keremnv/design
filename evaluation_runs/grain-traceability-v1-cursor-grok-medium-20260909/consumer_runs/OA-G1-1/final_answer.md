I'll start by reading the instruction file and the questions so I can work through them with only what's in this workspace.The purpose files mention a grain-traceability world; next I’ll locate the SQLite database and inspect its schema.Answers below use only `world/world.sqlite` and the declared purpose. Absent mill rows or unnamed hopper tickets are treated as **not established**, not as proof of a negative unless coverage explicitly supports that.

---

### NQ-01. Inbound loads for PGE-OUT-5002

**Established:** inbound tickets **WB-390** (`ticket:wb-390`, ER-7721, 23,850 kg, Willow Bend Farms) and **EF-18** (`ticket:ef-18`, ER-7729, 17,900 kg, East Fork Co-op).

**Evidence:** `elevator_loadout` LD-19 loads PGE-OUT-5002 from `bin:north-house-12` (26,000 kg, 2025-09-04 13:15). `bin_transfer` BM-004 (`work_order` OUT-5002) moves 26,000 kg BIN-12 → LOAD-PIT-2 with note `WB-390 / EF-18`. `ticket_named_on_move` names both tickets on BM-004. BM-005 then loads that pit onto `truck:nst-204`. Intake rows assign both tickets to BIN-12 before loadout.

**Not established as a contributor:** **DR-44**, which was already in BIN-12 (BM-001). It is not named on BM-004. Purpose `physical-ticket-allocation-PGE-OUT-5001` states that commercial scoping of DR-44 to RL-8841 / HFM-IN-601 is not a bin allocation.

---

### NQ-02. Downstream shipments from BIN-12, and source allocation

BIN-12 (`bin:north-house-12` / North House 12) received DR-44, WB-390, and EF-18 (`elevator_intake`, BM-001–BM-003). Three loadouts leave that bin:

| Shipment | Loadout | Individual source allocation |
|---|---|---|
| **PGE-OUT-5001** | LD-18, 39,000 kg, 2025-09-04 09:40 | **No.** Hopper does not name tickets. Unresolved `physical-ticket-allocation-PGE-OUT-5001`. |
| **PGE-OUT-5002** | LD-19 | **Yes, named tickets:** WB-390 and EF-18 on BM-004. Kilograms are **not** split between those two tickets. |
| **PGE-OUT-5003** | LD-20, 12,000 kg | **No.** BM-006 note is `no ticket on hopper sheet`. Cargo mark `N3 / EF-18?` is not a validated ticket. Unresolved `physical-ticket-allocation-PGE-OUT-5003`. |

Those movements continue to mill receipts **HFM-IN-601** (5001) and **HFM-IN-602** (5002). There is **no** `mill_intake` for 5003. PGE-OUT-5004 is from BIN-14, not BIN-12.

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 -05:00

**In window:** only **WB-390** (arrived 09:20, lane 1 → BIN-12 via BM-002 at 09:47) and **EF-18** (arrived 11:05, lane 1 → BIN-12 via BM-003 at 11:28). Both hard red wheat at Prairie Gate.

**After that window (established):** both remain in BIN-12 until 2025-09-04. At 13:02, BM-004 names them on the 26,000 kg OUT-5002 draw. That truck is PGE-OUT-5002 / manifest NS-8848 / BOL NS-5002-B, received as **HFM-IN-602** (25,500 kg, silo S-5, 2025-09-05 10:50), then mill run **MILL-2207** → **FEED-2207** (grower feed). Lab **SMP-602B** is a combined truck sample on HFM-IN-602 (`WB390 / EF18`). Title on WB-390 passed to GrainLink Merchants at 15:00 the same day (TR-102); Prairie Gate remained holder on that ticket record until mill intake.

**Not established:** that either ticket supplied PGE-OUT-5001 or PGE-OUT-5003; that EF-18 has its own title record; how the 26,000 kg was split between WB-390 and EF-18.

---

### NQ-04. Processor receipts with complete upstream inbound loads

**Complete (physical named tickets):** **HFM-IN-602** only — movement PGE-OUT-5002, tickets **WB-390** and **EF-18** on BM-004. BOL identity is established (NS-5002-B). Kilogram gap 26,000 vs 25,500 is recorded and unexplained (`quantity-differences-on-established-movements`); it is not treated as a different movement.

**Not complete:**

- **HFM-IN-601** (PGE-OUT-5001): BIN-12 blend; no hopper tickets. DR-44 is commercially tied via TR-103/TR-106 (RL-8841 / processor acceptance), which the purpose says is **not** physical allocation.
- **HFM-IN-604** (PGE-OUT-5004): BIN-14 after **MCR-118** and **S-52**; hopper `no individual ticket`. Unresolved `physical-ticket-allocation-PGE-OUT-5004`.

There is no mill receipt for PGE-OUT-5003.

---

### NQ-05. Unresolved chains

From `purpose_requirement_failure` (all `EXPLICIT_UNRESOLVED`):

1. **PGE-OUT-5001 physical tickets** — BIN-12 already held DR-44, WB-390, EF-18; no hopper names; commercial DR-44 scope ≠ bin allocation.
2. **PGE-OUT-5003 physical tickets** — hopper unnamed; `N3 / EF-18?` not a validated ticket (N3 is a route code).
3. **PGE-OUT-5003 mill receipt** — 12,000 kg left on NS-8910; no HFM slip in extracts; consignee HFM-E.
4. **MCR-118 grower** — intake “M. Creek”; desk claims Meadow Creek Farms **and** Meadow Creek Grain; no account key (TR-107).
5. **PGE-OUT-5004 physical tickets** — BIN-14 after MCR-118 and S-52; no per-delivery split.
6. **SMP-UNLISTED source ticket** — lot `N3 / EF-18?`; route-packet note not a ticket.
7. **SMP-604Q ticket** — “South House 14 cargo / MC-118” after both MCR-118 and S-52 in BIN-14.
8. **Quantity differences** on established movements 5001/5002/5004 (39,000/38,700; 26,000/25,500; 19,000/18,800 kg).

`extract_coverage` also: ownership export is recorded changes only; workspace extracts are a bounded set.

---

### NQ-06. Missing linkage for PGE-OUT-5003

**Primary source gap:** no receiving ticket on the hopper. BM-006: `no ticket on hopper sheet`. Carrier cargo mark `N3 / EF-18?` is **not** a validated source ticket; N3 is used as a route code (`carrier_departure.route_note`, unresolved `physical-ticket-allocation-PGE-OUT-5003`).

**Downstream gap (separate):** no `mill_intake` row for this movement; consignee HFM-E (`mill-receipt-absent-PGE-OUT-5003`). Consignee on the manifest is not a receipt (`consignee_is_not_receipt` for NS-8910).

---

### NQ-07. WB-390 at 2025-09-04 13:10:00-05:00

**Owner (established):** **GrainLink Merchants** — TR-102 title change, effective 2025-09-03 15:00 through 2025-09-05 10:50; TR-104 `owner_after` also GrainLink.

**Custody:**

- **Movement PGE-OUT-5002** (WB-390 named on BM-004 at 13:02): TR-104 custody change at **13:05**, `holder_after` **Northstar Bulk Transport**, basis dispatch handoff NS-8848.
- **Ticket-scoped TR-102** still lists `holder_after` **Prairie Gate Elevator** until mill dock 2025-09-05 10:50. Those two records are different scopes (ticket vs movement).
- **Physical place at 13:10:** still **LOAD-PIT-2** (BM-004 13:02; BM-005 to truck NST-204 is 13:14; loadout 13:15; carrier departure 13:23).

Do not collapse ticket-holder Prairie Gate and movement-holder Northstar into one fact; both are recorded.

---

### NQ-08. Downstream of SMP-602B

**SMP-602B** (LAB-4419, 2025-09-05 13:10): aflatoxin below limit; `local_lot` `WB390 / EF18`; hint **receiving slip HFM-IN-602**; comment “combined truck sample”.

**Affected downstream of that receipt:** mill intake **HFM-IN-602** (silo **S-5**), process **MILL-2207** started 15:10, output batch **FEED-2207** (grower feed).

WB-390 and EF-18 are **upstream** sources of the sampled truck, not downstream products. No other mill runs input HFM-IN-602.

---

### NQ-09. Apparent matches that must stay uncommitted

Do **not** treat as established:

1. **`N3 / EF-18?` = ticket EF-18** (cargo mark, SMP-UNLISTED lot, route packet).
2. **`M. Creek` = Meadow Creek Farms** or **Meadow Creek Grain** (TR-107 / `mcr-118-grower-identity`).
3. **SMP-604Q `MC-118` / South House 14 cargo = only MCR-118** (S-52 also in BIN-14).
4. **HFM-E consignee on NS-8910 = a mill receiving record**.
5. **Commercial DR-44 ↔ RL-8841 / HFM-IN-601 as physical BIN-12 allocation for PGE-OUT-5001**.
6. **Kilogram mismatches as different trucks** — BOL identity is established; masses unexplained.

Known aliases that **are** committed: BIN-12 = North House 12 / B-12; PGE-OUT-5001 ↔ mill label PG-OUT-5001; etc. (`known_as`).

---

### NQ-10. Processor record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** there is **no** `mill_intake` for `movement:PGE-OUT-5003`. Existing North receipts are HFM-IN-601 (5001), HFM-IN-602 (5002), HFM-IN-604 (5004). Consignee on NS-8910 is **HFM-E**, not HFM-N. HFM-North receiving_log is claimed **complete** for 2025-09-05 through 2025-09-07, so absence **at North** in that window is supported as “no North receiving row in the complete North log,” not as a surprise consignee match.

**HFM-E:** evidence **does not** justify “HFM-E has no such record.” Purpose and `extract_coverage` say North completeness **does not** support conclusions about other HFM sites; extracts are a bounded working set. Missing East slip is **unresolved** (`mill-receipt-absent-PGE-OUT-5003`), not a proven non-receipt.
