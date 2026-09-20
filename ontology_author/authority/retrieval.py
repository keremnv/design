"""Recover exact authoritative evidence from ProgramDelta + persisted warrants.

This helper does not migrate, renew, or adjudicate attachments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ontology_author.program_spine.comparison import ProgramDelta, SpineComparisonResult
from ontology_author.world.runtime.world import ConstructionWorld

from ontology_author.evidence.markdown import MarkdownSource
from .validation import observations_for_assertion


@dataclass(frozen=True)
class RecoveredAuthority:
    program_entity: str
    assertion_id: str
    handle: str
    native_location: str
    revision: str
    text: str
    delta_kind: str
    correspondence_continuity: str = ""
    correspondence_basis: str = ""
    migrated: bool = False


def affected_program_entities(delta: ProgramDelta) -> dict[str, str]:
    """Old program identities whose mechanical relations changed."""

    affected: dict[str, str] = {}
    invokes = delta.relations.get("program_invokes") or {}
    for item in invokes.get("retargeted") or []:
        old = item.get("old") or {}
        call_site = str(old.get("call_site") or "")
        if call_site:
            affected[call_site] = "relation_retarget"
        target = str(old.get("target") or "")
        if target:
            affected.setdefault(target, "relation_retarget")
    for item in invokes.get("removed") or []:
        old = item.get("old") or {}
        call_site = str(old.get("call_site") or "")
        if call_site:
            affected[call_site] = "relation_removed"
    for record in delta.maintenance:
        if record.get("retargeted_relations"):
            old_entity = str(record.get("old_entity") or "")
            if old_entity:
                affected.setdefault(old_entity, "maintenance_retarget")
    return affected


def recover_authority_for_delta(
    world: ConstructionWorld,
    delta: ProgramDelta,
    sources: Mapping[str, MarkdownSource],
    *,
    comparison: SpineComparisonResult | None = None,
) -> tuple[RecoveredAuthority, ...]:
    """Select persisted attachments for changed old identities and reconstruct evidence.

    CONTINUED + HEURISTIC correspondence is recorded when present. It never
    copies or validates the attachment onto the new snapshot.
    """

    affected = affected_program_entities(delta)
    continuity: dict[str, tuple[str, str]] = {}
    if comparison is not None:
        for claim in comparison.correspondences:
            if claim.old_entity:
                continuity[str(claim.old_entity)] = (claim.continuity, claim.basis_class)

    recovered: list[RecoveredAuthority] = []
    for warrant in world.relation_rows("authority_attachment_warrant"):
        entity = str(warrant["program_entity"])
        if entity not in affected:
            continue
        assertion_id = str(warrant["assertion_id"])
        status, basis = continuity.get(entity, ("", ""))
        for observation in observations_for_assertion(world, assertion_id):
            source = sources.get(observation.native_handle)
            if source is None:
                continue
            recovered.append(
                RecoveredAuthority(
                    program_entity=entity,
                    assertion_id=assertion_id,
                    handle=observation.native_handle,
                    native_location=observation.native_location,
                    revision=observation.source_revision,
                    text=source.reconstruct(observation),
                    delta_kind=affected[entity],
                    correspondence_continuity=status,
                    correspondence_basis=basis,
                    migrated=False,
                )
            )
    return tuple(recovered)
