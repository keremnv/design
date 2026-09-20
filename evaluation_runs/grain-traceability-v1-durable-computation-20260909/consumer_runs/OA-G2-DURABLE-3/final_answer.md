# Grain traceability held-out answers

World: v0 revision 95  
hash: `24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220`  
Computations used from `application/catalog.json` (cross-checked against World relations). Unsupported links are left unresolved.

---

## EVAL-SRC-001

**Family:** shipment_source_status  
**Dispatch:** PGE-OUT-5002

### Established

- **Source location:** Prairie Gate Elevator, North House 12 (`BIN-12`), loadout `LD-19` at `2025-09-04T13:15:00-05:00`, quantity `26000` kg.
- **Contributing inbound identities (hopper-named):** `WB-390`, `EF-18`.
- **Outbound manifest:** `NS-8848` (cargo_mark equals elevator dispatch_ref).
- Candidate tickets already in `BIN-12` before loadout: `DR-44`, `EF-18`, `WB-390`. Only the hopper-named pair is established as contributing.

### Unresolved

- **Individual source allocation remains unresolved** (`source_allocation_unresolved`: true).
- Requirement `out_5002_quantity_split`: hopper note names `WB-390` and `EF-18` together; the loadout does not allocate the blended 26000 kg to individual tickets.

---

## EVAL-SRC-002

**Family:** shipment_source_status  
**Dispatch:** PGE-OUT-5003

### Established

- **Source location:** Prairie Gate Elevator, North House 12 (`BIN-12`), loadout `LD-20` at `2025-09-05T07:10:00-05:00`, quantity `12000` kg.
- **Outbound manifest:** `NS-8910` (same vehicle tag and loaded weight; cargo_mark is not the dispatch id).
- Candidate tickets in `BIN-12` before loadout: `DR-44`, `EF-18`, `WB-390`.

### Unresolved

- **No established inbound material identity** (hopper sheet empty; `established_contributing_identities`: []).
- `out_5003_material_identity`: no ticket on the hopper sheet. `N3` is a route code elsewhere; the handwritten cargo note `N3 / EF-18?` is not a validated source ticket.
- `out_5003_mill_receipt`: carrier manifest exists, but no HFM receiving slip is in the supplied extracts. Consignee is `HFM-E`; North-log completeness does not speak to East.
- Source allocation remains unresolved.

---

## EVAL-SRC-003

**Family:** shipment_source_status  
**Dispatch:** PGE-OUT-5004

### Established

- **Source location:** Prairie Gate Elevator, South House 14 (`BIN-14`), loadout `LD-21` at `2025-09-07T10:30:00-05:00`, quantity `19000` kg.
- **Outbound manifest:** `RL-9127` (cargo_mark equals elevator dispatch_ref).
- Candidate tickets in `BIN-14` before loadout: `MCR-118`, `S-52`.
- Hopper names no tickets (`established_contributing_identities`: []).

### Unresolved

- **No inbound identities are established as contributing** to this truck.
- **Individual allocation is not resolved** (`source_allocation_unresolved`: true).
- Requirement `out_5004_ticket_composition`: South House 14 held `MCR-118` and `S-52`; the loadout desk did not record which delivery supplied which part of the truck.

---

## EVAL-PROV-001

**Family:** processor_receipt_provenance  
**Processor receipt:** HFM-IN-602

### Established

- **Mill receipt:** `HFM-IN-602` at Hearthland Feed Mill - North (`HFM-N`), dock `N-1`, silo `S-5`, received `2025-09-05T10:50:00-05:00`, `25500` kg HRW wheat, bill_reference `NS-5002-B`.
- **Upstream path:** dispatch `PGE-OUT-5002` → manifest `NS-8848` → mill slip `HFM-IN-602`.
  - outbound link: cargo_mark equals elevator dispatch_ref
  - inbound link: bill_of_lading equals mill bill_reference
- **Inbound material identities established as contributing to that dispatch:** `WB-390`, `EF-18` (hopper-named). Source bin `BIN-12`.
- **Downstream processing:** mill run `MILL-2207` started `2025-09-05T15:10:00-05:00`, output batch `FEED-2207` (grower feed).

### Unresolved

- **Individual ticket allocation on the upstream truck is unresolved** (`upstream_ticket_allocation`: true; `processing_run_missing`: false; `mill_receipt_missing`: false).
- Requirement `out_5002_quantity_split`: blended 26000 kg is not split between `WB-390` and `EF-18`.
- Candidate occupants of the source bin also included `DR-44`, which is not hopper-named for this dispatch.

---

## EVAL-PROV-002

**Family:** processor_receipt_provenance  
**Processor receipt:** HFM-IN-604

### Established

- **Mill receipt is recorded:** `HFM-IN-604` at Hearthland Feed Mill - North, dock `N-3`, silo `S-7`, received `2025-09-07T13:02:00-05:00`, `18800` kg, bill_reference `RL-5004-Q`.
- **Upstream dispatch:** `PGE-OUT-5004` → manifest `RL-9127` → mill slip `HFM-IN-604` (same BOL / cargo_mark bases as other North links).
- **Upstream source status:** loadout from `BIN-14`; no hopper-named inbound load; candidates in bin `MCR-118` and `S-52`; allocation unresolved.

### Unresolved

- **No identified inbound load is established** for the upstream dispatch (`established_contributing_identities`: []).
- **No processing output is recorded** (`processing`: null; `processing_run_missing`: true). Completeness note: `HFM-IN-604` has no mill run in the supplied mill_runs.
- Requirement `out_5004_ticket_composition`: which of `MCR-118` / `S-52` supplied the truck is not recorded.

---

## EVAL-CUST-001

**Family:** custody_owner_at  
**Material:** WB-390  
**Timestamp:** 2025-09-04T13:10:00-05:00

### Established (from covering `ownership_event`)

- Covering record `TR-102` (title_change, broker release GL-88), interval `[2025-09-03T15:00:00-05:00, 2025-09-05T10:50:00-05:00)`.
- **Recorded owner:** GrainLink Merchants (`owner_after`).
- **Recorded custodian:** Prairie Gate Elevator (`holder_after`).
- Timestamp is before loadout `LD-19` (`2025-09-04T13:15:00-05:00`). Dispatch-scoped custody row `TR-104` (`scope_ref` OUT-5002 / PGE-OUT-5002, holder Northstar Bulk Transport from `13:05`) is not a covering event for ticket `WB-390`.

### Unresolved

- Requirement `unrecorded_ownership`: the ownership export records changes; it does not guarantee that an unrecorded agreement did not exist.

---

## EVAL-CUST-002

**Family:** custody_owner_at  
**Material:** EF-18  
**Timestamp:** 2025-09-03T12:00:00-05:00

### Established

- Intake `ER-7729` arrived `2025-09-03T11:05:00-05:00` with `owner_at_intake` East Fork Co-op (grower East Fork Co-op). That is an intake fact, not a covering ownership_event at the query time.

### Unresolved

- **No covering `ownership_event` for EF-18 at this timestamp** (`covering_event`: null).
- **Recorded owner from ownership events:** not established (null).
- **Recorded custodian from ownership events:** not established (null).
- No `ownership_event` row is scoped to `EF-18` at all.
- Requirement `unrecorded_ownership` still applies.

---

## EVAL-INSP-001

**Family:** inspection_downstream_scope  
**Sample:** SMP-602B

Lab: tested `2025-09-05T13:10:00-05:00`, local_lot `WB390 / EF18` → identities `WB-390`, `EF-18`, material_hint names mill receipt `HFM-IN-602`, comment “combined truck sample”.

### Established as affected

- **Downstream shipment:** none established as *downstream of the sample* (the sample is on mill receiving slip `HFM-IN-602` after arrival).
- **Processor receipt:** `HFM-IN-602` (lab material_hint names this mill receipt).
- **Processed output:** `FEED-2207` (grower feed), mill run `MILL-2207` (run starts after the sample time).

### Unresolved

- **Attribution to an individual inbound ticket is not resolved.** The sample is a combined lot of `WB-390` and `EF-18`. Upstream dispatch `PGE-OUT-5002` names both on the hopper but does not allocate the blended quantity (`out_5002_quantity_split`).

---

## EVAL-INSP-002

**Family:** inspection_downstream_scope  
**Sample:** SMP-604Q

Lab: tested `2025-09-07T14:10:00-05:00`, local_lot `MC-118` → `MCR-118`, material_hint `South House 14 cargo` (not a mill-slip id).

### Established as affected

- Sampled inbound identity **MCR-118** is established.
- **Downstream shipment:** none established. PGE-OUT-5004 left `BIN-14` at `10:30` the same day, *before* this sample; hopper did not name a ticket, so that truck is not an established exclusive allocation even as a prior load.
- **Processor receipt:** none established as affected by this sample (`HFM-IN-604` is not named in the lab hint).
- **Processed output:** none recorded for `HFM-IN-604`, and none is attached to this sample.

### Unresolved

- Grower/account for `MCR-118`: requirement `m_creek_account` — intake uses “M. Creek”; commercial desk has claims from both Meadow Creek Farms and Meadow Creek Grain with no account key that selects one.
- Source composition of South House 14 remains mixed (`MCR-118` and `S-52`); `out_5004_ticket_composition` applies to the earlier unallocated loadout, not as a validated downstream effect of SMP-604Q.

---

## EVAL-INSP-003

**Family:** inspection_downstream_scope  
**Sample:** SMP-UNLISTED

Lab: tested `2025-09-08T09:00:00-05:00`, local_lot `N3 / EF-18?`, material_hint `route packet note`, comment “source ticket not recorded”. Sample row exists.

### Established

- **Validated downstream shipment:** not established.
- **Validated processor receipt:** not established.
- **Validated inbound source identity:** not established (`sampled_identities`: []).

### Unresolved (preserved)

- `sampled_material_identity`: source ticket not recorded.
- Requirement `smp_unlisted_source_ticket`: the route-packet note is not treated as a ticket; `N3` is a route code elsewhere and `EF-18?` is not a validated identity.
- No mill receipt, established_shipment, or hopper-named loadout is grounded from this sample.
