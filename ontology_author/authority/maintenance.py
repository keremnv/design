"""Attachment-maintenance assessment sidecar.

Evaluates recorded warrant dependencies against ProgramDelta. It does not
select cases, copy attachments, or emit compliance verdicts.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ontology_author.program_spine.comparison import SpineComparisonResult, load_comparison
from ontology_author.world.runtime.world import ConstructionWorld, world_id_of

from .evaluate import (
    canonical_json,
    continuation_view,
    copy_json,
    digest,
    find_relation_bucket,
    parse_json_list,
    program_entities,
    relation_rows_with_ids,
    relation_status,
    resolution_row,
    snapshot_id,
    structural_parents,
    world_dir,
)


MAINTENANCE_SCHEMA = "authority_maintenance/v0"
MAINTENANCE_MECHANISM_ID = "ontology_author.authority.maintenance"
MAINTENANCE_MECHANISM_VERSION = "v0"
MAINTENANCE_RECEIPT_VERSION = "authority_maintenance_receipt/v1"
PERSISTENCE_IMPLICATION = "NO_RENEWAL"


class GovernanceError(ValueError):
    """Maintenance, impact, or case assembly could not complete honestly."""


def _open(value: ConstructionWorld | Path | str) -> tuple[ConstructionWorld, bool]:
    if isinstance(value, ConstructionWorld):
        return value, False
    return ConstructionWorld.open(value, read_only=True), True


def _comparison(value: SpineComparisonResult | Path | str) -> SpineComparisonResult:
    if isinstance(value, SpineComparisonResult):
        return value
    return load_comparison(value)


def _claim_for_assertion(world: ConstructionWorld, assertion_id: str) -> dict[str, Any]:
    for row in world.relation_rows("authority_claim"):
        if str(row["assertion_id"]) == assertion_id:
            return dict(row)
    return {}


def _grounds_summary(changes: Sequence[str]) -> str:
    values = set(changes)
    if "NOT_COMPARABLE" in values:
        return "GROUNDS_INCOMPARABLE"
    if "UNKNOWN" in values:
        return "GROUNDS_UNKNOWN"
    if "LOST" in values:
        return "GROUNDS_LOST"
    if "CHANGED" in values:
        return "GROUNDS_CHANGED"
    return "GROUNDS_PRESERVED"


def _maintenance_action(continuation: str, correspondence_continuity: str, changes: Sequence[str]) -> str:
    values = set(changes)
    if (
        continuation == "NOT_COMPARABLE"
        or "NOT_COMPARABLE" in values
        or correspondence_continuity == "UNRESOLVED"
    ):
        return "CANNOT_ASSESS"
    if continuation in {"AMBIGUOUS", "NONE"} or values & {"CHANGED", "LOST", "UNKNOWN"}:
        return "RERESOLVE"
    return "HOLD"


def _entity_identity_change(view) -> tuple[str, list[dict[str, Any]]]:
    if view.continuation == "UNIQUE":
        return "PRESERVED", [
            {
                "bucket": "continued",
                "old_entity": view.claim.old_entity if view.claim else "",
                "new_entity": view.candidates[0] if view.candidates else "",
            }
        ]
    if view.continuation == "AMBIGUOUS":
        return "UNKNOWN", [{"bucket": "ambiguous", "candidates": list(view.candidates)}]
    if view.continuation == "NOT_COMPARABLE":
        return "NOT_COMPARABLE", [{"bucket": "unresolved"}]
    return "LOST", [{"bucket": "removed"}]


def _structural_change(
    *,
    listed: Sequence[str],
    attached: str,
    view,
    new_world: ConstructionWorld,
    comparison: SpineComparisonResult,
) -> tuple[str, list[dict[str, Any]]]:
    if not listed:
        return "PRESERVED", []
    if view.continuation == "NOT_COMPARABLE":
        return "NOT_COMPARABLE", [{"reason": "attached identity is not comparable"}]
    if view.continuation == "AMBIGUOUS":
        return "UNKNOWN", [{"reason": "attached identity has ambiguous continuation"}]
    if view.continuation == "NONE":
        return "LOST", [{"reason": "attached identity has no continuation"}]
    candidate = view.candidates[0]
    parents = structural_parents(new_world)
    chain = [candidate]
    current = candidate
    seen = {candidate}
    while current in parents and parents[current] not in seen:
        current = parents[current]
        chain.append(current)
        seen.add(current)
    new_ancestors = set(chain)
    worst = "PRESERVED"
    evidence: list[dict[str, Any]] = []
    rank = {"PRESERVED": 0, "CHANGED": 1, "LOST": 2, "UNKNOWN": 3, "NOT_COMPARABLE": 4}
    for old_id in listed:
        if old_id == attached:
            continue
        other = continuation_view(comparison, old_id)
        if other.continuation == "NOT_COMPARABLE":
            worst = "NOT_COMPARABLE"
            evidence.append({"old_entity": old_id, "bucket": "unresolved"})
            continue
        if other.continuation == "AMBIGUOUS":
            if rank["UNKNOWN"] > rank[worst]:
                worst = "UNKNOWN"
            evidence.append({"old_entity": old_id, "bucket": "ambiguous", "candidates": list(other.candidates)})
            continue
        if other.continuation == "NONE":
            if rank["LOST"] > rank[worst]:
                worst = "LOST"
            evidence.append({"old_entity": old_id, "bucket": "removed"})
            continue
        new_id = other.candidates[0]
        if new_id not in new_ancestors:
            if rank["CHANGED"] > rank[worst]:
                worst = "CHANGED"
            evidence.append({"old_entity": old_id, "new_entity": new_id, "bucket": "owner_not_enclosing"})
        else:
            evidence.append({"old_entity": old_id, "new_entity": new_id, "bucket": "preserved"})
    return worst, evidence


def _relation_change(
    *,
    recorded: Mapping[str, Any],
    comparison: SpineComparisonResult,
    old_world: ConstructionWorld,
) -> tuple[str, list[dict[str, Any]]]:
    relation = str(recorded.get("relation") or "")
    if not relation:
        return "UNKNOWN", [{"reason": "justifying relation omitted a relation name"}]
    status = relation_status(comparison.delta, relation)
    if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
        return "NOT_COMPARABLE", [{"relation": relation, "bucket": "NOT_COMPARABLE", "status": status}]
    bucket, row = find_relation_bucket(comparison.delta, relation, recorded)
    if bucket == "preserved":
        return "PRESERVED", [{"relation": relation, "bucket": "preserved", "row": row}]
    if bucket == "retargeted":
        return "CHANGED", [{"relation": relation, "bucket": "retargeted", "row": row}]
    if bucket == "removed":
        return "LOST", [{"relation": relation, "bucket": "removed", "row": row}]
    if bucket == "unresolved":
        return "UNKNOWN", [{"relation": relation, "bucket": "unresolved", "row": row}]
    if bucket == "NOT_COMPARABLE":
        return "NOT_COMPARABLE", [{"relation": relation, "bucket": "NOT_COMPARABLE", "row": row}]
    present = False
    try:
        for item in old_world.relation_rows(relation):
            if all(
                str(item.get(key) or "") == str(value)
                for key, value in recorded.items()
                if key != "relation"
            ):
                present = True
                break
    except Exception:
        present = False
    if not present:
        return "UNKNOWN", [{
            "relation": relation,
            "bucket": "absent",
            "reason": "warrant tuple is not in ProgramDelta or the old spine",
        }]
    return "UNKNOWN", [{
        "relation": relation,
        "bucket": "absent",
        "reason": "warrant tuple was not placed in a relation-delta bucket",
    }]


def _resolution_change(
    *,
    recorded: Mapping[str, Any],
    old_world: ConstructionWorld,
    new_world: ConstructionWorld,
    comparison: SpineComparisonResult,
) -> tuple[str, list[dict[str, Any]]]:
    subject = str(recorded.get("subject") or "")
    capability = str(recorded.get("capability") or "")
    if not subject or not capability:
        return "UNKNOWN", [{"reason": "resolution outcome omitted subject or capability"}]
    relation_name = "program_invokes" if capability.startswith("spine.calls") else ""
    if relation_name:
        status = relation_status(comparison.delta, relation_name)
        if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
            return "NOT_COMPARABLE", [{"capability": capability, "bucket": "NOT_COMPARABLE"}]
    subject_view = continuation_view(comparison, subject)
    if subject_view.continuation == "NOT_COMPARABLE":
        return "NOT_COMPARABLE", [{"subject": subject, "capability": capability}]
    if subject_view.continuation == "AMBIGUOUS":
        return "UNKNOWN", [{"subject": subject, "capability": capability, "candidates": list(subject_view.candidates)}]
    if subject_view.continuation == "NONE":
        return "LOST", [{"subject": subject, "capability": capability, "bucket": "removed"}]
    new_subject = subject_view.candidates[0]
    old_row = resolution_row(old_world, subject, capability)
    new_row = resolution_row(new_world, new_subject, capability)
    if old_row is None:
        return "UNKNOWN", [{"subject": subject, "capability": capability, "reason": "old resolution row missing"}]
    if new_row is None:
        return "LOST", [{"subject": subject, "new_subject": new_subject, "capability": capability}]
    old_status = str(old_row.get("status") or recorded.get("status") or "")
    new_status = str(new_row.get("status") or "")
    if old_status == new_status:
        return "PRESERVED", [{"subject": subject, "new_subject": new_subject, "capability": capability, "status": old_status}]
    return "CHANGED", [
        {
            "subject": subject,
            "new_subject": new_subject,
            "capability": capability,
            "old_status": old_status,
            "new_status": new_status,
        }
    ]


def assess_attachment_maintenance(
    old_world: ConstructionWorld | Path | str,
    new_world: ConstructionWorld | Path | str,
    comparison: SpineComparisonResult | Path | str,
) -> dict[str, Any]:
    """Return ``authority.maintenance.json`` payload. Does not mutate Worlds."""

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
        new_ids = program_entities(new)
        assessments: list[dict[str, Any]] = []
        omissions: list[str] = []
        for warrant in sorted(
            relation_rows_with_ids(old, "authority_attachment_warrant"),
            key=lambda row: (str(row.get("assertion_id") or ""), str(row.get("program_entity") or "")),
        ):
            if str(warrant.get("program_snapshot_id") or "") not in {old_snapshot, snapshot_id(old)}:
                omissions.append(
                    f"warrant {warrant.get('_assertion_id')} snapshot does not match the comparison old snapshot"
                )
                continue
            entity = str(warrant["program_entity"])
            claim = _claim_for_assertion(old, str(warrant["assertion_id"]))
            view = continuation_view(result, entity)
            illegal_candidates = [item for item in view.candidates if item not in new_ids]
            if illegal_candidates:
                raise GovernanceError(
                    "candidate continuation is not in the new program snapshot: " + ", ".join(illegal_candidates)
                )
            dependencies: list[dict[str, Any]] = []
            identity_change, identity_evidence = _entity_identity_change(view)
            dependencies.append(
                {
                    "kind": "entity_identity",
                    "recorded_fact": {"program_entity": entity},
                    "dependency_change": identity_change,
                    "delta_evidence": identity_evidence,
                }
            )
            structural = parse_json_list(warrant.get("structural_context"))
            structural_change, structural_evidence = _structural_change(
                listed=[str(item) for item in structural],
                attached=entity,
                view=view,
                new_world=new,
                comparison=result,
            )
            dependencies.append(
                {
                    "kind": "structural_context",
                    "recorded_fact": {"structural_context": structural},
                    "dependency_change": structural_change,
                    "delta_evidence": structural_evidence,
                }
            )
            for recorded in parse_json_list(warrant.get("justifying_program_relations")):
                if not isinstance(recorded, Mapping):
                    continue
                change, evidence = _relation_change(recorded=recorded, comparison=result, old_world=old)
                dependencies.append(
                    {
                        "kind": "program_relation",
                        "recorded_fact": copy_json(recorded),
                        "dependency_change": change,
                        "delta_evidence": evidence,
                    }
                )
            for recorded in parse_json_list(warrant.get("justifying_resolution_outcomes")):
                if not isinstance(recorded, Mapping):
                    continue
                change, evidence = _resolution_change(
                    recorded=recorded,
                    old_world=old,
                    new_world=new,
                    comparison=result,
                )
                dependencies.append(
                    {
                        "kind": "resolution_outcome",
                        "recorded_fact": copy_json(recorded),
                        "dependency_change": change,
                        "delta_evidence": evidence,
                    }
                )
            changes = [str(item["dependency_change"]) for item in dependencies]
            action = _maintenance_action(view.continuation, view.correspondence_continuity, changes)
            uncertainty: list[str] = []
            if view.correspondence_basis == "HEURISTIC":
                uncertainty.append("HEURISTIC correspondence is not attachment renewal")
            if view.continuation == "AMBIGUOUS":
                uncertainty.append("ambiguous continuation candidates were retained without selection")
            if "UNKNOWN" in changes:
                uncertainty.append("at least one warrant dependency is UNKNOWN")
            if "NOT_COMPARABLE" in changes:
                uncertainty.append("at least one warrant dependency is NOT_COMPARABLE")
            assessment_id = "maintenance:" + digest(
                {
                    "comparison_id": result.receipt.comparison_id,
                    "warrant_assertion_id": warrant.get("_assertion_id"),
                    "attachment_assertion_id": warrant.get("assertion_id"),
                    "program_entity": entity,
                }
            )
            assessments.append(
                {
                    "assessment_id": assessment_id,
                    "attachment_assertion_id": str(warrant["assertion_id"]),
                    "claim_kind": str(claim.get("claim_kind") or ""),
                    "relation_name": str(claim.get("relation_name") or ""),
                    "warrant_assertion_id": str(warrant.get("_assertion_id") or ""),
                    "old_program_entity": entity,
                    "candidate_new_manifestations": list(view.candidates),
                    "continuation": view.continuation,
                    "correspondence_continuity": view.correspondence_continuity,
                    "correspondence_basis": view.correspondence_basis,
                    "correspondence_outcome": view.outcome,
                    "dependencies_examined": dependencies,
                    "grounds_summary": _grounds_summary(changes),
                    "orphaned": view.continuation == "NONE",
                    "maintenance_action": action,
                    "persistence_implication": PERSISTENCE_IMPLICATION,
                    "known_uncertainty": uncertainty,
                    "limitations": list(view.limitations),
                }
            )
        payload = {
            "maintenance_id": "maintenance:" + digest(
                {
                    "comparison_id": result.receipt.comparison_id,
                    "old_snapshot": old_snapshot,
                    "new_snapshot": new_snapshot,
                    "assessments": assessments,
                }
            ),
            "contract": MAINTENANCE_SCHEMA,
            "mechanism": {
                "id": MAINTENANCE_MECHANISM_ID,
                "version": MAINTENANCE_MECHANISM_VERSION,
            },
            "receipt_version": MAINTENANCE_RECEIPT_VERSION,
            "old_world_id": world_id_of(old.path),
            "new_world_id": world_id_of(new.path),
            "old_snapshot": old_snapshot,
            "new_snapshot": new_snapshot,
            "comparison_id": result.receipt.comparison_id,
            "old_world": str(world_dir(old)),
            "new_world": str(world_dir(new)),
            "assessments": assessments,
            "known_omissions": omissions,
        }
        return json.loads(canonical_json(payload))
    finally:
        if old_owned:
            old.close()
        if new_owned:
            new.close()


def write_maintenance(payload: Mapping[str, Any], output_dir: Path | str) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "authority.maintenance.json"
    path.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
