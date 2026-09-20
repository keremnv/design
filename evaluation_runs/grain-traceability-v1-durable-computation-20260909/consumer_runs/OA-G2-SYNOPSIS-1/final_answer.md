# Grain traceability held-out answers

World: `v0` revision 95. `application/catalog.json` is not present; answers are grounded only in workspace World relations. Unresolved purpose failures are preserved rather than inferred.

---

## EVAL-SRC-001

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5002

### Established
- **Contributing inbound material identities:** WB-390 and EF-18 (hopper work order OUT-5002 / move BM-004 names both tickets; both were received into BIN-12).
- **Source location:** Prairie Gate Elevator, North House 12 (BIN-12 / B-12). Loadout LD-19 (26000 kg) and carrier manifest NS-8848 pick up from PG-ELEV.

### Unresolved
- **Individual source allocation:** unresolved. Hopper names WB-390 and EF-18 together; the loadout does not allocate the blended 26000 kg to individual tickets (`out_5002_quantity_split`).
- DR-44 is not named on this hopper sheet and is not established as a contributor to PGE-OUT-5002.

---

## EVAL-SRC-002

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5003

### Established
- **Source location:** Prairie Gate Elevator, North House 12 (BIN-12). Loadout LD-20 (12000 kg, truck NST-219); carrier manifest NS-8910 is the same departure (vehicle tag and loaded weight). Consignee recorded as HFM-E (Hearthland Feed Mill - East).

### Not established
- **Inbound material identity:** none validated. Hopper BM-006 records “no ticket on hopper sheet”. Cargo mark `N3 / EF-18?` is not a validated source ticket (`out_5003_material_identity`; N3 is a route code elsewhere).

### Unresolved / missing linkage
- No established ticket-to-dispatch allocation.
- No HFM receiving slip in the supplied extracts; North-log completeness does not cover East (`out_5003_mill_receipt`). Manifest exists; mill slip does not.

---

## EVAL-SRC-003

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5004

### Established
- **Contributing inbound material identities (house-level):** MCR-118 and S-52. Both were received into South House 14 (BIN-14) before loadout LD-21 from that house.
- Loadout and manifest identify the truck as leaving Prairie Gate BIN-14 (PGE-OUT-5004 / RL-9127).

### Unresolved
- **Individual allocation:** not resolved. Hopper BM-009 records “no individual ticket”; the loadout desk did not record which delivery supplied which part of the 19000 kg (`out_5004_ticket_composition`).

---

## EVAL-PROV-001

- **family:** processor_receipt_provenance
- **processor_receipt:** HFM-IN-602

### Established
- **Upstream dispatch / movement:** PGE-OUT-5002 ↔ manifest NS-8848 ↔ mill receipt HFM-IN-602 (BOL NS-5002-B). Derived `established_shipment` also names this chain.
- **Inbound material identities named into that truck:** WB-390 and EF-18.
- **Downstream processing output:** mill run MILL-2207 on input HFM-IN-602 produced **FEED-2207** (grower feed).

### Unresolved
- Quantity split of the blended 26000 kg between WB-390 and EF-18 (`out_5002_quantity_split`). Attribution of HFM-IN-602 / FEED-2207 to a single receiving ticket is not established.

---

## EVAL-PROV-002

- **family:** processor_receipt_provenance
- **processor_receipt:** HFM-IN-604

### Established
- **Upstream dispatch / source status:** PGE-OUT-5004 ↔ manifest RL-9127 ↔ HFM-IN-604 (BOL RL-5004-Q). Pickup from Prairie Gate South House 14 (BIN-14). House contents before loadout were MCR-118 and S-52; individual ticket share is not allocated.
- **Identified inbound load (mill slip):** yes. HFM-IN-604 is recorded at HFM-N dock N-3 (18800 kg, silo S-7).

### Not established
- **Processing output:** none recorded. No mill run names HFM-IN-604; `established_shipment` has empty `output_batch`. Completeness gap: HFM-IN-604 has no mill run in the supplied mill_runs.

---

## EVAL-CUST-001

- **family:** custody_owner_at
- **material:** WB-390
- **timestamp:** 2025-09-04T13:10:00-05:00

### Established (material-scoped records)
- **Owner:** GrainLink Merchants.
- **Custodian / holder:** Prairie Gate Elevator.
- Basis: title_change TR-102 on scope WB-390, effective 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00 (`owner_after` GrainLink Merchants, `holder_after` Prairie Gate Elevator). The query time falls in that interval.

### Unresolved
- Custody_change TR-104 (scope OUT-5002, start 2025-09-04T13:05:00-05:00) names holder Northstar Bulk Transport, but that scope is the dispatch, not ticket WB-390. Hopper blending of WB-390 with EF-18 without a quantity split means TR-104 cannot be applied as the custodian of WB-390 as a whole.
- Ownership export records changes only; it does not guarantee an unrecorded agreement did not exist (`unrecorded_ownership`).

---

## EVAL-CUST-002

- **family:** custody_owner_at
- **material:** EF-18
- **timestamp:** 2025-09-03T12:00:00-05:00

### Established
- **Owner:** East Fork Co-op (`owner_at_intake` on receipt ER-7729 / ticket EF-18; arrived 2025-09-03T11:05:00-05:00).
- **Custodian:** Prairie Gate Elevator. After intake, BM-003 (2025-09-03T11:28:00-05:00) placed EF-18 into BIN-12; at 12:00 the ticket is in elevator storage. No later ownership or custody event for EF-18 exists before this timestamp.

### Unresolved
- No `ownership_event` row is scoped to EF-18, so title/custody is not independently confirmed in the ownership export.
- Unrecorded agreements are not ruled out (`unrecorded_ownership`).

---

## EVAL-INSP-001

- **family:** inspection_downstream_scope
- **sample:** SMP-602B

### Established
- **Downstream shipment:** PGE-OUT-5002 / manifest NS-8848.
- **Processor receipt:** HFM-IN-602 (lab `material_hint` receiving slip HFM-IN-602; combined truck sample).
- **Processed output:** FEED-2207 (MILL-2207 on HFM-IN-602).

### Unresolved
- **Attribution to an individual inbound material:** not resolved. Sample local_lot is `WB390 / EF18` (combined truck sample); same unresolved quantity split as PGE-OUT-5002.

---

## EVAL-INSP-002

- **family:** inspection_downstream_scope
- **sample:** SMP-604Q

### Established
- **Downstream shipment:** PGE-OUT-5004 / manifest RL-9127.
- **Processor receipt:** HFM-IN-604.
- Lab records material_hint “South House 14 cargo” (BIN-14), which is the established loadout house for that dispatch.

### Not established
- **Processed output:** none recorded for HFM-IN-604.

### Unresolved
- **Source attribution:** individual inbound ticket is unresolved. South House 14 held MCR-118 and S-52 without a loadout split (`out_5004_ticket_composition`). Lab `local_lot` MC-118 (alias of MCR-118) is a recorded lot label, including unvalidated labels, and is not treated as a resolved exclusive ticket.

---

## EVAL-INSP-003

- **family:** inspection_downstream_scope
- **sample:** SMP-UNLISTED

### Established
- Lab row exists: tested 2025-09-08T09:00:00-05:00, LAB-4428, local_lot `N3 / EF-18?`, material_hint “route packet note”, comment “source ticket not recorded”.

### Not established
- **Validated downstream shipment:** none.
- **Processor receipt:** none.
- **Inbound source identity:** none. The route-packet note is not treated as a ticket (`smp_unlisted_source_ticket`).

### Unresolved (preserved, not inferred)
- Similarity of `N3 / EF-18?` to PGE-OUT-5003 cargo_mark is not a validated linkage. Hopper for OUT-5003 also has no ticket. No mill slip exists for that East consignee movement. These remain unlinked.
