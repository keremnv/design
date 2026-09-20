from profiles.design_account_settings.governance import (
    write_obligation_artifact,
)
from profiles.design_account_settings.structure import (
    extract_frontend_structure,
    write_structure_artifact,
)


def construct(source, world):
    implementation = source.read_text("AccountSettings.tsx")
    structure = extract_frontend_structure(
        implementation,
        source_name="AccountSettings.tsx",
        source_revision=source.file_hash("AccountSettings.tsx"),
    )
    obligations = governance.enumerate_obligations(structure)
    write_structure_artifact(world.path.parent, structure)
    write_obligation_artifact(world.path.parent, obligations)

    for referent_id in governance.referents_for(structure):
        world.add_referent(referent_id, label=referent_id.replace("_", " "))
    for obligation in obligations:
        world.add_obligation(
            obligation.obligation_id,
            question=obligation.question,
            reason=obligation.reason,
        )

    world.declare_relation(
        "requires_confirmation_before",
        [
            Role("action", RoleType.REFERENT),
            Role("consequence", RoleType.REFERENT),
            Role("context", RoleType.REFERENT),
        ],
        description="A candidate answer about confirmation before a consequence.",
        scope="WORLD",
    )
    world.declare_relation(
        "distinct_in_consequence",
        [
            Role("routine", RoleType.REFERENT),
            Role("destructive", RoleType.REFERENT),
            Role("context", RoleType.REFERENT),
        ],
        description="A candidate answer about differing action consequences.",
        scope="WORLD",
    )

    approved_basis = source.observation(
        "account-settings-requirements.md",
        "explicit confirmation before irreversible account deletion",
    )
    implementation_basis = source.observation(
        "AccountSettings.tsx",
        "delete action, confirmation context, and deleted consequence context",
    )

    confirmation = world.assert_tuple(
        "requires_confirmation_before",
        {
            "action": "delete_account",
            "consequence": "account_deleted",
            "context": "account_settings",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(approved_basis, implementation_basis),
            construction_method=(
                "agent translated the adopted confirmation rule into a candidate"
            ),
            extra={
                "interpretation": (
                    "account deletion has an irreversible destructive consequence"
                )
            },
        ),
    )
    distinction = world.assert_tuple(
        "distinct_in_consequence",
        {
            "routine": "save_changes",
            "destructive": "delete_account",
            "context": "account_settings",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(implementation_basis,),
            construction_method=(
                "agent interpretation that routine saving and deletion need "
                "distinct consequence handling"
            ),
        ),
    )

    commitments = {
        "confirmation_requirement": confirmation.assertion_id,
        "consequence_distinction": distinction.assertion_id,
    }
    for obligation in obligations:
        try:
            world.add_candidate(obligation.obligation_id, commitments[obligation.dimension])
        except KeyError as exc:
            raise ValueError(
                f"account-settings construction has no candidate for {obligation.dimension!r}"
            ) from exc
