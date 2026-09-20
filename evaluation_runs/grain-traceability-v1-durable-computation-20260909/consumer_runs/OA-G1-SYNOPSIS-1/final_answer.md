# Held-out answer set
experiment: grain-traceability-v1-durable-computation-20260909  
world_id: v0  
revision: 242  
catalog: application/catalog.json was not present in the workspace; answers are grounded in world.sqlite and world.purpose.json only.

---

## EVAL-SRC-001
family: shipment_source_status  
dispatch: PGE-OUT-5002

**Established contributing inbound material identities:** WB-390 and EF-18.

**Established source location:** North House 12 (BIN-12) at Prairie Gate Elevator. Loadout LD-19 pulled 26,000 kg from that bin onto truck NST-204. Bin move BM-004 (work order OUT-5002) names hopper note `WB-390 / EF-18` from BIN-12 into LOAD-PIT-2; `ticket_named_on_move` records both tickets on BM-004. BM-005 then places that quantity on NST-204. Carrier manifest NS-8848 / bill NS-5002-B identifies the same movement.

**Individual source allocation:** unresolved. Both named tickets are established as contributing, but no quantity split between WB-390 and EF-18 is recorded. The 26,000 kg load cannot be allocated to one inbound identity. Unexplained kilogram difference versus mill intake (26,000 kg loadout / 25,500 kg mill) is recorded and is not treated as a different movement.

---

## EVAL-SRC-002
family: shipment_source_status  
dispatch: PGE-OUT-5003

**Established source location:** North House 12 (BIN-12) at Prairie Gate Elevator. Loadout LD-20, 12,000 kg, truck NST-219, spout 2, route EAST-1. Bin move BM-006 is BIN-12 → LOAD-PIT-3 for work order OUT-5003. Carrier manifest NS-8910 / bill NS-5003-C departed to consignee HFM-E (Hearthland Feed Mill - East).

**Established inbound material identity:** none.

**Missing or unresolved source linkage:**
- Hopper note is `no ticket on hopper sheet` (BM-006). No `ticket_named_on_move` row for OUT-5003.
- Handwritten cargo mark `N3 / EF-18?` is not a validated source ticket; N3 is used as a route code elsewhere (`physical-ticket-allocation-PGE-OUT-5003`).
- No mill receiving slip is in the supplied extracts (`mill-receipt-absent-PGE-OUT-5003`). Consignee HFM-E is not a receipt. Completeness of the HFM-North receiving log does not support a conclusion about East mill receiving (`consignee_is_not_receipt` for NS-8910 / HFM-E).

---

## EVAL-SRC-003
family: shipment_source_status  
dispatch: PGE-OUT-5004

**Established contributing inbound material identities:** MCR-118 and S-52, as the two deliveries placed into the source bin before loadout (BM-007 and BM-008 into South House 14 / BIN-14). Loadout LD-21 left from South House 14, 19,000 kg, truck RLT-091; BM-009/BM-010 carry work order OUT-5004. Carrier RL-9127 / bill RL-5004-Q and mill receipt HFM-IN-604 identify the same truck movement.

**Individual allocation:** unresolved. Hopper note is `no individual ticket`. The loadout desk did not record which delivery supplied which part of the truck (`physical-ticket-allocation-PGE-OUT-5004`). Kilogram difference 19,000 kg loadout / 18,800 kg mill is recorded and unexplained; not a different movement.

---

## EVAL-PROV-001
family: processor_receipt_provenance  
processor_receipt: HFM-IN-602

**Upstream dispatch:** PGE-OUT-5002 (mill origin label PG-OUT-5002). Bill reference NS-5002-B; carrier Northstar Bulk Transport, vehicle NST-204, dock N-1, silo S-5, Hearthland Feed Mill - North, received 25,500 kg at 2025-09-05T10:50:00-05:00.

**Inbound material identities:** WB-390 and EF-18 are established as contributing on the elevator hopper / bin move for OUT-5002 (see EVAL-SRC-001). Lab sample SMP-602B on this receipt is labeled `WB390 / EF18` / combined truck sample.

**Downstream processing output:** established. Mill run MILL-2207 consumed HFM-IN-602 and produced output batch FEED-2207 (`grower feed`), started 2025-09-05T15:10:00-05:00.

**Unresolved allocation detail:** individual split between WB-390 and EF-18 is not recorded. Quantity difference 26,000 kg loadout / 25,500 kg mill is unexplained and is not treated as a different movement.

---

## EVAL-PROV-002
family: processor_receipt_provenance  
processor_receipt: HFM-IN-604

**Upstream dispatch:** PGE-OUT-5004 (origin label PG-OUT-5004). Bill RL-5004-Q; Redline Haulage truck RLT-091; HFM-North dock N-3, silo S-7; received 18,800 kg at 2025-09-07T13:02:00-05:00.

**Source status:** load originated at South House 14 (BIN-14) after MCR-118 and S-52 were both placed there. Those two inbound identities are the established contributing pool; which delivery supplied which part of the truck is unresolved (`physical-ticket-allocation-PGE-OUT-5004`).

**Identified inbound load:** established as movement PGE-OUT-5004 / bill RL-5004-Q. A single identified elevator receiving ticket for that load is not established.

**Processing output:** none recorded. No `mill_process` row has input_receipt HFM-IN-604.

---

## EVAL-CUST-001
family: custody_owner_at  
material: WB-390  
timestamp: 2025-09-04T13:10:00-05:00

**Recorded owner:** GrainLink Merchants.

**Recorded custodian (ticket-scoped):** Prairie Gate Elevator.

Grounding: ownership TR-102 is a title_change scoped to ticket WB-390, effective 2025-09-03T15:00:00-05:00 through 2025-09-05T10:50:00-05:00, owner_after GrainLink Merchants, holder_after Prairie Gate Elevator.

**Overlapping movement-scoped custody (not ticket-scoped):** TR-104 is a custody_change scoped to movement PGE-OUT-5002, effective 2025-09-04T13:05:00-05:00, owner_after GrainLink Merchants, holder_after Northstar Bulk Transport. WB-390 is established as a contributor to that movement, but TR-104 is commercially scoped to the movement, not to ticket WB-390. Commercial scope is not a bin allocation.

**Physical location at the timestamp:** LOAD-PIT-2 at Prairie Gate. BM-004 moved named `WB-390 / EF-18` into the pit at 13:02; truck load BM-005 is 13:14; loadout LD-19 is 13:15; carrier departure is 13:23. Ticket-level holder Prairie Gate is consistent with the grain still being on-site in the load pit at 13:10. Do not collapse TR-102 and TR-104 into a single ticket custodian.

---

## EVAL-CUST-002
family: custody_owner_at  
material: EF-18  
timestamp: 2025-09-03T12:00:00-05:00

**Recorded owner:** East Fork Co-op, from elevator intake ER-7729 (ticket EF-18), owner_recorded and grower_recorded at 2025-09-03T11:05:00-05:00. No later `ownership_event` is scoped to EF-18.

**Recorded custodian:** no custody_change or title_change is recorded for EF-18. Physical location at the timestamp is North House 12 (BIN-12) at Prairie Gate Elevator (BM-003 at 11:28 placed EF-18 there). Ownership export records changes only; absence of a later agreement is not proven.

---

## EVAL-INSP-001
family: inspection_downstream_scope  
sample: SMP-602B

**Downstream shipment:** PGE-OUT-5002 (established). Sample is a combined truck sample on receiving slip HFM-IN-602, which is mill intake of that dispatch (bill NS-5002-B).

**Processor receipt:** HFM-IN-602 (established). Lab local_lot `WB390 / EF18`; material_hint `receiving slip HFM-IN-602`.

**Processed output:** FEED-2207 from mill run MILL-2207 (established).

**Attribution to individual inbound material:** unresolved. The sample is labeled as a combined truck sample of WB-390 and EF-18; it is not allocated to one inbound ticket.

---

## EVAL-INSP-002
family: inspection_downstream_scope  
sample: SMP-604Q

**Downstream shipment:** PGE-OUT-5004 (established as the South House 14 cargo movement that became mill intake HFM-IN-604 / bill RL-5004-Q).

**Processor receipt:** HFM-IN-604 (established). Sample tested 2025-09-07T14:10:00-05:00, after mill receipt 13:02.

**Processed output:** none recorded.

**Unresolved source attribution:** sample is labeled South House 14 cargo / MC-118. After MCR-118 and S-52 were both placed in BIN-14, the cargo is not allocated to one delivery (`lab-sample-SMP-604Q-ticket`). Local_lot MC-118 is not a validated exclusive ticket allocation.

---

## EVAL-INSP-003
family: inspection_downstream_scope  
sample: SMP-UNLISTED

**Validated downstream shipment:** not established.

**Validated processor receipt:** not established.

**Validated inbound source identity:** not established.

**Unresolved linkage (preserved, not treated as established):** lab local_lot `N3 / EF-18?`, material_hint `route packet note`, comment `source ticket not recorded` (`lab-sample-SMP-UNLISTED-source-ticket`). The same unverified cargo mark appears on carrier departure PGE-OUT-5003 / NS-8910, where N3 is a route code and `EF-18?` is not a validated source ticket. That resemblance does not establish shipment, mill receipt, or ticket identity. PGE-OUT-5003 also has no mill intake in this World.
