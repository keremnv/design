"""Authoritative-source construction into a governed World that already holds a program spine."""

from .construction import AuthorityConstructor, AuthorityUniverse, DeclaredSource
from .schemas import (
    MECHANISM_KEY,
    AdequacyOutcome,
    AuthorityConstructionError,
    AuthorityConstructionReceipt,
    ClaimKind,
    CompletenessScope,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    UnresolvedKind,
    load_receipt,
)
from .lifecycle import (
    AuthorityConstructionResult,
    construct_authority_world,
    program_world_fingerprint,
)
from .maintenance import GovernanceError, assess_attachment_maintenance, write_maintenance
from .impact import assess_authority_change_impact, write_impact
from .case import assemble_governance_case, markdown_sources_from_root, write_case
from .governance import (
    assess_authority_governance,
    validate_case_sidecar,
    validate_impact_sidecar,
    validate_maintenance_sidecar,
)
from .retrieval import RecoveredAuthority, affected_program_entities, recover_authority_for_delta
from .validation import observations_for_assertion, validate_authority_construction

__all__ = [
    "MECHANISM_KEY",
    "AdequacyOutcome",
    "AuthorityConstructionError",
    "AuthorityConstructionReceipt",
    "AuthorityConstructionResult",
    "AuthorityConstructor",
    "AuthorityUniverse",
    "ClaimKind",
    "CompletenessScope",
    "DeclaredSource",
    "GovernanceError",
    "RecoveredAuthority",
    "ReferentResolution",
    "RelationSupport",
    "SourceStanding",
    "UnresolvedKind",
    "affected_program_entities",
    "assemble_governance_case",
    "assess_attachment_maintenance",
    "assess_authority_change_impact",
    "assess_authority_governance",
    "construct_authority_world",
    "load_receipt",
    "markdown_sources_from_root",
    "observations_for_assertion",
    "program_world_fingerprint",
    "recover_authority_for_delta",
    "validate_authority_construction",
    "validate_case_sidecar",
    "validate_impact_sidecar",
    "validate_maintenance_sidecar",
    "write_case",
    "write_impact",
    "write_maintenance",
]
