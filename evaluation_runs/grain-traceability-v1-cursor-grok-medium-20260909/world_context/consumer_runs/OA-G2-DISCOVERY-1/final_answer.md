I'll start by reading the instruction file and the questions, then work through them with the local files.I'll inspect the SQLite world schema and dump the tables that support the traceability questions.## NQ-01. Inbound loads for PGE-OUT-5002

**Established:** Scale tickets **WB-390** (receipt ER-7721) and **EF-18** (ER-7729) are named on the hopper move that feeds this dispatch. Individual kilogram split is **not** established.

**Facts:** `loadout_from_bin` PGE-OUT-5002 ← BIN-12 / LD-19 (26 000 kg). `storage_move` BM-004 (2025-09-04 13:02) BIN-12 → LOAD-PIT-2, material note `WB-390 / EF-18`. `hopper_names_ticket` BM-004/OUT-5002 names both tickets. `ticket_into_bin` put WB-390 (BM-002) and EF-18 (BM-003) into BIN-12. `established_shipment` continues the truck as NS-8848 → HFM-IN-602 → FEED-2207.

**Unresolved:** `out_5002_quantity_split` — blended 26 000 kg is not allocated to tickets.

**Not established:** **DR-44** also occupied BIN-12 (`ticket_into_bin` BM-001) but is not named on BM-004. Do not treat DR-44 as a contributor.

---

## NQ-02. Downstream of BIN-12, and source allocation

**Shipments that loaded from BIN-12** (`loadout_from_bin`): **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20). Occupants of BIN-12: DR-44, WB-390, EF-18 (`ticket_into_bin`). PGE-OUT-5004 is from BIN-14, not BIN-12.

**Individual source allocation:** **None** of those three dispatches have it.

| Dispatch | What is established | Allocation |
|---|---|---|
| PGE-OUT-5001 | From BIN-12 after all three tickets were in the house | Unresolved `out_5001_ticket_composition` |
| PGE-OUT-5002 | Hopper **names** WB-390 and EF-18 | Unresolved `out_5002_quantity_split` |
| PGE-OUT-5003 | From BIN-12; hopper “no ticket on hopper sheet” | Unresolved `out_5003_material_identity` |

---

## NQ-03. Grain received 2025-09-03 09:00–12:00 −05:00

**Received in window** (`intake_receipt`):

- **WB-390** / ER-7721 at 09:20 — 23 850 kg hard red wheat, Willow Bend Farms, Lane 1, assigned B-12 (= BIN-12).
- **EF-18** / ER-7729 at 11:05 — 17 900 kg, East Fork Co-op, Lane 1, B-12.

**Then established:** BM-002 09:47 INTAKE-1 → BIN-12 (WB-390); BM-003 11:28 INTAKE-1 → BIN-12 (EF-18). Title of WB-390: TR-102 at 15:00 same day Willow Bend → **GrainLink Merchants**, holder Prairie Gate. No `ownership_event` for EF-18 after intake.

**Later (outside the window, same material):** Both tickets are named on BM-004 / PGE-OUT-5002 (blend, no split). They were already in BIN-12 when PGE-OUT-5001 loaded 39 000 kg (ticket mix unresolved) and when PGE-OUT-5003 loaded 12 000 kg (identity unresolved). PGE-OUT-5002 is received at HFM-N as HFM-IN-602 and milled to **FEED-2207**.

---

## NQ-04. Processor receipts with complete upstream provenance

Mill receipts in the world: **HFM-IN-601**, **HFM-IN-602**, **HFM-IN-604** (all HFM-N).

**None** have complete provenance back to allocated inbound load(s).

- **HFM-IN-601** ← RL-8841 ← PGE-OUT-5001 ← BIN-12: chain to mill/FEED-2206 is established; inbound tickets are **not** identified (`out_5001_ticket_composition`).
- **HFM-IN-602** ← NS-8848 ← PGE-OUT-5002: inbound loads **named** (WB-390, EF-18) but **not** allocated (`out_5002_quantity_split`). Closest to identified sources; still incomplete.
- **HFM-IN-604** ← RL-9127 ← PGE-OUT-5004 ← BIN-14: tickets MCR-118 and S-52 unallocated (`out_5004_ticket_composition`); no mill run (`established_shipment.output_batch` empty; completeness gap).

---

## NQ-05. Unresolved chains

From `purpose_requirement_failure` and `established_shipment` completeness (INCOMPLETE):

1. **MCR-118 / m_creek_account** — grower “M. Creek” is not keyed to Meadow Creek Farms vs Meadow Creek Grain.
2. **PGE-OUT-5001** — which of DR-44 / WB-390 / EF-18 (BIN-12) supplied the truck.
3. **PGE-OUT-5002** — named WB-390 + EF-18; 26 000 kg not split.
4. **PGE-OUT-5003 identity** — no hopper ticket; cargo mark `N3 / EF-18?` is not a source ticket.
5. **PGE-OUT-5003 mill receipt** — manifest NS-8910, no mill slip; consignee HFM-E.
6. **PGE-OUT-5004** — BIN-14 held MCR-118 and S-52; no split.
7. **SMP-UNLISTED** — source ticket not recorded; route-packet lot is not a ticket.
8. **ownership_records.csv / unrecorded_ownership** — recorded events only; unrecorded agreements not ruled out.
9. **HFM-IN-604** — mill receipt exists; **no mill run** in `mill_process`.

---

## NQ-06. Missing linkage for PGE-OUT-5003

Two recorded gaps, both required for complete provenance:

1. **Material identity:** BM-006 “no ticket on hopper sheet”; manifest cargo_mark `N3 / EF-18?` is not a validated ticket (N3 is a route code elsewhere). Requirement `out_5003_material_identity`.
2. **Processor receipt:** `outbound_same_movement` to NS-8910 exists (vehicle NST-219 + 12 000 kg); **no** `inbound_same_movement` / `mill_receipt` row. Consignee **HFM-E**. Requirement `out_5003_mill_receipt`. Completeness: “PGE-OUT-5003 has a manifest and no mill slip in the extracts”.

---

## NQ-07. WB-390 at 2025-09-04 13:10:00−05:00 — owner vs custody

**Owner (established):** **GrainLink Merchants** — TR-102 title_change on scope WB-390, 2025-09-03 15:00 through 2025-09-05 10:50.

**Custody (not unique across scopes):**

- Ticket scope WB-390, TR-102 still lists **holder Prairie Gate Elevator** until 10:50 on 09-05.
- Dispatch scope OUT-5002, TR-104 from **13:05** lists **holder Northstar Bulk Transport**, owner GrainLink (dispatch handoff NS-8848).

**Physical location at 13:10:** After BM-004 (13:02) in **LOAD-PIT-2**; not yet BM-005 / truck NST-204 (13:14) or loadout LD-19 (13:15). That pit move is a **WB-390 / EF-18 blend** without quantity split.

Do not collapse TR-102 and TR-104. Unrecorded ownership is not ruled out (`unrecorded_ownership`).

---

## NQ-08. Downstream of SMP-602B

**Sample:** SMP-602B, 2025-09-05 13:10, lot `WB390 / EF18`, hint **HFM-IN-602**, aflatoxin below limit, “combined truck sample”.

**Affected downstream (established):** mill receipt **HFM-IN-602** (silo S-5) and mill output **FEED-2207** (MILL-2207, input HFM-IN-602, grower feed, start 15:10). Also the PGE-OUT-5002 / NS-8848 truck that that slip is linked to.

**Not established:** attribution to WB-390 vs EF-18 alone (`out_5002_quantity_split`). Those tickets are **upstream** sources of the combined sample, not separate downstream lots.

---

## NQ-09. Apparent matches that must not be treated as established

Do **not** commit:

1. **M. Creek** = Meadow Creek Farms **or** Meadow Creek Grain (`m_creek_account`; TR-107 party_claim, empty `owner_after`).
2. Cargo / lab lot **`N3 / EF-18?`** = ticket **EF-18** (`out_5003_material_identity`, `smp_unlisted_source_ticket`; N3 is a route code, not a ticket).
3. **SMP-UNLISTED** source ticket (explicitly unrecorded).
4. **SMP-604Q** lot `MC-118` as the **sole** cargo of South House 14 / PGE-OUT-5004 (BIN-14 also held S-52; `out_5004_ticket_composition`). Alias `MC-118` → `MCR-118` **is** in `identifier_alias`; that spelling match is not a composition claim.

Documented aliases that **are** established include DR44→DR-44, WB390→WB-390, EF18→EF-18, B-12/North House 12→BIN-12, PG-OUT-5002/OUT-5002→PGE-OUT-5002, etc.

---

## NQ-10. Processor record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** **No** mill receipt is linked to PGE-OUT-5003. `mill_receipt` is only HFM-IN-601/602/604; `inbound_same_movement` has RL-8841, NS-8848, RL-9127 — not NS-8910. Manifest consignee is **HFM-E**, not HFM-N. `extract_coverage` claims the HFM receiving log is **complete for HFM-N** in 2025-09-05/07 and draws **no conclusion about other HFM sites**. That supports a **justified negative for HFM-N** in this window: there is no North receiving slip for this truck.

**HFM-E:** **Cannot** justify “HFM-E has no such record.” Absence in the North extract is not evidence about East (`out_5003_mill_receipt`: “North-log completeness does not speak to East”). That is a missing assertion, not a justified negative.
