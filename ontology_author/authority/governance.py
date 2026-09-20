"""Narrow authority-governance APIs and sidecar validation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ontology_author.program_spine.comparison import SpineComparisonResult
from ontology_author.world.runtime.world import ConstructionWorld

from .case import (
    SEMANTIC_CONTEXT_INCLUSION_REASONS,
    SEMANTIC_CONTEXT_STATUSES,
    assemble_governance_case,
    write_case,
)
from .evaluate import relation_rows_with_ids, snapshot_id
from .impact import IMPACT_SCHEMA, assess_authority_change_impact, write_impact
from .maintenance import (
    MAINTENANCE_SCHEMA,
    PERSISTENCE_IMPLICATION,
    assess_attachment_maintenance,
    write_maintenance,
)
from ontology_author.evidence.markdown import MarkdownSource

COMPLIANCE_KEYS = {
    "verdict",
    "compliance",
    "compliant",
    "noncompliant",
    "non_compliant",
    "pass",
    "fail",
    "violation",
    "violations",
    "allowed",
    "prohibited",
    "renew",
    "renewed",
    "renewal",
    "relevance_score",
    "score",
}


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


def compliance_fields(payload: Mapping[str, Any]) -> list[str]:
    found = []
    for key in _walk_keys(payload):
        lowered = key.lower()
        if lowered in COMPLIANCE_KEYS:
            found.append(key)
    return sorted(set(found))


def validate_maintenance_sidecar(
    payload: Mapping[str, Any],
    *,
    old_world: ConstructionWorld,
    new_world: ConstructionWorld,
    comparison: SpineComparisonResult,
) -> list[str]:
    errors: list[str] = []
    if payload.get("contract") != MAINTENANCE_SCHEMA:
        errors.append("maintenance sidecar contract is not authority_maintenance/v0")
    if payload.get("comparison_id") != comparison.receipt.comparison_id:
        errors.append("maintenance sidecar comparison_id does not match the comparison")
    old_snapshot = str(
        comparison.receipt.snapshots.get("old", {}).get("id")
        or comparison.delta.old_snapshot
    )
    new_snapshot = str(
        comparison.receipt.snapshots.get("new", {}).get("id")
        or comparison.delta.new_snapshot
    )
    if (
        payload.get("old_snapshot") != old_snapshot
        or payload.get("new_snapshot") != new_snapshot
    ):
        errors.append("maintenance sidecar snapshot pair does not match the comparison")
    if snapshot_id(old_world) and snapshot_id(old_world) != old_snapshot:
        errors.append("maintenance old World snapshot does not match the comparison")
    if snapshot_id(new_world) and snapshot_id(new_world) != new_snapshot:
        errors.append("maintenance new World snapshot does not match the comparison")
    warrants = {
        str(row.get("_assertion_id") or "")
        for row in relation_rows_with_ids(old_world, "authority_attachment_warrant")
    }
    new_ids = {str(row["entity"]) for row in new_world.relation_rows("program_entity")}
    for item in payload.get("assessments") or []:
        if str(item.get("warrant_assertion_id") or "") not in warrants:
            errors.append(
                f"maintenance cites unknown warrant {item.get('warrant_assertion_id')}"
            )
        if item.get("persistence_implication") != PERSISTENCE_IMPLICATION:
            errors.append("v0 maintenance omitted NO_RENEWAL")
        if item.get("maintenance_action") not in {"HOLD", "RERESOLVE", "CANNOT_ASSESS"}:
            errors.append(
                f"invalid maintenance_action: {item.get('maintenance_action')}"
            )
        for candidate in item.get("candidate_new_manifestations") or []:
            if candidate not in new_ids:
                errors.append(
                    f"maintenance candidate is not in the new snapshot: {candidate}"
                )
        recorded_kinds = {
            str(dep.get("kind") or "")
            for dep in item.get("dependencies_examined") or []
        }
        if "entity_identity" not in recorded_kinds:
            errors.append("maintenance omitted the attached entity_identity dependency")
        if item.get(
            "correspondence_basis"
        ) == "HEURISTIC" and "HEURISTIC" not in json.dumps(
            item.get("known_uncertainty") or []
        ):
            errors.append("HEURISTIC correspondence was not labeled as such")
    errors.extend(
        f"maintenance contains compliance field {key}"
        for key in compliance_fields(payload)
    )
    return sorted(set(errors))


def validate_impact_sidecar(
    payload: Mapping[str, Any],
    *,
    old_world: ConstructionWorld,
    comparison: SpineComparisonResult,
    maintenance: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if payload.get("contract") != IMPACT_SCHEMA:
        errors.append("impact sidecar contract is not authority_impact/v0")
    if payload.get("comparison_id") != comparison.receipt.comparison_id:
        errors.append("impact sidecar comparison_id does not match the comparison")
    if payload.get("old_snapshot") != maintenance.get("old_snapshot"):
        errors.append("impact sidecar snapshot pair does not match maintenance")
    warrants = {
        str(row.get("_assertion_id") or "")
        for row in relation_rows_with_ids(old_world, "authority_attachment_warrant")
    }
    maint_ids = {
        str(item.get("warrant_assertion_id") or "")
        for item in maintenance.get("assessments") or []
    }
    for item in payload.get("impacts") or []:
        if str(item.get("warrant_assertion_id") or "") not in warrants:
            errors.append(
                f"impact cites unknown warrant {item.get('warrant_assertion_id')}"
            )
        if str(item.get("warrant_assertion_id") or "") not in maint_ids:
            errors.append(
                f"impact warrant was not assessed for maintenance: {item.get('warrant_assertion_id')}"
            )
        if item.get("impact") not in {
            "AFFECTED",
            "UNAFFECTED",
            "UNKNOWN",
            "NOT_COMPARABLE",
        }:
            errors.append(f"invalid impact status: {item.get('impact')}")
        if item.get("scope_source") not in {"PERSISTED", "DEFAULT_KIND_RULE"}:
            errors.append(f"invalid scope_source: {item.get('scope_source')}")
        if not item.get("scope_clauses"):
            errors.append("impact omitted the relevance-scope clauses actually used")
    errors.extend(
        f"impact contains compliance field {key}" for key in compliance_fields(payload)
    )
    return sorted(set(errors))


def validate_case_sidecar(
    payload: Mapping[str, Any],
    *,
    maintenance: Mapping[str, Any],
    impact: Mapping[str, Any],
    comparison: SpineComparisonResult,
) -> list[str]:
    errors: list[str] = []
    if payload.get("contract") != "governance_case/v0":
        errors.append("case sidecar contract is not governance_case/v0")
    if (
        payload.get("change", {}).get("comparison_id")
        != comparison.receipt.comparison_id
    ):
        errors.append("case sidecar comparison_id does not match the comparison")
    if payload.get("case_result") not in {
        "SELECTED",
        "NO_APPLICABLE_AUTHORITY",
        "NO_ATTACHMENT_FOUND",
        "UNRESOLVED",
    }:
        errors.append(f"invalid case_result: {payload.get('case_result')}")
    if payload.get("case_result") == "SELECTED" and not payload.get("selection"):
        errors.append("SELECTED case has no selected attachments")
    if payload.get("case_result") != "SELECTED" and payload.get("selection"):
        errors.append("empty-case result still lists selected attachments")
    maint_ids = {
        item["warrant_assertion_id"] for item in maintenance.get("assessments") or []
    }
    impact_ids = {item["warrant_assertion_id"] for item in impact.get("impacts") or []}
    for item in payload.get("selection") or []:
        warrant_id = str(item.get("warrant_assertion_id") or "")
        if warrant_id not in maint_ids or warrant_id not in impact_ids:
            errors.append(f"case selection cites an unassessed warrant {warrant_id}")
        if not item.get("selected_because"):
            errors.append(f"case selection {warrant_id} omitted selected_because")
    for observation in payload.get("authority", {}).get("observations") or []:
        if observation.get("standing") != "AUTHORITATIVE":
            errors.append("governing authority includes non-AUTHORITATIVE standing")
    authority_ids = {
        str(item.get("observation_id") or "")
        for item in payload.get("authority", {}).get("observations") or []
    }
    for item in payload.get("program_context", {}).get("source_evidence") or []:
        if str(item.get("evidence_id") or "") in authority_ids:
            errors.append(
                "program source evidence id collides with authority observation"
            )
        if item.get("reconstruction") not in {"OK", "FAILED"}:
            errors.append(
                f"invalid program source reconstruction: {item.get('reconstruction')}"
            )
        if item.get("side") not in {"OLD", "NEW", "CANDIDATE"}:
            errors.append(f"invalid program source side: {item.get('side')}")
    semantic_context = payload.get("semantic_context") or {}
    if semantic_context:
        if not isinstance(semantic_context, Mapping):
            errors.append("semantic_context must be an object")
        else:
            for key in ("referents", "claims", "program_links"):
                if not isinstance(semantic_context.get(key, []), list):
                    errors.append(f"semantic_context.{key} must be an array")
            valid_observations = {
                str(item.get("observation_id") or "")
                for container in (
                    payload.get("authority", {}).get("observations") or [],
                    payload.get("supporting_material") or [],
                )
                for item in container
                if isinstance(item, Mapping)
            }
            for item in semantic_context.get("referents") or []:
                if not isinstance(item, Mapping):
                    errors.append("semantic_context referent must be an object")
                    continue
                if not item.get("id"):
                    errors.append("semantic_context referent omitted id")
                if item.get("status") not in SEMANTIC_CONTEXT_STATUSES:
                    errors.append(
                        f"invalid semantic_context referent status: {item.get('status')}"
                    )
                reasons = item.get("included_because") or []
                if not set(reasons).issubset(SEMANTIC_CONTEXT_INCLUSION_REASONS):
                    errors.append(
                        "semantic_context referent has an invalid inclusion reason"
                    )
                if not set(item.get("source_observation_ids") or []).issubset(
                    valid_observations
                ):
                    errors.append(
                        "semantic_context referent cites an unknown observation"
                    )
            for item in semantic_context.get("claims") or []:
                if not isinstance(item, Mapping):
                    errors.append("semantic_context claim must be an object")
                    continue
                if not item.get("assertion_id"):
                    errors.append("semantic_context claim omitted assertion_id")
                reasons = item.get("included_because") or []
                if not set(reasons).issubset(SEMANTIC_CONTEXT_INCLUSION_REASONS):
                    errors.append(
                        "semantic_context claim has an invalid inclusion reason"
                    )
                if not set(item.get("source_observation_ids") or []).issubset(
                    valid_observations
                ):
                    errors.append("semantic_context claim cites an unknown observation")
            for item in semantic_context.get("program_links") or []:
                if not isinstance(item, Mapping):
                    errors.append("semantic_context program link must be an object")
                    continue
                if not item.get("semantic_referent") or not item.get("program_entity"):
                    errors.append("semantic_context program link omitted an endpoint")
                if item.get("status") not in SEMANTIC_CONTEXT_STATUSES:
                    errors.append(
                        f"invalid semantic_context program-link status: {item.get('status')}"
                    )
                reasons = item.get("included_because") or []
                if not set(reasons).issubset(SEMANTIC_CONTEXT_INCLUSION_REASONS):
                    errors.append(
                        "semantic_context program link has an invalid inclusion reason"
                    )
                if not set(item.get("source_observation_ids") or []).issubset(
                    valid_observations
                ):
                    errors.append(
                        "semantic_context program link cites an unknown observation"
                    )
            for item in payload.get("transition_facts") or []:
                if not isinstance(item, Mapping):
                    errors.append("transition fact must be an object")
                    continue
                if item.get("included_because") != ["SELECTED_TRANSITION_FACT"]:
                    errors.append("transition fact has an invalid inclusion reason")
                if not item.get("mechanical_evidence_refs"):
                    errors.append("transition fact omitted mechanical evidence refs")
    invariant_context = payload.get("invariant_context")
    if invariant_context is not None:
        if not isinstance(invariant_context, Mapping):
            errors.append("invariant_context must be an object")
        else:
            definition = invariant_context.get("definition") or {}
            baseline = invariant_context.get("baseline_derivation") or {}
            candidate = invariant_context.get("candidate_derivation") or {}
            if not isinstance(definition, Mapping) or not definition.get("definition_id"):
                errors.append("invariant_context omitted a scoped invariant definition")
            if not isinstance(baseline, Mapping) or not baseline.get("derivation_id"):
                errors.append("invariant_context omitted a baseline derivation")
            if not isinstance(candidate, Mapping) or not candidate.get("derivation_id"):
                errors.append("invariant_context omitted a candidate derivation")
            if (
                isinstance(definition, Mapping)
                and isinstance(baseline, Mapping)
                and isinstance(candidate, Mapping)
                and definition.get("definition_id")
                and (
                    baseline.get("definition_id") != definition.get("definition_id")
                    or candidate.get("definition_id") != definition.get("definition_id")
                )
            ):
                errors.append(
                    "invariant_context derivations do not cite the selected definition"
                )
            if candidate.get("evaluation_receipt", {}).get("model_invoked") is True:
                errors.append("candidate invariant derivation invoked a model")
    errors.extend(
        f"case contains compliance field {key}" for key in compliance_fields(payload)
    )
    return sorted(set(errors))


def assess_authority_governance(
    old_world: ConstructionWorld | Path | str,
    new_world: ConstructionWorld | Path | str,
    comparison: SpineComparisonResult | Path | str,
    sources: Mapping[str, MarkdownSource],
    *,
    output_dir: Path | str | None = None,
    purpose: str = "",
) -> dict[str, Any]:
    """Run maintenance, impact, and case assembly without hiding the stages."""

    maintenance = assess_attachment_maintenance(old_world, new_world, comparison)
    impact = assess_authority_change_impact(
        old_world, new_world, comparison, maintenance=maintenance
    )
    case = assemble_governance_case(
        old_world,
        new_world,
        comparison,
        sources,
        maintenance=maintenance,
        impact=impact,
        purpose=purpose,
    )
    bundle = {"maintenance": maintenance, "impact": impact, "case": case}
    if output_dir is not None:
        write_maintenance(maintenance, output_dir)
        write_impact(impact, output_dir)
        write_case(case, output_dir)
    return bundle
