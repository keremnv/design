# Grain traceability held-out answers

World: `v0` revision 242. No `application/catalog.json` was present; answers use World relations only. Ticket names on a hopper sheet establish contributing identities, not quantity allocation. Consignee codes are not mill receipts. Unsupported identity and blend allocation are left unresolved.

```json
{
  "experiment": "grain-traceability-v1-durable-computation-20260909",
  "answers": [
    {
      "task_id": "EVAL-SRC-001",
      "family": "shipment_source_status",
      "parameters": {"dispatch": "PGE-OUT-5002"},
      "established": {
        "dispatch": "PGE-OUT-5002",
        "loadout": "LD-19",
        "source_location": "North House 12 (BIN-12, Prairie Gate Elevator)",
        "contributing_inbound_identities": ["WB-390", "EF-18"],
        "hopper_move": "BM-004",
        "truck": "NST-204",
        "manifest": "NS-8848",
        "bill_of_lading": "NS-5002-B"
      },
      "unresolved": {
        "individual_source_allocation": true,
        "note": "Hopper sheet names WB-390 and EF-18 on BM-004. ticket_named_on_move is not a quantity allocation. No split of the 26,000 kg between those tickets is recorded. DR-44 was also in BIN-12 but is not named on this move and is not established as contributing."
      },
      "answer": "PGE-OUT-5002 was loaded from North House 12 (BIN-12). Established contributing inbound identities are WB-390 and EF-18. Individual source allocation between those tickets remains unresolved."
    },
    {
      "task_id": "EVAL-SRC-002",
      "family": "shipment_source_status",
      "parameters": {"dispatch": "PGE-OUT-5003"},
      "established": {
        "dispatch": "PGE-OUT-5003",
        "loadout": "LD-20",
        "source_location": "North House 12 (BIN-12, Prairie Gate Elevator)",
        "inbound_material_identity": null,
        "truck": "NST-219",
        "manifest": "NS-8910",
        "bill_of_lading": "NS-5003-C",
        "consignee_code": "HFM-E"
      },
      "unresolved": {
        "inbound_source_ticket": true,
        "handwritten_cargo_mark": "N3 / EF-18?",
        "mill_receipt": "absent",
        "purpose_failures": [
          "physical-ticket-allocation-PGE-OUT-5003",
          "mill-receipt-absent-PGE-OUT-5003"
        ],
        "note": "Hopper BM-006 records no ticket on hopper sheet. Handwritten cargo mark N3 / EF-18? is not a validated source ticket; N3 is a route code elsewhere. Consignee HFM-E is not a receiving slip. No mill_intake is recorded. HFM-North log completeness does not support a conclusion about East mill receiving."
      },
      "answer": "PGE-OUT-5003 left from North House 12. No inbound material identity is established. Source-ticket linkage is unresolved (unnamed hopper; unvalidated cargo mark N3 / EF-18?). No mill receiving slip is established."
    },
    {
      "task_id": "EVAL-SRC-003",
      "family": "shipment_source_status",
      "parameters": {"dispatch": "PGE-OUT-5004"},
      "established": {
        "dispatch": "PGE-OUT-5004",
        "loadout": "LD-21",
        "source_location": "South House 14 (BIN-14, Prairie Gate Elevator)",
        "contributing_inbound_identities": ["MCR-118", "S-52"],
        "truck": "RLT-091",
        "manifest": "RL-9127",
        "bill_of_lading": "RL-5004-Q"
      },
      "unresolved": {
        "individual_source_allocation": true,
        "purpose_failure": "physical-ticket-allocation-PGE-OUT-5004",
        "note": "MCR-118 and S-52 were both placed in South House 14 before LD-21. Hopper BM-009 records no individual ticket. The loadout desk did not record which delivery supplied which part of the 19,000 kg truck. Grower identity of MCR-118 (M. Creek vs Meadow Creek Farms vs Meadow Creek Grain) remains separately unresolved and is not required to name the ticket."
      },
      "answer": "Established contributing inbound identities are MCR-118 and S-52 (the deliveries placed in South House 14 before loadout). Individual allocation is not resolved."
    },
    {
      "task_id": "EVAL-PROV-001",
      "family": "processor_receipt_provenance",
      "parameters": {"processor_receipt": "HFM-IN-602"},
      "established": {
        "processor_receipt": "HFM-IN-602",
        "upstream_dispatch": "PGE-OUT-5002",
        "bill_reference": "NS-5002-B",
        "mill_site": "Hearthland Feed Mill - North",
        "silo": "S-5",
        "inbound_material_identities": ["WB-390", "EF-18"],
        "processing_run": "MILL-2207",
        "processed_output": "FEED-2207",
        "output_name": "grower feed"
      },
      "unresolved": {
        "individual_source_allocation": true,
        "quantity_difference": "26000 kg loadout / 25500 kg mill intake",
        "note": "Bill-of-lading identity of the truck movement is established. The kilogram difference is recorded and unexplained; it is not a different movement. Combined truck sample SMP-602B labels WB390 / EF18 and does not allocate to one ticket."
      },
      "answer": "HFM-IN-602 is the North mill receiving slip for upstream dispatch PGE-OUT-5002 (NS-5002-B). Inbound identities established as contributing are WB-390 and EF-18. Downstream processing output is FEED-2207 (MILL-2207, grower feed). Individual allocation between WB-390 and EF-18 remains unresolved."
    },
    {
      "task_id": "EVAL-PROV-002",
      "family": "processor_receipt_provenance",
      "parameters": {"processor_receipt": "HFM-IN-604"},
      "established": {
        "processor_receipt": "HFM-IN-604",
        "upstream_dispatch": "PGE-OUT-5004",
        "bill_reference": "RL-5004-Q",
        "mill_site": "Hearthland Feed Mill - North",
        "silo": "S-7",
        "source_location": "South House 14 (BIN-14)",
        "identified_inbound_load": "PGE-OUT-5004 / RL-5004-Q",
        "processing_output_recorded": false
      },
      "unresolved": {
        "individual_inbound_ticket": true,
        "source_status": "South House 14 cargo after MCR-118 and S-52 were both placed in BIN-14; hopper named no individual ticket",
        "processing_output": "no mill_process row for HFM-IN-604",
        "quantity_difference": "19000 kg loadout / 18800 kg mill intake"
      },
      "answer": "Upstream dispatch is PGE-OUT-5004. Source status is South House 14 with contributing tickets MCR-118 and S-52 unallocated. An identified inbound load (the PGE-OUT-5004 / RL-5004-Q truck) is established; an identified single inbound receiving ticket is not. No processing output is recorded."
    },
    {
      "task_id": "EVAL-CUST-001",
      "family": "custody_owner_at",
      "parameters": {"material": "WB-390", "timestamp": "2025-09-04T13:10:00-05:00"},
      "established": {
        "material": "WB-390",
        "timestamp": "2025-09-04T13:10:00-05:00",
        "owner": "GrainLink Merchants",
        "custodian_ticket_scoped": "Prairie Gate Elevator",
        "ownership_record": "TR-102",
        "record_window": "2025-09-03T15:00:00-05:00 to 2025-09-05T10:50:00-05:00",
        "physical_note": "BM-004 at 13:02 named WB-390 / EF-18 from BIN-12 into LOAD-PIT-2 for OUT-5002; BM-005 onto NST-204 is 13:14"
      },
      "unresolved": {
        "ticket_level_carrier_custody": true,
        "note": "TR-104 is a custody_change scoped commercially to movement PGE-OUT-5002 (not to ticket WB-390), effective 13:05, holder_after Northstar Bulk Transport, owner_after GrainLink Merchants. Because OUT-5002 is a named blend of WB-390 and EF-18 without quantity allocation, Northstar custody is established for the movement, not as an individual-ticket custodian of WB-390. TR-102 continues to record Prairie Gate as holder of WB-390 until mill dock scan HFM-IN-602."
      },
      "answer": "At 2025-09-04T13:10:00-05:00 the recorded owner of WB-390 is GrainLink Merchants. The recorded ticket-scoped custodian/holder is Prairie Gate Elevator (TR-102). Movement-level custody of PGE-OUT-5002 is recorded to Northstar Bulk Transport from 13:05 (TR-104) and is not treated as resolved individual custody of WB-390."
    },
    {
      "task_id": "EVAL-CUST-002",
      "family": "custody_owner_at",
      "parameters": {"material": "EF-18", "timestamp": "2025-09-03T12:00:00-05:00"},
      "established": {
        "material": "EF-18",
        "timestamp": "2025-09-03T12:00:00-05:00",
        "owner": "East Fork Co-op",
        "custodian": "Prairie Gate Elevator",
        "basis": "elevator_intake ER-7729 at 2025-09-03T11:05:00-05:00 with owner_recorded East Fork Co-op; BM-003 into North House 12 at 11:28. No ownership_event is scoped to EF-18."
      },
      "unresolved": {
        "unrecorded_agreements": "ownership_export records changes only; it does not prove an unrecorded title agreement did not exist",
        "note": "No title_change or custody_change is recorded against EF-18. Later OUT-5002 custody events (TR-104/TR-105) are not yet effective at this timestamp and are scoped to the movement, not this ticket."
      },
      "answer": "At 2025-09-03T12:00:00-05:00 the recorded owner of EF-18 is East Fork Co-op and the recorded custodian is Prairie Gate Elevator."
    },
    {
      "task_id": "EVAL-INSP-001",
      "family": "inspection_downstream_scope",
      "parameters": {"sample": "SMP-602B"},
      "established": {
        "sample": "SMP-602B",
        "material_hint": "receiving slip HFM-IN-602",
        "local_lot": "WB390 / EF18",
        "downstream_shipment": "PGE-OUT-5002",
        "processor_receipt": "HFM-IN-602",
        "processed_output": "FEED-2207",
        "processing_run": "MILL-2207"
      },
      "unresolved": {
        "attribution_to_individual_inbound_material": true,
        "note": "Lab comment is combined truck sample. Hopper names WB-390 and EF-18 without quantity allocation."
      },
      "answer": "SMP-602B is established as the combined truck sample on HFM-IN-602, which is PGE-OUT-5002. Downstream processed output FEED-2207 (MILL-2207) is established. Attribution to an individual inbound ticket (WB-390 vs EF-18) is not resolved."
    },
    {
      "task_id": "EVAL-INSP-002",
      "family": "inspection_downstream_scope",
      "parameters": {"sample": "SMP-604Q"},
      "established": {
        "sample": "SMP-604Q",
        "material_hint": "South House 14 cargo",
        "downstream_shipment": "PGE-OUT-5004",
        "processor_receipt": "HFM-IN-604",
        "processed_output_recorded": false
      },
      "unresolved": {
        "source_attribution": "MCR-118 versus S-52",
        "purpose_failure": "lab-sample-SMP-604Q-ticket",
        "processed_output": "no mill_process for HFM-IN-604",
        "note": "Sample is labeled South House 14 cargo / MC-118. After MCR-118 and S-52 were both placed in BIN-14, the cargo is not allocated to one delivery. The MC-118 / MCR-118 lot label is not a validated single-ticket attribution."
      },
      "answer": "SMP-604Q is established as affecting downstream shipment PGE-OUT-5004 and processor receipt HFM-IN-604. No processed output is recorded. Source attribution to an individual inbound ticket remains unresolved (South House 14 blend of MCR-118 and S-52)."
    },
    {
      "task_id": "EVAL-INSP-003",
      "family": "inspection_downstream_scope",
      "parameters": {"sample": "SMP-UNLISTED"},
      "established": {
        "sample": "SMP-UNLISTED",
        "lab_ticket": "LAB-4428",
        "validated_downstream_shipment": null,
        "validated_processor_receipt": null,
        "validated_inbound_source_identity": null
      },
      "unresolved": {
        "source_ticket": true,
        "purpose_failure": "lab-sample-SMP-UNLISTED-source-ticket",
        "recorded_but_unvalidated": {
          "local_lot": "N3 / EF-18?",
          "material_hint": "route packet note"
        },
        "note": "Source ticket is not recorded. Route packet note is not a validated source ticket. The same unverified string appears as cargo_mark on PGE-OUT-5003; that match does not establish a shipment, mill receipt, or EF-18 identity. No mill_intake exists for PGE-OUT-5003."
      },
      "answer": "No validated downstream shipment, processor receipt, or inbound source identity is established for SMP-UNLISTED. Linkage via the route packet note N3 / EF-18? remains unresolved."
    }
  ]
}
```
