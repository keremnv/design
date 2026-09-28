"""Product evaluator for the config.routes/v1 customer-export rule.

This is the installed canonical judgment rule for
``config.customer_export_route/v0``. Rule parameters come from
``rules.EVALUATOR_RULE`` (single source); the verdict logic preserves the
accepted fixture behavior branch for branch. The repository fixture
evaluator keeps its own copy for acceptance; a cross-check test asserts
verdict equivalence.
"""

from __future__ import annotations

import inspect
from typing import Any

from ontology_author.config_routes.rules import (
    EVALUATOR_METHOD_ID,
    EVALUATOR_RULE as RULE,
    EVALUATOR_VERSION,
)
from ontology_author.software_governance.judgment import (
    artifact_shell,
    facts,
    method_record,
)


def evaluate_route_case(case: dict[str, Any]) -> dict[str, Any]:
    """Judge one verified case under the customer-export rule."""
    method = method_record(
        method_id=EVALUATOR_METHOD_ID,
        version=EVALUATOR_VERSION,
        rule=dict(RULE),
        implementation_source=_implementation_source(),
    )
    proposition = _one(case, "governance_proposition")
    if _candidates(case) and _binding_count(case) != 1:
        return _construction_gap(case, method, proposition)
    subjects = facts(case, "software_subject")
    if len(subjects) != 1:
        return _unlicensed(case, method, proposition, None)
    subject = subjects[0]
    subject_id = subject["values"]["subject"]
    route = _route(case, subject_id)
    if (
        route is not None
        and route["values"].get("handler")
        and route["values"]["handler"] != RULE["required_handler"]
    ):
        return artifact_shell(
            case,
            method=method,
            applicability={
                "result": "DOES_NOT_APPLY",
                "because": "the recorded rule applies to a different handler",
                "assertion_ids": [subject["assertion_id"], route["assertion_id"]],
                "rule": {
                    "required_handler": RULE["required_handler"],
                    "observed_handler": route["values"]["handler"],
                },
            },
            program_findings=[],
            conformance=None,
            context_requests=[],
        )
    binding = _binding(case, proposition["values"]["proposition"], subject_id)
    if binding is None or subject["values"]["kind"] != RULE["applies_to_kind"]:
        return _unlicensed(case, method, proposition, subject)
    if route is None or "path" not in route["values"]:
        return artifact_shell(
            case,
            method=method,
            applicability=_applies(subject, binding),
            program_findings=[],
            conformance={
                "result": "UNKNOWN",
                "because": "the route path was not in the case",
                "assertion_ids": [],
                "rule": {"conformance_field": RULE["conformance_field"]},
            },
            context_requests=[
                _request(
                    gap="judgment",
                    proposition=proposition["values"]["proposition"],
                    subject=subject_id,
                    need="subject_property",
                    property="path",
                    availability="ABSENT",
                )
            ],
        )
    path = route["values"]["path"]
    finding = {
        "statement": f"this route's path is {path}",
        "status": "ESTABLISHED",
        "values": {"path": path},
        "assertion_ids": [route["assertion_id"]],
    }
    conforms = path == RULE["required_path"]
    return artifact_shell(
        case,
        method=method,
        applicability=_applies(subject, binding),
        program_findings=[finding],
        conformance={
            "result": "CONFORMS" if conforms else "CONFLICTS",
            "because": "the established path matches the recorded rule" if conforms else "the established path differs from the recorded rule",
            "assertion_ids": [route["assertion_id"]],
            "rule": {"required_path": RULE["required_path"], "observed_path": path},
        },
        context_requests=[],
    )


def _implementation_source() -> str:
    module = inspect.getmodule(_implementation_source)
    functions = [
        value
        for value in vars(module).values()
        if inspect.isfunction(value) and getattr(value, "__module__", None) == module.__name__
    ]
    return "".join(inspect.getsource(value) for value in sorted(functions, key=lambda item: item.__name__))


def _construction_gap(case: dict[str, Any], method: dict[str, Any], proposition: dict[str, Any]) -> dict[str, Any]:
    return artifact_shell(
        case,
        method=method,
        applicability={
            "result": "UNKNOWN",
            "because": "construction left the correspondence unresolved",
            "assertion_ids": [proposition["assertion_id"]],
            "rule": {},
        },
        program_findings=[],
        conformance=None,
        context_requests=[
            _request(
                gap="construction",
                proposition=proposition["values"]["proposition"],
                subject="",
                need="established_binding",
                availability="ABSENT",
            )
        ],
    )


def _unlicensed(
    case: dict[str, Any],
    method: dict[str, Any],
    proposition: dict[str, Any],
    subject: dict[str, Any] | None,
) -> dict[str, Any]:
    cited = [proposition["assertion_id"]]
    if subject is not None:
        cited.append(subject["assertion_id"])
    return artifact_shell(
        case,
        method=method,
        applicability={
            "result": "UNKNOWN",
            "because": "no binding and no recorded exclusion; incomplete coverage does not exclude the subject",
            "assertion_ids": cited,
            "rule": {"required_handler": RULE["required_handler"]},
        },
        program_findings=[],
        conformance=None,
        context_requests=[],
    )


def _applies(subject: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "result": "APPLIES",
        "because": "an established binding joins this proposition to a subject of the ruled kind",
        "assertion_ids": [subject["assertion_id"], binding["assertion_id"]],
        "rule": {"applies_to_kind": RULE["applies_to_kind"]},
    }


def _one(case: dict[str, Any], relation: str) -> dict[str, Any]:
    rows = facts(case, relation)
    if len(rows) != 1:
        raise KeyError(relation)
    return rows[0]


def _candidates(case: dict[str, Any]) -> list[dict[str, Any]]:
    return facts(case, "governance_candidate")


def _binding_count(case: dict[str, Any]) -> int:
    return len(facts(case, "governance_binding"))


def _binding(case: dict[str, Any], proposition: str, subject: str) -> dict[str, Any] | None:
    rows = [
        fact for fact in facts(case, "governance_binding")
        if fact["values"]["proposition"] == proposition and fact["values"]["software_subject"] == subject
    ]
    return rows[0] if rows else None


def _route(case: dict[str, Any], subject: str) -> dict[str, Any] | None:
    rows = [
        fact for fact in facts(case, "config_route")
        if fact["values"].get("subject") == subject
    ]
    return rows[0] if rows else None


def _request(**kwargs: str) -> dict[str, str]:
    return kwargs
