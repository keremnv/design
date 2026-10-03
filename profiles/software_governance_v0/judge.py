"""Mail profile evaluator for outbound notification routing.

The rule parameters below are the semantic basis for applicability and
conformance. They are copied into the judgment artifact. The fingerprint
identifies this function together with those parameters.
"""

from __future__ import annotations

import inspect
from typing import Any

from ontology_author.software_governance.judgment import artifact_shell, facts, method_record

RULE = {
    "applies_to_kind": "call_site",
    "excludes_kind": "callable",
    "conformance_field": "target",
    "required_target": "notificationGatewaySend",
}


def judge(case: dict[str, Any]) -> dict[str, Any]:
    method = method_record(
        method_id="mail.outbound_mail_passes",
        version="v0",
        rule=RULE,
        implementation_source=_implementation_source(),
    )
    proposition = _one(case, "governance_proposition")
    if _candidates(case, proposition) and _binding_count(case, proposition) != 1:
        return _construction_gap(case, method, proposition)
    subjects = facts(case, "software_subject")
    if len(subjects) != 1:
        kind_facts = facts(case, "program_entity_kind")
        if len(case["subject_ids"]) != 1 or not kind_facts:
            return _unlicensed(case, method, proposition, None)
        subject_id = case["subject_ids"][0]
        kind_fact = next(fact for fact in kind_facts if fact["values"].get("entity") == subject_id)
        kind = kind_fact["values"]["kind"]
        subject_assertion = kind_fact["assertion_id"]
    else:
        subject_id = subjects[0]["values"]["subject"]
        kind = subjects[0]["values"]["kind"]
        kind_fact = subjects[0]
        subject_assertion = subjects[0]["assertion_id"]
    if kind == RULE["excludes_kind"]:
        return artifact_shell(
            case,
            method=method,
            applicability={
                "result": "DOES_NOT_APPLY",
                "because": "the recorded rule excludes this subject kind",
                "assertion_ids": [subject_assertion],
                "rule": {"excludes_kind": RULE["excludes_kind"], "observed_kind": kind},
            },
            program_findings=[],
            conformance=None,
            context_requests=[],
        )
    binding = _binding(case, proposition["values"]["proposition"], subject_id)
    if binding is None or kind != RULE["applies_to_kind"]:
        return _unlicensed(case, method, proposition, kind_fact)
    resolution = _resolution(case, subject_id)
    invokes = _invokes(case, subject_id)
    if resolution is None or resolution["values"].get("status") != "RESOLVED" or len(invokes) != 1:
        status = "" if resolution is None else resolution["values"].get("status", "")
        requests = []
        if resolution is None:
            requests.append(_request(
                gap="judgment",
                proposition=proposition["values"]["proposition"],
                subject=subject_id,
                need="mechanical_target_resolution",
                availability="ABSENT",
            ))
        return artifact_shell(
            case,
            method=method,
            applicability=_applies(kind_fact, binding),
            program_findings=[
                {
                    "statement": "the call site has no unique resolved target",
                    "status": "UNRESOLVED",
                    "values": {"resolution_status": status},
                    "assertion_ids": [item["assertion_id"] for item in (resolution, *invokes) if item],
                }
            ],
            conformance={
                "result": "UNKNOWN",
                "because": "the mechanical target is not unique",
                "assertion_ids": [],
                "rule": {"conformance_field": RULE["conformance_field"]},
            },
            context_requests=requests,
        )
    target = invokes[0]["referent_labels"].get("target", "")
    finding = {
        "statement": f"this call site's resolved target is {target}",
        "status": "ESTABLISHED",
        "values": {"target": target, "resolution_status": "RESOLVED"},
        "assertion_ids": [resolution["assertion_id"], invokes[0]["assertion_id"]],
    }
    conforms = target == RULE["required_target"]
    return artifact_shell(
        case,
        method=method,
        applicability=_applies(kind_fact, binding),
        program_findings=[finding],
        conformance={
            "result": "CONFORMS" if conforms else "CONFLICTS",
            "because": "the established target matches the recorded rule" if conforms else "the established target differs from the recorded rule",
            "assertion_ids": finding["assertion_ids"],
            "rule": {"required_target": RULE["required_target"], "observed_target": target},
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
    kind_fact: dict[str, Any] | None,
) -> dict[str, Any]:
    cited = [proposition["assertion_id"]]
    if kind_fact is not None:
        cited.append(kind_fact["assertion_id"])
    return artifact_shell(
        case,
        method=method,
        applicability={
            "result": "UNKNOWN",
            "because": "no binding and no recorded exclusion; incomplete coverage does not exclude the subject",
            "assertion_ids": cited,
            "rule": {"applies_to_kind": RULE["applies_to_kind"], "excludes_kind": RULE["excludes_kind"]},
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


def _candidates(case: dict[str, Any], proposition: dict[str, Any]) -> list[dict[str, Any]]:
    proposition_id = proposition["values"]["proposition"]
    return [
        fact for fact in facts(case, "governance_candidate")
        if fact["values"]["proposition"] == proposition_id
    ]


def _binding_count(case: dict[str, Any], proposition: dict[str, Any]) -> int:
    proposition_id = proposition["values"]["proposition"]
    return len([
        fact for fact in facts(case, "governance_binding")
        if fact["values"]["proposition"] == proposition_id
    ])


def _binding(case: dict[str, Any], proposition: str, subject: str) -> dict[str, Any] | None:
    rows = [
        fact for fact in facts(case, "governance_binding")
        if fact["values"]["proposition"] == proposition and fact["values"]["software_subject"] == subject
    ]
    return rows[0] if rows else None


def _resolution(case: dict[str, Any], subject: str) -> dict[str, Any] | None:
    rows = [
        fact for fact in facts(case, "program_resolution")
        if fact["values"].get("subject") == subject
    ]
    return rows[0] if rows else None


def _invokes(case: dict[str, Any], subject: str) -> list[dict[str, Any]]:
    return [
        fact for fact in facts(case, "program_invokes")
        if fact["values"].get("call_site") == subject
    ]


def _request(**kwargs: str) -> dict[str, str]:
    return {"property": "", **kwargs}
