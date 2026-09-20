I'll start by reading the instruction file and the questions, then work through them with the files in this workspace.Answers use only `world/world.sqlite` and the declared purpose (trace grain when evidence establishes links; keep identity, ownership, and event linkage unresolved otherwise). Identifiers and relation facts are included for audit.

---

### NQ-01. Which inbound loads contributed to outbound shipment PGE-OUT-5002?

**Established contributors:** scale tickets **WB-390** (intake `ER-7721`) and **EF-18** (intake `ER-7729`).

- `hopper_names_ticket`: `BM-004` / `OUT-5002` names **WB-390** and **EF-18** (no kg split).
- `storage_move` `BM-004` (2025-09-04T13:02:00-05:00): BIN-12 → LOAD-PIT-2, note `WB-390 / EF-18`, 26000 kg, work order `OUT-5002`.
- `ticket_into_bin` / `intake_receipt`: WB-390 and EF-18 were received into BIN-12 (Willow Bend 23850 kg; East Fork 17900 kg).
- Chain onward is established: `loadout_from_bin` LD-19 from BIN-12; `outbound_same_movement` PGE-OUT-5002 ↔ NS-8848; `established_shipment` → HFM-IN-602 / FEED-2207.

**Not established:** kg from each ticket (`purpose_requirement_failure` `out_5002_quantity_split`). **DR-44** occupied BIN-12 but is not named on the OUT-5002 hopper; it is not an established contributor.

---

### NQ-02. Downstream shipments from BIN-12, and individual source allocation

**Shipments that contain material that occupied BIN-12** (`loadout_from_bin` bin BIN-12; North House 12 aliases to BIN-12):

| Dispatch | Carrier / mill continuation | Individual source allocation |
|---|---|---|
| **PGE-OUT-5001** | RL-8841 → HFM-IN-601 → FEED-2206 | **No** |
| **PGE-OUT-5002** | NS-8848 → HFM-IN-602 → FEED-2207 | **No** |
| **PGE-OUT-5003** | NS-8910; no mill slip | **No** |

BIN-12 intakes (`ticket_into_bin`): DR-44, WB-390, EF-18.

- **5001:** `out_5001_ticket_composition` — house already held DR-44, WB-390, and EF-18; loadout does not allocate tickets.
- **5002:** hopper **names** WB-390 and EF-18 (`hopper_names_ticket` = name without quantity); `out_5002_quantity_split` — 26000 kg not split.
- **5003:** `BM-006` “no ticket on hopper sheet”; `out_5003_material_identity`.

No BIN-12 outbound has individual source allocation.

---

### NQ-03. Grain received 2025-09-03 09:00:00-05:00 through 12:00:00-05:00

**In that window (established):** two Prairie Gate intakes, both hard red wheat, both moved into **BIN-12**:

1. **WB-390** / `ER-7721` arrived 09:20 Lane 1, 23850 kg, Willow Bend Farms → `BM-002` 09:47 INTAKE-1 → BIN-12.
2. **EF-18** / `ER-7729` arrived 11:05 Lane 1, 17900 kg, East Fork Co-op → `BM-003` 11:28 INTAKE-1 → BIN-12.

No loadout, lab, mill, or ownership row is timestamped inside the window.

**Later, established for those tickets:** both are named on PGE-OUT-5002 (26000 kg blend, split unresolved) → NS-8848 → HFM-IN-602 → MILL-2207 / **FEED-2207**. Title on WB-390 later that day (15:00) is GrainLink Merchants with Prairie Gate still holding (`TR-102`) — **after** the window.

**Not established:** how much of each ticket left on 5002; whether either ticket is in PGE-OUT-5001 or PGE-OUT-5003.

---

### NQ-04. Processor receipts with complete upstream provenance to identified inbound load(s)

Mill receipts in the representation (`mill_receipt`, all `HFM-N`): **HFM-IN-601**, **HFM-IN-602**, **HFM-IN-604**.

**Only HFM-IN-602** has provenance to **identified inbound loads**: NS-5002-B = NS-8848 BOL (`inbound_same_movement`) → PGE-OUT-5002 → hopper names **WB-390** and **EF-18**. Completeness of the **kg split** is still unresolved (`out_5002_quantity_split`).

**Not complete to identified inbound loads:**

- **HFM-IN-601** ← PGE-OUT-5001 from BIN-12 with no ticket names on loadout (`out_5001_ticket_composition`).
- **HFM-IN-604** ← PGE-OUT-5004 from BIN-14; hopper `BM-009` “no individual ticket”; house held MCR-118 and S-52 (`out_5004_ticket_composition`). Also no mill run (`established_shipment.output_batch` empty; completeness gap).

---

### NQ-05. Unresolved traceability chains (and the unresolved part)

From `purpose_requirement_failure` (8 rows) plus `_world_completeness` on `established_shipment`:

| Identity | Unresolved part |
|---|---|
| **MCR-118** (`m_creek_account`) | Grower/account: intake “M. Creek” vs claims Meadow Creek Farms and Meadow Creek Grain; no account key. |
| **PGE-OUT-5001** | Ticket composition from BIN-12 (DR-44 / WB-390 / EF-18). |
| **PGE-OUT-5002** | Quantity split of named WB-390 vs EF-18 (26000 kg). |
| **PGE-OUT-5003** | Material identity (no hopper ticket; cargo mark `N3 / EF-18?` not a validated ticket) **and** no mill receiving slip. |
| **PGE-OUT-5004** | Ticket composition from BIN-14 (MCR-118 vs S-52). |
| **HFM-IN-604** | No mill run in `mill_process` (completeness known gap). |
| **SMP-UNLISTED** | Source ticket not recorded; route-packet `N3 / EF-18?` not treated as a ticket. |
| **ownership_records.csv** (`unrecorded_ownership`) | Export is recorded changes only; does not prove an unrecorded agreement did not exist. |

`established_shipment` over `outbound_same_movement` is **INCOMPLETE**: PGE-OUT-5003 has a manifest and no mill slip; HFM-IN-604 has no mill run.

---

### NQ-06. Missing linkage for complete provenance of PGE-OUT-5003

**Specific missing mill link:** no `inbound_same_movement` / `mill_receipt` for manifest **NS-8910** (BOL NS-5003-C). Completeness: “PGE-OUT-5003 has a manifest and no mill slip in the extracts.” Consignee is **HFM-E**; North-log completeness does not cover East (`out_5003_mill_receipt`, `extract_coverage`).

**Also blocking complete provenance:** `out_5003_material_identity` — `BM-006` “no ticket on hopper sheet”; cargo mark `N3 / EF-18?` is not a validated source ticket (N3 is a route code elsewhere). `outbound_same_movement` exists only on vehicle tag + loaded weight, not cargo_mark = dispatch id.

---

### NQ-07. At 2025-09-04 13:10:00-05:00, owner and custody of WB-390 material

**Owner (established on ticket scope):** **GrainLink Merchants** — `TR-102` title_change on `WB-390`, effective 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00 (`owner_after` GrainLink Merchants). Intake owner Willow Bend is already superseded.

**Custody/holder is not a single established fact at that instant:**

- Ticket `TR-102` still has `holder_after` **Prairie Gate Elevator** until mill dock 2025-09-05T10:50.
- Dispatch `TR-104` on **OUT-5002** from **13:05** has `holder_after` **Northstar Bulk Transport**, `owner_after` GrainLink (`dispatch handoff NS-8848`). Hopper names that move as WB-390 / EF-18.
- Physical: `BM-004` at **13:02** already placed the named blend in **LOAD-PIT-2**; truck load `BM-005` is **13:14** and spout `LD-19` is **13:15** — both **after** 13:10.

**Not established:** how many kg of WB-390 are in that 26000 kg blend; that the overlapping TR-102 vs TR-104 holder fields are the same custody fact; any unrecorded agreement (`unrecorded_ownership`).

---

### NQ-08. Downstream material affected by SMP-602B

**SMP-602B** (2025-09-05T13:10:00-05:00, LAB-4419): aflatoxin **below limit** (ppb); `material_hint` receiving slip **HFM-IN-602**; `local_lot` `WB390 / EF18`; comment “combined truck sample”.

**Established affected material:** mill receipt **HFM-IN-602** (silo S-5, 25500 kg) and mill output **FEED-2207** (`MILL-2207` starts 15:10 the same day, input HFM-IN-602). That receipt is the PGE-OUT-5002 / NS-8848 truck whose hopper names WB-390 and EF-18.

**Not established:** a kg split of the sample (or the truck) to WB-390 vs EF-18 alone.

---

### NQ-09. Apparent identity matches that should not be committed

Do **not** treat these as established identities:

1. **`N3 / EF-18?`** (manifest NS-8910 cargo_mark; SMP-UNLISTED `local_lot`) as ticket **EF-18** or as a source ticket — explicit: not a validated ticket; N3 is a route code; lab “source ticket not recorded.”
2. **M. Creek** = **Meadow Creek Farms** or **Meadow Creek Grain** for MCR-118 — duplicate claims, no account key (`TR-107` `party_claim`; `m_creek_account`).
3. **BIN occupancy ⇒ load composition** — tickets in BIN-12/BIN-14 are not established as the makeup of PGE-OUT-5001 / 5003 / 5004.
4. **Hearthland Feed Mill** on `TR-105`/`TR-106` as **HFM-N** vs **HFM-E** — ownership uses an undifferentiated mill name; sites are distinct in `identifier_alias`.

**Established aliases (may be committed):** DR44/DR-44, WB390/WB-390, EF18/EF-18, MC-118/MCR-118; North House 12/B-12/BIN-12; PG-OUT-5001/5002/5004 and OUT-5002/5003/5004 → PGE-OUT-*; vehicles TRUCK-NS204/NST-204, TRUCK-RL091/RLT-091. There is **no** `PG-OUT-5003` alias (unlike 5001/5002/5004).

---

### NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** There is **no** processor receiving record for PGE-OUT-5003. `mill_receipt` is only HFM-IN-601/602/604 (all `mill_code` HFM-N), none matching NS-8910 / NS-5003-C. Manifest consignee is **HFM-E**, not HFM-N. `extract_coverage` claims the HFM receiving log is **complete for HFM-North** in 2025-09-05/2025-09-07. That supports a **justified negative** for HFM-N in that window (absence is not mere missing extract coverage for North).

**HFM-E:** The same coverage says **“no conclusion about other HFM sites.”** Completeness basis: “HFM-East receipts are outside the North log.” `out_5003_mill_receipt`: no slip in the supplied extracts, and North-log completeness **does not speak to East**. That is **absent assertion**, not a justified claim that HFM-E has no receiving record.
