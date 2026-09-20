I'll start by reading the instruction file and the questions, then work through each one using only what's in this workspace.Checking a few identifier aliases so BIN-12 and site codes line up with the questions.# Downstream grain traceability answers

Evidence is from `world/world.sqlite` plus purpose unresolved notes. Links are treated as established only when a relation records them.

---

### NQ-01. Inbound loads that contributed to PGE-OUT-5002

**Established:** tickets **WB-390** (`ticket:wb-390`, ER-7721) and **EF-18** (`ticket:ef-18`, ER-7729).

- Loadout `LD-19` drew **26,000 kg** from North House 12 (`bin:north-house-12` / BIN-12) onto `truck:nst-204` for `movement:PGE-OUT-5002` at 2025-09-04 13:15-05:00.
- Bin move **BM-004** (13:02) is the hopper pull for work order OUT-5002: BIN-12 → LOAD-PIT-2, material note `WB-390 / EF-18`, 26,000 kg.
- `ticket_named_on_move` names both tickets on BM-004. BM-005 then moved that quantity pit → truck.

**Not established:** **DR-44** as a contributor. It was already in BIN-12 (BM-001 / ER-7714) but is not named on BM-004 or on the loadout. No kilogram split between WB-390 and EF-18. A 500 kg mill vs loadout difference on this movement is recorded and unexplained; it is not treated as a different movement.

---

### NQ-02. Downstream shipments from BIN-12, and source allocation

BIN-12 = `bin:north-house-12`. Three elevator shipments were loaded from that bin:

| Shipment | Loadout | Individual source allocation? |
|---|---|---|
| **PGE-OUT-5001** | LD-18, 39,000 kg, 2025-09-04 09:40 | **No.** Hopper does not name tickets. Purpose: `physical-ticket-allocation-PGE-OUT-5001`. Commercial scoping of DR-44 to RL-8841 / HFM-IN-601 is not a bin allocation. |
| **PGE-OUT-5002** | LD-19, 26,000 kg, 2025-09-04 13:15 | **Yes.** BM-004 / `ticket_named_on_move` names WB-390 and EF-18. No kg split between those two tickets. |
| **PGE-OUT-5003** | LD-20, 12,000 kg, 2025-09-05 07:10 | **No.** BM-006: `no ticket on hopper sheet`. Cargo mark `N3 / EF-18?` is not a validated ticket (`physical-ticket-allocation-PGE-OUT-5003`). |

Further mill receipts exist for 5001 (HFM-IN-601) and 5002 (HFM-IN-602), not for 5003. Those mill records inherit the same allocation status as the elevator shipments.

---

### NQ-03. Grain received 2025-09-03 09:00 through 12:00-05:00

**Received in window (two intakes only):**

1. **WB-390 / ER-7721** — 23,850 kg hard red wheat, Willow Bend Farms, Lane 1, arrived 09:20; BM-002 into BIN-12 at 09:47.
2. **EF-18 / ER-7729** — 17,900 kg hard red wheat, East Fork Co-op, Lane 1, arrived 11:05; BM-003 into BIN-12 at 11:28.

They joined **DR-44** already in BIN-12 (39,900 kg from 2025-09-02).

**What is established afterward:**

- 2025-09-03 15:00: title on WB-390 to **GrainLink Merchants**; custody remains Prairie Gate (`ownership:TR-102`).
- 2025-09-04 13:02–13:15: **26,000 kg** named WB-390 / EF-18 left as **PGE-OUT-5002** (NS-8848 / NST-204), mill receipt **HFM-IN-602** (25,500 kg, silo S-5), then mill run **MILL-2207** → **FEED-2207**.
- Same bin also supplied **PGE-OUT-5001** (39,000 kg, 09:40 on 09-04) and **PGE-OUT-5003** (12,000 kg, 09-05) **without** ticket names, so it is **not** established that remaining window grain went on those trucks, or how much of each ticket remained in BIN-12.

---

### NQ-04. Processor receipts with complete upstream provenance to inbound load(s)

Three mill receipts: **HFM-IN-601**, **HFM-IN-602**, **HFM-IN-604**.

**Complete to identified inbound load(s):** **HFM-IN-602** only.  
Chain: HFM-IN-602 → `movement:PGE-OUT-5002` (BOL NS-5002-B) → LD-19 / BM-004 → tickets **WB-390** and **EF-18**. Identity of the truck movement is established. The 26,000 vs 25,500 kg difference is unresolved quantity, not a break of that identity.

**Not complete:**

- **HFM-IN-601** (PGE-OUT-5001): mill and carrier identity are established; physical sources in BIN-12 are not allocated. DR-44 commercial scope to RL-8841 / HFM-IN-601 is not a receiving-ticket allocation.
- **HFM-IN-604** (PGE-OUT-5004): traces to BIN-14 after **MCR-118** and **S-52** were both placed there; hopper: `no individual ticket` (`physical-ticket-allocation-PGE-OUT-5004`).

No mill receipt exists for PGE-OUT-5003.

---

### NQ-05. Unresolved chains and the unresolved part of each

From `purpose_requirement_failure` (all `EXPLICIT_UNRESOLVED`):

1. **PGE-OUT-5001** — physical ticket allocation from BIN-12 blend (DR-44, WB-390, EF-18); hopper unnamed; ownership ≠ bin allocation.
2. **PGE-OUT-5003 physical source** — hopper has no ticket; `N3 / EF-18?` is not a validated source ticket (N3 is a route code).
3. **PGE-OUT-5003 mill intake** — 12,000 kg left on NS-8910 to HFM-E; no receiving slip in extracts (`mill-receipt-absent-PGE-OUT-5003`).
4. **MCR-118 grower identity** — intake name `M. Creek`; commercial claims from both Meadow Creek Farms and Meadow Creek Grain; no account key (`ownership:TR-107`).
5. **PGE-OUT-5004** — BIN-14 blend of MCR-118 and S-52; no individual ticket on hopper.
6. **SMP-UNLISTED** — source ticket not recorded; route-packet `N3 / EF-18?` is not a validated ticket.
7. **SMP-604Q** — labeled South House 14 cargo / MC-118; after two deliveries in BIN-14, cargo is not allocated to one delivery.
8. **Quantity differences** on established movements: 5001 39000/38700, 5002 26000/25500, 5004 19000/18800 kg — unexplained, not new movements.

---

### NQ-06. Missing linkage for complete provenance of PGE-OUT-5003

**Primary gap:** no validated ticket-to-load link. BM-006 records `no ticket on hopper sheet`. Carrier cargo mark `N3 / EF-18?` on NS-8910 is not accepted as ticket EF-18 (`physical-ticket-allocation-PGE-OUT-5003`, `carrier_departure.route_note`).

**Second gap on the same chain:** no mill receiving row for this movement (`mill-receipt-absent-PGE-OUT-5003`). Consignee HFM-E is not a receipt (`consignee_is_not_receipt` on `manifest:NS-8910`).

---

### NQ-07. Owner and custody of WB-390 material at 2025-09-04 13:10:00-05:00

**Owner:** **GrainLink Merchants**. Ticket-scoped `ownership:TR-102` (title change WB-390, start 2025-09-03 15:00, end 2025-09-05 10:50) has `owner_after` GrainLink. Movement-scoped `ownership:TR-104` (OUT-5002, start 13:05) also has `owner_after` GrainLink.

**Custody is split; do not treat as one holder:**

- Ticket-scoped TR-102 still has `holder_after` **Prairie Gate Elevator** through 2025-09-05 10:50.
- Movement-scoped TR-104 (OUT-5002 only, from 13:05) has `holder_after` **Northstar Bulk Transport**.
- Physically at 13:10: BM-004 (13:02) has put 26,000 kg labeled WB-390/EF-18 into **LOAD-PIT-2** on the Prairie Gate site; BM-005 onto NST-204 is **13:14**. Remainder of WB-390 in BIN-12 vs this pull is not allocated.

So: owner GrainLink; ticket custody still Prairie Gate; the OUT-5002 slice is already commercially held by Northstar while still in the load pit.

---

### NQ-08. Downstream material affected by SMP-602B

SMP-602B (`sample:SMP-602B`, LAB-4419, 2025-09-05 13:10): aflatoxin below limit; local lot `WB390 / EF18`; hint **receiving slip HFM-IN-602**; comment `combined truck sample`.

**Affected (established):** mill receipt **HFM-IN-602** (PGE-OUT-5002, silo **S-5**, 25,500 kg), mill run **MILL-2207** (started 15:10, input HFM-IN-602), output batch **FEED-2207** (grower feed).

**Named on the combined truck, not a per-ticket lab split:** WB-390 and EF-18.

**Not established as affected:** DR-44, PGE-OUT-5001 / HFM-IN-601 / FEED-2206, PGE-OUT-5003/5004, BIN-14 cargo.

---

### NQ-09. Apparent identity matches that should not be committed

- **`N3 / EF-18?` ≠ ticket EF-18** (cargo mark and SMP-UNLISTED local lot; N3 is a route code).
- **`M. Creek` ≠ uniquely Meadow Creek Farms or Meadow Creek Grain** (MCR-118 / TR-107).
- **SMP-604Q `MC-118` ≠ sole source MCR-118** after MCR-118 and S-52 both entered BIN-14.
- **Consignee HFM-N / HFM-E ≠ mill receipt** (`consignee_is_not_receipt` on all four manifests).
- **Commercial DR-44 on RL-8841 / HFM-IN-601 ≠ physical contents of PGE-OUT-5001**.
- **Lab lots that look like tickets** (MC-118, N3/EF-18?) **without** a named hopper/ticket link.

Contrast: mill origin labels `PG-OUT-5001/5002/5004` matching elevator movements, and SMP-602B tied to HFM-IN-602, are recorded as established identities.

---

### NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** There is **no** `mill_intake` for `movement:PGE-OUT-5003`. The three North receipts are HFM-IN-601/602/604 (movements 5001/5002/5004). Consignee on NS-8910 is **HFM-E**, not HFM-N. Extract coverage states the **HFM-North receiving log is complete for 2025-09-05 through 2025-09-07**. That supports a **justified negative**: no HFM-N receiving record for this truck in that window.

**HFM-E:** Absence from this workspace does **not** justify “HFM-E has no record.” Purpose `mill-receipt-absent-PGE-OUT-5003` and HFM-North coverage both say North completeness does not support a conclusion about East. `site:hfm-east` exists; no East mill_intake rows appear; that is **missing evidence**, not a demonstrated non-event.
