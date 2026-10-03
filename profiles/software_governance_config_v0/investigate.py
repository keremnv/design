"""Config-profile investigation over a sealed route World.

The helper may read mechanical facts and any capability the caller supplies.
It does not judge. A source field this producer did not assert becomes a
proposal, not a case citation. A copied judgment request does not limit
which mechanical relations are inspected.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from ontology_author.software_governance.investigation import (
    added_assertion_ids,
    expanded_case,
    make_proposal,
    make_receipt,
)
from ontology_author.software_governance.reads import GovernanceView

METHOD_ID = "config.subject-investigation"
PUBLISHED_SOURCE_KEYS = frozenset({"id", "path", "handler"})


def investigate(
    view: GovernanceView,
    case: dict[str, Any],
    question: dict[str, Any],
    capabilities: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    subject = str(question["subject"])
    mechanical = view.mechanical_facts_for_subject(subject)
    inspected = sorted({str(item["relation"]) for item in mechanical})
    unpublished = _unpublished(subject, mechanical, question, capabilities, inspected)
    missing = [item for item in mechanical if not _case_has(case, item)]
    if unpublished:
        proposal = _proposal(case, question, unpublished)
        outcome = "PROPOSAL"
        child = None
        added: list[str] = []
    elif missing:
        child = expanded_case(view, case, case_id=f"{case['case_id']}-expanded")
        added = added_assertion_ids(case, child)
        proposal = None
        outcome = "CASE_EXPANDED"
    else:
        child = None
        added = []
        proposal = None
        outcome = "UNRESOLVED"
    receipt = make_receipt(
        question_id=str(question["question_id"]),
        parent_case_id=str(case["case_id"]),
        world_id=str(case["world_id"]),
        revision=int(case["revision"]),
        world_address=str(case["world_address"]),
        method_id=METHOD_ID,
        capabilities=tuple(capabilities),
        outcome=outcome,
        resulting_case_id=None if child is None else str(child["case_id"]),
        added_assertion_ids=added,
        proposal_id=None if proposal is None else str(proposal["proposal_id"]),
        inspected_relations=inspected,
    )
    return {"outcome": outcome, "case": child, "proposal": proposal, "receipt": receipt}


def _unpublished(
    subject: str,
    mechanical: list[dict[str, Any]],
    question: dict[str, Any],
    capabilities: dict[str, Callable[..., Any]],
    inspected: list[str],
) -> dict[str, Any] | None:
    reader = capabilities.get("manifestation-text")
    if reader is None:
        return None
    manifested = reader(subject)
    inspected.append("software_manifestation")
    if not isinstance(manifested, dict) or manifested.get("status") != "OK":
        return None
    try:
        payload = json.loads(str(manifested["content"]))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    sealed_fields = {key for item in mechanical for key in item["values"]}
    for key, value in payload.items():
        if key in PUBLISHED_SOURCE_KEYS or key in sealed_fields:
            continue
        if _relevant(str(key), question):
            return {
                "field": str(key),
                "value": value,
                "content_digest": str(manifested.get("content_digest") or ""),
                "scheme": str(manifested.get("scheme") or ""),
                "location": str(manifested.get("location") or ""),
                "text": str(manifested["content"]),
            }
    return None


def _relevant(key: str, question: dict[str, Any]) -> bool:
    need = question.get("structured_need") or {}
    if need.get("property") == key:
        return True
    return key in str(question["question"])


def _proposal(
    case: dict[str, Any],
    question: dict[str, Any],
    discovered: dict[str, Any],
) -> dict[str, Any]:
    return make_proposal(
        proposal_id=f"proposal:{question['question_id']}",
        originating_case_id=str(case["case_id"]),
        originating_question_id=str(question["question_id"]),
        epistemic_class="mechanical",
        payload={"field": discovered["field"], "value": discovered["value"]},
        basis={
            "kind": "reconstructed-manifestation",
            "scheme": discovered["scheme"],
            "location": discovered["location"],
            "content_digest": discovered["content_digest"],
            "text": discovered["text"],
        },
        method={"id": METHOD_ID, "capability": "manifestation-text"},
        reason=(
            "the sealed world has no assertion for this field; "
            "reconstructed source text is not an assertion"
        ),
    )


def _case_has(case: dict[str, Any], item: dict[str, Any]) -> bool:
    values = {str(key): str(value) for key, value in item["values"].items()}
    return any(
        fact["relation"] == item["relation"] and fact["values"] == values
        for fact in case["facts"]
    )
