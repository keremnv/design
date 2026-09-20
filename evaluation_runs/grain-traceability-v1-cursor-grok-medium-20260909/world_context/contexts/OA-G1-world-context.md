WORLD CONTEXT
renderer: world-context-renderer-v1.0.0
world hash: dc2e7e45c1327fc997691b4fa4071c5fd44edb6aed2b57e2d1e4e4c70a471eb8
world id: v0
revision: 242
world.sqlite sha256: b2053bcf7c9e02a39b64a77065ff952c4357e494b024292c08eb9a6ff9481a4c

PURPOSE
# Purpose

Trace grain through Prairie Gate receiving, storage, and loadout, then through carrier shipment and Hearthland mill intake and processing. Record where material came from, what happened to it, and where it went only when the workspace evidence establishes those links. Keep unsupported identity, blend allocation, and missing receiving evidence unresolved.

## User basis

> Build a reusable World that lets us trace grain through receiving, storage, processing, and outbound shipment, including determining where material came from, what happened to it, and where it went when the available evidence establishes those links. Preserve uncertainty where material identity or event linkage cannot be established.

SEMANTIC SURFACE
15 relations · 65 referents · 177 assertions

bin_transfer(move: REFERENT, from_place: REFERENT, to_place: REFERENT, material_note: TEXT, quantity_kg: TEXT, work_order: TEXT, logged_at: TEXT)
  BASE · WORLD · 10 rows
carrier_departure(manifest: REFERENT, movement: REFERENT, carrier: REFERENT, vehicle: REFERENT, cargo_mark: TEXT, bill_of_lading: TEXT, consignee_code: TEXT, consignee_name: TEXT, pickup_site: REFERENT, weight_kg: TEXT, departed_at: TEXT, route_note: TEXT)
  BASE · WORLD · 4 rows
commercial_scope(record: REFERENT, scoped: REFERENT, scope_kind: TEXT)
  BASE · WORLD · 7 rows
consignee_is_not_receipt(manifest: REFERENT, consignee_code: TEXT)
  BASE · WORLD · 4 rows
elevator_intake(ticket: REFERENT, receipt_no: TEXT, site: REFERENT, grower_recorded: TEXT, commodity: TEXT, net_kg: TEXT, lane: REFERENT, assigned_bin: REFERENT, owner_recorded: TEXT, arrived_at: TEXT, grade_note: TEXT)
  BASE · WORLD · 5 rows
elevator_loadout(loadout: REFERENT, movement: REFERENT, bin: REFERENT, truck: REFERENT, dispatch_ref: TEXT, quantity_kg: TEXT, spout: TEXT, route_code: TEXT, loaded_at: TEXT, desk_comment: TEXT)
  BASE · WORLD · 4 rows
extract_coverage(collection: TEXT, coverage_claim: TEXT)
  BASE · WORLD · 4 rows
known_as(entity: REFERENT, token: TEXT, system: TEXT)
  BASE · WORLD · 94 rows
lab_result(sample: REFERENT, tested_at: TEXT, lab_ticket: TEXT, local_lot: TEXT, material_hint: TEXT, test_name: TEXT, result: TEXT, unit: TEXT, comment: TEXT)
  BASE · WORLD · 4 rows
location(place: REFERENT, site: REFERENT, kind: TEXT, local_name: TEXT)
  BASE · WORLD · 14 rows
mill_intake(receipt: REFERENT, movement: REFERENT, site: REFERENT, dock: TEXT, bill_reference: TEXT, origin_label: TEXT, received_kg: TEXT, silo: TEXT, commodity: TEXT, received_at: TEXT)
  BASE · WORLD · 3 rows
mill_process(run: REFERENT, input_receipt: REFERENT, output_batch: REFERENT, output_name: TEXT, started_at: TEXT)
  BASE · WORLD · 2 rows
ownership_event(record: REFERENT, record_type: TEXT, scope_ref: TEXT, effective_start: TEXT, effective_end: TEXT, from_party: TEXT, to_party: TEXT, owner_after: TEXT, holder_after: TEXT, basis: TEXT, recorded_at: TEXT)
  BASE · WORLD · 7 rows
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  BASE · PURPOSE · 8 rows
ticket_named_on_move(ticket: REFERENT, move: REFERENT, note_span: TEXT)
  BASE · WORLD · 7 rows

DERIVATIONS
(none recorded)

COMPLETENESS
(none recorded)

UNRESOLVEDNESS
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  8 rows

GROUNDING
SOURCE: 288 records in _world_groundings
WORLD: 177 records in _world_groundings
assertion origins: world.sqlite.origins.json
mechanism tables: _world_groundings, _world_assertions

ACCESS
world.sqlite
world.purpose.json
world.sqlite.origins.json
world.admission.json
