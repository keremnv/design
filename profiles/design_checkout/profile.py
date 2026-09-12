"""The intentionally bounded Design language used by the checkout fixture.

This is application vocabulary, not a proposal for a universal Design
ontology. The Contract authorizes the three decision relations used by the
fixture, plus one explicitly negative availability relation required by the
counterfactual adequacy test.
"""

from __future__ import annotations

from pathlib import Path

from ontology_author.world import Contract
from ontology_author.world.core.origins import ConstructionOrigin

from .governance import (
    GovernanceProfile,
    adopt_governance_law,
    compile_governance_law,
    select_authoritative_sources,
)


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


def load_design_law(project_root: Path | str) -> GovernanceProfile:
    """Select, compile, and explicitly adopt the fixture's effective law.

    This function is intentionally outside ``construction.py``. The caller
    selects/adopts the law before invoking the ordinary Project lifecycle;
    construction receives only the resulting effective profile.
    """

    selected = select_authoritative_sources(project_root)
    proposed = compile_governance_law(selected)
    return adopt_governance_law(proposed)


# Compatibility for callers that want the checked-in fixture's effective law.
# The dimensions are not authored here; they come through the explicit source
# manifest and compiler above.
DESIGN_LAW = load_design_law(Path(__file__).with_name("fixture"))


DESIGN_CONTRACT = Contract(
    "design-mobile-checkout",
    "1",
    semantic_origins=frozenset({ConstructionOrigin.SEMANTIC.value}),
    semantic_relations=frozenset(DESIGN_RELATION_NAMES),
    allow_semantic_reference_relations=True,
)
