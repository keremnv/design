# Grain traceability held-out answers

World: `v0` revision 95, hash `24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220`.
Computations used: `shipment_source_status`, `processor_receipt_provenance`, `custody_owner_at`, `inspection_downstream_scope`, cross-checked against sealed World relations. Unsupported links are left unresolved.

---

## EVAL-SRC-001

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5002
- **established_contributing_inbound_identities:** WB-390, EF-18 (hopper-named on move BM-004 / work order OUT-5002)
- **established_source_location:** Prairie Gate Elevator, BIN-12 (North House 12), loadout LD-19 at 2025-09-04T13:15:00-05:00, 26000 kg
- **candidate_identities_in_source_bin_not_established_as_this_truck:** DR-44 (also in BIN-12 before loadout; not named on this hopper)
- **source_allocation_unresolved:** true
- **unresolved:** `out_5002_quantity_split` — hopper names WB-390 and EF-18 together; the blended 26000 kg is not allocated to individual tickets
- **outbound_manifest:** NS-8848 (cargo_mark equals elevator dispatch_ref)

---

## EVAL-SRC-002

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5003
- **established_source_location:** Prairie Gate Elevator, BIN-12 (North House 12), loadout LD-20 at 2025-09-05T07:10:00-05:00, 12000 kg
- **established_inbound_material_identity:** none (no hopper-named ticket; established contributing identities empty)
- **candidate_identities_in_source_bin:** DR-44, EF-18, WB-390 (occupants of BIN-12 before loadout; not established as this truck)
- **source_allocation_unresolved:** true
- **missing_or_unresolved_source_linkage:**
  - `out_5003_material_identity` — no ticket on the hopper sheet; cargo mark `N3 / EF-18?` is not a validated source ticket (N3 is a route code elsewhere)
  - `out_5003_mill_receipt` — carrier manifest NS-8910 exists; no HFM receiving slip in the extracts; consignee HFM-E is outside the HFM-North completeness claim
- **outbound_manifest:** NS-8910 (same vehicle tag and loaded weight; cargo_mark is not the dispatch id)

---

## EVAL-SRC-003

- **family:** shipment_source_status
- **dispatch:** PGE-OUT-5004
- **established_contributing_inbound_identities:** none (no hopper-named tickets on the loadout)
- **candidate_identities_in_source_bin:** MCR-118, S-52 (both moved into BIN-14 / South House 14 before loadout LD-21)
- **established_source_location:** Prairie Gate Elevator, BIN-14 (South House 14), loadout LD-21 at 2025-09-07T10:30:00-05:00, 19000 kg
- **individual_allocation_resolved:** no
- **unresolved:** `out_5004_ticket_composition` — South House 14 held MCR-118 and S-52; the loadout desk did not record which delivery supplied which part of the truck

---

## EVAL-PROV-001

- **family:** processor_receipt_provenance
- **processor_receipt:** HFM-IN-602
- **mill_receipt_established:** true (HFM-N / Hearthland Feed Mill - North, dock N-1, received 2025-09-05T10:50:00-05:00, 25500 kg, silo S-5)
- **upstream_dispatch:** PGE-OUT-5002
- **established_path:** PGE-OUT-5002 → manifest NS-8848 → HFM-IN-602
  - outbound_link_basis: cargo_mark equals elevator dispatch_ref
  - inbound_link_basis: bill_of_lading equals mill bill_reference
- **established_contributing_inbound_identities:** WB-390, EF-18
- **downstream_processing_output:** established — run MILL-2207 started 2025-09-05T15:10:00-05:00, output_batch FEED-2207, output_name grower feed
- **unresolved_allocation_detail:** `out_5002_quantity_split` — WB-390 and EF-18 are named together; individual ticket shares of the 26000 kg blend are not recorded (`upstream_ticket_allocation`: true)

---

## EVAL-PROV-002

- **family:** processor_receipt_provenance
- **processor_receipt:** HFM-IN-604
- **mill_receipt_established:** true (HFM-N / Hearthland Feed Mill - North, dock N-3, received 2025-09-07T13:02:00-05:00, 18800 kg, silo S-7)
- **upstream_dispatch:** PGE-OUT-5004
- **established_path:** PGE-OUT-5004 → manifest RL-9127 → HFM-IN-604
  - outbound_link_basis: cargo_mark equals elevator dispatch_ref
  - inbound_link_basis: bill_of_lading equals mill bill_reference
- **upstream_source_status:** BIN-14 at Prairie Gate Elevator; contributing inbound tickets not established (hopper unnamed); candidates MCR-118 and S-52; `source_allocation_unresolved`: true (`out_5004_ticket_composition`)
- **identified_inbound_load_established:** mill slip HFM-IN-604 is established; an individual inbound elevator ticket for that load is not established
- **processing_output_recorded:** no — `processing_run_missing` (established_shipment output_batch empty; no mill_process row names HFM-IN-604; completeness gap: HFM-IN-604 has no mill run in the supplied mill_runs)

---

## EVAL-CUST-001

- **family:** custody_owner_at
- **material:** WB-390
- **timestamp:** 2025-09-04T13:10:00-05:00
- **recorded_owner:** GrainLink Merchants
- **recorded_custodian:** Prairie Gate Elevator
- **covering_event:** TR-102 (title_change), scope WB-390, effective 2025-09-03T15:00:00-05:00 to 2025-09-05T10:50:00-05:00, basis broker release GL-88, from Willow Bend Farms to GrainLink Merchants
- **owner_recorded:** true
- **custodian_recorded:** true
- **caveat_unresolved:** `unrecorded_ownership` — the ownership export records changes only; it does not guarantee that an unrecorded agreement did not exist

---

## EVAL-CUST-002

- **family:** custody_owner_at
- **material:** EF-18
- **timestamp:** 2025-09-03T12:00:00-05:00
- **recorded_owner:** unresolved / not recorded (no covering `ownership_event` for EF-18)
- **recorded_custodian:** unresolved / not recorded (no covering `ownership_event` for EF-18)
- **covering_event:** none
- **owner_recorded:** false
- **custodian_recorded:** false
- **related_intake_not_used_as_title_record:** intake ER-7729 at 2025-09-03T11:05:00-05:00 lists `owner_at_intake` East Fork Co-op; that is intake metadata, not a covering ownership_event at the query time
- **caveat_unresolved:** `unrecorded_ownership` — recorded changes only; no EF-18 title/custody row exists in the export

---

## EVAL-INSP-001

- **family:** inspection_downstream_scope
- **sample:** SMP-602B
- **sample_found:** true (tested 2025-09-05T13:10:00-05:00, lab LAB-4419, local_lot `WB390 / EF18`, material_hint `receiving slip HFM-IN-602`, comment combined truck sample)
- **sampled_identities:** WB-390, EF-18 (aliases WB390, EF18)
- **established_affected_processor_receipt:** HFM-IN-602 (lab material_hint names this mill receipt)
- **established_affected_processed_output:** FEED-2207 (MILL-2207, grower feed)
- **established_affected_downstream_shipment:** none after the mill sample; the mill slip is already the receiving end of PGE-OUT-5002 / NS-8848, which is upstream of this test time
- **attribution_to_individual_inbound_material_resolved:** no — both WB-390 and EF-18 are named as the combined truck; `out_5002_quantity_split` remains unresolved

---

## EVAL-INSP-002

- **family:** inspection_downstream_scope
- **sample:** SMP-604Q
- **sample_found:** true (tested 2025-09-07T14:10:00-05:00, lab LAB-4422, local_lot `MC-118`, material_hint `South House 14 cargo`)
- **sampled_identity:** MCR-118 (alias MC-118)
- **established_affected_downstream_shipment:** none
- **established_affected_processor_receipt:** none (material_hint names a bin, not a mill slip; no hopper-exclusive allocation of MCR-118 onto a truck)
- **processed_output_recorded:** no (and HFM-IN-604, the only mill slip on the BIN-14 outbound path, has no mill_process row)
- **related_but_not_established:** PGE-OUT-5004 loaded from BIN-14 at 2025-09-07T10:30:00-05:00 and HFM-IN-604 received that dispatch at 2025-09-07T13:02:00-05:00, both before this sample; those movements are not established as containing MCR-118 specifically
- **unresolved_source_attribution:**
  - `out_5004_ticket_composition` — BIN-14 held MCR-118 and S-52; loadout did not record which delivery supplied the truck
  - `m_creek_account` — intake grower `M. Creek` is not resolved between Meadow Creek Farms and Meadow Creek Grain

---

## EVAL-INSP-003

- **family:** inspection_downstream_scope
- **sample:** SMP-UNLISTED
- **sample_found:** true (tested 2025-09-08T09:00:00-05:00, lab LAB-4428, local_lot `N3 / EF-18?`, material_hint `route packet note`, comment source ticket not recorded)
- **validated_downstream_shipment_established:** no
- **validated_processor_receipt_established:** no
- **validated_inbound_source_identity_established:** no (`sampled_identities` empty; `sampled_identity_unresolved` true)
- **unresolved_linkage:**
  - `smp_unlisted_source_ticket` — lab comment records that the source ticket was not recorded; the route-packet note is not treated as a ticket
  - local_lot `N3 / EF-18?` matches the cargo_mark on manifest NS-8910 (PGE-OUT-5003) but that mark is already World-unresolved as a source ticket (`out_5003_material_identity`); it is not used here as a validated identity
  - no mill slip is established for PGE-OUT-5003 (`out_5003_mill_receipt`)
