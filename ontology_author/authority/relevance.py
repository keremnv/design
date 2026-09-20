"""Persisted authority relevance scopes.

Warrant rows answer why an attachment points at a program manifestation.
Relevance-scope rows answer which ProgramDelta facts should surface that
attachment for later case assembly. The two MUST stay separate.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from ontology_author.program_spine.comparison import COMPARABLE_RELATIONS, RELATION_CAPABILITIES
from ontology_author.world.runtime.world import ConstructionWorld


CLAUSE_KINDS = (
    "ATTACHED_IDENTITY",
    "IDENTITY_MANIFESTATION",
    "ENDPOINT_RELATION",
    "STRUCTURAL_SCOPE",
    "EXPLICIT_IDENTITY",
)
SCOPE_ORIGINS = ("DEFAULT_KIND_RULE", "EXPLICIT")
MANIFESTATION_PROPERTIES = (
    "name",
    "source_location",
    "source_manifestation",
    "signature",
    "boundary",
    "structural_context",
    "identity_kind",
)
CALLABLE_KINDS = {"callable", "method"}
MODULE_KINDS = {"module", "source_unit"}
UNSUPPORTED_SCOPE_KEYS = {
    "query",
    "dsl",
    "cypher",
    "watch",
    "sql",
    "sparql",
    "score",
    "relevance_score",
    "verdict",
    "compliance",
    "compliant",
    "noncompliant",
    "pass",
    "fail",
    "violation",
    "allowed",
    "prohibited",
}
COMPLIANCE_SCOPE_TOKENS = {
    "PASS",
    "FAIL",
    "COMPLIANT",
    "NONCOMPLIANT",
    "VIOLATION",
    "ALLOWED",
    "PROHIBITED",
    "VERDICT",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def default_relevance_clauses(kind: str, program_entity: str) -> tuple[dict[str, Any], ...]:
    """Kind defaults from the governance-case contract. Always materialized."""

    attached = {
        "clause_kind": "ATTACHED_IDENTITY",
        "identity_id": program_entity,
        "relation_name": "",
        "endpoint_role": "",
        "relation_tuple": {},
        "manifestation_properties": [],
        "structural_capability": "",
    }
    if kind == "call_site":
        return (
            dict(attached),
            {
                "clause_kind": "ENDPOINT_RELATION",
                "identity_id": program_entity,
                "relation_name": "program_invokes",
                "endpoint_role": "",
                "relation_tuple": {},
                "manifestation_properties": [],
                "structural_capability": "",
            },
        )
    if kind in CALLABLE_KINDS:
        return (
            dict(attached),
            {
                "clause_kind": "IDENTITY_MANIFESTATION",
                "identity_id": program_entity,
                "relation_name": "",
                "endpoint_role": "",
                "relation_tuple": {},
                "manifestation_properties": ["signature", "source_manifestation"],
                "structural_capability": "",
            },
            {
                "clause_kind": "ENDPOINT_RELATION",
                "identity_id": program_entity,
                "relation_name": "program_invokes",
                "endpoint_role": "target",
                "relation_tuple": {},
                "manifestation_properties": [],
                "structural_capability": "",
            },
        )
    if kind in MODULE_KINDS:
        return (
            dict(attached),
            {
                "clause_kind": "ENDPOINT_RELATION",
                "identity_id": program_entity,
                "relation_name": "program_imports",
                "endpoint_role": "",
                "relation_tuple": {},
                "manifestation_properties": [],
                "structural_capability": "",
            },
        )
    return (dict(attached),)


def normalize_clause(clause: Mapping[str, Any], *, program_entity: str, origin: str) -> dict[str, Any]:
    unknown = sorted(set(clause) - {
        "clause_kind",
        "identity_id",
        "relation_name",
        "endpoint_role",
        "relation_tuple",
        "manifestation_properties",
        "structural_capability",
        "origin",
    })
    if unknown:
        raise ValueError(f"unsupported relevance-scope fields: {', '.join(unknown)}")
    lowered = {str(key).lower() for key in clause}
    if lowered & UNSUPPORTED_SCOPE_KEYS:
        raise ValueError("relevance scope must not encode a watch-query DSL or compliance outcome")
    kind = str(clause.get("clause_kind") or "")
    if kind not in CLAUSE_KINDS:
        raise ValueError(f"unsupported relevance-scope clause_kind: {kind or '<empty>'}")
    identity = str(clause.get("identity_id") or program_entity)
    relation_name = str(clause.get("relation_name") or "")
    endpoint_role = str(clause.get("endpoint_role") or "")
    raw_tuple = clause.get("relation_tuple") or {}
    if raw_tuple and not isinstance(raw_tuple, Mapping):
        raise ValueError("relevance-scope relation_tuple must be an object")
    relation_tuple = {str(key): value for key, value in dict(raw_tuple).items()}
    properties = [str(item) for item in list(clause.get("manifestation_properties") or [])]
    capability = str(clause.get("structural_capability") or "")
    if kind == "ATTACHED_IDENTITY":
        relation_name = ""
        endpoint_role = ""
        relation_tuple = {}
        properties = []
        capability = ""
        identity = program_entity
    elif kind == "IDENTITY_MANIFESTATION":
        relation_name = ""
        endpoint_role = ""
        relation_tuple = {}
        capability = ""
        if not properties:
            raise ValueError("IDENTITY_MANIFESTATION needs manifestation_properties")
        illegal = [item for item in properties if item not in MANIFESTATION_PROPERTIES]
        if illegal:
            raise ValueError(f"unsupported manifestation properties: {', '.join(illegal)}")
    elif kind == "ENDPOINT_RELATION":
        if not relation_name:
            raise ValueError("ENDPOINT_RELATION needs a relation_name")
        if relation_name not in COMPARABLE_RELATIONS:
            raise ValueError(f"ENDPOINT_RELATION uses unknown relation {relation_name!r}")
        properties = []
        capability = ""
    elif kind == "STRUCTURAL_SCOPE":
        if not identity:
            raise ValueError("STRUCTURAL_SCOPE needs a root identity")
        if relation_name and relation_name not in COMPARABLE_RELATIONS:
            raise ValueError(f"STRUCTURAL_SCOPE uses unknown relation {relation_name!r}")
        if capability and capability not in set(RELATION_CAPABILITIES.values()):
            raise ValueError(f"STRUCTURAL_SCOPE uses unknown capability {capability!r}")
        if relation_name and not capability:
            capability = RELATION_CAPABILITIES[relation_name]
        properties = list(properties)
    elif kind == "EXPLICIT_IDENTITY":
        if not identity:
            raise ValueError("EXPLICIT_IDENTITY needs identity_id")
        relation_name = str(clause.get("relation_name") or "")
        if relation_name and relation_name not in COMPARABLE_RELATIONS:
            raise ValueError(f"EXPLICIT_IDENTITY uses unknown relation {relation_name!r}")
    text_fields = [kind, relation_name, endpoint_role, capability, origin]
    if any(token in COMPLIANCE_SCOPE_TOKENS for field in text_fields for token in field.split()):
        raise ValueError("relevance scope must not encode compliance outcomes")
    return {
        "clause_kind": kind,
        "identity_id": identity,
        "relation_name": relation_name,
        "endpoint_role": endpoint_role,
        "relation_tuple": dict(sorted(relation_tuple.items())),
        "manifestation_properties": properties,
        "structural_capability": capability,
        "origin": origin,
    }


def scope_row_values(
    *,
    warrant_assertion_id: str,
    attachment_assertion_id: str,
    program_entity: str,
    clause: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "warrant_assertion_id": warrant_assertion_id,
        "attachment_assertion_id": attachment_assertion_id,
        "program_entity": program_entity,
        "clause_kind": clause["clause_kind"],
        "identity_id": clause["identity_id"],
        "relation_name": clause["relation_name"],
        "endpoint_role": clause["endpoint_role"],
        "relation_tuple": canonical_json(clause["relation_tuple"]),
        "manifestation_properties": canonical_json(clause["manifestation_properties"]),
        "structural_capability": clause["structural_capability"],
        "origin": clause["origin"],
    }


def clause_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    try:
        relation_tuple = json.loads(row.get("relation_tuple") or "{}")
    except json.JSONDecodeError:
        relation_tuple = {}
    try:
        properties = json.loads(row.get("manifestation_properties") or "[]")
    except json.JSONDecodeError:
        properties = []
    if not isinstance(relation_tuple, dict):
        relation_tuple = {}
    if not isinstance(properties, list):
        properties = []
    return {
        "clause_kind": str(row.get("clause_kind") or ""),
        "identity_id": str(row.get("identity_id") or row.get("program_entity") or ""),
        "relation_name": str(row.get("relation_name") or ""),
        "endpoint_role": str(row.get("endpoint_role") or ""),
        "relation_tuple": relation_tuple,
        "manifestation_properties": [str(item) for item in properties],
        "structural_capability": str(row.get("structural_capability") or ""),
        "origin": str(row.get("origin") or ""),
        "warrant_assertion_id": str(row.get("warrant_assertion_id") or ""),
        "attachment_assertion_id": str(row.get("attachment_assertion_id") or ""),
        "program_entity": str(row.get("program_entity") or ""),
    }


def clause_key(clause: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        clause.get("clause_kind"),
        clause.get("identity_id"),
        clause.get("relation_name"),
        clause.get("endpoint_role"),
        canonical_json(clause.get("relation_tuple") or {}),
        canonical_json(clause.get("manifestation_properties") or []),
        clause.get("structural_capability"),
    )


def relation_rows_with_ids(world: ConstructionWorld, relation: str) -> list[dict[str, Any]]:
    """Like ``relation_rows`` but keep hidden ``_assertion_id``.

    Semantic SELECT strips underscore columns. Warrant and relevance-scope
    identity needs ordinary SQL.
    """

    schema = world.relation_schema(relation)
    column_to_role = {role["column"]: role["name"] for role in schema["roles"]}
    physical = world.query(f'SELECT * FROM "{relation}"')
    return [
        {column_to_role.get(key, key): value for key, value in row.items()}
        for row in physical
    ]


def load_scope_rows(world: Any, warrant_assertion_id: str) -> list[dict[str, Any]]:
    try:
        rows = relation_rows_with_ids(world, "authority_relevance_scope")
    except Exception:
        return []
    matched = [
        clause_from_row(row)
        for row in rows
        if str(row.get("warrant_assertion_id") or "") == warrant_assertion_id
    ]
    return sorted(matched, key=lambda item: clause_key(item))


def default_clause_keys(kind: str, program_entity: str) -> set[tuple[Any, ...]]:
    return {
        clause_key({**clause, "origin": "DEFAULT_KIND_RULE"})
        for clause in default_relevance_clauses(kind, program_entity)
    }
