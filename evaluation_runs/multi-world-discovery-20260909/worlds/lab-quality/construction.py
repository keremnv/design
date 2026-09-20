def construct(source, world, purpose):
    rt = lambda name: Role(name, RoleType.TEXT)

    world.declare_relation(
        "lab_result",
        [
            Role("sample", RoleType.REFERENT),
            rt("lab_ticket"),
            rt("local_lot"),
            rt("material_hint"),
            rt("test_name"),
            rt("result"),
            rt("unit"),
            rt("tested_at"),
            rt("comment"),
        ],
        scope="WORLD",
        description="Lab measurements as recorded. local_lot is the lab's label, not a proven identity join.",
    )

    for row in source.rows("evidence/inspection_results.csv"):
        sample = f"sample:{row['sample_no']}"
        world.add_referent(sample, label=row["sample_no"])
        world.assert_tuple(
            "lab_result",
            {
                "sample": sample,
                "lab_ticket": row["lab_ticket"],
                "local_lot": row["local_lot"],
                "material_hint": row["material_hint"],
                "test_name": row["test_name"],
                "result": row["result"],
                "unit": row["unit"],
                "tested_at": row["tested_at"],
                "comment": row["comment"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "evidence/inspection_results.csv",
                f"sample_no={row['sample_no']}",
            ),
        )

    purpose.unresolved(
        "smp_unlisted_source_ticket",
        relation="lab_result",
        subject={"sample": "sample:SMP-UNLISTED", "local_lot": "N3 / EF-18?"},
        reason="source ticket not recorded; local_lot copies the unvalidated route-packet note",
    )
    purpose.unresolved(
        "smp_602b_combined_truck",
        relation="lab_result",
        subject={"sample": "sample:SMP-602B", "local_lot": "WB390 / EF18"},
        reason="combined truck sample; the result is not allocated to one receiving ticket",
    )
    purpose.unresolved(
        "smp_604q_lot_label",
        relation="lab_result",
        subject={"sample": "sample:SMP-604Q", "local_lot": "MC-118"},
        reason="lab lot MC-118 is not itself a proven join to scale ticket MCR-118 or a legal account",
    )
