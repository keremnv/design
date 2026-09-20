"""Authority change-impact sidecar.

Compares ProgramDelta against persisted relevance-scope clauses. It does not
assess warrant validity or emit compliance verdicts.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ontology_author.program_spine.comparison import SpineComparisonResult, load_comparison
from ontology_author.world.runtime.world import ConstructionWorld, world_id_of

from .evaluate import (
    canonical_json,
    capability_for_relation,
    continuation_view,
    copy_json,
    descendants,
    digest,
    entity_kind,
    find_relation_bucket,
    identity_surface_event,
    manifestation_property_hit,
    program_entities,
    relation_hits_for_identity,
    relation_rows_with_ids,
    relation_status,
    snapshot_id,
    world_dir,
)
from .maintenance import GovernanceError, assess_attachment_maintenance
from .relevance import (
    clause_key,
    default_relevance_clauses,
    load_scope_rows,
    normalize_clause,
)


IMPACT_SCHEMA = "authority_impact/v0"
IMPACT_MECHANISM_ID = "ontology_author.authority.impact"
IMPACT_MECHANISM_VERSION = "v0"


def _open(value: ConstructionWorld | Path | str) -> tuple[ConstructionWorld, bool]:
    if isinstance(value, ConstructionWorld):
        return value, False
    return ConstructionWorld.open(value, read_only=True), True


def _comparison(value: SpineComparisonResult | Path | str) -> SpineComparisonResult:
    if isinstance(value, SpineComparisonResult):
        return value
    return load_comparison(value)


def _rank(status: str) -> int:
    return {"UNAFFECTED": 0, "AFFECTED": 1, "UNKNOWN": 2, "NOT_COMPARABLE": 3}.get(status, 0)


def _merge(current: str, incoming: str) -> str:
    return incoming if _rank(incoming) > _rank(current) else current


def _evaluate_clause(
    *,
    clause: Mapping[str, Any],
    attached: str,
    view,
    comparison: SpineComparisonResult,
    old_world: ConstructionWorld,
) -> tuple[str, list[dict[str, Any]], list[str]]:
    kind = str(clause.get("clause_kind") or "")
    limitations: list[str] = []
    if kind == "ATTACHED_IDENTITY":
        status, refs = identity_surface_event(comparison, attached)
        return status, refs, limitations
    if kind == "EXPLICIT_IDENTITY":
        target = str(clause.get("identity_id") or attached)
        status, refs = identity_surface_event(comparison, target)
        target_view = continuation_view(comparison, target)
        properties = [str(item) for item in clause.get("manifestation_properties") or []]
        if properties:
            if target_view.continuation != "UNIQUE":
                extra = "NOT_COMPARABLE" if target_view.continuation == "NOT_COMPARABLE" else "UNKNOWN"
                status = _merge(status, extra)
            else:
                changed = [item for item in properties if manifestation_property_hit(item, target_view.changes)]
                if changed:
                    status = _merge(status, "AFFECTED")
                    refs.append({"kind": "explicit_manifestation", "old_entity": target, "properties": changed})
        if clause.get("relation_name"):
            rel_status, rel_refs, rel_limits = _evaluate_clause(
                clause={
                    **clause,
                    "clause_kind": "ENDPOINT_RELATION",
                    "identity_id": target,
                },
                attached=target,
                view=target_view,
                comparison=comparison,
                old_world=old_world,
            )
            status = _merge(status, rel_status)
            refs.extend(rel_refs)
            limitations.extend(rel_limits)
        return status, refs, limitations
    if kind == "IDENTITY_MANIFESTATION":
        if view.continuation != "UNIQUE":
            status = "NOT_COMPARABLE" if view.continuation == "NOT_COMPARABLE" else "UNKNOWN"
            return status, [{"kind": "manifestation", "old_entity": attached, "reason": "no unique continuation"}], list(view.limitations)
        changes = dict(view.changes)
        properties = [str(item) for item in clause.get("manifestation_properties") or []]
        changed = [item for item in properties if manifestation_property_hit(item, changes)]
        if changed:
            delta_row = next(
                (
                    copy_json(item)
                    for item in comparison.delta.manifestations
                    if str(item.get("old_entity") or "") == attached
                ),
                {
                    "old_entity": attached,
                    "new_entity": view.candidates[0] if view.candidates else "",
                    "changes": changes,
                },
            )
            return "AFFECTED", [{"kind": "manifestation", "properties": changed, "row": delta_row}], []
        return "UNAFFECTED", [], []
    if kind == "ENDPOINT_RELATION":
        relation = str(clause.get("relation_name") or "")
        status = relation_status(comparison.delta, relation)
        if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
            return "NOT_COMPARABLE", [{"kind": "relation", "relation": relation, "bucket": "NOT_COMPARABLE"}], [
                f"{capability_for_relation(relation)} cannot be compared"
            ]
        recorded = dict(clause.get("relation_tuple") or {})
        identities = {attached}
        role = str(clause.get("endpoint_role") or "")
        if view.continuation == "UNIQUE":
            identities.update(view.candidates)
        elif view.continuation == "AMBIGUOUS":
            identities.update(view.candidates)
        elif view.continuation == "NOT_COMPARABLE":
            return "NOT_COMPARABLE", [{"kind": "relation", "relation": relation}], list(view.limitations)
        if recorded:
            bucket, row = find_relation_bucket(comparison.delta, relation, recorded)
            if bucket == "NOT_COMPARABLE":
                return "NOT_COMPARABLE", [{"kind": "relation", "relation": relation, "bucket": bucket, "row": row}], []
            if bucket in {"retargeted", "removed", "added"}:
                return "AFFECTED", [{"kind": "relation", "relation": relation, "bucket": bucket, "row": row}], []
            if bucket == "unresolved":
                return "UNKNOWN", [{"kind": "relation", "relation": relation, "bucket": bucket, "row": row}], []
            if bucket == "preserved":
                return "UNAFFECTED", [], []
            return "UNKNOWN", [{"kind": "relation", "relation": relation, "bucket": "absent"}], [
                "persisted relation tuple could not be matched in ProgramDelta"
            ]
        rel_hits = relation_hits_for_identity(comparison.delta, relation, identities, role=role)
        if any(item.get("bucket") == "NOT_COMPARABLE" for item in rel_hits):
            return "NOT_COMPARABLE", rel_hits, [f"{capability_for_relation(relation)} cannot be compared"]
        if any(item.get("bucket") == "unresolved" for item in rel_hits):
            return "UNKNOWN", rel_hits, []
        if any(item.get("bucket") in {"added", "removed", "retargeted"} for item in rel_hits):
            return "AFFECTED", rel_hits, []
        if view.continuation in {"AMBIGUOUS", "NONE"}:
            return "UNKNOWN", [{"kind": "relation", "relation": relation, "reason": "continuation prevents endpoint mapping"}], []
        return "UNAFFECTED", [], []
    if kind == "STRUCTURAL_SCOPE":
        root = str(clause.get("identity_id") or attached)
        kids = descendants(old_world, root)
        if not kids:
            return "UNAFFECTED", [], []
        relation = str(clause.get("relation_name") or "")
        if relation:
            status = relation_status(comparison.delta, relation)
            if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
                return "NOT_COMPARABLE", [{"kind": "structural_scope", "relation": relation}], [
                    f"{capability_for_relation(relation)} cannot be compared"
                ]
        worst = "UNAFFECTED"
        refs: list[dict[str, Any]] = []
        for child in kids:
            child_status, child_refs = identity_surface_event(comparison, child)
            worst = _merge(worst, child_status)
            refs.extend(child_refs)
            child_view = continuation_view(comparison, child)
            if child_view.continuation == "UNIQUE":
                for prop in clause.get("manifestation_properties") or ["signature", "source_manifestation"]:
                    if manifestation_property_hit(str(prop), child_view.changes):
                        worst = _merge(worst, "AFFECTED")
                        refs.append({"kind": "structural_manifestation", "old_entity": child, "property": prop})
            elif child_view.continuation == "NOT_COMPARABLE":
                worst = _merge(worst, "NOT_COMPARABLE")
            elif child_view.continuation == "AMBIGUOUS":
                worst = _merge(worst, "UNKNOWN")
            elif child_view.continuation == "NONE":
                worst = _merge(worst, "AFFECTED")
            if relation:
                ids = {child, *child_view.candidates}
                rel_hits = relation_hits_for_identity(comparison.delta, relation, ids)
                if any(item.get("bucket") == "NOT_COMPARABLE" for item in rel_hits):
                    worst = _merge(worst, "NOT_COMPARABLE")
                elif any(item.get("bucket") == "unresolved" for item in rel_hits):
                    worst = _merge(worst, "UNKNOWN")
                elif any(item.get("bucket") in {"added", "removed", "retargeted"} for item in rel_hits):
                    worst = _merge(worst, "AFFECTED")
                refs.extend(rel_hits)
        return worst, refs, limitations
    return "UNKNOWN", [{"kind": "clause", "reason": f"unsupported clause_kind {kind}"}], ["unsupported clause"]


def _clauses_for_warrant(
    old_world: ConstructionWorld,
    warrant: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], str, list[str]]:
    warrant_id = str(warrant.get("_assertion_id") or "")
    entity = str(warrant.get("program_entity") or "")
    rows = load_scope_rows(old_world, warrant_id)
    if rows:
        return rows, "PERSISTED", []
    kind = entity_kind(old_world, entity)
    inferred = [
        normalize_clause(clause, program_entity=entity, origin="DEFAULT_KIND_RULE")
        for clause in default_relevance_clauses(kind, entity)
    ]
    return inferred, "DEFAULT_KIND_RULE", [
        f"warrant {warrant_id} had no persisted relevance scope; applied documented kind default"
    ]


def assess_authority_change_impact(
    old_world: ConstructionWorld | Path | str,
    new_world: ConstructionWorld | Path | str,
    comparison: SpineComparisonResult | Path | str,
    *,
    maintenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return ``authority.impact.json`` payload. Does not mutate Worlds."""

    old, old_owned = _open(old_world)
    new, new_owned = _open(new_world)
    try:
        result = _comparison(comparison)
        old_snapshot = str(result.receipt.snapshots.get("old", {}).get("id") or result.delta.old_snapshot)
        new_snapshot = str(result.receipt.snapshots.get("new", {}).get("id") or result.delta.new_snapshot)
        if snapshot_id(old) and snapshot_id(old) != old_snapshot:
            raise GovernanceError("comparison old snapshot does not match the old World")
        if snapshot_id(new) and snapshot_id(new) != new_snapshot:
            raise GovernanceError("comparison new snapshot does not match the new World")
        maintenance_payload = maintenance or assess_attachment_maintenance(old, new, result)
        by_warrant = {
            str(item["warrant_assertion_id"]): item
            for item in maintenance_payload.get("assessments") or []
        }
        new_ids = program_entities(new)
        impacts: list[dict[str, Any]] = []
        omissions: list[str] = []
        for warrant in sorted(
            relation_rows_with_ids(old, "authority_attachment_warrant"),
            key=lambda row: (str(row.get("assertion_id") or ""), str(row.get("program_entity") or "")),
        ):
            if str(warrant.get("program_snapshot_id") or "") not in {old_snapshot, snapshot_id(old)}:
                continue
            entity = str(warrant["program_entity"])
            warrant_id = str(warrant.get("_assertion_id") or "")
            assessment = by_warrant.get(warrant_id) or {}
            view = continuation_view(result, entity)
            illegal = [item for item in view.candidates if item not in new_ids]
            if illegal:
                raise GovernanceError(
                    "candidate continuation is not in the new program snapshot: " + ", ".join(illegal)
                )
            clauses, scope_source, clause_omissions = _clauses_for_warrant(old, warrant)
            omissions.extend(clause_omissions)
            worst = "UNAFFECTED"
            intersecting: list[dict[str, Any]] = []
            limitations: list[str] = []
            used = []
            for clause in sorted(clauses, key=clause_key):
                status, refs, limits = _evaluate_clause(
                    clause=clause,
                    attached=entity,
                    view=view,
                    comparison=result,
                    old_world=old,
                )
                used.append({**clause, "impact": status})
                worst = _merge(worst, status)
                intersecting.extend(refs)
                limitations.extend(limits)
            impact_id = "impact:" + digest(
                {
                    "comparison_id": result.receipt.comparison_id,
                    "warrant_assertion_id": warrant_id,
                    "attachment_assertion_id": warrant.get("assertion_id"),
                }
            )
            impacts.append(
                {
                    "impact_id": impact_id,
                    "attachment_assertion_id": str(warrant["assertion_id"]),
                    "warrant_assertion_id": warrant_id,
                    "old_program_entity": entity,
                    "candidate_new_manifestations": list(view.candidates),
                    "maintenance_assessment_id": assessment.get("assessment_id", ""),
                    "scope_source": scope_source,
                    "scope_clauses": used,
                    "impact": worst,
                    "intersecting_deltas": intersecting,
                    "limitations": list(dict.fromkeys(limitations)),
                }
            )
        payload = {
            "impact_id": "impact:" + digest(
                {
                    "comparison_id": result.receipt.comparison_id,
                    "old_snapshot": old_snapshot,
                    "new_snapshot": new_snapshot,
                    "impacts": impacts,
                }
            ),
            "contract": IMPACT_SCHEMA,
            "mechanism": {"id": IMPACT_MECHANISM_ID, "version": IMPACT_MECHANISM_VERSION},
            "old_world_id": world_id_of(old.path),
            "new_world_id": world_id_of(new.path),
            "old_snapshot": old_snapshot,
            "new_snapshot": new_snapshot,
            "comparison_id": result.receipt.comparison_id,
            "old_world": str(world_dir(old)),
            "new_world": str(world_dir(new)),
            "maintenance_id": maintenance_payload.get("maintenance_id", ""),
            "impacts": impacts,
            "known_omissions": omissions,
        }
        return json.loads(canonical_json(payload))
    finally:
        if old_owned:
            old.close()
        if new_owned:
            new.close()


def write_impact(payload: Mapping[str, Any], output_dir: Path | str) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "authority.impact.json"
    path.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
