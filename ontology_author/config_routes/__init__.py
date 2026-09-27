"""Production config.routes/v1 profile (Phase 1 Construction slice).

This is the installed, workspace-capable production surface for bounded
config-route Software Governance construction. It does not import fixture
builders and it does not depend on fixed repository paths.

The generic ``ontology_author.software_governance`` package stays
producer-neutral; this package owns config interpretation, establishment
rules, and the thin caller-facing construction facade.
"""

from ontology_author.config_routes.construct import (
    ConfigRoutesReport,
    construct_config_world,
)
from ontology_author.config_routes.rules import (
    EVALUATOR_RULE,
    PROFILE_ID,
    PROFILE_VERSION,
    RULES,
)

__all__ = [
    "PROFILE_ID",
    "PROFILE_VERSION",
    "RULES",
    "EVALUATOR_RULE",
    "ConfigRoutesReport",
    "construct_config_world",
]
