I'll start by reading the instruction file and the questions, then work through each item with the local files.The grain world is in SQLite. I'll inspect the schema and dump the tables that the questions depend on.Checking mill uniqueness and whether any mill intake is linked to PGE-OUT-5003 under another id.Answers use only `world/world.sqlite` and the declared purpose. Assertion ids are from that world.

---

### NQ-01. Inbound loads for PGE-OUT-5002

**Established:** PGE-OUT-5002 is supplied by inbound tickets **WB-390** (`ticket:wb-390`, ER-7721) and **EF-18** (`ticket:ef-18`, ER-7729).

- Loadout `loadout:LD-19` (`assertion:acedc74b500dc78e2412d1b0`) is `movement:PGE-OUT-5002` from `bin:north-house-12` (BIN-12), 26,000 kg, truck `truck:nst-204`.
- Bin move `move:BM-004` (`assertion:30c4b53f2e3501133a11fa22`) names **WB-390 / EF-18**, work order OUT-5002, 26,000 kg BIN-12 → LOAD-PIT-2.
- `ticket_named_on_move` names those tickets on BM-004 (`assertion:210852e82d6e4cb3a2734163`, `assertion:2b65b98ac4fe761678c2f768`).
- Intakes: WB-390 ER-7721 23,850 kg (`assertion:629c1317c180d9cd46aa3444`); EF-18 ER-7729 17,900 kg (`assertion:613864c2a9c856c23ad51a82`).

**Not established:** DR-44 did occupy BIN-12 earlier (BM-001), but it is not named on the OUT-5002 hopper path. Commercial scoping of DR-44 to RL-8841 / HFM-IN-601 is recorded as **not** a bin allocation (`physical-ticket-allocation-PGE-OUT-5001`). Kilograms are not split between WB-390 and EF-18 on the 26,000 kg truck (`quantity-differences-on-established-movements` is a mill-weight issue, not a third inbound ticket).

---

### NQ-02. Downstream shipments from BIN-12, and source allocation

BIN-12 is `bin:north-house-12` (`known_as` token BIN-12, `assertion:11c10e8e1a236e4efb02af57`).

**Established occupants then loadouts from that bin:**

| Shipment | Evidence it left BIN-12 | Individual source allocation |
|---|---|---|
| **PGE-OUT-5001** | `loadout:LD-18` (`assertion:1ac7b10c96430ae7559a3ca3`) | **No.** Hopper does not name tickets (`physical-ticket-allocation-PGE-OUT-5001`). |
| **PGE-OUT-5002** | LD-19 + BM-004/BM-005 | **Yes, jointly:** WB-390 and EF-18 named on BM-004. No per-ticket kg split. |
| **PGE-OUT-5003** | LD-20 + BM-006 (`assertion:b96739fb49f157806b38c41c`, `assertion:175ead3f295300945a7efaad`, hopper “no ticket”) | **No.** (`physical-ticket-allocation-PGE-OUT-5003`) |

BIN-14 loadouts (PGE-OUT-5004) are not BIN-12.

Further mill batches FEED-2206 / FEED-2207 inherit 5001 / 5002; they are process lots, not additional elevator shipments.

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 −05:00

**Received in window (two loads only):**

1. **WB-390** arrived 09:20 (`assertion:629c1317c180d9cd46aa3444`), placed BIN-12 at 09:47 (BM-002).
2. **EF-18** arrived 11:05 (`assertion:613864c2a9c856c23ad51a82`), placed BIN-12 at 11:28 (BM-003).

DR-44 (09-02) and MCR-118 / S-52 (09-07) are outside the window.

**What happened to that grain:**

- During the window: Prairie Gate intake, assigned/moved into BIN-12.
- Later **named** on OUT-5002 (BM-004 13:02 on 09-04) → LD-19 → manifest NS-8848 / BOL NS-5002-B → mill receipt **HFM-IN-602** (`assertion:6370a150371873c87767f3af`) → mill run **MILL-2207** / batch **FEED-2207** (`assertion:364d1909edf90414ec549772`).
- WB-390 title to GrainLink Merchants at 15:00 the same day (TR-102, after the window).
- Combined inbound kg (23,850 + 17,900 = 41,750) exceeds the 26,000 kg named OUT-5002 draw. Remaining WB-390/EF-18 in BIN-12 is **not** allocated to OUT-5001 or OUT-5003.

---

### NQ-04. Processor receipts with complete upstream provenance

Mill intakes: HFM-IN-601 (PGE-OUT-5001), HFM-IN-602 (PGE-OUT-5002), HFM-IN-604 (PGE-OUT-5004). There is no mill intake for PGE-OUT-5003.

**Complete to identified inbound load(s):** only **HFM-IN-602**. Movement identity is established (BOL NS-5002-B), and the elevator hopper names **WB-390** and **EF-18**. Unexplained 26,000 vs 25,500 kg is recorded and is not treated as a different movement.

**Not complete:**

- **HFM-IN-601:** truck identity to PGE-OUT-5001 is established; physical tickets from BIN-12 are unresolved. DR-44 commercial scope to RL-8841 / HFM-IN-601 is not a bin allocation.
- **HFM-IN-604:** truck identity to PGE-OUT-5004 is established; BIN-14 held MCR-118 and S-52 with no individual ticket (`physical-ticket-allocation-PGE-OUT-5004`).

---

### NQ-05. Unresolved chains and the unresolved part

From `purpose_requirement_failure` (all `EXPLICIT_UNRESOLVED`):

1. **physical-ticket-allocation-PGE-OUT-5001** — which of DR-44 / WB-390 / EF-18 physically went on LD-18; hopper unnamed.
2. **physical-ticket-allocation-PGE-OUT-5003** — BM-006 hopper has no ticket; cargo mark `N3 / EF-18?` is not a validated source ticket (N3 is a route code).
3. **mill-receipt-absent-PGE-OUT-5003** — no HFM receiving slip in extracts; consignee HFM-E.
4. **physical-ticket-allocation-PGE-OUT-5004** — MCR-118 vs S-52 in South House 14; hopper “no individual ticket.”
5. **mcr-118-grower-identity** — intake “M. Creek”; desk claims Meadow Creek Farms and Meadow Creek Grain; no account key.
6. **lab-sample-SMP-UNLISTED-source-ticket** — source ticket not recorded; route-packet note is not a ticket.
7. **lab-sample-SMP-604Q-ticket** — labeled South House 14 cargo / MC-118 after both MCR-118 and S-52 were in BIN-14.
8. **quantity-differences-on-established-movements** — 39000/38700 (5001), 26000/25500 (5002), 19000/18800 (5004) unexplained; movement identity still holds.

---

### NQ-06. Missing linkage for PGE-OUT-5003 provenance

**Primary missing physical link:** no validated source ticket on the load. Hopper BM-006: “no ticket on hopper sheet.” Carrier cargo mark `N3 / EF-18?` is not a scale ticket; N3 is a route code (`assertion:1ca11e54f7973c1299ab5530`, `physical-ticket-allocation-PGE-OUT-5003`).

**Second missing link (downstream):** no mill_intake row for `movement:PGE-OUT-5003` (`mill-receipt-absent-PGE-OUT-5003`). Consignee HFM-E is not a receipt (`consignee_is_not_receipt` `assertion:44b894410d735ff9cabd5b2a`).

---

### NQ-07. WB-390 ownership and custody at 2025-09-04 13:10:00−05:00

**Owner: GrainLink Merchants.**  
TR-102 (`assertion:5a72b9b6edd288bd1bbaf5af`): title WB-390 from 2025-09-03T15:00 through 2025-09-05T10:50; `owner_after` GrainLink Merchants. TR-104 (`assertion:a2dc631527e2a22ebdd7f3ff`) on OUT-5002 also has `owner_after` GrainLink from 13:05.

**Custody (for the OUT-5002-named WB-390):** **Northstar Bulk Transport.**  
TR-104 custody change on `movement:PGE-OUT-5002` effective **13:05** (before 13:10): `holder_after` Northstar Bulk Transport, basis “dispatch handoff NS-8848.”

Physical location at 13:10: BM-004 at 13:02 moved named WB-390/EF-18 into LOAD-PIT-2; BM-005 onto the truck is 13:14; loadout timestamp 13:15. Custody on the movement record already flipped at 13:05.

**Caveat:** TR-102 still lists Prairie Gate as `holder_after` on the ticket until mill receipt. The movement-level TR-104 overlay is the dispatch custody for the named OUT-5002 quantity. Remaining unsplit WB-390 kg still in BIN-12 is not separately custody-recorded.

---

### NQ-08. Downstream material affected by SMP-602B

**SMP-602B** (`assertion:4fcd0e99c9c1d56495c6c461`): aflatoxin “below limit,” local lot `WB390 / EF18`, hint “receiving slip HFM-IN-602,” combined truck sample.

**Established scope:** mill receipt **HFM-IN-602** (PGE-OUT-5002 / NS-5002-B) and mill output **FEED-2207** from **MILL-2207** (`input_receipt_id` HFM-IN-602). Named inbound tickets on that truck: WB-390 and EF-18.

**Not established:** applying the sample to DR-44, to other BIN-12 trucks (5001/5003), or to BIN-14 material.

---

### NQ-09. Apparent identity matches that must stay uncommitted

Do **not** treat as established:

1. **`N3 / EF-18?` ↔ ticket EF-18** — N3 is a route code; mark is not a validated ticket (OUT-5003 cargo, SMP-UNLISTED local_lot).
2. **`M. Creek` ↔ Meadow Creek Farms or Meadow Creek Grain** — duplicate claims, no account key (TR-107, `mcr-118-grower-identity`).
3. **SMP-604Q `MC-118` ↔ exclusive MCR-118** — cargo is South House 14 after MCR-118 **and** S-52.
4. **Consignee HFM-E / HFM-N ↔ mill receipt** — `consignee_is_not_receipt` on all four manifests.
5. **Commercial DR-44 ↔ physical grain on PGE-OUT-5001** — scoped to RL-8841 / HFM-IN-601, explicitly not a bin allocation.
6. **Loadout vs mill kg mismatch ↔ different movement** — identity is established; weights unexplained.

Aliases that **are** committed (e.g. PGE-OUT-5002 / PG-OUT-5002 / OUT-5002, BIN-12 / North House 12, DR-44 / DR44) should not be conflated with the list above.

---

### NQ-10. Processor receipt for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** There is **no** `mill_intake` for `movement:PGE-OUT-5003`. North receipts in the world are only HFM-IN-601, HFM-IN-602, HFM-IN-604. HFM-North receiving_log is claimed complete for 2025-09-05 through 2025-09-07 (`assertion:60e97e17725e645601667102`). OUT-5003 departed 2025-09-05T07:24 with consignee **HFM-E**, not HFM-N. Absence at **HFM-N** is a justified negative for this working set.

**HFM-E:** Evidence does **not** justify “HFM-E has no such record.” The North log’s completeness does not speak to East (`same coverage claim`; `mill-receipt-absent-PGE-OUT-5003`). Extracts are a bounded working set (`assertion:b1ca5a261f71be06de56b517`). Missing slip here is unresolved absence, not a proof that East never received the truck.
