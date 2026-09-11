def construct(source, world, purpose):
    requirements = source.read_text("checkout-requirements.md")
    implementation = source.read_text("Checkout.tsx")
    if "purchase confidence" not in requirements:
        raise ValueError("the constructor needs the checkout task evidence")
    if 'data-region="order-summary"' not in implementation:
        raise ValueError("the constructor needs the order-summary evidence")
    if 'data-region="payment-entry"' not in implementation:
        raise ValueError("the constructor needs the payment-entry evidence")

    referents = {
        "mobile_checkout": "Mobile checkout",
        "checkout_commitment": "Checkout commitment point",
        "order_total": "Order total",
        "promo_code": "Promo-code entry",
        "order_summary": "Order summary",
        "payment_entry": "Payment entry",
        "purchase_confidence": "Confident purchase",
    }
    for referent_id, label in referents.items():
        world.add_referent(referent_id, label=label)

    world.add_obligation(
        "O7",
        question="What should dominate visual hierarchy at checkout commitment?",
        reason="A candidate is recorded, but no resolver runs in this slice.",
    )
    world.add_obligation(
        "O8",
        question="What critical order information must remain available during payment entry?",
        reason="A candidate is recorded, but no resolver runs in this slice.",
    )
    world.add_obligation(
        "O9",
        question="What should support confident purchase at checkout commitment?",
        reason="A candidate is recorded, but no resolver runs in this slice.",
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

    requirements_basis = source.observation(
        "checkout-requirements.md",
        "critical order summary remains available during payment entry",
    )
    implementation_basis = source.observation(
        "Checkout.tsx",
        "order-summary and payment-entry regions",
    )

    available = world.assert_tuple(
        "remains_available_during",
        {
            "subject": "order_summary",
            "activity": "payment_entry",
            "context": "mobile_checkout",
        },
        origin=ConstructionOrigin.MECHANICAL,
        grounding=AssertionGrounding(
            observations=(requirements_basis,),
            construction_method="encoded from an explicit checkout requirement",
        ),
    )

    prominent = world.assert_tuple(
        "relative_prominence",
        {
            "more": "order_total",
            "less": "promo_code",
            "context": "checkout_commitment",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(requirements_basis, implementation_basis),
            construction_method=(
                "agent design judgment: make the amount due more prominent than "
                "the optional promo action at the commitment point"
            ),
            extra={"basis": "requirements plus checkout structure"},
        ),
    )

    supports_confidence = world.assert_tuple(
        "supports",
        {
            "subject": "order_summary",
            "goal": "purchase_confidence",
            "context": "checkout_commitment",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(requirements_basis, implementation_basis),
            construction_method=(
                "agent design judgment: visible order summary supports confident purchase"
            ),
            extra={"basis": "requirements plus checkout structure"},
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
    for obligation_id, commitment in (
        ("O7", prominent),
        ("O8", available),
        ("O9", supports_confidence),
    ):
        world.assert_tuple(
            "candidate_for",
            {
                "obligation": obligation_id,
                "commitment": commitment.assertion_id,
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=candidate_grounding,
        )
