"""Shared ProgramDelta / correspondence inspection for maintenance and impact."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ontology_author.program_spine.comparison import (
    COMPARABLE_RELATIONS,
    RELATION_CAPABILITIES,
    CorrespondenceClaim,
    ProgramDelta,
    SpineComparisonResult,
)
from ontology_author.world.runtime.world import ConstructionWorld


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()[:32]


def copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


def relation_rows_with_ids(world: ConstructionWorld, relation: str) -> list[dict[str, Any]]:
    """Like ``relation_rows`` but keep hidden ``_assertion_id``.

    Semantic SELECT strips underscore columns. Maintenance and relevance
    scope need the warrant assertion identity, so this uses ordinary SQL.
    """

    schema = world.relation_schema(relation)
    column_to_role = {role["column"]: role["name"] for role in schema["roles"]}
    physical = world.query(f'SELECT * FROM "{relation}"')
    rows = []
    for row in physical:
        mapped = {column_to_role.get(key, key): value for key, value in row.items()}
        rows.append(mapped)
    return rows


def snapshot_id(world: ConstructionWorld) -> str:
    rows = world.relation_rows("program_snapshot")
    if not rows:
        return ""
    snapshot_ref = str(rows[0]["snapshot"])
    assertion = world.query(
        "SELECT assertion_id FROM _world_assertions WHERE relation_name='program_snapshot'"
    )
    if assertion:
        extra = _grounding_extra(world, str(assertion[0]["assertion_id"]))
        return str(extra.get("snapshot_id") or snapshot_ref)
    return snapshot_ref


def _grounding_extra(world: ConstructionWorld, assertion_id: str) -> dict[str, Any]:
    warrant = world.warrant_for_assertion(assertion_id)
    for base in warrant.get("bases") or []:
        detail = base.get("detail")
        if isinstance(detail, dict) and isinstance(detail.get("extra"), dict):
            return dict(detail["extra"])
    return {}


def entity_kind(world: ConstructionWorld, entity: str) -> str:
    for row in world.relation_rows("program_entity_kind"):
        if str(row["entity"]) == entity:
            return str(row["kind"] or "")
    return ""


def entity_label(world: ConstructionWorld, entity: str) -> str:
    rows = world.query("SELECT label FROM _world_referents WHERE id=?", (entity,))
    return str(rows[0]["label"]) if rows else ""


def structural_parents(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["child"]): str(row["parent"])
        for row in world.relation_rows("structural_context")
    }


def structural_children(world: ConstructionWorld) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    for row in world.relation_rows("structural_context"):
        children.setdefault(str(row["parent"]), []).append(str(row["child"]))
    return children


def ancestor_chain(world: ConstructionWorld, entity: str) -> list[str]:
    parents = structural_parents(world)
    chain = [entity]
    current = entity
    seen = {entity}
    while current in parents and parents[current] not in seen:
        current = parents[current]
        chain.append(current)
        seen.add(current)
    chain.reverse()
    return chain


def descendants(world: ConstructionWorld, root: str) -> list[str]:
    children = structural_children(world)
    output: list[str] = []
    stack = list(children.get(root, []))
    seen = {root}
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        output.append(node)
        stack.extend(children.get(node, []))
    return sorted(output)


def parse_json_list(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return list(raw)
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return list(value) if isinstance(value, list) else []


def parse_json_object(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


@dataclass(frozen=True)
class ContinuationView:
    continuation: str
    candidates: tuple[str, ...]
    correspondence_continuity: str
    correspondence_basis: str
    outcome: str
    changes: Mapping[str, str]
    limitations: tuple[str, ...]
    claim: CorrespondenceClaim | None


def claims_for(comparison: SpineComparisonResult, old_entity: str) -> tuple[CorrespondenceClaim, ...]:
    return tuple(item for item in comparison.correspondences if item.old_entity == old_entity)


def continuation_view(comparison: SpineComparisonResult, old_entity: str) -> ContinuationView:
    claims = claims_for(comparison, old_entity)
    identity = comparison.delta.identity
    ambiguous = [
        item for item in identity.get("ambiguous") or []
        if str(item.get("old_entity") or "") == old_entity
    ]
    unresolved = [
        item for item in identity.get("unresolved") or []
        if str(item.get("old_entity") or "") == old_entity
    ]
    universe = str(identity.get("universe_basis") or "")
    incomplete = "incomplete" in universe or "not-comparable" in universe
    if any(item.continuity == "AMBIGUOUS" for item in claims) or ambiguous:
        candidates: list[str] = []
        for claim in claims:
            if claim.candidate_entities:
                candidates.extend(str(item) for item in claim.candidate_entities)
        for item in ambiguous:
            candidates.extend(str(value) for value in item.get("candidate_entities") or [])
        ordered = tuple(dict.fromkeys(candidates))
        claim = next((item for item in claims if item.continuity == "AMBIGUOUS"), claims[0] if claims else None)
        return ContinuationView(
            continuation="AMBIGUOUS",
            candidates=ordered,
            correspondence_continuity="AMBIGUOUS",
            correspondence_basis=claim.basis_class if claim else "HEURISTIC",
            outcome=claim.outcome if claim else "AMBIGUOUS",
            changes=dict(claim.changes) if claim else {},
            limitations=tuple(claim.limitations) if claim else ("ambiguous continuation candidates",),
            claim=claim,
        )
    continued = [item for item in claims if item.continuity == "CONTINUED" and item.new_entity]
    if len(continued) == 1:
        claim = continued[0]
        return ContinuationView(
            continuation="UNIQUE",
            candidates=(str(claim.new_entity),),
            correspondence_continuity=claim.continuity,
            correspondence_basis=claim.basis_class,
            outcome=claim.outcome,
            changes=dict(claim.changes),
            limitations=tuple(claim.limitations),
            claim=claim,
        )
    if any(item.continuity == "UNRESOLVED" for item in claims) or unresolved or incomplete:
        claim = next((item for item in claims if item.continuity == "UNRESOLVED"), claims[0] if claims else None)
        return ContinuationView(
            continuation="NOT_COMPARABLE",
            candidates=(),
            correspondence_continuity=claim.continuity if claim else "UNRESOLVED",
            correspondence_basis=claim.basis_class if claim else "ABSENT",
            outcome=claim.outcome if claim else "UNRESOLVED",
            changes=dict(claim.changes) if claim else {},
            limitations=tuple(claim.limitations) if claim else ("identity correspondence is unresolved",),
            claim=claim,
        )
    removed = old_entity in set(identity.get("removed") or [])
    no_match = any(item.continuity == "NO_MATCH" for item in claims) or removed or not claims
    claim = next((item for item in claims if item.continuity == "NO_MATCH"), claims[0] if claims else None)
    return ContinuationView(
        continuation="NONE",
        candidates=(),
        correspondence_continuity=claim.continuity if claim else ("NO_MATCH" if no_match else "ABSENT"),
        correspondence_basis=claim.basis_class if claim else "ABSENT",
        outcome=claim.outcome if claim else "DELETED",
        changes=dict(claim.changes) if claim else {},
        limitations=tuple(claim.limitations) if claim else (),
        claim=claim,
    )


def relation_payload(delta: ProgramDelta, relation: str) -> dict[str, Any]:
    payload = delta.relations.get(relation) or {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def relation_status(delta: ProgramDelta, relation: str) -> str:
    return str(relation_payload(delta, relation).get("status") or "")


def old_row_roles(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in row.items()
        if key not in {"snapshot"} and value is not None and not str(key).startswith("_")
    }


def recorded_tuple_matches(recorded: Mapping[str, Any], old_row: Mapping[str, Any]) -> bool:
    for key, value in recorded.items():
        if key == "relation":
            continue
        if str(old_row.get(key) or "") != str(value):
            return False
    return True


def find_relation_bucket(
    delta: ProgramDelta,
    relation: str,
    recorded: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any] | None]:
    payload = relation_payload(delta, relation)
    status = str(payload.get("status") or "")
    if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
        return "NOT_COMPARABLE", {"status": status, "limitations": list(payload.get("limitations") or [])}
    for bucket in ("preserved", "retargeted", "removed", "unresolved"):
        for item in payload.get(bucket) or []:
            if not isinstance(item, Mapping):
                continue
            old_row = item.get("old")
            if isinstance(old_row, Mapping) and recorded_tuple_matches(recorded, old_row):
                return bucket, copy_json(item)
    return "", None


def tuple_involves(row: Mapping[str, Any], identities: set[str], *, role: str = "") -> bool:
    if role:
        return str(row.get(role) or "") in identities
    return any(str(value) in identities for value in row.values() if isinstance(value, str))


def relation_hits_for_identity(
    delta: ProgramDelta,
    relation: str,
    identities: set[str],
    *,
    role: str = "",
) -> list[dict[str, Any]]:
    payload = relation_payload(delta, relation)
    status = str(payload.get("status") or "")
    if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
        return [{"bucket": "NOT_COMPARABLE", "status": status, "limitations": list(payload.get("limitations") or [])}]
    hits: list[dict[str, Any]] = []
    for bucket in ("added", "removed", "retargeted", "unresolved"):
        for item in payload.get(bucket) or []:
            if not isinstance(item, Mapping):
                continue
            old_row = item.get("old") if isinstance(item.get("old"), Mapping) else {}
            new_row = item.get("new") if isinstance(item.get("new"), Mapping) else {}
            if tuple_involves(old_row, identities, role=role) or tuple_involves(new_row, identities, role=role):
                hits.append({"bucket": bucket, "row": copy_json(item)})
    return hits


def manifestation_property_hit(property_name: str, changes: Mapping[str, str]) -> bool:
    """True when a listed manifestation property changed in a selection-relevant way.

    Name-only and location-only moves are not hits unless those properties are
    themselves listed. Default scopes list ``signature`` and
    ``source_manifestation``. Digest-only file-hash movement (location
    preserved) is treated as a neighboring-edit, not an implementation change
    of this identity.
    """

    if changes.get(property_name) != "CHANGED":
        return False
    if property_name in {"name", "source_location", "signature", "boundary", "structural_context", "identity_kind"}:
        return True
    if property_name != "source_manifestation":
        return False
    name = changes.get("name") == "CHANGED"
    location = changes.get("source_location") == "CHANGED"
    signature = changes.get("signature") == "CHANGED"
    if signature:
        return True
    if name and not location:
        return False
    if not location and not name:
        return False
    return True


def identity_surface_event(comparison: SpineComparisonResult, old_entity: str) -> tuple[str, list[dict[str, Any]]]:
    """Return impact status contribution and delta refs for ATTACHED_IDENTITY."""

    view = continuation_view(comparison, old_entity)
    identity = comparison.delta.identity
    refs: list[dict[str, Any]] = []
    if view.continuation == "AMBIGUOUS":
        refs.append({"kind": "identity", "bucket": "ambiguous", "old_entity": old_entity, "candidates": list(view.candidates)})
        return "AFFECTED", refs
    if view.continuation == "NOT_COMPARABLE":
        refs.append({"kind": "identity", "bucket": "unresolved", "old_entity": old_entity})
        return "NOT_COMPARABLE", refs
    if view.continuation == "NONE":
        refs.append({"kind": "identity", "bucket": "removed", "old_entity": old_entity})
        return "AFFECTED", refs
    splits = [item for item in identity.get("split") or [] if old_entity in set(item.get("old_entities") or [item.get("old_entity")])]
    merges = [item for item in identity.get("merged") or [] if old_entity in set(item.get("old_entities") or [])]
    if splits:
        refs.append({"kind": "identity", "bucket": "split", "row": copy_json(splits[0])})
        return "AFFECTED", refs
    if merges:
        refs.append({"kind": "identity", "bucket": "merged", "row": copy_json(merges[0])})
        return "AFFECTED", refs
    return "UNAFFECTED", refs


def changed_program_identities(delta: ProgramDelta, *, kinds: Mapping[str, str] | None = None) -> set[str]:
    changed: set[str] = set()
    identity = delta.identity
    changed.update(str(item) for item in identity.get("removed") or [])
    for item in identity.get("ambiguous") or []:
        if item.get("old_entity"):
            changed.add(str(item["old_entity"]))
    for item in identity.get("unresolved") or []:
        if item.get("old_entity"):
            changed.add(str(item["old_entity"]))
    for item in identity.get("split") or []:
        changed.update(str(value) for value in item.get("old_entities") or [])
        if item.get("old_entity"):
            changed.add(str(item["old_entity"]))
    for item in identity.get("merged") or []:
        changed.update(str(value) for value in item.get("old_entities") or [])
    for item in delta.manifestations:
        if item.get("old_entity") and any(status == "CHANGED" for status in (item.get("changes") or {}).values()):
            if manifestation_property_hit("signature", item.get("changes") or {}) or manifestation_property_hit(
                "source_manifestation", item.get("changes") or {}
            ) or manifestation_property_hit("boundary", item.get("changes") or {}) or manifestation_property_hit(
                "structural_context", item.get("changes") or {}
            ):
                changed.add(str(item["old_entity"]))
    for relation, payload in delta.relations.items():
        if relation not in COMPARABLE_RELATIONS:
            continue
        if payload.get("status") in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
            continue
        for bucket in ("added", "removed", "retargeted", "unresolved"):
            for item in payload.get(bucket) or []:
                if not isinstance(item, Mapping):
                    continue
                for side in ("old", "new"):
                    row = item.get(side)
                    if isinstance(row, Mapping):
                        changed.update(str(value) for value in row.values() if isinstance(value, str) and value)
    output = {item for item in changed if item}
    if kinds is None:
        return output
    attachable = {
        "call_site",
        "callable",
        "method",
        "module",
        "source_unit",
        "class",
        "interface",
        "type",
        "data",
    }
    return {item for item in output if kinds.get(item, "") in attachable or item not in kinds}


def capability_for_relation(relation: str) -> str:
    return RELATION_CAPABILITIES.get(relation, "")


def world_dir(world: ConstructionWorld) -> Any:
    return world.path.parent


def program_entities(world: ConstructionWorld) -> set[str]:
    return {str(row["entity"]) for row in world.relation_rows("program_entity")}


def resolution_row(world: ConstructionWorld, subject: str, capability: str) -> dict[str, Any] | None:
    for row in world.relation_rows("program_resolution"):
        if str(row.get("subject") or "") == subject and str(row.get("capability") or "") == capability:
            return dict(row)
    return None
