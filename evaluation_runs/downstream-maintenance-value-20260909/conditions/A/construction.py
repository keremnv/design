import json


def construct(source, world, purpose):
    rr = lambda name: Role(name, RoleType.REFERENT)
    rt = lambda name: Role(name, RoleType.TEXT)

    world.declare_relation(
        "intake",
        [
            rr("ticket"),
            rt("receipt_no"),
            rt("grower_recorded"),
            rt("assigned_bin"),
            rt("net_kg"),
            rt("arrived_at"),
        ],
        scope="WORLD",
        description="Prairie Gate scale ticket at receiving.",
    )
    world.declare_relation(
        "place_alias",
        [rt("local_name"), rt("canonical")],
        scope="WORLD",
    )
    world.declare_relation(
        "loadout",
        [
            rt("dispatch_ref"),
            rt("bin_label"),
            rt("truck_tag"),
            rt("quantity_kg"),
            rt("loaded_at"),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "manifest",
        [
            rt("manifest_no"),
            rt("cargo_mark"),
            rt("bill_of_lading"),
            rt("consignee_code"),
            rt("weight_kg"),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "mill_receipt",
        [
            rt("local_receipt"),
            rt("bill_reference"),
            rt("origin_label"),
            rt("received_kg"),
            rt("received_at"),
        ],
        scope="WORLD",
    )
    world.declare_relation(
        "mill_run",
        [rt("run_no"), rt("input_receipt"), rt("output_batch"), rt("output_name")],
        scope="WORLD",
    )
    world.declare_relation(
        "dispatch_to_mill",
        [rt("dispatch_ref"), rt("manifest_no"), rt("mill_receipt"), rt("link_basis")],
        scope="WORLD",
    )

    notes = "evidence/operating_notes.md"
    for local_name, canonical, loc in (
        ("PG-ELEV", "Prairie Gate Elevator", "Local names: PG-ELEV"),
        ("Prairie Gate", "Prairie Gate Elevator", "Local names: Prairie Gate"),
        ("BIN-12", "BIN-12", "BIN-12 “North House 12”"),
        ("North House 12", "BIN-12", "BIN-12 “North House 12”"),
        ("B-12", "BIN-12", "assigned_bin B-12"),
        ("BIN-14", "BIN-14", "BIN-14 “South House 14”"),
        ("South House 14", "BIN-14", "BIN-14 “South House 14”"),
        ("B-14", "BIN-14", "assigned_bin B-14"),
        ("HFM-N", "Hearthland Feed Mill - North", "HFM-N is the North mill"),
        ("HFM-E", "Hearthland Feed Mill - East", "HFM-E is the East mill"),
    ):
        world.assert_tuple(
            "place_alias",
            {"local_name": local_name, "canonical": canonical},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(notes, loc),
        )

    for row in source.rows("evidence/elevator_receipts.csv"):
        ticket = f"ticket:{row['scale_ticket']}"
        world.add_referent(ticket, label=row["scale_ticket"])
        world.assert_tuple(
            "intake",
            {
                "ticket": ticket,
                "receipt_no": row["receipt_no"],
                "grower_recorded": row["grower_name"],
                "assigned_bin": row["assigned_bin"],
                "net_kg": row["net_kg"],
                "arrived_at": row["arrival_local"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/elevator_receipts.csv",
                f"scale_ticket={row['scale_ticket']}",
            ),
        )

    for row in source.rows("evidence/loadout_log.csv"):
        world.assert_tuple(
            "loadout",
            {
                "dispatch_ref": row["dispatch_ref"],
                "bin_label": row["bin_label"],
                "truck_tag": row["truck_tag"],
                "quantity_kg": row["quantity_kg"],
                "loaded_at": row["loaded_at"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/loadout_log.csv",
                f"dispatch_ref={row['dispatch_ref']}",
            ),
        )

    manifests = json.loads(source.read_text("evidence/carrier_manifests.json"))
    for row in manifests:
        world.assert_tuple(
            "manifest",
            {
                "manifest_no": row["manifest_no"],
                "cargo_mark": row["cargo_mark"],
                "bill_of_lading": row["bill_of_lading"],
                "consignee_code": row["consignee_code"],
                "weight_kg": str(row["weight_kg"]),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/carrier_manifests.json",
                f"manifest_no={row['manifest_no']}",
            ),
        )

    processor = json.loads(source.read_text("evidence/processor_receipts.json"))
    mill_by_bol = {}
    for row in processor["receiving_log"]:
        mill_by_bol[row["bill_reference"]] = row
        world.assert_tuple(
            "mill_receipt",
            {
                "local_receipt": row["local_receipt"],
                "bill_reference": row["bill_reference"],
                "origin_label": row["origin_label"],
                "received_kg": str(row["received_kg"]),
                "received_at": row["received_at"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/processor_receipts.json",
                f"receiving_log.local_receipt={row['local_receipt']}",
            ),
        )
    for row in processor["mill_runs"]:
        for receipt in row["input_receipts"]:
            world.assert_tuple(
                "mill_run",
                {
                    "run_no": row["run_no"],
                    "input_receipt": receipt,
                    "output_batch": row["output_batch"],
                    "output_name": row["output_name"],
                },
                origin=ConstructionOrigin.MECHANICAL,
                grounding=source.grounding(
                    "evidence/processor_receipts.json",
                    f"mill_runs.run_no={row['run_no']}",
                ),
            )

    for row in manifests:
        mill = mill_by_bol.get(row["bill_of_lading"])
        if mill is None:
            continue
        world.assert_tuple(
            "dispatch_to_mill",
            {
                "dispatch_ref": row["cargo_mark"],
                "manifest_no": row["manifest_no"],
                "mill_receipt": mill["local_receipt"],
                "link_basis": "cargo_mark on manifest joined to mill bill_reference",
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/carrier_manifests.json",
                f"manifest_no={row['manifest_no']}",
            ),
        )

    purpose.unresolved(
        "out_5003_no_mill_slip",
        relation="manifest",
        subject={"dispatch_ref": "PGE-OUT-5003", "manifest_no": "NS-8910"},
        reason="PGE-OUT-5003 has a carrier manifest but no HFM receiving slip in the supplied extracts",
    )
