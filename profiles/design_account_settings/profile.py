"""Bounded account-settings Design vocabulary and selected law."""

from __future__ import annotations

from pathlib import Path

from ontology_author.world import Contract
from ontology_author.world.core.origins import ConstructionOrigin

from .authority import load_evidence_authority
from .governance import (
    GovernanceProfile,
    adopt_governance_law,
    compile_governance_law,
    select_authoritative_sources,
)


ACCOUNT_SETTINGS_REFERENTS = (
    "account_settings",
    "save_changes",
    "delete_account",
    "account_deleted",
)


ACCOUNT_SETTINGS_RELATIONS = {
    "requires_confirmation_before": ("action", "consequence", "context"),
    "distinct_in_consequence": ("routine", "destructive", "context"),
}
ACCOUNT_SETTINGS_RELATION_NAMES = tuple(ACCOUNT_SETTINGS_RELATIONS)


def load_account_settings_law(project_root: Path | str) -> GovernanceProfile:
    """Select, compile, and explicitly adopt the account-settings law."""

    selected = select_authoritative_sources(project_root)
    proposed = compile_governance_law(selected)
    return adopt_governance_law(proposed)


ACCOUNT_SETTINGS_LAW = load_account_settings_law(Path(__file__).with_name("fixture"))
ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY = load_evidence_authority(
    Path(__file__).with_name("fixture")
)


ACCOUNT_SETTINGS_CONTRACT = Contract(
    "design-account-settings",
    "1",
    semantic_origins=frozenset({ConstructionOrigin.SEMANTIC.value}),
    semantic_relations=frozenset(ACCOUNT_SETTINGS_RELATION_NAMES),
    resolution_warrant_kinds=frozenset({"APPROVED_REQUIREMENT"}),
)


__all__ = [
    "ACCOUNT_SETTINGS_CONTRACT",
    "ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY",
    "ACCOUNT_SETTINGS_LAW",
    "ACCOUNT_SETTINGS_REFERENTS",
    "ACCOUNT_SETTINGS_RELATIONS",
    "ACCOUNT_SETTINGS_RELATION_NAMES",
    "load_account_settings_law",
]
