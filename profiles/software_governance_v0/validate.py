"""Admission rules for the source-backed TypeScript mail profile.

These rules are narrower than generic Software Governance validation.
"""

from __future__ import annotations

from ontology_author.evidence.program_source import (
    program_source_observations,
    reconstruct_program_observation,
)
from ontology_author.program_spine.typescript import EXTRACTOR_ID
from ontology_author.software_governance.reads import GovernanceView
from ontology_author.world.runtime.world import ConstructionWorld

PROFILE_SUPPORT = "SOURCE_EXPLICIT"
PROFILE_BINDING_RESOLUTION = "DETERMINISTIC"
PROFILE_CANDIDATE_RESOLUTIONS = frozenset({"AMBIGUOUS", "UNRESOLVED"})


def validate_mail_profile(world: ConstructionWorld) -> list[str]:
    errors: list[str] = []
    extractors = [
        str(row["extractor"])
        for row in world.relation_rows("program_snapshot")
    ] if _has(world, "program_snapshot") else []
    if not any(item.startswith(EXTRACTOR_ID) for item in extractors):
        errors.append("mail profile requires the TypeScript program spine extractor")
    view = GovernanceView(world)
    for row in world.relation_rows("governance_binding"):
        subject = str(row["software_subject"])
        inspected = view.inspect_governance_binding(str(row["proposition"]), subject)
        errors.extend(_correspondence_errors(
            "governance_binding",
            str(row["proposition"]),
            support=str(inspected["relation_support"] or ""),
            resolution=str(inspected["endpoint_resolution"] or ""),
            positive=PROFILE_BINDING_RESOLUTION,
        ))
        errors.extend(_source_errors(world, subject))
    propositions = {str(row["proposition"]) for row in world.relation_rows("governance_candidate")}
    for proposition in sorted(propositions):
        for item in view.binding_candidates_for_proposition(proposition)["candidates"]:
            subject = str(item["software_subject"])
            errors.extend(_correspondence_errors(
                "governance_candidate",
                proposition,
                support=str(item["relation_support"] or ""),
                resolution=str(item["endpoint_resolution"] or ""),
                positive=None,
            ))
            errors.extend(_source_errors(world, subject))
    return errors


def _correspondence_errors(
    relation: str,
    proposition: str,
    *,
    support: str,
    resolution: str,
    positive: str | None,
) -> list[str]:
    errors: list[str] = []
    if support != PROFILE_SUPPORT:
        errors.append(
            f"{relation} {proposition} support {support!r} is not {PROFILE_SUPPORT}"
        )
    if positive is None:
        if resolution not in PROFILE_CANDIDATE_RESOLUTIONS:
            errors.append(
                f"{relation} {proposition} resolution {resolution!r} is not a profile candidate resolution"
            )
    elif resolution != positive:
        errors.append(
            f"{relation} {proposition} resolution {resolution!r} is not {positive}"
        )
    return errors


def _source_errors(world: ConstructionWorld, subject: str) -> list[str]:
    observations = program_source_observations(world, subject)
    if len(observations) != 1:
        return [f"mail profile subject {subject} does not have one reconstructible source observation"]
    _text, status = reconstruct_program_observation(world, observations[0])
    if status != "OK":
        return [f"mail profile subject {subject} source did not reconstruct"]
    return []


def _has(world: ConstructionWorld, relation: str) -> bool:
    try:
        world.relation_schema(relation)
    except Exception:
        return False
    return True
