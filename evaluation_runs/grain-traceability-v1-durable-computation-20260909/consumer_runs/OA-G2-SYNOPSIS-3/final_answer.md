# Evaluation answer set

Experiment: grain-traceability-v1-durable-computation-20260909  
World: v0 revision 95 (`world.sqlite`)  
Note: `application/catalog.json` was not present in the workspace. Answers are taken from World relations, purpose unresolved requirements, and the `established_shipment` derivation. Unsupported or ambiguous links are left unresolved.

---

## EVAL-SRC-001

**family:** shipment_source_status  
**dispatch:** PGE-OUT-5002

**Established contributing inbound material identities:** WB-390 and EF-18.  
Hopper move BM-004 / work order OUT-5002 names both tickets (`hopper_names_ticket`; `storage_move` material note `WB-390 / EF-18`).

**Established source location:** BIN-12 (North House 12 / B-12) at Prairie Gate Elevator.  
`loadout_from_bin` and `loadout_event` LD-19 record the spout from North House 12; aliases map those labels to BIN-12.

**Individual source allocation:** unresolved.  
Requirement `out_5002_quantity_split`: the hopper names WB-390 and EF-18 together; the 26000 kg loadout is not allocated to individual tickets.

**Not treated as contributing for this dispatch:** DR-44 remains in BIN-12 history but is not named on the OUT-5002 hopper note.

---

## EVAL-SRC-002

**family:** shipment_source_status  
**dispatch:** PGE-OUT-5003

**Established source location:** BIN-12 (North House 12) at Prairie Gate Elevator (`loadout_from_bin`, `loadout_event` LD-20, `storage_move` BM-006).

**Established inbound material identity:** none.

**Unresolved source linkage:**
- Hopper sheet records `no ticket on hopper sheet` (BM-006).
- Requirement `out_5003_material_identity`: cargo mark `N3 / EF-18?` is not a validated source ticket; N3 is a route code elsewhere.
- Requirement `out_5003_mill_receipt`: carrier manifest NS-8910 exists (`outbound_same_movement`), but no mill slip is in the extracts; consignee is HFM-E, and HFM-North completeness does not cover East. No row in `inbound_same_movement` or `established_shipment` for this dispatch.

---

## EVAL-SRC-003

**family:** shipment_source_status  
**dispatch:** PGE-OUT-5004

**Established contributing inbound material identities:** MCR-118 and S-52.  
Both tickets are recorded into BIN-14 (`ticket_into_bin` BM-007, BM-008) before loadout LD-21 from South House 14 / BIN-14.

**Individual allocation:** unresolved.  
Requirement `out_5004_ticket_composition`: South House 14 held both deliveries; the loadout desk did not record which delivery supplied which part of the 19000 kg truck. Hopper note BM-009 is `no individual ticket`.

---

## EVAL-PROV-001

**family:** processor_receipt_provenance  
**processor_receipt:** HFM-IN-602

**Upstream dispatch:** PGE-OUT-5002 (aliases PG-OUT-5002, OUT-5002), carrier manifest NS-8848, bill NS-5002-B.  
Links: `outbound_same_movement` (cargo_mark equals dispatch_ref), `inbound_same_movement` (BOL equals mill `bill_reference`), derived `established_shipment`.

**Inbound material identities:** WB-390 and EF-18 (hopper-named contributors to that dispatch).

**Downstream processing output:** mill run MILL-2207, output batch FEED-2207 (grower feed), input receipt HFM-IN-602.

**Unresolved allocation:** quantity split of the blended 26000 kg between WB-390 and EF-18 (`out_5002_quantity_split`). Attribution of the mill receipt or FEED-2207 to a single inbound ticket is not established.

---

## EVAL-PROV-002

**family:** processor_receipt_provenance  
**processor_receipt:** HFM-IN-604

**Upstream dispatch:** PGE-OUT-5004 (aliases PG-OUT-5004, OUT-5004), manifest RL-9127, bill RL-5004-Q.  
`established_shipment` records dispatch PGE-OUT-5004, manifest RL-9127, mill receipt HFM-IN-604.

**Source status:** loadout from BIN-14 / South House 14. Contributing house contents are MCR-118 and S-52; which portion of the truck came from which ticket is unresolved (`out_5004_ticket_composition`).

**Identified inbound load:** established. The mill slip is matched to the carrier BOL / elevator dispatch above.

**Processing output:** not recorded. No `mill_process` row names HFM-IN-604; derived `output_batch` is empty. Completeness gap: HFM-IN-604 has no mill run in the supplied mill_runs.

---

## EVAL-CUST-001

**family:** custody_owner_at  
**material:** WB-390  
**timestamp:** 2025-09-04T13:10:00-05:00

**Recorded owner:** GrainLink Merchants.  
`ownership_event` TR-102 (`title_change` on WB-390) is in force from 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00, `owner_after` GrainLink Merchants. TR-104 on OUT-5002 (effective from 2025-09-04T13:05:00-05:00) also has `owner_after` GrainLink Merchants.

**Recorded custodian of ticket WB-390:** Prairie Gate Elevator on the ticket-scoped record (TR-102 `holder_after`).

**Custodian of WB-390 as a single identity at this instant:** unresolved.  
At 13:10, TR-104 already records a custody handoff of OUT-5002 to Northstar Bulk Transport, and BM-004 has moved a WB-390 / EF-18 blend toward loadout, but:
- loadout LD-19 and truck move BM-005 are still later (13:15 and 13:14);
- individual allocation of WB-390 into OUT-5002 is unresolved (`out_5002_quantity_split`);
- TR-102 still lists Prairie Gate as holder of WB-390 through the next day.

The ticket therefore does not have a unique established custodian at 13:10. Ownership export also does not guarantee absence of unrecorded agreements (`unrecorded_ownership`).

---

## EVAL-CUST-002

**family:** custody_owner_at  
**material:** EF-18  
**timestamp:** 2025-09-03T12:00:00-05:00

**Recorded owner:** East Fork Co-op.  
`intake_receipt` ER-7729 (`arrived_at` 2025-09-03T11:05:00-05:00) has `owner_at_intake` East Fork Co-op. No later `ownership_event` with `scope_ref` EF-18 is recorded.

**Recorded custodian:** no `ownership_event` records a holder for EF-18.

**Location evidence (not an ownership-event custody assignment):** by 12:00 the ticket is in BIN-12 at Prairie Gate Elevator (`storage_move` BM-003 at 11:28). Physical possession at the elevator is consistent with that move; it is not a recorded title or custody change.

**Unresolved:** whether any unrecorded ownership or custody agreement existed (`unrecorded_ownership`).

---

## EVAL-INSP-001

**family:** inspection_downstream_scope  
**sample:** SMP-602B

**Lab record:** tested 2025-09-05T13:10:00-05:00; `material_hint` receiving slip HFM-IN-602; `local_lot` `WB390 / EF18`; comment `combined truck sample`.

**Established affected shipment:** PGE-OUT-5002 / manifest NS-8848.

**Established affected processor receipt:** HFM-IN-602.

**Established affected processed output:** FEED-2207 (MILL-2207).

**Attribution to individual inbound material:** unresolved. The sample is a combined truck sample naming WB-390 and EF-18 together; quantity split remains unresolved (`out_5002_quantity_split`).

---

## EVAL-INSP-002

**family:** inspection_downstream_scope  
**sample:** SMP-604Q

**Lab record:** `material_hint` South House 14 cargo; `local_lot` MC-118 (alias of MCR-118); comment `customer hold review`.

**Established affected shipment:** PGE-OUT-5004 / manifest RL-9127 (South House 14 / BIN-14 loadout).

**Established affected processor receipt:** HFM-IN-604.

**Processed output:** not recorded (no mill run on HFM-IN-604).

**Unresolved source attribution:** loadout from BIN-14 does not allocate between MCR-118 and S-52 (`out_5004_ticket_composition`). The lab lot label MC-118 does not resolve individual inbound attribution of the house cargo. `lab_test` local lots include unvalidated labels and are not by themselves a ticket allocation.

---

## EVAL-INSP-003

**family:** inspection_downstream_scope  
**sample:** SMP-UNLISTED

**Validated downstream shipment:** not established.

**Validated processor receipt:** not established.

**Validated inbound source identity:** not established.

**Unresolved linkage:** requirement `smp_unlisted_source_ticket` — lab comment records that the source ticket was not recorded; `local_lot` / `material_hint` `N3 / EF-18?` / `route packet note` is not treated as a ticket. The same cargo-mark string appears on manifest NS-8910 for PGE-OUT-5003, but that mark is itself not a validated source ticket (`out_5003_material_identity`). No mill slip exists for that East consignee movement (`out_5003_mill_receipt`). Those coincidences are not an established inspection-to-shipment or inspection-to-ticket link.

---

## Cross-task derivation note

`established_shipment` is derived by joining `outbound_same_movement` to `inbound_same_movement` on `manifest_no`, then left-joining `mill_process` on mill receipt. Completeness over `outbound_same_movement` is INCOMPLETE: PGE-OUT-5003 has a manifest and no mill slip; HFM-IN-604 has no mill run. That incompleteness is used above rather than inferred away.
