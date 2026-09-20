"""Deterministic GovernanceCase assembly from maintenance + impact + stored evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ontology_author.program_spine.comparison import (
    SpineComparisonResult,
    load_comparison,
)
from ontology_author.world.core.model import CompletenessStatus
from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld, world_id_of

from .schemas import ClaimKind, CompletenessScope, SourceStanding
from .evaluate import (
    ancestor_chain,
    canonical_json,
    changed_program_identities,
    continuation_view,
    copy_json,
    digest,
    entity_kind,
    entity_label,
    parse_json_list,
    relation_rows_with_ids,
    snapshot_id,
    world_dir,
)
from .impact import assess_authority_change_impact
from .maintenance import GovernanceError, assess_attachment_maintenance
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.evidence.program_source import program_source_observations, source_evidence_record
from .validation import observations_for_assertion

CASE_SCHEMA = "governance_case/v0"
CASE_MECHANISM_ID = "ontology_author.authority.case"
CASE_MECHANISM_VERSION = "v0"
CASE_RECEIPT_VERSION = "governance_case_receipt/v1"
# Keep these application relation names local to avoid importing the semantic
# constructor/provider package into authority case assembly.  The trusted
# PROGRAM_REALIZATION profile owns the same stable names.
PROGRAM_REALIZATION_RELATION = "semantic_program_realization"
PROGRAM_RELATIONSHIP_RELATION = "semantic_payment_access_path"
PROGRAM_INVARIANT_RELATION = "semantic_payment_provider_access_invariant"
SEMANTIC_WARRANT_RELATION = "semantic_commitment_warrant"
SEMANTIC_CONTEXT_INCLUSION_REASONS = {
    "SELECTED_ATTACHMENT_SEMANTIC_CONTEXT",
    "CHANGED_ENDPOINT_SEMANTIC_CONTEXT",
    "SELECTED_TRANSITION_FACT",
    "PERSISTED_SEMANTIC_COMMITMENT",
}
SEMANTIC_CONTEXT_STATUSES = {
    "POSITIVE",
    "ABSENCE_WITH_COMPLETE_COVERAGE",
    "ABSENCE_WITHOUT_COMPLETE_COVERAGE",
}
REASON_FOR_ACTION = {
    "RERESOLVE": "ATTACHMENT_GROUNDS_CHANGED",
    "CANNOT_ASSESS": "ATTACHMENT_GROUNDS_UNASSESSABLE",
}
REASON_FOR_IMPACT = {
    "AFFECTED": "GOVERNED_SURFACE_CHANGED",
    "UNKNOWN": "GOVERNED_SURFACE_UNKNOWN",
    "NOT_COMPARABLE": "GOVERNED_SURFACE_NOT_COMPARABLE",
}


def _open(value: ConstructionWorld | Path | str) -> tuple[ConstructionWorld, bool]:
    if isinstance(value, ConstructionWorld):
        return value, False
    return ConstructionWorld.open(value, read_only=True), True


def _comparison(value: SpineComparisonResult | Path | str) -> SpineComparisonResult:
    if isinstance(value, SpineComparisonResult):
        return value
    return load_comparison(value)


def selected_because(maintenance_action: str, impact: str) -> list[str]:
    reasons: list[str] = []
    if maintenance_action in REASON_FOR_ACTION:
        reasons.append(REASON_FOR_ACTION[maintenance_action])
    if impact in REASON_FOR_IMPACT:
        reasons.append(REASON_FOR_IMPACT[impact])
    return reasons


def should_select(maintenance_action: str, impact: str) -> bool:
    return bool(selected_because(maintenance_action, impact))


def _standing_map(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["source_handle"]): str(row["standing"])
        for row in world.relation_rows("authority_source")
    }


def _obs_key(observation: SourceObservation) -> tuple[str, str, str, str]:
    return (
        observation.provider,
        observation.native_handle,
        observation.source_revision,
        observation.native_location,
    )


def _reconstruct(
    observation: SourceObservation, sources: Mapping[str, MarkdownSource]
) -> tuple[str, str]:
    source = sources.get(observation.native_handle)
    if source is None:
        return "", "FAILED"
    try:
        return source.reconstruct(observation), "OK"
    except Exception:
        return "", "FAILED"


def _claim_tuple(
    world: ConstructionWorld, assertion_id: str, relation_name: str
) -> dict[str, Any]:
    try:
        rows = relation_rows_with_ids(world, relation_name)
    except Exception:
        return {}
    for row in rows:
        if str(row.get("_assertion_id") or "") == assertion_id:
            return {key: value for key, value in row.items() if key != "_assertion_id"}
    return {}


def _resolutions(world: ConstructionWorld, assertion_id: str) -> dict[str, str]:
    return {
        str(row["role"]): str(row["resolution"])
        for row in world.relation_rows("authority_endpoint_resolution")
        if str(row["assertion_id"]) == assertion_id
    }


def _semantics(world: ConstructionWorld, values: Mapping[str, Any]) -> list[str]:
    members = {str(row["entity"]) for row in world.relation_rows("semantic_entity")}
    return [str(value) for value in values.values() if str(value) in members]


def _store_observation(
    observation: SourceObservation,
    *,
    sources: Mapping[str, MarkdownSource],
    standing: Mapping[str, str],
    attachment_id: str,
    authority_obs: dict[tuple[str, str, str, str], dict[str, Any]],
    supporting_obs: dict[tuple[str, str, str, str], dict[str, Any]],
    reconstruction_failures: list[dict[str, Any]],
    known_omissions: list[str],
) -> str:
    key = _obs_key(observation)
    text, status = _reconstruct(observation, sources)
    record = {
        "observation_id": "obs:" + digest(list(key)),
        "provider": observation.provider,
        "handle": observation.native_handle,
        "revision": observation.source_revision,
        "native_location": observation.native_location,
        "standing": standing.get(observation.native_handle, ""),
        "reconstructed_text": text,
        "reconstruction": status,
        "selected_by": [attachment_id],
    }
    if status != "OK":
        reconstruction_failures.append(
            {
                "observation_id": record["observation_id"],
                "handle": observation.native_handle,
                "native_location": observation.native_location,
            }
        )
        known_omissions.append(
            f"exact evidence could not be reconstructed for {observation.native_handle} {observation.native_location}"
        )
    if record["standing"] == SourceStanding.AUTHORITATIVE.value:
        target = authority_obs
    else:
        target = supporting_obs
        known_omissions.append(
            f"non-authoritative source {observation.native_handle} was not presented as governing authority"
        )
    existing = target.get(key)
    if existing:
        existing["selected_by"] = sorted(set(existing["selected_by"]) | {attachment_id})
        return existing["observation_id"]
    target[key] = record
    return record["observation_id"]


def _related_claims(
    world: ConstructionWorld,
    *,
    attachment_id: str,
    claim_kind: str,
    observations: Sequence[SourceObservation],
    tuple_values: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if claim_kind != ClaimKind.SEMANTIC_PROGRAM.value:
        return []
    semantics = set(_semantics(world, tuple_values))
    left_keys = {_obs_key(item) for item in observations}
    related: list[dict[str, Any]] = []
    for row in world.relation_rows("authority_claim"):
        other_id = str(row["assertion_id"])
        if other_id == attachment_id:
            continue
        kind = str(row["claim_kind"])
        if kind not in {
            ClaimKind.SOURCE_SEMANTIC.value,
            ClaimKind.SOURCE_PROPOSITION.value,
        }:
            continue
        other_tuple = _claim_tuple(world, other_id, str(row["relation_name"]))
        if not semantics.intersection(_semantics(world, other_tuple)):
            continue
        other_obs = observations_for_assertion(world, other_id)
        if not left_keys.intersection(_obs_key(item) for item in other_obs):
            continue
        related.append(
            {"claim": dict(row), "tuple": other_tuple, "observations": other_obs}
        )
    return related


def _semantic_absence_status(world: ConstructionWorld) -> tuple[str, dict[str, Any]]:
    """Return only a completeness-backed absence when the World declares one.

    The v0 authority constructor has attachment/construction completeness, but
    no semantic-program-link completeness scope.  Keep this deliberately
    narrow: a generic COMPLETE claim must not become a closed-world semantic
    assumption merely because a link was not found.
    """

    for row in world.relation_rows("authority_completeness"):
        status = str(row.get("status") or "")
        scope_text = " ".join(
            str(row.get(key) or "") for key in ("scope", "universe", "basis")
        ).lower()
        if (
            status == CompletenessStatus.COMPLETE.value
            and "semantic" in scope_text
            and "program" in scope_text
        ):
            return "ABSENCE_WITH_COMPLETE_COVERAGE", {
                "scope": row.get("scope"),
                "universe": row.get("universe"),
                "status": status,
                "basis": row.get("basis"),
                "known_gaps": parse_json_list(row.get("known_gaps")),
            }
    return "ABSENCE_WITHOUT_COMPLETE_COVERAGE", {
        "scope": "SEMANTIC_PROGRAM_LINKS",
        "status": "NOT_DECLARED",
        "basis": "no semantic/program-link completeness claim was persisted",
        "known_gaps": [
            "semantic-program link absence is not licensed as a negative conclusion"
        ],
    }


def _attachment_universe(world: ConstructionWorld, purpose: str) -> set[str]:
    return {
        str(row["target"])
        for row in world.relation_rows("authority_attachment_scope")
        if not purpose or str(row.get("purpose") or "") == purpose
    }


def _attachment_completeness(world: ConstructionWorld) -> dict[str, Any]:
    for row in world.relation_rows("authority_completeness"):
        if str(row["scope"]) == CompletenessScope.ATTACHMENT.value:
            return dict(row)
    kernel = world.latest_completeness("authority_attachment_coverage") or {}
    return {
        "status": kernel.get("status", CompletenessStatus.INCOMPLETE.value),
        "basis": kernel.get("basis", ""),
        "known_gaps": json.dumps(list(kernel.get("known_gaps") or [])),
        "universe": kernel.get("universe_relation", "authority_attachment_scope"),
    }


def _uncertain_comparison(comparison: SpineComparisonResult) -> bool:
    basis = str(comparison.delta.identity.get("universe_basis") or "")
    if "incomplete" in basis or "not-comparable" in basis:
        return True
    return any(
        str((payload or {}).get("status") or "") == "NOT_COMPARABLE"
        for payload in comparison.delta.relations.values()
    )


def _case_result(
    *,
    selected: Sequence[Mapping[str, Any]],
    considered_impacts: Sequence[Mapping[str, Any]],
    considered_maintenance: Sequence[Mapping[str, Any]],
    changed: set[str],
    universe: set[str],
    completeness: Mapping[str, Any],
    comparison: SpineComparisonResult,
) -> str:
    if selected:
        return "SELECTED"
    impacts = [str(item.get("impact") or "") for item in considered_impacts]
    actions = [
        str(item.get("maintenance_action") or "") for item in considered_maintenance
    ]
    if (
        any(item in {"UNKNOWN", "NOT_COMPARABLE"} for item in impacts)
        or "CANNOT_ASSESS" in actions
    ):
        return "UNRESOLVED"
    complete = (
        str(completeness.get("status") or "") == CompletenessStatus.COMPLETE.value
    )
    gaps = parse_json_list(completeness.get("known_gaps"))
    gap_hits = [
        str(item) for item in gaps if any(str(item) in member for member in changed)
    ]
    unaffectable = (
        not impacts or all(item == "UNAFFECTED" for item in impacts)
    ) and "CANNOT_ASSESS" not in actions
    if _uncertain_comparison(comparison) and unaffectable:
        return "UNRESOLVED"
    if unaffectable and complete and not gap_hits and changed.issubset(universe):
        return "NO_APPLICABLE_AUTHORITY"
    return "NO_ATTACHMENT_FOUND"


def _explicit_conflicts(claims: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    governing = [item for item in claims if item.get("governing")]
    for index, left in enumerate(governing):
        for right in governing[index + 1 :]:
            if left.get("relation_name") != right.get("relation_name"):
                continue
            left_tuple = dict(left.get("tuple") or {})
            right_tuple = dict(right.get("tuple") or {})
            if set(left_tuple) != set(right_tuple) or left_tuple == right_tuple:
                continue
            shared = [key for key in left_tuple if left_tuple[key] == right_tuple[key]]
            differing = [
                key for key in left_tuple if left_tuple[key] != right_tuple[key]
            ]
            if shared and differing:
                conflicts.append(
                    {
                        "relation_name": left.get("relation_name"),
                        "claims": [left.get("assertion_id"), right.get("assertion_id")],
                        "shared_roles": shared,
                        "differing_roles": differing,
                    }
                )
    return conflicts


def _manifestation_reason(properties: Sequence[Any]) -> str:
    names = {str(item) for item in properties if item}
    if "source_manifestation" in names:
        return "MANIFESTATION_CHANGED"
    if "signature" in names:
        return "SIGNATURE_CHANGED"
    return ""


def _add_source_target(
    targets: dict[tuple[str, str], dict[str, str]],
    *,
    side: str,
    entity: str,
    reason: str,
) -> None:
    if not entity or not reason:
        return
    key = (side, entity)
    current = targets.get(key)
    if current is None:
        targets[key] = {
            "side": side,
            "program_entity": entity,
            "inclusion_reason": reason,
        }
        return
    rank = {
        "AMBIGUOUS_CANDIDATE": 3,
        "WARRANT_MANIFESTATION_DEPENDENCY": 2,
        "EXPLICIT_SCOPE_IDENTITY": 1,
        "MANIFESTATION_CHANGED": 0,
        "SIGNATURE_CHANGED": 0,
    }
    if rank.get(reason, 0) > rank.get(str(current.get("inclusion_reason") or ""), 0):
        current["inclusion_reason"] = reason


def _source_targets(
    *,
    assessment: Mapping[str, Any],
    impact_row: Mapping[str, Any],
    comparison: SpineComparisonResult,
) -> list[dict[str, str]]:
    """Select identities whose grounded ranges belong in the case.

    Relation-only hits (call-site retargets) do not include caller/callee bodies.
    """

    entity = str(assessment.get("old_program_entity") or "")
    candidates = [
        str(item) for item in assessment.get("candidate_new_manifestations") or []
    ]
    continuation = str(assessment.get("continuation") or "")
    targets: dict[tuple[str, str], dict[str, str]] = {}
    if continuation == "AMBIGUOUS":
        _add_source_target(
            targets, side="OLD", entity=entity, reason="AMBIGUOUS_CANDIDATE"
        )
        for candidate in candidates:
            _add_source_target(
                targets,
                side="CANDIDATE",
                entity=candidate,
                reason="AMBIGUOUS_CANDIDATE",
            )
    for hit in impact_row.get("intersecting_deltas") or []:
        if not isinstance(hit, Mapping):
            continue
        kind = str(hit.get("kind") or "")
        if kind in {"relation", "identity"}:
            continue
        if kind == "manifestation":
            reason = _manifestation_reason(hit.get("properties") or [])
            if not reason:
                continue
            _add_source_target(targets, side="OLD", entity=entity, reason=reason)
            if continuation == "UNIQUE" and candidates:
                _add_source_target(
                    targets, side="NEW", entity=candidates[0], reason=reason
                )
            continue
        if kind in {"explicit_manifestation", "structural_manifestation"}:
            old_id = str(hit.get("old_entity") or "")
            properties = list(hit.get("properties") or [])
            if hit.get("property"):
                properties.append(hit.get("property"))
            if kind == "structural_manifestation" and not properties:
                properties = ["source_manifestation"]
            reason = _manifestation_reason(properties) or "EXPLICIT_SCOPE_IDENTITY"
            if kind == "explicit_manifestation" or kind == "structural_manifestation":
                reason = "EXPLICIT_SCOPE_IDENTITY"
            view = continuation_view(comparison, old_id)
            if view.continuation == "AMBIGUOUS":
                _add_source_target(
                    targets, side="OLD", entity=old_id, reason="AMBIGUOUS_CANDIDATE"
                )
                for candidate in view.candidates:
                    _add_source_target(
                        targets,
                        side="CANDIDATE",
                        entity=str(candidate),
                        reason="AMBIGUOUS_CANDIDATE",
                    )
                continue
            _add_source_target(targets, side="OLD", entity=old_id, reason=reason)
            row = hit.get("row") if isinstance(hit.get("row"), Mapping) else {}
            new_id = str(row.get("new_entity") or "")
            if new_id:
                _add_source_target(targets, side="NEW", entity=new_id, reason=reason)
            elif view.continuation == "UNIQUE" and view.candidates:
                _add_source_target(
                    targets, side="NEW", entity=str(view.candidates[0]), reason=reason
                )
    for dep in assessment.get("dependencies_examined") or []:
        if not isinstance(dep, Mapping):
            continue
        recorded = json.dumps(dep.get("recorded_fact") or {})
        if (
            dep.get("dependency_change") == "CHANGED"
            and "source_manifestation" in recorded
        ):
            _add_source_target(
                targets,
                side="OLD",
                entity=entity,
                reason="WARRANT_MANIFESTATION_DEPENDENCY",
            )
            if continuation == "UNIQUE" and candidates:
                _add_source_target(
                    targets,
                    side="NEW",
                    entity=candidates[0],
                    reason="WARRANT_MANIFESTATION_DEPENDENCY",
                )
    return sorted(
        targets.values(),
        key=lambda item: (
            item["side"],
            item["program_entity"],
            item["inclusion_reason"],
        ),
    )


def assemble_governance_case(
    old_world: ConstructionWorld | Path | str,
    new_world: ConstructionWorld | Path | str,
    comparison: SpineComparisonResult | Path | str,
    sources: Mapping[str, MarkdownSource],
    *,
    maintenance: Mapping[str, Any] | None = None,
    impact: Mapping[str, Any] | None = None,
    purpose: str = "",
    invariant_definition: Mapping[str, Any] | None = None,
    baseline_invariant_derivation: Mapping[str, Any] | None = None,
    candidate_invariant_derivation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return ``governance.case.json``. Does not mutate Worlds or search Markdown."""

    old, old_owned = _open(old_world)
    new, new_owned = _open(new_world)
    try:
        return _assemble(
            old,
            new,
            _comparison(comparison),
            sources,
            maintenance=maintenance,
            impact=impact,
            purpose=purpose,
            invariant_definition=invariant_definition,
            baseline_invariant_derivation=baseline_invariant_derivation,
            candidate_invariant_derivation=candidate_invariant_derivation,
        )
    finally:
        if old_owned:
            old.close()
        if new_owned:
            new.close()


def _invariant_relation_tuples(
    derivation: Mapping[str, Any], *, side: str
) -> list[dict[str, Any]]:
    """Copy evaluator-grounded invoke facts into case mechanical evidence."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for member in derivation.get("member_results") or []:
        if not isinstance(member, Mapping):
            continue
        facts = []
        first_hop = member.get("first_hop")
        if isinstance(first_hop, Mapping):
            facts.append(first_hop)
        facts.extend(
            item
            for item in member.get("path_evidence") or []
            if isinstance(item, Mapping)
        )
        for fact in facts:
            recorded = {
                "relation": str(fact.get("relation") or "program_invokes"),
                "call_site": str(fact.get("call_site") or ""),
                "target": str(fact.get("target") or ""),
            }
            if not recorded["call_site"] or not recorded["target"]:
                continue
            evidence_id = str(fact.get("evidence_id") or "relation:" + digest(recorded))
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            rows.append(
                {
                    "axis": "scoped_invariant_derivation",
                    "side": side,
                    "recorded_fact": recorded,
                    "evidence_id": evidence_id,
                    "inclusion_reason": "SCOPED_INVARIANT_DERIVATION",
                    "member_id": str(member.get("member_id") or ""),
                    "member_result": str(member.get("result") or ""),
                    "derivation_id": str(derivation.get("derivation_id") or ""),
                    "overall_truth": str(derivation.get("overall_truth") or ""),
                }
            )
    return rows


def _assemble(
    old: ConstructionWorld,
    new: ConstructionWorld,
    result: SpineComparisonResult,
    sources: Mapping[str, MarkdownSource],
    *,
    maintenance: Mapping[str, Any] | None,
    impact: Mapping[str, Any] | None,
    purpose: str,
    invariant_definition: Mapping[str, Any] | None = None,
    baseline_invariant_derivation: Mapping[str, Any] | None = None,
    candidate_invariant_derivation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    old_snapshot = str(
        result.receipt.snapshots.get("old", {}).get("id") or result.delta.old_snapshot
    )
    new_snapshot = str(
        result.receipt.snapshots.get("new", {}).get("id") or result.delta.new_snapshot
    )
    if snapshot_id(old) and snapshot_id(old) != old_snapshot:
        raise GovernanceError("comparison old snapshot does not match the old World")
    if snapshot_id(new) and snapshot_id(new) != new_snapshot:
        raise GovernanceError("comparison new snapshot does not match the new World")
    maintenance_payload = maintenance or assess_attachment_maintenance(old, new, result)
    impact_payload = impact or assess_authority_change_impact(
        old, new, result, maintenance=maintenance_payload
    )
    standing = _standing_map(old)
    purpose_value = purpose
    if not purpose_value:
        rows = old.relation_rows("authority_completeness")
        if rows:
            purpose_value = str(rows[0].get("purpose") or "")
    by_maint = {
        str(item["warrant_assertion_id"]): item
        for item in maintenance_payload.get("assessments") or []
    }
    by_impact = {
        str(item["warrant_assertion_id"]): item
        for item in impact_payload.get("impacts") or []
    }
    selections: list[dict[str, Any]] = []
    authority_obs: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    supporting_obs: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    claims_out: dict[str, dict[str, Any]] = {}
    semantic_out: dict[str, dict[str, Any]] = {}
    semantic_context_claims: dict[str, dict[str, Any]] = {}
    semantic_context_referents: dict[str, dict[str, Any]] = {}
    semantic_context_program_links: dict[tuple[str, str, str], dict[str, Any]] = {}
    transition_facts: dict[str, dict[str, Any]] = {}
    referents: dict[str, dict[str, Any]] = {}
    structural: list[dict[str, Any]] = []
    relation_tuples: list[dict[str, Any]] = []
    resolutions: list[dict[str, Any]] = []
    triggering: list[dict[str, Any]] = []
    heuristic: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    reconstruction_failures: list[dict[str, Any]] = []
    unresolved_construction: list[dict[str, Any]] = []
    source_evidence: dict[tuple[Any, ...], dict[str, Any]] = {}
    known_omissions: list[str] = [
        str(item) for item in maintenance_payload.get("known_omissions") or []
    ]
    known_omissions.extend(
        str(item) for item in impact_payload.get("known_omissions") or []
    )
    old_program_entities = {
        str(row["entity"]) for row in old.relation_rows("program_entity")
    }

    def _merge_context_reason(
        record: dict[str, Any], *, attachment_id: str, reason: str
    ) -> None:
        record["selected_by"] = sorted(
            set(record.get("selected_by") or []) | {attachment_id}
        )
        record["included_because"] = sorted(
            set(record.get("included_because") or []) | {reason}
        )

    def _record_semantic_context_claim(
        claim: Mapping[str, Any],
        tuple_values: Mapping[str, Any],
        observation_ids: Sequence[str],
        *,
        attachment_id: str,
        inclusion_reason: str = "SELECTED_ATTACHMENT_SEMANTIC_CONTEXT",
    ) -> tuple[list[str], list[str]]:
        """Project only already-persisted semantic claims into the case."""

        claim_id = str(claim.get("assertion_id") or "")
        semantics = _semantics(old, tuple_values)
        if not claim_id or not semantics:
            return [], []
        context_claim = semantic_context_claims.setdefault(
            claim_id,
            {
                "assertion_id": claim_id,
                "relation_name": claim.get("relation_name"),
                "tuple": copy_json(tuple_values),
                "claim_kind": claim.get("claim_kind"),
                "relation_support": claim.get("relation_support"),
                "endpoint_resolution": copy_json(
                    claim.get("endpoint_resolution") or {}
                ),
                "source_observation_ids": sorted(set(observation_ids)),
                "selected_by": [],
                "included_because": [],
            },
        )
        context_claim["source_observation_ids"] = sorted(
            set(context_claim.get("source_observation_ids") or [])
            | set(observation_ids)
        )
        _merge_context_reason(
            context_claim,
            attachment_id=attachment_id,
            reason=inclusion_reason,
        )
        for semantic in semantics:
            referent = semantic_context_referents.setdefault(
                semantic,
                {
                    "id": semantic,
                    "label": entity_label(old, semantic),
                    "claim_refs": [],
                    "source_observation_ids": [],
                    "selected_by": [],
                    "included_because": [],
                    "status": "POSITIVE",
                },
            )
            referent["claim_refs"] = sorted(
                set(referent.get("claim_refs") or []) | {claim_id}
            )
            referent["source_observation_ids"] = sorted(
                set(referent.get("source_observation_ids") or []) | set(observation_ids)
            )
            _merge_context_reason(
                referent,
                attachment_id=attachment_id,
                reason=inclusion_reason,
            )
            previous = semantic_out.get(semantic, {"selected_by": []})
            semantic_out[semantic] = {
                "id": semantic,
                "label": entity_label(old, semantic),
                "selected_by": sorted(
                    set(previous.get("selected_by") or []) | {attachment_id}
                ),
            }

        program_entities = [
            str(value)
            for value in tuple_values.values()
            if str(value) in old_program_entities
        ]
        if (
            str(claim.get("claim_kind") or "") == ClaimKind.SEMANTIC_PROGRAM.value
            and program_entities
        ):
            for semantic in semantics:
                for program_entity in program_entities:
                    key = (claim_id, semantic, program_entity)
                    link = semantic_context_program_links.setdefault(
                        key,
                        {
                            "assertion_id": claim_id,
                            "relation_name": claim.get("relation_name"),
                            "semantic_referent": semantic,
                            "program_entity": program_entity,
                            "program_snapshot_id": snapshot_id(old),
                            "side": "OLD",
                            "tuple": copy_json(tuple_values),
                            "source_observation_ids": sorted(set(observation_ids)),
                            "status": "POSITIVE",
                            "selected_by": [],
                            "included_because": [],
                        },
                    )
                    link["source_observation_ids"] = sorted(
                        set(link.get("source_observation_ids") or [])
                        | set(observation_ids)
                    )
                    _merge_context_reason(
                        link,
                        attachment_id=attachment_id,
                        reason=inclusion_reason,
                    )
        return semantics, [claim_id]

    def _record_changed_endpoint_context(
        *,
        attachment_id: str,
        assessment: Mapping[str, Any],
        semantic_referents: Sequence[str],
        old_program_links: Sequence[Mapping[str, Any]],
    ) -> None:
        """Expose new-side link absence without manufacturing a new link."""

        if not semantic_referents or not old_program_links:
            return
        absence_status, coverage = _semantic_absence_status(old)
        old_link_entities = {
            str(item.get("program_entity") or "") for item in old_program_links
        }
        for candidate in assessment.get("candidate_new_manifestations") or []:
            candidate_id = str(candidate)
            if not candidate_id or candidate_id in old_link_entities:
                continue
            for link in old_program_links:
                relation_name = str(link.get("relation_name") or "")
                semantic = str(link.get("semantic_referent") or "")
                if semantic not in semantic_referents:
                    continue
                key = (relation_name, semantic, candidate_id)
                record = semantic_context_program_links.setdefault(
                    key,
                    {
                        "assertion_id": None,
                        "relation_name": relation_name,
                        "semantic_referent": semantic,
                        "program_entity": candidate_id,
                        "program_snapshot_id": new_snapshot,
                        "side": "NEW",
                        "tuple": {},
                        "status": absence_status,
                        "coverage": copy_json(coverage),
                        "selected_by": [],
                        "included_because": [],
                    },
                )
                _merge_context_reason(
                    record,
                    attachment_id=attachment_id,
                    reason="CHANGED_ENDPOINT_SEMANTIC_CONTEXT",
                )

    def _record_transition_facts(
        *,
        attachment_id: str,
        semantic_claim_refs: Sequence[str],
        semantic_referents: Sequence[str],
        deltas: Sequence[Mapping[str, Any]],
    ) -> None:
        """Project a selected, already-mechanical old/new endpoint change."""

        # A selected direct source→program attachment can also make a
        # mechanical old/new transition meaningful.  It gets an explicit
        # attachment ref below but no fabricated semantic referent.
        if not deltas:
            return
        for delta in deltas:
            row = delta.get("row") if isinstance(delta.get("row"), Mapping) else {}
            changed_endpoint = str(row.get("changed_endpoint") or "")
            old_value = row.get("old") if isinstance(row.get("old"), Mapping) else None
            new_value = row.get("new") if isinstance(row.get("new"), Mapping) else None
            if not old_value or not new_value:
                old_entity = str(delta.get("old_entity") or "")
                new_entity = str(delta.get("new_entity") or "")
                changes = (
                    delta.get("changes")
                    if isinstance(delta.get("changes"), Mapping)
                    else {}
                )
                changed_properties = [
                    str(key)
                    for key, value in changes.items()
                    if str(value) == "CHANGED"
                ]
                if old_entity and new_entity and changed_properties:
                    changed_endpoint = next(
                        (
                            candidate
                            for candidate in (
                                "source_manifestation",
                                "signature",
                                "source_location",
                                "name",
                                "boundary",
                            )
                            if candidate in changed_properties
                        ),
                        changed_properties[0],
                    )
                    old_value = {
                        "program_entity": old_entity,
                        "changes": copy_json(changes),
                    }
                    new_value = {
                        "program_entity": new_entity,
                        "changes": copy_json(changes),
                    }
            if not old_value or not new_value or old_value == new_value:
                continue
            if not changed_endpoint:
                continue
            evidence_id = str(delta.get("evidence_id") or "delta:" + digest(delta))
            item = {
                "authority_attachment_id": attachment_id,
                "subject_semantic_referents": sorted(set(semantic_referents)),
                "authority_claim_refs": [attachment_id],
                "relation": delta.get("relation"),
                "changed_endpoint": changed_endpoint,
                "old": copy_json(old_value),
                "new": copy_json(new_value),
                "mechanical_evidence_refs": [evidence_id],
                "semantic_context_refs": sorted(set(semantic_claim_refs)),
                "included_because": ["SELECTED_TRANSITION_FACT"],
            }
            transition_facts[digest(item)] = item

    def _transition_deltas(
        *,
        assessment: Mapping[str, Any],
        impact_row: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """Add a selected manifestation delta when impact summarized it."""

        deltas = [
            copy_json(item)
            for item in impact_row.get("intersecting_deltas") or []
            if isinstance(item, Mapping)
        ]
        if any(
            isinstance(item.get("row"), Mapping)
            and isinstance(item["row"].get("old"), Mapping)
            and isinstance(item["row"].get("new"), Mapping)
            for item in deltas
        ):
            return deltas
        old_entity = str(assessment.get("old_program_entity") or "")
        candidates = {
            str(item) for item in assessment.get("candidate_new_manifestations") or []
        }
        for manifestation in result.delta.manifestations:
            if not isinstance(manifestation, Mapping):
                continue
            if str(manifestation.get("old_entity") or "") != old_entity:
                continue
            if str(manifestation.get("new_entity") or "") not in candidates:
                continue
            changes = manifestation.get("changes")
            if not isinstance(changes, Mapping) or not any(
                value == "CHANGED" for value in changes.values()
            ):
                continue
            deltas.append(
                {
                    "kind": "manifestation",
                    "old_entity": old_entity,
                    "new_entity": str(manifestation.get("new_entity") or ""),
                    "changes": copy_json(changes),
                }
            )
        return deltas

    for warrant in sorted(
        relation_rows_with_ids(old, "authority_attachment_warrant"),
        key=lambda row: (
            str(row.get("assertion_id") or ""),
            str(row.get("program_entity") or ""),
        ),
    ):
        warrant_id = str(warrant.get("_assertion_id") or "")
        assessment = by_maint.get(warrant_id)
        impact_row = by_impact.get(warrant_id)
        if assessment is None or impact_row is None:
            continue
        reasons = selected_because(
            str(assessment["maintenance_action"]), str(impact_row["impact"])
        )
        if not reasons:
            continue
        attachment_id = str(warrant["assertion_id"])
        entity = str(warrant["program_entity"])
        claim_row = next(
            (
                item
                for item in old.relation_rows("authority_claim")
                if str(item["assertion_id"]) == attachment_id
            ),
            {},
        )
        observations = observations_for_assertion(old, attachment_id)
        tuple_values = _claim_tuple(
            old, attachment_id, str(claim_row.get("relation_name") or "")
        )
        observation_ids = [
            _store_observation(
                observation,
                sources=sources,
                standing=standing,
                attachment_id=attachment_id,
                authority_obs=authority_obs,
                supporting_obs=supporting_obs,
                reconstruction_failures=reconstruction_failures,
                known_omissions=known_omissions,
            )
            for observation in observations
        ]
        governing = bool(claim_row.get("governing"))
        if (
            observations
            and standing.get(observations[0].native_handle)
            != SourceStanding.AUTHORITATIVE.value
        ):
            governing = False
        claims_out[attachment_id] = {
            "assertion_id": attachment_id,
            "relation_name": claim_row.get("relation_name"),
            "tuple": tuple_values,
            "claim_kind": claim_row.get("claim_kind"),
            "relation_support": claim_row.get("relation_support"),
            "endpoint_resolution": _resolutions(old, attachment_id),
            "governing": governing,
        }
        semantic_claim_refs: list[str] = []
        selected_semantic_referents: list[str] = []
        selected_program_links: list[dict[str, Any]] = []
        selected_contexts: list[
            tuple[Mapping[str, Any], Mapping[str, Any], Sequence[str]]
        ] = [(claims_out[attachment_id], tuple_values, observation_ids)]
        for related in _related_claims(
            old,
            attachment_id=attachment_id,
            claim_kind=str(claim_row.get("claim_kind") or ""),
            observations=observations,
            tuple_values=tuple_values,
        ):
            other = related["claim"]
            other_id = str(other["assertion_id"])
            related_observation_ids: list[str] = []
            claims_out.setdefault(
                other_id,
                {
                    "assertion_id": other_id,
                    "relation_name": other.get("relation_name"),
                    "tuple": related["tuple"],
                    "claim_kind": other.get("claim_kind"),
                    "relation_support": other.get("relation_support"),
                    "endpoint_resolution": _resolutions(old, other_id),
                    "governing": bool(other.get("governing")),
                },
            )
            for observation in related["observations"]:
                stored_id = _store_observation(
                    observation,
                    sources=sources,
                    standing=standing,
                    attachment_id=attachment_id,
                    authority_obs=authority_obs,
                    supporting_obs=supporting_obs,
                    reconstruction_failures=reconstruction_failures,
                    known_omissions=known_omissions,
                )
                observation_ids.append(stored_id)
                related_observation_ids.append(stored_id)
            selected_contexts.append(
                (claims_out[other_id], related["tuple"], related_observation_ids)
            )
        for context_claim, context_tuple, context_observations in selected_contexts:
            semantics, claim_refs = _record_semantic_context_claim(
                context_claim,
                context_tuple,
                context_observations,
                attachment_id=attachment_id,
            )
            selected_semantic_referents.extend(semantics)
            semantic_claim_refs.extend(claim_refs)
        # A selected authority may be connected to a changed endpoint through
        # a persisted semantic-program claim that is not itself the selected
        # attachment.  Include it only when the claim shares the selected
        # authority evidence and its old program endpoint is in the triggering
        # delta.  This is a bounded World read, not semantic discovery.
        selected_observation_keys = {_obs_key(item) for item in observations}
        changed_old_endpoints: set[str] = set()
        # The selected attachment's own warrant may summarize only the
        # governed surface (for example a callable manifestation), while a
        # persisted semantic commitment can depend on a bounded relation
        # tuple inside that surface.  Include the exact old endpoints already
        # marked changed by ProgramDelta.  This is a mechanical endpoint
        # intersection, not semantic traversal or rediscovery.
        changed_old_endpoints.update(
            changed_program_identities(
                result.delta,
                kinds={
                    str(row["entity"]): str(row["kind"])
                    for row in old.relation_rows("program_entity_kind")
                },
            )
        )
        for delta in _transition_deltas(assessment=assessment, impact_row=impact_row):
            row = delta.get("row") if isinstance(delta.get("row"), Mapping) else {}
            old_value = row.get("old") if isinstance(row.get("old"), Mapping) else {}
            changed_old_endpoints.update(
                str(value)
                for value in old_value.values()
                if str(value) in old_program_entities
            )
            old_entity = str(delta.get("old_entity") or "")
            if old_entity in old_program_entities:
                changed_old_endpoints.add(old_entity)
        for persisted_claim in old.relation_rows("authority_claim"):
            persisted_id = str(persisted_claim.get("assertion_id") or "")
            if (
                persisted_id in claims_out
                or str(persisted_claim.get("claim_kind") or "")
                != ClaimKind.SEMANTIC_PROGRAM.value
            ):
                continue
            persisted_observations = observations_for_assertion(old, persisted_id)
            if not selected_observation_keys.intersection(
                _obs_key(item) for item in persisted_observations
            ):
                continue
            persisted_tuple = _claim_tuple(
                old, persisted_id, str(persisted_claim.get("relation_name") or "")
            )
            persisted_semantics = set(_semantics(old, persisted_tuple))
            persisted_programs = {
                str(value)
                for value in persisted_tuple.values()
                if str(value) in old_program_entities
            }
            if not persisted_semantics.intersection(selected_semantic_referents):
                continue
            if not persisted_programs.intersection(changed_old_endpoints):
                continue
            persisted_observation_ids = [
                _store_observation(
                    observation,
                    sources=sources,
                    standing=standing,
                    attachment_id=attachment_id,
                    authority_obs=authority_obs,
                    supporting_obs=supporting_obs,
                    reconstruction_failures=reconstruction_failures,
                    known_omissions=known_omissions,
                )
                for observation in persisted_observations
            ]
            claims_out[persisted_id] = {
                "assertion_id": persisted_id,
                "relation_name": persisted_claim.get("relation_name"),
                "tuple": persisted_tuple,
                "claim_kind": persisted_claim.get("claim_kind"),
                "relation_support": persisted_claim.get("relation_support"),
                "endpoint_resolution": _resolutions(old, persisted_id),
                "governing": bool(persisted_claim.get("governing")),
            }
            semantics, claim_refs = _record_semantic_context_claim(
                claims_out[persisted_id],
                persisted_tuple,
                persisted_observation_ids,
                attachment_id=attachment_id,
            )
            selected_semantic_referents.extend(semantics)
            semantic_claim_refs.extend(claim_refs)
        # A semantic commitment is not an authority_claim.  When a selected
        # authority is affected by a changed manifestation, however, its
        # persisted semantic/program assertion is bounded, already-grounded
        # context for that case.  Read only the canonical commitment relation
        # and its warrant; do not discover or reconstruct semantic meaning.
        relation_names = {
            str(row["name"]) for row in old.query("SELECT name FROM _world_relations")
        }
        persisted_warrants = (
            old.relation_rows(SEMANTIC_WARRANT_RELATION)
            if SEMANTIC_WARRANT_RELATION in relation_names
            else []
        )
        persisted_commitments: dict[str, tuple[str, Mapping[str, Any]]] = {}
        for relation_name in (
            PROGRAM_REALIZATION_RELATION,
            PROGRAM_RELATIONSHIP_RELATION,
            PROGRAM_INVARIANT_RELATION,
        ):
            if relation_name not in relation_names:
                continue
            for item in relation_rows_with_ids(old, relation_name):
                persisted_commitments[str(item.get("_assertion_id") or "")] = (
                    relation_name,
                    item,
                )
        for semantic_warrant in persisted_warrants:
            realization_id = str(semantic_warrant.get("assertion_id") or "")
            realization_record = persisted_commitments.get(realization_id)
            if realization_record is None:
                continue
            realization_name, realization = realization_record
            realization_tuple = {
                key: value
                for key, value in realization.items()
                if key != "_assertion_id"
            }
            persisted_semantics = set(_semantics(old, realization_tuple))
            if not persisted_semantics.intersection(selected_semantic_referents):
                continue
            persisted_programs = {
                str(value)
                for value in realization_tuple.values()
                if str(value) in old_program_entities
            }
            if not persisted_programs.intersection(changed_old_endpoints):
                continue
            persisted_observations = observations_for_assertion(old, realization_id)
            if not selected_observation_keys.intersection(
                _obs_key(item) for item in persisted_observations
            ):
                continue
            persisted_observation_ids = [
                _store_observation(
                    observation,
                    sources=sources,
                    standing=standing,
                    attachment_id=attachment_id,
                    authority_obs=authority_obs,
                    supporting_obs=supporting_obs,
                    reconstruction_failures=reconstruction_failures,
                    known_omissions=known_omissions,
                )
                for observation in persisted_observations
            ]
            endpoint_resolution = {}
            try:
                endpoint_resolution = json.loads(
                    str(semantic_warrant.get("resolution_basis") or "{}")
                )
            except (TypeError, ValueError):
                endpoint_resolution = {}
            persisted_claim = {
                "assertion_id": realization_id,
                "relation_name": realization_name,
                "tuple": realization_tuple,
                "claim_kind": ClaimKind.SEMANTIC_PROGRAM.value,
                "relation_support": "PERSISTED_COMMITMENT",
                "endpoint_resolution": endpoint_resolution,
                "governing": False,
            }
            semantics, claim_refs = _record_semantic_context_claim(
                persisted_claim,
                realization_tuple,
                persisted_observation_ids,
                attachment_id=attachment_id,
                inclusion_reason="PERSISTED_SEMANTIC_COMMITMENT",
            )
            selected_semantic_referents.extend(semantics)
            semantic_claim_refs.extend(claim_refs)
        selected_program_links = [
            item
            for item in semantic_context_program_links.values()
            if attachment_id in set(item.get("selected_by") or [])
            and item.get("status") == "POSITIVE"
        ]
        _record_changed_endpoint_context(
            attachment_id=attachment_id,
            assessment=assessment,
            semantic_referents=selected_semantic_referents,
            old_program_links=selected_program_links,
        )
        selected_transition_deltas = _transition_deltas(
            assessment=assessment, impact_row=impact_row
        )
        existing_delta_digests = {
            digest(item)
            for item in impact_row.get("intersecting_deltas") or []
            if isinstance(item, Mapping)
        }
        triggering.extend(
            copy_json(item)
            for item in selected_transition_deltas
            if digest(item) not in existing_delta_digests
        )
        _record_transition_facts(
            attachment_id=attachment_id,
            semantic_claim_refs=semantic_claim_refs,
            semantic_referents=selected_semantic_referents,
            deltas=selected_transition_deltas,
        )
        referents[entity] = {
            "id": entity,
            "side": "old",
            "kind": entity_kind(old, entity),
            "label": entity_label(old, entity),
        }
        for candidate in assessment.get("candidate_new_manifestations") or []:
            referents[str(candidate)] = {
                "id": str(candidate),
                "side": "new",
                "kind": entity_kind(new, str(candidate)),
                "label": entity_label(new, str(candidate)),
            }
        structural.append(
            {"side": "old", "entity": entity, "chain": ancestor_chain(old, entity)}
        )
        for candidate in assessment.get("candidate_new_manifestations") or []:
            structural.append(
                {
                    "side": "new",
                    "entity": candidate,
                    "chain": ancestor_chain(new, str(candidate)),
                }
            )
        for dep in assessment.get("dependencies_examined") or []:
            if dep.get("kind") == "program_relation":
                relation_tuples.append(
                    {
                        "axis": "warrant",
                        "recorded_fact": dep.get("recorded_fact"),
                        "dependency_change": dep.get("dependency_change"),
                        "delta_evidence": dep.get("delta_evidence"),
                    }
                )
            if dep.get("kind") == "resolution_outcome":
                resolutions.append(copy_json(dep))
        triggering.extend(
            copy_json(item) for item in impact_row.get("intersecting_deltas") or []
        )
        for dep in assessment.get("dependencies_examined") or []:
            if dep.get("dependency_change") in {
                "CHANGED",
                "LOST",
                "UNKNOWN",
                "NOT_COMPARABLE",
            }:
                triggering.extend(
                    copy_json(item) for item in dep.get("delta_evidence") or []
                )
        if assessment.get("correspondence_basis") == "HEURISTIC":
            heuristic.append(
                {
                    "old_program_entity": entity,
                    "candidates": list(
                        assessment.get("candidate_new_manifestations") or []
                    ),
                    "continuity": assessment.get("correspondence_continuity"),
                }
            )
        if assessment.get("continuation") == "AMBIGUOUS":
            ambiguous.append(
                {
                    "old_program_entity": entity,
                    "candidates": list(
                        assessment.get("candidate_new_manifestations") or []
                    ),
                }
            )
        selections.append(
            {
                "attachment_assertion_id": attachment_id,
                "warrant_assertion_id": warrant_id,
                "maintenance_assessment_ref": assessment.get("assessment_id"),
                "change_impact_ref": impact_row.get("impact_id"),
                "selected_because": reasons,
                "selection_path": {
                    "maintenance_action": assessment.get("maintenance_action"),
                    "impact": impact_row.get("impact"),
                    "warrant_dependencies": [
                        item
                        for item in assessment.get("dependencies_examined") or []
                        if item.get("dependency_change") != "PRESERVED"
                    ],
                    "relevance_hits": impact_row.get("intersecting_deltas") or [],
                    "scope_source": impact_row.get("scope_source"),
                    "scope_clauses": impact_row.get("scope_clauses") or [],
                },
                "attachment_warrant": {
                    "program_entity": entity,
                    "structural_context": parse_json_list(
                        warrant.get("structural_context")
                    ),
                    "justifying_program_relations": parse_json_list(
                        warrant.get("justifying_program_relations")
                    ),
                    "justifying_resolution_outcomes": parse_json_list(
                        warrant.get("justifying_resolution_outcomes")
                    ),
                },
                "authority_relevance_scope": impact_row.get("scope_clauses") or [],
                "attachment_maintenance_assessment": assessment,
                "authority_change_impact": impact_row,
                "semantic_referent": next(iter(_semantics(old, tuple_values)), None),
                "observation_ids": sorted(set(observation_ids)),
            }
        )
        for target in _source_targets(
            assessment=assessment, impact_row=impact_row, comparison=result
        ):
            side = str(target["side"])
            identity = str(target["program_entity"])
            host = old if side == "OLD" else new
            snap = old_snapshot if side == "OLD" else new_snapshot
            observations = program_source_observations(host, identity)
            if not observations:
                known_omissions.append(
                    f"no grounded program source observation for {identity}"
                )
                reconstruction_failures.append(
                    {
                        "program_entity": identity,
                        "side": side,
                        "reason": "missing grounded observation",
                    }
                )
                continue
            for observation in observations:
                record = source_evidence_record(
                    world=host,
                    entity=identity,
                    side=side,
                    snapshot_id=snap,
                    inclusion_reason=str(target["inclusion_reason"]),
                    selected_by=attachment_id,
                    observation=observation,
                )
                key = (
                    record["side"],
                    record["snapshot"],
                    record["program_entity"],
                    record["handle"],
                    record["native_location"],
                    record["inclusion_reason"],
                )
                existing = source_evidence.get(key)
                if existing:
                    existing["selected_by"] = sorted(
                        set(existing["selected_by"]) | {attachment_id}
                    )
                    continue
                source_evidence[key] = record
                if record["reconstruction"] != "OK":
                    reconstruction_failures.append(
                        {
                            "evidence_id": record["evidence_id"],
                            "program_entity": identity,
                            "side": side,
                            "handle": record["handle"],
                            "native_location": record["native_location"],
                        }
                    )
                    known_omissions.append(
                        "program source could not be reconstructed for "
                        f"{identity} {record['handle']} {record['native_location']}"
                    )

    kinds = {
        str(row["entity"]): str(row["kind"])
        for row in old.relation_rows("program_entity_kind")
    }
    changed = changed_program_identities(result.delta, kinds=kinds)
    universe = _attachment_universe(old, purpose_value)
    completeness = _attachment_completeness(old)
    case_result = _case_result(
        selected=selections,
        considered_impacts=list(impact_payload.get("impacts") or []),
        considered_maintenance=list(maintenance_payload.get("assessments") or []),
        changed=changed,
        universe=universe,
        completeness=completeness,
        comparison=result,
    )
    for row in old.relation_rows("authority_unresolved"):
        candidates = {str(item) for item in parse_json_list(row.get("candidates_json"))}
        if candidates & changed:
            unresolved_construction.append(copy_json(row))
    # Mechanical evidence is copied into the case as bounded rows rather than
    # as World facts. Give those rows stable IDs so a later adjudicator can
    # cite exactly what it saw without inventing a relation or delta handle.
    invariant_supplied = all(
        isinstance(item, Mapping) and item
        for item in (
            invariant_definition,
            baseline_invariant_derivation,
            candidate_invariant_derivation,
        )
    )
    if any(
        item is not None
        for item in (
            invariant_definition,
            baseline_invariant_derivation,
            candidate_invariant_derivation,
        )
    ) and not invariant_supplied:
        raise GovernanceError(
            "scoped invariant case evidence requires definition, baseline "
            "derivation, and candidate derivation together"
        )
    invariant_context = None
    if invariant_supplied:
        invariant_context = {
            "inclusion_reason": "SELECTED_SCOPED_INVARIANT_DERIVATION",
            "authority_question": (
                "All payment-provider access from Checkout must go through "
                "PaymentGateway."
            ),
            "definition": copy_json(invariant_definition),
            "baseline_derivation": copy_json(baseline_invariant_derivation),
            "candidate_derivation": copy_json(candidate_invariant_derivation),
            "preferred_candidate_truth_artifact": "candidate_derivation",
            "supersedes_for_candidate_truth": [
                "semantic_payment_provider_access_invariant",
                "semantic_commitment_warrant",
            ],
            "class_membership_evidence": copy_json(
                (candidate_invariant_derivation or {}).get("evaluation_receipt", {}).get(
                    "class_membership_evidence"
                )
                or []
            ),
            "membership_gaps": copy_json(
                (candidate_invariant_derivation or {}).get("evaluation_receipt", {}).get(
                    "membership_gaps"
                )
                or []
            ),
        }
        existing_relation_ids = {
            str(item.get("evidence_id") or digest(item)) for item in relation_tuples
        }
        for item in _invariant_relation_tuples(
            baseline_invariant_derivation, side="OLD"
        ) + _invariant_relation_tuples(candidate_invariant_derivation, side="NEW"):
            if str(item.get("evidence_id") or "") in existing_relation_ids:
                continue
            relation_tuples.append(item)
            existing_relation_ids.add(str(item.get("evidence_id") or ""))
    relation_tuples = [
        {
            **copy_json(item),
            "evidence_id": str(item.get("evidence_id") or "relation:" + digest(item)),
        }
        for item in relation_tuples
    ]
    resolutions = [
        {
            **copy_json(item),
            "evidence_id": str(item.get("evidence_id") or "resolution:" + digest(item)),
        }
        for item in resolutions
    ]
    triggering = [
        {
            **copy_json(item),
            "evidence_id": str(item.get("evidence_id") or "delta:" + digest(item)),
        }
        for item in triggering
    ]
    claims_list = [claims_out[key] for key in sorted(claims_out)]
    authority_list = [authority_obs[key] for key in sorted(authority_obs)]
    supporting_list = [supporting_obs[key] for key in sorted(supporting_obs)]
    source_list = [source_evidence[key] for key in sorted(source_evidence)]
    semantic_context = {
        "referents": [
            semantic_context_referents[key]
            for key in sorted(semantic_context_referents)
        ],
        "claims": [
            semantic_context_claims[key] for key in sorted(semantic_context_claims)
        ],
        "program_links": [
            semantic_context_program_links[key]
            for key in sorted(semantic_context_program_links)
        ],
    }
    transition_list = [transition_facts[key] for key in sorted(transition_facts)]
    because_counts: dict[str, int] = {}
    for item in selections:
        for reason in item["selected_because"]:
            because_counts[reason] = because_counts.get(reason, 0) + 1
    case_id = "case:" + digest(
        {
            "comparison_id": result.receipt.comparison_id,
            "old_snapshot": old_snapshot,
            "new_snapshot": new_snapshot,
            "selections": [
                {
                    "attachment_assertion_id": item["attachment_assertion_id"],
                    "warrant_assertion_id": item["warrant_assertion_id"],
                    "selected_because": item["selected_because"],
                }
                for item in selections
            ],
            "case_result": case_result,
            "semantic_context": semantic_context,
            "transition_facts": transition_list,
            **({"invariant_context": invariant_context} if invariant_context else {}),
        }
    )
    payload = {
        "case_id": case_id,
        "contract": CASE_SCHEMA,
        "assembly": {
            "receipt_version": CASE_RECEIPT_VERSION,
            "case_id": case_id,
            "mechanism_id": CASE_MECHANISM_ID,
            "mechanism_version": CASE_MECHANISM_VERSION,
            "old_snapshot_id": old_snapshot,
            "new_snapshot_id": new_snapshot,
            "comparison_id": result.receipt.comparison_id,
            "purpose": purpose_value,
            "warrants_considered": len(maintenance_payload.get("assessments") or []),
            "warrants_selected": len(selections),
            "selected_because_counts": because_counts,
            "assessments_hold": sum(
                1
                for item in maintenance_payload.get("assessments") or []
                if item.get("maintenance_action") == "HOLD"
            ),
            "impacts_affected": sum(
                1
                for item in impact_payload.get("impacts") or []
                if item.get("impact") == "AFFECTED"
            ),
            "impacts_unaffected": sum(
                1
                for item in impact_payload.get("impacts") or []
                if item.get("impact") == "UNAFFECTED"
            ),
            "impacts_unknown": sum(
                1
                for item in impact_payload.get("impacts") or []
                if item.get("impact") in {"UNKNOWN", "NOT_COMPARABLE"}
            ),
            "observations_selected": len(authority_list),
            "semantic_referents_involved": sorted(semantic_out),
            "program_referents_included": sorted(referents),
            "program_source_evidence": len(source_list),
            "unresolved_or_ambiguous_items": len(ambiguous)
            + len(unresolved_construction),
            "completeness_basis": {
                "status": completeness.get("status"),
                "universe": completeness.get("universe"),
                "basis": completeness.get("basis"),
                "known_gaps": parse_json_list(completeness.get("known_gaps")),
            },
            "known_omissions": sorted(set(known_omissions)),
            "selection_mechanism": CASE_SCHEMA,
        },
        "case_result": case_result,
        "change": {
            "old_snapshot_id": old_snapshot,
            "new_snapshot_id": new_snapshot,
            "comparison_id": result.receipt.comparison_id,
            "triggering_deltas": triggering,
            "comparison_limitations": list(result.receipt.not_comparable_capabilities),
        },
        "program_context": {
            "referents": [referents[key] for key in sorted(referents)],
            "structural_context": structural,
            "relation_tuples": relation_tuples,
            "resolution_outcomes": resolutions,
            "source_evidence": source_list,
        },
        "semantic_context": semantic_context,
        "transition_facts": transition_list,
        **({"invariant_context": invariant_context} if invariant_context else {}),
        "authority": {
            "observations": authority_list,
            "claims": claims_list,
            "semantic_referents": [semantic_out[key] for key in sorted(semantic_out)],
        },
        "supporting_material": supporting_list,
        "selection": selections,
        "uncertainty": {
            "heuristic_correspondences": heuristic,
            "ambiguous_continuations": ambiguous,
            "unresolved_construction": unresolved_construction,
            "maintenance_cannot_assess": [
                item["assessment_id"]
                for item in maintenance_payload.get("assessments") or []
                if item.get("maintenance_action") == "CANNOT_ASSESS"
            ],
            "impact_unknown": [
                item["impact_id"]
                for item in impact_payload.get("impacts") or []
                if item.get("impact") == "UNKNOWN"
            ],
            "impact_not_comparable": [
                item["impact_id"]
                for item in impact_payload.get("impacts") or []
                if item.get("impact") == "NOT_COMPARABLE"
            ],
            "reconstruction_failures": reconstruction_failures,
            "program_source_reconstruction_failures": [
                item
                for item in reconstruction_failures
                if item.get("evidence_id") or item.get("program_entity")
            ],
            "completeness_limitations": parse_json_list(completeness.get("known_gaps")),
            "known_losses": list(result.receipt.known_losses),
        },
        "conflicts": _explicit_conflicts(claims_list),
        "maintenance_id": maintenance_payload.get("maintenance_id", ""),
        "impact_id": impact_payload.get("impact_id", ""),
        "old_world_id": world_id_of(old.path),
        "new_world_id": world_id_of(new.path),
        "old_world": str(world_dir(old)),
        "new_world": str(world_dir(new)),
    }
    return json.loads(canonical_json(payload))


def write_case(payload: Mapping[str, Any], output_dir: Path | str) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "governance.case.json"
    path.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def markdown_sources_from_root(
    old_world: ConstructionWorld, source_root: Path | str
) -> dict[str, MarkdownSource]:
    root = Path(source_root)
    sources: dict[str, MarkdownSource] = {}
    for row in old_world.relation_rows("authority_source"):
        handle = str(row["source_handle"])
        path = root / handle
        if path.exists():
            sources[handle] = MarkdownSource(path, handle=handle)
    return sources
