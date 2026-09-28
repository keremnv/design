"""Expand a Judgment case only inside its sealed publication.

Citation checks are Judgment's. This module rejects a different publication
before those checks run, and it does not write the World.
"""

from __future__ import annotations

import copy
from typing import Any

from ontology_author.software_governance.investigation.records import InvestigationBoundary
from ontology_author.software_governance.judgment import assemble_case, verify_case
from ontology_author.software_governance.reads import GovernanceView


def expanded_case(view: GovernanceView, parent: dict[str, Any], *, case_id: str) -> dict[str, Any]:
    """Assemble an ordinary Judgment case for the parent's publication.

    The caller supplies the opened World. A different publication address is
    rejected before any citation is copied across. ``world_id`` alone does
    not identify the publication.
    """

    if str(view.world.path.parent) != parent["world_address"]:
        raise InvestigationBoundary("the opened world is not the case publication")
    if view.world.world_id != parent["world_id"]:
        raise InvestigationBoundary("world id differs")
    child = assemble_case(
        view,
        case_id=case_id,
        question=str(parent["question"]),
        proposition_ids=tuple(parent["proposition_ids"]),
        subject_ids=tuple(parent["subject_ids"]),
    )
    if child["revision"] != parent["revision"]:
        raise InvestigationBoundary("revision differs")
    errors = verify_case(view, child)
    if errors:
        raise InvestigationBoundary("; ".join(errors))
    if child["proposition_ids"] != parent["proposition_ids"]:
        raise InvestigationBoundary("proposition changed")
    if child["subject_ids"] != parent["subject_ids"]:
        raise InvestigationBoundary("subject changed")
    parent_ids = {fact["assertion_id"] for fact in parent["facts"]}
    child_ids = {fact["assertion_id"] for fact in child["facts"]}
    if not parent_ids <= child_ids:
        raise InvestigationBoundary("expansion removed citations")
    return child


def added_assertion_ids(parent: dict[str, Any], child: dict[str, Any]) -> list[str]:
    parent_ids = {fact["assertion_id"] for fact in parent["facts"]}
    return [
        fact["assertion_id"]
        for fact in child["facts"]
        if fact["assertion_id"] not in parent_ids
    ]


def citation_errors(view: GovernanceView, case: dict[str, Any], fact: dict[str, Any]) -> list[str]:
    """Append one citation and return Judgment's verification errors.

    The sealed World is only read. This does not implement a second citation check.
    """

    cloned = copy.deepcopy(case)
    cloned["facts"] = [*case["facts"], fact]
    return verify_case(view, cloned)
