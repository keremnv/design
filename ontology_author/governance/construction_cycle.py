"""One semantic-construction cycle: execute at most one required obligation.

This is incremental semantic acquisition, not a scheduler. One invocation
classifies currently required obligations, may execute exactly one authorized
construction, and then stops. Remaining work is reconsidered only by a later
explicit cycle after readiness is recomputed.

Canonical selection sorts by ``obligation_id`` for reproducibility only. It is
not a claim that the selected obligation is more important, more likely to
resolve the case, or semantically preferable. Selection does not inspect
source text, model confidence, endpoint names, likely truth value, token cost,
or semantic content.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ontology_author.semantic_binding.schemas import (
    ConstructionObligation,
    copy_json,
)
from ontology_author.governance.obligation_synthesis import (
    PendingConstructionObligations,
)

from .construction_execution import (
    ACTION_DEFER,
    ACTION_EXECUTE,
    ACTION_REQUIRE_APPROVAL,
    RESULT_CANDIDATE_PRODUCED,
    RESULT_SEMANTICALLY_UNRESOLVED,
    RESOURCE_AVAILABLE,
    ConstructionExecutionDecision,
    ConstructionExecutionPolicy,
    ConstructionExecutionResult,
    decide_construction_execution,
    execute_construction_obligation,
    required_obligations_for_execution,
)

CYCLE_SCHEMA = "semantic_construction_cycle/v0"
CYCLE_NO_CONSTRUCTION_REQUIRED = "NO_CONSTRUCTION_REQUIRED"
CYCLE_CONSTRUCTION_ATTEMPTED = "CONSTRUCTION_ATTEMPTED"
CYCLE_APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
CYCLE_DEFERRED = "DEFERRED"

NEXT_ADJUDICATION = "ADJUDICATION"
NEXT_CONSTRUCTION = "CONSTRUCTION"
NEXT_STOP = "STOP"

ELIGIBILITY_AUTO_EXECUTABLE = "AUTO_EXECUTABLE"
ELIGIBILITY_APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
ELIGIBILITY_DEFERRED = "DEFERRED"
ELIGIBILITY_PREVIOUSLY_UNRESOLVED = "PREVIOUSLY_UNRESOLVED"

REASON_READY = "READY_FOR_ADJUDICATION"
REASON_CANONICAL_AUTO_EXECUTABLE = "CANONICAL_OBLIGATION_ID_ORDER"
REASON_ALL_APPROVAL_REQUIRED = "NO_AUTO_EXECUTABLE_REQUIRED_OBLIGATION"
REASON_ALL_DEFERRED = "NO_EXECUTABLE_OR_APPROVAL_CAPABLE_REQUIRED_OBLIGATION"
REASON_PREVIOUSLY_UNRESOLVED = "PREVIOUSLY_UNRESOLVED_SAME_BASIS"
REASON_UNRESOLVED_STOPS_CYCLE = "SEMANTICALLY_UNRESOLVED_STOPS_CYCLE"
REASON_FAILURE_STOPS_CYCLE = "EXECUTION_FAILED_STOPS_CYCLE"
REASON_ADMISSION_NOT_COMMITMENT = "ADMISSION_DID_NOT_PERSIST_COMMITMENT"
REASON_PUBLISHED_AND_REEVALUATED = "PUBLISHED_AND_REEVALUATED"

CANONICAL_SELECTION_NOTE = (
    "This ordering is for reproducibility only. It is not a claim that this "
    "obligation is more important, more likely to resolve the case, or "
    "semantically preferable."
)


@dataclass(frozen=True)
class PreviousUnresolvedAttempt:
    """Same-basis UNRESOLVED provenance supplied to a cycle. Not a retry ledger."""

    obligation_id: str
    construction_profile: str
    material_basis: str
    result: str = RESULT_SEMANTICALLY_UNRESOLVED

    def matches(self, obligation: ConstructionObligation, material_basis: str) -> bool:
        return (
            self.result == RESULT_SEMANTICALLY_UNRESOLVED
            and self.obligation_id == obligation.obligation_id
            and self.construction_profile == obligation.admission_profile
            and self.material_basis == str(material_basis or "")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "construction_profile": self.construction_profile,
            "material_basis": self.material_basis,
            "result": self.result,
        }


def _previous_attempts(
    values: Sequence[PreviousUnresolvedAttempt | Mapping[str, Any]] | None,
) -> tuple[PreviousUnresolvedAttempt, ...]:
    if not values:
        return ()
    items: list[PreviousUnresolvedAttempt] = []
    for value in values:
        if isinstance(value, PreviousUnresolvedAttempt):
            items.append(value)
            continue
        items.append(
            PreviousUnresolvedAttempt(
                obligation_id=str(value.get("obligation_id") or ""),
                construction_profile=str(value.get("construction_profile") or ""),
                material_basis=str(value.get("material_basis") or ""),
                result=str(value.get("result") or RESULT_SEMANTICALLY_UNRESOLVED),
            )
        )
    return tuple(items)


@dataclass(frozen=True)
class ObligationEligibility:
    """Per-obligation execution classification. Does not mutate the obligation."""

    obligation_id: str
    eligibility: str
    action: str
    reason: str
    execution_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "eligibility": self.eligibility,
            "action": self.action,
            "reason": self.reason,
            "execution_authority": self.execution_authority,
        }


@dataclass(frozen=True)
class SemanticConstructionCycleResult:
    """Outcome of one incremental semantic-acquisition cycle.

    CONSTRUCTION_ATTEMPTED means at most one constructor ran. It does not
    encode semantic truth.
    """

    status: str
    reason: str
    selected_obligation_id: str = ""
    required_before: tuple[str, ...] = ()
    required_after: tuple[str, ...] = ()
    dormant_before: tuple[str, ...] = ()
    dormant_after: tuple[str, ...] = ()
    pending_before: tuple[str, ...] = ()
    pending_after: tuple[str, ...] = ()
    readiness_before: Mapping[str, Any] | None = None
    readiness_after: Mapping[str, Any] | None = None
    eligibility: tuple[ObligationEligibility, ...] = ()
    execution_decision: ConstructionExecutionDecision | None = None
    execution_result: ConstructionExecutionResult | None = None
    admission_result: Mapping[str, Any] | None = None
    published_world_revision: str = ""
    next: str = NEXT_STOP
    candidate_changed: bool = False
    constructor_attempts: int = 0
    contract: str = CYCLE_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_changed", False)
        if self.readiness_before is not None:
            object.__setattr__(self, "readiness_before", copy_json(self.readiness_before))
        if self.readiness_after is not None:
            object.__setattr__(self, "readiness_after", copy_json(self.readiness_after))
        if self.admission_result is not None:
            object.__setattr__(self, "admission_result", copy_json(self.admission_result))

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "status": self.status,
            "reason": self.reason,
            "selected_obligation_id": self.selected_obligation_id,
            "required_before": list(self.required_before),
            "required_after": list(self.required_after),
            "dormant_before": list(self.dormant_before),
            "dormant_after": list(self.dormant_after),
            "pending_before": list(self.pending_before),
            "pending_after": list(self.pending_after),
            "readiness_before": copy_json(self.readiness_before)
            if self.readiness_before is not None
            else None,
            "readiness_after": copy_json(self.readiness_after)
            if self.readiness_after is not None
            else None,
            "eligibility": [item.to_dict() for item in self.eligibility],
            "execution_decision_id": (
                self.execution_decision.decision_id
                if self.execution_decision is not None
                else ""
            ),
            "execution_decision": (
                self.execution_decision.to_dict()
                if self.execution_decision is not None
                else None
            ),
            "execution_result": (
                self.execution_result.to_dict()
                if self.execution_result is not None
                else None
            ),
            "admission_result": copy_json(self.admission_result)
            if self.admission_result is not None
            else None,
            "published_world_revision": self.published_world_revision,
            "next": self.next,
            "candidate_changed": False,
            "constructor_attempts": self.constructor_attempts,
            "canonical_selection_note": CANONICAL_SELECTION_NOTE,
        }


def select_canonical_obligation(
    obligations: Sequence[ConstructionObligation],
) -> ConstructionObligation | None:
    """Pick one obligation by sorting ``obligation_id``.

    This ordering is for reproducibility only. It is not semantic ranking.
    """

    if not obligations:
        return None
    return sorted(obligations, key=lambda item: item.obligation_id)[0]


def _next_from_readiness(readiness: Mapping[str, Any] | None) -> str:
    status = str((readiness or {}).get("status") or "")
    if status == "READY_FOR_ADJUDICATION":
        return NEXT_ADJUDICATION
    if status == "CONSTRUCTION_REQUIRED":
        return NEXT_CONSTRUCTION
    return NEXT_STOP


def classify_required_obligations(
    required: Sequence[ConstructionObligation],
    *,
    policy: ConstructionExecutionPolicy,
    resource_permission: str = RESOURCE_AVAILABLE,
    previous_unresolved: Sequence[PreviousUnresolvedAttempt | Mapping[str, Any]] = (),
    material_basis: str = "",
) -> tuple[ObligationEligibility, ...]:
    """Classify each required obligation independently. Does not execute."""

    prior = _previous_attempts(previous_unresolved)
    classified: list[ObligationEligibility] = []
    for obligation in required:
        decision = decide_construction_execution(
            [obligation],
            policy=policy,
            resource_permission=resource_permission,
        )
        if any(item.matches(obligation, material_basis) for item in prior):
            classified.append(
                ObligationEligibility(
                    obligation_id=obligation.obligation_id,
                    eligibility=ELIGIBILITY_PREVIOUSLY_UNRESOLVED,
                    action=ACTION_DEFER,
                    reason=REASON_PREVIOUSLY_UNRESOLVED,
                    execution_authority=decision.execution_authority,
                )
            )
            continue
        if decision.action == ACTION_EXECUTE:
            eligibility = ELIGIBILITY_AUTO_EXECUTABLE
        elif decision.action == ACTION_REQUIRE_APPROVAL:
            eligibility = ELIGIBILITY_APPROVAL_REQUIRED
        else:
            eligibility = ELIGIBILITY_DEFERRED
        classified.append(
            ObligationEligibility(
                obligation_id=obligation.obligation_id,
                eligibility=eligibility,
                action=decision.action,
                reason=decision.reason,
                execution_authority=decision.execution_authority,
            )
        )
    return tuple(classified)


def _snapshot_ids(readiness: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(readiness.get("required_obligation_ids") or ()),
        tuple(readiness.get("dormant_obligation_ids") or ()),
        tuple(readiness.get("pending_obligation_ids") or ()),
    )


def _assess(
    *,
    case: Mapping[str, Any],
    derivation: Any,
    pending_obligations: Any,
):
    from ontology_author.governance.case_readiness import assess_governance_case_readiness

    return assess_governance_case_readiness(
        pending_obligations=pending_obligations,
        derivation=derivation,
        case=case,
    )


def _reevaluate(
    *,
    candidate_world: Any,
    definition: Any,
    governed_world: Any,
    membership_source_by_handle: Mapping[str, str] | None,
    membership_authority_by_handle: Mapping[str, str] | None,
    case: Mapping[str, Any],
    baseline_derivation: Any,
):
    from ontology_author.governance.checkout_invariant import (
        evaluate_checkout_provider_boundary,
        invariant_context_for_case,
    )
    from ontology_author.governance.obligation_synthesis import (
        context_from_invariant_definition,
        pending_class_membership_obligations_from_derivation,
    )

    derivation = evaluate_checkout_provider_boundary(
        candidate_world,
        definition,
        membership_prior_world=governed_world,
        membership_source_by_handle=membership_source_by_handle,
        membership_authority_by_handle=membership_authority_by_handle,
    )
    pending = pending_class_membership_obligations_from_derivation(
        derivation, context_from_invariant_definition(definition)
    )
    refreshed_case = copy_json(case)
    refreshed_case["invariant_context"] = invariant_context_for_case(
        definition, baseline=baseline_derivation, candidate=derivation
    )
    readiness = _assess(
        case=refreshed_case, derivation=derivation, pending_obligations=pending
    )
    return derivation, pending, readiness


def advance_semantic_construction_cycle(
    *,
    case: Mapping[str, Any],
    derivation: Any,
    pending_obligations: PendingConstructionObligations | Sequence[Any],
    policy: ConstructionExecutionPolicy,
    resource_permission: str = RESOURCE_AVAILABLE,
    constructor: Any | None = None,
    construction_inputs: Callable[[ConstructionObligation], Mapping[str, Any]]
    | None = None,
    previous_unresolved: Sequence[PreviousUnresolvedAttempt | Mapping[str, Any]] = (),
    material_basis: str = "",
    candidate_world: Any | None = None,
    governed_world: Any | None = None,
    definition: Any | None = None,
    baseline_derivation: Any | None = None,
    membership_source_by_handle: Mapping[str, str] | None = None,
    membership_authority_by_handle: Mapping[str, str] | None = None,
    publication_dir: Path | str | None = None,
    constructor_metadata: Mapping[str, Any] | None = None,
    execution_authorization: Any | None = None,
    consumed_approval_ids: Sequence[str] = (),
) -> SemanticConstructionCycleResult:
    """Perform at most one authorized semantic construction, then stop.

    The call never recursively continues into another obligation. After a
    published commitment it recomputes readiness for the same candidate.
    """

    readiness = _assess(
        case=case, derivation=derivation, pending_obligations=pending_obligations
    )
    readiness_payload = readiness.to_dict()
    required_before, dormant_before, pending_before = _snapshot_ids(readiness_payload)
    if readiness.status != "CONSTRUCTION_REQUIRED":
        return SemanticConstructionCycleResult(
            status=CYCLE_NO_CONSTRUCTION_REQUIRED,
            reason=REASON_READY,
            required_before=required_before,
            required_after=required_before,
            dormant_before=dormant_before,
            dormant_after=dormant_before,
            pending_before=pending_before,
            pending_after=pending_before,
            readiness_before=readiness_payload,
            readiness_after=readiness_payload,
            next=NEXT_ADJUDICATION,
        )

    required = required_obligations_for_execution(pending_obligations, readiness)
    classified = classify_required_obligations(
        required,
        policy=policy,
        resource_permission=resource_permission,
        previous_unresolved=previous_unresolved,
        material_basis=material_basis,
    )
    auto_ids = {
        item.obligation_id
        for item in classified
        if item.eligibility == ELIGIBILITY_AUTO_EXECUTABLE
    }
    auto_obligations = [
        obligation for obligation in required if obligation.obligation_id in auto_ids
    ]
    selected = select_canonical_obligation(auto_obligations)
    decision = None
    if selected is None:
        approval_obligations = [
            obligation
            for obligation in required
            if any(
                item.obligation_id == obligation.obligation_id
                and item.eligibility == ELIGIBILITY_APPROVAL_REQUIRED
                for item in classified
            )
        ]
        if approval_obligations:
            requested = select_canonical_obligation(approval_obligations)
            requested_decision = decide_construction_execution(
                [requested],
                policy=policy,
                resource_permission=resource_permission,
            )
            from .construction_approval import (
                AUTHORIZATION_AUTHORIZED,
                ConstructionExecutionAuthorization,
            )

            authorized = (
                isinstance(execution_authorization, ConstructionExecutionAuthorization)
                and execution_authorization.status == AUTHORIZATION_AUTHORIZED
                and execution_authorization.obligation_id == requested.obligation_id
                and execution_authorization.execution_decision_id
                == requested_decision.decision_id
            )
            if authorized:
                selected = requested
                decision = requested_decision
            else:
                return SemanticConstructionCycleResult(
                    status=CYCLE_APPROVAL_REQUIRED,
                    reason=REASON_ALL_APPROVAL_REQUIRED,
                    selected_obligation_id=requested.obligation_id,
                    required_before=required_before,
                    required_after=required_before,
                    dormant_before=dormant_before,
                    dormant_after=dormant_before,
                    pending_before=pending_before,
                    pending_after=pending_before,
                    readiness_before=readiness_payload,
                    readiness_after=readiness_payload,
                    eligibility=classified,
                    execution_decision=requested_decision,
                    next=NEXT_STOP,
                )
        else:
            previously = any(
                item.eligibility == ELIGIBILITY_PREVIOUSLY_UNRESOLVED
                for item in classified
            )
            return SemanticConstructionCycleResult(
                status=CYCLE_DEFERRED,
                reason=(
                    REASON_PREVIOUSLY_UNRESOLVED if previously else REASON_ALL_DEFERRED
                ),
                required_before=required_before,
                required_after=required_before,
                dormant_before=dormant_before,
                dormant_after=dormant_before,
                pending_before=pending_before,
                pending_after=pending_before,
                readiness_before=readiness_payload,
                readiness_after=readiness_payload,
                eligibility=classified,
                next=NEXT_STOP,
            )

    if decision is None:
        decision = decide_construction_execution(
            [selected],
            policy=policy,
            resource_permission=resource_permission,
        )
    inputs = dict(construction_inputs(selected) if construction_inputs is not None else {})
    inputs.setdefault("case", case)
    executed = execute_construction_obligation(
        selected,
        decision,
        constructor=constructor,
        constructor_metadata=constructor_metadata,
        execution_authorization=execution_authorization,
        consumed_approval_ids=consumed_approval_ids,
        **{
            key: value
            for key, value in inputs.items()
            if key
            in {
                "case",
                "bounded_program_source",
                "maintenance_dependencies",
                "completeness_receipts",
                "program_endpoint_kinds",
                "output_dir",
            }
        },
    )
    attempts = executed.invocation_count
    if executed.status != RESULT_CANDIDATE_PRODUCED:
        reason = (
            REASON_UNRESOLVED_STOPS_CYCLE
            if executed.status == RESULT_SEMANTICALLY_UNRESOLVED
            else REASON_FAILURE_STOPS_CYCLE
        )
        return SemanticConstructionCycleResult(
            status=CYCLE_CONSTRUCTION_ATTEMPTED,
            reason=reason,
            selected_obligation_id=selected.obligation_id,
            required_before=required_before,
            required_after=required_before,
            dormant_before=dormant_before,
            dormant_after=dormant_before,
            pending_before=pending_before,
            pending_after=pending_before,
            readiness_before=readiness_payload,
            readiness_after=readiness_payload,
            eligibility=classified,
            execution_decision=decision,
            execution_result=executed,
            next=NEXT_STOP,
            constructor_attempts=attempts,
        )

    from ontology_author.authority.evaluate import snapshot_id as world_snapshot_id
    from ontology_author.semantic_binding.admission import (
        admit_semantic_candidate,
        materialize_semantic_commitment_revision,
    )

    snapshot_world = governed_world if governed_world is not None else candidate_world
    snapshot = world_snapshot_id(snapshot_world) if snapshot_world is not None else ""
    admitted = admit_semantic_candidate(
        selected,
        executed.candidate,
        executed.catalog,
        snapshot_id=snapshot,
    )
    if admitted.outcome != "PERSIST_COMMITMENT":
        return SemanticConstructionCycleResult(
            status=CYCLE_CONSTRUCTION_ATTEMPTED,
            reason=REASON_ADMISSION_NOT_COMMITMENT,
            selected_obligation_id=selected.obligation_id,
            required_before=required_before,
            required_after=required_before,
            dormant_before=dormant_before,
            dormant_after=dormant_before,
            pending_before=pending_before,
            pending_after=pending_before,
            readiness_before=readiness_payload,
            readiness_after=readiness_payload,
            eligibility=classified,
            execution_decision=decision,
            execution_result=executed,
            admission_result=admitted.to_dict(),
            next=NEXT_STOP,
            constructor_attempts=attempts,
        )

    published_path = ""
    readiness_after_payload = readiness_payload
    required_after, dormant_after, pending_after = (
        required_before,
        dormant_before,
        pending_before,
    )
    if publication_dir is not None and snapshot_world is not None:
        materialize_semantic_commitment_revision(
            snapshot_world,
            publication_dir,
            selected,
            executed.candidate,
            admitted,
            executed.catalog,
            snapshot_id=snapshot,
        )
        published_path = str(publication_dir)
        from ontology_author.world.runtime.world import ConstructionWorld

        revised = ConstructionWorld.open(
            Path(publication_dir) / Path(snapshot_world.path).name, read_only=True
        )
        try:
            _after_derivation, _after_pending, after_readiness = _reevaluate(
                candidate_world=candidate_world if candidate_world is not None else snapshot_world,
                definition=definition,
                governed_world=revised,
                membership_source_by_handle=membership_source_by_handle,
                membership_authority_by_handle=membership_authority_by_handle,
                case=case,
                baseline_derivation=baseline_derivation
                if baseline_derivation is not None
                else derivation,
            )
            readiness_after_payload = after_readiness.to_dict()
            required_after, dormant_after, pending_after = _snapshot_ids(
                readiness_after_payload
            )
        finally:
            revised.close()

    return SemanticConstructionCycleResult(
        status=CYCLE_CONSTRUCTION_ATTEMPTED,
        reason=REASON_PUBLISHED_AND_REEVALUATED,
        selected_obligation_id=selected.obligation_id,
        required_before=required_before,
        required_after=required_after,
        dormant_before=dormant_before,
        dormant_after=dormant_after,
        pending_before=pending_before,
        pending_after=pending_after,
        readiness_before=readiness_payload,
        readiness_after=readiness_after_payload,
        eligibility=classified,
        execution_decision=decision,
        execution_result=executed,
        admission_result=admitted.to_dict(),
        published_world_revision=published_path,
        next=_next_from_readiness(readiness_after_payload),
        constructor_attempts=attempts,
    )
