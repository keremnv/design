"""Deterministic admission and maintenance for semantic candidates.

Nothing in this module decides whether a semantic proposition is true.  The
admission profile checks only declared obligation shape, bounded evidence,
resolution metadata, scope, completeness, and mechanical maintenance
dependencies.  A constructor cannot supply the admission outcome.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ontology_author.authority.schemas import (
    ClaimKind,
    ReferentResolution,
    RelationSupport,
)
from ontology_author.authority.evaluate import (
    find_relation_bucket,
    relation_rows_with_ids,
)
from ontology_author.authority.evaluate import (
    snapshot_id as authority_snapshot_id,
)
from ontology_author.authority.validation import observations_for_assertion
from ontology_author.program_spine.comparison import SpineComparisonResult
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.commit import (
    _remove_tree,
    _seal_world,
    validate_contract_admission,
)
from ontology_author.world.runtime.world import ConstructionWorld

from .construction import validate_semantic_candidate
from .schemas import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    CLASS_MEMBERSHIP_RELATION,
    CLASS_MEMBERSHIP_TUPLE_SHAPE,
    CONSTRUCTION_OBLIGATION_KIND,
    MAINTENANCE_DEPENDENCY_KINDS,
    PROGRAM_INVARIANT_OBLIGATION_KIND,
    PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
    CandidateValidationError,
    ConstructionObligation,
    PersistenceAdmissionDecision,
    SemanticCandidate,
    SemanticCommitmentWarrant,
    SemanticPersistenceError,
    SemanticPolarity,
    WARRANT_SCHEMA,
    copy_json,
    digest,
    write_json_artifact,
)
from .membership import persist_interpretation_basis

ADMISSION_PROFILE = "semantic-binding/v1"
RELATIONSHIP_ADMISSION_PROFILE = "semantic-program-relationship/v1"
INVARIANT_ADMISSION_PROFILE = "semantic-program-invariant/v1"
MEMBERSHIP_ADMISSION_PROFILE = CLASS_MEMBERSHIP_ADMISSION_PROFILE
ADMISSION_PROFILES = {
    ADMISSION_PROFILE: {"version": 1, "negative_requires_complete": True},
    RELATIONSHIP_ADMISSION_PROFILE: {
        "version": 1,
        "negative_requires_complete": True,
    },
    INVARIANT_ADMISSION_PROFILE: {
        "version": 1,
        "negative_requires_complete": True,
        "positive_requires_complete_universe": True,
    },
    MEMBERSHIP_ADMISSION_PROFILE: {
        "version": 1,
        "negative_requires_complete": False,
        "positive_membership_only": True,
    },
}
WARRANT_RELATION = "semantic_commitment_warrant"
PROGRAM_REALIZATION_RELATION = "semantic_program_realization"
PROGRAM_REALIZATION_RELATION_DESCRIPTION = (
    "Trusted PROGRAM_REALIZATION semantic-to-program binding."
)
PROGRAM_RELATIONSHIP_RELATION = "semantic_payment_access_path"
PROGRAM_RELATIONSHIP_RELATION_DESCRIPTION = (
    "Trusted bounded payment-access mediation relationship."
)
PROGRAM_INVARIANT_RELATION = "semantic_payment_provider_access_invariant"
PROGRAM_INVARIANT_RELATION_DESCRIPTION = (
    "Trusted scoped payment-provider access invariant."
)
PROGRAM_INVARIANT_UNIVERSE_RELATION = (
    "program_provider_access:checkout-payment-scope"
)
PROGRAM_MEMBERSHIP_RELATION = CLASS_MEMBERSHIP_RELATION
PROGRAM_MEMBERSHIP_RELATION_DESCRIPTION = (
    "Trusted CLASS_MEMBERSHIP semantic-class membership for one supplied program manifestation."
)
PROGRAM_INVARIANT_TUPLE_SHAPE = {
    "access": "SEMANTIC",
    "boundary": "SEMANTIC",
    "scope_root": "PROGRAM",
}
PAYMENT_RELATIONSHIP_TUPLE_SHAPE = {
    "access": "SEMANTIC",
    "boundary": "SEMANTIC",
    "checkout_entry": "PROGRAM",
    "service": "PROGRAM",
    "service_call_site": "PROGRAM",
    "gateway": "PROGRAM",
    "gateway_call_site": "PROGRAM",
    "provider": "PROGRAM",
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
_DEPENDENCY_KINDS = MAINTENANCE_DEPENDENCY_KINDS
_STATUS_RANK = {
    "PRESERVED": 0,
    "CHANGED": 1,
    "LOST": 2,
    "UNKNOWN": 3,
    "NOT_COMPARABLE": 4,
}
SELECTION_SCHEMA = "semantic_delta_selection/v0"
# Canonical commitment relations scanned for persisted semantic tuples. This
# matches the read set used by authority case assembly; membership has a
# separate interpretation-basis maintenance path and is not selected here.
SELECTION_COMMITMENT_RELATIONS = (
    PROGRAM_REALIZATION_RELATION,
    PROGRAM_RELATIONSHIP_RELATION,
    PROGRAM_INVARIANT_RELATION,
)


def _as_obligation(
    value: ConstructionObligation | Mapping[str, Any],
) -> ConstructionObligation:
    return (
        value
        if isinstance(value, ConstructionObligation)
        else ConstructionObligation.from_dict(value)
    )


def _as_candidate(value: SemanticCandidate | Mapping[str, Any]) -> SemanticCandidate:
    return (
        value
        if isinstance(value, SemanticCandidate)
        else SemanticCandidate.from_dict(value)
    )


def _catalog_entries(catalog: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [item for item in catalog.get("entries") or [] if isinstance(item, Mapping)]


def _evidence_entries(
    catalog: Mapping[str, Any], reference: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    kind = str(reference.get("kind") or "")
    identifier = str(reference.get("id") or "")
    return [
        item
        for item in _catalog_entries(catalog)
        if str(item.get("kind") or "") == kind
        and str(item.get("id") or "") == identifier
    ]


def _completeness_entry(
    catalog: Mapping[str, Any], identifier: str
) -> Mapping[str, Any] | None:
    for item in _catalog_entries(catalog):
        if (
            item.get("category") == "COMPLETENESS_RECEIPT"
            and str(item.get("id") or "") == identifier
        ):
            return item
    return None


def _matching_complete_scope(
    obligation: ConstructionObligation,
    candidate: SemanticCandidate,
    catalog: Mapping[str, Any],
) -> str | None:
    for identifier in candidate.completeness_refs:
        item = _completeness_entry(catalog, identifier)
        receipt = item.get("receipt") if item else None
        if (
            not isinstance(receipt, Mapping)
            or str(receipt.get("status") or "").upper() != "COMPLETE"
        ):
            continue
        scope_values = {
            str(receipt.get(key) or "")
            for key in ("scope", "universe", "program_scope", "construction_scope")
        }
        if (
            obligation.program_scope in scope_values
            or "SEMANTIC_PROGRAM" in scope_values
        ):
            return identifier
    return None


def _matching_complete_invariant_scope(
    obligation: ConstructionObligation,
    candidate: SemanticCandidate,
    catalog: Mapping[str, Any],
) -> str | None:
    """Require a complete, explicitly enumerated baseline invariant universe."""

    valid_mechanical_ids = {
        str(item.get("id") or "")
        for item in _catalog_entries(catalog)
        if item.get("category") == "MECHANICAL_FACT"
    }
    selected_evidence_ids = {
        str(reference.get("id") or "")
        for reference in candidate.evidence_refs
        if str(reference.get("kind") or "") == "relation_tuple"
    }
    selected_dependency_evidence_ids = {
        str(item.get("evidence_id") or "")
        for item in candidate.maintenance_dependencies
        if str(item.get("evidence_id") or "")
    }
    for identifier in candidate.completeness_refs:
        item = _completeness_entry(catalog, identifier)
        receipt = item.get("receipt") if item else None
        if not isinstance(receipt, Mapping):
            continue
        if str(receipt.get("status") or "").upper() != "COMPLETE":
            continue
        if str(receipt.get("universe") or "") != PROGRAM_INVARIANT_UNIVERSE_RELATION:
            continue
        declared_scope = str(receipt.get("program_scope") or "")
        if declared_scope and declared_scope != obligation.program_scope:
            continue
        members = {
            str(value)
            for value in receipt.get("member_evidence_refs") or []
            if str(value)
        }
        if (
            not members
            or not members.issubset(valid_mechanical_ids)
            or not members.issubset(selected_evidence_ids)
            or not members.issubset(selected_dependency_evidence_ids)
        ):
            continue
        return identifier
    return None


def _evidence_classes(
    candidate: SemanticCandidate, catalog: Mapping[str, Any]
) -> set[str]:
    classes: set[str] = set()
    for reference in candidate.evidence_refs:
        classes.update(
            str(item.get("evidence_class") or "")
            for item in _evidence_entries(catalog, reference)
        )
    return classes


def _has_declared_authority_grounding(
    obligation: ConstructionObligation,
    candidate: SemanticCandidate,
    catalog: Mapping[str, Any],
) -> bool:
    """Require grounding from the authority selected by the obligation."""

    declared = set(obligation.authority_refs)
    for reference in candidate.evidence_refs:
        for item in _evidence_entries(catalog, reference):
            if item.get("category") != "AUTHORITATIVE_EVIDENCE":
                continue
            if str(item.get("kind") or "") == "authority_observation":
                pointer = item.get("pointer")
                handles = {
                    str(item.get("id") or ""),
                    str((pointer or {}).get("native_handle") or "")
                    if isinstance(pointer, Mapping)
                    else "",
                }
                if handles.intersection(declared):
                    return True
                continue
            claim = item.get("persisted_claim")
            if isinstance(claim, Mapping) and declared.intersection(
                str(value) for value in claim.get("source_observation_ids") or []
            ):
                return True
    return False


def _has_program_grounding(
    candidate: SemanticCandidate, catalog: Mapping[str, Any]
) -> bool:
    allowed = {"PROGRAM_SOURCE", "MECHANICAL_FACT"}
    return any(
        item.get("category") in allowed
        for reference in candidate.evidence_refs
        for item in _evidence_entries(catalog, reference)
    )


def _dependency_map(candidate: SemanticCandidate) -> list[Mapping[str, Any]]:
    return [
        item for item in candidate.maintenance_dependencies if isinstance(item, Mapping)
    ]


def _inspectable_dependency(item: Mapping[str, Any]) -> bool:
    kind = str(item.get("kind") or "")
    if kind == "program_identity":
        return bool(str(item.get("program_entity") or ""))
    if kind == "relation_tuple":
        recorded = item.get("recorded")
        return isinstance(recorded, Mapping) and bool(
            str(recorded.get("relation") or "")
        )
    if kind == "structural_context":
        return bool(str(item.get("program_entity") or "")) and isinstance(
            item.get("chain"), list
        )
    if kind == "manifestation_property":
        return bool(str(item.get("program_entity") or "")) and bool(
            str(item.get("property") or "")
        )
    return False


def _decision(
    candidate: SemanticCandidate,
    obligation: ConstructionObligation,
    *,
    outcome: str,
    reason: str,
    evidence_refs: Sequence[Mapping[str, str]] = (),
    completeness_refs: Sequence[str] = (),
    snapshot_id: str = "",
) -> PersistenceAdmissionDecision:
    selected_evidence = tuple(evidence_refs) or candidate.evidence_refs
    selected_completeness = tuple(completeness_refs) or candidate.completeness_refs
    return PersistenceAdmissionDecision(
        candidate_id=candidate.candidate_id,
        obligation_id=obligation.obligation_id,
        outcome=outcome,
        reason=reason,
        admission_profile=obligation.admission_profile,
        evidence_refs=selected_evidence,
        completeness_refs=selected_completeness,
        maintenance_dependency_ids=tuple(
            str(item.get("dependency_id") or "")
            for item in candidate.maintenance_dependencies
        ),
        snapshot_id=snapshot_id,
    )


def admit_semantic_candidate(
    obligation: ConstructionObligation | Mapping[str, Any],
    candidate: SemanticCandidate | Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    snapshot_id: str = "",
) -> PersistenceAdmissionDecision:
    """Apply ``semantic-binding/v1`` without interpreting semantic truth."""

    selected = _as_obligation(obligation)
    value = _as_candidate(candidate)
    if selected.admission_profile not in ADMISSION_PROFILES:
        raise SemanticPersistenceError(
            f"unsupported admission profile: {selected.admission_profile}"
        )
    errors = validate_semantic_candidate(selected, value, catalog)
    if errors:
        raise CandidateValidationError(errors)

    if (
        value.relation_name != selected.semantic_relation
        or selected.semantic_subject not in value.semantic_endpoint_refs
    ):
        return _decision(
            value,
            selected,
            outcome="DROP",
            reason="DOES_NOT_DISCHARGE_OBLIGATION",
            snapshot_id=snapshot_id,
        )
    if value.program_scope != selected.program_scope or not set(
        value.program_endpoint_refs
    ).issubset(set(selected.allowed_program_endpoints)):
        return _decision(
            value,
            selected,
            outcome="DROP",
            reason="OUTSIDE_DECLARED_SCOPE",
            snapshot_id=snapshot_id,
        )
    if value.claim_kind != ClaimKind.SEMANTIC_PROGRAM.value:
        return _decision(
            value,
            selected,
            outcome="DROP",
            reason="DOES_NOT_DISCHARGE_OBLIGATION",
            snapshot_id=snapshot_id,
        )
    if selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND:
        allowed_subject = next(iter(selected.allowed_program_endpoints))
        if value.membership_result == "UNRESOLVED":
            return _decision(
                value,
                selected,
                outcome="RECORD_UNRESOLVED",
                reason="MEMBERSHIP_UNRESOLVED",
                snapshot_id=snapshot_id,
            )
        if value.polarity == SemanticPolarity.NEGATIVE.value:
            return _decision(
                value,
                selected,
                outcome="DROP",
                reason="DOES_NOT_DISCHARGE_OBLIGATION",
                snapshot_id=snapshot_id,
            )
        if (
            value.membership_result != "MEMBER"
            or value.tuple.get("semantic_class") != selected.semantic_subject
            or value.tuple.get("program_manifestation") != allowed_subject
            or set(value.program_endpoint_refs) != {allowed_subject}
            or set(value.semantic_endpoint_refs) != {selected.semantic_subject}
        ):
            return _decision(
                value,
                selected,
                outcome="DROP",
                reason="DOES_NOT_DISCHARGE_OBLIGATION",
                snapshot_id=snapshot_id,
            )
    if any(
        str(value.endpoint_resolution.get(role) or "") not in _CERTAIN_RESOLUTIONS
        for role in selected.tuple_shape
    ):
        return _decision(
            value,
            selected,
            outcome="RECORD_UNRESOLVED",
            reason="AMBIGUOUS_ENDPOINT",
            snapshot_id=snapshot_id,
        )
    if value.support_kind == RelationSupport.HYPOTHESIZED.value:
        return _decision(
            value,
            selected,
            outcome="RECORD_UNRESOLVED",
            reason="HYPOTHESIZED_SUPPORT",
            snapshot_id=snapshot_id,
        )

    classes = _evidence_classes(value, catalog)
    required = set(selected.required_evidence_classes)
    missing = sorted(required - classes)
    if not _has_declared_authority_grounding(selected, value, catalog):
        missing.append("DECLARED_AUTHORITY_GROUNDING")
        missing = sorted(set(missing))
    if missing or not _has_program_grounding(value, catalog):
        reason = (
            "INSUFFICIENT_GROUNDING"
            if not missing
            else "MISSING_EVIDENCE_CLASS:" + ",".join(missing)
        )
        return _decision(
            value,
            selected,
            outcome="RECORD_UNRESOLVED",
            reason=reason,
            snapshot_id=snapshot_id,
        )
    if value.polarity == SemanticPolarity.NEGATIVE.value:
        complete = _matching_complete_scope(selected, value, catalog)
        if complete is None:
            return _decision(
                value,
                selected,
                outcome="RECORD_UNRESOLVED",
                reason="NEGATIVE_WITHOUT_COMPLETE_SCOPE",
                snapshot_id=snapshot_id,
            )
        complete_refs = (complete,)
    else:
        complete_refs = value.completeness_refs

    if (
        selected.obligation_kind == PROGRAM_INVARIANT_OBLIGATION_KIND
        and selected.admission_profile == INVARIANT_ADMISSION_PROFILE
    ):
        complete = _matching_complete_invariant_scope(selected, value, catalog)
        if complete is None:
            return _decision(
                value,
                selected,
                outcome="RECORD_UNRESOLVED",
                reason="UNIVERSAL_WITHOUT_COMPLETE_SCOPE",
                snapshot_id=snapshot_id,
            )
        complete_refs = (complete,)

    dependencies = _dependency_map(value)
    inspectable = bool(dependencies) and all(
        _inspectable_dependency(item) for item in dependencies
    )
    if (
        selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
        and selected.admission_profile == MEMBERSHIP_ADMISSION_PROFILE
    ):
        if inspectable:
            return _decision(
                value,
                selected,
                outcome="PERSIST_COMMITMENT",
                reason="GROUNDED_WITH_INSPECTABLE_MAINTENANCE_DEPENDENCIES",
                evidence_refs=value.evidence_refs,
                completeness_refs=complete_refs,
                snapshot_id=snapshot_id,
            )
        return _decision(
            value,
            selected,
            outcome="RECORD_UNRESOLVED",
            reason="INSUFFICIENT_GROUNDING",
            snapshot_id=snapshot_id,
        )
    if inspectable:
        return _decision(
            value,
            selected,
            outcome="PERSIST_COMMITMENT",
            reason="GROUNDED_WITH_INSPECTABLE_MAINTENANCE_DEPENDENCIES",
            evidence_refs=value.evidence_refs,
            completeness_refs=complete_refs,
            snapshot_id=snapshot_id,
        )
    return _decision(
        value,
        selected,
        outcome="PERSIST_SNAPSHOT_FACT",
        reason="GROUNDED_BUT_NO_INSPECTABLE_MAINTENANCE_DEPENDENCIES",
        evidence_refs=value.evidence_refs,
        completeness_refs=complete_refs,
        snapshot_id=snapshot_id,
    )


def _warrant_relation(world: ConstructionWorld) -> None:
    schema = {
        "assertion_id": Role("assertion_id", RoleType.TEXT),
        "obligation_id": Role("obligation_id", RoleType.TEXT),
        "snapshot_id": Role("snapshot_id", RoleType.TEXT),
        "evidence_refs": Role("evidence_refs", RoleType.TEXT),
        "support_kind": Role("support_kind", RoleType.TEXT),
        "resolution_basis": Role("resolution_basis", RoleType.TEXT),
        "depends_on": Role("depends_on", RoleType.TEXT),
        "admission_profile": Role("admission_profile", RoleType.TEXT),
        "admission_decision_id": Role("admission_decision_id", RoleType.TEXT),
    }
    if WARRANT_RELATION not in {
        str(row["name"]) for row in world.query("SELECT name FROM _world_relations")
    }:
        world.declare_relation(
            WARRANT_RELATION,
            list(schema.values()),
            scope="WORLD",
            description="Semantic commitment maintenance warrant.",
        )


def _observations_for_candidate(
    candidate: SemanticCandidate, catalog: Mapping[str, Any]
) -> tuple[SourceObservation, ...]:
    observations: dict[tuple[str, str, str, str], SourceObservation] = {}
    by_id = {
        str(item.get("id") or ""): item
        for item in _catalog_entries(catalog)
        if str(item.get("id") or "")
    }
    for reference in candidate.evidence_refs:
        for entry in _evidence_entries(catalog, reference):
            pointers: list[Mapping[str, Any]] = []
            pointer = entry.get("pointer")
            if isinstance(pointer, Mapping):
                pointers.append(pointer)
            persisted_claim = entry.get("persisted_claim")
            if isinstance(persisted_claim, Mapping):
                for observation_id in persisted_claim.get(
                    "source_observation_ids"
                ) or []:
                    observation_entry = by_id.get(str(observation_id))
                    if isinstance(observation_entry, Mapping):
                        observation_pointer = observation_entry.get("pointer")
                        if isinstance(observation_pointer, Mapping):
                            pointers.append(observation_pointer)
            for pointer in pointers:
                values = (
                    str(pointer.get("provider") or ""),
                    str(pointer.get("native_handle") or ""),
                    str(pointer.get("source_revision") or ""),
                    str(pointer.get("native_location") or ""),
                )
                if all(values):
                    observations[values] = SourceObservation(*values)
    return tuple(observations[key] for key in sorted(observations))


def canonical_semantic_commitment_schema(
    obligation: ConstructionObligation | Mapping[str, Any],
) -> dict[str, Any]:
    """Return a trusted World relation shape for a supported obligation.

    Relation names and World roles are selected by this application mapping,
    never by a constructor.  The relational experiment intentionally supports
    one exact bounded payment-path shape; it is not a generic graph relation.
    """

    selected = _as_obligation(obligation)
    if (
        selected.obligation_kind == CONSTRUCTION_OBLIGATION_KIND
        and selected.admission_profile == ADMISSION_PROFILE
    ):
        semantic_roles = [
            role for role, kind in selected.tuple_shape.items() if kind == "SEMANTIC"
        ]
        program_roles = [
            role for role, kind in selected.tuple_shape.items() if kind == "PROGRAM"
        ]
        if len(semantic_roles) != 1 or len(program_roles) != 1:
            raise SemanticPersistenceError(
                "PROGRAM_REALIZATION/v1 requires exactly one semantic and one program role"
            )
        return {
            "name": PROGRAM_REALIZATION_RELATION,
            "description": PROGRAM_REALIZATION_RELATION_DESCRIPTION,
            "roles": [
                {"name": "semantic_subject", "type": RoleType.REFERENT.value},
                {"name": "program_manifestation", "type": RoleType.REFERENT.value},
            ],
            "source_roles": {
                "semantic_subject": semantic_roles[0],
                "program_manifestation": program_roles[0],
            },
        }
    if (
        selected.obligation_kind == PROGRAM_RELATIONSHIP_OBLIGATION_KIND
        and selected.admission_profile == RELATIONSHIP_ADMISSION_PROFILE
        and dict(selected.tuple_shape) == PAYMENT_RELATIONSHIP_TUPLE_SHAPE
    ):
        return {
            "name": PROGRAM_RELATIONSHIP_RELATION,
            "description": PROGRAM_RELATIONSHIP_RELATION_DESCRIPTION,
            "roles": [
                {"name": role, "type": RoleType.REFERENT.value}
                for role in PAYMENT_RELATIONSHIP_TUPLE_SHAPE
            ],
            "source_roles": {
                role: role for role in PAYMENT_RELATIONSHIP_TUPLE_SHAPE
            },
        }
    if (
        selected.obligation_kind == PROGRAM_INVARIANT_OBLIGATION_KIND
        and selected.admission_profile == INVARIANT_ADMISSION_PROFILE
        and dict(selected.tuple_shape) == PROGRAM_INVARIANT_TUPLE_SHAPE
    ):
        return {
            "name": PROGRAM_INVARIANT_RELATION,
            "description": PROGRAM_INVARIANT_RELATION_DESCRIPTION,
            "roles": [
                {"name": role, "type": RoleType.REFERENT.value}
                for role in PROGRAM_INVARIANT_TUPLE_SHAPE
            ],
            "source_roles": {
                role: role for role in PROGRAM_INVARIANT_TUPLE_SHAPE
            },
        }
    if (
        selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
        and selected.admission_profile == MEMBERSHIP_ADMISSION_PROFILE
        and dict(selected.tuple_shape) == CLASS_MEMBERSHIP_TUPLE_SHAPE
    ):
        return {
            "name": PROGRAM_MEMBERSHIP_RELATION,
            "description": PROGRAM_MEMBERSHIP_RELATION_DESCRIPTION,
            "roles": [
                {"name": "semantic_class", "type": RoleType.REFERENT.value},
                {"name": "program_manifestation", "type": RoleType.REFERENT.value},
            ],
            "source_roles": {
                "semantic_class": "semantic_class",
                "program_manifestation": "program_manifestation",
            },
        }
    raise SemanticPersistenceError(
        "no trusted semantic commitment relation exists for obligation kind/profile/shape"
    )


def canonical_program_realization_schema(
    obligation: ConstructionObligation | Mapping[str, Any],
) -> dict[str, Any]:
    """Return the trusted World relation shape for PROGRAM_REALIZATION."""

    selected = _as_obligation(obligation)
    if selected.obligation_kind != CONSTRUCTION_OBLIGATION_KIND:
        raise SemanticPersistenceError(
            "canonical program realization requires PROGRAM_REALIZATION"
        )
    return canonical_semantic_commitment_schema(selected)


def _candidate_grounding(
    selected: ConstructionObligation,
    value: SemanticCandidate,
    selected_decision: PersistenceAdmissionDecision,
    catalog: Mapping[str, Any],
) -> AssertionGrounding:
    observations = _observations_for_candidate(value, catalog)
    if not observations:
        raise SemanticPersistenceError(
            "admitted semantic state has no reconstructible source grounding"
        )
    evidence_classes = sorted(_evidence_classes(value, catalog))
    return AssertionGrounding(
        observations=observations,
        construction_method=value.construction_method or "bounded semantic constructor",
        extra={
            "semantic_persistence": selected.admission_profile,
            "obligation_id": selected.obligation_id,
            "candidate_id": value.candidate_id,
            "admission_decision_id": selected_decision.decision_id,
            "support_kind": value.support_kind,
            "evidence_refs": [copy_json(item) for item in value.evidence_refs],
            "evidence_classes": evidence_classes,
        },
    )


def _persist_candidate_assertion(
    world: ConstructionWorld,
    selected: ConstructionObligation,
    value: SemanticCandidate,
    selected_decision: PersistenceAdmissionDecision,
    catalog: Mapping[str, Any],
    *,
    snapshot_id: str,
    relation_name: str,
    tuple_values: Mapping[str, str],
) -> dict[str, Any]:
    if relation_name not in {
        str(row["name"]) for row in world.query("SELECT name FROM _world_relations")
    }:
        raise SemanticPersistenceError(
            f"semantic relation schema is not present: {relation_name}"
        )
    grounding = _candidate_grounding(selected, value, selected_decision, catalog)
    asserted = world.assert_tuple(
        relation_name,
        tuple_values,
        origin=ConstructionOrigin.SEMANTIC,
        grounding=grounding,
    )
    result: dict[str, Any] = {
        "assertion_id": asserted.assertion_id,
        "obligation_id": selected.obligation_id,
        "candidate_id": value.candidate_id,
        "snapshot_id": snapshot_id,
        "outcome": selected_decision.outcome,
        "relation_name": relation_name,
        "tuple": copy_json(tuple_values),
        "grounding": copy_json(grounding.extra or {}),
    }
    if selected_decision.outcome != "PERSIST_COMMITMENT":
        return result
    _warrant_relation(world)
    warrant = SemanticCommitmentWarrant(
        assertion_id=asserted.assertion_id,
        obligation_id=selected.obligation_id,
        snapshot_id=snapshot_id,
        evidence_refs=value.evidence_refs,
        support_kind=value.support_kind,
        resolution_basis=value.endpoint_resolution,
        depends_on=value.maintenance_dependencies,
        admission_profile=selected.admission_profile,
        admission_decision_id=selected_decision.decision_id,
    )
    warrant_row = world.assert_tuple(
        WARRANT_RELATION,
        {
            "assertion_id": warrant.assertion_id,
            "obligation_id": warrant.obligation_id,
            "snapshot_id": warrant.snapshot_id,
            "evidence_refs": json.dumps(warrant.evidence_refs, sort_keys=True),
            "support_kind": warrant.support_kind,
            "resolution_basis": json.dumps(warrant.resolution_basis, sort_keys=True),
            "depends_on": json.dumps(warrant.depends_on, sort_keys=True),
            "admission_profile": warrant.admission_profile,
            "admission_decision_id": warrant.admission_decision_id,
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=grounding,
    )
    result["warrant_id"] = warrant_row.assertion_id
    result["warrant"] = warrant.to_dict()
    if selected.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND:
        result["interpretation_basis"] = persist_interpretation_basis(
            world,
            assertion_id=asserted.assertion_id,
            obligation=selected,
            candidate=value,
            catalog=catalog,
            grounding=grounding,
        )
    return result


def persist_admitted_candidate(
    world: ConstructionWorld,
    obligation: ConstructionObligation | Mapping[str, Any],
    candidate: SemanticCandidate | Mapping[str, Any],
    decision: PersistenceAdmissionDecision | Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    snapshot_id: str,
) -> dict[str, Any] | None:
    """Persist only an admitted fact/commitment into an existing World.

    The relation schema must already exist.  This function does not create an
    ontology relation or a new semantic referent as a side effect.
    """

    selected = _as_obligation(obligation)
    value = _as_candidate(candidate)
    selected_decision = (
        decision
        if isinstance(decision, PersistenceAdmissionDecision)
        else PersistenceAdmissionDecision(**dict(decision))
    )
    if (
        selected_decision.candidate_id != value.candidate_id
        or selected_decision.obligation_id != selected.obligation_id
    ):
        raise SemanticPersistenceError(
            "admission decision does not match candidate and obligation"
        )
    # A caller-supplied decision is an inspectable receipt, not authority to
    # bypass the gate. Recompute the deterministic result before writing any
    # World assertion so a forged/manual PERSIST_* decision cannot admit a
    # candidate that the profile would reject.
    expected_decision = admit_semantic_candidate(
        selected,
        value,
        catalog,
        snapshot_id=snapshot_id,
    )
    if selected_decision.to_dict() != expected_decision.to_dict():
        raise SemanticPersistenceError(
            "admission decision does not match deterministic profile result"
        )
    if selected_decision.outcome not in {"PERSIST_SNAPSHOT_FACT", "PERSIST_COMMITMENT"}:
        return None
    if selected_decision.snapshot_id and selected_decision.snapshot_id != snapshot_id:
        raise SemanticPersistenceError(
            "persistence snapshot differs from admission decision"
        )
    if selected.obligation_kind in {
        PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        PROGRAM_INVARIANT_OBLIGATION_KIND,
        CLASS_MEMBERSHIP_OBLIGATION_KIND,
    }:
        relation = canonical_semantic_commitment_schema(selected)
        relation_name = relation["name"]
        tuple_values = {
            role: value.tuple[source_role]
            for role, source_role in relation["source_roles"].items()
        }
    else:
        relation_name = value.relation_name
        tuple_values = value.tuple
    return _persist_candidate_assertion(
        world,
        selected,
        value,
        selected_decision,
        catalog,
        snapshot_id=snapshot_id,
        relation_name=relation_name,
        tuple_values=tuple_values,
    )


def materialize_semantic_commitment_revision(
    baseline_world: ConstructionWorld | Path | str,
    target_world_dir: Path | str,
    obligation: ConstructionObligation | Mapping[str, Any],
    candidate: SemanticCandidate | Mapping[str, Any],
    decision: PersistenceAdmissionDecision | Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    snapshot_id: str,
) -> dict[str, Any]:
    """Publish a sealed World revision containing one admitted commitment.

    The source bundle is copied to a sibling staging bundle, changed only
    there, validated, sealed, and atomically renamed.  The baseline bundle is
    never opened writable and remains byte-for-byte untouched.
    """

    selected = _as_obligation(obligation)
    value = _as_candidate(candidate)
    selected_decision = (
        decision
        if isinstance(decision, PersistenceAdmissionDecision)
        else PersistenceAdmissionDecision(**dict(decision))
    )
    if selected_decision.candidate_id != value.candidate_id:
        raise SemanticPersistenceError("admission decision does not match candidate")
    expected = admit_semantic_candidate(
        selected, value, catalog, snapshot_id=snapshot_id
    )
    if selected_decision.to_dict() != expected.to_dict():
        raise SemanticPersistenceError(
            "admission decision does not match deterministic profile result"
        )
    if selected_decision.outcome != "PERSIST_COMMITMENT":
        raise SemanticPersistenceError(
            "World materialization requires PERSIST_COMMITMENT"
        )

    source_path = (
        baseline_world.path
        if isinstance(baseline_world, ConstructionWorld)
        else Path(baseline_world)
    )
    source_path = source_path.resolve()
    source_bundle = source_path.parent
    target_bundle = Path(target_world_dir).resolve()
    if not source_path.is_file():
        raise SemanticPersistenceError(f"baseline World database is missing: {source_path}")
    if target_bundle.exists():
        raise SemanticPersistenceError(
            f"target World revision already exists: {target_bundle}"
        )
    if target_bundle == source_bundle:
        raise SemanticPersistenceError("World revision target must differ from baseline")
    target_bundle.parent.mkdir(parents=True, exist_ok=True)
    staging = target_bundle.parent / (
        f".{target_bundle.name}.staging-{uuid.uuid4().hex}"
    )
    if staging.exists():
        _remove_tree(staging)
    shutil.copytree(source_bundle, staging)
    for path in sorted(staging.rglob("*")):
        path.chmod(path.stat().st_mode | (0o700 if path.is_dir() else 0o600))
    staging.chmod(staging.stat().st_mode | 0o700)
    staged_path = staging / source_path.name
    world: ConstructionWorld | None = None
    try:
        world = ConstructionWorld.open(staged_path, read_only=False)
        actual_snapshot = authority_snapshot_id(world)
        if actual_snapshot != snapshot_id:
            raise SemanticPersistenceError(
                f"baseline semantic snapshot mismatch: expected {snapshot_id!r}, "
                f"found {actual_snapshot!r}"
            )
        relation = canonical_semantic_commitment_schema(selected)
        existing = {
            str(row["name"])
            for row in world.query("SELECT name FROM _world_relations")
        }
        if relation["name"] not in existing:
            world.declare_relation(
                relation["name"],
                [
                    Role(item["name"], RoleType(item["type"]))
                    for item in relation["roles"]
                ],
                scope="WORLD",
                description=relation["description"],
            )
        tuple_values = {
            role: value.tuple[source_role]
            for role, source_role in relation["source_roles"].items()
        }
        persisted = _persist_candidate_assertion(
            world,
            selected,
            value,
            selected_decision,
            catalog,
            snapshot_id=snapshot_id,
            relation_name=relation["name"],
            tuple_values=tuple_values,
        )
        report = validate_contract_admission(world)
        if not report.ok:
            raise SemanticPersistenceError(
                "materialized World failed admission validation: "
                + "; ".join(str(item.get("message") or item) for item in report.ungrounded)
            )
        (staging / "world.admission.json").write_text(
            json.dumps(world.admission_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        world.close()
        world = None
        _seal_world(staging)
        staging.rename(target_bundle)
        return {
            **persisted,
            "source_world_dir": str(source_bundle),
            "target_world_dir": str(target_bundle),
            "baseline_snapshot_id": snapshot_id,
            "candidate_snapshot_id": snapshot_id,
            "relation_schema": relation,
            "world_revision": _world_revision(target_bundle / source_path.name),
            "published": True,
        }
    except Exception:
        if world is not None:
            try:
                world.close()
            except (OSError, RuntimeError, sqlite3.Error):
                pass
        if staging.exists():
            _remove_tree(staging)
        raise


def _world_revision(path: Path) -> int:
    world = ConstructionWorld.open(path, read_only=True)
    try:
        rows = world.query("SELECT revision FROM _world_meta WHERE singleton = 1")
        return int(rows[0]["revision"]) if rows else 0
    finally:
        world.close()


def _dependency_status(
    dependency: Mapping[str, Any],
    comparison: SpineComparisonResult,
) -> tuple[str, dict[str, Any]]:
    kind = str(dependency.get("kind") or "")
    entity = str(dependency.get("program_entity") or "")
    if kind == "program_identity" or kind == "structural_context":
        claims = [
            item for item in comparison.correspondences if item.old_entity == entity
        ]
        if len(claims) == 1 and claims[0].continuity == "CONTINUED":
            return "PRESERVED", {
                "kind": kind,
                "old_entity": entity,
                "new_entity": claims[0].new_entity,
            }
        if any(item.continuity == "AMBIGUOUS" for item in claims):
            return "UNKNOWN", {
                "kind": kind,
                "old_entity": entity,
                "reason": "ambiguous correspondence",
            }
        if not claims or any(item.continuity == "UNRESOLVED" for item in claims):
            return "NOT_COMPARABLE", {
                "kind": kind,
                "old_entity": entity,
                "reason": "unresolved correspondence",
            }
        return "LOST", {
            "kind": kind,
            "old_entity": entity,
            "reason": "no continued correspondence",
        }
    if kind == "relation_tuple":
        recorded = dependency.get("recorded")
        if not isinstance(recorded, Mapping):
            return "UNKNOWN", {
                "kind": kind,
                "reason": "relation tuple is not inspectable",
            }
        relation = str(recorded.get("relation") or "")
        bucket, evidence = find_relation_bucket(comparison.delta, relation, recorded)
        status = {
            "preserved": "PRESERVED",
            "retargeted": "CHANGED",
            "removed": "LOST",
            "unresolved": "UNKNOWN",
            "NOT_COMPARABLE": "NOT_COMPARABLE",
        }.get(bucket, "UNKNOWN")
        return status, {
            "kind": kind,
            "relation": relation,
            "bucket": bucket,
            "evidence": copy_json(evidence or {}),
        }
    if kind == "manifestation_property":
        property_name = str(dependency.get("property") or "")
        for item in comparison.delta.manifestations:
            if str(item.get("old_entity") or "") == entity:
                changes = item.get("changes") or {}
                if str(changes.get(property_name) or "") in {
                    "CHANGED",
                    "LOST",
                    "UNKNOWN",
                    "NOT_COMPARABLE",
                }:
                    return {
                        "CHANGED": "CHANGED",
                        "LOST": "LOST",
                        "UNKNOWN": "UNKNOWN",
                        "NOT_COMPARABLE": "NOT_COMPARABLE",
                    }[str(changes[property_name])], {
                        "kind": kind,
                        "old_entity": entity,
                        "property": property_name,
                        "change": changes[property_name],
                    }
                return "PRESERVED", {
                    "kind": kind,
                    "old_entity": entity,
                    "property": property_name,
                    "change": changes.get(property_name),
                }
        return "UNKNOWN", {
            "kind": kind,
            "old_entity": entity,
            "property": property_name,
            "reason": "manifestation not found",
        }
    return "UNKNOWN", {"kind": kind, "reason": "unsupported dependency kind"}


def maintain_semantic_commitment(
    warrant: SemanticCommitmentWarrant | Mapping[str, Any],
    comparison: SpineComparisonResult,
) -> dict[str, Any]:
    """Assess only the mechanical basis of an S0 commitment."""

    value = (
        warrant
        if isinstance(warrant, SemanticCommitmentWarrant)
        else SemanticCommitmentWarrant(
            assertion_id=str(warrant.get("assertion_id") or ""),
            obligation_id=str(warrant.get("obligation_id") or ""),
            snapshot_id=str(warrant.get("snapshot_id") or ""),
            evidence_refs=tuple(warrant.get("evidence_refs") or ()),
            support_kind=str(warrant.get("support_kind") or ""),
            resolution_basis=dict(warrant.get("resolution_basis") or {}),
            depends_on=tuple(warrant.get("depends_on") or ()),
            admission_profile=str(
                warrant.get("admission_profile") or ADMISSION_PROFILE
            ),
            admission_decision_id=str(warrant.get("admission_decision_id") or ""),
        )
    )
    assessments: list[dict[str, Any]] = []
    for dependency in value.depends_on:
        status, evidence = _dependency_status(dependency, comparison)
        assessments.append(
            {
                "dependency": copy_json(dependency),
                "status": status,
                "evidence": evidence,
            }
        )
    status = max(
        (str(item["status"]) for item in assessments),
        key=lambda item: _STATUS_RANK.get(item, 3),
        default="PRESERVED",
    )
    return {
        "contract": "semantic_commitment_maintenance/v0",
        "assertion_id": value.assertion_id,
        "obligation_id": value.obligation_id,
        "snapshot_id": value.snapshot_id,
        "comparison_id": comparison.receipt.comparison_id,
        "status": status,
        "candidate_semantic_status": "ESTABLISHED"
        if status == "PRESERVED"
        else "UNRESOLVED",
        "transferred": False,
        "model_invoked": False,
        "assessments": assessments,
        "known_limitations": [
            "maintenance assesses construction basis only; it does not replace or negate semantic meaning"
        ],
    }


def _warrant_from_row(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Rebuild a persisted warrant mapping, or return None when unreadable."""

    try:
        return {
            "contract": WARRANT_SCHEMA,
            "assertion_id": str(row.get("assertion_id") or ""),
            "obligation_id": str(row.get("obligation_id") or ""),
            "snapshot_id": str(row.get("snapshot_id") or ""),
            "evidence_refs": json.loads(str(row.get("evidence_refs") or "[]")),
            "support_kind": str(row.get("support_kind") or ""),
            "resolution_basis": json.loads(
                str(row.get("resolution_basis") or "{}")
            ),
            "depends_on": json.loads(str(row.get("depends_on") or "[]")),
            "admission_profile": str(row.get("admission_profile") or ""),
            "admission_decision_id": str(
                row.get("admission_decision_id") or ""
            ),
        }
    except (TypeError, ValueError):
        return None


def select_affected_semantic_commitments(
    world: ConstructionWorld,
    comparison: SpineComparisonResult,
) -> dict[str, Any]:
    """Select persisted commitments whose maintenance basis is not preserved.

    This is a read-only projection over a sealed World plus a ProgramDelta
    comparison. It never invents, transfers, or re-resolves semantic claims:
    each persisted ``SemanticCommitmentWarrant`` is evaluated with
    :func:`maintain_semantic_commitment`, and only non-``PRESERVED`` results
    are selected. ``UNKNOWN`` and ``NOT_COMPARABLE`` surface explicitly.
    """

    relation_names = {
        str(row["name"]) for row in world.query("SELECT name FROM _world_relations")
    }
    warrant_rows = (
        world.relation_rows(WARRANT_RELATION)
        if WARRANT_RELATION in relation_names
        else []
    )
    commitments: dict[str, tuple[str, dict[str, Any]]] = {}
    for relation_name in SELECTION_COMMITMENT_RELATIONS:
        if relation_name not in relation_names:
            continue
        for item in relation_rows_with_ids(world, relation_name):
            key = str(item.get("_assertion_id") or "")
            if key:
                commitments[key] = (
                    relation_name,
                    {
                        name: value
                        for name, value in item.items()
                        if name != "_assertion_id"
                    },
                )
    selected: list[dict[str, Any]] = []
    for row in sorted(warrant_rows, key=lambda item: str(item.get("assertion_id") or "")):
        assertion_id = str(row.get("assertion_id") or "")
        warrant = _warrant_from_row(row)
        record = commitments.get(assertion_id)
        if warrant is None or record is None:
            selected.append(
                {
                    "assertion_id": assertion_id,
                    "relation_name": (
                        record[0] if record is not None else ""
                    ),
                    "tuple": copy_json(record[1]) if record is not None else {},
                    "snapshot_id": str(row.get("snapshot_id") or ""),
                    "maintenance": {
                        "status": "UNKNOWN",
                        "reason": (
                            "persisted warrant is unreadable"
                            if warrant is None
                            else "persisted commitment tuple is absent"
                        ),
                        "transferred": False,
                        "model_invoked": False,
                        "assessments": [],
                    },
                    "warrant": None,
                    "observations": [],
                }
            )
            continue
        maintenance = maintain_semantic_commitment(warrant, comparison)
        if maintenance["status"] == "PRESERVED":
            continue
        relation_name, semantic_tuple = record
        selected.append(
            {
                "assertion_id": assertion_id,
                "relation_name": relation_name,
                "tuple": copy_json(semantic_tuple),
                "snapshot_id": warrant["snapshot_id"],
                "maintenance": maintenance,
                "warrant": copy_json(warrant),
                "observations": [
                    observation.as_pointer()
                    for observation in observations_for_assertion(
                        world, assertion_id
                    )
                ],
            }
        )
    return {
        "schema": SELECTION_SCHEMA,
        "world_snapshot_id": authority_snapshot_id(world),
        "comparison_id": comparison.receipt.comparison_id,
        "warrants_considered": len(warrant_rows),
        "commitments_found": len(commitments),
        "selected": selected,
    }


def create_lazy_reresolution_obligation(
    original: ConstructionObligation | Mapping[str, Any],
    *,
    candidate_program_endpoints: Sequence[str],
    question: str,
    explicit_request: bool = False,
) -> ConstructionObligation:
    """Create a new bounded obligation only after an explicit request."""

    if not explicit_request:
        raise SemanticPersistenceError(
            "lazy re-resolution requires an explicit request"
        )
    base = _as_obligation(original)
    endpoints = tuple(
        sorted({str(item) for item in candidate_program_endpoints if str(item)})
    )
    if not endpoints:
        raise SemanticPersistenceError(
            "lazy re-resolution needs a candidate program endpoint"
        )
    return ConstructionObligation(
        obligation_id=digest(
            {"base": base.obligation_id, "endpoints": endpoints, "question": question},
            "obligation",
        ),
        purpose=base.purpose,
        authority_refs=base.authority_refs,
        semantic_subject=base.semantic_subject,
        semantic_relation=base.semantic_relation,
        question=question,
        program_scope=base.program_scope,
        allowed_program_endpoints=endpoints,
        required_evidence_classes=base.required_evidence_classes,
        tuple_shape=base.tuple_shape,
        admission_profile=base.admission_profile,
    )


def write_admission_decision(
    decision: PersistenceAdmissionDecision | Mapping[str, Any], output_dir: Path | str
) -> Path:
    payload = (
        decision.to_dict()
        if isinstance(decision, PersistenceAdmissionDecision)
        else dict(decision)
    )
    return write_json_artifact(payload, Path(output_dir) / "persistence.admission.json")


__all__ = [
    "ADMISSION_PROFILE",
    "ADMISSION_PROFILES",
    "PAYMENT_RELATIONSHIP_TUPLE_SHAPE",
    "PROGRAM_REALIZATION_RELATION",
    "PROGRAM_RELATIONSHIP_RELATION",
    "PROGRAM_MEMBERSHIP_RELATION",
    "MEMBERSHIP_ADMISSION_PROFILE",
    "RELATIONSHIP_ADMISSION_PROFILE",
    "WARRANT_RELATION",
    "admit_semantic_candidate",
    "canonical_program_realization_schema",
    "canonical_semantic_commitment_schema",
    "create_lazy_reresolution_obligation",
    "maintain_semantic_commitment",
    "materialize_semantic_commitment_revision",
    "persist_admitted_candidate",
    "write_admission_decision",
]
