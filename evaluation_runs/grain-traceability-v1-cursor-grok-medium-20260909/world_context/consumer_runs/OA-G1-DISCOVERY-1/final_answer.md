I'll read the instruction and question files first, then work through every question using only what's in this workspace.Answers use only `world/world.sqlite` and the purpose/admission files. Established means a recorded relation; unresolved is an explicit `purpose_requirement_failure` or a missing link the purpose tells us not to invent.

---

**NQ-01. Which inbound loads contributed to outbound shipment PGE-OUT-5002?**

**Established:** inbound tickets **WB-390** (`ER-7721`, 23,850 kg) and **EF-18** (`ER-7729`, 17,900 kg).

- `elevator_loadout` `LD-19` loads **PGE-OUT-5002** from `bin:north-house-12` (BIN-12), 26,000 kg, truck `NST-204` (`assertion:acedc74b500dc78e2412d1b0`).
- `bin_transfer` `BM-004` (`2025-09-04T13:02:00-05:00`) moves 26,000 kg BIN-12 → `LOAD-PIT-2` with material note `WB-390 / EF-18`, work order `OUT-5002` (`assertion:30c4b53f2e3501133a11fa22`).
- `ticket_named_on_move` names **WB-390** and **EF-18** on `BM-004` (`assertion:210852e82d6e4cb3a2734163`, `assertion:2b65b98ac4fe761678c2f768`). That relation is a named token, not a kilogram split.
- `BM-005` then loads the pit onto `NST-204`. Carrier `NS-8848` / BOL `NS-5002-B`. Lab `SMP-602B` is a combined truck sample on mill slip `HFM-IN-602` labeled `WB390 / EF18`.
- Unlike OUT-5001/5003/5004, there is **no** `physical-ticket-allocation-PGE-OUT-5002` unresolved requirement.

**Not established:** kilogram split between WB-390 and EF-18; whether residual **DR-44** still in BIN-12 entered the truck. DR-44 was in BIN-12 from `BM-001` but is **not** named on the OUT-5002 hopper sheet; commercial scope of DR-44 is `RL-8841` / `HFM-IN-601` (`TR-103`/`TR-106`), which the purpose says is not a bin allocation.

---

**NQ-02. Which downstream shipments contain material that occupied BIN-12, and which of those have individual source allocation?**

**Established occupants of BIN-12 (`bin:north-house-12`):** DR-44 (`BM-001`), WB-390 (`BM-002`), EF-18 (`BM-003`).

**Downstream elevator shipments from that bin** (`elevator_loadout`):

| Movement | Loadout | Individual source allocation |
|---|---|---|
| **PGE-OUT-5001** | `LD-18`, 39,000 kg | **No.** Unresolved `physical-ticket-allocation-PGE-OUT-5001`: bin already held DR-44, WB-390, EF-18; no hopper tickets; desk comment is only `seal 8841`. |
| **PGE-OUT-5002** | `LD-19`, 26,000 kg | **Named sources, not a single-ticket split.** Hopper `BM-004` names WB-390 and EF-18. Not listed as an unresolved physical allocation. Still not a per-ticket quantity allocation (`ticket_named_on_move` description). |
| **PGE-OUT-5003** | `LD-20`, 12,000 kg | **No.** Unresolved `physical-ticket-allocation-PGE-OUT-5003`: hopper `BM-006` is `no ticket on hopper sheet`; cargo mark `N3 / EF-18?` is not a validated ticket. |

Further downstream: mill `HFM-IN-601` ← 5001, `HFM-IN-602` ← 5002; batches `FEED-2206` / `FEED-2207`. **No mill intake** for 5003.

---

**NQ-03. What happened to grain received 2025-09-03 09:00:00-05:00 through 2025-09-03 12:00:00-05:00?**

**Received in window** (`elevator_intake`):

1. **WB-390** / `ER-7721` — 09:20, Lane 1, 23,850 kg HRW, Willow Bend Farms → assigned BIN-12. `BM-002` 09:47 INTAKE-1 → BIN-12.
2. **EF-18** / `ER-7729` — 11:05, Lane 1, 17,900 kg HRW, East Fork Co-op → assigned BIN-12. `BM-003` 11:28 INTAKE-1 → BIN-12.

**Then established:**

- Both sit in BIN-12 with earlier **DR-44**.
- **WB-390 title:** `TR-102` at 15:00 same day — owner **GrainLink Merchants**, holder still Prairie Gate (broker release `GL-88`).
- **EF-18:** no `ownership_event` row; title/custody after intake is **not** recorded.
- **26,000 kg** named WB-390 / EF-18 leave on **PGE-OUT-5002** (`BM-004`/`BM-005`, `LD-19`, `NS-8848`, 13:15–13:23 on 2025-09-04) → mill **HFM-IN-602** (25,500 kg, silo S-5) → mill run **MILL-2207** → **FEED-2207**.
- Combined intake 41,750 kg vs 26,000 kg named on OUT-5002: **remainder in BIN-12 is not allocated** to later loadouts (5001 left earlier the same day without tickets; 5003 has no ticket). Do not treat later BIN-12 trucks as proven remainder of this window.

---

**NQ-04. Which processor receipts have complete upstream provenance back to an identified inbound load or loads?**

Three `mill_intake` rows, all at **HFM-N**:

| Receipt | Movement | Inbound loads |
|---|---|---|
| **HFM-IN-602** | PGE-OUT-5002, BOL `NS-5002-B` | **Yes — WB-390 and EF-18** via `BM-004` / `ticket_named_on_move`. Movement identity established. Kg loadout 26,000 vs mill 25,500 is recorded and unexplained (`quantity-differences-on-established-movements`), not a different movement. |
| **HFM-IN-601** | PGE-OUT-5001, BOL `RL-5001-A` | **No complete physical provenance.** `physical-ticket-allocation-PGE-OUT-5001`. Commercial DR-44 ↔ `RL-8841` / `HFM-IN-601` is not a bin allocation. |
| **HFM-IN-604** | PGE-OUT-5004, BOL `RL-5004-Q` | **No.** `physical-ticket-allocation-PGE-OUT-5004`: MCR-118 and S-52 both in BIN-14; hopper `no individual ticket`. |

No mill receipt for PGE-OUT-5003. **Only HFM-IN-602** has identified inbound load(s). Quantity split between those two tickets is still not allocated.

---

**NQ-05. Which traceability chains remain unresolved, and what part of each chain is unresolved?**

From `purpose_requirement_failure` (all `EXPLICIT_UNRESOLVED`):

1. **PGE-OUT-5001 physical tickets** (`elevator_loadout`) — which BIN-12 tickets (DR-44, WB-390, EF-18) supplied `LD-18`; no hopper names.
2. **PGE-OUT-5003 physical tickets** (`carrier_departure`) — hopper unnamed; `N3 / EF-18?` not a validated source ticket.
3. **PGE-OUT-5003 mill intake** (`mill_intake`) — truck left on `NS-8910`; no HFM receiving slip in extracts.
4. **MCR-118 grower identity** (`elevator_intake`) — scale name `M. Creek`; commercial claims Meadow Creek Farms and Meadow Creek Grain; no account key (`TR-107`).
5. **PGE-OUT-5004 physical tickets** (`elevator_loadout`) — MCR-118 vs S-52 in South House 14; hopper `no individual ticket`.
6. **SMP-UNLISTED source ticket** (`lab_result`) — source ticket not recorded; route-packet `N3 / EF-18?` not validated.
7. **SMP-604Q ticket** (`lab_result`) — labeled South House 14 cargo / `MC-118` after both MCR-118 and S-52 were in BIN-14.
8. **Quantity differences** (`mill_intake`) — 5001 39000/38700, 5002 26000/25500, 5004 19000/18800 kg; identity of those trucks is established; the kg gaps are unexplained.

**Absent, not listed as a failure:** no ownership events for EF-18 or S-52; that is missing assertion, not a negative finding.

---

**NQ-06. What specific missing linkage prevents complete provenance for PGE-OUT-5003?**

Two recorded gaps:

1. **Source-ticket link (primary for cargo identity):** `physical-ticket-allocation-PGE-OUT-5003`. `BM-006` hopper: `no ticket on hopper sheet`. Manifest `NS-8910` cargo mark `N3 / EF-18?` is **not** a validated scale ticket; `N3` is a route code elsewhere (loadout route `EAST-1`). That is the missing inbound-ticket linkage.
2. **Processor receiving link:** `mill-receipt-absent-PGE-OUT-5003`. 12,000 kg left Prairie Gate; **no** `mill_intake` row. Consignee **HFM-E**. HFM-North log completeness does not speak to East.

Loadout `LD-20` from BIN-12 and carrier departure are established; the chain breaks at ticket allocation, then again at mill receipt.

---

**NQ-07. At 2025-09-04 13:10:00-05:00, who owned and who had custody of the WB-390 material?**

**Owner (title): GrainLink Merchants.**

- `TR-102` (`scope_ref` WB-390, `commercial_scope` `ticket:wb-390`): title change 2025-09-03T15:00 through 2025-09-05T10:50; `owner_after` GrainLink Merchants (`assertion:5a72b9b6edd288bd1bbaf5af`).
- `TR-104` (scope **movement** PGE-OUT-5002, effective 13:05): `owner_after` also GrainLink Merchants.

**Custody / holder — two scopes, do not collapse:**

- **Ticket WB-390 (`TR-102`):** `holder_after` still **Prairie Gate Elevator** until mill time 2025-09-05T10:50.
- **Movement OUT-5002 (`TR-104`):** custody change 2025-09-04T13:05 — from Prairie Gate to **Northstar Bulk Transport**; `holder_after` Northstar. Basis: dispatch handoff `NS-8848`. Hopper `BM-004` at **13:02** already named WB-390 on that movement.

**Physical location at 13:10:** after `BM-004` (13:02) and before `BM-005` (13:14) / `LD-19` (13:15) — **LOAD-PIT-2 at Prairie Gate**, not yet on `NST-204`.

So: **title GrainLink**; **recorded truck custody for the named OUT-5002 load is Northstar from 13:05**; **ticket-level holder text still Prairie Gate**; **grain is physically in the Prairie Gate load pit**.

---

**NQ-08. Which downstream material is affected by inspection result SMP-602B?**

**SMP-602B** (`assertion:4fcd0e99c9c1d56495c6c461`): 2025-09-05T13:10, `LAB-4419`, lot `WB390 / EF18`, hint **receiving slip HFM-IN-602**, aflatoxin below limit, comment `combined truck sample`.

**Established downstream of that slip:**

- Mill receipt **HFM-IN-602** ← movement **PGE-OUT-5002** (BOL `NS-5002-B`).
- Mill run **MILL-2207** consumes HFM-IN-602 → output batch **FEED-2207** (grower feed), started 2025-09-05T15:10 (`assertion:364d1909edf90414ec549772`).

**Upstream named on the same truck (not further mill product):** WB-390 and EF-18 via `BM-004`.

**Not established as affected:** HFM-IN-601 / FEED-2206, PGE-OUT-5001/5003/5004, SMP-604Q, SMP-UNLISTED.

---

**NQ-09. Which apparent identity matches should not be committed as established?**

Do **not** treat these as established identity (purpose `preserve-unsupported-identity-as-unresolved` plus explicit failures):

1. **`N3 / EF-18?` = ticket EF-18** — cargo mark / lab lot; N3 is a route code; hopper unnamed (`physical-ticket-allocation-PGE-OUT-5003`, `lab-sample-SMP-UNLISTED-source-ticket`).
2. **SMP-604Q `MC-118` = solely MCR-118** — after MCR-118 and S-52 both in BIN-14 (`lab-sample-SMP-604Q-ticket`). Token `MC-118` → `ticket:mcr-118` in `known_as` is a lab spelling, not cargo allocation.
3. **`M. Creek` = Meadow Creek Farms or Meadow Creek Grain** — `mcr-118-grower-identity` / `TR-107`.
4. **Consignee `HFM-N` / `HFM-E` = a mill receiving slip** — `consignee_is_not_receipt` on all four manifests.
5. **Commercial DR-44 ↔ `RL-8841` / HFM-IN-601 = physical BIN-12 allocation to PGE-OUT-5001** — purpose note on `physical-ticket-allocation-PGE-OUT-5001`.
6. **Kg mismatches = different truck identities** — BOL identity of 5001/5002/5004 is established; gaps are unexplained, not new movements.

`known_as` aliases (BIN-12/B-12/North House 12, PG-OUT-5002, WB390, etc.) **are** committed identifier maps, not the matches above.

---

**NQ-10. Is there a processor receiving record for PGE-OUT-5003 at HFM-N, and can the evidence justify saying that HFM-E has no such record?**

**HFM-N:** **No** `mill_intake` for `movement:PGE-OUT-5003`. The three receipts are HFM-IN-601/602/604, all `site:hfm-north`, none linked to 5003. Consignee on `NS-8910` is **HFM-E**, not HFM-N. Extract coverage: HFM-North receiving log is **complete for 2025-09-05 through 2025-09-07** (`assertion:60e97e17725e645601667102`). Departure is 2025-09-05T07:24. Absence of a North slip in that complete window supports **no HFM-N receiving record for this movement**. Completeness of that log **does not** imply anything about other HFM sites.

**HFM-E:** **Cannot** justify “HFM-E has no such record.” Failure `mill-receipt-absent-PGE-OUT-5003` states there is no HFM slip **in the supplied extracts**, consignee is HFM-E, and **North completeness does not support a conclusion about East mill receiving.** `workspace_extracts` is a bounded working set, not a claim that every organizational record exists here. Absence of an East row is **missing evidence**, not a justified negative for HFM-E.
