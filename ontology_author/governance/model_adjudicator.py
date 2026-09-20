"""Evidence-bounded model adjudication for GovernanceCase sidecars.

This module is deliberately an adapter, not an execution gate.  The model is
given one serialized GovernanceCase, a compact adjudication contract, and the
GovernanceAdjudication output schema.  It has no repository or World access.

Provider mechanics live behind :class:`AdjudicatorTransport`; the resulting
artifact is still assembled by ``create_governance_adjudication`` and checked
by ``validate_governance_adjudication``.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, TypeAlias
from urllib.parse import urlsplit, urlunsplit

import requests

from .adjudication import (
    ADJUDICATION_SCHEMA,
    ADJUDICATION_STATES,
    ADJUDICATION_VERSION,
    ADJUDICATOR_KINDS,
    APPLICABILITY,
    BASIS,
    CONFORMANCE,
    DECISION_RIGHT,
    FINDING_CONTEXT,
    HEURISTIC_DEPENDENCE,
    SOURCE_KINDS,
    TRUTH,
    AdjudicationError,
    create_governance_adjudication,
    validate_governance_adjudication,
    write_governance_adjudication,
)

MODEL_INSTRUCTION_VERSION = "governance-model-adjudicator/v1"
INVOCATION_SCHEMA = "governance_adjudication_invocation/v0"
INVOCATION_VERSION = 0
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-5-mini"
MAX_ATTEMPTS = 2

GovernanceCase: TypeAlias = Mapping[str, Any]
GovernanceAdjudication: TypeAlias = dict[str, Any]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)


def _copy(value: Any) -> Any:
    return json.loads(_canonical_json(value))


def _inspectable_base_url(value: str) -> str:
    """Remove URL credentials/query material before putting an endpoint in a receipt."""

    raw = str(value).strip().rstrip("/")
    try:
        parsed = urlsplit(raw)
        if not parsed.scheme or not parsed.hostname:
            return raw.split("?", 1)[0].split("#", 1)[0].rstrip("/")
        hostname = parsed.hostname
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = hostname
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path.rstrip("/"), "", ""))
    except ValueError:
        return "[invalid-endpoint]"


def _schema_object(
    properties: Mapping[str, Any], required: Sequence[str] | None = None
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(required if required is not None else properties),
        "additionalProperties": False,
    }


def _array(items: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"type": "array", "items": dict(items or {})}


def _string_array() -> dict[str, Any]:
    return _array({"type": "string"})


def _evidence_ref_schema() -> dict[str, Any]:
    return _schema_object(
        {
            "kind": {"type": "string"},
            "id": {"type": "string"},
        },
        ("kind", "id"),
    )


def governance_adjudication_schema() -> dict[str, Any]:
    """Return the strict provider-facing JSON Schema for v0 artifacts.

    The repository's application validator remains authoritative.  This
    schema only gives providers a structural target; it cannot enforce case
    membership of evidence IDs or semantic UNKNOWN propagation.
    """

    authority_finding = _schema_object(
        {
            "finding_id": {"type": "string"},
            "observation_ids": _string_array(),
            "attachment_refs": _string_array(),
            "applicability": {"enum": ["APPLIES", "DOES_NOT_APPLY", "UNKNOWN"]},
            "interpretation_summary": {"type": "string"},
            "relevant_qualifiers": _array(),
            "supporting_case_facts": _array(),
            "supporting_context_refs": _array(),
            "selected_because_ignored": {"type": "boolean"},
            "finding_context": {"enum": ["SUFFICIENT", "INSUFFICIENT", "UNKNOWN"]},
            "context_reasons": _string_array(),
            "evidence_refs": _array(_evidence_ref_schema()),
            "applicability_basis": {"type": "string"},
        }
    )
    program_finding = _schema_object(
        {
            "finding_id": {"type": "string"},
            "proposition": {"type": "string"},
            "truth_value": {"enum": ["TRUE", "FALSE", "UNKNOWN"]},
            "side": {"enum": ["NEW", "OLD", "COMPARISON"]},
            "basis": {"enum": ["MECHANICAL", "INTERPRETIVE"]},
            "heuristic_dependence": {"enum": ["MATERIAL", "NOT_MATERIAL", "UNKNOWN"]},
            "evidence_refs": _array(_evidence_ref_schema()),
            "finding_context": {"enum": ["SUFFICIENT", "INSUFFICIENT", "UNKNOWN"]},
            "context_reasons": _string_array(),
            "limitations": _string_array(),
        }
    )
    conformance_finding = _schema_object(
        {
            "finding_id": {"type": "string"},
            "authority_finding_refs": _string_array(),
            "program_finding_refs": _string_array(),
            "result": {"enum": ["CONFORMS", "CONFLICTS", "UNKNOWN", "NOT_APPLICABLE"]},
            "prior_state": {
                "type": ["string", "null"],
                "enum": ["CONFORMS", "CONFLICTS", "UNKNOWN", None],
            },
        }
    )
    authority_conflict = _schema_object(
        {
            "conflict_id": {"type": "string"},
            "authority_finding_refs": _string_array(),
            "issue": {"type": "string"},
            "precedence": {"enum": ["UNESTABLISHED", "EXPLICIT_IN_CASE"]},
            "resolution": {"type": "string"},
        }
    )
    decision_right = _schema_object(
        {
            "subject": {"type": "string"},
            "outcome": {
                "enum": [
                    "DELEGATED",
                    "CONSTRAINED",
                    "PROHIBITED",
                    "APPROVAL_REQUIRED",
                    "UNKNOWN",
                    "NOT_ESTABLISHED",
                ]
            },
            "authority_basis_refs": _string_array(),
            "rationale": {"type": "string"},
            "related_rights": _array(
                _schema_object(
                    {
                        "subject": {"type": "string"},
                        "outcome": {
                            "enum": [
                                "DELEGATED",
                                "CONSTRAINED",
                                "PROHIBITED",
                                "APPROVAL_REQUIRED",
                                "UNKNOWN",
                                "NOT_ESTABLISHED",
                            ]
                        },
                        "authority_basis_refs": _string_array(),
                    }
                )
            ),
        }
    )
    context_request = _schema_object(
        {
            "request_id": {"type": "string"},
            "reason": {"type": "string"},
            "program_identities": _string_array(),
            "relation_or_context_needed": _array(),
            "source_evidence_requested": _array(
                _schema_object(
                    {
                        "side": {"enum": ["OLD", "NEW", "CANDIDATE"]},
                        "program_entity": {"type": "string"},
                        "kind": {
                            "enum": [
                                "IMPLEMENTATION",
                                "SIGNATURE",
                                "CALLERS_IN_DECLARED_SCOPE",
                                "CALLEES",
                                "NAMED_RELATION",
                                "CANDIDATE_IMPLEMENTATIONS",
                            ]
                        },
                        "note": {"type": "string"},
                    }
                )
            ),
            "would_enable": {"type": "string"},
        }
    )
    rationale = _schema_object(
        {
            "statement": {"type": "string"},
            "evidence_refs": _array(_evidence_ref_schema()),
            "supports": _array(),
        }
    )
    return _schema_object(
        {
            "adjudication_id": {"type": "string"},
            "contract": {"enum": [ADJUDICATION_SCHEMA]},
            "adjudication_version": {"enum": [ADJUDICATION_VERSION]},
            "case_id": {"type": "string"},
            "adjudicator": _schema_object(
                {
                    "kind": {"enum": sorted(ADJUDICATOR_KINDS)},
                    "identity": {"type": "string"},
                    "version": {"type": "string"},
                    "configuration": {"type": "object", "additionalProperties": True},
                }
            ),
            "context_sufficiency": _schema_object(
                {
                    "status": {"enum": ["SUFFICIENT", "INSUFFICIENT", "UNKNOWN"]},
                    "reasons": _string_array(),
                }
            ),
            "authority_findings": _array(authority_finding),
            "program_findings": _array(program_finding),
            "conformance_findings": _array(conformance_finding),
            "authority_conflicts": _array(authority_conflict),
            "decision_right": decision_right,
            "unresolved_questions": _array(),
            "context_requests": _array(context_request),
            "rationale": _array(rationale),
            "case_summary": {"type": "string"},
            "adjudication_state": {
                "enum": [
                    "RESOLVED",
                    "UNRESOLVED",
                    "AUTHORITY_CONFLICT",
                    "INSUFFICIENT_CONTEXT",
                ]
            },
            "known_limitations": _array(),
            "empty_case_note": {"type": "string"},
        }
    )


MODEL_DRAFT_SCHEMA = "model_adjudication_draft/v0"
MODEL_DRAFT_VERSION = 0
_CATALOG_PREFIXES = {
    "AUTHORITATIVE_OBSERVATION": "A",
    "MECHANICAL_PROGRAM_FACT": "M",
    "PROGRAM_SOURCE": "S",
    "SUPPORTING_MATERIAL": "U",
    "PROGRAM_IDENTITY": "P",
    "AUTHORITY_CLAIM": "C",
    "SEMANTIC_CONTEXT": "E",
}


@dataclass(frozen=True)
class ModelAdjudicationDraft:
    """Runtime-only semantic output before canonical artifact compilation."""

    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return _copy(self.payload)


def _catalog_add(
    entries: dict[tuple[str, str, str], dict[str, str]],
    *,
    category: str,
    kind: str,
    identifier: Any,
) -> None:
    value = str(identifier or "").strip()
    if value:
        entries.setdefault(
            (category, kind, value),
            {"category": category, "kind": kind, "id": value},
        )


def build_case_evidence_catalog(case: GovernanceCase) -> dict[str, Any]:
    """Build the deterministic, case-scoped alias catalog for model input."""

    entries: dict[tuple[str, str, str], dict[str, str]] = {}
    authority = case.get("authority") or {}
    for item in authority.get("observations") or []:
        if (
            isinstance(item, Mapping)
            and str(item.get("standing") or "") == "AUTHORITATIVE"
        ):
            _catalog_add(
                entries,
                category="AUTHORITATIVE_OBSERVATION",
                kind="authority_observation",
                identifier=item.get("observation_id"),
            )
    for item in authority.get("claims") or []:
        if isinstance(item, Mapping):
            _catalog_add(
                entries,
                category="AUTHORITY_CLAIM",
                kind="claim",
                identifier=item.get("assertion_id"),
            )
    semantic_context = case.get("semantic_context") or {}
    for item in semantic_context.get("claims") or []:
        if isinstance(item, Mapping):
            # The claim identity is already canonical evidence.  The
            # additional category records why this persisted claim was
            # selected without introducing a new durable evidence kind.
            _catalog_add(
                entries,
                category="SEMANTIC_CONTEXT",
                kind="claim",
                identifier=item.get("assertion_id"),
            )
    for item in semantic_context.get("program_links") or []:
        if isinstance(item, Mapping) and item.get("assertion_id"):
            _catalog_add(
                entries,
                category="SEMANTIC_CONTEXT",
                kind="claim",
                identifier=item.get("assertion_id"),
            )
    for item in case.get("supporting_material") or []:
        if isinstance(item, Mapping):
            _catalog_add(
                entries,
                category="SUPPORTING_MATERIAL",
                kind="supporting_material",
                identifier=item.get("observation_id"),
            )

    program = case.get("program_context") or {}
    for item in program.get("source_evidence") or []:
        if isinstance(item, Mapping):
            _catalog_add(
                entries,
                category="PROGRAM_SOURCE",
                kind="program_source",
                identifier=item.get("evidence_id"),
            )
    for item in program.get("referents") or []:
        if isinstance(item, Mapping):
            _catalog_add(
                entries,
                category="PROGRAM_IDENTITY",
                kind="program_referent",
                identifier=item.get("id"),
            )
    for item in (case.get("change") or {}).get("triggering_deltas") or []:
        if isinstance(item, Mapping):
            _catalog_add(
                entries,
                category="MECHANICAL_PROGRAM_FACT",
                kind="delta",
                identifier=item.get("evidence_id")
                or item.get("delta_id")
                or item.get("id"),
            )
    for item in program.get("relation_tuples") or []:
        if not isinstance(item, Mapping):
            continue
        _catalog_add(
            entries,
            category="MECHANICAL_PROGRAM_FACT",
            kind="relation_tuple",
            identifier=item.get("evidence_id")
            or item.get("tuple_id")
            or item.get("id"),
        )
        for nested in item.get("delta_evidence") or []:
            if isinstance(nested, Mapping):
                _catalog_add(
                    entries,
                    category="MECHANICAL_PROGRAM_FACT",
                    kind="delta",
                    identifier=nested.get("evidence_id")
                    or nested.get("delta_id")
                    or nested.get("id"),
                )
    for item in program.get("resolution_outcomes") or []:
        if isinstance(item, Mapping):
            _catalog_add(
                entries,
                category="MECHANICAL_PROGRAM_FACT",
                kind="resolution_outcome",
                identifier=item.get("evidence_id")
                or item.get("resolution_id")
                or item.get("id"),
            )

    by_category: dict[str, list[dict[str, str]]] = {
        category: [] for category in _CATALOG_PREFIXES
    }
    for entry in sorted(
        entries.values(), key=lambda row: (row["category"], row["kind"], row["id"])
    ):
        by_category[entry["category"]].append(entry)
    catalog_entries: list[dict[str, str]] = []
    allowed: dict[str, list[str]] = {}
    for category, prefix in _CATALOG_PREFIXES.items():
        category_entries = by_category[category]
        aliases: list[str] = []
        for index, entry in enumerate(category_entries, start=1):
            alias = f"{prefix}{index}"
            row = {**entry, "alias": alias}
            catalog_entries.append(row)
            aliases.append(alias)
        allowed[category] = aliases
    return {
        "contract": "governance_case_evidence_catalog/v0",
        "version": 0,
        "case_id": str(case.get("case_id") or ""),
        "entries": catalog_entries,
        "allowed_aliases": allowed,
    }


def _catalog_index(catalog: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for item in catalog.get("entries") or []:
        if not isinstance(item, Mapping):
            raise AdjudicationError("evidence catalog contains a non-object entry")
        alias = str(item.get("alias") or "")
        if not alias or alias in index:
            raise AdjudicationError(
                f"evidence catalog has duplicate or empty alias: {alias!r}"
            )
        index[alias] = {
            "alias": alias,
            "category": str(item.get("category") or ""),
            "kind": str(item.get("kind") or ""),
            "id": str(item.get("id") or ""),
        }
    return index


def _alias_schema(aliases: Sequence[str]) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string", "enum": list(aliases)}
    return schema


def _alias_array_schema(aliases: Sequence[str]) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "array",
        "items": _alias_schema(aliases),
        "uniqueItems": True,
    }
    if not aliases:
        schema["maxItems"] = 0
    return schema


def model_adjudication_draft_schema(
    case: GovernanceCase,
    evidence_catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a case-restricted schema for the runtime-only model draft."""

    catalog = evidence_catalog or build_case_evidence_catalog(case)
    allowed = catalog.get("allowed_aliases") or {}
    authority = list(allowed.get("AUTHORITATIVE_OBSERVATION") or [])
    mechanical = list(allowed.get("MECHANICAL_PROGRAM_FACT") or [])
    source = list(allowed.get("PROGRAM_SOURCE") or [])
    support = list(allowed.get("SUPPORTING_MATERIAL") or [])
    identities = list(allowed.get("PROGRAM_IDENTITY") or [])
    rationale_aliases = [
        *authority,
        *mechanical,
        *source,
        *support,
        *identities,
        *list(allowed.get("AUTHORITY_CLAIM") or []),
        *list(allowed.get("SEMANTIC_CONTEXT") or []),
    ]
    program_evidence = [
        *mechanical,
        *source,
        *support,
        *identities,
        *list(allowed.get("SEMANTIC_CONTEXT") or []),
    ]
    related_right = _schema_object(
        {
            "subject": {"type": "string"},
            "outcome": {"enum": sorted(DECISION_RIGHT)},
            "authority_refs": _alias_array_schema(authority),
        }
    )
    source_request = _schema_object(
        {
            "side": {"enum": ["OLD", "NEW", "CANDIDATE"]},
            "program_alias": _alias_schema(identities),
            "kind": {"enum": sorted(SOURCE_KINDS)},
            "note": {"type": "string"},
        }
    )
    program_finding = _schema_object(
        {
            "proposition": {"type": "string"},
            "truth_value": {"enum": sorted(TRUTH)},
            "side": {"enum": ["NEW", "OLD", "COMPARISON"]},
            "basis": {"enum": sorted(BASIS)},
            "heuristic_dependence": {"enum": sorted(HEURISTIC_DEPENDENCE)},
            "evidence_refs": _alias_array_schema(program_evidence),
            "finding_context": {"enum": sorted(FINDING_CONTEXT)},
            "context_reasons": _string_array(),
            "limitations": _array(),
        }
    )
    authority_item = _schema_object(
        {
            "authority_ref": _alias_schema(authority),
            "applicability": {"enum": sorted(APPLICABILITY)},
            "interpretation_summary": {"type": "string"},
            "applicability_basis": {"type": "string"},
            "finding_context": {"enum": sorted(FINDING_CONTEXT)},
            "context_reasons": _string_array(),
            "program_findings": _array(program_finding),
            "conformance": _schema_object(
                {
                    "result": {"enum": sorted(CONFORMANCE)},
                    "finding_indexes": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "uniqueItems": True,
                    },
                    "prior_state": {
                        "type": ["string", "null"],
                        "enum": ["CONFORMS", "CONFLICTS", "UNKNOWN", None],
                    },
                }
            ),
        }
    )
    context_request = _schema_object(
        {
            "reason": {"type": "string"},
            "program_aliases": _alias_array_schema(identities),
            "relation_or_context_needed": _array(),
            "source_evidence_requested": _array(source_request),
            "would_enable": {"type": "string"},
        }
    )
    return _schema_object(
        {
            "case_id": {"const": str(case.get("case_id") or "")},
            "context_sufficiency": _schema_object(
                {
                    "status": {"enum": sorted(FINDING_CONTEXT)},
                    "reasons": _string_array(),
                }
            ),
            "authority_items": _array(authority_item),
            "authority_conflicts": _array(
                _schema_object(
                    {
                        "authority_refs": _alias_array_schema(authority),
                        "issue": {"type": "string"},
                        "precedence": {"enum": ["UNESTABLISHED", "EXPLICIT_IN_CASE"]},
                        "resolution": {"type": "string"},
                    }
                )
            ),
            "decision_right": _schema_object(
                {
                    "subject": {"type": "string"},
                    "outcome": {"enum": sorted(DECISION_RIGHT)},
                    "authority_refs": _alias_array_schema(authority),
                    "rationale": {"type": "string"},
                    "related_rights": _array(related_right),
                }
            ),
            "context_requests": _array(context_request),
            "rationale": _array(
                _schema_object(
                    {
                        "statement": {"type": "string"},
                        "evidence_refs": _alias_array_schema(rationale_aliases),
                    }
                )
            ),
            "unresolved_questions": _array(),
            "case_summary": {"type": "string"},
            "adjudication_state": {"enum": sorted(ADJUDICATION_STATES)},
            "known_limitations": _array(),
            "empty_case_note": {"type": "string"},
        }
    )


def _draft_unknown_keys(
    value: Mapping[str, Any], allowed: set[str], location: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise AdjudicationError(
            f"{location} contains unknown fields: {', '.join(unknown)}"
        )


def _draft_mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdjudicationError(f"{location} must be an object")
    return value


def _draft_list(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise AdjudicationError(f"{location} must be an array")
    return value


def _resolve_draft_alias(
    alias: Any,
    catalog_index: Mapping[str, Mapping[str, str]],
    categories: set[str],
    location: str,
) -> dict[str, str]:
    value = str(alias or "")
    entry = catalog_index.get(value)
    if entry is None:
        raise AdjudicationError(
            f"{location} uses an alias not present in the case catalog: {value}"
        )
    if entry["category"] not in categories:
        wanted = ", ".join(sorted(categories))
        raise AdjudicationError(
            f"{location} alias {value} has category {entry['category']}; expected {wanted}"
        )
    return dict(entry)


def _resolve_draft_aliases(
    aliases: Any,
    catalog_index: Mapping[str, Mapping[str, str]],
    categories: set[str],
    location: str,
) -> list[dict[str, str]]:
    values = _draft_list(aliases, location)
    resolved: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, alias in enumerate(values):
        entry = _resolve_draft_alias(
            alias, catalog_index, categories, f"{location}[{index}]"
        )
        if entry["alias"] in seen:
            raise AdjudicationError(
                f"{location} contains duplicate alias {entry['alias']}"
            )
        seen.add(entry["alias"])
        resolved.append(entry)
    return resolved


def _draft_content_id(prefix: str, value: Mapping[str, Any]) -> str:
    return f"{prefix}:{hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()[:32]}"


def compile_model_adjudication_draft(
    case: GovernanceCase,
    evidence_catalog: Mapping[str, Any],
    draft: ModelAdjudicationDraft | Mapping[str, Any],
    *,
    adjudicator: Mapping[str, Any] | None = None,
) -> GovernanceAdjudication:
    """Compile a case-bounded model draft into the canonical artifact."""

    catalog = _copy(evidence_catalog)
    if catalog != build_case_evidence_catalog(case):
        raise AdjudicationError(
            "evidence catalog does not exactly match the GovernanceCase"
        )
    catalog_index = _catalog_index(catalog)
    payload = (
        draft.to_dict() if isinstance(draft, ModelAdjudicationDraft) else _copy(draft)
    )
    payload = _draft_mapping(payload, "model adjudication draft")
    _draft_unknown_keys(
        payload,
        {
            "case_id",
            "context_sufficiency",
            "authority_items",
            "authority_conflicts",
            "decision_right",
            "context_requests",
            "rationale",
            "unresolved_questions",
            "case_summary",
            "adjudication_state",
            "known_limitations",
            "empty_case_note",
        },
        "model adjudication draft",
    )
    if payload.get("case_id") != case.get("case_id"):
        raise AdjudicationError("model draft case_id does not match the GovernanceCase")

    authority_rows: list[dict[str, Any]] = []
    program_rows: list[dict[str, Any]] = []
    conformance_rows: list[dict[str, Any]] = []
    authority_ids: dict[str, str] = {}
    authority_items = _draft_list(payload.get("authority_items"), "authority_items")
    for authority_index, raw_item in enumerate(authority_items):
        item = _draft_mapping(raw_item, f"authority_items[{authority_index}]")
        _draft_unknown_keys(
            item,
            {
                "authority_ref",
                "applicability",
                "interpretation_summary",
                "applicability_basis",
                "finding_context",
                "context_reasons",
                "program_findings",
                "conformance",
            },
            f"authority_items[{authority_index}]",
        )
        authority_entry = _resolve_draft_alias(
            item.get("authority_ref"),
            catalog_index,
            {"AUTHORITATIVE_OBSERVATION"},
            f"authority_items[{authority_index}].authority_ref",
        )
        authority_alias = authority_entry["alias"]
        if authority_alias in authority_ids:
            raise AdjudicationError(
                f"authority item repeats case authority alias {authority_alias}"
            )
        applicability = str(item.get("applicability") or "UNKNOWN").upper()
        finding_context = str(item.get("finding_context") or "UNKNOWN").upper()
        authority_row = {
            "observation_ids": [authority_entry["id"]],
            "attachment_refs": [],
            "applicability": applicability,
            "interpretation_summary": str(item.get("interpretation_summary") or ""),
            "relevant_qualifiers": [],
            "supporting_case_facts": [],
            "supporting_context_refs": [],
            "evidence_refs": [
                {"kind": authority_entry["kind"], "id": authority_entry["id"]}
            ],
            "applicability_basis": str(item.get("applicability_basis") or ""),
            "finding_context": finding_context,
            "context_reasons": list(item.get("context_reasons") or []),
        }
        authority_row["finding_id"] = _draft_content_id(
            "afinding",
            {"authority_ref": authority_alias, **authority_row},
        )
        authority_ids[authority_alias] = authority_row["finding_id"]
        authority_rows.append(authority_row)

        local_program_ids: list[str] = []
        raw_programs = _draft_list(
            item.get("program_findings"),
            f"authority_items[{authority_index}].program_findings",
        )
        for program_index, raw_program in enumerate(raw_programs):
            program = _draft_mapping(
                raw_program,
                f"authority_items[{authority_index}].program_findings[{program_index}]",
            )
            location = (
                f"authority_items[{authority_index}].program_findings[{program_index}]"
            )
            _draft_unknown_keys(
                program,
                {
                    "proposition",
                    "truth_value",
                    "side",
                    "basis",
                    "heuristic_dependence",
                    "evidence_refs",
                    "finding_context",
                    "context_reasons",
                    "limitations",
                },
                location,
            )
            evidence = _resolve_draft_aliases(
                program.get("evidence_refs"),
                catalog_index,
                {
                    "MECHANICAL_PROGRAM_FACT",
                    "PROGRAM_SOURCE",
                    "SUPPORTING_MATERIAL",
                    "PROGRAM_IDENTITY",
                    "SEMANTIC_CONTEXT",
                },
                f"{location}.evidence_refs",
            )
            program_row = {
                "proposition": str(program.get("proposition") or ""),
                "truth_value": str(program.get("truth_value") or "UNKNOWN").upper(),
                "side": str(program.get("side") or "NEW").upper(),
                "basis": str(program.get("basis") or "").upper(),
                "heuristic_dependence": str(
                    program.get("heuristic_dependence") or "UNKNOWN"
                ).upper(),
                "evidence_refs": [
                    {"kind": entry["kind"], "id": entry["id"]} for entry in evidence
                ],
                "finding_context": str(
                    program.get("finding_context") or "UNKNOWN"
                ).upper(),
                "context_reasons": list(program.get("context_reasons") or []),
                "limitations": list(program.get("limitations") or []),
            }
            program_row["finding_id"] = _draft_content_id(
                "pfinding",
                {
                    "authority_ref": authority_alias,
                    "index": program_index,
                    **program_row,
                },
            )
            local_program_ids.append(program_row["finding_id"])
            program_rows.append(program_row)

        conformance = _draft_mapping(
            item.get("conformance"),
            f"authority_items[{authority_index}].conformance",
        )
        _draft_unknown_keys(
            conformance,
            {"result", "finding_indexes", "prior_state"},
            f"authority_items[{authority_index}].conformance",
        )
        indexes = _draft_list(
            conformance.get("finding_indexes"),
            f"authority_items[{authority_index}].conformance.finding_indexes",
        )
        selected_program_ids: list[str] = []
        for finding_index, raw_index in enumerate(indexes):
            if isinstance(raw_index, bool) or not isinstance(raw_index, int):
                raise AdjudicationError(
                    f"authority_items[{authority_index}].conformance.finding_indexes[{finding_index}] must be an integer"
                )
            if raw_index < 0 or raw_index >= len(local_program_ids):
                raise AdjudicationError(
                    f"authority_items[{authority_index}].conformance finding index {raw_index} is out of range"
                )
            selected_program_ids.append(local_program_ids[raw_index])
        conformance_row = {
            "authority_finding_refs": [authority_row["finding_id"]],
            "program_finding_refs": selected_program_ids,
            "result": str(conformance.get("result") or "UNKNOWN").upper(),
            "prior_state": (
                None
                if conformance.get("prior_state") in {None, ""}
                else str(conformance.get("prior_state")).upper()
            ),
        }
        conformance_row["finding_id"] = _draft_content_id(
            "cfinding",
            {"authority_ref": authority_alias, **conformance_row},
        )
        conformance_rows.append(conformance_row)

    conflict_rows: list[dict[str, Any]] = []
    for conflict_index, raw_conflict in enumerate(
        _draft_list(payload.get("authority_conflicts"), "authority_conflicts")
    ):
        conflict = _draft_mapping(
            raw_conflict, f"authority_conflicts[{conflict_index}]"
        )
        location = f"authority_conflicts[{conflict_index}]"
        _draft_unknown_keys(
            conflict, {"authority_refs", "issue", "precedence", "resolution"}, location
        )
        refs = _resolve_draft_aliases(
            conflict.get("authority_refs"),
            catalog_index,
            {"AUTHORITATIVE_OBSERVATION"},
            f"{location}.authority_refs",
        )
        row = {
            "authority_finding_refs": [authority_ids[entry["alias"]] for entry in refs],
            "issue": str(conflict.get("issue") or ""),
            "precedence": str(conflict.get("precedence") or "UNESTABLISHED").upper(),
            "resolution": str(conflict.get("resolution") or "unresolved"),
        }
        row["conflict_id"] = _draft_content_id(
            "aconflict", {"index": conflict_index, **row}
        )
        conflict_rows.append(row)

    raw_right = _draft_mapping(payload.get("decision_right"), "decision_right")
    _draft_unknown_keys(
        raw_right,
        {"subject", "outcome", "authority_refs", "rationale", "related_rights"},
        "decision_right",
    )
    right_refs = _resolve_draft_aliases(
        raw_right.get("authority_refs"),
        catalog_index,
        {"AUTHORITATIVE_OBSERVATION"},
        "decision_right.authority_refs",
    )
    related_rights: list[dict[str, Any]] = []
    for related_index, raw_related in enumerate(
        _draft_list(raw_right.get("related_rights"), "decision_right.related_rights")
    ):
        related = _draft_mapping(
            raw_related, f"decision_right.related_rights[{related_index}]"
        )
        location = f"decision_right.related_rights[{related_index}]"
        _draft_unknown_keys(related, {"subject", "outcome", "authority_refs"}, location)
        related_refs = _resolve_draft_aliases(
            related.get("authority_refs"),
            catalog_index,
            {"AUTHORITATIVE_OBSERVATION"},
            f"{location}.authority_refs",
        )
        related_rights.append(
            {
                "subject": str(related.get("subject") or ""),
                "outcome": str(related.get("outcome") or "UNKNOWN").upper(),
                "authority_basis_refs": [
                    authority_ids[entry["alias"]] for entry in related_refs
                ],
            }
        )
    decision_right = {
        "subject": str(raw_right.get("subject") or ""),
        "outcome": str(raw_right.get("outcome") or "UNKNOWN").upper(),
        "authority_basis_refs": [authority_ids[entry["alias"]] for entry in right_refs],
        "rationale": str(raw_right.get("rationale") or ""),
        "related_rights": related_rights,
    }

    request_rows: list[dict[str, Any]] = []
    for request_index, raw_request in enumerate(
        _draft_list(payload.get("context_requests"), "context_requests")
    ):
        request = _draft_mapping(raw_request, f"context_requests[{request_index}]")
        location = f"context_requests[{request_index}]"
        _draft_unknown_keys(
            request,
            {
                "reason",
                "program_aliases",
                "relation_or_context_needed",
                "source_evidence_requested",
                "would_enable",
            },
            location,
        )
        identities = _resolve_draft_aliases(
            request.get("program_aliases"),
            catalog_index,
            {"PROGRAM_IDENTITY"},
            f"{location}.program_aliases",
        )
        requested_rows: list[dict[str, Any]] = []
        for source_index, raw_source in enumerate(
            _draft_list(
                request.get("source_evidence_requested"),
                f"{location}.source_evidence_requested",
            )
        ):
            source_request = _draft_mapping(
                raw_source, f"{location}.source_evidence_requested[{source_index}]"
            )
            source_location = f"{location}.source_evidence_requested[{source_index}]"
            _draft_unknown_keys(
                source_request,
                {"side", "program_alias", "kind", "note"},
                source_location,
            )
            identity = _resolve_draft_alias(
                source_request.get("program_alias"),
                catalog_index,
                {"PROGRAM_IDENTITY"},
                f"{source_location}.program_alias",
            )
            requested_rows.append(
                {
                    "side": str(source_request.get("side") or "CANDIDATE").upper(),
                    "program_entity": identity["id"],
                    "kind": str(source_request.get("kind") or "IMPLEMENTATION").upper(),
                    "note": str(source_request.get("note") or ""),
                }
            )
        row = {
            "reason": str(request.get("reason") or ""),
            "program_identities": [entry["id"] for entry in identities],
            "relation_or_context_needed": list(
                request.get("relation_or_context_needed") or []
            ),
            "source_evidence_requested": requested_rows,
            "would_enable": str(request.get("would_enable") or ""),
        }
        row["request_id"] = _draft_content_id("creq", {"index": request_index, **row})
        request_rows.append(row)

    rationale_rows: list[dict[str, Any]] = []
    for rationale_index, raw_rationale in enumerate(
        _draft_list(payload.get("rationale"), "rationale")
    ):
        rationale = _draft_mapping(raw_rationale, f"rationale[{rationale_index}]")
        location = f"rationale[{rationale_index}]"
        _draft_unknown_keys(rationale, {"statement", "evidence_refs"}, location)
        refs = _resolve_draft_aliases(
            rationale.get("evidence_refs"),
            catalog_index,
            {
                "AUTHORITATIVE_OBSERVATION",
                "MECHANICAL_PROGRAM_FACT",
                "PROGRAM_SOURCE",
                "SUPPORTING_MATERIAL",
                "PROGRAM_IDENTITY",
                "AUTHORITY_CLAIM",
                "SEMANTIC_CONTEXT",
            },
            f"{location}.evidence_refs",
        )
        rationale_rows.append(
            {
                "statement": str(rationale.get("statement") or ""),
                "evidence_refs": [
                    {"kind": entry["kind"], "id": entry["id"]} for entry in refs
                ],
                "supports": [],
            }
        )

    context_sufficiency = _draft_mapping(
        payload.get("context_sufficiency"), "context_sufficiency"
    )
    _draft_unknown_keys(
        context_sufficiency, {"status", "reasons"}, "context_sufficiency"
    )
    compiler_adjudicator = adjudicator or {
        "kind": "MODEL",
        "identity": "model-adjudicator",
        "version": MODEL_INSTRUCTION_VERSION,
        "configuration": {},
    }
    return create_governance_adjudication(
        case,
        adjudicator=compiler_adjudicator,
        authority_findings=authority_rows,
        program_findings=program_rows,
        conformance_findings=conformance_rows,
        authority_conflicts=conflict_rows,
        decision_right=decision_right,
        context_requests=request_rows,
        rationale=rationale_rows,
        unresolved_questions=_draft_list(
            payload.get("unresolved_questions"), "unresolved_questions"
        ),
        case_summary=str(payload.get("case_summary") or ""),
        known_limitations=_draft_list(
            payload.get("known_limitations"), "known_limitations"
        ),
        empty_case_note=str(payload.get("empty_case_note") or ""),
        context_sufficiency=context_sufficiency,
        adjudication_state=str(payload.get("adjudication_state") or "").upper(),
    )


OUTPUT_FIELDS = frozenset(governance_adjudication_schema()["properties"])
KNOWN_EVIDENCE_KINDS = frozenset(
    {
        "authority_observation",
        "supporting_material",
        "claim",
        "program_source",
        "program_referent",
        "relation_tuple",
        "program_relation",
        "delta",
        "triggering_delta",
        "resolution_outcome",
        "finding",
    }
)


ADJUDICATION_INSTRUCTION = f"""You are a bounded governance adjudicator ({MODEL_INSTRUCTION_VERSION}).

The user case below is the complete evidence boundary. Use only the supplied
GovernanceCase. You have no repository, filesystem, search, web, or other
context. Never invent an evidence reference, authority item, source fact, or
program fact. If evidence needed for a conclusion is absent, use UNKNOWN and
emit a bounded ContextRequest instead of searching. If required program
evidence is absent, the program finding remains UNKNOWN, context sufficiency is
INSUFFICIENT, and the request names the bounded evidence needed.

Original reconstructed AUTHORITATIVE text controls interpretation. Normalized
claims are indexes/aids; supporting material is not authority; selected_because
is selection provenance, not normative evidence; old code is evidence, not
authority. Preserve uncertainty, HEURISTIC correspondence, and completeness
limitations. UNKNOWN is not FALSE.

The model-facing schema describes a runtime-only ModelAdjudicationDraft. Produce
exactly one JSON object matching that schema. Select evidence only by the
case-scoped aliases in the evidence catalog. Do not output canonical evidence
IDs, evidence kinds, finding IDs, conflict IDs, request IDs, or generated
cross-references; deterministic runtime code assigns those. Do not include
prose outside JSON, hidden reasoning, chain-of-thought, confidence, scores,
verdict fields, or provider/runtime details.

RULE 1 — SOURCE INTERPRETATION: If a program finding requires interpreting
supplied program source code, its basis is INTERPRETIVE. Supplied source text
never makes a finding MECHANICAL by itself.

RULE 2 — HEURISTIC CORRESPONDENCE: HEURISTIC dependence is MATERIAL only when
the finding's truth depends on assuming the old and new manifestations are the
same program thing. If a new-side mechanical fact independently establishes the
finding, use NOT_MATERIAL.

RULE 3 — DECISION RIGHT: NOT_ESTABLISHED is appropriate only when no applicable
authority establishes a decision right for the subject. If authority APPLIES
but uncertainty, missing context, or conflict prevents resolving that right,
use UNKNOWN. NOT_ESTABLISHED never means DELEGATED.

RULE 4 — MISSING EVIDENCE: Never invent evidence, program identities, or
authority. If the case lacks evidence required for a conclusion, use UNKNOWN
and emit a ContextRequest only for bounded identities/context permitted by the
supplied case schema.

Keep decision_right separate from conformance: CONFORMS does not imply
DELEGATED and CONFLICTS does not imply PROHIBITED. Preserve the vocabulary
DELEGATED, CONSTRAINED, PROHIBITED, APPROVAL_REQUIRED, UNKNOWN, and
NOT_ESTABLISHED.

Populate the draft in this order: assess context sufficiency; assess
applicability for each authority item; establish explicit program findings;
determine conformance for each applicable item; identify authority conflicts;
determine the case-local decision right only where established; emit bounded
ContextRequests for missing evidence; and provide short evidence-linked
rationale. Only the structured artifact and concise rationale are requested.

GovernanceCase JSON follows:
"""


@dataclass(frozen=True)
class ModelAdjudicatorConfig:
    """Provider-neutral model settings plus OpenRouter connection settings."""

    provider: str = "openrouter"
    model: str = DEFAULT_MODEL
    model_version: str = ""
    base_url: str = DEFAULT_OPENROUTER_BASE_URL
    api_key: str | None = None
    timeout_seconds: float = 120.0
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    max_attempts: int = MAX_ATTEMPTS
    identity: str = ""

    def __post_init__(self) -> None:
        if not str(self.provider).strip():
            raise ValueError("adjudicator provider must be non-empty")
        if not str(self.model).strip():
            raise ValueError("adjudicator model must be non-empty")
        if float(self.timeout_seconds) <= 0:
            raise ValueError("adjudicator timeout_seconds must be positive")
        if int(self.max_attempts) < 1:
            raise ValueError("adjudicator max_attempts must be at least one")

    @classmethod
    def from_value(
        cls, value: ModelAdjudicatorConfig | Mapping[str, Any]
    ) -> ModelAdjudicatorConfig:
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            raise TypeError(
                "adjudicator_config must be ModelAdjudicatorConfig or a mapping"
            )
        aliases = {
            "timeout": "timeout_seconds",
            "timeout_sec": "timeout_seconds",
            "max_retries": "max_attempts",
        }
        values: dict[str, Any] = {}
        for key, item in value.items():
            name = aliases.get(str(key), str(key))
            if name in cls.__dataclass_fields__:
                values[name] = item
        return cls(**values)

    @property
    def attempts(self) -> int:
        return min(MAX_ATTEMPTS, max(1, int(self.max_attempts)))

    @property
    def model_identity(self) -> str:
        return self.identity.strip() or f"{self.provider}:{self.model}"

    def inspectable_configuration(self) -> dict[str, Any]:
        """Return provenance settings with secrets and transport internals removed."""

        output: dict[str, Any] = {
            "provider": str(self.provider),
            "model": str(self.model),
            "base_url": _inspectable_base_url(self.base_url),
            "timeout_seconds": float(self.timeout_seconds),
            "max_attempts": self.attempts,
        }
        if self.model_version:
            output["model_version"] = str(self.model_version)
        if self.temperature is not None:
            output["temperature"] = float(self.temperature)
        if self.top_p is not None:
            output["top_p"] = float(self.top_p)
        if self.max_tokens is not None:
            output["max_tokens"] = int(self.max_tokens)
        return output


@dataclass(frozen=True)
class AdjudicatorRequest:
    """Provider-neutral request; ``case_json`` is the complete case boundary."""

    case_json: str
    instruction: str
    output_schema: Mapping[str, Any]
    evidence_catalog_json: str = ""
    previous_output_json: str | None = None
    validation_errors: tuple[str, ...] = ()

    def input_text(self) -> str:
        """Return the complete bounded model input without runtime internals."""

        if not self.evidence_catalog_json:
            return self.case_json
        return (
            self.case_json
            + "\nEvidence catalog JSON follows:\n"
            + self.evidence_catalog_json
        )

    def repair_text(self) -> str:
        if self.previous_output_json is None:
            return ""
        errors = "\n".join(f"- {error}" for error in self.validation_errors)
        return (
            "\n\nRepair the same artifact. The previous structured output and exact "
            "local validation errors are below. Correct only the artifact; use "
            "the same GovernanceCase and do not add context.\n"
            f"Validation errors:\n{errors}\n"
            f"Previous structured output:\n{self.previous_output_json}\n"
        )


@dataclass(frozen=True)
class AdjudicatorTransportResponse:
    payload: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)


class AdjudicatorTransport(Protocol):
    """Small provider boundary used by the model adapter and fake transports."""

    def generate(
        self, request: AdjudicatorRequest
    ) -> AdjudicatorTransportResponse | Any:
        """Return a structured candidate or raise for a provider/runtime error."""


class OpenRouterAdjudicatorTransport:
    """OpenRouter chat transport using provider-native JSON Schema output."""

    def __init__(self, config: ModelAdjudicatorConfig) -> None:
        self.config = config
        self.api_key = config.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY must be set for model adjudication")

    def generate(self, request: AdjudicatorRequest) -> AdjudicatorTransportResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": request.instruction},
                {
                    "role": "user",
                    "content": request.input_text() + request.repair_text(),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "governance_adjudication",
                    "strict": True,
                    "schema": request.output_schema,
                },
            },
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature
        if self.config.top_p is not None:
            payload["top_p"] = self.config.top_p
        if self.config.max_tokens is not None:
            payload["max_tokens"] = self.config.max_tokens
        response = requests.post(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=float(self.config.timeout_seconds),
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                f"model provider HTTP {response.status_code}: {response.text[:300]}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError("model provider returned non-JSON response") from exc
        if body.get("error"):
            raise RuntimeError(f"model provider error: {body['error']}")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("model provider returned no choices")
        message = choices[0].get("message") if isinstance(choices[0], Mapping) else None
        if not isinstance(message, Mapping):
            raise TypeError("model provider response has no message")
        candidate = message.get("parsed")
        if candidate is None:
            candidate = message.get("content")
        if candidate is None:
            raise RuntimeError("model provider response has no structured content")
        metadata = {
            key: body[key]
            for key in ("id", "model", "system_fingerprint")
            if isinstance(body.get(key), (str, int, float, bool))
        }
        return AdjudicatorTransportResponse(payload=candidate, metadata=metadata)


class ModelAdjudicationInvocationError(AdjudicationError):
    """A model invocation failed; this is not a GovernanceAdjudication state."""

    def __init__(self, message: str, receipt: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.receipt = _copy(receipt)


def _default_transport(config: ModelAdjudicatorConfig) -> AdjudicatorTransport:
    if config.provider.lower() == "openrouter":
        return OpenRouterAdjudicatorTransport(config)
    raise RuntimeError(f"unsupported adjudicator provider: {config.provider}")


def _instruction_hash() -> str:
    return hashlib.sha256(ADJUDICATION_INSTRUCTION.encode("utf-8")).hexdigest()[:32]


def _schema_hash(schema: Mapping[str, Any] | None = None) -> str:
    selected = schema if schema is not None else governance_adjudication_schema()
    return hashlib.sha256(_canonical_json(selected).encode("utf-8")).hexdigest()[:32]


def _base_receipt(
    case: GovernanceCase,
    config: ModelAdjudicatorConfig,
    schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "contract": INVOCATION_SCHEMA,
        "invocation_version": INVOCATION_VERSION,
        "case_id": str(case.get("case_id") or ""),
        "adjudicator_kind": "MODEL",
        "provider": str(config.provider),
        "model": str(config.model),
        "model_identity": config.model_identity,
        "model_version": str(config.model_version),
        "configuration": config.inspectable_configuration(),
        "instruction_template_version": MODEL_INSTRUCTION_VERSION,
        "instruction_template_hash": _instruction_hash(),
        "schema_contract": ADJUDICATION_SCHEMA,
        "schema_version": ADJUDICATION_VERSION,
        "schema_hash": _schema_hash(schema),
        "model_output_contract": MODEL_DRAFT_SCHEMA,
        "model_output_version": MODEL_DRAFT_VERSION,
        "attempt_count": 0,
        "attempts": [],
        "runtime_status": "FAILED_PROVIDER",
        "validation_result": "NOT_RUN",
        "validation_errors": [],
        "adjudication_id": None,
    }


def _redact_runtime_error(error: BaseException, config: ModelAdjudicatorConfig) -> str:
    message = str(error)
    secrets = {
        secret
        for secret in (config.api_key, os.environ.get("OPENROUTER_API_KEY"))
        if secret
    }
    for secret in secrets:
        message = message.replace(secret, "[REDACTED]")
    return message


def _response_value(
    response: AdjudicatorTransportResponse | Any,
) -> tuple[Any, Mapping[str, Any]]:
    if isinstance(response, AdjudicatorTransportResponse):
        return response.payload, response.metadata
    return response, {}


def _decode_candidate(
    candidate: Any,
) -> tuple[Mapping[str, Any] | None, str | None, str]:
    if isinstance(candidate, Mapping):
        return candidate, None, _canonical_json(candidate)
    if not isinstance(candidate, str):
        return None, "model response is not a JSON object", repr(candidate)
    raw = candidate.strip()
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        return None, f"model response is not valid JSON: {exc}", raw
    if not isinstance(parsed, Mapping):
        return None, "model response JSON must be an object", raw
    return parsed, None, _canonical_json(parsed)


def _model_shape_errors(
    candidate: Mapping[str, Any], case: GovernanceCase
) -> list[str]:
    # New model-facing output is a nested draft.  Its case-specific shape and
    # aliases are checked by the deterministic compiler below.  Keep accepting
    # the canonical shape here for compatibility with the existing transport
    # boundary and HUMAN/DETERMINISTIC fixture-style stubs.
    if "authority_items" in candidate:
        if candidate.get("case_id") != case.get("case_id"):
            return ["model draft case_id does not match the GovernanceCase"]
        return []
    errors: list[str] = []
    missing = sorted(OUTPUT_FIELDS - set(candidate))
    extra = sorted(set(candidate) - OUTPUT_FIELDS)
    if missing:
        errors.append("model output is missing fields: " + ", ".join(missing))
    if extra:
        errors.append("model output contains unknown fields: " + ", ".join(extra))
    if candidate.get("contract") != ADJUDICATION_SCHEMA:
        errors.append(f"model output contract is not {ADJUDICATION_SCHEMA}")
    if candidate.get("adjudication_version") != ADJUDICATION_VERSION:
        errors.append(
            f"model output adjudication_version is not {ADJUDICATION_VERSION}"
        )
    if candidate.get("case_id") != case.get("case_id"):
        errors.append("model output case_id does not match the GovernanceCase")
    adjudicator = candidate.get("adjudicator")
    if not isinstance(adjudicator, Mapping) or adjudicator.get("kind") != "MODEL":
        errors.append("model output adjudicator.kind must be MODEL")
    for item in candidate.get("authority_findings") or []:
        if (
            isinstance(item, Mapping)
            and item.get("selected_because_ignored") is not True
        ):
            errors.append("authority finding selected_because_ignored must be true")
    return errors


def _case_mechanical_evidence_ids(case: GovernanceCase) -> dict[str, set[str]]:
    """Index IDs materialized by case assembly for model-only integrity checks."""

    program = case.get("program_context") or {}
    relation_ids: set[str] = set()
    for item in program.get("relation_tuples") or []:
        if isinstance(item, Mapping):
            for key in ("evidence_id", "id", "tuple_id"):
                if item.get(key):
                    relation_ids.add(str(item[key]))
            for nested in item.get("delta_evidence") or []:
                if isinstance(nested, Mapping):
                    for key in ("evidence_id", "id", "delta_id"):
                        if nested.get(key):
                            relation_ids.add(str(nested[key]))
    resolution_ids = {
        str(item[key])
        for item in program.get("resolution_outcomes") or []
        if isinstance(item, Mapping)
        for key in ("evidence_id", "id", "resolution_id")
        if item.get(key)
    }
    delta_ids: set[str] = set()
    for item in (case.get("change") or {}).get("triggering_deltas") or []:
        if isinstance(item, Mapping):
            for key in ("evidence_id", "id", "delta_id"):
                if item.get(key):
                    delta_ids.add(str(item[key]))
    return {
        "relation_tuple": relation_ids,
        "program_relation": relation_ids,
        "delta": delta_ids,
        "triggering_delta": delta_ids,
        "resolution_outcome": resolution_ids,
    }


def _model_evidence_errors(
    artifact: Mapping[str, Any], case: GovernanceCase
) -> list[str]:
    """Reject evidence handles that the bounded case does not expose.

    The older artifact validator intentionally permits opaque mechanical
    handles for human-authored records. Model output is stricter: its only
    permitted mechanical handles are IDs materialized in the case.
    """

    mechanical_ids = _case_mechanical_evidence_ids(case)
    program_referents = {
        str(item.get("id") or "")
        for item in (case.get("program_context") or {}).get("referents") or []
        if isinstance(item, Mapping) and item.get("id")
    }
    refs: list[Mapping[str, Any]] = []
    for container in (
        *(artifact.get("authority_findings") or []),
        *(artifact.get("program_findings") or []),
        *(artifact.get("rationale") or []),
    ):
        refs.extend(
            item
            for item in container.get("evidence_refs") or []
            if isinstance(item, Mapping)
        )
    errors: list[str] = []
    for ref in refs:
        kind = str(ref.get("kind") or "")
        ref_id = str(ref.get("id") or "")
        if kind not in KNOWN_EVIDENCE_KINDS:
            errors.append(f"unsupported model evidence kind: {kind}")
        elif kind in mechanical_ids and ref_id not in mechanical_ids[kind]:
            errors.append(
                f"mechanical evidence ref is not in the case: {kind}:{ref_id}"
            )
    for request in artifact.get("context_requests") or []:
        if not isinstance(request, Mapping):
            continue
        for identity in request.get("program_identities") or []:
            if str(identity) not in program_referents:
                errors.append(
                    f"ContextRequest program identity is not in the case: {identity}"
                )
        for requested in request.get("source_evidence_requested") or []:
            if isinstance(requested, Mapping):
                entity = str(requested.get("program_entity") or "")
                if entity and entity not in program_referents:
                    errors.append(
                        f"ContextRequest program entity is not in the case: {entity}"
                    )
    return sorted(set(errors))


def _candidate_artifact(
    candidate: Mapping[str, Any],
    case: GovernanceCase,
    config: ModelAdjudicatorConfig,
) -> GovernanceAdjudication:
    """Decorate model semantic fields with runtime provenance, then validate."""

    shape_errors = _model_shape_errors(candidate, case)
    if shape_errors:
        raise AdjudicationError("; ".join(shape_errors))

    adjudicator = {
        "kind": "MODEL",
        "identity": config.model_identity,
        "version": config.model_version,
        "configuration": config.inspectable_configuration(),
    }
    if "authority_items" in candidate:
        # Model drafts contain only semantic choices and case-scoped aliases.
        # The compiler expands those aliases, assigns generated IDs, and then
        # invokes the unchanged canonical artifact validator.
        return compile_model_adjudication_draft(
            case,
            build_case_evidence_catalog(case),
            candidate,
            adjudicator=adjudicator,
        )

    # Compatibility path for an already canonical structured response.  The
    # durable validator still remains the final authority for this path.
    artifact = create_governance_adjudication(
        case,
        adjudicator=adjudicator,
        authority_findings=candidate.get("authority_findings") or [],
        program_findings=candidate.get("program_findings") or [],
        conformance_findings=candidate.get("conformance_findings") or [],
        authority_conflicts=candidate.get("authority_conflicts") or [],
        decision_right=candidate.get("decision_right") or {},
        context_requests=candidate.get("context_requests") or [],
        rationale=candidate.get("rationale") or [],
        unresolved_questions=candidate.get("unresolved_questions") or [],
        case_summary=str(candidate.get("case_summary") or ""),
        known_limitations=candidate.get("known_limitations") or [],
        empty_case_note=str(candidate.get("empty_case_note") or ""),
        context_sufficiency=candidate.get("context_sufficiency") or {},
        adjudication_state=str(candidate.get("adjudication_state") or ""),
        validate=False,
    )
    errors = validate_governance_adjudication(artifact, case)
    errors.extend(_model_evidence_errors(artifact, case))
    if errors:
        raise AdjudicationError("; ".join(errors))
    return artifact


def _write_invocation_receipt(
    receipt: Mapping[str, Any], output_dir: Path | str
) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "governance.adjudication.invocation.json"
    path.write_text(_pretty_json(receipt) + "\n", encoding="utf-8")
    return path


def write_governance_adjudication_invocation(
    receipt: Mapping[str, Any], output_dir: Path | str
) -> Path:
    """Write a runtime receipt without writing or mutating an adjudication."""

    return _write_invocation_receipt(receipt, output_dir)


class ModelAdjudicator:
    """Run a bounded model adjudication against one complete GovernanceCase."""

    def __init__(
        self,
        config: ModelAdjudicatorConfig | Mapping[str, Any],
        *,
        transport: AdjudicatorTransport | None = None,
    ) -> None:
        self.config = ModelAdjudicatorConfig.from_value(config)
        self.transport = transport

    def adjudicate(
        self,
        case: GovernanceCase,
        *,
        output_dir: Path | str | None = None,
    ) -> GovernanceAdjudication:
        if not isinstance(case, Mapping) or not str(case.get("case_id") or "").strip():
            raise ValueError("case must be a GovernanceCase mapping with case_id")
        if output_dir is not None:
            stale_artifact = Path(output_dir) / "governance.adjudication.json"
            if stale_artifact.is_file() or stale_artifact.is_symlink():
                stale_artifact.unlink()
        case_json = _canonical_json(case)
        evidence_catalog = build_case_evidence_catalog(case)
        evidence_catalog_json = _canonical_json(evidence_catalog)
        instruction = ADJUDICATION_INSTRUCTION
        output_schema = model_adjudication_draft_schema(case, evidence_catalog)
        transport = self.transport
        receipt = _base_receipt(case, self.config, output_schema)
        previous_json: str | None = None
        validation_errors: tuple[str, ...] = ()
        last_metadata: Mapping[str, Any] = {}

        for attempt in range(1, self.config.attempts + 1):
            request = AdjudicatorRequest(
                case_json=case_json,
                instruction=instruction,
                output_schema=output_schema,
                evidence_catalog_json=evidence_catalog_json,
                previous_output_json=previous_json,
                validation_errors=validation_errors,
            )
            attempt_record: dict[str, Any] = {
                "attempt": attempt,
                "response_received": False,
                "validation_result": "NOT_RUN",
                "validation_errors": [],
            }
            try:
                if transport is None:
                    transport = _default_transport(self.config)
                response = transport.generate(request)
                candidate_value, metadata = _response_value(response)
                last_metadata = metadata
                attempt_record["response_received"] = True
                candidate, decode_error, serialized = _decode_candidate(candidate_value)
                attempt_record["response_digest"] = hashlib.sha256(
                    serialized.encode("utf-8")
                ).hexdigest()[:32]
                previous_json = serialized
                if decode_error:
                    raise AdjudicationError(decode_error)
                assert candidate is not None
                try:
                    artifact = _candidate_artifact(candidate, case, self.config)
                except AdjudicationError:
                    raise
                except (
                    Exception
                ) as exc:  # malformed structured fields are validation failures
                    raise AdjudicationError(
                        f"model output cannot be assembled: {exc}"
                    ) from exc
                attempt_record["validation_result"] = "VALID"
                receipt["attempts"].append(attempt_record)
                receipt["attempt_count"] = attempt
                receipt["runtime_status"] = "SUCCEEDED"
                receipt["validation_result"] = "VALID"
                receipt["validation_errors"] = []
                receipt["adjudication_id"] = artifact["adjudication_id"]
                if last_metadata:
                    receipt["provider_response_metadata"] = {
                        str(key): value
                        for key, value in last_metadata.items()
                        if isinstance(value, (str, int, float, bool))
                    }
                if output_dir is not None:
                    # This is intentionally after local validation.  A failed
                    # model response can never become a downstream artifact.
                    write_governance_adjudication(artifact, output_dir)
                    _write_invocation_receipt(receipt, output_dir)
                return artifact
            except AdjudicationError as exc:
                validation_errors = tuple(
                    str(error) for error in str(exc).split("; ") if error
                )
                attempt_record["validation_errors"] = list(validation_errors)
                attempt_record["validation_result"] = "INVALID"
                receipt["attempts"].append(attempt_record)
                receipt["attempt_count"] = attempt
                receipt["validation_errors"] = list(validation_errors)
                if attempt < self.config.attempts:
                    continue
                receipt["runtime_status"] = "FAILED_VALIDATION"
                receipt["validation_result"] = "INVALID"
                if output_dir is not None:
                    _write_invocation_receipt(receipt, output_dir)
                raise ModelAdjudicationInvocationError(
                    "model adjudication failed local validation after bounded repair",
                    receipt,
                ) from exc
            except (
                Exception
            ) as exc:  # provider/runtime failures are not epistemic states
                attempt_record["runtime_error"] = _redact_runtime_error(
                    exc, self.config
                )
                receipt["attempts"].append(attempt_record)
                receipt["attempt_count"] = attempt
                receipt["runtime_status"] = "FAILED_PROVIDER"
                receipt["validation_result"] = "NOT_RUN"
                receipt["validation_errors"] = []
                if output_dir is not None:
                    _write_invocation_receipt(receipt, output_dir)
                raise ModelAdjudicationInvocationError(
                    "model adjudication provider/runtime failure",
                    receipt,
                ) from exc

        # The loop always returns or raises; retain an explicit guard for
        # static analyzers and future changes to the retry policy.
        raise ModelAdjudicationInvocationError(
            "model adjudication did not run", receipt
        )


def adjudicate_governance_case(
    case: GovernanceCase,
    *,
    adjudicator_config: ModelAdjudicatorConfig | Mapping[str, Any],
    transport: AdjudicatorTransport | None = None,
    output_dir: Path | str | None = None,
) -> GovernanceAdjudication:
    """Adjudicate one complete GovernanceCase and return a valid artifact."""

    return ModelAdjudicator(adjudicator_config, transport=transport).adjudicate(
        case,
        output_dir=output_dir,
    )


__all__ = [
    "ADJUDICATION_INSTRUCTION",
    "DEFAULT_MODEL",
    "INVOCATION_SCHEMA",
    "INVOCATION_VERSION",
    "MAX_ATTEMPTS",
    "MODEL_DRAFT_SCHEMA",
    "MODEL_DRAFT_VERSION",
    "MODEL_INSTRUCTION_VERSION",
    "AdjudicatorRequest",
    "AdjudicatorTransport",
    "AdjudicatorTransportResponse",
    "GovernanceAdjudication",
    "GovernanceCase",
    "ModelAdjudicationDraft",
    "ModelAdjudicationInvocationError",
    "ModelAdjudicator",
    "ModelAdjudicatorConfig",
    "OpenRouterAdjudicatorTransport",
    "adjudicate_governance_case",
    "build_case_evidence_catalog",
    "compile_model_adjudication_draft",
    "governance_adjudication_schema",
    "model_adjudication_draft_schema",
    "write_governance_adjudication_invocation",
]
