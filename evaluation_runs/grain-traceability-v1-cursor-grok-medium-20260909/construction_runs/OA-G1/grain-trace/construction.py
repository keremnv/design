"""Construct a purpose-fit grain-trace World from workspace evidence."""

from __future__ import annotations

import json
import re

from ontology_author.world.core.model import Role, RoleType, RelationMode
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation


NOTES = "evidence/operating_notes.md"
INTAKES = "evidence/elevator_receipts.csv"
MOVES = "evidence/bin_movements.csv"
LOADOUTS = "evidence/loadout_log.csv"
MANIFESTS = "evidence/carrier_manifests.json"
OWNERSHIP = "evidence/ownership_records.csv"
INSPECTIONS = "evidence/inspection_results.csv"
PROCESSOR = "evidence/processor_receipts.json"

TICKET_TOKEN = re.compile(r"\b(?:DR-44|WB-390|EF-18|MCR-118|S-52)\b")


def construct(source, world, purpose) -> None:
    purpose.require(
        "trace-grain-flow",
        note="Trace receiving, storage, processing, and outbound shipment when evidence establishes the links.",
    )

    rt = lambda name: Role(name, RoleType.TEXT)
    rr = lambda name: Role(name, RoleType.REFERENT)

    world.declare_relation(
        "known_as",
        [rr("entity"), rt("token"), rt("system")],
        description="A recorded identifier used for an entity in one evidence system.",
    )
    world.declare_relation(
        "location",
        [rr("place"), rr("site"), rt("kind"), rt("local_name")],
        description="A physical place used in receiving, storage, loadout, or mill handling.",
    )
    world.declare_relation(
        "elevator_intake",
        [
            rr("ticket"),
            rt("receipt_no"),
            rr("site"),
            rt("grower_recorded"),
            rt("commodity"),
            rt("net_kg"),
            rr("lane"),
            rr("assigned_bin"),
            rt("owner_recorded"),
            rt("arrived_at"),
            rt("grade_note"),
        ],
        description="Prairie Gate scale ticket at the receiving lane.",
    )
    world.declare_relation(
        "bin_transfer",
        [
            rr("move"),
            rr("from_place"),
            rr("to_place"),
            rt("material_note"),
            rt("quantity_kg"),
            rt("work_order"),
            rt("logged_at"),
        ],
        description="Bin-crew hopper or house movement as logged.",
    )
    world.declare_relation(
        "ticket_named_on_move",
        [rr("ticket"), rr("move"), rt("note_span")],
        description="A scale ticket token written on a hopper sheet. Not a quantity allocation.",
    )
    world.declare_relation(
        "elevator_loadout",
        [
            rr("loadout"),
            rr("movement"),
            rr("bin"),
            rr("truck"),
            rt("dispatch_ref"),
            rt("quantity_kg"),
            rt("spout"),
            rt("route_code"),
            rt("loaded_at"),
            rt("desk_comment"),
        ],
        description="Elevator spout loadout identifying bin and truck, not ticket allocation.",
    )
    world.declare_relation(
        "carrier_departure",
        [
            rr("manifest"),
            rr("movement"),
            rr("carrier"),
            rr("vehicle"),
            rt("cargo_mark"),
            rt("bill_of_lading"),
            rt("consignee_code"),
            rt("consignee_name"),
            rr("pickup_site"),
            rt("weight_kg"),
            rt("departed_at"),
            rt("route_note"),
        ],
        description="Carrier manifest as the departure record for a truck movement.",
    )
    world.declare_relation(
        "mill_intake",
        [
            rr("receipt"),
            rr("movement"),
            rr("site"),
            rt("dock"),
            rt("bill_reference"),
            rt("origin_label"),
            rt("received_kg"),
            rt("silo"),
            rt("commodity"),
            rt("received_at"),
        ],
        description="Local mill receiving slip created when a truck is accepted at a dock.",
    )
    world.declare_relation(
        "mill_process",
        [
            rr("run"),
            rr("input_receipt"),
            rr("output_batch"),
            rt("output_name"),
            rt("started_at"),
        ],
        description="Mill run consuming a local receiving slip into an output batch.",
    )
    world.declare_relation(
        "lab_result",
        [
            rr("sample"),
            rt("tested_at"),
            rt("lab_ticket"),
            rt("local_lot"),
            rt("material_hint"),
            rt("test_name"),
            rt("result"),
            rt("unit"),
            rt("comment"),
        ],
        description="Lab test as recorded, including unvalidated lot labels.",
    )
    world.declare_relation(
        "ownership_event",
        [
            rr("record"),
            rt("record_type"),
            rt("scope_ref"),
            rt("effective_start"),
            rt("effective_end"),
            rt("from_party"),
            rt("to_party"),
            rt("owner_after"),
            rt("holder_after"),
            rt("basis"),
            rt("recorded_at"),
        ],
        description="Recorded title, custody, or party-claim event. Not a claim that unrecorded agreements are absent.",
    )
    world.declare_relation(
        "commercial_scope",
        [rr("record"), rr("scoped"), rt("scope_kind")],
        description="Entity the ownership desk used as the scope of a recorded event.",
    )
    world.declare_relation(
        "extract_coverage",
        [rt("collection"), rt("coverage_claim")],
        description="Stated completeness or boundedness of a supplied extract.",
    )
    world.declare_relation(
        "consignee_is_not_receipt",
        [rr("manifest"), rt("consignee_code")],
        description="Carrier consignee code is a destination code, not a mill receiving slip.",
    )

    def obs(path: str, loc: str) -> SourceObservation:
        return source.observation(path, loc)

    def ground(*observations: SourceObservation, method: str = "mechanical") -> AssertionGrounding:
        return AssertionGrounding(observations=observations, construction_method=method)

    def add(entity: str, label: str, *observations: SourceObservation) -> str:
        return world.add_referent(entity, label=label, observations=observations)

    def known(entity: str, token: str, system: str, g: AssertionGrounding, origin=ConstructionOrigin.MECHANICAL) -> None:
        world.assert_tuple(
            "known_as",
            {"entity": entity, "token": token, "system": system},
            origin=origin,
            grounding=g,
        )

    def put(relation: str, values: dict, g: AssertionGrounding, origin=ConstructionOrigin.MECHANICAL) -> None:
        world.assert_tuple(relation, values, origin=origin, grounding=g)

    # --- sites, houses, mills -------------------------------------------------
    pg = "site:prairie-gate"
    hfm_n = "site:hfm-north"
    hfm_e = "site:hfm-east"
    add(pg, "Prairie Gate Elevator", obs(NOTES, "L8"), obs(MANIFESTS, "pickup_site=PG-ELEV"))
    add(hfm_n, "Hearthland Feed Mill - North", obs(NOTES, "L10"), obs(PROCESSOR, "site_directory.HFM-N"))
    add(hfm_e, "Hearthland Feed Mill - East", obs(NOTES, "L10"), obs(PROCESSOR, "site_directory.HFM-E"))
    known(pg, "PG-ELEV", "carrier_pickup_site", ground(obs(NOTES, "L8"), obs(MANIFESTS, "pickup_site=PG-ELEV")), ConstructionOrigin.SEMANTIC)
    known(pg, "Prairie Gate", "operating_notes", ground(obs(NOTES, "L8")), ConstructionOrigin.SEMANTIC)
    known(pg, "Prairie Gate Elevator", "ownership_records", ground(obs(OWNERSHIP, "to_party=Prairie Gate Elevator")), ConstructionOrigin.MECHANICAL)
    known(hfm_n, "HFM-N", "consignee_and_site_directory", ground(obs(NOTES, "L10"), obs(PROCESSOR, "site_directory.HFM-N")), ConstructionOrigin.SEMANTIC)
    known(hfm_e, "HFM-E", "consignee_and_site_directory", ground(obs(NOTES, "L10"), obs(PROCESSOR, "site_directory.HFM-E")), ConstructionOrigin.SEMANTIC)

    processor = json.loads(source.read_text(PROCESSOR))
    put(
        "extract_coverage",
        {
            "collection": "HFM-North receiving_log",
            "coverage_claim": "Receiving log supplied for HFM-North is complete for 2025-09-05 through 2025-09-07. No conclusion about other HFM sites follows from its absence.",
        },
        ground(obs(NOTES, "L17"), method="notes-completeness"),
        ConstructionOrigin.SEMANTIC,
    )

    bin12 = "bin:north-house-12"
    bin14 = "bin:south-house-14"
    add(bin12, "North House 12", obs(NOTES, "L9"), obs(INTAKES, "assigned_bin=B-12"), obs(MOVES, "to_point=BIN-12"))
    add(bin14, "South House 14", obs(NOTES, "L9"), obs(INTAKES, "assigned_bin=B-14"), obs(MOVES, "to_point=BIN-14"))
    for token, system, loc in (
        ("BIN-12", "bin_system", "L9"),
        ("North House 12", "elevator_desk", "L9"),
        ("B-12", "scale_assigned_bin", "assigned_bin=B-12"),
    ):
        path = NOTES if loc.startswith("L") else INTAKES
        known(bin12, token, system, ground(obs(path, loc)), ConstructionOrigin.SEMANTIC if path == NOTES else ConstructionOrigin.MECHANICAL)
    for token, system, loc in (
        ("BIN-14", "bin_system", "L9"),
        ("South House 14", "elevator_desk", "L9"),
        ("B-14", "scale_assigned_bin", "assigned_bin=B-14"),
    ):
        path = NOTES if loc.startswith("L") else INTAKES
        known(bin14, token, system, ground(obs(path, loc)), ConstructionOrigin.SEMANTIC if path == NOTES else ConstructionOrigin.MECHANICAL)

    put("location", {"place": bin12, "site": pg, "kind": "bin", "local_name": "North House 12"}, ground(obs(NOTES, "L9"), obs(LOADOUTS, "bin_label=North House 12")), ConstructionOrigin.SEMANTIC)
    put("location", {"place": bin14, "site": pg, "kind": "bin", "local_name": "South House 14"}, ground(obs(NOTES, "L9"), obs(LOADOUTS, "bin_label=South House 14")), ConstructionOrigin.SEMANTIC)

    lanes = {
        "Lane 1": "lane:intake-1",
        "Lane 2": "lane:intake-2",
        "Lane 3": "lane:intake-3",
        "INTAKE-1": "lane:intake-1",
        "INTAKE-2": "lane:intake-2",
        "INTAKE-3": "lane:intake-3",
    }
    add("lane:intake-1", "Intake / Lane 1", obs(INTAKES, "receiving_lane=Lane 1"), obs(MOVES, "from_point=INTAKE-1"))
    add("lane:intake-2", "Intake / Lane 2", obs(INTAKES, "receiving_lane=Lane 2"), obs(MOVES, "from_point=INTAKE-2"))
    add("lane:intake-3", "Intake / Lane 3", obs(INTAKES, "receiving_lane=Lane 3"), obs(MOVES, "from_point=INTAKE-3"))
    for token, entity in lanes.items():
        path = INTAKES if token.startswith("Lane") else MOVES
        field = "receiving_lane" if token.startswith("Lane") else "from_point"
        known(entity, token, "receiving_or_bin", ground(obs(path, f"{field}={token}")))
        put("location", {"place": entity, "site": pg, "kind": "intake_lane", "local_name": token}, ground(obs(path, f"{field}={token}")), ConstructionOrigin.SEMANTIC)

    pits = {
        "LOAD-PIT-1": "pit:load-1",
        "LOAD-PIT-2": "pit:load-2",
        "LOAD-PIT-3": "pit:load-3",
    }
    for token, entity in pits.items():
        add(entity, token, obs(MOVES, f"to_point={token}"))
        known(entity, token, "bin_system", ground(obs(MOVES, f"to_point={token}")))
        put("location", {"place": entity, "site": pg, "kind": "load_pit", "local_name": token}, ground(obs(MOVES, f"to_point={token}")))

    silos = {"S-4": "silo:s-4", "S-5": "silo:s-5", "S-7": "silo:s-7"}
    for token, entity in silos.items():
        add(entity, token, obs(PROCESSOR, f"receiving_log.silo={token}"))
        known(entity, token, "hfm_north_silo", ground(obs(PROCESSOR, f"receiving_log.silo={token}")))
        put("location", {"place": entity, "site": hfm_n, "kind": "silo", "local_name": token}, ground(obs(PROCESSOR, f"receiving_log.silo={token}")))

    trucks = {
        "RLT-088": "truck:rlt-088",
        "NST-204": "truck:nst-204",
        "NST-219": "truck:nst-219",
        "RLT-091": "truck:rlt-091",
        "TRUCK-NS204": "truck:nst-204",
        "TRUCK-RL091": "truck:rlt-091",
    }
    add("truck:rlt-088", "RLT-088", obs(LOADOUTS, "truck_tag=RLT-088"), obs(MANIFESTS, "vehicle=RLT-088"))
    add("truck:nst-204", "NST-204", obs(LOADOUTS, "truck_tag=NST-204"), obs(MOVES, "to_point=TRUCK-NS204"))
    add("truck:nst-219", "NST-219", obs(LOADOUTS, "truck_tag=NST-219"), obs(MANIFESTS, "vehicle=NST-219"))
    add("truck:rlt-091", "RLT-091", obs(LOADOUTS, "truck_tag=RLT-091"), obs(MOVES, "to_point=TRUCK-RL091"))
    for token, entity in trucks.items():
        if token.startswith("TRUCK-"):
            known(entity, token, "bin_system", ground(obs(MOVES, f"to_point={token}")), ConstructionOrigin.SEMANTIC)
        else:
            known(entity, token, "loadout_or_carrier", ground(obs(LOADOUTS, f"truck_tag={token}")), ConstructionOrigin.MECHANICAL)

    carriers = {
        "Redline Haulage": "party:redline-haulage",
        "Northstar Bulk Transport": "party:northstar-bulk-transport",
    }
    for name, entity in carriers.items():
        add(entity, name, obs(MANIFESTS, f"carrier={name}"))
        known(entity, name, "carrier_manifest", ground(obs(MANIFESTS, f"carrier={name}")))

    tickets = {
        "DR-44": "ticket:dr-44",
        "WB-390": "ticket:wb-390",
        "EF-18": "ticket:ef-18",
        "MCR-118": "ticket:mcr-118",
        "S-52": "ticket:s-52",
    }
    for token, entity in tickets.items():
        add(entity, token, obs(INTAKES, f"scale_ticket={token}"))
        known(entity, token, "scale_ticket", ground(obs(INTAKES, f"scale_ticket={token}")))
    known("ticket:dr-44", "DR44", "lab_local_lot", ground(obs(INSPECTIONS, "sample_no=SMP-7714A")), ConstructionOrigin.SEMANTIC)
    known("ticket:wb-390", "WB390", "lab_local_lot", ground(obs(INSPECTIONS, "sample_no=SMP-602B")), ConstructionOrigin.SEMANTIC)
    known("ticket:mcr-118", "MC-118", "lab_local_lot", ground(obs(INSPECTIONS, "sample_no=SMP-604Q")), ConstructionOrigin.SEMANTIC)

    # --- intakes --------------------------------------------------------------
    lane_by_label = {"Lane 1": "lane:intake-1", "Lane 2": "lane:intake-2", "Lane 3": "lane:intake-3"}
    bin_by_assigned = {"B-12": bin12, "B-14": bin14}
    for row in source.rows(INTAKES):
        ticket_token = row["scale_ticket"]
        ticket = tickets[ticket_token]
        assigned = bin_by_assigned[row["assigned_bin"]]
        lane = lane_by_label[row["receiving_lane"]]
        loc = f"scale_ticket={ticket_token}"
        put(
            "elevator_intake",
            {
                "ticket": ticket,
                "receipt_no": row["receipt_no"],
                "site": pg,
                "grower_recorded": row["grower_name"],
                "commodity": row["commodity"],
                "net_kg": row["net_kg"],
                "lane": lane,
                "assigned_bin": assigned,
                "owner_recorded": row["owner_at_intake"],
                "arrived_at": row["arrival_local"],
                "grade_note": row["grade_note"],
            },
            ground(obs(INTAKES, loc)),
        )
        known(ticket, row["receipt_no"], "elevator_receipt_no", ground(obs(INTAKES, loc)))

    # --- bin transfers --------------------------------------------------------
    place = {
        "INTAKE-1": "lane:intake-1",
        "INTAKE-2": "lane:intake-2",
        "INTAKE-3": "lane:intake-3",
        "BIN-12": bin12,
        "BIN-14": bin14,
        "LOAD-PIT-1": "pit:load-1",
        "LOAD-PIT-2": "pit:load-2",
        "LOAD-PIT-3": "pit:load-3",
        "TRUCK-NS204": "truck:nst-204",
        "TRUCK-RL091": "truck:rlt-091",
    }
    for row in source.rows(MOVES):
        move = f"move:{row['move_id']}"
        add(move, row["move_id"], obs(MOVES, f"move_id={row['move_id']}"))
        known(move, row["move_id"], "bin_move_id", ground(obs(MOVES, f"move_id={row['move_id']}")))
        put(
            "bin_transfer",
            {
                "move": move,
                "from_place": place[row["from_point"]],
                "to_place": place[row["to_point"]],
                "material_note": row["material_note"],
                "quantity_kg": row["quantity_kg"],
                "work_order": row["work_order"],
                "logged_at": row["logged_at"],
            },
            ground(obs(MOVES, f"move_id={row['move_id']}")),
        )
        note = row["material_note"]
        if "not confirmed" in note.lower() or "EF-18?" in note:
            continue
        for token in TICKET_TOKEN.findall(note):
            put(
                "ticket_named_on_move",
                {"ticket": tickets[token], "move": move, "note_span": token},
                ground(obs(MOVES, f"move_id={row['move_id']}"), obs(NOTES, "L14")),
                ConstructionOrigin.SEMANTIC,
            )

    # --- movements from loadout desk -----------------------------------------
    movements = {}
    bin_by_label = {"North House 12": bin12, "South House 14": bin14}
    for row in source.rows(LOADOUTS):
        dispatch = row["dispatch_ref"]
        movement = f"movement:{dispatch}"
        movements[dispatch] = movement
        loadout = f"loadout:{row['dispatch_id']}"
        add(movement, dispatch, obs(LOADOUTS, f"dispatch_id={row['dispatch_id']}"), obs(NOTES, "L10"))
        add(loadout, row["dispatch_id"], obs(LOADOUTS, f"dispatch_id={row['dispatch_id']}"))
        known(movement, dispatch, "elevator_dispatch", ground(obs(LOADOUTS, f"dispatch_ref={dispatch}")), ConstructionOrigin.MECHANICAL)
        known(loadout, row["dispatch_id"], "loadout_dispatch_id", ground(obs(LOADOUTS, f"dispatch_id={row['dispatch_id']}")))
        mill_origin = dispatch.replace("PGE-OUT-", "PG-OUT-")
        mill_origins = {item["origin_label"] for item in processor["receiving_log"]}
        if mill_origin in mill_origins:
            known(
                movement,
                mill_origin,
                "mill_origin_label",
                ground(obs(NOTES, "L10"), obs(PROCESSOR, f"origin_label={mill_origin}")),
                ConstructionOrigin.SEMANTIC,
            )
        wo = dispatch.replace("PGE-", "")
        wo_values = {item["work_order"] for item in source.rows(MOVES)}
        if wo in wo_values:
            known(
                movement,
                wo,
                "bin_work_order",
                ground(obs(NOTES, "L10"), obs(MOVES, f"work_order={wo}")),
                ConstructionOrigin.SEMANTIC,
            )
        put(
            "elevator_loadout",
            {
                "loadout": loadout,
                "movement": movement,
                "bin": bin_by_label[row["bin_label"]],
                "truck": trucks[row["truck_tag"]],
                "dispatch_ref": dispatch,
                "quantity_kg": row["quantity_kg"],
                "spout": row["spout"],
                "route_code": row["route_code"],
                "loaded_at": row["loaded_at"],
                "desk_comment": row["desk_comment"],
            },
            ground(obs(LOADOUTS, f"dispatch_id={row['dispatch_id']}")),
        )

    # --- carrier departures ---------------------------------------------------
    cargo_to_movement = {
        "PGE-OUT-5001": "PGE-OUT-5001",
        "PGE-OUT-5002": "PGE-OUT-5002",
        "PGE-OUT-5004": "PGE-OUT-5004",
    }
    for row in source.rows(MANIFESTS):
        manifest = f"manifest:{row['manifest_no']}"
        add(manifest, row["manifest_no"], obs(MANIFESTS, f"manifest_no={row['manifest_no']}"))
        known(manifest, row["manifest_no"], "manifest_no", ground(obs(MANIFESTS, f"manifest_no={row['manifest_no']}")))
        known(manifest, row["bill_of_lading"], "bill_of_lading", ground(obs(MANIFESTS, f"manifest_no={row['manifest_no']}")))
        cargo = row["cargo_mark"]
        if cargo in cargo_to_movement:
            movement = movements[cargo_to_movement[cargo]]
            method = "cargo_mark matches elevator dispatch_ref"
            origin = ConstructionOrigin.SEMANTIC
            g = ground(
                obs(MANIFESTS, f"manifest_no={row['manifest_no']}"),
                obs(LOADOUTS, f"dispatch_ref={cargo}"),
                obs(NOTES, "L16"),
                method=method,
            )
        elif row["manifest_no"] == "NS-8910":
            movement = movements["PGE-OUT-5003"]
            origin = ConstructionOrigin.SEMANTIC
            g = ground(
                obs(MANIFESTS, "manifest_no=NS-8910"),
                obs(LOADOUTS, "dispatch_ref=PGE-OUT-5003"),
                obs(NOTES, "L22"),
                method="notes identify 12000 kg PGE-OUT-5003 with a carrier manifest; vehicle NST-219 and weight match loadout LD-20",
            )
        else:
            raise ConstructionError(f"unlinked manifest {row['manifest_no']}")
        put(
            "carrier_departure",
            {
                "manifest": manifest,
                "movement": movement,
                "carrier": carriers[row["carrier"]],
                "vehicle": trucks[row["vehicle"]],
                "cargo_mark": cargo,
                "bill_of_lading": row["bill_of_lading"],
                "consignee_code": row["consignee_code"],
                "consignee_name": row["consignee_name"],
                "pickup_site": pg,
                "weight_kg": str(row["weight_kg"]),
                "departed_at": row["departed_local"],
                "route_note": str(row.get("route_note") or ""),
            },
            g,
            origin,
        )
        put(
            "consignee_is_not_receipt",
            {"manifest": manifest, "consignee_code": row["consignee_code"]},
            ground(obs(NOTES, "L10"), obs(MANIFESTS, f"manifest_no={row['manifest_no']}")),
            ConstructionOrigin.SEMANTIC,
        )

    # --- mill receiving and processing ----------------------------------------
    bol_to_movement = {
        "RL-5001-A": movements["PGE-OUT-5001"],
        "NS-5002-B": movements["PGE-OUT-5002"],
        "RL-5004-Q": movements["PGE-OUT-5004"],
    }
    for row in processor["receiving_log"]:
        receipt = f"mill-receipt:{row['local_receipt']}"
        add(receipt, row["local_receipt"], obs(PROCESSOR, f"local_receipt={row['local_receipt']}"))
        known(receipt, row["local_receipt"], "hfm_local_receipt", ground(obs(PROCESSOR, f"local_receipt={row['local_receipt']}")))
        movement = bol_to_movement[row["bill_reference"]]
        # North dock codes in this extract
        put(
            "mill_intake",
            {
                "receipt": receipt,
                "movement": movement,
                "site": hfm_n,
                "dock": row["dock"],
                "bill_reference": row["bill_reference"],
                "origin_label": row["origin_label"],
                "received_kg": str(row["received_kg"]),
                "silo": row["silo"],
                "commodity": row["commodity"],
                "received_at": row["received_at"],
            },
            ground(
                obs(PROCESSOR, f"local_receipt={row['local_receipt']}"),
                obs(MANIFESTS, f"bill_of_lading={row['bill_reference']}"),
                obs(NOTES, "L16"),
                method="mill slip joins carrier bill_of_lading; mill creates a new local receipt",
            ),
            ConstructionOrigin.SEMANTIC,
        )

    for row in processor["mill_runs"]:
        run = f"mill-run:{row['run_no']}"
        batch = f"batch:{row['output_batch']}"
        add(run, row["run_no"], obs(PROCESSOR, f"run_no={row['run_no']}"))
        add(batch, row["output_batch"], obs(PROCESSOR, f"output_batch={row['output_batch']}"))
        known(run, row["run_no"], "mill_run_no", ground(obs(PROCESSOR, f"run_no={row['run_no']}")))
        known(batch, row["output_batch"], "mill_output_batch", ground(obs(PROCESSOR, f"output_batch={row['output_batch']}")))
        for local in row["input_receipts"]:
            put(
                "mill_process",
                {
                    "run": run,
                    "input_receipt": f"mill-receipt:{local}",
                    "output_batch": batch,
                    "output_name": row["output_name"],
                    "started_at": row["started_at"],
                },
                ground(obs(PROCESSOR, f"run_no={row['run_no']}")),
            )

    # --- lab ------------------------------------------------------------------
    for row in source.rows(INSPECTIONS):
        sample = f"sample:{row['sample_no']}"
        add(sample, row["sample_no"], obs(INSPECTIONS, f"sample_no={row['sample_no']}"))
        known(sample, row["sample_no"], "sample_no", ground(obs(INSPECTIONS, f"sample_no={row['sample_no']}")))
        put(
            "lab_result",
            {
                "sample": sample,
                "tested_at": row["tested_at"],
                "lab_ticket": row["lab_ticket"],
                "local_lot": row["local_lot"],
                "material_hint": row["material_hint"],
                "test_name": row["test_name"],
                "result": row["result"],
                "unit": row["unit"],
                "comment": row["comment"],
            },
            ground(obs(INSPECTIONS, f"sample_no={row['sample_no']}")),
        )

    # --- ownership ------------------------------------------------------------
    scope_map = {
        "DR-44": ("ticket:dr-44", "ticket"),
        "WB-390": ("ticket:wb-390", "ticket"),
        "MCR-118": ("ticket:mcr-118", "ticket"),
        "OUT-5002": ("movement:PGE-OUT-5002", "movement"),
    }
    for row in source.rows(OWNERSHIP):
        rec = f"ownership:{row['record_no']}"
        add(rec, row["record_no"], obs(OWNERSHIP, f"record_no={row['record_no']}"))
        known(rec, row["record_no"], "ownership_record_no", ground(obs(OWNERSHIP, f"record_no={row['record_no']}")))
        put(
            "ownership_event",
            {
                "record": rec,
                "record_type": row["record_type"],
                "scope_ref": row["scope_ref"],
                "effective_start": row["effective_start"],
                "effective_end": row["effective_end"] or "",
                "from_party": row["from_party"],
                "to_party": row["to_party"],
                "owner_after": row["owner_after"],
                "holder_after": row["holder_after"],
                "basis": row["basis"],
                "recorded_at": row["recorded_at"],
            },
            ground(obs(OWNERSHIP, f"record_no={row['record_no']}")),
        )
        scoped, kind = scope_map[row["scope_ref"]]
        put(
            "commercial_scope",
            {"record": rec, "scoped": scoped, "scope_kind": kind},
            ground(obs(OWNERSHIP, f"record_no={row['record_no']}")),
            ConstructionOrigin.SEMANTIC,
        )

    put(
        "extract_coverage",
        {
            "collection": "scale_and_bin_exports",
            "coverage_claim": "Scale and bin exports cover the listed tickets and movements for 2025-09-02 through 2025-09-07.",
        },
        ground(obs(NOTES, "L18"), method="notes-completeness"),
        ConstructionOrigin.SEMANTIC,
    )
    put(
        "extract_coverage",
        {
            "collection": "ownership_export",
            "coverage_claim": "Ownership export contains recorded changes, not a guarantee that an unrecorded agreement did not exist.",
        },
        ground(obs(NOTES, "L18"), method="notes-completeness"),
        ConstructionOrigin.SEMANTIC,
    )
    put(
        "extract_coverage",
        {
            "collection": "workspace_extracts",
            "coverage_claim": "Supplied extracts are a bounded working set, not a claim that every record held by every organization exists here.",
        },
        ground(obs("README.md", "L5"), method="readme-bounded-set"),
        ConstructionOrigin.SEMANTIC,
    )

    purpose.require_unique(
        "one-mill-intake-per-receipt",
        per="receipt",
        candidates="mill_intake",
        cardinality="ONE",
        requires_established_world=True,
    )
    purpose.require_unique(
        "one-carrier-departure-per-movement",
        per="movement",
        candidates="carrier_departure",
        cardinality="ONE",
        requires_established_world=True,
    )
    purpose.require_materializable("has-elevator-intakes", relation="elevator_intake", requires_established_world=True)
    purpose.require_materializable("has-mill-process", relation="mill_process", requires_established_world=True)

    purpose.unresolved(
        "physical-ticket-allocation-PGE-OUT-5001",
        subject={"movement": "PGE-OUT-5001", "bin": "North House 12"},
        relation="elevator_loadout",
        reason="BIN-12 already held DR-44, WB-390, and EF-18 before LD-18. No hopper sheet names tickets for OUT-5001. Loadout does not allocate a blended truck back to receiving tickets unless the desk comment says so. Ownership records commercially scope DR-44 to RL-8841 / HFM-IN-601; that is not a bin allocation.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "physical-ticket-allocation-PGE-OUT-5003",
        subject={"movement": "PGE-OUT-5003", "hopper_note": "no ticket on hopper sheet", "cargo_mark": "N3 / EF-18?"},
        relation="carrier_departure",
        reason="Hopper sheet has no ticket. Handwritten cargo mark N3 / EF-18? is not a validated source ticket; N3 is used as a route code elsewhere.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "mill-receipt-absent-PGE-OUT-5003",
        subject={"movement": "PGE-OUT-5003", "consignee_code": "HFM-E", "manifest": "NS-8910"},
        relation="mill_intake",
        reason="12,000 kg truck on PGE-OUT-5003 left with a carrier manifest, but no HFM receiving slip is in the supplied extracts. Consignee is HFM-E. HFM-North log completeness does not support a conclusion about East mill receiving.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "mcr-118-grower-identity",
        subject={"ticket": "MCR-118", "intake_name": "M. Creek", "claims": ["Meadow Creek Farms", "Meadow Creek Grain"]},
        relation="elevator_intake",
        reason="Intake uses M. Creek for the MCR-118 delivery. The commercial desk has claims from both Meadow Creek Farms and Meadow Creek Grain and has no account key that selects one.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "physical-ticket-allocation-PGE-OUT-5004",
        subject={"movement": "PGE-OUT-5004", "bin": "South House 14", "deliveries": ["MCR-118", "S-52"]},
        relation="elevator_loadout",
        reason="PGE-OUT-5004 left from South House 14 after two deliveries were placed there. The loadout desk did not record which delivery supplied which part of that truck. Hopper note is no individual ticket.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "lab-sample-SMP-UNLISTED-source-ticket",
        subject={"sample": "SMP-UNLISTED", "local_lot": "N3 / EF-18?"},
        relation="lab_result",
        reason="Source ticket not recorded; route packet note is not a validated source ticket.",
        grounding_ref=INSPECTIONS,
    )
    purpose.unresolved(
        "lab-sample-SMP-604Q-ticket",
        subject={"sample": "SMP-604Q", "local_lot": "MC-118", "material_hint": "South House 14 cargo"},
        relation="lab_result",
        reason="Sample is labeled South House 14 cargo / MC-118. After MCR-118 and S-52 were both placed in BIN-14, the cargo is not allocated to one delivery.",
        grounding_ref=INSPECTIONS,
    )
    purpose.unresolved(
        "quantity-differences-on-established-movements",
        subject={
            "PGE-OUT-5001": "39000 kg loadout / 38700 kg mill",
            "PGE-OUT-5002": "26000 kg loadout / 25500 kg mill",
            "PGE-OUT-5004": "19000 kg loadout / 18800 kg mill",
        },
        relation="mill_intake",
        reason="Bill-of-lading identity of these truck movements is established. The kilogram differences are recorded and unexplained; they are not treated as a different movement.",
        grounding_ref=PROCESSOR,
    )

    purpose.require("preserve-unsupported-identity-as-unresolved")
