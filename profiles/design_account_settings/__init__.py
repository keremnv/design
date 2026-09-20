"""Bounded Design profile for the account-settings fixture."""

from .authority import (
    EvidenceAuthorityBinding,
    EvidenceAuthorityConfiguration,
    load_evidence_authority,
)
from .governance import (
    ACCOUNT_SETTINGS_COMPILER_ID,
    AuthoritativeLawSources,
    GeneratedObligation,
    GovernanceBinding,
    GovernanceProfile,
    GovernedDimension,
    LawRuleProvenance,
    LawSource,
    ProposedGovernanceLaw,
    adopt_governance_law,
    compile_governance_law,
    select_authoritative_sources,
    write_obligation_artifact,
)
from .profile import (
    ACCOUNT_SETTINGS_CONTRACT,
    ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY,
    ACCOUNT_SETTINGS_LAW,
    ACCOUNT_SETTINGS_REFERENTS,
    ACCOUNT_SETTINGS_RELATIONS,
    ACCOUNT_SETTINGS_RELATION_NAMES,
    load_account_settings_law,
)
from .structure import (
    FrontendStructure,
    NodeSelector,
    StructuralNode,
    extract_frontend_structure,
    write_structure_artifact,
)

__all__ = [
    "ACCOUNT_SETTINGS_COMPILER_ID",
    "ACCOUNT_SETTINGS_CONTRACT",
    "ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY",
    "ACCOUNT_SETTINGS_LAW",
    "ACCOUNT_SETTINGS_REFERENTS",
    "ACCOUNT_SETTINGS_RELATIONS",
    "ACCOUNT_SETTINGS_RELATION_NAMES",
    "AuthoritativeLawSources",
    "EvidenceAuthorityBinding",
    "EvidenceAuthorityConfiguration",
    "FrontendStructure",
    "GeneratedObligation",
    "GovernanceBinding",
    "GovernanceProfile",
    "GovernedDimension",
    "LawRuleProvenance",
    "LawSource",
    "NodeSelector",
    "ProposedGovernanceLaw",
    "StructuralNode",
    "adopt_governance_law",
    "compile_governance_law",
    "extract_frontend_structure",
    "load_account_settings_law",
    "load_evidence_authority",
    "select_authoritative_sources",
    "write_obligation_artifact",
    "write_structure_artifact",
]
