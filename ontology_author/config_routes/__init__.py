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
from ontology_author.config_routes.semantic import construct_config_requirements
from ontology_author.config_routes.binding import construct_config_binding
from ontology_author.config_routes.inspect import (
    inspect_binding,
    inspect_config_world,
    inspect_proposition,
    inspect_subject,
)
from ontology_author.config_routes.judge import (
    judge_config_world,
    read_judgment_bundle,
    verify_judgment_bundle,
)
from ontology_author.config_routes.investigate import (
    investigate_config_world,
    read_investigation_bundle,
    verify_investigation_bundle,
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
    "construct_config_requirements",
    "construct_config_binding",
    "inspect_binding",
    "inspect_config_world",
    "inspect_proposition",
    "inspect_subject",
    "judge_config_world",
    "read_judgment_bundle",
    "verify_judgment_bundle",
    "investigate_config_world",
    "read_investigation_bundle",
    "verify_investigation_bundle",
]
