"""Bounded Design profile for the mobile checkout fixture."""

from .profile import (
    DESIGN_CONTRACT,
    DESIGN_LAW,
    DESIGN_REFERENTS,
    DESIGN_RELATIONS,
    DESIGN_RELATION_NAMES,
)
from .governance import (
    GeneratedObligation,
    GovernanceBinding,
    GovernanceProfile,
    GovernedDimension,
)
from .structure import (
    FrontendStructure,
    NodeSelector,
    StructuralNode,
    extract_frontend_structure,
)

__all__ = [
    "DESIGN_CONTRACT",
    "DESIGN_LAW",
    "DESIGN_REFERENTS",
    "DESIGN_RELATIONS",
    "DESIGN_RELATION_NAMES",
    "FrontendStructure",
    "GeneratedObligation",
    "GovernanceBinding",
    "GovernanceProfile",
    "GovernedDimension",
    "NodeSelector",
    "StructuralNode",
    "extract_frontend_structure",
]
