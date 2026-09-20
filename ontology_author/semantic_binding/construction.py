"""Bounded semantic-construction projection and candidate compiler.

The projection is deliberately case-scoped.  It gives a constructor a finite
set of semantic referents, program endpoints, observations, mechanical facts,
and maintenance dependencies.  It does not expose a repository and it does
not decide whether the resulting candidate may be persisted.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ontology_author.authority.schemas import (
    ClaimKind,
    ReferentResolution,
    RelationSupport,
)
from ontology_author.governance.model_adjudicator import (
    AdjudicatorRequest,
    AdjudicatorTransport,
    AdjudicatorTransportResponse,
)

from .schemas import (
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    CLASS_MEMBERSHIP_PROGRAM_ROLE_KINDS,
    MAINTENANCE_DEPENDENCY_KINDS,
    PROGRAM_INVARIANT_OBLIGATION_KIND,
    PROGRAM_INVARIANT_PROGRAM_ROLE_KINDS,
    PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
    PROGRAM_RELATIONSHIP_PROGRAM_ROLE_KINDS,
    CandidateValidationError,
    ConstructionObligation,
    EvidenceClass,
    SemanticCandidate,
    SemanticConstructionInvocationError,
    SemanticPersistenceError,
    canonical_json,
    copy_json,
    digest,
    write_json_artifact,
)

CONSTRUCTION_CATALOG_VERSION = "semantic_construction_catalog/v0"
MODEL_CONSTRUCTION_VERSION = "semantic-constructor/v0"
SEMANTIC_CONSTRUCTION_INVOCATION_SCHEMA = "semantic_construction_invocation/v0"
SEMANTIC_CONSTRUCTION_INSTRUCTION_VERSION = "semantic-constructor-instruction/v1"
SEMANTIC_CONSTRUCTION_INSTRUCTION = """You are a bounded semantic constructor.

Answer only the supplied ConstructionObligation using only the enumerated
case-scoped catalog. Return exactly one JSON object matching the supplied
schema. Select aliases from the catalog; never invent evidence, endpoints,
semantic referents, maintenance dependencies, or IDs. The output is a
SemanticCandidate proposal, not a persistence decision: do not emit a
persistence outcome, confidence, trust score, or maintenance result.

Use CROSS_EVIDENCE_INFERRED only when the supplied authority/semantic and
program evidence together support the proposed relation. If the supplied
evidence does not establish the relation, preserve uncertainty in the
candidate (for example with HYPOTHESIZED support); deterministic admission
will decide its lifecycle. Do not use a negative claim unless the supplied
completeness receipt explicitly covers the declared scope. Do not provide
hidden reasoning or prose outside the JSON object."""
CLASS_MEMBERSHIP_CONSTRUCTION_INSTRUCTION = """You are a bounded CLASS_MEMBERSHIP constructor.

Answer only whether the already-fixed program manifestation belongs to the
already-fixed semantic class. The program subject and semantic class are
supplied by the obligation; do not replace them, do not search a repository,
and do not invent evidence. Return exactly one JSON object matching the
supplied schema. Select only catalog aliases.

Return MEMBER only if the supplied authority, program source, and mechanical
facts together establish membership. If they do not, return UNRESOLVED.
Do not emit NON_MEMBER, a persistence outcome, confidence, or hidden
reasoning."""
_CATEGORIES = {
    "SEMANTIC_REFERENT",
    "PROGRAM_ENDPOINT",
    "AUTHORITATIVE_EVIDENCE",
    "PROGRAM_SOURCE",
    "MECHANICAL_FACT",
    "SUPPORTING_MATERIAL",
    "MAINTENANCE_DEPENDENCY",
    "COMPLETENESS_RECEIPT",
}
_CERTAIN_RESOLUTIONS = {
    item.value
    for item in (
        ReferentResolution.NATIVE_ID,
        ReferentResolution.DETERMINISTIC,
        ReferentResolution.SOURCE_DEFINED,
        ReferentResolution.AGENT_RESOLVED,
    )
}


def _as_obligation(
    value: ConstructionObligation | Mapping[str, Any],
) -> ConstructionObligation:
    return (
        value
        if isinstance(value, ConstructionObligation)
        else ConstructionObligation.from_dict(value)
    )


def trusted_role_signature(
    obligation: ConstructionObligation | Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return trusted structural role constraints for one obligation.

    The signature is derived from the obligation shape and the application
    profile.  It can constrain mechanical entity kinds, but it never chooses
    a semantic referent or a particular program entity.
    """

    selected = _as_obligation(obligation)
    signature: dict[str, dict[str, Any]] = {}
    for role, category in selected.tuple_shape.items():
        signature[role] = {
            "category": (
                "SEMANTIC_REFERENT" if category == "SEMANTIC" else "PROGRAM_ENDPOINT"
            )
        }
    if selected.obligation_kind in {
        PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        PROGRAM_INVARIANT_OBLIGATION_KIND,
        CLASS_MEMBERSHIP_OBLIGATION_KIND,
    }:
        role_kinds = (
            PROGRAM_RELATIONSHIP_PROGRAM_ROLE_KINDS
            if selected.obligation_kind == PROGRAM_RELATIONSHIP_OBLIGATION_KIND
            else PROGRAM_INVARIANT_PROGRAM_ROLE_KINDS
            if selected.obligation_kind == PROGRAM_INVARIANT_OBLIGATION_KIND
            else CLASS_MEMBERSHIP_PROGRAM_ROLE_KINDS
        )
        for role in (
            role
            for role, category in selected.tuple_shape.items()
            if category == "PROGRAM"
        ):
            signature[role]["allowed_program_kinds"] = list(
                role_kinds.get(role, ())
            )
    return signature


def _case(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not str(value.get("case_id") or "").strip():
        raise SemanticPersistenceError(
            "construction input must be a GovernanceCase with case_id"
        )
    return value


def _add_entry(
    entries: list[dict[str, Any]],
    *,
    category: str,
    identifier: str,
    kind: str,
    evidence_class: str,
    description: str = "",
    **extra: Any,
) -> None:
    identifier = str(identifier or "").strip()
    if not identifier:
        return
    item: dict[str, Any] = {
        "category": category,
        "id": identifier,
        "kind": kind,
        "evidence_class": evidence_class,
        "description": description,
    }
    item.update(copy_json(extra))
    entries.append(item)


def _authority_observation_entries(
    case: Mapping[str, Any],
    obligation: ConstructionObligation,
    entries: list[dict[str, Any]],
) -> None:
    observations = (case.get("authority") or {}).get("observations") or []
    wanted = set(obligation.authority_refs)
    for item in observations:
        if not isinstance(item, Mapping):
            continue
        identifier = str(item.get("observation_id") or "")
        if (
            wanted
            and identifier not in wanted
            and str(item.get("handle") or "") not in wanted
        ):
            continue
        _add_entry(
            entries,
            category="AUTHORITATIVE_EVIDENCE",
            identifier=identifier,
            kind="authority_observation",
            evidence_class=EvidenceClass.AUTHORITY_GROUNDING.value,
            description=str(item.get("reconstructed_text") or item.get("handle") or ""),
            pointer={
                "provider": item.get("provider"),
                "native_handle": item.get("handle"),
                "source_revision": item.get("revision"),
                "native_location": item.get("native_location"),
                "standing": item.get("standing"),
            },
        )


def _semantic_entries(case: Mapping[str, Any], entries: list[dict[str, Any]]) -> None:
    context = case.get("semantic_context") or {}
    referents = (
        context.get("referents")
        or (case.get("authority") or {}).get("semantic_referents")
        or []
    )
    for item in referents:
        if not isinstance(item, Mapping):
            continue
        identifier = str(item.get("id") or "")
        if not identifier.startswith("semantic:"):
            continue
        _add_entry(
            entries,
            category="SEMANTIC_REFERENT",
            identifier=identifier,
            kind="semantic_referent",
            evidence_class=EvidenceClass.AUTHORITY_GROUNDING.value,
            description=str(item.get("label") or identifier),
            resolution=ReferentResolution.AGENT_RESOLVED.value,
            source_observation_ids=item.get("source_observation_ids") or [],
        )
    for item in context.get("claims") or []:
        if not isinstance(item, Mapping):
            continue
        identifier = str(item.get("assertion_id") or "")
        if not identifier:
            continue
        claim_kind = str(item.get("claim_kind") or "claim")
        evidence_class = (
            EvidenceClass.PROGRAM_GROUNDING.value
            if claim_kind == ClaimKind.SEMANTIC_PROGRAM.value
            else EvidenceClass.AUTHORITY_GROUNDING.value
        )
        _add_entry(
            entries,
            category="MECHANICAL_FACT"
            if claim_kind == ClaimKind.SEMANTIC_PROGRAM.value
            else "AUTHORITATIVE_EVIDENCE",
            identifier=identifier,
            kind="claim",
            evidence_class=evidence_class,
            description=str(item.get("relation_name") or "persisted semantic claim"),
            persisted_claim=copy_json(item),
        )


def _supporting_entries(case: Mapping[str, Any], entries: list[dict[str, Any]]) -> None:
    for item in case.get("supporting_material") or []:
        if not isinstance(item, Mapping):
            continue
        identifier = str(
            item.get("observation_id")
            or item.get("evidence_id")
            or item.get("id")
            or item.get("handle")
            or ""
        )
        _add_entry(
            entries,
            category="SUPPORTING_MATERIAL",
            identifier=identifier,
            kind="supporting_material",
            evidence_class=EvidenceClass.SUPPORTING_MATERIAL.value,
            description=str(
                item.get("reconstructed_text") or item.get("handle") or identifier
            ),
            pointer=copy_json(item),
        )


def _program_entries(
    case: Mapping[str, Any],
    obligation: ConstructionObligation,
    entries: list[dict[str, Any]],
    bounded_program_source: Sequence[Mapping[str, Any]],
    program_endpoint_kinds: Mapping[str, str] | None,
) -> None:
    context = case.get("program_context") or {}
    endpoint_kinds = {
        str(identifier): str(kind)
        for identifier, kind in (program_endpoint_kinds or {}).items()
        if str(identifier) and str(kind)
    }
    known: dict[str, dict[str, Any]] = {}
    for item in context.get("referents") or []:
        if isinstance(item, Mapping) and item.get("id"):
            known[str(item["id"])] = dict(item)
    for identifier in obligation.allowed_program_endpoints:
        known.setdefault(
            identifier,
            {"id": identifier, "kind": endpoint_kinds.get(identifier, "")},
        )
    for identifier, item in sorted(known.items()):
        _add_entry(
            entries,
            category="PROGRAM_ENDPOINT",
            identifier=identifier,
            kind="program_referent",
            evidence_class="PROGRAM_IDENTITY",
            description=str(item.get("label") or item.get("kind") or identifier),
            side=item.get("side"),
            resolution=ReferentResolution.DETERMINISTIC.value,
            program_kind=str(
                endpoint_kinds.get(identifier)
                or item.get("program_entity_kind")
                or item.get("kind")
                or ""
            ),
        )
    for item in context.get("source_evidence") or []:
        if not isinstance(item, Mapping):
            continue
        _add_entry(
            entries,
            category="PROGRAM_SOURCE",
            identifier=str(item.get("evidence_id") or ""),
            kind="program_source",
            evidence_class=EvidenceClass.PROGRAM_GROUNDING.value,
            description=str(
                item.get("reconstructed_text") or item.get("program_entity") or ""
            ),
            pointer=copy_json(item),
        )
    for item in bounded_program_source:
        if not isinstance(item, Mapping):
            raise SemanticPersistenceError(
                "bounded program source entries must be objects"
            )
        _add_entry(
            entries,
            category="PROGRAM_SOURCE",
            identifier=str(item.get("evidence_id") or ""),
            kind="program_source",
            evidence_class=EvidenceClass.PROGRAM_GROUNDING.value,
            description=str(
                item.get("reconstructed_text")
                or item.get("text")
                or item.get("program_entity")
                or ""
            ),
            pointer=copy_json(item),
        )


def _mechanical_entries(case: Mapping[str, Any], entries: list[dict[str, Any]]) -> None:
    context = case.get("program_context") or {}
    for item in context.get("relation_tuples") or []:
        if not isinstance(item, Mapping):
            continue
        identifier = str(item.get("evidence_id") or "")
        _add_entry(
            entries,
            category="MECHANICAL_FACT",
            identifier=identifier,
            kind="relation_tuple",
            evidence_class=EvidenceClass.MECHANICAL_GROUNDING.value,
            description=str(
                (item.get("recorded_fact") or {}).get("relation")
                or "mechanical relation fact"
            ),
            fact=copy_json(item),
        )
    for item in context.get("resolution_outcomes") or []:
        if not isinstance(item, Mapping):
            continue
        _add_entry(
            entries,
            category="MECHANICAL_FACT",
            identifier=str(item.get("evidence_id") or ""),
            kind="resolution_outcome",
            evidence_class=EvidenceClass.MECHANICAL_GROUNDING.value,
            description=str(item.get("capability") or "resolution outcome"),
            fact=copy_json(item),
        )
    for item in case.get("transition_facts") or []:
        if not isinstance(item, Mapping):
            continue
        for identifier in item.get("mechanical_evidence_refs") or []:
            _add_entry(
                entries,
                category="MECHANICAL_FACT",
                identifier=str(identifier),
                kind="delta",
                evidence_class=EvidenceClass.MECHANICAL_GROUNDING.value,
                description="selected old/new transition fact",
                fact=copy_json(item),
            )


def _dependency_entries(
    case: Mapping[str, Any],
    entries: list[dict[str, Any]],
    explicit: Sequence[Mapping[str, Any]],
) -> None:
    candidates: list[dict[str, Any]] = [
        dict(item) for item in explicit if isinstance(item, Mapping)
    ]
    relation_evidence = {
        json.dumps(item.get("recorded_fact") or {}, sort_keys=True): str(
            item.get("evidence_id") or ""
        )
        for item in (case.get("program_context") or {}).get("relation_tuples") or []
        if isinstance(item, Mapping) and item.get("evidence_id")
    }
    for selection in case.get("selection") or []:
        if not isinstance(selection, Mapping):
            continue
        warrant = selection.get("attachment_warrant") or {}
        entity = str(warrant.get("program_entity") or "")
        if entity:
            candidates.append({"kind": "program_identity", "program_entity": entity})
        for relation in warrant.get("justifying_program_relations") or []:
            if isinstance(relation, Mapping):
                candidate = {
                    "kind": "relation_tuple",
                    "recorded": copy_json(relation),
                }
                evidence_id = relation_evidence.get(
                    json.dumps(relation, sort_keys=True)
                )
                if evidence_id:
                    candidate["evidence_id"] = evidence_id
                candidates.append(candidate)
        chain = warrant.get("structural_context") or []
        if chain:
            candidates.append(
                {
                    "kind": "structural_context",
                    "program_entity": entity,
                    "chain": copy_json(chain),
                }
            )
    for candidate in candidates:
        if not str(candidate.get("dependency_id") or ""):
            candidate["dependency_id"] = digest(candidate, "dependency")
        identifier = str(candidate["dependency_id"])
        _add_entry(
            entries,
            category="MAINTENANCE_DEPENDENCY",
            identifier=identifier,
            kind="dependency",
            evidence_class=EvidenceClass.MECHANICAL_GROUNDING.value,
            description=str(candidate.get("kind") or "maintenance dependency"),
            dependency=candidate,
        )


def _completeness_entries(
    case: Mapping[str, Any],
    entries: list[dict[str, Any]],
    explicit: Sequence[Mapping[str, Any]],
) -> None:
    values = list(explicit)
    raw = case.get("completeness") or case.get("completeness_receipts") or []
    if isinstance(raw, Mapping):
        values.extend(item for item in raw.values() if isinstance(item, Mapping))
    else:
        values.extend(item for item in raw if isinstance(item, Mapping))
    for item in values:
        identifier = str(item.get("receipt_id") or item.get("id") or "")
        if not identifier:
            continue
        _add_entry(
            entries,
            category="COMPLETENESS_RECEIPT",
            identifier=identifier,
            kind="completeness",
            evidence_class=EvidenceClass.MECHANICAL_GROUNDING.value,
            description=str(item.get("scope") or "completeness receipt"),
            receipt=copy_json(item),
        )


def build_semantic_construction_catalog(
    obligation: ConstructionObligation | Mapping[str, Any],
    case: Mapping[str, Any],
    *,
    bounded_program_source: Sequence[Mapping[str, Any]] = (),
    maintenance_dependencies: Sequence[Mapping[str, Any]] = (),
    completeness_receipts: Sequence[Mapping[str, Any]] = (),
    program_endpoint_kinds: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic legal-reference catalog for one obligation."""

    selected = _as_obligation(obligation)
    selected_case = _case(case)
    entries: list[dict[str, Any]] = []
    _authority_observation_entries(selected_case, selected, entries)
    _semantic_entries(selected_case, entries)
    _supporting_entries(selected_case, entries)
    _program_entries(
        selected_case,
        selected,
        entries,
        bounded_program_source,
        program_endpoint_kinds,
    )
    _mechanical_entries(selected_case, entries)
    _dependency_entries(selected_case, entries, maintenance_dependencies)
    _completeness_entries(selected_case, entries, completeness_receipts)

    # Stable aliases are generated after sorting canonical entries. Duplicate
    # canonical IDs in different legal categories retain separate aliases.
    category_order = {
        "SEMANTIC_REFERENT": "Q",
        "PROGRAM_ENDPOINT": "P",
        "AUTHORITATIVE_EVIDENCE": "A",
        "PROGRAM_SOURCE": "S",
        "MECHANICAL_FACT": "M",
        "SUPPORTING_MATERIAL": "U",
        "MAINTENANCE_DEPENDENCY": "D",
        "COMPLETENESS_RECEIPT": "C",
    }
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in entries:
        key = (str(item["category"]), str(item["id"]), str(item["kind"]))
        unique[key] = item
    ordered = sorted(
        unique.values(),
        key=lambda item: (str(item["category"]), str(item["id"]), str(item["kind"])),
    )
    counters: dict[str, int] = {}
    catalog_entries: list[dict[str, Any]] = []
    for item in ordered:
        category = str(item["category"])
        counters[category] = counters.get(category, 0) + 1
        catalog_entries.append(
            {
                "alias": f"{category_order[category]}{counters[category]}",
                **copy_json(item),
            }
        )
    return {
        "contract": CONSTRUCTION_CATALOG_VERSION,
        "version": CONSTRUCTION_CATALOG_VERSION,
        "model_input_version": MODEL_CONSTRUCTION_VERSION,
        "obligation": selected.to_dict(),
        "case_id": str(selected_case["case_id"]),
        "role_signature": trusted_role_signature(selected),
        "entries": catalog_entries,
        "allowed_aliases": {
            category: [
                item["alias"]
                for item in catalog_entries
                if item["category"] == category
            ]
            for category in sorted(_CATEGORIES)
        },
    }


def _catalog_index(catalog: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if catalog.get("contract") != CONSTRUCTION_CATALOG_VERSION:
        raise CandidateValidationError("unsupported semantic construction catalog")
    index: dict[str, dict[str, Any]] = {}
    for item in catalog.get("entries") or []:
        if not isinstance(item, Mapping) or not str(item.get("alias") or ""):
            raise CandidateValidationError(
                "construction catalog contains malformed entry"
            )
        alias = str(item["alias"])
        if alias in index:
            raise CandidateValidationError(
                f"construction catalog repeats alias {alias}"
            )
        index[alias] = dict(item)
    return index


def _catalog_entry_by_id(
    catalog: Mapping[str, Any], identifier: str
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in catalog.get("entries") or []
        if str(item.get("id") or "") == identifier
    ]


def semantic_candidate_schema(catalog: Mapping[str, Any]) -> dict[str, Any]:
    """Return a dynamic schema whose references are aliases in this catalog."""

    index = _catalog_index(catalog)
    obligation = ConstructionObligation.from_dict(catalog["obligation"])
    role_signature = trusted_role_signature(obligation)
    aliases = lambda category: [
        alias for alias, item in index.items() if item["category"] == category
    ]
    evidence_fields = {
        "authority_evidence_aliases": (
            "AUTHORITATIVE_EVIDENCE",
            EvidenceClass.AUTHORITY_GROUNDING.value,
        ),
        "program_source_evidence_aliases": (
            "PROGRAM_SOURCE",
            EvidenceClass.PROGRAM_GROUNDING.value,
        ),
        "mechanical_evidence_aliases": (
            "MECHANICAL_FACT",
            EvidenceClass.MECHANICAL_GROUNDING.value,
        ),
    }
    required_classes = set(obligation.required_evidence_classes)
    if obligation.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND:
        evidence_properties: dict[str, Any] = {}
        for field, (category, evidence_class) in evidence_fields.items():
            legal_aliases = aliases(category)
            evidence_properties[field] = {
                "type": "array",
                "items": {"enum": legal_aliases} if legal_aliases else {"type": "string"},
                "minItems": 0,
                "maxItems": max(len(legal_aliases), 0),
            }
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "result",
                "authority_evidence_aliases",
                "program_source_evidence_aliases",
                "mechanical_evidence_aliases",
                "maintenance_dependency_aliases",
            ],
            "properties": {
                "result": {"enum": ["MEMBER", "UNRESOLVED"]},
                **evidence_properties,
                "maintenance_dependency_aliases": {
                    "type": "array",
                    "items": (
                        {"enum": aliases("MAINTENANCE_DEPENDENCY")}
                        if aliases("MAINTENANCE_DEPENDENCY")
                        else {"type": "string"}
                    ),
                    "maxItems": len(aliases("MAINTENANCE_DEPENDENCY")),
                },
            },
        }
    is_structured = obligation.obligation_kind in {
        PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        PROGRAM_INVARIANT_OBLIGATION_KIND,
    }
    semantic_roles = [
        role for role, kind in obligation.tuple_shape.items() if kind == "SEMANTIC"
    ]
    program_roles = [
        role for role, kind in obligation.tuple_shape.items() if kind == "PROGRAM"
    ]
    evidence_properties: dict[str, Any] = {}
    for field, (category, evidence_class) in evidence_fields.items():
        legal_aliases = aliases(category)
        evidence_properties[field] = {
            "type": "array",
            "items": {"enum": legal_aliases},
            "minItems": 1 if evidence_class in required_classes else 0,
            "maxItems": len(legal_aliases),
        }
    endpoint_properties: dict[str, Any]
    endpoint_required: list[str]
    if is_structured:
        def role_aliases(role: str) -> list[str]:
            allowed_kinds = set(
                role_signature.get(role, {}).get("allowed_program_kinds") or ()
            )
            allowed_endpoints = set(obligation.allowed_program_endpoints)
            return [
                alias
                for alias, item in index.items()
                if item["category"] == "PROGRAM_ENDPOINT"
                and str(item.get("id") or "") in allowed_endpoints
                and str(item.get("program_kind") or "") in allowed_kinds
            ]

        endpoint_properties = {
            "semantic_endpoints": {
                "type": "object",
                "additionalProperties": False,
                "required": semantic_roles,
                "properties": {
                    role: {"type": "string", "enum": aliases("SEMANTIC_REFERENT")}
                    for role in semantic_roles
                },
            },
            "program_endpoints": {
                "type": "object",
                "additionalProperties": False,
                "required": program_roles,
                "properties": {
                    role: {"type": "string", "enum": role_aliases(role)}
                    for role in program_roles
                },
            },
        }
        endpoint_required = ["semantic_endpoints", "program_endpoints"]
    else:
        endpoint_properties = {
            "semantic_endpoint_aliases": {
                "type": "array",
                "items": {"enum": aliases("SEMANTIC_REFERENT")},
                "minItems": 1,
            },
            "program_endpoint_aliases": {
                "type": "array",
                "items": {"enum": aliases("PROGRAM_ENDPOINT")},
                "minItems": 1,
            },
        }
        endpoint_required = [
            "semantic_endpoint_aliases",
            "program_endpoint_aliases",
        ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "obligation_id",
            "claim_kind",
            "relation_name",
            *endpoint_required,
            "polarity",
            "support_kind",
            *evidence_fields,
            "program_scope",
            "maintenance_dependency_aliases",
            "completeness_aliases",
        ],
        "properties": {
            "obligation_id": {"const": obligation.obligation_id},
            "claim_kind": {"enum": [ClaimKind.SEMANTIC_PROGRAM.value]},
            "relation_name": (
                {"const": obligation.semantic_relation}
                if is_structured
                else {"type": "string", "minLength": 1}
            ),
            **endpoint_properties,
            "polarity": {"enum": ["POSITIVE", "NEGATIVE"]},
            "support_kind": {"enum": [str(item.value) for item in RelationSupport]},
            **evidence_properties,
            "program_scope": {"const": obligation.program_scope},
            "maintenance_dependency_aliases": {
                "type": "array",
                "items": {"enum": aliases("MAINTENANCE_DEPENDENCY")},
                "maxItems": len(aliases("MAINTENANCE_DEPENDENCY")),
            },
            "completeness_aliases": {
                "type": "array",
                "items": {"enum": aliases("COMPLETENESS_RECEIPT")},
                "minItems": (
                    1
                    if obligation.obligation_kind == PROGRAM_INVARIANT_OBLIGATION_KIND
                    else 0
                ),
                "maxItems": len(aliases("COMPLETENESS_RECEIPT")),
            },
        },
    }


def _construction_request(
    obligation: ConstructionObligation,
    catalog: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    previous_output_json: str | None = None,
    validation_errors: Sequence[str] = (),
) -> AdjudicatorRequest:
    """Create the provider-neutral request for one bounded construction."""

    input_payload = {
        "contract": MODEL_CONSTRUCTION_VERSION,
        "case_id": str(catalog.get("case_id") or ""),
        "construction_obligation": obligation.to_dict(),
        "case_scoped_catalog": copy_json(catalog),
    }
    return AdjudicatorRequest(
        case_json=canonical_json(input_payload),
        instruction=(
            CLASS_MEMBERSHIP_CONSTRUCTION_INSTRUCTION
            if obligation.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
            else SEMANTIC_CONSTRUCTION_INSTRUCTION
        ),
        output_schema=schema,
        previous_output_json=previous_output_json,
        validation_errors=tuple(str(item) for item in validation_errors),
    )


def _construction_payload(
    response: AdjudicatorTransportResponse | Any,
) -> tuple[Mapping[str, Any] | None, Mapping[str, Any], str | None]:
    if isinstance(response, AdjudicatorTransportResponse):
        payload = response.payload
        metadata = response.metadata
    else:
        payload = response
        metadata = {}
    if isinstance(payload, Mapping):
        return payload, metadata, None
    if not isinstance(payload, str):
        return None, metadata, "constructor response is not a JSON object"
    try:
        parsed = json.loads(payload)
    except (TypeError, ValueError) as exc:
        return None, metadata, f"constructor response is not valid JSON: {exc}"
    if not isinstance(parsed, Mapping):
        return None, metadata, "constructor response JSON must be an object"
    return parsed, metadata, None


def _validate_model_draft_shape(
    draft: Mapping[str, Any], schema: Mapping[str, Any]
) -> tuple[str, ...]:
    """Apply the small structural subset used by the dynamic JSON Schema.

    Cursor/provider structured-output guarantees are useful but not trusted as
    the local boundary.  This deliberately checks shape and legal enum
    members only; semantic admission remains a separate step.
    """

    errors: list[str] = []

    def check(value: Any, rule: Mapping[str, Any], path: str) -> None:
        if "const" in rule and value != rule["const"]:
            errors.append(f"{path} must equal {rule['const']!r}")
        enum = rule.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{path} is not one of the supplied enum values")
        value_type = rule.get("type")
        if value_type == "array":
            if not isinstance(value, list):
                errors.append(f"{path} must be an array")
                return
            minimum = int(rule.get("minItems") or 0)
            maximum = rule.get("maxItems")
            if len(value) < minimum:
                errors.append(f"{path} requires at least {minimum} item(s)")
            if maximum is not None and len(value) > int(maximum):
                errors.append(f"{path} allows at most {maximum} item(s)")
            item_rule = rule.get("items")
            if isinstance(item_rule, Mapping):
                for index, item in enumerate(value):
                    check(item, item_rule, f"{path}[{index}]")
            return
        if value_type == "object":
            if not isinstance(value, Mapping):
                errors.append(f"{path} must be an object")
                return
            properties = rule.get("properties") or {}
            missing = [
                str(field) for field in rule.get("required") or [] if field not in value
            ]
            errors.extend(f"missing required field: {path}.{field}" for field in missing)
            if rule.get("additionalProperties") is False:
                errors.extend(
                    f"unknown field: {path}.{field}"
                    for field in sorted(set(value) - set(properties))
                )
            for field, child_rule in properties.items():
                if field in value and isinstance(child_rule, Mapping):
                    check(value[field], child_rule, f"{path}.{field}")

    properties = schema.get("properties") or {}
    required = schema.get("required") or []
    missing = [str(field) for field in required if field not in draft]
    errors.extend(f"missing required field: {field}" for field in missing)
    if schema.get("additionalProperties") is False:
        errors.extend(
            f"unknown field: {field}"
            for field in sorted(set(draft) - set(properties))
        )
    for field, rule in properties.items():
        if field in draft and isinstance(rule, Mapping):
            check(draft[field], rule, str(field))
    return tuple(sorted(set(errors)))


def _safe_metadata(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep invocation receipts inspectable without persisting credentials."""

    if not isinstance(value, Mapping):
        return {}
    blocked = ("secret", "token", "password", "api_key", "authorization")
    return {
        str(key): copy_json(item)
        for key, item in value.items()
        if not any(fragment in str(key).lower() for fragment in blocked)
    }


def _construction_receipt(
    obligation: ConstructionObligation,
    catalog: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    constructor_metadata: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    runtime_status: str,
    validation_result: str,
    validation_errors: Sequence[str] = (),
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return {
        "contract": SEMANTIC_CONSTRUCTION_INVOCATION_SCHEMA,
        "invocation_version": SEMANTIC_CONSTRUCTION_INVOCATION_SCHEMA,
        "case_id": str(catalog.get("case_id") or ""),
        "obligation_id": obligation.obligation_id,
        "constructor_kind": "MODEL",
        "constructor_metadata": _safe_metadata(constructor_metadata),
        "instruction_template_version": SEMANTIC_CONSTRUCTION_INSTRUCTION_VERSION,
        "instruction_template_hash": digest(
            CLASS_MEMBERSHIP_CONSTRUCTION_INSTRUCTION
            if obligation.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
            else SEMANTIC_CONSTRUCTION_INSTRUCTION,
            "sha256",
        ).split(":", 1)[1],
        "catalog_contract": str(catalog.get("contract") or ""),
        "catalog_version": str(catalog.get("version") or ""),
        "catalog_hash": digest(catalog, "sha256").split(":", 1)[1],
        "schema_hash": digest(schema, "sha256").split(":", 1)[1],
        "attempt_count": len(attempts),
        "attempts": [copy_json(item) for item in attempts],
        "runtime_status": runtime_status,
        "validation_result": validation_result,
        "validation_errors": sorted({str(item) for item in validation_errors}),
        "candidate_id": candidate_id,
    }


def construct_semantic_candidate(
    obligation: ConstructionObligation | Mapping[str, Any],
    case: Mapping[str, Any],
    *,
    transport: AdjudicatorTransport,
    bounded_program_source: Sequence[Mapping[str, Any]] = (),
    maintenance_dependencies: Sequence[Mapping[str, Any]] = (),
    completeness_receipts: Sequence[Mapping[str, Any]] = (),
    program_endpoint_kinds: Mapping[str, str] | None = None,
    constructor_metadata: Mapping[str, Any] | None = None,
    output_dir: Path | str | None = None,
    max_attempts: int = 2,
    construction_method: str = "bounded semantic model constructor",
) -> SemanticCandidate:
    """Run a bounded constructor and compile its output deterministically.

    The provider-neutral governance transport receives only the generated
    catalog and schema. It cannot discover a repository. At most two attempts
    are made, and no candidate artifact is written unless compilation passes.
    """

    selected = _as_obligation(obligation)
    if not hasattr(transport, "generate"):
        raise TypeError("semantic construction transport must provide generate()")
    attempts_limit = min(2, int(max_attempts))
    if attempts_limit < 1:
        raise ValueError("semantic construction max_attempts must be positive")
    catalog = build_semantic_construction_catalog(
        selected,
        case,
        bounded_program_source=bounded_program_source,
        maintenance_dependencies=maintenance_dependencies,
        completeness_receipts=completeness_receipts,
        program_endpoint_kinds=program_endpoint_kinds,
    )
    schema = semantic_candidate_schema(catalog)
    directory = Path(output_dir) if output_dir is not None else None
    if directory is not None:
        for filename in (
            "semantic.candidate.json",
            "semantic.construction.invocation.json",
        ):
            stale = directory / filename
            if stale.is_file() or stale.is_symlink():
                stale.unlink()
        write_json_artifact(catalog, directory / "semantic.construction.catalog.json")
        write_json_artifact(schema, directory / "semantic.construction.schema.json")

    attempts: list[dict[str, Any]] = []
    previous_output_json: str | None = None
    validation_errors: tuple[str, ...] = ()
    for attempt_number in range(1, attempts_limit + 1):
        request = _construction_request(
            selected,
            catalog,
            schema,
            previous_output_json=previous_output_json,
            validation_errors=validation_errors,
        )
        try:
            response = transport.generate(request)
        except Exception as exc:  # provider/runtime failure, not unresolvedness
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "FAILED_PROVIDER",
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:500],
                }
            )
            receipt = _construction_receipt(
                selected,
                catalog,
                schema,
                constructor_metadata=constructor_metadata or {},
                attempts=attempts,
                runtime_status="FAILED_PROVIDER",
                validation_result="NOT_RUN",
            )
            if directory is not None:
                write_json_artifact(
                    receipt, directory / "semantic.construction.invocation.json"
                )
            raise SemanticConstructionInvocationError(
                "semantic construction provider failed", receipt
            ) from exc
        draft, metadata, decode_error = _construction_payload(response)
        if decode_error:
            validation_errors = (decode_error,)
        else:
            assert draft is not None
            previous_output_json = canonical_json(draft)
            shape_errors = _validate_model_draft_shape(draft, schema)
            if shape_errors:
                validation_errors = shape_errors
            else:
                try:
                    candidate = compile_semantic_candidate_draft(
                        selected,
                        catalog,
                        draft,
                        construction_method=construction_method,
                    )
                except (CandidateValidationError, ValueError) as exc:
                    validation_errors = tuple(getattr(exc, "errors", (str(exc),)))
                else:
                    attempts.append(
                        {
                            "attempt": attempt_number,
                            "status": "VALID",
                            "response_metadata": _safe_metadata(metadata),
                            "draft_digest": digest(draft, "semantic-draft"),
                        }
                    )
                    receipt = _construction_receipt(
                        selected,
                        catalog,
                        schema,
                        constructor_metadata=constructor_metadata or {},
                        attempts=attempts,
                        runtime_status="SUCCEEDED",
                        validation_result="VALID",
                        candidate_id=candidate.candidate_id,
                    )
                    if directory is not None:
                        write_json_artifact(
                            candidate.to_dict(), directory / "semantic.candidate.json"
                        )
                        write_json_artifact(
                            receipt, directory / "semantic.construction.invocation.json"
                        )
                    return candidate
        attempts.append(
            {
                "attempt": attempt_number,
                "status": "FAILED_VALIDATION",
                "validation_errors": list(validation_errors),
                "draft_digest": digest(previous_output_json, "semantic-draft")
                if previous_output_json is not None
                else None,
            }
        )
    receipt = _construction_receipt(
        selected,
        catalog,
        schema,
        constructor_metadata=constructor_metadata or {},
        attempts=attempts,
        runtime_status="FAILED_VALIDATION",
        validation_result="INVALID",
        validation_errors=validation_errors,
    )
    if directory is not None:
        write_json_artifact(
            receipt, directory / "semantic.construction.invocation.json"
        )
    raise SemanticConstructionInvocationError(
        "semantic construction output remained invalid after bounded retry",
        receipt,
    )


def _resolve_aliases(
    index: Mapping[str, Mapping[str, Any]],
    values: Any,
    categories: set[str],
    location: str,
) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise CandidateValidationError(f"{location} must be an array")
    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, raw in enumerate(values):
        alias = str(raw or "")
        item = index.get(alias)
        if item is None:
            raise CandidateValidationError(
                f"{location}[{position}] alias is not in the case catalog: {alias}"
            )
        if item["category"] not in categories:
            raise CandidateValidationError(
                f"{location}[{position}] alias has illegal category {item['category']}"
            )
        if alias in seen:
            raise CandidateValidationError(f"{location} repeats alias {alias}")
        seen.add(alias)
        resolved.append(dict(item))
    return resolved


def _resolve_role_aliases(
    index: Mapping[str, Mapping[str, Any]],
    values: Any,
    roles: Sequence[str],
    category: str,
    location: str,
    allowed_kinds: Mapping[str, Sequence[str]] | Sequence[str] = (),
) -> list[dict[str, Any]]:
    if not isinstance(values, Mapping):
        raise CandidateValidationError(f"{location} must be an object")
    unknown = sorted(set(values) - set(roles))
    if unknown:
        raise CandidateValidationError(
            f"{location} contains unknown role(s): {', '.join(unknown)}"
        )
    missing = [role for role in roles if role not in values]
    if missing:
        raise CandidateValidationError(
            f"{location} is missing role(s): {', '.join(missing)}"
        )
    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    for role in roles:
        alias = str(values[role] or "")
        items = _resolve_aliases(index, [alias], {category}, f"{location}.{role}")
        if isinstance(allowed_kinds, Mapping):
            role_allowed_kinds = tuple(allowed_kinds.get(role) or ())
        else:
            role_allowed_kinds = tuple(allowed_kinds)
        if role_allowed_kinds and str(items[0].get("program_kind") or "") not in set(
            role_allowed_kinds
        ):
            raise CandidateValidationError(
                f"{location}.{role} selected program kind "
                f"{items[0].get('program_kind')!r}; allowed kinds are "
                + ", ".join(sorted(str(item) for item in role_allowed_kinds))
            )
        if alias in seen:
            raise CandidateValidationError(f"{location} repeats alias {alias}")
        seen.add(alias)
        resolved.extend(items)
    return resolved


def compile_semantic_candidate_draft(
    obligation: ConstructionObligation | Mapping[str, Any],
    catalog: Mapping[str, Any],
    draft: Mapping[str, Any],
    *,
    construction_method: str = "bounded semantic constructor",
) -> SemanticCandidate:
    """Expand a model draft into a canonical, still-non-durable candidate."""

    selected = _as_obligation(obligation)
    role_signature = trusted_role_signature(selected)
    if catalog.get("obligation") != selected.to_dict():
        raise CandidateValidationError(
            "catalog obligation does not match ConstructionObligation"
        )
    index = _catalog_index(catalog)
    if not isinstance(draft, Mapping):
        raise CandidateValidationError("semantic constructor output must be an object")
    forbidden = {
        "persistence_outcome",
        "should_persist",
        "trust_score",
        "confidence",
        "decision",
    }
    present_forbidden = sorted(forbidden.intersection(draft))
    if present_forbidden:
        raise CandidateValidationError(
            f"model cannot set persistence fields: {', '.join(present_forbidden)}"
        )
    expected = {
        "obligation_id",
        "claim_kind",
        "relation_name",
        "polarity",
        "support_kind",
        "authority_evidence_aliases",
        "program_source_evidence_aliases",
        "mechanical_evidence_aliases",
        "program_scope",
        "maintenance_dependency_aliases",
        "completeness_aliases",
    }
    membership_draft = selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
    if membership_draft:
        expected = {
            "result",
            "authority_evidence_aliases",
            "program_source_evidence_aliases",
            "mechanical_evidence_aliases",
            "maintenance_dependency_aliases",
        }
    elif selected.obligation_kind in {
        PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        PROGRAM_INVARIANT_OBLIGATION_KIND,
    }:
        expected.update({"semantic_endpoints", "program_endpoints"})
    else:
        expected.update({"semantic_endpoint_aliases", "program_endpoint_aliases"})
    unknown = sorted(set(draft) - expected)
    if unknown:
        raise CandidateValidationError(
            f"semantic constructor output contains unknown fields: {', '.join(unknown)}"
        )
    if membership_draft:
        return _compile_class_membership_draft(
            selected,
            catalog,
            index,
            draft,
            construction_method=construction_method,
        )
    if str(draft.get("obligation_id") or "") != selected.obligation_id:
        raise CandidateValidationError("candidate references a different obligation")
    semantic_roles = [
        role for role, kind in selected.tuple_shape.items() if kind == "SEMANTIC"
    ]
    program_roles = [
        role for role, kind in selected.tuple_shape.items() if kind == "PROGRAM"
    ]
    if selected.obligation_kind in {
        PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        PROGRAM_INVARIANT_OBLIGATION_KIND,
    }:
        semantic = _resolve_role_aliases(
            index,
            draft.get("semantic_endpoints"),
            semantic_roles,
            "SEMANTIC_REFERENT",
            "semantic_endpoints",
        )
        program = _resolve_role_aliases(
            index,
            draft.get("program_endpoints"),
            program_roles,
            "PROGRAM_ENDPOINT",
            "program_endpoints",
            allowed_kinds={
                role: tuple(
                    role_signature.get(role, {}).get("allowed_program_kinds") or ()
                )
                for role in program_roles
            },
        )
    else:
        semantic = _resolve_aliases(
            index,
            draft.get("semantic_endpoint_aliases"),
            {"SEMANTIC_REFERENT"},
            "semantic_endpoint_aliases",
        )
        program = _resolve_aliases(
            index,
            draft.get("program_endpoint_aliases"),
            {"PROGRAM_ENDPOINT"},
            "program_endpoint_aliases",
        )
    evidence: list[dict[str, Any]] = []
    for field, category in (
        ("authority_evidence_aliases", "AUTHORITATIVE_EVIDENCE"),
        ("program_source_evidence_aliases", "PROGRAM_SOURCE"),
        ("mechanical_evidence_aliases", "MECHANICAL_FACT"),
    ):
        evidence.extend(
            _resolve_aliases(index, draft.get(field), {category}, field)
        )
    dependencies = _resolve_aliases(
        index,
        draft.get("maintenance_dependency_aliases"),
        {"MAINTENANCE_DEPENDENCY"},
        "maintenance_dependency_aliases",
    )
    completeness = _resolve_aliases(
        index,
        draft.get("completeness_aliases"),
        {"COMPLETENESS_RECEIPT"},
        "completeness_aliases",
    )
    if len(semantic_roles) != len(semantic):
        raise CandidateValidationError(
            "semantic endpoint count does not match obligation tuple shape"
        )
    if len(program_roles) != len(program):
        raise CandidateValidationError(
            "program endpoint count does not match obligation tuple shape"
        )
    tuple_values = {
        **{
            role: item["id"]
            for role, item in zip(semantic_roles, semantic, strict=True)
        },
        **{role: item["id"] for role, item in zip(program_roles, program, strict=True)},
    }
    endpoint_resolution = {
        **{
            role: str(item.get("resolution") or ReferentResolution.DETERMINISTIC.value)
            for role, item in zip(semantic_roles, semantic, strict=True)
        },
        **{
            role: str(item.get("resolution") or ReferentResolution.DETERMINISTIC.value)
            for role, item in zip(program_roles, program, strict=True)
        },
    }
    candidate = SemanticCandidate(
        obligation_id=selected.obligation_id,
        claim_kind=str(draft.get("claim_kind") or ""),
        relation_name=str(draft.get("relation_name") or ""),
        tuple=tuple_values,
        polarity=str(draft.get("polarity") or ""),
        semantic_endpoint_refs=tuple(item["id"] for item in semantic),
        program_endpoint_refs=tuple(item["id"] for item in program),
        support_kind=str(draft.get("support_kind") or ""),
        endpoint_resolution=endpoint_resolution,
        evidence_refs=tuple(
            {"kind": str(item["kind"]), "id": str(item["id"])} for item in evidence
        ),
        program_scope=str(draft.get("program_scope") or ""),
        maintenance_dependencies=tuple(
            copy_json(item.get("dependency") or {}) for item in dependencies
        ),
        completeness_refs=tuple(str(item["id"]) for item in completeness),
        construction_method=construction_method,
    )
    errors = validate_semantic_candidate(selected, candidate, catalog)
    if errors:
        raise CandidateValidationError(errors)
    return candidate


def _compile_class_membership_draft(
    selected: ConstructionObligation,
    catalog: Mapping[str, Any],
    index: Mapping[str, Mapping[str, Any]],
    draft: Mapping[str, Any],
    *,
    construction_method: str,
) -> SemanticCandidate:
    result = str(draft.get("result") or "").strip().upper()
    if result not in {"MEMBER", "UNRESOLVED"}:
        raise CandidateValidationError(
            "CLASS_MEMBERSHIP result must be MEMBER or UNRESOLVED"
        )
    evidence: list[dict[str, Any]] = []
    for field, category in (
        ("authority_evidence_aliases", "AUTHORITATIVE_EVIDENCE"),
        ("program_source_evidence_aliases", "PROGRAM_SOURCE"),
        ("mechanical_evidence_aliases", "MECHANICAL_FACT"),
    ):
        evidence.extend(
            _resolve_aliases(index, draft.get(field) or [], {category}, field)
        )
    dependencies = _resolve_aliases(
        index,
        draft.get("maintenance_dependency_aliases") or [],
        {"MAINTENANCE_DEPENDENCY"},
        "maintenance_dependency_aliases",
    )
    semantic_id = selected.semantic_subject
    program_id = next(iter(selected.allowed_program_endpoints))
    semantic_entries = [
        item
        for item in index.values()
        if item.get("category") == "SEMANTIC_REFERENT" and item.get("id") == semantic_id
    ]
    program_entries = [
        item
        for item in index.values()
        if item.get("category") == "PROGRAM_ENDPOINT" and item.get("id") == program_id
    ]
    if not semantic_entries:
        raise CandidateValidationError("fixed semantic class is absent from the catalog")
    if not program_entries:
        raise CandidateValidationError("fixed program subject is absent from the catalog")
    semantic = semantic_entries[0]
    program = program_entries[0]
    candidate = SemanticCandidate(
        obligation_id=selected.obligation_id,
        claim_kind="SEMANTIC_PROGRAM",
        relation_name=selected.semantic_relation,
        tuple={
            "semantic_class": semantic_id,
            "program_manifestation": program_id,
        },
        polarity="POSITIVE",
        semantic_endpoint_refs=(semantic_id,),
        program_endpoint_refs=(program_id,),
        support_kind="CROSS_EVIDENCE_INFERRED",
        endpoint_resolution={
            "semantic_class": str(
                semantic.get("resolution") or ReferentResolution.AGENT_RESOLVED.value
            ),
            "program_manifestation": str(
                program.get("resolution") or ReferentResolution.DETERMINISTIC.value
            ),
        },
        evidence_refs=tuple(
            {"kind": str(item["kind"]), "id": str(item["id"])} for item in evidence
        ),
        program_scope=selected.program_scope,
        maintenance_dependencies=tuple(
            copy_json(item.get("dependency") or {}) for item in dependencies
        ),
        construction_method=construction_method,
        membership_result=result,
    )
    errors = validate_semantic_candidate(selected, candidate, catalog)
    if errors:
        raise CandidateValidationError(errors)
    return candidate


def validate_semantic_candidate(
    obligation: ConstructionObligation | Mapping[str, Any],
    candidate: SemanticCandidate | Mapping[str, Any],
    catalog: Mapping[str, Any],
) -> list[str]:
    """Validate candidate references and shape without deciding admission."""

    selected = _as_obligation(obligation)
    role_signature = trusted_role_signature(selected)
    try:
        value = (
            candidate
            if isinstance(candidate, SemanticCandidate)
            else SemanticCandidate.from_dict(candidate)
        )
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    try:
        index = _catalog_index(catalog)
    except CandidateValidationError as exc:
        return list(exc.errors)
    errors: list[str] = []
    expected_candidate_id = digest(value._identity_payload(), "semantic-candidate")
    if value.candidate_id != expected_candidate_id:
        errors.append("candidate_id does not match deterministic candidate content")
    if value.obligation_id != selected.obligation_id:
        errors.append("candidate references an unknown or different obligation")
    if value.program_scope != selected.program_scope:
        errors.append("candidate program scope differs from obligation")
    if (
        selected.obligation_kind == PROGRAM_INVARIANT_OBLIGATION_KIND
        and value.relation_name != selected.semantic_relation
    ) or (
        selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
        and value.relation_name != selected.semantic_relation
    ):
        errors.append(
            "structured candidate relation does not match the trusted obligation relation"
        )
    if selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND:
        allowed_subject = next(iter(selected.allowed_program_endpoints))
        if value.tuple.get("semantic_class") != selected.semantic_subject:
            errors.append("CLASS_MEMBERSHIP semantic class cannot be replaced by the model")
        if value.tuple.get("program_manifestation") != allowed_subject:
            errors.append("CLASS_MEMBERSHIP program subject cannot be replaced by the model")
        if set(value.program_endpoint_refs) != {allowed_subject}:
            errors.append("CLASS_MEMBERSHIP program subject is not the obligation subject")
        if value.membership_result not in {"MEMBER", "UNRESOLVED"}:
            errors.append("CLASS_MEMBERSHIP candidate must be MEMBER or UNRESOLVED")
        if value.polarity != "POSITIVE":
            errors.append("CLASS_MEMBERSHIP v0 does not admit NON_MEMBER")
    if set(value.tuple) != set(selected.tuple_shape):
        errors.append("candidate tuple roles do not match obligation tuple shape")
    for role, kind in selected.tuple_shape.items():
        expected = (
            value.semantic_endpoint_refs
            if kind == "SEMANTIC"
            else value.program_endpoint_refs
        )
        if value.tuple.get(role) not in expected:
            errors.append(
                f"candidate tuple role {role} is not one of its declared endpoints"
            )
    for endpoint in value.semantic_endpoint_refs:
        if not any(
            item.get("category") == "SEMANTIC_REFERENT" and item.get("id") == endpoint
            for item in index.values()
        ):
            errors.append(f"candidate uses unknown semantic endpoint {endpoint}")
    for endpoint in value.program_endpoint_refs:
        if not any(
            item.get("category") == "PROGRAM_ENDPOINT" and item.get("id") == endpoint
            for item in index.values()
        ):
            errors.append(f"candidate uses unknown program endpoint {endpoint}")
    for role, category in selected.tuple_shape.items():
        if category != "PROGRAM":
            continue
        endpoint = value.tuple.get(role)
        allowed_kinds = tuple(
            role_signature.get(role, {}).get("allowed_program_kinds") or ()
        )
        if not allowed_kinds:
            continue
        matching = [
            item
            for item in index.values()
            if item.get("category") == "PROGRAM_ENDPOINT"
            and str(item.get("id") or "") == str(endpoint or "")
        ]
        if not matching:
            continue
        actual_kinds = {
            str(item.get("program_kind") or "") for item in matching
        }
        if not actual_kinds.intersection(allowed_kinds):
            errors.append(
                f"candidate tuple role {role} uses program kind(s) "
                f"{sorted(actual_kinds)}; allowed kinds are "
                + ", ".join(sorted(allowed_kinds))
            )
    if value.claim_kind != ClaimKind.SEMANTIC_PROGRAM.value:
        errors.append(
            "supported semantic candidates must use claim kind SEMANTIC_PROGRAM"
        )
    for role, resolution in value.endpoint_resolution.items():
        if resolution not in _CERTAIN_RESOLUTIONS | {
            ReferentResolution.AMBIGUOUS.value,
            ReferentResolution.UNRESOLVED.value,
        }:
            errors.append(
                f"candidate has unknown endpoint resolution {resolution} for {role}"
            )
    valid_evidence = {
        (str(item.get("kind")), str(item.get("id"))) for item in index.values()
    }
    for item in value.evidence_refs:
        if (str(item.get("kind")), str(item.get("id"))) not in valid_evidence:
            errors.append(f"candidate uses evidence not present in catalog: {item}")
    valid_dependency_ids = {
        str(item.get("id"))
        for item in index.values()
        if item.get("category") == "MAINTENANCE_DEPENDENCY"
    }
    for dependency in value.maintenance_dependencies:
        dependency_id = str(dependency.get("dependency_id") or "")
        if dependency_id and dependency_id not in valid_dependency_ids:
            errors.append(
                f"candidate uses unknown maintenance dependency {dependency_id}"
            )
        dependency_kind = str(dependency.get("kind") or "")
        if dependency_kind not in MAINTENANCE_DEPENDENCY_KINDS:
            errors.append(
                "candidate uses unsupported maintenance dependency kind "
                + dependency_kind
            )
    valid_completeness_ids = {
        str(item.get("id"))
        for item in index.values()
        if item.get("category") == "COMPLETENESS_RECEIPT"
    }
    errors.extend(
        f"candidate uses unknown completeness receipt {identifier}"
        for identifier in value.completeness_refs
        if identifier not in valid_completeness_ids
    )
    return sorted(set(errors))


def write_construction_artifact(
    payload: Mapping[str, Any],
    output_dir: Path | str,
    *,
    filename: str = "semantic.construction.json",
) -> Path:
    return write_json_artifact(payload, Path(output_dir) / filename)


__all__ = [
    "CONSTRUCTION_CATALOG_VERSION",
    "MODEL_CONSTRUCTION_VERSION",
    "SEMANTIC_CONSTRUCTION_INSTRUCTION",
    "SEMANTIC_CONSTRUCTION_INSTRUCTION_VERSION",
    "SEMANTIC_CONSTRUCTION_INVOCATION_SCHEMA",
    "build_semantic_construction_catalog",
    "compile_semantic_candidate_draft",
    "construct_semantic_candidate",
    "semantic_candidate_schema",
    "trusted_role_signature",
    "validate_semantic_candidate",
    "write_construction_artifact",
]
