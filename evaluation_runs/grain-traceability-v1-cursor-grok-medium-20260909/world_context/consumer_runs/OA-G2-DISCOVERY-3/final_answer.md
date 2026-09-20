I'll read the instruction and question files first, then work through each question using only what's in this workspace.The world is in SQLite. I'll inspect the schema and dump the relations needed for the traceability questions.Answers use `world/world.sqlite` plus `world/world.purpose.json`. Established links are treated as facts; `UNRESOLVED` / `purpose_requirement_failure` rows are not filled in by inference.

---

### NQ-01. Inbound loads for PGE-OUT-5002

**Established contributing inbound loads:** scale tickets **WB-390** (receipt **ER-7721**) and **EF-18** (receipt **ER-7729**).

**Facts:** `loadout_from_bin` puts PGE-OUT-5002 on **BIN-12** (LD-19). `hopper_names_ticket` on move **BM-004** / work order OUT-5002 names **WB-390** and **EF-18**. Those tickets are `intake_receipt` / `ticket_into_bin` into BIN-12 (BM-002, BM-003). `established_shipment` continues the truck to **HFM-IN-602** / **FEED-2207**; that does not add further inbound tickets.

**Not established:** kilogram split of the 26 000 kg blend (`out_5002_quantity_split`). **DR-44** was already in BIN-12 but is **not** named on BM-004; its contribution to this truck is not established.

---

### NQ-02. Downstream shipments from BIN-12; source allocation

**Shipments that left BIN-12:** **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20) — all in `loadout_from_bin` with bin **BIN-12** (aliases: North House 12, B-12).

**Individual source allocation:** **none** of those three.

- **5001:** `out_5001_ticket_composition` — BIN-12 already held DR-44, WB-390, and EF-18; loadout does not allocate.
- **5002:** tickets **named** (WB-390, EF-18) but **not allocated** (`out_5002_quantity_split`).
- **5003:** hopper BM-006 “no ticket on hopper sheet”; `out_5003_material_identity`.

PGE-OUT-5004 is from **BIN-14**, not BIN-12.

---

### NQ-03. Grain received 2025-09-03 09:00–12:00-05:00

**Received in window:** **WB-390** (ER-7721, 09:20, 23 850 kg, Willow Bend Farms) and **EF-18** (ER-7729, 11:05, 17 900 kg, East Fork Co-op), both assigned B-12.

**Then established:** BM-002 (09:47) and BM-003 (11:28) put both tickets into **BIN-12**. Hopper **BM-004** (2025-09-04 13:02) names both on the **PGE-OUT-5002** 26 000 kg pull. That dispatch is the same movement as manifest **NS-8848**, mill slip **HFM-IN-602**, mill run **MILL-2207** → **FEED-2207**. Lab **SMP-602B** is a combined-truck aflatoxin sample on HFM-IN-602.

**Not established:** how much of each ticket is on 5002; whether any of this grain is on **PGE-OUT-5001** or **PGE-OUT-5003** (bin composition / identity unresolved). Title on WB-390 later moves to GrainLink (TR-102); EF-18 has no later `ownership_event`.

---

### NQ-04. Processor receipts with complete upstream provenance to inbound load(s)

**Processor receipts in world:** HFM-IN-601, HFM-IN-602, HFM-IN-604 (all `mill_code` HFM-N).

**None** have complete ticket-level upstream provenance.

| Receipt | Upstream chain | Gap |
|---|---|---|
| **HFM-IN-601** | RL-8841 ← PGE-OUT-5001 ← BIN-12 | contributing tickets **not identified** |
| **HFM-IN-602** | NS-8848 ← PGE-OUT-5002; hopper **names** WB-390 and EF-18 | identity of contributing **loads** is recorded; **quantity split is not** |
| **HFM-IN-604** | RL-9127 ← PGE-OUT-5004 ← BIN-14 | MCR-118 vs S-52 **not allocated** (`out_5004_ticket_composition`) |

HFM-IN-604 also has **no** `mill_process` row (completeness note); that is downstream of the slip, not an inbound-load gap.

---

### NQ-05. Unresolved chains and which part is unresolved

From `purpose_requirement_failure` / purpose `UNRESOLVED`:

1. **MCR-118 / m_creek_account** — grower string “M. Creek” vs competing claims Meadow Creek Farms and Meadow Creek Grain; no account key.
2. **PGE-OUT-5001 / out_5001_ticket_composition** — which BIN-12 tickets (DR-44, WB-390, EF-18) supplied the truck.
3. **PGE-OUT-5002 / out_5002_quantity_split** — 26 000 kg named WB-390 and EF-18 without per-ticket weights.
4. **PGE-OUT-5003 / out_5003_material_identity** — no hopper ticket; cargo mark `N3 / EF-18?` is not a validated ticket (N3 used as a route code elsewhere).
5. **PGE-OUT-5003 / out_5003_mill_receipt** — carrier manifest **NS-8910** exists; **no** mill slip in extracts; consignee **HFM-E**.
6. **PGE-OUT-5004 / out_5004_ticket_composition** — BIN-14 held MCR-118 and S-52; loadout does not split.
7. **SMP-UNLISTED / smp_unlisted_source_ticket** — lab says source ticket not recorded; route-packet note is not a ticket.
8. **ownership export / unrecorded_ownership** — recorded changes only; does not prove no unrecorded agreement.

`established_shipment` completeness also flags: PGE-OUT-5003 has no mill slip; **HFM-IN-604** has no mill run in `mill_process`.

---

### NQ-06. Missing linkage for complete provenance of PGE-OUT-5003

Two recorded gaps, both required for a full chain:

1. **Source identity:** BM-006 has no ticket; manifest cargo_mark `N3 / EF-18?` is not treated as a ticket (`out_5003_material_identity` on `manifest_event`).
2. **Processor inbound link:** no `inbound_same_movement` for **NS-8910**; no `mill_receipt` for this dispatch (`out_5003_mill_receipt`). Consignee is **HFM-E**.

Outbound elevator↔manifest **is** linked (`outbound_same_movement`: same vehicle **NST-219** and 12 000 kg; cargo_mark is not the dispatch id).

---

### NQ-07. Owner and custody of WB-390 at 2025-09-04 13:10:00-05:00

**Recorded owner of ticket WB-390:** **GrainLink Merchants** (TR-102 title change, 2025-09-03 15:00 through 2025-09-05 10:50).

**Custody is not a single lot-wide fact at this timestamp:**

- TR-102 still lists **holder_after = Prairie Gate Elevator** for scope **WB-390**.
- TR-104 (scope **OUT-5002**, start **13:05**) lists **holder_after = Northstar Bulk Transport**, **owner_after = GrainLink Merchants**.
- Physically, BM-004 at **13:02** moved a **WB-390 / EF-18** named 26 000 kg to **LOAD-PIT-2**; truck fill BM-005 is **13:14**. Loadout LD-19 is **13:15**.

So at 13:10: owner of the ticket is GrainLink; the OUT-5002 load’s recorded holder is Northstar; residual WB-390 still in BIN-12 is **not** quantity-established. `unrecorded_ownership` still applies.

---

### NQ-08. Downstream material affected by SMP-602B

**SMP-602B** (`lab_test`): aflatoxin **below limit**; `material_hint` **HFM-IN-602**; `local_lot` WB390 / EF18; comment “combined truck sample”.

**Affected downstream of that slip:** mill input **HFM-IN-602** (silo S-5) and mill output **FEED-2207** (MILL-2207, grower feed). Same truck as **PGE-OUT-5002** / **NS-8848**.

Named source tickets WB-390 / EF-18 are the sampled blend **upstream** of the mill slip; no further product after FEED-2207 is recorded.

---

### NQ-09. Apparent identity matches that should not be committed

Do **not** treat as established:

- **`N3 / EF-18?`** (manifest NS-8910 cargo_mark; SMP-UNLISTED `local_lot`) as ticket **EF-18** or as a source ticket — N3 is a route code; notes are not validated tickets.
- **“M. Creek”** as **Meadow Creek Farms** or **Meadow Creek Grain** (`m_creek_account` / TR-107 duplicate claims, empty `owner_after`).
- **SMP-604Q** `local_lot` **MC-118** as proving HFM-IN-604 / South House 14 cargo is **only** MCR-118 (spelling MC-118→MCR-118 **is** in `identifier_alias`; composition of OUT-5004 is not).

Contrast: aliases such as DR44→DR-44, WB390→WB-390, North House 12→BIN-12, PG-OUT-5002→PGE-OUT-5002 **are** in `identifier_alias` and may be used.

---

### NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** **No.** There is no `mill_receipt` (and no `inbound_same_movement`) tying PGE-OUT-5003 / NS-8910 / NS-5003-C to HFM-N. The HFM receiving-log coverage claim is **complete for HFM-N** in 2025-09-05/2025-09-07, and the three North slips are 601/602/604. That supports a **justified negative at HFM-N**.

**HFM-E:** Consignee on NS-8910 **is** HFM-E. Absence of an East slip in the workspace is **missing evidence**, not a proof that East never received it. Coverage explicitly: “no conclusion about other HFM sites”; `out_5003_mill_receipt`: “North-log completeness does not speak to East.” **Cannot** justify “HFM-E has no such record.”
