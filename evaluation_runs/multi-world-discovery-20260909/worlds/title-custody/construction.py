def construct(source, world, purpose):
    rt = lambda name: Role(name, RoleType.TEXT)

    world.declare_relation(
        "ownership_event",
        [
            Role("record", RoleType.REFERENT),
            rt("record_type"),
            rt("scope_ref"),
            rt("effective_start"),
            rt("effective_end"),
            rt("from_party"),
            rt("to_party"),
            rt("owner_after"),
            rt("holder_after"),
            rt("basis"),
        ],
        scope="WORLD",
        description="Title or custody event from the ownership export. Empty owner_after is recorded as written.",
    )

    for row in source.rows("evidence/ownership_records.csv"):
        record = f"ownership:{row['record_no']}"
        world.add_referent(record, label=row["record_no"])
        world.assert_tuple(
            "ownership_event",
            {
                "record": record,
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
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/ownership_records.csv",
                f"record_no={row['record_no']}",
            ),
        )

    purpose.unresolved(
        "mcr118_duplicate_account_claim",
        relation="ownership_event",
        subject={"scope_ref": "MCR-118", "record_no": "TR-107"},
        reason="duplicate account claims from Meadow Creek Farms and Meadow Creek Grain; no account key selects one",
    )
    purpose.unresolved(
        "s52_no_later_title_event",
        relation="ownership_event",
        subject={"scope_ref": "S-52"},
        reason="ownership export has no title_change for S-52 after intake; remaining house contents are not established here",
    )
