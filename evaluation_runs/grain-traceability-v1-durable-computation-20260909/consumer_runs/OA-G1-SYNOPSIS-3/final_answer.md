# Grain traceability — held-out answers

World: `world/world.sqlite` (revision 242). No `application/catalog.json` was present; answers use World relations and explicit unresolved requirements only.

---

## EVAL-SRC-001

**Family:** shipment_source_status  
**Dispatch:** PGE-OUT-5002

### Established

- **Source location:** Prairie Gate Elevator, **North House 12** (`bin:north-house-12`). Loadout `LD-19` and hopper move `BM-004` both name this bin for work order `OUT-5002`.
- **Contributing inbound material identities:** scale tickets **WB-390** and **EF-18**. Move `BM-004` material note is `WB-390 / EF-18`; `ticket_named_on_move` records both tickets on that move. Cargo then goes `BM-005` pit → truck `NST-204`. Carrier manifest `NS-8848` / BOL `NS-5002-B` is the same movement.
- **DR-44 is not established as contributing** to this dispatch. It was in North House 12 earlier, but this hopper names only WB-390 and EF-18.

### Unresolved

- **Individual source allocation remains unresolved.** The 26,000 kg truck is a named blend of WB-390 and EF-18; no split, hopper share, or desk comment allocates kilograms to one ticket versus the other.
- Loadout vs mill weights (26,000 kg vs 25,500 kg on `HFM-IN-602`) are recorded and unexplained; they are not treated as a different movement.

---

## EVAL-SRC-002

**Family:** shipment_source_status  
**Dispatch:** PGE-OUT-5003

### Established

- **Source location:** Prairie Gate Elevator, **North House 12**. Loadout `LD-20` and move `BM-006` (work order `OUT-5003`) leave from that bin to `LOAD-PIT-3` then truck `NST-219`.
- Carrier departure is established: manifest `NS-8910`, BOL `NS-5003-C`, consignee code `HFM-E` (Hearthland Feed Mill - East), 12,000 kg.

### Unresolved

- **No inbound material identity is established.** Hopper note is `no ticket on hopper sheet`. Handwritten cargo mark `N3 / EF-18?` is **not** a validated source ticket (`physical-ticket-allocation-PGE-OUT-5003`); `N3` is a route code elsewhere.
- **No mill receiving slip** is in the extracts for this truck (`mill-receipt-absent-PGE-OUT-5003`). Consignee `HFM-E` is not a receipt. HFM-North log completeness does not support a conclusion about East mill receiving.

---

## EVAL-SRC-003

**Family:** shipment_source_status  
**Dispatch:** PGE-OUT-5004

### Established

- **Source location:** Prairie Gate Elevator, **South House 14**. Loadout `LD-21` and moves `BM-009`/`BM-010` (work order `OUT-5004`).
- **Inbound identities established as the contributing bin contents:** **MCR-118** and **S-52** (placed into South House 14 on `BM-007` and `BM-008` before loadout). Carrier movement `RL-9127` / BOL `RL-5004-Q` is the same dispatch.

### Unresolved

- **Individual allocation is not resolved** (`physical-ticket-allocation-PGE-OUT-5004`). Hopper note is `no individual ticket`. The desk did not record which delivery supplied which part of the 19,000 kg truck.

---

## EVAL-PROV-001

**Family:** processor_receipt_provenance  
**Processor receipt:** HFM-IN-602

### Established

- **Upstream dispatch:** mill intake links `HFM-IN-602` to movement **PGE-OUT-5002** (origin label `PG-OUT-5002`, bill `NS-5002-B`, dock N-1, silo S-5, HFM-North, 25,500 kg at 2025-09-05T10:50:00-05:00).
- **Inbound material identities on that dispatch:** **WB-390** and **EF-18** (named on elevator hopper `BM-004`).
- **Downstream processing output:** mill run **MILL-2207** on this receipt produced batch **FEED-2207** (`grower feed`), started 2025-09-05T15:10:00-05:00.

### Unresolved

- **Allocation among WB-390 and EF-18** on the combined truck is not resolved.
- Kilogram difference 26,000 (loadout) vs 25,500 (mill) is unexplained; movement identity remains PGE-OUT-5002.

---

## EVAL-PROV-002

**Family:** processor_receipt_provenance  
**Processor receipt:** HFM-IN-604

### Established

- **Upstream dispatch:** **PGE-OUT-5004** (origin `PG-OUT-5004`, bill `RL-5004-Q`, dock N-3, silo S-7, HFM-North, 18,800 kg at 2025-09-07T13:02:00-05:00). Bill-of-lading identity of the truck movement is established.
- **Source status:** loaded from **South House 14** after **MCR-118** and **S-52** were both placed there.
- **Identified inbound load (movement):** yes — the receipt is the same established movement as PGE-OUT-5004 / RL-5004-Q.
- **Processing output:** **none recorded.** There is no `mill_process` row with input `HFM-IN-604`.

### Unresolved

- **No single inbound scale ticket** is identified for this load (`physical-ticket-allocation-PGE-OUT-5004`).
- Grower/account identity for MCR-118 remains unresolved if that ticket is in play (`mcr-118-grower-identity`: intake `M. Creek`; commercial claims Meadow Creek Farms vs Meadow Creek Grain).
- Kilogram difference 19,000 vs 18,800 is unexplained; not a different movement.

---

## EVAL-CUST-001

**Family:** custody_owner_at  
**Material:** WB-390  
**Timestamp:** 2025-09-04T13:10:00-05:00

### Established (ticket-scoped record in force)

- **Owner:** **GrainLink Merchants** (`ownership:TR-102`, title change WB-390, effective 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00).
- **Custodian (holder on TR-102):** **Prairie Gate Elevator**.

At this instant WB-390 had been named onto OUT-5002 hopper move `BM-004` (13:02, into load pit 2) but had not yet been recorded onto truck `NST-204` (`BM-005` at 13:14; loadout `LD-19` at 13:15).

### Unresolved / not treated as a full ticket reassignment

- `ownership:TR-104` (effective 13:05) records **Northstar Bulk Transport** as holder of **movement PGE-OUT-5002**, with owner still GrainLink. That record is commercially scoped to the **movement**, not to ticket WB-390. Because OUT-5002 is an unallocated WB-390/EF-18 blend, TR-104 does **not** establish that the entire WB-390 identity had left Prairie Gate custody at 13:10.

---

## EVAL-CUST-002

**Family:** custody_owner_at  
**Material:** EF-18  
**Timestamp:** 2025-09-03T12:00:00-05:00

### Established

- **Owner:** **East Fork Co-op** (elevator intake `ticket:ef-18`, `owner_recorded` / `grower_recorded`; arrived 2025-09-03T11:05:00-05:00 into North House 12).
- **Custodian:** **Prairie Gate Elevator** (on-site in North House 12 after `BM-003` at 11:28).

### Unresolved

- There is **no** `ownership_event` scoped to EF-18. The ownership extract records changes only; absence of a later title/custody row is not proof that no other agreement existed, but no other recorded owner or holder applies at this timestamp.

---

## EVAL-INSP-001

**Family:** inspection_downstream_scope  
**Sample:** SMP-602B

### Established

- **Downstream shipment:** **PGE-OUT-5002** (lab local lot `WB390 / EF18`; material hint receiving slip **HFM-IN-602**; comment `combined truck sample`).
- **Processor receipt:** **HFM-IN-602**.
- **Processed output:** **FEED-2207** via mill run **MILL-2207**.

### Unresolved

- **Attribution to an individual inbound material is not resolved.** The sample is a combined truck sample of WB-390 and EF-18; neither ticket is isolated.

---

## EVAL-INSP-002

**Family:** inspection_downstream_scope  
**Sample:** SMP-604Q

### Established

- **Downstream shipment:** **PGE-OUT-5004** (material hint `South House 14 cargo`; mill receipt **HFM-IN-604** is that cargo’s established truck).
- **Processor receipt:** **HFM-IN-604**.
- **Processed output:** **none recorded.**

### Unresolved

- **Source attribution to one inbound delivery is unresolved** (`lab-sample-SMP-604Q-ticket`). Local lot `MC-118` / hint South House 14 cargo does not allocate the cargo to MCR-118 versus S-52 after both were placed in BIN-14.

---

## EVAL-INSP-003

**Family:** inspection_downstream_scope  
**Sample:** SMP-UNLISTED

### Established

- A lab row exists (LAB-4428, protein 12.5%, tested 2025-09-08T09:00:00-05:00) with local lot `N3 / EF-18?` and material hint `route packet note`.

### Unresolved (no validated chain)

- **No validated inbound source identity** (`lab-sample-SMP-UNLISTED-source-ticket`). Source ticket not recorded; route packet note is not a validated source ticket.
- **No validated downstream shipment.** The string `N3 / EF-18?` matches the unvalidated cargo mark on PGE-OUT-5003; that mark is explicitly not a confirmed scale ticket, so the shipment link is not established.
- **No processor receipt** is established for this sample (and PGE-OUT-5003 itself has no mill intake in the extracts).

Preserve the unvalidated `N3 / EF-18?` note as unresolved linkage only.
