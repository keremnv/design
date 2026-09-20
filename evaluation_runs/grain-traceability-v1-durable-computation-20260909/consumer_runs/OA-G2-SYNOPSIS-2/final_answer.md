# Grain traceability held-out answers

Experiment: `grain-traceability-v1-durable-computation-20260909`  
World: `v0` revision 95. `application/catalog.json` was not present; answers are grounded in `world/world.sqlite` and purpose unresolved notes. Empty mill outputs and unvalidated cargo notes are not treated as established identities.

## EVAL-SRC-001

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5002
- **established contributing inbound material identities:** WB-390, EF-18 (hopper sheet on move BM-004 / work order OUT-5002 names both tickets)
- **established source location:** Prairie Gate Elevator, BIN-12 (North House 12); loadout LD-19
- **downstream linkage (supporting, not asked as primary):** same movement as manifest NS-8848 and mill receipt HFM-IN-602; mill run MILL-2207 produced FEED-2207
- **individual source allocation:** unresolved (`out_5002_quantity_split`) — hopper names WB-390 and EF-18 together; the 26000 kg blend is not allocated to individual tickets

## EVAL-SRC-002

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5003
- **established source location:** Prairie Gate Elevator, BIN-12 (North House 12); loadout LD-20, 12000 kg, vehicle NST-219, route EAST-1
- **established inbound material identity:** none. Hopper move BM-006 records “no ticket on hopper sheet”; there is no `hopper_names_ticket` row for OUT-5003
- **missing / unresolved source linkage:**
  - `out_5003_material_identity` — cargo mark `N3 / EF-18?` is not a validated source ticket (N3 is a route code elsewhere)
  - `out_5003_mill_receipt` — carrier manifest NS-8910 exists (consignee HFM-E / Hearthland Feed Mill - East), but no HFM receiving slip is in the extracts; North-log completeness does not speak to East
- **established_shipment:** not derived for this dispatch (manifest without mill slip)

## EVAL-SRC-003

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5004
- **established contributing inbound material identities:** MCR-118 and S-52 (both ticketed into BIN-14 / South House 14 before loadout LD-21 from that bin)
- **individual allocation:** unresolved (`out_5004_ticket_composition`) — South House 14 held both deliveries; the loadout desk did not record which delivery supplied which part of the 19000 kg truck. Hopper move BM-009 notes “no individual ticket”
- **grower account for MCR-118:** separately unresolved (`m_creek_account`) — intake grower “M. Creek” is not keyed to Meadow Creek Farms vs Meadow Creek Grain

## EVAL-PROV-001

- **family:** processor_receipt_provenance
- **processor receipt:** HFM-IN-602 (HFM-N dock N-1, 2025-09-05T10:50:00-05:00, bill NS-5002-B, origin label PG-OUT-5002)
- **upstream dispatch:** PGE-OUT-5002 (alias PG-OUT-5002 / OUT-5002), manifest NS-8848; BOL match `NS-5002-B`
- **inbound material identities:** WB-390 and EF-18 (established as contributing; see EVAL-SRC-001)
- **downstream processing output:** established — mill run MILL-2207, output batch FEED-2207 (grower feed)
- **unresolved allocation:** `out_5002_quantity_split` — blended 26000 kg not split between WB-390 and EF-18; lab sample on this slip is a combined truck sample

## EVAL-PROV-002

- **family:** processor_receipt_provenance
- **processor receipt:** HFM-IN-604 (HFM-N dock N-3, 2025-09-07T13:02:00-05:00, bill RL-5004-Q, origin label PG-OUT-5004)
- **upstream dispatch:** PGE-OUT-5004, manifest RL-9127; BOL match establishes this mill slip as the same movement
- **source status:** loadout from BIN-14 / South House 14; bin contents MCR-118 and S-52 are established as the contributing pool; individual ticket composition is unresolved (`out_5004_ticket_composition`)
- **identified inbound load:** established at the mill as HFM-IN-604 (linked to RL-9127 / PGE-OUT-5004). Individual Prairie Gate receiving ticket for the truck is not identified
- **processing output:** not recorded — `established_shipment.output_batch` is empty; completeness gap: HFM-IN-604 has no mill run in the supplied mill_runs

## EVAL-CUST-001

- **family:** custody_owner_at
- **material:** WB-390
- **timestamp:** 2025-09-04T13:10:00-05:00
- **recorded owner:** GrainLink Merchants (title change TR-102, scope WB-390, effective 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00)
- **recorded holder on the WB-390 title record:** Prairie Gate Elevator
- **concurrent dispatch custody (not uniquely attributable to WB-390):** TR-104 (scope OUT-5002) from 2025-09-04T13:05:00-05:00 names holder Northstar Bulk Transport and owner GrainLink Merchants. At 13:10 the WB-390/EF-18 blend is in LOAD-PIT-2 (BM-004 at 13:02; truck load BM-005/LD-19 at 13:14–13:15)
- **unresolved:** individual quantity split of the OUT-5002 blend (`out_5002_quantity_split`), so custody of WB-390 as a single identity cannot be moved entirely onto the Northstar handoff; remaining WB-390 in BIN-12 is not allocated. Ownership export is recorded changes only (`unrecorded_ownership`)

## EVAL-CUST-002

- **family:** custody_owner_at
- **material:** EF-18
- **timestamp:** 2025-09-03T12:00:00-05:00
- **recorded owner:** East Fork Co-op (`intake_receipt.owner_at_intake` on ER-7729 / ticket EF-18, arrived 2025-09-03T11:05:00-05:00)
- **recorded custodian:** Prairie Gate Elevator — material is in BIN-12 after storage move BM-003 (2025-09-03T11:28:00-05:00)
- **ownership_event scoped to EF-18:** none at this timestamp (no title or custody row for EF-18)
- **unresolved:** `unrecorded_ownership` — the ownership export records listed changes only and does not prove an unrecorded agreement did not exist

## EVAL-INSP-001

- **family:** inspection_downstream_scope
- **sample:** SMP-602B (LAB-4419, aflatoxin below limit; local lot WB390/EF18; hint receiving slip HFM-IN-602; comment “combined truck sample”)
- **established downstream shipment:** PGE-OUT-5002 / manifest NS-8848
- **established processor receipt:** HFM-IN-602
- **established processed output:** FEED-2207 (MILL-2207)
- **attribution to individual inbound material:** unresolved — sample is combined; WB-390 and EF-18 are both named but not allocated (`out_5002_quantity_split`)

## EVAL-INSP-002

- **family:** inspection_downstream_scope
- **sample:** SMP-604Q (LAB-4422, moisture 14.8 percent; local lot MC-118; hint “South House 14 cargo”; comment “customer hold review”)
- **established downstream shipment:** PGE-OUT-5004 / manifest RL-9127
- **established processor receipt:** HFM-IN-604
- **processed output:** not recorded (no mill run on HFM-IN-604)
- **unresolved source attribution:**
  - `out_5004_ticket_composition` — South House 14 cargo is the MCR-118 + S-52 pool; loadout does not allocate the truck
  - lab local_lot `MC-118` aliases to MCR-118 but is not treated as a resolved exclusive inbound identity
  - `m_creek_account` remains unresolved if MCR-118 is at issue

## EVAL-INSP-003

- **family:** inspection_downstream_scope
- **sample:** SMP-UNLISTED (LAB-4428, protein 12.5 percent; local lot `N3 / EF-18?`; hint “route packet note”; comment “source ticket not recorded”)
- **validated downstream shipment:** not established
- **validated processor receipt:** not established
- **validated inbound source identity:** not established
- **unresolved linkage (`smp_unlisted_source_ticket`):** lab comment records that the source ticket was not recorded; the route-packet note is not treated as a ticket. The string `N3 / EF-18?` matches an unvalidated cargo mark on manifest NS-8910 / PGE-OUT-5003, which itself has unresolved material identity and no mill slip; that resemblance is not a validated event link
