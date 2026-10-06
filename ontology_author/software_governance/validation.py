"""Representational checks for a Software Governance World.

These checks do not decide whether a governance proposition is true.
They also do not encode one profile's support class, endpoint class, or
source-byte rule as the definition of a binding.
"""

from __future__ import annotations

import re
from typing import Any

from ontology_author.evidence.program_source import reconstruct_program_observation
from ontology_author.software_governance.evidence import reconstruct_governance_observation
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.runtime.world import ConstructionWorld

CONTRACT_ID = "software_governance_construction/v0"
BINDINGS_CAPABILITY = "software_governance.bindings/v0"
NON_POSITIVE_RESOLUTIONS = frozenset({"AMBIGUOUS", "UNRESOLVED"})
FORBIDDEN_EXTRA = frozenset({"confidence", "score", "probability"})
_GAP_NAME = re.compile(r"^[a-z][a-z0-9_]*$")

_SEMANTIC_RELATIONS = (
    "governance_proposition",
    "governance_binding",
    "governance_candidate",
    "governance_question",
)
_COVERAGE_RELATIONS = (
    "governance_completeness",
    "governance_known_gap",
)
_RECEIPT_RELATIONS = (
    "software_subject",
    "software_manifestation",
)
_COVERAGE_ORIGINS = frozenset({
    ConstructionOrigin.MECHANICAL.value,
    ConstructionOrigin.SEMANTIC.value,
})


def validate_governance_world(world: ConstructionWorld) -> list[str]:
    errors: list[str] = []
    errors.extend(_schema_errors(world))
    if any(
        item.startswith("governance_binding")
        or item.startswith("governance_proposition")
        or item.startswith("governance_candidate")
        or item.startswith("governance_completeness")
        or item.startswith("governance_known_gap")
        or item.startswith("software_subject")
        or item.startswith("software_manifestation")
        for item in errors
    ):
        return errors
    errors.extend(_origin_errors(world))
    for row in world.relation_rows("governance_proposition"):
        if not str(row["statement"]).strip() or not str(row["domain_relation"]).strip():
            errors.append(f"proposition {row['proposition']} lacks statement or domain relation")
        errors.extend(_basis_errors(world, "governance_proposition", dict(row), correspondence=False))
    candidates = {
        (str(row["proposition"]), str(row["software_subject"]))
        for row in world.relation_rows("governance_candidate")
    }
    for row in world.relation_rows("governance_binding"):
        pair = (str(row["proposition"]), str(row["software_subject"]))
        if pair in candidates:
            errors.append(f"established binding {pair[0]} to {pair[1]} is also recorded as a candidate")
        errors.extend(_subject_errors(world, pair[1]))
        errors.extend(_basis_errors(world, "governance_binding", dict(row), correspondence=True))
    questions = {str(row["proposition"]) for row in world.relation_rows("governance_question")}
    for row in world.relation_rows("governance_question"):
        if str(row["state"]) != "UNRESOLVED" or not str(row["question"]).strip():
            errors.append(f"governance question for {row['proposition']} is not an explicit unresolved question")
    for row in world.relation_rows("governance_candidate"):
        proposition = str(row["proposition"])
        subject = str(row["software_subject"])
        if proposition not in questions:
            errors.append(f"candidate correspondence for {proposition} has no unresolved question")
        errors.extend(_subject_errors(world, subject))
        errors.extend(_basis_errors(world, "governance_candidate", dict(row), correspondence=True))
    errors.extend(_manifestation_errors(world))
    errors.extend(_completeness_errors(world))
    return errors


def _schema_errors(world: ConstructionWorld) -> list[str]:
    expected = {
        "governance_binding": {"proposition": "REFERENT", "software_subject": "REFERENT"},
        "governance_candidate": {"proposition": "REFERENT", "software_subject": "REFERENT"},
        "governance_proposition": {
            "proposition": "REFERENT",
            "statement": "TEXT",
            "domain_relation": "TEXT",
        },
        "governance_completeness": {
            "capability": "TEXT",
            "status": "TEXT",
            "universe": "REFERENT",
            "basis": "TEXT",
        },
        "governance_known_gap": {"capability": "TEXT", "gap": "TEXT"},
        "software_subject": {
            "subject": "REFERENT",
            "snapshot": "REFERENT",
            "kind": "TEXT",
            "capability": "TEXT",
            "version": "TEXT",
        },
        "software_manifestation": {
            "subject": "REFERENT",
            "scheme": "TEXT",
            "location": "TEXT",
            "capability": "TEXT",
        },
    }
    errors: list[str] = []
    for relation, roles in expected.items():
        actual = _roles(world, relation)
        if actual != roles:
            errors.append(f"{relation} schema is {actual}, expected {roles}")
    return errors


def _roles(world: ConstructionWorld, relation: str) -> dict[str, str] | None:
    try:
        schema = world.relation_schema(relation)
    except Exception:
        return None
    return {str(role["name"]): str(role["type"]) for role in schema["roles"]}


def _origin_errors(world: ConstructionWorld) -> list[str]:
    errors: list[str] = []
    for relation in _SEMANTIC_RELATIONS:
        errors.extend(_origin_mismatch(
            world,
            relation,
            expected=frozenset({ConstructionOrigin.SEMANTIC.value}),
            reason="semantic construction",
        ))
    for relation in _RECEIPT_RELATIONS:
        errors.extend(_origin_mismatch(
            world,
            relation,
            expected=frozenset({ConstructionOrigin.MECHANICAL.value}),
            reason="mechanical subject identification",
        ))
    for relation in _COVERAGE_RELATIONS:
        errors.extend(_origin_mismatch(
            world,
            relation,
            expected=_COVERAGE_ORIGINS,
            reason="construction coverage",
        ))
    return errors


def _origin_mismatch(
    world: ConstructionWorld,
    relation: str,
    *,
    expected: frozenset[str],
    reason: str,
) -> list[str]:
    if _roles(world, relation) is None:
        return []
    errors: list[str] = []
    for row in world.query(
        "SELECT assertion_id FROM _world_assertions WHERE relation_name = ? ORDER BY assertion_id",
        (relation,),
    ):
        assertion_id = str(row["assertion_id"])
        origins = world.origins_for_assertion(assertion_id)
        if not origins or any(origin not in expected for origin in origins):
            errors.append(
                f"{relation} {assertion_id} is {reason} recorded as {origins}"
            )
    return errors


def _subject_errors(world: ConstructionWorld, subject: str) -> list[str]:
    """One subject receipt: snapshot, kind, and producer capability/version.

    The receipt is producer-neutral. It does not read a program-spine table,
    and it does not require a source byte observation.
    """

    rows = [
        row for row in world.relation_rows("software_subject")
        if str(row["subject"]) == subject
    ]
    if len(rows) != 1:
        return [f"software subject {subject} has no single subject receipt"]
    row = rows[0]
    errors: list[str] = []
    if not str(row["snapshot"]).strip():
        errors.append(f"software subject {subject} has no snapshot")
    if not str(row["kind"]).strip():
        errors.append(f"software subject {subject} has no declared subject kind")
    if not str(row["capability"]).strip() or not str(row["version"]).strip():
        errors.append(f"software subject {subject} has no inspectable producer")
    return errors


def _basis_errors(
    world: ConstructionWorld,
    relation: str,
    values: dict[str, Any],
    *,
    correspondence: bool,
) -> list[str]:
    assertion_id = world._inner._store.assertion_id_for_tuple(relation, values)
    warrant = world.warrant_for_assertion(assertion_id)
    errors: list[str] = []
    saw_source = False
    saw_method = False
    broken_observations = 0
    extra: dict[str, Any] = {}
    for base in warrant["bases"]:
        detail = base.get("detail")
        if not isinstance(detail, dict):
            continue
        if str(detail.get("construction_method") or "").strip():
            saw_method = True
        if isinstance(detail.get("extra"), dict):
            extra = detail["extra"]
        for observation in detail.get("observations") or []:
            if not isinstance(observation, dict):
                broken_observations += 1
                continue
            required = (
                "provider",
                "native_handle",
                "source_revision",
                "native_location",
            )
            if not all(str(observation.get(key) or "").strip() for key in required):
                broken_observations += 1
                continue
            _text, status = reconstruct_governance_observation(world, observation)
            if status != "OK":
                _text, status = reconstruct_program_observation(world, observation)
            if status == "OK":
                saw_source = True
            else:
                broken_observations += 1
    label = str(values.get("proposition") or assertion_id)
    if not saw_source or not saw_method:
        errors.append(f"{relation} {label} lacks recoverable source grounding or a construction method")
    if broken_observations:
        errors.append(
            f"{relation} {label} has {broken_observations} unreconstructible recorded evidence observation(s)"
        )
    for key in FORBIDDEN_EXTRA:
        if key in extra:
            errors.append(f"{relation} {label} carries numeric confidence field {key}")
    if str(extra.get("contract") or "") != CONTRACT_ID:
        errors.append(f"{relation} {label} does not identify {CONTRACT_ID}")
    if not correspondence:
        return errors
    support = str(extra.get("relation_support") or "").strip()
    chosen = str(extra.get("endpoint_resolution") or "").strip()
    if not support:
        errors.append(f"{relation} {label} does not record relationship support")
    if not chosen:
        errors.append(f"{relation} {label} does not record endpoint resolution")
    elif relation == "governance_binding" and chosen in NON_POSITIVE_RESOLUTIONS:
        errors.append(
            f"{relation} {label} records non-positive endpoint resolution {chosen!r} as established"
        )
    elif relation == "governance_candidate" and chosen not in NON_POSITIVE_RESOLUTIONS:
        errors.append(
            f"{relation} {label} records endpoint resolution {chosen!r} on a candidate"
        )
    if not str(extra.get("software_evidence") or "").strip():
        errors.append(f"{relation} {label} does not record software-side evidence")
    return errors


def _manifestation_errors(world: ConstructionWorld) -> list[str]:
    errors: list[str] = []
    for row in world.relation_rows("software_manifestation"):
        subject = str(row["subject"])
        if not str(row["scheme"]).strip() or not str(row["location"]).strip():
            errors.append(f"software subject {subject} manifestation lacks a scheme or location")
        if not str(row["capability"]).strip():
            errors.append(f"software subject {subject} manifestation has no capability")
        errors.extend(_basis_errors(
            world,
            "software_manifestation",
            dict(row),
            correspondence=False,
        ))
    return errors


def _completeness_errors(world: ConstructionWorld) -> list[str]:
    errors: list[str] = []
    claims = list(world.relation_rows("governance_completeness"))
    capabilities = {str(row["capability"]) for row in claims}
    gaps: dict[str, list[str]] = {}
    for row in world.relation_rows("governance_known_gap"):
        capability = str(row["capability"])
        gap = str(row["gap"])
        gaps.setdefault(capability, []).append(gap)
        if capability not in capabilities:
            errors.append(f"known gap {gap!r} has no completeness claim for {capability}")
        if _GAP_NAME.fullmatch(gap) is None:
            errors.append(f"known gap {gap!r} is not a gap identifier")
    for row in claims:
        capability = str(row["capability"])
        status = str(row["status"])
        if not capability.strip() or not str(row["basis"]).strip():
            errors.append("governance completeness lacks a capability or basis")
        if status not in {"COMPLETE", "INCOMPLETE", "UNKNOWN"}:
            errors.append(f"governance completeness status {status!r} is not a scoped status")
        if status == "COMPLETE" and gaps.get(capability):
            errors.append(f"COMPLETE governance completeness for {capability} declares known gaps")
    return errors
