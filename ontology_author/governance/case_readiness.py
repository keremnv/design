"""Deterministic GovernanceCase readiness: pending vs required construction.

This is a workflow precondition check, not an adjudication and not a
constructor.  It consumes already-detected MembershipGaps and already
synthesized ConstructionObligations.  It does not execute them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ontology_author.semantic_binding.schemas import (
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    ConstructionObligation,
    copy_json,
)
from ontology_author.governance.checkout_invariant import (
    CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
    TRUTH_FALSE,
    TRUTH_TRUE,
    TRUTH_UNKNOWN,
    ScopedInvariantEvaluation,
)
from ontology_author.semantic_binding.membership import GAP_REASON_NO_EVIDENCE, MembershipGap
from ontology_author.governance.obligation_synthesis import (
    PendingConstructionObligations,
    SynthesizedClassMembershipObligation,
    parse_membership_gap,
)

READINESS_PROFILE = "governance-case-readiness/v1"
READINESS_VERSION = 1
STATUS_READY_FOR_ADJUDICATION = "READY_FOR_ADJUDICATION"
STATUS_CONSTRUCTION_REQUIRED = "CONSTRUCTION_REQUIRED"
WORKFLOW_PENDING = "PENDING"
WORKFLOW_REQUIRED = "REQUIRED"
WORKFLOW_DORMANT = "DORMANT"
MATERIALITY_UNKNOWN_BLOCKED_BY_MEMBERSHIP = (
    "UNKNOWN_INVARIANT_BLOCKED_BY_MEMBERSHIP_GAP"
)
MATERIALITY_KNOWN_VIOLATION_DECIDES = "KNOWN_VIOLATION_ALREADY_DECIDES_INVARIANT"
MATERIALITY_INVARIANT_ALREADY_DECIDED = "INVARIANT_RESULT_ALREADY_DECIDED"
EVENTUAL_CONTEXT_REQUIRED = "CONTEXT_REQUIRED"
UNSUPPORTED_NON_MEMBERSHIP_UNKNOWN = "NON_MEMBERSHIP_UNKNOWN"
UNSUPPORTED_GAP_KIND = "UNSUPPORTED_GAP_KIND"
UNSUPPORTED_CONSUMER = "UNSUPPORTED_MATERIALITY_CONSUMER"
SUPPORTED_GAP_REASONS = frozenset({GAP_REASON_NO_EVIDENCE})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _derivation_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return copy_json(value.to_dict())
    payload = _as_mapping(value)
    return copy_json(payload) if payload is not None else {}


def _pending_items(
    pending: PendingConstructionObligations
    | Sequence[SynthesizedClassMembershipObligation | Mapping[str, Any]]
    | None,
) -> tuple[SynthesizedClassMembershipObligation, ...]:
    if pending is None:
        return ()
    if isinstance(pending, PendingConstructionObligations):
        return pending.items
    items: list[SynthesizedClassMembershipObligation] = []
    for item in pending:
        if isinstance(item, SynthesizedClassMembershipObligation):
            items.append(item)
            continue
        payload = _as_mapping(item)
        if payload is None:
            continue
        obligation_payload = payload.get("obligation") or payload
        gap_payload = payload.get("gap") or {}
        items.append(
            SynthesizedClassMembershipObligation(
                obligation=ConstructionObligation.from_dict(obligation_payload),
                gap=MembershipGap.from_dict(gap_payload),
                provenance=dict(payload.get("provenance") or {}),
                construction_context=dict(payload.get("construction_context") or {}),
            )
        )
    return tuple(items)


def _gap_key(gap: MembershipGap) -> tuple[str, str, str]:
    return (gap.semantic_class, gap.program_subject, gap.snapshot)


def _item_key(item: SynthesizedClassMembershipObligation) -> tuple[str, str, str]:
    subject = ""
    if item.obligation.allowed_program_endpoints:
        subject = item.obligation.allowed_program_endpoints[0]
    snapshot = _text(item.construction_context.get("snapshot")) or item.gap.snapshot
    klass = item.obligation.semantic_subject or item.gap.semantic_class
    return (klass, subject or item.gap.program_subject, snapshot)


@dataclass(frozen=True)
class RequiredConstructionObligation:
    """A pending obligation that currently blocks this case."""

    obligation_id: str
    obligation_kind: str
    semantic_class: str
    program_subject: str
    source_gap_id: str
    requested_by: tuple[str, ...]
    materiality_reason: str
    causal_chain: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "obligation_kind": self.obligation_kind,
            "semantic_class": self.semantic_class,
            "program_subject": self.program_subject,
            "source_gap_id": self.source_gap_id,
            "requested_by": list(self.requested_by),
            "materiality_reason": self.materiality_reason,
            "causal_chain": copy_json(self.causal_chain),
            "workflow_state": WORKFLOW_REQUIRED,
        }


@dataclass(frozen=True)
class ConstructionRequired:
    """Bounded required-construction view. Not an adoption decision."""

    required_construction_obligations: tuple[RequiredConstructionObligation, ...]
    eventual_workflow_outcome: str = EVENTUAL_CONTEXT_REQUIRED

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_construction_obligations": [
                item.to_dict() for item in self.required_construction_obligations
            ],
            "eventual_workflow_outcome": self.eventual_workflow_outcome,
            "note": (
                "CONSTRUCTION_REQUIRED may later map to CONTEXT_REQUIRED "
                "without collapsing readiness into adjudication or adoption."
            ),
        }


@dataclass(frozen=True)
class GovernanceCaseReadiness:
    """Deterministic precondition: is this case ready to adjudicate?"""

    status: str
    required_construction_obligations: tuple[RequiredConstructionObligation, ...]
    pending_obligation_ids: tuple[str, ...]
    required_obligation_ids: tuple[str, ...]
    dormant_obligation_ids: tuple[str, ...]
    materiality_consumer: str
    overall_truth: str
    unmatched_material_gaps: tuple[Mapping[str, Any], ...] = ()
    unsupported_reasons: tuple[str, ...] = ()
    construction_required: ConstructionRequired | None = None
    adjudicator_invoked: bool = False
    constructor_invoked: bool = False
    model_invoked: bool = False
    repository_searched: bool = False
    profile: str = READINESS_PROFILE
    version: int = READINESS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "profile": self.profile,
            "version": self.version,
            "required_construction_obligations": [
                item.to_dict() for item in self.required_construction_obligations
            ],
            "pending_obligation_ids": list(self.pending_obligation_ids),
            "required_obligation_ids": list(self.required_obligation_ids),
            "dormant_obligation_ids": list(self.dormant_obligation_ids),
            "materiality_consumer": self.materiality_consumer,
            "overall_truth": self.overall_truth,
            "unmatched_material_gaps": copy_json(list(self.unmatched_material_gaps)),
            "unsupported_reasons": list(self.unsupported_reasons),
            "construction_required": (
                self.construction_required.to_dict()
                if self.construction_required is not None
                else None
            ),
            "adjudicator_invoked": False,
            "constructor_invoked": False,
            "model_invoked": False,
            "repository_searched": False,
            "adjudication_state": None,
            "adoption_outcome": None,
        }

    def construction_context(self) -> dict[str, Any]:
        return {
            "pending_obligation_ids": list(self.pending_obligation_ids),
            "required_obligation_ids": list(self.required_obligation_ids),
            "dormant_obligation_ids": list(self.dormant_obligation_ids),
            "readiness_status": self.status,
            "readiness_profile": self.profile,
        }


def attach_construction_context(
    case: Mapping[str, Any], readiness: GovernanceCaseReadiness
) -> dict[str, Any]:
    """Overlay workflow IDs onto a case copy. Does not change case identity."""

    payload = copy_json(case)
    payload["construction_context"] = readiness.construction_context()
    return payload


def _supported_gaps(
    gaps: Sequence[MembershipGap | Mapping[str, Any] | None],
) -> tuple[list[MembershipGap], tuple[str, ...]]:
    supported: list[MembershipGap] = []
    reasons: list[str] = []
    for item in gaps:
        parsed = parse_membership_gap(item)
        if parsed is None:
            reasons.append(UNSUPPORTED_GAP_KIND)
            continue
        if _text(parsed.reason) not in SUPPORTED_GAP_REASONS:
            reasons.append(UNSUPPORTED_GAP_KIND)
            continue
        if not parsed.semantic_class or not parsed.program_subject:
            reasons.append(UNSUPPORTED_GAP_KIND)
            continue
        supported.append(parsed)
    return supported, tuple(dict.fromkeys(reasons))


def _membership_gaps_are_material(derivation: Mapping[str, Any]) -> bool:
    """checkout-provider-boundary/v1: gaps matter only if they can change truth."""

    evaluator = _text(derivation.get("evaluator_id"))
    if evaluator != CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID:
        return False
    truth = _text(derivation.get("overall_truth")).upper()
    if truth in {TRUTH_FALSE, TRUTH_TRUE}:
        return False
    return truth == TRUTH_UNKNOWN


def _causal_chain(
    *,
    case_id: str,
    derivation: Mapping[str, Any],
    gap: MembershipGap,
    obligation: ConstructionObligation,
    requested_by: Sequence[str],
) -> dict[str, Any]:
    return {
        "governance_case_id": case_id,
        "needs": "ScopedInvariantEvaluation",
        "derivation_id": _text(derivation.get("derivation_id")),
        "definition_id": _text(derivation.get("definition_id")),
        "evaluator_id": _text(derivation.get("evaluator_id")),
        "overall_truth": _text(derivation.get("overall_truth")),
        "unknown_because": {
            "kind": "MembershipGap",
            "gap_id": gap.gap_id,
            "semantic_class": gap.semantic_class,
            "program_subject": gap.program_subject,
            "reason": gap.reason,
        },
        "formulated_as": {
            "kind": CLASS_MEMBERSHIP_OBLIGATION_KIND,
            "obligation_id": obligation.obligation_id,
            "semantic_class": obligation.semantic_subject,
            "program_subject": obligation.allowed_program_endpoints[0]
            if obligation.allowed_program_endpoints
            else "",
        },
        "requested_by": list(requested_by),
        "consumer": CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
    }


def assess_governance_case_readiness(
    *,
    pending_obligations: PendingConstructionObligations
    | Sequence[SynthesizedClassMembershipObligation | Mapping[str, Any]]
    | None = None,
    derivation: ScopedInvariantEvaluation | Mapping[str, Any] | None = None,
    case: Mapping[str, Any] | None = None,
    membership_gaps: Sequence[MembershipGap | Mapping[str, Any] | None] | None = None,
) -> GovernanceCaseReadiness:
    """Select required obligations for one case. Does not formulate or execute.

    Materiality is the checkout-provider-boundary/v1 truth table, not
    obligation kind.  Known FALSE suppresses unrelated membership work.
    """

    case_payload = _as_mapping(case) or {}
    invariant_context = _as_mapping(case_payload.get("invariant_context")) or {}
    derivation_payload = _derivation_payload(derivation)
    if not derivation_payload:
        derivation_payload = _derivation_payload(
            invariant_context.get("candidate_derivation")
        )
    case_id = _text(case_payload.get("case_id"))
    evaluator = _text(derivation_payload.get("evaluator_id"))
    truth = _text(derivation_payload.get("overall_truth")).upper()
    receipt = _as_mapping(derivation_payload.get("evaluation_receipt")) or {}
    raw_gaps = (
        list(membership_gaps)
        if membership_gaps is not None
        else list(receipt.get("membership_gaps") or ())
    )
    supported_gaps, unsupported = _supported_gaps(raw_gaps)
    items = _pending_items(pending_obligations)
    pending_ids = tuple(item.obligation.obligation_id for item in items)
    consumer = evaluator or CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID
    unsupported_reasons = list(unsupported)
    if evaluator and evaluator != CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID:
        unsupported_reasons.append(UNSUPPORTED_CONSUMER)

    material = _membership_gaps_are_material(derivation_payload)
    required: list[RequiredConstructionObligation] = []
    required_ids: list[str] = []
    matched_keys: set[tuple[str, str, str]] = set()
    if material:
        by_key = {_item_key(item): item for item in items}
        for gap in supported_gaps:
            key = _gap_key(gap)
            item = by_key.get(key)
            if item is None:
                continue
            requested = tuple(
                item.provenance.get("requested_by") or ((gap.requested_by,) if gap.requested_by else ())
            )
            required.append(
                RequiredConstructionObligation(
                    obligation_id=item.obligation.obligation_id,
                    obligation_kind=item.obligation.obligation_kind,
                    semantic_class=item.obligation.semantic_subject,
                    program_subject=item.obligation.allowed_program_endpoints[0],
                    source_gap_id=gap.gap_id,
                    requested_by=requested,
                    materiality_reason=MATERIALITY_UNKNOWN_BLOCKED_BY_MEMBERSHIP,
                    causal_chain=_causal_chain(
                        case_id=case_id,
                        derivation=derivation_payload,
                        gap=gap,
                        obligation=item.obligation,
                        requested_by=requested,
                    ),
                )
            )
            required_ids.append(item.obligation.obligation_id)
            matched_keys.add(key)
        unmatched = [
            gap.to_dict()
            for gap in supported_gaps
            if _gap_key(gap) not in matched_keys
        ]
    else:
        unmatched = []

    if truth == TRUTH_UNKNOWN and not supported_gaps:
        unsupported_reasons.append(UNSUPPORTED_NON_MEMBERSHIP_UNKNOWN)

    required_ids_tuple = tuple(dict.fromkeys(required_ids))
    dormant_ids = tuple(
        obligation_id
        for obligation_id in pending_ids
        if obligation_id not in set(required_ids_tuple)
    )
    status = (
        STATUS_CONSTRUCTION_REQUIRED
        if required or unmatched
        else STATUS_READY_FOR_ADJUDICATION
    )
    construction = (
        ConstructionRequired(required_construction_obligations=tuple(required))
        if status == STATUS_CONSTRUCTION_REQUIRED
        else None
    )
    return GovernanceCaseReadiness(
        status=status,
        required_construction_obligations=tuple(required),
        pending_obligation_ids=pending_ids,
        required_obligation_ids=required_ids_tuple,
        dormant_obligation_ids=dormant_ids,
        materiality_consumer=consumer,
        overall_truth=truth,
        unmatched_material_gaps=tuple(unmatched),
        unsupported_reasons=tuple(dict.fromkeys(unsupported_reasons)),
        construction_required=construction,
    )
