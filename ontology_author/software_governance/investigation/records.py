"""Investigation question, receipt, and proposal records.

These records sit outside the sealed World and outside the Judgment case.
A proposal is not an assertion.
"""

from __future__ import annotations

from typing import Any

EPISTEMIC_CLASSES = ("mechanical", "semantic", "source/evidence", "other")
OUTCOMES = ("CASE_EXPANDED", "PROPOSAL", "UNRESOLVED")
ORIGIN_KINDS = ("judgment_request", "open")


class InvestigationBoundary(Exception):
    """The investigation tried to leave the sealed publication or the case contract."""


def make_question(
    *,
    question_id: str,
    question: str,
    purpose: str,
    proposition: str,
    subject: str,
    origin: dict[str, Any],
    structured_need: dict[str, str] | None = None,
) -> dict[str, Any]:
    kind = origin.get("kind")
    if kind not in ORIGIN_KINDS or not str(origin.get("case_id") or ""):
        raise InvestigationBoundary("origin needs a case id and kind judgment_request or open")
    record: dict[str, Any] = {
        "question_id": question_id,
        "question": question,
        "purpose": purpose,
        "proposition": proposition,
        "subject": subject,
        "origin": {
            "case_id": str(origin["case_id"]),
            "kind": kind,
        },
    }
    if origin.get("request") is not None:
        record["origin"]["request"] = origin["request"]
    if structured_need is not None:
        if "need" not in structured_need or "property" not in structured_need:
            raise InvestigationBoundary("structured need requires need and property")
        record["structured_need"] = {
            "need": str(structured_need["need"]),
            "property": str(structured_need["property"]),
        }
    return record


def make_proposal(
    *,
    proposal_id: str,
    originating_case_id: str,
    originating_question_id: str,
    epistemic_class: str,
    payload: dict[str, Any],
    basis: dict[str, Any],
    method: dict[str, str],
    reason: str,
) -> dict[str, Any]:
    if epistemic_class not in EPISTEMIC_CLASSES:
        raise InvestigationBoundary(f"unknown epistemic class {epistemic_class}")
    if "assertion_id" in payload or "assertion_id" in basis:
        raise InvestigationBoundary("a proposal is not an assertion")
    return {
        "proposal_id": proposal_id,
        "originating_case_id": originating_case_id,
        "originating_question_id": originating_question_id,
        "epistemic_class": epistemic_class,
        "payload": dict(payload),
        "basis": dict(basis),
        "method": dict(method),
        "reason": reason,
    }


def make_receipt(
    *,
    question_id: str,
    parent_case_id: str,
    world_id: str,
    revision: int,
    world_address: str,
    method_id: str,
    capabilities: tuple[str, ...] | list[str],
    outcome: str,
    resulting_case_id: str | None,
    added_assertion_ids: list[str],
    proposal_id: str | None,
    inspected_relations: list[str],
) -> dict[str, Any]:
    if outcome not in OUTCOMES:
        raise InvestigationBoundary(f"unknown outcome {outcome}")
    if outcome == "CASE_EXPANDED" and (not resulting_case_id or proposal_id is not None):
        raise InvestigationBoundary("case expansion records a resulting case and no proposal")
    if outcome == "PROPOSAL" and (not proposal_id or resulting_case_id is not None or added_assertion_ids):
        raise InvestigationBoundary("a proposal records no expanded case")
    if outcome == "UNRESOLVED" and (resulting_case_id or proposal_id or added_assertion_ids):
        raise InvestigationBoundary("an unresolved investigation adds nothing")
    return {
        "question_id": question_id,
        "parent_case_id": parent_case_id,
        "world_id": world_id,
        "revision": revision,
        "world_address": world_address,
        "method": {"id": method_id, "capabilities": list(capabilities)},
        "outcome": outcome,
        "resulting_case_id": resulting_case_id,
        "added_assertion_ids": list(added_assertion_ids),
        "proposal_id": proposal_id,
        "inspected_relations": list(inspected_relations),
    }
