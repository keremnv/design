"""The intentionally bounded Design language used by the checkout fixture.

This is application vocabulary, not a proposal for a universal Design
ontology. The Contract authorizes the three decision relations used by the
fixture, plus one explicitly negative availability relation required by the
counterfactual adequacy test.
"""

from __future__ import annotations

from ontology_author.world import Contract
from ontology_author.world.core.origins import ConstructionOrigin

from .governance import (
    GovernanceBinding,
    GovernanceProfile,
    GovernedDimension,
)
from .structure import NodeSelector


DESIGN_REFERENTS = (
    "mobile_checkout",
    "checkout_commitment",
    "order_total",
    "promo_code",
    "order_summary",
    "payment_entry",
    "purchase_confidence",
)


DESIGN_RELATIONS = {
    "relative_prominence": ("more", "less", "context"),
    "remains_available_during": ("subject", "activity", "context"),
    "supports": ("subject", "goal", "context"),
    # This fourth relation is deliberately narrow. Without it, an absent
    # positive tuple means both "not required" and "not yet determined".
    "does_not_remain_available_during": ("subject", "activity", "context"),
}


DESIGN_RELATION_NAMES = tuple(DESIGN_RELATIONS)


DESIGN_LAW = GovernanceProfile(
    "design-mobile-checkout-law",
    "1",
    dimensions=(
        GovernedDimension(
            "availability",
            bindings=(
                GovernanceBinding(
                    "subject",
                    selector=NodeSelector("data-region", "order-summary", "region"),
                ),
                GovernanceBinding(
                    "activity",
                    selector=NodeSelector("data-region", "payment-entry", "region"),
                ),
                GovernanceBinding(
                    "context",
                    selector=NodeSelector("data-screen", "mobile-checkout", "surface"),
                ),
            ),
            question_template=(
                "What availability relationship should hold between {subject} "
                "and {activity} in {context}?"
            ),
        ),
        GovernedDimension(
            "priority",
            bindings=(
                GovernanceBinding(
                    "more",
                    selector=NodeSelector("data-field", "order-total", "element"),
                ),
                GovernanceBinding(
                    "less",
                    selector=NodeSelector("data-action", "promo-code", "interaction"),
                ),
                GovernanceBinding(
                    "context",
                    selector=NodeSelector(
                        "data-context", "checkout-commitment", "context"
                    ),
                ),
            ),
            question_template=(
                "What should dominate visual hierarchy between {more} and {less} "
                "at {context}?"
            ),
        ),
        GovernedDimension(
            "goal_support",
            bindings=(
                GovernanceBinding(
                    "subject",
                    selector=NodeSelector("data-region", "order-summary", "region"),
                ),
                GovernanceBinding("goal", fixed_value="purchase_confidence"),
                GovernanceBinding(
                    "context",
                    selector=NodeSelector(
                        "data-context", "checkout-commitment", "context"
                    ),
                ),
            ),
            question_template=(
                "What should support {goal} at {context}, and how should "
                "{subject} contribute?"
            ),
        ),
    ),
)


DESIGN_CONTRACT = Contract(
    "design-mobile-checkout",
    "1",
    semantic_origins=frozenset({ConstructionOrigin.SEMANTIC.value}),
    semantic_relations=frozenset(DESIGN_RELATION_NAMES),
    allow_semantic_reference_relations=True,
)
