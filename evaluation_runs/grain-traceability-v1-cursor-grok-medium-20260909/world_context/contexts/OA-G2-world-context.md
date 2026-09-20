WORLD CONTEXT
renderer: world-context-renderer-v1.0.0
world hash: 24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220
world id: v0
revision: 95
world.sqlite sha256: fdd4f332b7b5372bdfc1da6f0e9e1a33b96aa6c12c129768bec30e11f80f4586

PURPOSE
# Purpose

Trace grain through Prairie Gate receiving and storage, carrier outbound shipment, and Hearthland processing when evidence establishes those links, and keep material identity, ownership, and event linkage unresolved when it does not.

## User basis

> Build a reusable World that lets us trace grain through receiving, storage, processing, and outbound shipment, including determining where material came from, what happened to it, and where it went when the available evidence establishes those links. Preserve uncertainty where material identity or event linkage cannot be established.

> Produce the smallest grounded World that is sufficient for the declared purpose. Preserve unsupported meaning as unresolved rather than guessing.

SEMANTIC SURFACE
17 relations · 0 referents · 98 assertions

established_shipment(dispatch_ref: TEXT, manifest_no: TEXT, mill_receipt: TEXT, output_batch: TEXT)
  DERIVED · WORLD · 3 rows
extract_coverage(desk: TEXT, site: TEXT, window: TEXT, claim: TEXT)
  BASE · WORLD · 3 rows
hopper_names_ticket(move_id: TEXT, work_order: TEXT, scale_ticket: TEXT)
  BASE · WORLD · 7 rows
identifier_alias(form: TEXT, canonical: TEXT, kind: TEXT)
  BASE · WORLD · 22 rows
inbound_same_movement(manifest_no: TEXT, mill_receipt: TEXT, link_basis: TEXT)
  BASE · WORLD · 3 rows
intake_receipt(receipt_no: TEXT, scale_ticket: TEXT, arrived_at: TEXT, commodity: TEXT, grower_name: TEXT, net_kg: TEXT, receiving_lane: TEXT, assigned_bin: TEXT, owner_at_intake: TEXT, grade_note: TEXT)
  BASE · WORLD · 5 rows
lab_test(sample_no: TEXT, tested_at: TEXT, lab_ticket: TEXT, local_lot: TEXT, material_hint: TEXT, test_name: TEXT, result: TEXT, unit: TEXT, comment: TEXT)
  BASE · WORLD · 4 rows
loadout_event(dispatch_id: TEXT, loaded_at: TEXT, truck_tag: TEXT, dispatch_ref: TEXT, bin_label: TEXT, quantity_kg: TEXT, route_code: TEXT, desk_comment: TEXT)
  BASE · WORLD · 4 rows
loadout_from_bin(dispatch_ref: TEXT, bin: TEXT, loadout_id: TEXT)
  BASE · WORLD · 4 rows
manifest_event(manifest_no: TEXT, carrier: TEXT, vehicle: TEXT, departed_at: TEXT, pickup_site: TEXT, consignee_code: TEXT, consignee_name: TEXT, bill_of_lading: TEXT, cargo_mark: TEXT, weight_kg: TEXT)
  BASE · WORLD · 4 rows
mill_process(run_no: TEXT, started_at: TEXT, input_receipt: TEXT, output_batch: TEXT, output_name: TEXT)
  BASE · WORLD · 2 rows
mill_receipt(local_receipt: TEXT, mill_code: TEXT, received_at: TEXT, dock: TEXT, bill_reference: TEXT, origin_label: TEXT, received_kg: TEXT, silo: TEXT, commodity: TEXT)
  BASE · WORLD · 3 rows
outbound_same_movement(dispatch_ref: TEXT, manifest_no: TEXT, link_basis: TEXT)
  BASE · WORLD · 4 rows
ownership_event(record_no: TEXT, record_type: TEXT, scope_ref: TEXT, effective_start: TEXT, effective_end: TEXT, from_party: TEXT, to_party: TEXT, owner_after: TEXT, holder_after: TEXT, basis: TEXT)
  BASE · WORLD · 7 rows
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  BASE · PURPOSE · 8 rows
storage_move(move_id: TEXT, logged_at: TEXT, from_point: TEXT, to_point: TEXT, material_note: TEXT, quantity_kg: TEXT, work_order: TEXT)
  BASE · WORLD · 10 rows
ticket_into_bin(scale_ticket: TEXT, bin: TEXT, move_id: TEXT)
  BASE · WORLD · 5 rows

DERIVATIONS
established_shipment
  inputs: inbound_same_movement, mill_process, outbound_same_movement
  state: STALE
  execution: SUCCEEDED · 3 outputs

COMPLETENESS
established_shipment over outbound_same_movement
  status: INCOMPLETE
  basis: BOL match from carrier manifest to mill slip; mill output only when a run names that slip; HFM-East receipts are outside the North log
  known gaps: PGE-OUT-5003 has a manifest and no mill slip in the extracts; HFM-IN-604 has no mill run in the supplied mill_runs

UNRESOLVEDNESS
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  8 rows

GROUNDING
DERIVATION: 3 records in _world_groundings
SOURCE: 108 records in _world_groundings
WORLD: 102 records in _world_groundings
assertion origins: world.sqlite.origins.json
mechanism tables: _world_groundings, _world_assertions

ACCESS
world.sqlite
world.purpose.json
world.sqlite.origins.json
world.admission.json
