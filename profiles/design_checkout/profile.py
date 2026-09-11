"""The intentionally bounded Design language used by the checkout fixture.

This is application vocabulary, not a proposal for a universal Design
ontology. The Contract authorizes the three decision relations used by the
fixture, plus one explicitly negative availability relation required by the
counterfactual adequacy test.
"""

from __future__ import annotations

from ontology_author.world import Contract
from ontology_author.world.core.origins import ConstructionOrigin


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


DESIGN_OBLIGATIONS = {
    "O7": "What should dominate visual hierarchy at checkout commitment?",
    "O8": "What critical order information must remain available during payment entry?",
    "O9": "What should support confident purchase at checkout commitment?",
}


DESIGN_CONTRACT = Contract(
    "design-mobile-checkout",
    "1",
    semantic_origins=frozenset({ConstructionOrigin.SEMANTIC.value}),
    semantic_relations=frozenset(DESIGN_RELATION_NAMES),
    allow_semantic_reference_relations=True,
)
