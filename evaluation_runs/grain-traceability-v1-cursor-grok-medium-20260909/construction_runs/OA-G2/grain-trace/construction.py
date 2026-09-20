"""Construct a purpose-fit World for grain movement traceability."""

from __future__ import annotations

import json
import re

from ontology_author.world.core.model import Completeness, CompletenessStatus
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding


NOTES = "evidence/operating_notes.md"
ELEVATOR = "evidence/elevator_receipts.csv"
BINS = "evidence/bin_movements.csv"
LOADOUT = "evidence/loadout_log.csv"
MANIFESTS = "evidence/carrier_manifests.json"
PROCESSOR = "evidence/processor_receipts.json"
OWNERSHIP = "evidence/ownership_records.csv"
LABS = "evidence/inspection_results.csv"

TICKET_RE = re.compile(r"^[A-Z]+-?\d+[A-Z]?$")


def _roles(*names: str):
    return [Role(name, RoleType.TEXT) for name in names]


def _g(source, table: str, location: str, method: str = ""):
    return source.grounding(table, location, method=method)


def _join_g(source, specs: list[tuple[str, str]], method: str):
    return AssertionGrounding(
        observations=tuple(source.observation(table, loc) for table, loc in specs),
        construction_method=method,
    )


def _put(world, relation: str, values: dict, origin, grounding):
    world.assert_tuple(relation, values, origin=origin, grounding=grounding)


def _ticket_forms(text: str) -> list[str]:
    parts = [part.strip() for part in str(text).replace(",", "/").split("/") if part.strip()]
    out = []
    for part in parts:
        compact = part.replace(" ", "")
        if TICKET_RE.match(compact) and "?" not in part:
            if "-" not in compact:
                compact = re.sub(r"^([A-Z]+)(\d+)$", r"\1-\2", compact)
            out.append(compact)
    return out


def construct(source, world, purpose) -> None:
    mech = ConstructionOrigin.MECHANICAL
    sem = ConstructionOrigin.SEMANTIC

    world.declare_relation(
        "identifier_alias",
        _roles("form", "canonical", "kind"),
        description="Documented or source-used spellings of one identifier.",
    )
    world.declare_relation(
        "extract_coverage",
        _roles("desk", "site", "window", "claim"),
        description="Completeness claims stated in the yard notes for supplied extracts.",
    )
    world.declare_relation(
        "intake_receipt",
        _roles(
            "receipt_no",
            "scale_ticket",
            "arrived_at",
            "commodity",
            "grower_name",
            "net_kg",
            "receiving_lane",
            "assigned_bin",
            "owner_at_intake",
            "grade_note",
        ),
        description="Prairie Gate scale tickets as received.",
    )
    world.declare_relation(
        "storage_move",
        _roles(
            "move_id",
            "logged_at",
            "from_point",
            "to_point",
            "material_note",
            "quantity_kg",
            "work_order",
        ),
        description="Bin-system hopper and house movements.",
    )
    world.declare_relation(
        "loadout_event",
        _roles(
            "dispatch_id",
            "loaded_at",
            "truck_tag",
            "dispatch_ref",
            "bin_label",
            "quantity_kg",
            "route_code",
            "desk_comment",
        ),
        description="Elevator spout loadout records.",
    )
    world.declare_relation(
        "manifest_event",
        _roles(
            "manifest_no",
            "carrier",
            "vehicle",
            "departed_at",
            "pickup_site",
            "consignee_code",
            "consignee_name",
            "bill_of_lading",
            "cargo_mark",
            "weight_kg",
        ),
        description="Carrier departure manifests.",
    )
    world.declare_relation(
        "mill_receipt",
        _roles(
            "local_receipt",
            "mill_code",
            "received_at",
            "dock",
            "bill_reference",
            "origin_label",
            "received_kg",
            "silo",
            "commodity",
        ),
        description="Hearthland North dock receiving slips in the supplied log.",
    )
    world.declare_relation(
        "mill_process",
        _roles("run_no", "started_at", "input_receipt", "output_batch", "output_name"),
        description="Mill runs that name their input receipts.",
    )
    world.declare_relation(
        "lab_test",
        _roles(
            "sample_no",
            "tested_at",
            "lab_ticket",
            "local_lot",
            "material_hint",
            "test_name",
            "result",
            "unit",
            "comment",
        ),
        description="Lab results as recorded, including unvalidated lot labels.",
    )
    world.declare_relation(
        "ownership_event",
        _roles(
            "record_no",
            "record_type",
            "scope_ref",
            "effective_start",
            "effective_end",
            "from_party",
            "to_party",
            "owner_after",
            "holder_after",
            "basis",
        ),
        description="Recorded title, custody, and party-claim events.",
    )
    world.declare_relation(
        "ticket_into_bin",
        _roles("scale_ticket", "bin", "move_id"),
        description="A hopper note that names exactly one receiving ticket into a house.",
    )
    world.declare_relation(
        "hopper_names_ticket",
        _roles("move_id", "work_order", "scale_ticket"),
        description="A hopper note that names a ticket without allocating quantity.",
    )
    world.declare_relation(
        "loadout_from_bin",
        _roles("dispatch_ref", "bin", "loadout_id"),
        description="Loadout spout bin after local house names are aligned.",
    )
    world.declare_relation(
        "outbound_same_movement",
        _roles("dispatch_ref", "manifest_no", "link_basis"),
        description="Elevator dispatch and carrier manifest for one truck departure.",
    )
    world.declare_relation(
        "inbound_same_movement",
        _roles("manifest_no", "mill_receipt", "link_basis"),
        description="Carrier bill of lading matched to a mill receiving slip.",
    )
    world.declare_relation(
        "established_shipment",
        _roles("dispatch_ref", "manifest_no", "mill_receipt", "output_batch"),
        mode=RelationMode.DERIVED,
        description="Dispatch to mill receipt, with mill output when a run names that receipt.",
    )

    def alias(form, canonical, kind, table, loc, origin=mech, method=""):
        _put(
            world,
            "identifier_alias",
            {"form": form, "canonical": canonical, "kind": kind},
            origin,
            _g(source, table, loc, method=method),
        )

    alias("PG-ELEV", "Prairie Gate Elevator", "site", NOTES, "Local names: PG-ELEV")
    alias("Prairie Gate", "Prairie Gate Elevator", "site", NOTES, "Local names: Prairie Gate")
    alias("BIN-12", "BIN-12", "bin", NOTES, "Local names: BIN-12 North House 12")
    alias("North House 12", "BIN-12", "bin", NOTES, "Local names: BIN-12 North House 12")
    alias("B-12", "BIN-12", "bin", ELEVATOR, "assigned_bin=B-12", origin=sem, method="elevator bin code for North House 12")
    alias("BIN-14", "BIN-14", "bin", NOTES, "Local names: BIN-14 South House 14")
    alias("South House 14", "BIN-14", "bin", NOTES, "Local names: BIN-14 South House 14")
    alias("B-14", "BIN-14", "bin", ELEVATOR, "assigned_bin=B-14", origin=sem, method="elevator bin code for South House 14")
    alias("HFM-N", "Hearthland Feed Mill - North", "site", PROCESSOR, "site_directory.HFM-N")
    alias("HFM-E", "Hearthland Feed Mill - East", "site", PROCESSOR, "site_directory.HFM-E")

    for form, canonical, loc in (
        ("DR44", "DR-44", "local_lot=DR44"),
        ("WB390", "WB-390", "local_lot=WB390 / EF18"),
        ("EF18", "EF-18", "local_lot=WB390 / EF18"),
        ("MC-118", "MCR-118", "local_lot=MC-118"),
    ):
        alias(form, canonical, "scale_ticket", LABS, loc, origin=sem, method="lab lot spelling of a scale ticket")

    known_tickets: set[str] = set()

    alias("TRUCK-NS204", "NST-204", "vehicle", BINS, "to_point=TRUCK-NS204", origin=sem, method="bin truck point for loadout truck_tag")
    alias("TRUCK-RL091", "RLT-091", "vehicle", BINS, "to_point=TRUCK-RL091", origin=sem, method="bin truck point for loadout truck_tag")

    coverage = [
        (
            "HFM receiving log",
            "HFM-N",
            "2025-09-05/2025-09-07",
            "complete for HFM-North in this window; no conclusion about other HFM sites",
            "How the exports are maintained: HFM-North receiving log",
        ),
        (
            "scale and bin exports",
            "Prairie Gate Elevator",
            "2025-09-02/2025-09-07",
            "cover the listed tickets and movements in this window",
            "How the exports are maintained: scale and bin exports",
        ),
        (
            "ownership export",
            "Prairie Gate Elevator",
            "recorded changes only",
            "recorded changes, not a guarantee that an unrecorded agreement did not exist",
            "How the exports are maintained: ownership export",
        ),
    ]
    for desk, site, window, claim, loc in coverage:
        _put(
            world,
            "extract_coverage",
            {"desk": desk, "site": site, "window": window, "claim": claim},
            mech,
            _g(source, NOTES, loc),
        )

    for row in source.rows(ELEVATOR):
        ticket = row["scale_ticket"]
        known_tickets.add(ticket)
        loc = f"receipt_no={row['receipt_no']}"
        _put(
            world,
            "intake_receipt",
            {
                "receipt_no": row["receipt_no"],
                "scale_ticket": ticket,
                "arrived_at": row["arrival_local"],
                "commodity": row["commodity"],
                "grower_name": row["grower_name"],
                "net_kg": row["net_kg"],
                "receiving_lane": row["receiving_lane"],
                "assigned_bin": row["assigned_bin"],
                "owner_at_intake": row["owner_at_intake"],
                "grade_note": row["grade_note"],
            },
            mech,
            _g(source, ELEVATOR, loc),
        )
        assigned = {"B-12": "BIN-12", "B-14": "BIN-14"}.get(row["assigned_bin"], row["assigned_bin"])
        _put(
            world,
            "identifier_alias",
            {
                "form": row["assigned_bin"],
                "canonical": assigned,
                "kind": "bin",
            },
            sem,
            _g(source, ELEVATOR, loc, method="assigned_bin code"),
        )

    for row in source.rows(BINS):
        loc = f"move_id={row['move_id']}"
        note = row["material_note"]
        _put(
            world,
            "storage_move",
            {
                "move_id": row["move_id"],
                "logged_at": row["logged_at"],
                "from_point": row["from_point"],
                "to_point": row["to_point"],
                "material_note": note,
                "quantity_kg": row["quantity_kg"],
                "work_order": row["work_order"],
            },
            mech,
            _g(source, BINS, loc),
        )
        tickets = [item for item in _ticket_forms(note) if item in known_tickets]
        house = row["to_point"] if row["to_point"].startswith("BIN-") else ""
        if house and len(tickets) == 1:
            _put(
                world,
                "ticket_into_bin",
                {
                    "scale_ticket": tickets[0],
                    "bin": house,
                    "move_id": row["move_id"],
                },
                sem,
                _g(source, BINS, loc, method="single ticket copied into material_note on house fill"),
            )
        for ticket in tickets:
            _put(
                world,
                "hopper_names_ticket",
                {
                    "move_id": row["move_id"],
                    "work_order": row["work_order"],
                    "scale_ticket": ticket,
                },
                sem,
                _g(source, BINS, loc, method="ticket token in material_note; not a quantity split"),
            )

    bin_from_label = {"North House 12": "BIN-12", "South House 14": "BIN-14"}
    for row in source.rows(LOADOUT):
        loc = f"dispatch_id={row['dispatch_id']}"
        _put(
            world,
            "loadout_event",
            {
                "dispatch_id": row["dispatch_id"],
                "loaded_at": row["loaded_at"],
                "truck_tag": row["truck_tag"],
                "dispatch_ref": row["dispatch_ref"],
                "bin_label": row["bin_label"],
                "quantity_kg": row["quantity_kg"],
                "route_code": row["route_code"],
                "desk_comment": row["desk_comment"],
            },
            mech,
            _g(source, LOADOUT, loc),
        )
        house = bin_from_label[row["bin_label"]]
        _put(
            world,
            "loadout_from_bin",
            {
                "dispatch_ref": row["dispatch_ref"],
                "bin": house,
                "loadout_id": row["dispatch_id"],
            },
            sem,
            _join_g(
                source,
                [(LOADOUT, loc), (NOTES, f"Local names: {row['bin_label']}")],
                "loadout bin_label aligned to bin-system house code",
            ),
        )

    manifests = json.loads(source.read_text(MANIFESTS))
    for row in manifests:
        loc = f"manifest_no={row['manifest_no']}"
        _put(
            world,
            "manifest_event",
            {
                "manifest_no": row["manifest_no"],
                "carrier": row["carrier"],
                "vehicle": row["vehicle"],
                "departed_at": row["departed_local"],
                "pickup_site": row["pickup_site"],
                "consignee_code": row["consignee_code"],
                "consignee_name": row["consignee_name"],
                "bill_of_lading": row["bill_of_lading"],
                "cargo_mark": row["cargo_mark"],
                "weight_kg": str(row["weight_kg"]),
            },
            mech,
            _g(source, MANIFESTS, loc),
        )

    processor = json.loads(source.read_text(PROCESSOR))
    for row in processor["receiving_log"]:
        origin = row.get("origin_label") or ""
        if origin.startswith("PG-OUT-"):
            alias(
                origin,
                origin.replace("PG-OUT-", "PGE-OUT-", 1),
                "dispatch",
                PROCESSOR,
                f"receiving_log.local_receipt={row['local_receipt']}",
                origin=sem,
                method="mill origin_label spelling of elevator PGE-OUT dispatch",
            )
    for row in source.rows(BINS):
        work = row["work_order"]
        if work.startswith("OUT-"):
            alias(
                work,
                work.replace("OUT-", "PGE-OUT-", 1),
                "dispatch",
                BINS,
                f"move_id={row['move_id']}",
                origin=sem,
                method="bin work order number for an elevator PGE-OUT dispatch",
            )
    for row in processor["receiving_log"]:
        loc = f"receiving_log.local_receipt={row['local_receipt']}"
        _put(
            world,
            "mill_receipt",
            {
                "local_receipt": row["local_receipt"],
                "mill_code": "HFM-N",
                "received_at": row["received_at"],
                "dock": row["dock"],
                "bill_reference": row["bill_reference"],
                "origin_label": row["origin_label"],
                "received_kg": str(row["received_kg"]),
                "silo": row["silo"],
                "commodity": row["commodity"],
            },
            sem,
            _join_g(
                source,
                [(PROCESSOR, loc), (NOTES, "How the exports are maintained: HFM-North receiving log")],
                "supplied receiving_log is the HFM-North extract",
            ),
        )
    for row in processor["mill_runs"]:
        for input_receipt in row["input_receipts"]:
            loc = f"mill_runs.run_no={row['run_no']}"
            _put(
                world,
                "mill_process",
                {
                    "run_no": row["run_no"],
                    "started_at": row["started_at"],
                    "input_receipt": input_receipt,
                    "output_batch": row["output_batch"],
                    "output_name": row["output_name"],
                },
                mech,
                _g(source, PROCESSOR, loc),
            )

    for row in source.rows(LABS):
        loc = f"sample_no={row['sample_no']}"
        _put(
            world,
            "lab_test",
            {key: row[key] for key in (
                "sample_no",
                "tested_at",
                "lab_ticket",
                "local_lot",
                "material_hint",
                "test_name",
                "result",
                "unit",
                "comment",
            )},
            mech,
            _g(source, LABS, loc),
        )

    for row in source.rows(OWNERSHIP):
        loc = f"record_no={row['record_no']}"
        _put(
            world,
            "ownership_event",
            {
                "record_no": row["record_no"],
                "record_type": row["record_type"],
                "scope_ref": row["scope_ref"],
                "effective_start": row["effective_start"],
                "effective_end": row["effective_end"],
                "from_party": row["from_party"],
                "to_party": row["to_party"],
                "owner_after": row["owner_after"],
                "holder_after": row["holder_after"],
                "basis": row["basis"],
            },
            mech,
            _g(source, OWNERSHIP, loc),
        )

    loadouts = {row["dispatch_ref"]: row for row in source.rows(LOADOUT)}
    for manifest in manifests:
        cargo = manifest["cargo_mark"]
        vehicle = manifest["vehicle"]
        weight = str(manifest["weight_kg"])
        matched = None
        basis = ""
        method = ""
        if cargo in loadouts:
            matched = cargo
            basis = "cargo_mark equals elevator dispatch_ref"
            method = "carrier cargo_mark is the elevator PGE-OUT dispatch id"
        else:
            for dispatch_ref, load in loadouts.items():
                if load["truck_tag"] == vehicle and load["quantity_kg"] == weight:
                    matched = dispatch_ref
                    basis = "same vehicle tag and loaded weight; cargo_mark is not the dispatch id"
                    method = "truck_tag and quantity match; handwritten cargo_mark not used as ticket or dispatch identity"
                    break
        if matched is None:
            continue
        load = loadouts[matched]
        _put(
            world,
            "outbound_same_movement",
            {
                "dispatch_ref": matched,
                "manifest_no": manifest["manifest_no"],
                "link_basis": basis,
            },
            sem,
            _join_g(
                source,
                [
                    (LOADOUT, f"dispatch_id={load['dispatch_id']}"),
                    (MANIFESTS, f"manifest_no={manifest['manifest_no']}"),
                ],
                method,
            ),
        )

    mill_by_bol = {row["bill_reference"]: row for row in processor["receiving_log"]}
    for manifest in manifests:
        mill = mill_by_bol.get(manifest["bill_of_lading"])
        if mill is None:
            continue
        _put(
            world,
            "inbound_same_movement",
            {
                "manifest_no": manifest["manifest_no"],
                "mill_receipt": mill["local_receipt"],
                "link_basis": "bill_of_lading equals mill bill_reference",
            },
            sem,
            _join_g(
                source,
                [
                    (MANIFESTS, f"manifest_no={manifest['manifest_no']}"),
                    (PROCESSOR, f"receiving_log.local_receipt={mill['local_receipt']}"),
                ],
                "carrier bill matched to mill receiving slip; consignee code is not itself a slip",
            ),
        )

    world.register_derivation(
        "established_shipment",
        sql="""
            SELECT
                outbound_same_movement.dispatch_ref,
                outbound_same_movement.manifest_no,
                inbound_same_movement.mill_receipt,
                COALESCE(mill_process.output_batch, '') AS output_batch
            FROM outbound_same_movement
            JOIN inbound_same_movement
              ON outbound_same_movement.manifest_no = inbound_same_movement.manifest_no
            LEFT JOIN mill_process
              ON mill_process.input_receipt = inbound_same_movement.mill_receipt
        """,
        inputs=["outbound_same_movement", "inbound_same_movement", "mill_process"],
    )
    world.rerun(
        "established_shipment",
        completeness=Completeness(
            status=CompletenessStatus.INCOMPLETE,
            universe="outbound_same_movement",
            basis="BOL match from carrier manifest to mill slip; mill output only when a run names that slip; HFM-East receipts are outside the North log",
            known_gaps=(
                "PGE-OUT-5003 has a manifest and no mill slip in the extracts",
                "HFM-IN-604 has no mill run in the supplied mill_runs",
            ),
        ),
    )

    purpose.require("intake_recorded", relation="intake_receipt")
    purpose.require("storage_recorded", relation="storage_move")
    purpose.require("loadout_recorded", relation="loadout_event")
    purpose.require("manifest_recorded", relation="manifest_event")
    purpose.require("mill_intake_recorded", relation="mill_receipt")
    purpose.require_materializable("intake_rows", relation="intake_receipt")
    purpose.require_materializable("shipment_links", relation="outbound_same_movement")
    purpose.require_unique(
        "one_manifest_per_dispatch",
        per="dispatch_ref",
        candidates="outbound_same_movement",
        cardinality="ONE",
        requires_established_world=False,
    )
    purpose.require_unique(
        "one_mill_slip_per_manifest",
        per="manifest_no",
        candidates="inbound_same_movement",
        cardinality="ONE",
        requires_established_world=False,
    )

    purpose.unresolved(
        "m_creek_account",
        subject={"affected": "MCR-118", "scale_ticket": "MCR-118", "grower_name": "M. Creek"},
        relation="intake_receipt",
        reason="Intake uses M. Creek; commercial desk has claims from both Meadow Creek Farms and Meadow Creek Grain and has no account key that selects one.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "out_5001_ticket_composition",
        subject={"affected": "PGE-OUT-5001", "dispatch_ref": "PGE-OUT-5001", "bin": "BIN-12"},
        relation="loadout_from_bin",
        reason="North House 12 already held DR-44, WB-390, and EF-18 before this spout load. The loadout comment does not allocate the truck back to receiving tickets.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "out_5002_quantity_split",
        subject={"affected": "PGE-OUT-5002", "dispatch_ref": "PGE-OUT-5002", "named_tickets": "WB-390 / EF-18"},
        relation="hopper_names_ticket",
        reason="Hopper note names WB-390 and EF-18 together; the loadout does not allocate the blended 26000 kg to individual tickets.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "out_5003_material_identity",
        subject={"affected": "PGE-OUT-5003", "dispatch_ref": "PGE-OUT-5003", "cargo_mark": "N3 / EF-18?"},
        relation="manifest_event",
        reason="No ticket on the hopper sheet. N3 is a route code elsewhere; the handwritten cargo note is not a validated source ticket.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "out_5003_mill_receipt",
        subject={"affected": "PGE-OUT-5003", "dispatch_ref": "PGE-OUT-5003", "consignee_code": "HFM-E"},
        relation="inbound_same_movement",
        reason="Truck left with a carrier manifest, but no HFM receiving slip is in the supplied extracts. Consignee is HFM-E; North-log completeness does not speak to East.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "out_5004_ticket_composition",
        subject={"affected": "PGE-OUT-5004", "dispatch_ref": "PGE-OUT-5004", "bin": "BIN-14"},
        relation="loadout_from_bin",
        reason="South House 14 held MCR-118 and S-52; the loadout desk did not record which delivery supplied which part of the truck.",
        grounding_ref=NOTES,
    )
    purpose.unresolved(
        "smp_unlisted_source_ticket",
        subject={"affected": "SMP-UNLISTED", "sample_no": "SMP-UNLISTED", "local_lot": "N3 / EF-18?"},
        relation="lab_test",
        reason="Lab comment records that the source ticket was not recorded; the route-packet note is not treated as a ticket.",
        grounding_ref=LABS,
    )
    purpose.unresolved(
        "unrecorded_ownership",
        subject={"affected": "ownership_records.csv", "export": "ownership_records.csv"},
        relation="ownership_event",
        reason="Ownership export contains recorded changes, not a guarantee that an unrecorded agreement did not exist.",
        grounding_ref=NOTES,
    )
