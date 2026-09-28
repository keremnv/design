"""Assemble and verify a bounded judgment case.

A case cites sealed Construction assertions. It is not a World, and inclusion
in the case is not applicability. This module does not apply a profile rule.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ontology_author.evidence.program_source import reconstruct_program_observation
from ontology_author.software_governance.evidence import reconstruct_governance_observation
from ontology_author.software_governance.reads import GovernanceView
from ontology_author.world.runtime.world import ConstructionWorld

CASE_RELATIONS = (
    "governance_proposition",
    "governance_binding",
    "governance_candidate",
    "governance_question",
    "governance_completeness",
    "governance_known_gap",
    "software_subject",
    "software_manifestation",
)


def assemble_case(
    view: GovernanceView,
    *,
    case_id: str,
    question: str,
    proposition_ids: tuple[str, ...],
    subject_ids: tuple[str, ...],
    omit_relations: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Present bounded World material. Inclusion is not applicability."""

    world = view.world
    labels = {
        str(row["id"]): str(row["label"])
        for row in world.query("SELECT id, label FROM _world_referents")
    }
    revision = int(world.query("SELECT revision FROM _world_meta WHERE singleton = 1")[0]["revision"])
    facts: list[dict[str, Any]] = []
    inspected: list[str] = []
    for relation in CASE_RELATIONS:
        inspected.append(relation)
        for row in world.relation_rows(relation):
            if not _selected(relation, row, proposition_ids, subject_ids):
                continue
            facts.append(_fact(world, relation, row, labels))
    mechanical_names = []
    for subject in subject_ids:
        for item in view.mechanical_facts_for_subject(subject):
            relation = str(item["relation"])
            if relation in omit_relations:
                continue
            if relation not in mechanical_names:
                mechanical_names.append(relation)
            facts.append(_fact(world, relation, item["values"], labels))
    inspected.extend(mechanical_names)
    return {
        "case_id": case_id,
        "question": question,
        "world_id": world.world_id,
        "revision": revision,
        "world_address": str(world.path.parent),
        "proposition_ids": list(proposition_ids),
        "subject_ids": list(subject_ids),
        "inspected_relations": inspected,
        "facts": facts,
    }


def verify_case(view: GovernanceView, case: dict[str, Any]) -> list[str]:
    """Check each citation against the sealed assertion and its grounding.

    Referent labels are display text. They are not part of the citation.
    """

    errors = []
    if case["world_id"] != view.world.world_id:
        errors.append("world id differs")
    for fact in case["facts"]:
        relation = str(fact["relation"])
        sealed_values = _values_for_assertion(view.world, relation, str(fact["assertion_id"]))
        if sealed_values is None:
            errors.append(f"{relation} assertion id is not in the sealed world")
            continue
        if sealed_values != fact["values"]:
            errors.append(f"{relation} values do not match the sealed assertion")
            continue
        try:
            warrant = view.world.warrant_for_assertion(fact["assertion_id"])
        except KeyError:
            errors.append(f"{relation} assertion id is not in the sealed world")
            continue
        if warrant["relation"] != relation:
            errors.append(f"{relation} assertion belongs to {warrant['relation']}")
            continue
        sealed = _support_from_warrant(view.world, warrant)
        if _fingerprint(sealed) != fact["support_fingerprint"]:
            errors.append(f"{relation} support fingerprint does not match the sealed grounding")
        if _fingerprint(fact["support"]) != fact["support_fingerprint"]:
            errors.append(f"{relation} presented support does not match its fingerprint")
    return errors


def facts(case: dict[str, Any], relation: str) -> list[dict[str, Any]]:
    return _facts(case, relation)


def _facts(case: dict[str, Any], relation: str) -> list[dict[str, Any]]:
    return [fact for fact in case["facts"] if fact["relation"] == relation]


def _selected(relation: str, row: dict[str, Any], propositions: tuple[str, ...], subjects: tuple[str, ...]) -> bool:
    if relation in {"governance_completeness", "governance_known_gap"}:
        return True
    if relation == "governance_proposition":
        return str(row["proposition"]) in propositions
    if relation in {"governance_binding", "governance_candidate"}:
        return str(row["proposition"]) in propositions and str(row["software_subject"]) in subjects
    if relation == "governance_question":
        return str(row["proposition"]) in propositions
    if relation in {"software_subject", "software_manifestation"}:
        return str(row["subject"]) in subjects
    return False


def _fact(
    world: ConstructionWorld,
    relation: str,
    row: dict[str, Any],
    labels: dict[str, str],
) -> dict[str, Any]:
    values = {str(key): str(row[key]) for key in row if not str(key).startswith("_")}
    assertion_id = world._inner._store.assertion_id_for_tuple(
        relation,
        _typed(world, relation, values),
    )
    warrant = world.warrant_for_assertion(assertion_id)
    support = _support_from_warrant(world, warrant)
    return {
        "assertion_id": assertion_id,
        "relation": relation,
        "values": values,
        "referent_labels": {
            key: labels[value]
            for key, value in values.items()
            if value in labels
        },
        "support": support,
        "support_fingerprint": _fingerprint(support),
    }


def _support_from_warrant(world: ConstructionWorld, warrant: dict[str, Any]) -> dict[str, Any]:
    bases = []
    reconstructed = []
    seen: set[str] = set()
    for base in warrant["bases"]:
        detail = base.get("detail", base.get("detail_text", ""))
        bases.append({
            "kind": base["kind"],
            "reference": base["reference"],
            "detail": detail,
        })
        observations = detail.get("observations") if isinstance(detail, dict) else None
        if not isinstance(observations, list):
            continue
        for observation in observations:
            if not isinstance(observation, dict):
                continue
            key = json.dumps(observation, sort_keys=True, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            reconstructed.append(_reconstruct(world, observation))
    return {
        "origins": list(warrant["construction_origins"]),
        "bases": bases,
        "reconstructed": reconstructed,
    }


def _reconstruct(world: ConstructionWorld, observation: dict[str, Any]) -> dict[str, str]:
    text, status = reconstruct_governance_observation(world, observation)
    if status != "OK":
        text, status = reconstruct_program_observation(world, observation)
    return {
        "native_handle": str(observation.get("native_handle") or ""),
        "native_location": str(observation.get("native_location") or ""),
        "text": text,
        "status": status,
    }


def _values_for_assertion(world: ConstructionWorld, relation: str, assertion_id: str) -> dict[str, str] | None:
    store = world._inner._store
    try:
        rows = world.relation_rows(relation)
    except Exception:
        return None
    for row in rows:
        values = {str(key): str(row[key]) for key in row if not str(key).startswith("_")}
        try:
            found = store.assertion_id_for_tuple(relation, _typed(world, relation, values))
        except Exception:
            continue
        if found == assertion_id:
            return values
    return None


def _typed(world: ConstructionWorld, relation: str, values: dict[str, Any]) -> dict[str, Any]:
    schema = world.relation_schema(relation)
    kinds = {str(role["name"]): str(role["type"]) for role in schema["roles"]}
    typed: dict[str, Any] = {}
    for key, value in values.items():
        kind = kinds[key]
        if kind == "BOOLEAN":
            if value in (True, False, 0, 1):
                typed[key] = value
            elif str(value) in {"1", "True", "true"}:
                typed[key] = 1
            else:
                typed[key] = 0
        elif kind == "INTEGER":
            typed[key] = int(value)
        elif kind == "REAL":
            typed[key] = float(value)
        else:
            typed[key] = str(value)
    return typed


def _fingerprint(support: dict[str, Any]) -> str:
    payload = json.dumps(support, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
