"""Runtime-neutral GovernanceAdjudication artifact substrate.

This is not an adjudicator. Humans, models, and deterministic checks emit the
same sidecar. Findings are not written into either World.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


ADJUDICATION_SCHEMA = "governance_adjudication/v0"
ADJUDICATION_VERSION = 0
DEFAULT_DECISION_SUBJECT = "ADOPT_OR_KEEP_NEW_PROGRAM_STATE"

ADJUDICATOR_KINDS = {"HUMAN", "MODEL", "DETERMINISTIC_CHECK"}
APPLICABILITY = {"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"}
TRUTH = {"TRUE", "FALSE", "UNKNOWN"}
BASIS = {"MECHANICAL", "INTERPRETIVE"}
HEURISTIC_DEPENDENCE = {"MATERIAL", "NOT_MATERIAL", "UNKNOWN"}
FINDING_CONTEXT = {"SUFFICIENT", "INSUFFICIENT", "UNKNOWN"}
CONFORMANCE = {"CONFORMS", "CONFLICTS", "UNKNOWN", "NOT_APPLICABLE"}
DECISION_RIGHT = {
    "DELEGATED",
    "CONSTRAINED",
    "PROHIBITED",
    "APPROVAL_REQUIRED",
    "UNKNOWN",
    "NOT_ESTABLISHED",
}
ADJUDICATION_STATES = {"RESOLVED", "UNRESOLVED", "AUTHORITY_CONFLICT", "INSUFFICIENT_CONTEXT"}
SOURCE_KINDS = {
    "IMPLEMENTATION",
    "SIGNATURE",
    "CALLERS_IN_DECLARED_SCOPE",
    "CALLEES",
    "NAMED_RELATION",
    "CANDIDATE_IMPLEMENTATIONS",
}
MECHANICAL_EVIDENCE_KINDS = {
    "relation_tuple",
    "delta",
    "triggering_delta",
    "program_referent",
    "program_relation",
    "resolution_outcome",
}
PROGRAM_SOURCE_KIND = "program_source"
AUTHORITY_OBS_KIND = "authority_observation"
SUPPORTING_KIND = "supporting_material"
CLAIM_KIND = "claim"

FORBIDDEN_FIELD_NAMES = {
    "confidence",
    "score",
    "relevance_score",
    "verdict",
    "pass",
    "fail",
    "compliance",
    "compliant",
    "noncompliant",
    "non_compliant",
    "violation",
    "violations",
    "chain_of_thought",
    "chainofthought",
    "hidden_prompt",
    "private_reasoning",
    "deliberation",
    "scratchpad",
    "prompt",
    "system_prompt",
    "supplied_source",
}


class AdjudicationError(ValueError):
    """The adjudication artifact violates its application contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:32]


def _copy(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return keys


def _index_case(case: Mapping[str, Any]) -> dict[str, set[str]]:
    authority_obs = {
        str(item.get("observation_id") or "")
        for item in (case.get("authority") or {}).get("observations") or []
        if item.get("observation_id")
    }
    supporting = {
        str(item.get("observation_id") or "")
        for item in case.get("supporting_material") or []
        if item.get("observation_id")
    }
    claims = {
        str(item.get("assertion_id") or "")
        for item in (case.get("authority") or {}).get("claims") or []
        if item.get("assertion_id")
    }
    program_source = {
        str(item.get("evidence_id") or "")
        for item in (case.get("program_context") or {}).get("source_evidence") or []
        if item.get("evidence_id")
    }
    referents = {
        str(item.get("id") or "")
        for item in (case.get("program_context") or {}).get("referents") or []
        if item.get("id")
    }
    selections = {
        str(item.get("attachment_assertion_id") or "")
        for item in case.get("selection") or []
        if item.get("attachment_assertion_id")
    }
    return {
        "authority_observation": authority_obs,
        "supporting_material": supporting,
        "claim": claims,
        "program_source": program_source,
        "program_referent": referents,
        "attachment": selections,
    }


def _normalize_evidence(refs: Sequence[Any] | None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in refs or []:
        if isinstance(item, Mapping):
            kind = str(item.get("kind") or "").strip()
            ref_id = str(item.get("id") or item.get("evidence_id") or item.get("observation_id") or "").strip()
            if kind or ref_id:
                row = {"kind": kind, "id": ref_id}
                if item.get("path"):
                    row["path"] = str(item["path"])
                output.append(row)
        elif item:
            output.append({"kind": "", "id": str(item)})
    output.sort(key=lambda item: (item.get("kind") or "", item.get("id") or ""))
    return output


def _normalize_finding_context(item: Mapping[str, Any]) -> tuple[str, list[str]]:
    status = str(item.get("finding_context") or item.get("context_sufficiency") or "SUFFICIENT").upper()
    if status not in FINDING_CONTEXT:
        status = "UNKNOWN"
    reasons = [str(reason) for reason in item.get("context_reasons") or item.get("reasons") or [] if str(reason).strip()]
    return status, sorted(set(reasons))


def rollup_context_sufficiency(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    statuses = [str(item.get("finding_context") or "") for item in items]
    reasons: list[str] = []
    for item in items:
        reasons.extend(str(reason) for reason in item.get("context_reasons") or [] if str(reason).strip())
    if any(status == "INSUFFICIENT" for status in statuses):
        status = "INSUFFICIENT"
    elif any(status == "UNKNOWN" for status in statuses):
        status = "UNKNOWN"
    else:
        status = "SUFFICIENT"
    return {"status": status, "reasons": sorted(set(reasons))}


def rollup_adjudication_state(
    *,
    context_sufficiency: Mapping[str, Any],
    authority_findings: Sequence[Mapping[str, Any]],
    program_findings: Sequence[Mapping[str, Any]],
    conformance_findings: Sequence[Mapping[str, Any]],
    authority_conflicts: Sequence[Mapping[str, Any]],
    context_requests: Sequence[Mapping[str, Any]],
) -> str:
    items = (*authority_findings, *program_findings)
    if str(context_sufficiency.get("status") or "") == "INSUFFICIENT" or any(
        str(item.get("finding_context") or "") == "INSUFFICIENT" for item in items
    ):
        return "INSUFFICIENT_CONTEXT"
    if authority_conflicts:
        return "AUTHORITY_CONFLICT"
    if any(str(item.get("applicability") or "") == "UNKNOWN" for item in authority_findings):
        return "UNRESOLVED"
    if any(str(item.get("truth_value") or "") == "UNKNOWN" for item in program_findings):
        return "UNRESOLVED"
    if any(str(item.get("result") or "") == "UNKNOWN" for item in conformance_findings):
        return "UNRESOLVED"
    if str(context_sufficiency.get("status") or "") == "UNKNOWN":
        return "UNRESOLVED"
    if context_requests:
        return "UNRESOLVED"
    return "RESOLVED"


def _assign_id(prefix: str, item: Mapping[str, Any], fields: Sequence[str]) -> str:
    existing = str(item.get("finding_id") or item.get("conflict_id") or item.get("request_id") or "").strip()
    if existing:
        return existing
    payload = {field: item.get(field) for field in fields}
    return f"{prefix}:{_digest(payload)}"


def create_governance_adjudication(
    case: Mapping[str, Any],
    *,
    adjudicator: Mapping[str, Any],
    authority_findings: Sequence[Mapping[str, Any]] = (),
    program_findings: Sequence[Mapping[str, Any]] = (),
    conformance_findings: Sequence[Mapping[str, Any]] = (),
    authority_conflicts: Sequence[Mapping[str, Any]] = (),
    decision_right: Mapping[str, Any],
    context_requests: Sequence[Mapping[str, Any]] = (),
    rationale: Sequence[Mapping[str, Any]] = (),
    unresolved_questions: Sequence[Any] = (),
    case_summary: str = "",
    known_limitations: Sequence[Any] = (),
    empty_case_note: str = "",
    context_sufficiency: Mapping[str, Any] | None = None,
    adjudication_state: str | None = None,
    validate: bool = True,
) -> dict[str, Any]:
    """Assemble ``governance.adjudication.json``. Does not adjudicate or mutate Worlds."""

    case_id = str(case.get("case_id") or "").strip()
    if not case_id:
        raise AdjudicationError("GovernanceCase is missing case_id")
    kind = str(adjudicator.get("kind") or "").upper()
    if kind not in ADJUDICATOR_KINDS:
        raise AdjudicationError(f"unknown adjudicator kind {adjudicator.get('kind')!r}")
    authorities: list[dict[str, Any]] = []
    for item in authority_findings:
        row = _copy(item)
        context, reasons = _normalize_finding_context(row)
        evidence = _normalize_evidence(row.get("evidence_refs") or row.get("supporting_case_facts"))
        row.update(
            {
                "finding_id": _assign_id(
                    "afinding",
                    row,
                    ("observation_ids", "applicability", "interpretation_summary"),
                ),
                "observation_ids": sorted({str(obs) for obs in row.get("observation_ids") or [] if str(obs)}),
                "attachment_refs": sorted({str(obs) for obs in row.get("attachment_refs") or [] if str(obs)}),
                "applicability": str(row.get("applicability") or "UNKNOWN").upper(),
                "interpretation_summary": str(row.get("interpretation_summary") or ""),
                "relevant_qualifiers": list(row.get("relevant_qualifiers") or []),
                "supporting_case_facts": _copy(row.get("supporting_case_facts") or []),
                "supporting_context_refs": _copy(row.get("supporting_context_refs") or []),
                "evidence_refs": evidence,
                "applicability_basis": str(row.get("applicability_basis") or ""),
                "finding_context": context,
                "context_reasons": reasons,
                "selected_because_ignored": True,
            }
        )
        authorities.append(row)
    programs: list[dict[str, Any]] = []
    for item in program_findings:
        row = _copy(item)
        context, reasons = _normalize_finding_context(row)
        row.update(
            {
                "finding_id": _assign_id("pfinding", row, ("proposition", "truth_value", "side", "basis")),
                "proposition": str(row.get("proposition") or ""),
                "truth_value": str(row.get("truth_value") or "UNKNOWN").upper(),
                "side": str(row.get("side") or "NEW").upper(),
                "basis": str(row.get("basis") or "").upper(),
                "heuristic_dependence": str(row.get("heuristic_dependence") or "UNKNOWN").upper(),
                "evidence_refs": _normalize_evidence(row.get("evidence_refs")),
                "finding_context": context,
                "context_reasons": reasons,
                "limitations": list(row.get("limitations") or []),
            }
        )
        programs.append(row)
    conformances: list[dict[str, Any]] = []
    for item in conformance_findings:
        row = _copy(item)
        prior = row.get("prior_state")
        row.update(
            {
                "finding_id": _assign_id(
                    "cfinding",
                    row,
                    ("authority_finding_refs", "program_finding_refs", "result"),
                ),
                "authority_finding_refs": sorted(
                    {str(obs) for obs in row.get("authority_finding_refs") or [] if str(obs)}
                ),
                "program_finding_refs": sorted(
                    {str(obs) for obs in row.get("program_finding_refs") or [] if str(obs)}
                ),
                "result": str(row.get("result") or "UNKNOWN").upper(),
                "prior_state": None if prior in {None, ""} else str(prior).upper(),
            }
        )
        conformances.append(row)
    conflicts: list[dict[str, Any]] = []
    for item in authority_conflicts:
        row = _copy(item)
        row.update(
            {
                "conflict_id": _assign_id("aconflict", row, ("authority_finding_refs", "issue")),
                "authority_finding_refs": sorted(
                    {str(obs) for obs in row.get("authority_finding_refs") or [] if str(obs)}
                ),
                "issue": str(row.get("issue") or ""),
                "precedence": str(row.get("precedence") or "UNESTABLISHED").upper(),
                "resolution": str(row.get("resolution") or "unresolved"),
            }
        )
        conflicts.append(row)
    requests: list[dict[str, Any]] = []
    for item in context_requests:
        row = _copy(item)
        row.update(
            {
                "request_id": _assign_id("creq", row, ("reason", "program_identities", "source_evidence_requested")),
                "reason": str(row.get("reason") or ""),
                "program_identities": sorted({str(obs) for obs in row.get("program_identities") or [] if str(obs)}),
                "relation_or_context_needed": list(row.get("relation_or_context_needed") or []),
                "source_evidence_requested": _copy(row.get("source_evidence_requested") or []),
                "would_enable": str(row.get("would_enable") or ""),
            }
        )
        requests.append(row)
    rationale_rows = []
    for item in rationale:
        row = _copy(item) if isinstance(item, Mapping) else {"statement": str(item), "evidence_refs": []}
        row["statement"] = str(row.get("statement") or "")
        row["evidence_refs"] = _normalize_evidence(row.get("evidence_refs"))
        row["supports"] = row.get("supports") or []
        rationale_rows.append(row)
    rolled = rollup_context_sufficiency([*authorities, *programs])
    sufficiency = _copy(context_sufficiency) if context_sufficiency is not None else rolled
    if "status" in sufficiency:
        sufficiency["status"] = str(sufficiency["status"]).upper()
    sufficiency.setdefault("reasons", rolled["reasons"])
    right = _copy(decision_right)
    right["subject"] = str(right.get("subject") or DEFAULT_DECISION_SUBJECT)
    right["outcome"] = str(right.get("outcome") or "").upper()
    right["authority_basis_refs"] = sorted(
        {
            str(obs)
            for obs in (right.get("authority_basis_refs") or right.get("authority_basis") or [])
            if str(obs)
        }
    )
    right["rationale"] = str(right.get("rationale") or "")
    related = []
    for item in right.get("related_rights") or []:
        rel = _copy(item)
        rel["subject"] = str(rel.get("subject") or "")
        rel["outcome"] = str(rel.get("outcome") or "").upper()
        rel["authority_basis_refs"] = sorted(
            {str(obs) for obs in rel.get("authority_basis_refs") or [] if str(obs)}
        )
        related.append(rel)
    right["related_rights"] = related
    state = adjudication_state or rollup_adjudication_state(
        context_sufficiency=sufficiency,
        authority_findings=authorities,
        program_findings=programs,
        conformance_findings=conformances,
        authority_conflicts=conflicts,
        context_requests=requests,
    )
    state = str(state).upper()
    payload = {
        "contract": ADJUDICATION_SCHEMA,
        "adjudication_version": ADJUDICATION_VERSION,
        "case_id": case_id,
        "adjudicator": {
            "kind": kind,
            "identity": str(adjudicator.get("identity") or ""),
            "version": str(adjudicator.get("version") or ""),
            "configuration": _copy(adjudicator.get("configuration") or {}),
        },
        "context_sufficiency": {
            "status": str(sufficiency.get("status") or "UNKNOWN"),
            "reasons": list(sufficiency.get("reasons") or []),
        },
        "authority_findings": authorities,
        "program_findings": programs,
        "conformance_findings": conformances,
        "authority_conflicts": conflicts,
        "decision_right": right,
        "unresolved_questions": list(unresolved_questions),
        "context_requests": requests,
        "rationale": rationale_rows,
        "case_summary": str(case_summary),
        "adjudication_state": state,
        "known_limitations": list(known_limitations),
        "empty_case_note": str(empty_case_note),
    }
    identifiable = {key: value for key, value in payload.items() if key != "adjudication_id"}
    payload["adjudication_id"] = "adjudication:" + _digest(identifiable)
    payload = json.loads(_canonical_json(payload))
    if validate:
        errors = validate_governance_adjudication(payload, case)
        if errors:
            raise AdjudicationError("; ".join(errors))
    return payload


def validate_governance_adjudication(payload: Mapping[str, Any], case: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("contract") != ADJUDICATION_SCHEMA:
        errors.append("adjudication sidecar contract is not governance_adjudication/v0")
    if payload.get("case_id") != case.get("case_id"):
        errors.append("adjudication case_id does not match the GovernanceCase")
    if not case.get("case_id"):
        errors.append("unknown case IDs")
    adjudicator = payload.get("adjudicator") or {}
    if adjudicator.get("kind") not in ADJUDICATOR_KINDS:
        errors.append(f"invalid adjudicator kind: {adjudicator.get('kind')}")
    if payload.get("adjudication_state") not in ADJUDICATION_STATES:
        errors.append(f"invalid adjudication_state: {payload.get('adjudication_state')}")
    sufficiency = payload.get("context_sufficiency") or {}
    if sufficiency.get("status") not in FINDING_CONTEXT:
        errors.append(f"invalid context_sufficiency: {sufficiency.get('status')}")
    for key in _walk_keys(payload):
        if key.lower() in FORBIDDEN_FIELD_NAMES:
            errors.append(f"adjudication contains forbidden field {key}")
    index = _index_case(case)
    finding_ids = {
        str(item.get("finding_id") or "")
        for item in [
            *(payload.get("authority_findings") or []),
            *(payload.get("program_findings") or []),
            *(payload.get("conformance_findings") or []),
        ]
        if item.get("finding_id")
    }
    applies = []
    insufficient_items = False
    for item in payload.get("authority_findings") or []:
        applicability = str(item.get("applicability") or "")
        if applicability not in APPLICABILITY:
            errors.append(f"invalid applicability: {applicability}")
        if applicability == "APPLIES":
            applies.append(item)
        context = str(item.get("finding_context") or "")
        if context not in FINDING_CONTEXT:
            errors.append(f"invalid finding_context: {context}")
        if context == "INSUFFICIENT":
            insufficient_items = True
        observations = [str(obs) for obs in item.get("observation_ids") or []]
        if not observations:
            errors.append(f"{item.get('finding_id')} used a normalized claim as sole authority")
        for obs_id in observations:
            if obs_id in index["supporting_material"]:
                errors.append("supporting material cannot govern")
            elif obs_id not in index["authority_observation"]:
                errors.append(f"authority observation is not in the case: {obs_id}")
        for ref in item.get("attachment_refs") or []:
            if str(ref) not in index["attachment"] and str(ref) not in index["claim"]:
                errors.append(f"attachment ref is not in the case: {ref}")
        if applicability == "DOES_NOT_APPLY" and not str(item.get("applicability_basis") or "").strip():
            errors.append("DOES_NOT_APPLY requires a positive cited basis")
        errors.extend(_validate_evidence_refs(item.get("evidence_refs") or [], index, finding_ids))
        for ref in item.get("supporting_context_refs") or []:
            ref_id = str(ref.get("id") or ref) if isinstance(ref, Mapping) else str(ref)
            if ref_id in index["authority_observation"] and ref_id not in index["supporting_material"]:
                continue
            if ref_id and ref_id not in index["supporting_material"]:
                errors.append(f"supporting context ref is not in the case: {ref_id}")
    program_by_id = {str(item.get("finding_id") or ""): item for item in payload.get("program_findings") or []}
    authority_by_id = {
        str(item.get("finding_id") or ""): item for item in payload.get("authority_findings") or []
    }
    for item in payload.get("program_findings") or []:
        truth = str(item.get("truth_value") or "")
        basis = str(item.get("basis") or "")
        if truth not in TRUTH:
            errors.append(f"invalid program finding truth: {truth}")
        if basis not in BASIS:
            errors.append(f"invalid program finding basis: {basis}")
        if str(item.get("heuristic_dependence") or "") not in HEURISTIC_DEPENDENCE:
            errors.append(f"invalid heuristic_dependence: {item.get('heuristic_dependence')}")
        context = str(item.get("finding_context") or "")
        if context not in FINDING_CONTEXT:
            errors.append(f"invalid finding_context: {context}")
        if context == "INSUFFICIENT":
            insufficient_items = True
        refs = item.get("evidence_refs") or []
        if truth in {"TRUE", "FALSE"} and not refs:
            errors.append(f"{item.get('finding_id')} TRUE/FALSE finding has no evidence")
        errors.extend(_validate_evidence_refs(refs, index, finding_ids))
        kinds = {str(ref.get("kind") or "") for ref in refs}
        if basis == "MECHANICAL" and refs and not (kinds & MECHANICAL_EVIDENCE_KINDS):
            errors.append(f"{item.get('finding_id')} MECHANICAL finding is based only on interpretive program source")
        if basis == "MECHANICAL" and kinds <= {PROGRAM_SOURCE_KIND} and refs:
            errors.append(f"{item.get('finding_id')} MECHANICAL finding is based only on interpretive program source")
        if str(item.get("heuristic_dependence") or "") == "MATERIAL" and truth in {"TRUE", "FALSE"}:
            errors.append(f"{item.get('finding_id')} MATERIAL heuristic dependence cannot settle TRUE/FALSE")
    for item in payload.get("conformance_findings") or []:
        result = str(item.get("result") or "")
        if result not in CONFORMANCE:
            errors.append(f"invalid conformance: {result}")
        prior = item.get("prior_state")
        if prior not in {None, ""} and prior not in {"CONFORMS", "CONFLICTS", "UNKNOWN"}:
            errors.append(f"invalid prior_state: {prior}")
        auth_refs = [str(obs) for obs in item.get("authority_finding_refs") or []]
        prog_refs = [str(obs) for obs in item.get("program_finding_refs") or []]
        for ref in auth_refs:
            if ref not in authority_by_id:
                errors.append(f"conformance cites unknown authority finding {ref}")
        for ref in prog_refs:
            if ref not in program_by_id:
                errors.append(f"conformance cites unknown program finding {ref}")
        required_unknown = False
        for ref in auth_refs:
            auth = authority_by_id.get(ref) or {}
            if auth.get("applicability") == "UNKNOWN":
                required_unknown = True
            if auth.get("applicability") == "DOES_NOT_APPLY" and result not in {"NOT_APPLICABLE"}:
                errors.append(f"{item.get('finding_id')} DOES_NOT_APPLY cannot CONFORM or CONFLICT")
        for ref in prog_refs:
            prog = program_by_id.get(ref) or {}
            if prog.get("truth_value") == "UNKNOWN":
                required_unknown = True
        if result in {"CONFORMS", "CONFLICTS"} and required_unknown:
            errors.append(f"{item.get('finding_id')} CONFORMS/CONFLICTS depends on UNKNOWN required findings")
    for item in payload.get("authority_conflicts") or []:
        refs = [str(obs) for obs in item.get("authority_finding_refs") or []]
        if len(refs) < 2:
            errors.append(f"{item.get('conflict_id')} authority conflict needs at least two authority items")
        for ref in refs:
            if ref not in authority_by_id:
                errors.append(f"authority conflict cites unknown finding {ref}")
        if item.get("precedence") not in {"UNESTABLISHED", "EXPLICIT_IN_CASE"}:
            errors.append(f"invalid authority-conflict precedence: {item.get('precedence')}")
    right = payload.get("decision_right") or {}
    outcome = str(right.get("outcome") or "")
    if outcome not in DECISION_RIGHT:
        errors.append(f"invalid decision_right outcome: {outcome}")
    if not right.get("subject"):
        errors.append("decision_right subject is missing")
    basis_refs = [str(obs) for obs in right.get("authority_basis_refs") or []]
    if outcome not in {"NOT_ESTABLISHED"} and not basis_refs and not str(right.get("rationale") or "").strip():
        errors.append("decision-right outcome has no basis except legitimate NOT_ESTABLISHED cases")
    for ref in basis_refs:
        if ref not in authority_by_id and ref not in finding_ids:
            errors.append(f"decision-right basis is not in the adjudication: {ref}")
    if outcome == "DELEGATED" and not applies:
        errors.append("DELEGATED cannot be derived from empty or non-applicable authority")
    if outcome == "DELEGATED" and payload.get("authority_conflicts"):
        errors.append("DELEGATED cannot hide an unresolved authority conflict")
    if outcome == "NOT_ESTABLISHED" and applies:
        errors.append("NOT_ESTABLISHED requires no APPLIES authority items for the subject")
    for item in payload.get("context_requests") or []:
        for requested in item.get("source_evidence_requested") or []:
            if not isinstance(requested, Mapping):
                continue
            kind = str(requested.get("kind") or "")
            if kind and kind not in SOURCE_KINDS:
                errors.append(f"unsupported ContextRequest source kind: {kind}")
        if item.get("query") or item.get("cypher") or item.get("search"):
            errors.append("ContextRequest must not be a search/query language")
    for item in payload.get("rationale") or []:
        if not str(item.get("statement") or "").strip():
            continue
        if not item.get("evidence_refs"):
            errors.append("rationale statement is missing evidence references")
        errors.extend(_validate_evidence_refs(item.get("evidence_refs") or [], index, finding_ids))
    expected_state = rollup_adjudication_state(
        context_sufficiency=sufficiency,
        authority_findings=payload.get("authority_findings") or [],
        program_findings=payload.get("program_findings") or [],
        conformance_findings=payload.get("conformance_findings") or [],
        authority_conflicts=payload.get("authority_conflicts") or [],
        context_requests=payload.get("context_requests") or [],
    )
    actual_state = str(payload.get("adjudication_state") or "")
    if payload.get("authority_conflicts") and actual_state == "RESOLVED":
        errors.append("unresolved authority conflict hidden under RESOLVED")
    if insufficient_items and actual_state == "RESOLVED":
        errors.append("insufficient finding context hidden under RESOLVED")
    if insufficient_items and actual_state not in {"INSUFFICIENT_CONTEXT"}:
        errors.append("required context is insufficient but top-level state is not INSUFFICIENT_CONTEXT")
    if (
        sufficiency.get("status") == "INSUFFICIENT" or insufficient_items
    ) and not payload.get("context_requests"):
        errors.append("INSUFFICIENT context is missing a ContextRequest")
    if actual_state == "AUTHORITY_CONFLICT" and not payload.get("authority_conflicts"):
        errors.append("AUTHORITY_CONFLICT state has empty authority_conflicts")
    if actual_state == "INSUFFICIENT_CONTEXT" and expected_state not in {
        "INSUFFICIENT_CONTEXT",
        "AUTHORITY_CONFLICT",
        "UNRESOLVED",
    }:
        if not (insufficient_items or sufficiency.get("status") == "INSUFFICIENT"):
            errors.append("INSUFFICIENT_CONTEXT state has no insufficient finding")
    return sorted(set(errors))


def _validate_evidence_refs(
    refs: Sequence[Mapping[str, Any]],
    index: Mapping[str, set[str]],
    finding_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    for ref in refs:
        kind = str(ref.get("kind") or "")
        ref_id = str(ref.get("id") or "")
        if not ref_id:
            continue
        if kind == AUTHORITY_OBS_KIND and ref_id not in index["authority_observation"]:
            errors.append(f"authority observation is not in the case: {ref_id}")
        elif kind == PROGRAM_SOURCE_KIND and ref_id not in index["program_source"]:
            errors.append(f"program evidence ref is not in the case: {ref_id}")
        elif kind == SUPPORTING_KIND and ref_id not in index["supporting_material"]:
            errors.append(f"supporting material ref is not in the case: {ref_id}")
        elif kind == CLAIM_KIND and ref_id not in index["claim"]:
            errors.append(f"claim ref is not in the case: {ref_id}")
        elif kind == "program_referent" and ref_id not in index["program_referent"]:
            errors.append(f"program referent is not in the case: {ref_id}")
        elif kind == "finding" and ref_id not in finding_ids:
            errors.append(f"finding ref is not in the adjudication: {ref_id}")
        elif kind == AUTHORITY_OBS_KIND and ref_id in index["supporting_material"]:
            errors.append("supporting material cannot govern")
    return errors


def write_governance_adjudication(payload: Mapping[str, Any], output_dir: Path | str) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "governance.adjudication.json"
    path.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_governance_adjudication(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise AdjudicationError("governance.adjudication.json must be an object")
    return json.loads(_canonical_json(payload))
