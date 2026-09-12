from profiles.design_checkout.structure import (
    extract_frontend_structure,
    write_structure_artifact,
)
from profiles.design_checkout.governance import write_obligation_artifact


def construct(source, world, purpose):
    requirements = source.read_text("checkout-requirements.md")
    implementation = source.read_text("Checkout.tsx")
    if "purchase confidence" not in requirements:
        raise ValueError("the constructor needs the checkout task evidence")
    if 'data-region="order-summary"' not in implementation:
        raise ValueError("the constructor needs the order-summary evidence")
    if 'data-region="payment-entry"' not in implementation:
        raise ValueError("the constructor needs the payment-entry evidence")
    if governance is None:
        raise ValueError("the checkout constructor needs an explicit Governance Law")

    structure = extract_frontend_structure(
        implementation,
        source_name="Checkout.tsx",
        source_revision=source.file_hash("Checkout.tsx"),
    )
    generated_obligations = governance.enumerate_obligations(structure)
    relevant_referents = governance.referents_for(structure)
    write_structure_artifact(
        world.path.parent,
        structure,
        relevant_ids=relevant_referents,
    )
    write_obligation_artifact(world.path.parent, generated_obligations)

    referent_labels = {
        "mobile_checkout": "Mobile checkout",
        "checkout_commitment": "Checkout commitment point",
        "order_total": "Order total",
        "promo_code": "Promo-code entry",
        "order_summary": "Order summary",
        "payment_entry": "Payment entry",
        "purchase_confidence": "Confident purchase",
    }
    for referent_id in relevant_referents:
        world.add_referent(
            referent_id,
            label=referent_labels.get(referent_id, referent_id.replace("_", " ")),
        )
    for obligation in generated_obligations:
        world.add_obligation(
            obligation.obligation_id,
            question=obligation.question,
            reason=obligation.reason,
        )

    design_roles = {
        "relative_prominence": [
            Role("more", RoleType.REFERENT),
            Role("less", RoleType.REFERENT),
            Role("context", RoleType.REFERENT),
        ],
        "remains_available_during": [
            Role("subject", RoleType.REFERENT),
            Role("activity", RoleType.REFERENT),
            Role("context", RoleType.REFERENT),
        ],
        "supports": [
            Role("subject", RoleType.REFERENT),
            Role("goal", RoleType.REFERENT),
            Role("context", RoleType.REFERENT),
        ],
    }
    world.declare_relation(
        "relative_prominence",
        design_roles["relative_prominence"],
        description="A hierarchy decision between two product referents in a context.",
        scope="WORLD",
    )
    world.declare_relation(
        "remains_available_during",
        design_roles["remains_available_during"],
        description="A persistence decision about a product referent during an activity.",
        scope="WORLD",
    )
    world.declare_relation(
        "supports",
        design_roles["supports"],
        description="A means-to-design-goal decision in a context.",
        scope="WORLD",
    )
    world.declare_relation(
        "does_not_remain_available_during",
        design_roles["remains_available_during"],
        description="A provisional explicit negative availability decision.",
        scope="WORLD",
    )

    requirements_basis = source.observation(
        "checkout-requirements.md",
        "critical order summary remains available during payment entry",
    )
    implementation_basis = source.observation(
        "Checkout.tsx",
        "order-summary and payment-entry regions",
    )

    commitments = {}
    for obligation in generated_obligations:
        values = obligation.binding_map
        if obligation.dimension == "availability":
            commitments[obligation.obligation_id] = world.assert_tuple(
                "remains_available_during",
                {
                    "subject": values["subject"],
                    "activity": values["activity"],
                    "context": values["context"],
                },
                origin=ConstructionOrigin.MECHANICAL,
                grounding=AssertionGrounding(
                    observations=(requirements_basis, implementation_basis),
                    construction_method=(
                        "candidate encoded from the explicit requirement; current "
                        "frontend structure is evidence, not law"
                    ),
                    extra={
                        "basis": "requirements plus current structural model",
                        "resolution_authority": "APPROVED_REQUIREMENT",
                        "current_present_during": list(structure.present_during),
                    },
                ),
            )
        elif obligation.dimension == "priority":
            commitments[obligation.obligation_id] = world.assert_tuple(
                "relative_prominence",
                {
                    "more": values["more"],
                    "less": values["less"],
                    "context": values["context"],
                },
                origin=ConstructionOrigin.SEMANTIC,
                grounding=AssertionGrounding(
                    observations=(requirements_basis, implementation_basis),
                    construction_method=(
                        "agent design judgment: make the amount due more prominent "
                        "than the optional promo action at the commitment point"
                    ),
                    extra={
                        "basis": "requirements plus current structural model",
                        "resolution_authority": "AGENT_JUDGMENT",
                    },
                ),
            )
        elif obligation.dimension == "goal_support":
            commitments[obligation.obligation_id] = world.assert_tuple(
                "supports",
                {
                    "subject": values["subject"],
                    "goal": values["goal"],
                    "context": values["context"],
                },
                origin=ConstructionOrigin.SEMANTIC,
                grounding=AssertionGrounding(
                    observations=(requirements_basis, implementation_basis),
                    construction_method=(
                        "agent design judgment: visible order summary supports "
                        "confident purchase"
                    ),
                    extra={
                        "basis": "requirements plus current structural model",
                        "resolution_authority": "AGENT_JUDGMENT",
                    },
                ),
            )

    world.declare_relation(
        "candidate_for",
        [
            Role(
                "obligation",
                RoleType.TEXT,
                reference_kind=SemanticRefKind.OBLIGATION,
            ),
            Role(
                "commitment",
                RoleType.TEXT,
                reference_kind=SemanticRefKind.COMMITMENT,
            ),
        ],
        description="A commitment proposed as a candidate answer to an obligation.",
        scope="WORLD",
    )
    candidate_grounding = AssertionGrounding(
        observations=(),
        construction_method="constructor records candidate relationship",
    )
    for obligation_id, commitment in sorted(commitments.items()):
        world.assert_tuple(
            "candidate_for",
            {
                "obligation": obligation_id,
                "commitment": commitment.assertion_id,
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=candidate_grounding,
        )
