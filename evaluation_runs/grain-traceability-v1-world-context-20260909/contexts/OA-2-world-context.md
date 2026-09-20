WORLD CONTEXT
renderer: world-context-renderer-v1.0.0
world hash: 1eebe0f15eacb711080db8826d7bc2bad39da3ff28658afcfa5fb5f30da7e9d3
world id: v0
revision: 235
world.sqlite sha256: 5f490eb794d65b977bec9a4cc1e97c9416a809da44acac893cca680abbd2fafb

PURPOSE
# Purpose

Trace grain through receiving, storage, processing, and outbound shipment using the workspace's declared purpose in `/PURPOSE.md`. Establish material origins, events, destinations, inspections, and recorded ownership/custody only where evidence supports them. Retain ambiguous identities, allocations, missing links, and bounded coverage explicitly.

## User basis

> Construct the reusable semantic World for this workspace and its declared purpose.

> Produce the smallest grounded World that is sufficient for the declared purpose. Preserve unsupported meaning as unresolved rather than guessing.

SEMANTIC SURFACE
17 relations · 66 referents · 185 assertions

acceptance(cargo: REFERENT, at: TEXT, site: REFERENT, dock: TEXT, silo: TEXT, bill: TEXT, kg: REAL)
  BASE · WORLD · 3 rows
alias(entity: REFERENT, namespace: TEXT, name: TEXT)
  BASE · WORLD · 30 rows
coverage(site: REFERENT, dataset: TEXT, start_date: TEXT, end_date: TEXT, qualification: TEXT)
  BASE · WORLD · 2 rows
departure(manifest: REFERENT, at: TEXT, carrier: REFERENT, truck: TEXT, pickup: REFERENT, intended_site: REFERENT, bill: TEXT, kg: REAL, cargo_mark: TEXT)
  BASE · WORLD · 4 rows
entity(entity: REFERENT, kind: TEXT)
  BASE · WORLD · 66 rows
flow(upstream: REFERENT, downstream: REFERENT, basis: TEXT)
  BASE · WORLD · 8 rows
inspection(sample: REFERENT, at: TEXT, lab_ticket: TEXT, local_lot: TEXT, hint: TEXT, test: TEXT, result: TEXT, unit: TEXT)
  BASE · WORLD · 4 rows
intake(cargo: REFERENT, receipt: TEXT, at: TEXT, commodity: TEXT, supplier: REFERENT, owner: REFERENT, kg: REAL, bin: REFERENT)
  BASE · WORLD · 5 rows
loadout(cargo: REFERENT, dispatch: TEXT, at: TEXT, bin: REFERENT, truck: TEXT, kg: REAL, route: TEXT)
  BASE · WORLD · 4 rows
manifest_for(manifest: REFERENT, cargo: REFERENT, basis: TEXT)
  BASE · WORLD · 4 rows
movement(event: REFERENT, at: TEXT, from_point: REFERENT, to_point: REFERENT, kg: REAL, material_note: TEXT, work_order: TEXT)
  BASE · WORLD · 10 rows
party_record(record: REFERENT, recorded_at: TEXT, kind: TEXT, scope: REFERENT, start: TEXT, end: TEXT, from_party: REFERENT, to_party: REFERENT, owner_after: TEXT, holder_after: TEXT, basis: TEXT)
  BASE · WORLD · 7 rows
processing(run: REFERENT, at: TEXT, input: REFERENT, output: REFERENT, product: TEXT)
  BASE · WORLD · 2 rows
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  BASE · PURPOSE · 13 rows
sample_of(sample: REFERENT, cargo: REFERENT)
  BASE · WORLD · 2 rows
stored(cargo: REFERENT, bin: REFERENT, event: REFERENT)
  BASE · WORLD · 5 rows
trace(upstream: REFERENT, downstream: REFERENT)
  DERIVED · WORLD · 16 rows

DERIVATIONS
trace
  inputs: flow
  state: CURRENT
  execution: SUCCEEDED · 16 outputs

COMPLETENESS
trace over flow
  status: COMPLETE
  basis: Recursive UNION exhausts this finite graph; not complete real-world lineage
  known gaps: (none recorded)

UNRESOLVEDNESS
purpose_requirement_failure(requirement_id: TEXT, affected_identity: TEXT, failure_kind: TEXT, relation_name: TEXT, subject_json: TEXT, grounding_ref: TEXT)
  13 rows

GROUNDING
DERIVATION: 16 records in _world_groundings
SOURCE: 271 records in _world_groundings
WORLD: 172 records in _world_groundings
assertion origins: world.sqlite.origins.json
mechanism tables: _world_groundings, _world_assertions

ACCESS
world.sqlite
world.purpose.json
world.sqlite.origins.json
world.admission.json
