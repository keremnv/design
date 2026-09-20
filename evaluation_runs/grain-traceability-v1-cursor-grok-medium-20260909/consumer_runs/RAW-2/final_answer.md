I'll start by reading the instruction file and the question list so I can answer from the workspace only.# Downstream grain traceability answers

Evidence is the Prairie Gate / Hearthland extracts in `evidence/`, plus the joining rules in `evidence/operating_notes.md`. Identifier aliases used below: `BIN-12` = North House 12; elevator `PGE-OUT-####` vs mill `PG-OUT-####` joined only where a bill of lading matches.

---

### NQ-01. Inbound loads that contributed to PGE-OUT-5002

**Established as named on the hopper sheet:** inbound tickets **WB-390** (receipt `ER-7721`, Willow Bend Farms, 23 850 kg) and **EF-18** (receipt `ER-7729`, East Fork Co-op, 17 900 kg).

**Facts:** `LD-19` loaded **26 000 kg** as `PGE-OUT-5002` from North House 12 on 2025-09-04 13:15. `BM-004` at 13:02 moved 26 000 kg `BIN-12` → `LOAD-PIT-2` with `material_note` `WB-390 / EF-18` and work order `OUT-5002`; `BM-005` put that quantity on `TRUCK-NS204`. Manifest `NS-8848` cargo mark `PGE-OUT-5002`.

**Not established:** portion of the 26 000 kg from WB-390 vs EF-18. Loadout `LD-19` desk comment is only `seal 8848`; notes say a loadout does not allocate a blend to individual tickets unless the desk comment says so. **DR-44** (`ER-7714`) was already in BIN-12 (`BM-001`) and was not isolated before this draw (`BM-002`/`BM-003` preceded `LD-18`/`LD-19`); it is **not named** on `BM-004`, so contribution of DR-44 is not established and not excluded.

---

### NQ-02. Downstream shipments that held BIN-12 material, and individual source allocation

**Shipments that occupied BIN-12 (North House 12):**

| Outbound | Evidence it came from BIN-12 | Individual source allocation |
|---|---|---|
| **PGE-OUT-5001** | `LD-18` spout from North House 12, 39 000 kg | **None.** No `bin_movements` hopper row; desk comment is only `seal 8841`. BIN-12 already held DR-44 + WB-390 + EF-18. |
| **PGE-OUT-5002** | `LD-19` + `BM-004`/`BM-005` | **None individual.** Hopper names a **combined** `WB-390 / EF-18` pair, not ticket-level shares. |
| **PGE-OUT-5003** | `LD-20` + `BM-006` | **None.** Hopper `material_note` is `no ticket on hopper sheet`. |

Processor-side continuations of those BIN-12 loads (where received): **HFM-IN-601** (BOL `RL-5001-A` ↔ `PGE-OUT-5001`) and **HFM-IN-602** (BOL `NS-5002-B` ↔ `PGE-OUT-5002`); mill run **MILL-2207** / **FEED-2207** from HFM-IN-602. **PGE-OUT-5004** is South House 14 (`BIN-14`), not BIN-12.

---

### NQ-03. Grain received 2025-09-03 09:00 through 12:00 (offset −05:00)

**Received in window:**

- **09:20** `ER-7721` / **WB-390**, 23 850 kg hard red wheat, Lane 1, assigned `B-12`, owner at intake Willow Bend Farms.
- **11:05** `ER-7729` / **EF-18**, 17 900 kg hard red wheat, Lane 1, assigned `B-12`, owner at intake East Fork Co-op.

**Then:** both were put into **BIN-12** (`BM-002` 09:47; `BM-003` 11:28), commingled with prior **DR-44**. Same afternoon, **TR-102** moved **title** of WB-390 to **GrainLink Merchants** (holder still Prairie Gate). Later BIN-12 loadouts: `PGE-OUT-5001` (09-04 09:40), `PGE-OUT-5002` (hopper names WB-390/EF-18), `PGE-OUT-5003` (unallocated). No other receipts fall in that three-hour window.

---

### NQ-04. Processor receipts with complete upstream provenance to identified inbound load(s)

**None** of the three HFM-N receipts is complete.

- **HFM-IN-601:** linked to `PGE-OUT-5001` via BOL `RL-5001-A`, but BIN-12 was already mixed and there is no hopper allocation (and no `BM-*` row) to inbound tickets. Ownership treats **DR-44** as the lot (`TR-103`/`TR-106`); that is not a recorded physical allocation after commingling.
- **HFM-IN-602:** linked to `PGE-OUT-5002` via BOL `NS-5002-B`; hopper identifies **WB-390 and EF-18 together**, not complete ticket-level provenance, and DR-44 commingling is unresolved.
- **HFM-IN-604:** linked to `PGE-OUT-5004` via BOL `RL-5004-Q`; BIN-14 held **MCR-118** and **S-52**; notes and `BM-009` (`no individual ticket`) say the desk did not record which delivery supplied the truck.

There is **no** processor receipt in the extract for **PGE-OUT-5003**.

---

### NQ-05. Unresolved chains and the unresolved part of each

1. **PGE-OUT-5003** (`NS-8910`, 12 000 kg from BIN-12): origin unresolved — hopper has **no ticket**; `N3 / EF-18?` is **not** a validated scale ticket. Destination: **no mill receiving slip** in the extracts (consignee code `HFM-E` is not a slip).
2. **PGE-OUT-5004 / HFM-IN-604:** BIN-14 blend of **MCR-118** and **S-52** without individual allocation (`BM-009`, operating notes).
3. **PGE-OUT-5001 / HFM-IN-601:** legal chain on **DR-44**, but physical mix in BIN-12 before loadout; missing hopper/bin-move allocation.
4. **PGE-OUT-5002 / HFM-IN-602:** inbound pair named as a **blend** only; no shares; DR-44 not resolved in or out.
5. **MCR-118 / “M. Creek”:** grower identity unresolved — **TR-107** duplicate claims (Meadow Creek Farms vs Meadow Creek Grain), no account key.
6. **SMP-UNLISTED** (`N3 / EF-18?`): lab row with **source ticket not recorded**; must not close a chain to EF-18.

---

### NQ-06. Missing linkage for complete provenance of PGE-OUT-5003

**Specific origin break:** `BM-006` (`BIN-12` → `LOAD-PIT-3`, 12 000 kg, `OUT-5003`) has **`no ticket on hopper sheet`**. The packet/manifest mark **`N3 / EF-18?`** is a handwritten guess; notes and `NS-8910.route_note` state **N3 is a route code** and the note is **not a confirmed scale ticket**. That is the missing inbound identity link.

**Separate downstream gap (does not fix origin):** carrier left with `NS-8910`, but **no HFM receiving slip** is in the supplied extracts.

---

### NQ-07. Ownership and custody of WB-390 at 2025-09-04 13:10:00−05:00

**Owner:** **GrainLink Merchants**. `TR-102` title change on `WB-390` is effective 2025-09-03 15:00 through 2025-09-05 10:50; `owner_after` is GrainLink.

**Custody:** do not treat as a single holder.

- Lot-level `TR-102` still lists **holder Prairie Gate Elevator** until 2025-09-05 10:50.
- `TR-104` (scope **OUT-5002**, not the whole WB-390 lot) from **13:05** lists holder **Northstar Bulk Transport**.
- Physically at 13:10: `BM-004` (13:02) had moved 26 000 kg labeled `WB-390 / EF-18` into **LOAD-PIT-2**; `BM-005` onto the truck is **13:14**; `LD-19` is **13:15**. So that draw was still in the elevator load pit, not yet on `TRUCK-NS204`.
- WB-390 intake was 23 850 kg vs a 26 000 kg blended draw, so **any remainder in BIN-12 is not shown as transferred** with OUT-5002.

---

### NQ-08. Downstream material affected by SMP-602B

**SMP-602B** is a **combined truck sample** on receiving slip **HFM-IN-602**, `local_lot` `WB390 / EF18`, aflatoxin below limit (LAB-4419).

**Affected, as far as the records go:** mill receipt **HFM-IN-602** (silo **S-5**), truck **PGE-OUT-5002** / BOL **NS-5002-B**, and mill run **MILL-2207** → output batch **FEED-2207** (grower feed), whose `input_receipts` are only `HFM-IN-602`. The sample does **not** isolate WB-390 from EF-18.

---

### NQ-09. Apparent identity matches that should not be committed

- **`N3 / EF-18?` ≠ inbound ticket EF-18** (manifest route note, operating notes, `SMP-UNLISTED` comment). `N3` is a route code, not a source ticket.
- **`M. Creek` / MCR-118 ≠ a chosen legal grower.** `TR-107`: Meadow Creek Farms and Meadow Creek Grain both claim; no account key.
- **Carrier consignee `HFM-E` ≠ an HFM-E receiving slip.** Notes: a consignee code is not a mill receiving slip.
- **SMP-604Q `MC-118` / “South House 14 cargo” ≠ MCR-118 alone** (BIN-14 also held S-52; no individual ticket on `OUT-5004`).
- **SMP-602B `WB390 / EF18` ≠ a single inbound lot** (combined truck sample).

BOL-backed pairs (`RL-5001-A`, `NS-5002-B`, `RL-5004-Q`) are the joins that *are* recorded; the list above is what must stay uncommitted.

---

### NQ-10. Processor record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** **No.** The HFM-North `receiving_log` has `HFM-IN-601`, `HFM-IN-602`, `HFM-IN-604` only. Notes state that log is **complete for 2025-09-05 through 2025-09-07**. `PGE-OUT-5003` departed 2025-09-05 07:24 (`NS-8910`) and is not among those slips. That completeness statement supports a **justified negative for HFM-N**.

**HFM-E:** **Cannot** say HFM-E has no receiving record. Notes: **no conclusion about other HFM sites follows from absence**; the North extract is not an East-mill complete set. Manifest consignee is **HFM-E**, which only shows intended consignee, not a dock slip. Absence of an HFM-E row here is **missing evidence**, not a proof that HFM-E never created one.
