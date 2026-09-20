I'll start by reading `INSTRUCTION.md` and `consumer_questions.md`, then work through every question with the files in this workspace.I have the grain-flow tables and unresolved-requirement notes. Next I’ll map each question to those facts, including what is established versus left open.

**NQ-01. Inbound loads for PGE-OUT-5002**

**Established:** outbound `PGE-OUT-5002` (`movement:PGE-OUT-5002`, loadout `LD-19`) drew **26,000 kg from North House 12 (`BIN-12` / `bin:north-house-12`)** onto `NST-204`. Hopper move `BM-004` (work order `OUT-5002`, 2025-09-04T13:02) notes **`WB-390 / EF-18`**, and `ticket_named_on_move` names those two scale tickets on `BM-004`. `BM-005` then loaded that pit quantity onto the truck. Mill slip `HFM-IN-602` and lab `SMP-602B` (`local_lot` `WB390 / EF18`, hint `receiving slip HFM-IN-602`, “combined truck sample”) match the same movement.

Inbound tickets:

- **`WB-390` / `ER-7721`** (`ticket:wb-390`): 23,850 kg, 2025-09-03T09:20, into `BIN-12` via `BM-002`
- **`EF-18` / `ER-7729`** (`ticket:ef-18`): 17,900 kg, 2025-09-03T11:05, into `BIN-12` via `BM-003`

**Not established:** kilogram split between those two tickets (`ticket_named_on_move` is “not a quantity allocation”). **`DR-44` occupied the same bin** (`BM-001`) but is **not named** on the `OUT-5002` hopper; contribution of `DR-44` to this truck is not established. Commercial scoping of `DR-44` to `RL-8841` / `HFM-IN-601` is not a bin allocation.

---

**NQ-02. Downstream shipments from BIN-12, and source allocation**

**Established occupants of `BIN-12`:** `DR-44`, `WB-390`, `EF-18` (`BM-001`–`BM-003`).

**Downstream movements that left `BIN-12`:**

| Movement | Loadout | Hopper / allocation |
|---|---|---|
| **PGE-OUT-5001** | `LD-18`, 39,000 kg, 2025-09-04T09:40 | **No individual source allocation.** Unresolved `physical-ticket-allocation-PGE-OUT-5001`: bin already held all three tickets; no hopper ticket names. Continues to `HFM-IN-601` → `MILL-2206` / `FEED-2206`. |
| **PGE-OUT-5002** | `LD-19`, 26,000 kg | **Named sources `WB-390` and `EF-18` on `BM-004`**, not a per-ticket quantity split. Continues to `HFM-IN-602` → `MILL-2207` / `FEED-2207`. |
| **PGE-OUT-5003** | `LD-20`, 12,000 kg | **No individual source allocation.** `BM-006` hopper: “no ticket on hopper sheet”; cargo mark `N3 / EF-18?` is not a validated ticket. No mill intake in the world. |

Only **PGE-OUT-5002** has hopper-named source tickets. **5001 and 5003 do not.**

---

**NQ-03. Grain received 2025-09-03 09:00–12:00 -05:00**

**Received in-window (two Prairie Gate intakes):**

1. **`WB-390` / `ER-7721`**, 09:20, 23,850 kg HRW, Lane 1, Willow Bend Farms → `BIN-12` at 09:47 (`BM-002`).
2. **`EF-18` / `ER-7729`**, 11:05, 17,900 kg HRW, Lane 1, East Fork Co-op → `BIN-12` at 11:28 (`BM-003`).

No other `elevator_intake` falls in that window.

**Later, established:** both tickets are named on the **26,000 kg `OUT-5002` draw** (`BM-004`/`BM-005`/`LD-19`), shipped `NS-8848` / `NS-5002-B` to HFM-North, received as **`HFM-IN-602`** (25,500 kg, silo `S-5`), processed **`MILL-2207` → `FEED-2207`**. Title of `WB-390` moved to **GrainLink Merchants** at 15:00 the same day (`TR-102`); elevator remained holder. `EF-18` has **no** `ownership_event`.

**Not established:** whether any of this grain also left on **PGE-OUT-5001** (earlier 04 Sep from the same bin) or **PGE-OUT-5003**; those allocations are unresolved. Combined inbound **41,750 kg** vs **26,000 kg** on 5002, so remainder in `BIN-12` is unallocated by ticket. Loadout vs mill kg for 5002 (26,000 vs 25,500) is recorded and unexplained, not a different movement.

---

**NQ-04. Processor receipts with complete upstream provenance to identified inbound load(s)**

Mill receipts: `HFM-IN-601`, `HFM-IN-602`, `HFM-IN-604` (all HFM-North).

- **`HFM-IN-602`:** **yes, to identified loads `WB-390` and `EF-18`** via `PGE-OUT-5002` + named hopper `BM-004`. Per-ticket weights are not allocated. BOL identity of the truck is established despite the 26,000/25,500 kg gap.
- **`HFM-IN-601`:** movement `PGE-OUT-5001` is established; **physical inbound tickets are not**. Unresolved blend of `DR-44`/`WB-390`/`EF-18`. Commercial `DR-44` ↔ `RL-8841`/`HFM-IN-601` is not physical allocation.
- **`HFM-IN-604`:** movement `PGE-OUT-5004` from `BIN-14` after **`MCR-118` and `S-52`**; hopper “no individual ticket”. Unresolved `physical-ticket-allocation-PGE-OUT-5004`.

**PGE-OUT-5003 has no processor receipt** in the world (`mill-receipt-absent-PGE-OUT-5003`).

---

**NQ-05. Unresolved chains (from `purpose_requirement_failure`)**

1. **`physical-ticket-allocation-PGE-OUT-5001`** — which of `DR-44`/`WB-390`/`EF-18` physically went on `LD-18`.
2. **`physical-ticket-allocation-PGE-OUT-5003`** — no hopper ticket; `N3 / EF-18?` not a validated source.
3. **`mill-receipt-absent-PGE-OUT-5003`** — 12,000 kg departed `NS-8910` to consignee `HFM-E`; no mill slip in extracts.
4. **`mcr-118-grower-identity`** — intake “M. Creek”; desk claims **Meadow Creek Farms** and **Meadow Creek Grain**; no account key.
5. **`physical-ticket-allocation-PGE-OUT-5004`** — `BIN-14` blend of `MCR-118` and `S-52` on `LD-21`.
6. **`lab-sample-SMP-UNLISTED-source-ticket`** — source ticket not recorded; route-packet `N3 / EF-18?` unvalidated.
7. **`lab-sample-SMP-604Q-ticket`** — labeled South House 14 / `MC-118`; after both deliveries in `BIN-14`, not allocated to one ticket.
8. **`quantity-differences-on-established-movements`** — 5001: 39,000/38,700; 5002: 26,000/25,500; 5004: 19,000/18,800 kg; same BOLs, unexplained.

---

**NQ-06. Missing linkage for complete provenance of PGE-OUT-5003**

Two recorded gaps, not one:

1. **Inbound physical source:** `BM-006` hopper has **no ticket**. Carrier cargo mark **`N3 / EF-18?` is not a validated scale ticket**; `N3` is used as a route code (`carrier_departure.route_note`; unresolved `physical-ticket-allocation-PGE-OUT-5003`). Loadout `LD-20` only identifies **`BIN-12`**, not a receiving ticket.
2. **Downstream mill receipt:** no `mill_intake` for this movement. Consignee **`HFM-E` is a destination code, not a receipt** (`consignee_is_not_receipt` on `NS-8910`; `mill-receipt-absent-PGE-OUT-5003`).

The specific missing **source** link is hopper/ticket allocation from `BIN-12`. The specific missing **destination** link is a mill receiving slip.

---

**NQ-07. Ownership and custody of WB-390 at 2025-09-04 13:10:00-05:00**

**Owner (established for ticket `WB-390`):** **GrainLink Merchants** (`TR-102` title change, effective 2025-09-03T15:00 through 2025-09-05T10:50; `commercial_scope` ticket).

**Custody is not a single ticket-wide fact at that instant:**

- **`TR-102`** still lists **holder_after = Prairie Gate Elevator** for ticket `WB-390` until 2025-09-05T10:50.
- **`TR-104`** (effective **13:05**, scope **`OUT-5002` / movement**, not the ticket) lists **holder_after = Northstar Bulk Transport**, owner still GrainLink. Basis: dispatch handoff `NS-8848`.
- Physically, the named **26,000 kg `WB-390 / EF-18` draw** was in **`LOAD-PIT-2`** (after `BM-004` 13:02, before `BM-005` 13:14). How much of ticket `WB-390` was in that draw vs still in `BIN-12` is **not allocated**. Remainder in `BIN-12` would still be Prairie Gate custody under `TR-102`.

**Not established:** that “the WB-390 material” as a whole had left elevator custody, or a single custodian for 100% of the ticket at 13:10.

---

**NQ-08. Downstream material affected by SMP-602B**

**Established:** `SMP-602B` (`LAB-4419`, 2025-09-05T13:10) is a **combined truck sample** of mill receipt **`HFM-IN-602`** (`PGE-OUT-5002`), lots labeled `WB390 / EF18`, aflatoxin below limit.

**Affected established downstream:** **`HFM-IN-602`** (silo `S-5`) and mill run **`MILL-2207` / batch `FEED-2207`** (grower feed, started 15:10 the same day).

**Not established:** a result attached to `WB-390` or `EF-18` separately, or to other movements (`5001`/`5003`) that also used `BIN-12`.

---

**NQ-09. Apparent identity matches that must not be committed**

Do **not** treat as established:

1. **`N3 / EF-18?` = ticket `EF-18`** (cargo mark / `SMP-UNLISTED` local lot; `N3` is a route code; source ticket not recorded).
2. **Intake “M. Creek” = Meadow Creek Farms or Meadow Creek Grain** (duplicate claims, no account key; `TR-107` / `mcr-118-grower-identity`).
3. **`SMP-604Q` local lot `MC-118` = solely inbound `MCR-118`** (South House 14 cargo after `MCR-118` and `S-52` were both placed).
4. **Carrier consignee `HFM-E` / `HFM-N` = a mill receiving slip** (`consignee_is_not_receipt`).
5. **Ownership scope of `DR-44` to `RL-8841` / `HFM-IN-601` = physical grain on `PGE-OUT-5001`**.
6. **Same-bin occupancy = contribution to a given loadout** unless the hopper/desk names tickets (as for `OUT-5002`).

`known_as` links such as `PG-OUT-5002` ↔ `PGE-OUT-5002`, `WB390` ↔ `WB-390`, `MC-118` ↔ `MCR-118` as **tokens** are recorded; they do not by themselves allocate blended cargo.

---

**NQ-10. Processor record for PGE-OUT-5003 at HFM-N vs HFM-E**

**HFM-N:** There is **no** `mill_intake` tying `PGE-OUT-5003` to `site:hfm-north`. North receipts in-world are only `HFM-IN-601/602/604` for **5001, 5002, 5004**. Extract coverage: **HFM-North receiving log is complete for 2025-09-05 through 2025-09-07**, and 5003 departed 2025-09-05 (consignee `HFM-E`, not North). **Justified negative: HFM-N has no receiving record for this movement** in that complete North log.

**HFM-E:** **No mill intake row at East appears**, and consignee `HFM-E` is not a receipt. That is **absence in the bounded extracts**, not East-mill completeness. Unresolved `mill-receipt-absent-PGE-OUT-5003` and coverage: **“No conclusion about other HFM sites follows from [North log] absence.”** **Cannot justify “HFM-E has no such record.”**
