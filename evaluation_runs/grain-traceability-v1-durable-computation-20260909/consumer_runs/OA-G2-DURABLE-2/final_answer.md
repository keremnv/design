# Grain traceability — held-out answers

World: `v0` revision 95  
Hash: `24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220`  
Computations used from `application/catalog.json`; conclusions kept only where World rows support them.

---

## EVAL-SRC-001 — PGE-OUT-5002 (`shipment_source_status`)

**Established contributing inbound identities:** `WB-390`, `EF-18`  
Hopper sheet on move `BM-004` / work order `OUT-5002` names both tickets.

**Established source location:** Prairie Gate Elevator, `BIN-12` (North House 12)  
Loadout `LD-19` at `2025-09-04T13:15:00-05:00`, 26000 kg, truck `NST-204`. Outbound manifest `NS-8848` (cargo_mark equals dispatch_ref).

**Individual source allocation:** **unresolved**  
`out_5002_quantity_split`: hopper names WB-390 and EF-18 together; the 26000 kg blend is not split by ticket.  
Bin occupants before loadout also include `DR-44`; that ticket is a candidate in the bin, not hopper-named as contributing to this dispatch.

---

## EVAL-SRC-002 — PGE-OUT-5003 (`shipment_source_status`)

**Established source location:** Prairie Gate Elevator, `BIN-12` (North House 12)  
Loadout `LD-20` at `2025-09-05T07:10:00-05:00`, 12000 kg. Manifest `NS-8910` (same vehicle tag and loaded weight; cargo_mark is not the dispatch id).

**Established inbound material identity:** **none**  
No hopper-named ticket. Candidates still in `BIN-12` before loadout: `DR-44`, `EF-18`, `WB-390`.

**Missing / unresolved source linkage:**
- `out_5003_material_identity`: no ticket on hopper; cargo_mark `N3 / EF-18?` is not a validated source ticket (`N3` is a route code elsewhere).
- `out_5003_mill_receipt`: carrier manifest exists; no mill receiving slip in extracts (consignee `HFM-E`; North-log completeness does not cover East).
- Ticket-to-truck allocation remains unresolved.

---

## EVAL-SRC-003 — PGE-OUT-5004 (`shipment_source_status`)

**Established contributing inbound identities:** **none** (hopper does not name a ticket for this loadout).

**Candidate identities in source bin `BIN-14` (South House 14) before loadout `LD-21` (`2025-09-07T10:30:00-05:00`, 19000 kg):** `MCR-118`, `S-52`.

**Individual allocation:** **unresolved**  
`out_5004_ticket_composition`: South House 14 held both deliveries; the desk did not record which supplied the truck.  
Outbound path otherwise established: manifest `RL-9127`.

---

## EVAL-PROV-001 — HFM-IN-602 (`processor_receipt_provenance`)

**Mill receipt:** established. Hearthland Feed Mill - North, dock N-1, `2025-09-05T10:50:00-05:00`, 25500 kg, silo S-5, bill `NS-5002-B`.

**Upstream dispatch / manifest:** `PGE-OUT-5002` / `NS-8848`  
`established_shipment` and BOL match (`bill_of_lading` = mill `bill_reference`). Origin label `PG-OUT-5002` aliases to `PGE-OUT-5002`.

**Inbound material identities on that dispatch:** `WB-390` and `EF-18` (hopper-named). Source bin `BIN-12`.

**Downstream processing:** established. Run `MILL-2207` started `2025-09-05T15:10:00-05:00`, output batch `FEED-2207` (grower feed).

**Unresolved allocation:** `out_5002_quantity_split` — quantity shares of WB-390 vs EF-18 on the blended truck are not recorded. Processing_run and mill_receipt are not missing.

---

## EVAL-PROV-002 — HFM-IN-604 (`processor_receipt_provenance`)

**Mill receipt:** established. HFM-N, dock N-3, `2025-09-07T13:02:00-05:00`, 18800 kg, silo S-7, bill `RL-5004-Q`.

**Upstream dispatch / source:** `PGE-OUT-5004` / manifest `RL-9127` / bin `BIN-14`. Path is in `established_shipment` (output_batch empty).

**Identified inbound load:** **not established.** Hopper names no ticket. Candidates `MCR-118` and `S-52`. `out_5004_ticket_composition` remains.

**Processing output:** **not recorded.** No `mill_process` row names `HFM-IN-604` (`processing_run_missing`). Completeness note: HFM-IN-604 has no mill run in the supplied mill_runs.

---

## EVAL-CUST-001 — WB-390 at `2025-09-04T13:10:00-05:00` (`custody_owner_at`)

**Recorded owner:** GrainLink Merchants  
**Recorded custodian (holder):** Prairie Gate Elevator

Covering event `TR-102` (title_change), interval `[2025-09-03T15:00:00-05:00, 2025-09-05T10:50:00-05:00)`, basis broker release GL-88. Query time is inside that interval (loadout of PGE-OUT-5002 is 13:15, after this timestamp).

Intake owner at intake was Willow Bend Farms; that is superseded by `TR-102` for this time.

**Caveat (not a substitute owner):** `unrecorded_ownership` — the ownership export records changes, not a guarantee that an unrecorded agreement did not exist. No other covering `ownership_event` for scope `WB-390` at this instant.

---

## EVAL-CUST-002 — EF-18 at `2025-09-03T12:00:00-05:00` (`custody_owner_at`)

**Recorded owner:** **not established** (null)  
**Recorded custodian:** **not established** (null)

No `ownership_event` has `scope_ref` matching `EF-18`. There is therefore no covering recorded title/custody interval at this timestamp.

World does show intake `ER-7729`: arrived `2025-09-03T11:05:00-05:00`, `owner_at_intake` East Fork Co-op, then `ticket_into_bin` `BM-003` at `11:28` into `BIN-12`. That is intake context, not a covering ownership_event at 12:00, so it is **not** treated as recorded owner/custodian at the query time.

`unrecorded_ownership` still applies to the export as a whole.

---

## EVAL-INSP-001 — SMP-602B (`inspection_downstream_scope`)

Sample found: tested `2025-09-05T13:10:00-05:00`, local_lot `WB390 / EF18` → identities `WB-390`, `EF-18`; material_hint names receiving slip `HFM-IN-602`; comment “combined truck sample”.

**Established affected processor receipt:** `HFM-IN-602` (hint names the mill slip).  
**Established affected processed output:** `FEED-2207` / run `MILL-2207` / grower feed.  
**Established affected downstream shipment after the sample:** **none** (mill-hint path; no later elevator loadout from the sample time).

The mill slip is the same movement as dispatch `PGE-OUT-5002` / manifest `NS-8848`, already received at `10:50` before this test.

**Attribution to individual inbound material:** **unresolved.** Combined lot names both tickets; `out_5002_quantity_split` still applies. Computation `unresolved_scope` is empty because the mill-hint path does not attach that dispatch failure; World still does not allocate WB-390 vs EF-18.

---

## EVAL-INSP-002 — SMP-604Q (`inspection_downstream_scope`)

Sample found: tested `2025-09-07T14:10:00-05:00`, local_lot `MC-118` → `MCR-118`, material_hint `South House 14 cargo` (bin alias, **not** a mill-receipt id), comment “customer hold review”.

**Established affected downstream shipment:** **none**  
**Established affected processor receipt:** **none**  
**Processed output recorded:** **no**

Why not established: hint does not name `HFM-IN-604`; loadout `PGE-OUT-5004` from `BIN-14` is at `10:30`, before the sample, and hopper did not uniquely name `MCR-118`. `BIN-14` also held `S-52` (`out_5004_ticket_composition`). Treating the mill slip or truck as affected by this sample would be an allocation guess.

**Unresolved source attribution:**
- Sampled identity `MCR-118` is established as a lot label, but not exclusively allocated to a dispatch.
- `m_creek_account`: intake grower is `M. Creek`; commercial desk claims Meadow Creek Farms and Meadow Creek Grain with no selecting account key.
- If the cargo were later joined to `HFM-IN-604`, that slip still has **no** mill_process output.

---

## EVAL-INSP-003 — SMP-UNLISTED (`inspection_downstream_scope`)

Sample found: tested `2025-09-08T09:00:00-05:00`, local_lot `N3 / EF-18?`, material_hint `route packet note`, comment `source ticket not recorded`.

**Validated downstream shipment:** **not established**  
**Validated processor receipt:** **not established**  
**Validated inbound source identity:** **not established** (`sampled_identities` empty)

**Unresolved linkage (preserve):**
- `sampled_material_identity` / `smp_unlisted_source_ticket`: source ticket was not recorded; the route-packet note is not treated as a ticket.
- Same cargo-mark string appears on manifest `NS-8910` (`PGE-OUT-5003`), which World already marks as a non-validated source (`out_5003_material_identity`). That resemblance is **not** used to bind this sample to that truck or to `EF-18`.

---

## Computation vs World

| Task | Computation result used | World override / caveat |
|---|---|---|
| EVAL-SRC-001–003 | `shipment_source_status` | Agrees with hopper, loadout, and purpose_requirement_failure rows. |
| EVAL-PROV-001–002 | `processor_receipt_provenance` | Agrees with `established_shipment` / mill_process gaps. |
| EVAL-CUST-001 | `custody_owner_at` | Agrees with covering `TR-102`. |
| EVAL-CUST-002 | `custody_owner_at` | Keep owner/custodian unresolved; do not promote `owner_at_intake`. |
| EVAL-INSP-001 | mill-hint path | Add World unresolved quantity split WB-390 / EF-18. |
| EVAL-INSP-002 | empty established_affected | Correct: do not infer HFM-IN-604 / PGE-OUT-5004 from bin hint. |
| EVAL-INSP-003 | unknown identity | Correct: do not bind `N3 / EF-18?` to PGE-OUT-5003. |
