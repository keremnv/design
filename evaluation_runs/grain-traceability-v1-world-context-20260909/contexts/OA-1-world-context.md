WORLD CONTEXT
renderer: world-context-renderer-v1.0.0
world hash: d39faa9ed9e40b03fea7cd329033ae7756664f4dae533ff83a6c7c725006b116
world id: v0
revision: 362
world.sqlite sha256: 817d294ee4d32c8ff01b27dd13e436658a3076fd79241e8e973b7c7059873a0e

PURPOSE
# Purpose

Trace the supplied grain deliveries through elevator receiving, storage, truck dispatch, mill receipt, and processing into feed batches. Establish material lineage and event links only where supported; retain unresolved source allocation, party identity, inspection scope, and missing downstream evidence. Keep ownership distinct from physical custody and recorded intent distinct from actual receipt.

The declared domain purpose is in the workspace's `PURPOSE.md`.

## User basis

> Construct the reusable semantic World for this workspace and its declared purpose.

> Produce the smallest grounded World that is sufficient for the declared purpose. Preserve unsupported meaning as unresolved rather than guessing.

SEMANTIC SURFACE
19 relations · 85 referents · 293 assertions

coverage(site: REFERENT, dataset: TEXT, start_date: TEXT, end_date: TEXT, extent: TEXT)
  BASE · WORLD · 2 rows
departure(event: REFERENT, cargo: REFERENT, vehicle: REFERENT, carrier: REFERENT, pickup: REFERENT, intended_destination: REFERENT, quantity_kg: REAL, bill: TEXT)
  BASE · WORLD · 4 rows
designation(entity: REFERENT, namespace: TEXT, label: TEXT)
  BASE · WORLD · 37 rows
dispatch(event: REFERENT, cargo: REFERENT, bin: REFERENT, vehicle: REFERENT, quantity_kg: REAL, route_code: TEXT)
  BASE · WORLD · 4 rows
entity(entity: REFERENT, kind: TEXT, label: TEXT)
  BASE · WORLD · 85 rows
event(event: REFERENT, kind: TEXT, occurred_at: TEXT)
  BASE · WORLD · 32 rows
event_link(earlier: REFERENT, later: REFERENT, kind: TEXT)
  BASE · WORLD · 19 rows
event_material(event: REFERENT, material: REFERENT, role: TEXT)
  BASE · WORLD · 32 rows
inspection(event: REFERENT, test: TEXT, result: TEXT, unit: TEXT, reported_scope: TEXT)
  BASE · WORLD · 4 rows
inspection_scope(event: REFERENT, subject: REFERENT, scope_kind: TEXT)
  BASE · WORLD · 3 rows
intake_party(material: REFERENT, grower: REFERENT, owner_label: REFERENT)
  BASE · WORLD · 5 rows
material_flow(upstream: REFERENT, downstream: REFERENT, kind: TEXT)
  BASE · WORLD · 8 rows
movement(event: REFERENT, from_place: REFERENT, to_place: REFERENT, quantity_kg: REAL)
  BASE · WORLD · 10 rows
ownership_record(record: REFERENT, scope: REFERENT, record_type: TEXT, recorded_at: TEXT, effective_start: TEXT, effective_end: TEXT, from_party: REFERENT, to_party: REFERENT, owner_after: TEXT, holder_after: TEXT, basis: TEXT)
  BASE · WORLD · 7 rows
party_candidate(designation: REFERENT, candidate: REFERENT)
  BASE · WORLD · 2 rows
processing(event: REFERENT, input: REFERENT, output: REFERENT, product: TEXT)
  BASE · WORLD · 2 rows
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  BASE · PURPOSE · 13 rows
receiving(event: REFERENT, material: REFERENT, site: REFERENT, storage: REFERENT, quantity_kg: REAL, commodity: TEXT)
  BASE · WORLD · 8 rows
trace(upstream: REFERENT, downstream: REFERENT)
  DERIVED · WORLD · 16 rows

DERIVATIONS
trace
  inputs: material_flow
  state: CURRENT
  execution: SUCCEEDED · 16 outputs

COMPLETENESS
trace over material_flow
  status: INCOMPLETE
  basis: Recursive UNION over all grounded direct edges
  known gaps: Not complete real-world lineage: source allocation and missing downstream evidence remain unresolved.

UNRESOLVEDNESS
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  13 rows

GROUNDING
DERIVATION: 16 records in _world_groundings
SOURCE: 448 records in _world_groundings
WORLD: 282 records in _world_groundings
assertion origins: world.sqlite.origins.json
mechanism tables: _world_groundings, _world_assertions

ACCESS
world.sqlite
world.purpose.json
world.sqlite.origins.json
world.admission.json
