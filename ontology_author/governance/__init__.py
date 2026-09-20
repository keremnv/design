"""Small governance-side checks over the generic Ontology Author substrate.

This module deliberately does not change World storage. It gives governance
construction code a vocabulary for identity planes and for the finer support
metadata that generic ``ConstructionOrigin`` cannot carry by itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ontology_author.world.core.source import AssertionGrounding, SourceObservation

from .adjudication import (
    ADJUDICATION_SCHEMA,
    AdjudicationError,
    create_governance_adjudication,
    load_governance_adjudication,
    validate_governance_adjudication,
    write_governance_adjudication,
)
from .candidate import (
    ADOPTION_DECISION_SCHEMA,
    ADOPTION_OUTCOMES,
    ADOPTION_POLICY_SCHEMA,
    REVISION_BRIEF_SCHEMA,
    CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT,
    CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION,
    REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT,
    REASON_REQUIRED_SEMANTIC_CONSTRUCTION,
    AdoptionPolicy,
    BaselineBindingError,
    CandidateAdoptionDecision,
    CandidateEvaluation,
    CandidateEvaluationError,
    CandidateEvaluationResult,
    GitRepository,
    GitResolutionError,
    GitSnapshot,
    build_governance_revision_brief,
    decide_candidate_adoption,
    decide_semantic_construction_required,
    evaluate_candidate,
    evaluate_git_candidate,
    validate_candidate_adoption_decision,
    write_candidate_adoption,
    write_governance_revision_brief,
)
from .case_lifecycle import (
    GovernedCaseEvaluationResult,
    evaluate_assembled_candidate_case,
)
from .construction_execution import (
    ACTION_DEFER,
    ACTION_EXECUTE,
    ACTION_REQUIRE_APPROVAL,
    AUTHORITY_APPROVAL_REQUIRED,
    AUTHORITY_AUTO_ALLOWED,
    AUTHORITY_DISALLOWED,
    ConstructionExecutionDecision,
    ConstructionExecutionNotAuthorized,
    ConstructionExecutionPolicy,
    ConstructionExecutionResult,
    RESOURCE_AVAILABLE,
    RESOURCE_UNAVAILABLE,
    RESULT_CANDIDATE_PRODUCED,
    RESULT_EXECUTION_FAILED,
    RESULT_SEMANTICALLY_UNRESOLVED,
    STATUS_MULTIPLE_UNSUPPORTED,
    STATUS_NOT_REQUIRED,
    approval_required_class_membership_policy,
    auto_allowed_class_membership_policy,
    decide_construction_execution,
    execute_construction_obligation,
    required_obligations_for_execution,
)
from .construction_approval import (
    APPROVAL_KIND,
    ConstructionExecutionApproval,
    ConstructionExecutionAuthorization,
    authorize_construction_execution,
    construction_execution_approval,
)
from .construction_cycle import (
    CYCLE_APPROVAL_REQUIRED,
    CYCLE_CONSTRUCTION_ATTEMPTED,
    CYCLE_DEFERRED,
    CYCLE_NO_CONSTRUCTION_REQUIRED,
    NEXT_ADJUDICATION,
    PreviousUnresolvedAttempt,
    SemanticConstructionCycleResult,
    advance_semantic_construction_cycle,
    classify_required_obligations,
    select_canonical_obligation,
)
from .model_adjudicator import (
    ADJUDICATION_INSTRUCTION,
    DEFAULT_MODEL,
    INVOCATION_SCHEMA,
    INVOCATION_VERSION,
    MAX_ATTEMPTS,
    MODEL_DRAFT_SCHEMA,
    MODEL_DRAFT_VERSION,
    MODEL_INSTRUCTION_VERSION,
    AdjudicatorRequest,
    AdjudicatorTransport,
    AdjudicatorTransportResponse,
    ModelAdjudicationDraft,
    ModelAdjudicationInvocationError,
    ModelAdjudicator,
    ModelAdjudicatorConfig,
    OpenRouterAdjudicatorTransport,
    adjudicate_governance_case,
    build_case_evidence_catalog,
    compile_model_adjudication_draft,
    governance_adjudication_schema,
    model_adjudication_draft_schema,
    write_governance_adjudication_invocation,
)
from .obligation_synthesis import (
    GENERATION_METHOD,
    STATUS_CANNOT_SYNTHESIZE,
    STATUS_SYNTHESIZED,
    SYNTHESIS_PROFILE,
    MembershipObligationContext,
    ObligationSynthesisFailure,
    PendingConstructionObligations,
    SynthesizedClassMembershipObligation,
    class_membership_obligation_key,
    collect_pending_class_membership_obligations,
    context_from_invariant_definition,
    membership_obligation_context,
    pending_class_membership_obligations_from_derivation,
    synthesize_class_membership_obligation,
)
from .case_readiness import (
    STATUS_CONSTRUCTION_REQUIRED,
    STATUS_READY_FOR_ADJUDICATION,
    ConstructionRequired,
    GovernanceCaseReadiness,
    RequiredConstructionObligation,
    assess_governance_case_readiness,
    attach_construction_context,
)
from .checkout_invariant import (
    CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
    CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION,
    CHECKOUT_PROVIDER_BOUNDARY_KIND,
    CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE,
    INVARIANT_DEFINITION_SCHEMA,
    INVARIANT_EVALUATION_SCHEMA,
    ScopedInvariantDefinition,
    ScopedInvariantEvaluation,
    aggregate_checkout_provider_boundary_truth,
    evaluate_checkout_provider_boundary,
    invariant_context_for_case,
)


class IdentityPlane(StrEnum):
    SOURCE = "SOURCE"
    SEMANTIC = "SEMANTIC"
    PROGRAM = "PROGRAM"


class SupportMode(StrEnum):
    MECHANICALLY_SOURCE_NATIVE = "mechanically_source_native"
    SOURCE_EXPLICIT = "source_explicit"
    SOURCE_STRUCTURAL = "source_structural"
    CROSS_EVIDENCE_INFERRED = "cross_evidence_inferred"
    HYPOTHESIZED = "hypothesized"


class ReferentResolution(StrEnum):
    NATIVE_ID = "native_id"
    DETERMINISTIC = "deterministic"
    SOURCE_DEFINED = "source_defined"
    AGENT_RESOLVED = "agent_resolved"
    AMBIGUOUS = "ambiguous"


class GovernanceValidationError(ValueError):
    """A governance-specific identity or support invariant was violated."""


def namespaced_referent_id(plane: IdentityPlane | str, local_id: str) -> str:
    """Return a stable, visibly plane-qualified governance referent ID."""

    try:
        selected = IdentityPlane(plane)
    except ValueError as exc:
        raise GovernanceValidationError(f"unknown identity plane {plane!r}") from exc
    local = str(local_id or "").strip()
    if not local:
        raise GovernanceValidationError("a namespaced referent local ID must be non-empty")
    return f"{selected.value.lower()}:{local}"


def identity_plane(referent_id: str) -> IdentityPlane:
    """Read the plane prefix of a governance namespaced referent ID."""

    prefix, separator, _local = str(referent_id or "").partition(":")
    if not separator:
        raise GovernanceValidationError(
            f"governance referent {referent_id!r} has no identity-plane namespace"
        )
    try:
        return IdentityPlane(prefix.upper())
    except ValueError as exc:
        raise GovernanceValidationError(
            f"governance referent {referent_id!r} has unknown identity plane"
        ) from exc


def validate_relation_identity_planes(
    values: Mapping[str, Any], expected: Mapping[str, IdentityPlane | str]
) -> None:
    """Require every identity-bearing relation value to use its intended plane.

    This is an application-side check. Generic World relations intentionally
    remain unaware of governance identity planes.
    """

    if set(values) != set(expected):
        raise GovernanceValidationError(
            f"relation identity roles {sorted(expected)} do not match values {sorted(values)}"
        )
    for role, expected_plane in expected.items():
        actual = identity_plane(str(values[role]))
        try:
            wanted = IdentityPlane(expected_plane)
        except ValueError as exc:
            raise GovernanceValidationError(
                f"unknown expected identity plane {expected_plane!r} for {role!r}"
            ) from exc
        if actual is not wanted:
            raise GovernanceValidationError(
                f"{role!r} requires {wanted.value} identity, got {actual.value}"
            )


@dataclass(frozen=True)
class GovernanceSupport:
    """Fine support metadata carried through existing assertion grounding.

    The metadata is intentionally an application value object, not a new
    kernel primitive. Source observations are required so a durable support
    record has a reconstructible evidence path. A cross-evidence inference can
    therefore list all observations that established it.
    """

    support_mode: SupportMode | str
    observations: tuple[SourceObservation, ...]
    referent_resolution: Mapping[str, ReferentResolution | str] = field(
        default_factory=dict
    )
    construction_method: str = ""

    def __post_init__(self) -> None:
        try:
            mode = SupportMode(self.support_mode)
        except ValueError as exc:
            raise GovernanceValidationError(
                f"unknown governance support mode {self.support_mode!r}"
            ) from exc
        object.__setattr__(self, "support_mode", mode)
        observations = tuple(self.observations)
        if not observations:
            raise GovernanceValidationError(
                "durable governance support needs reconstructible source observations"
            )
        for observation in observations:
            if not isinstance(observation, SourceObservation):
                raise GovernanceValidationError(
                    "governance support observations must be SourceObservation values"
                )
            if not all(
                str(value or "").strip()
                for value in (
                    observation.provider,
                    observation.native_handle,
                    observation.source_revision,
                    observation.native_location,
                )
            ):
                raise GovernanceValidationError(
                    "each governance source observation needs provider, handle, "
                    "revision, and location"
                )
        resolutions: dict[str, ReferentResolution] = {}
        for role, resolution in dict(self.referent_resolution).items():
            try:
                resolutions[str(role)] = ReferentResolution(resolution)
            except ValueError as exc:
                raise GovernanceValidationError(
                    f"unknown referent resolution {resolution!r} for {role!r}"
                ) from exc
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "referent_resolution", resolutions)

    def assertion_grounding(self) -> AssertionGrounding:
        """Encode support metadata using the existing grounding boundary."""

        return AssertionGrounding(
            observations=self.observations,
            construction_method=self.construction_method,
            extra={
                "governance_support_mode": self.support_mode.value,
                "governance_referent_resolution": {
                    role: resolution.value
                    for role, resolution in sorted(self.referent_resolution.items())
                },
            },
        )


__all__ = [
    "ADJUDICATION_SCHEMA",
    "ADJUDICATION_INSTRUCTION",
    "ADOPTION_DECISION_SCHEMA",
    "ADOPTION_OUTCOMES",
    "ADOPTION_POLICY_SCHEMA",
    "CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT",
    "CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION",
    "DEFAULT_MODEL",
    "INVOCATION_SCHEMA",
    "INVOCATION_VERSION",
    "MAX_ATTEMPTS",
    "MODEL_DRAFT_SCHEMA",
    "MODEL_DRAFT_VERSION",
    "MODEL_INSTRUCTION_VERSION",
    "REVISION_BRIEF_SCHEMA",
    "APPROVAL_KIND",
    "AdjudicationError",
    "AdjudicatorRequest",
    "AdjudicatorTransport",
    "AdjudicatorTransportResponse",
    "AdoptionPolicy",
    "BaselineBindingError",
    "CandidateAdoptionDecision",
    "CandidateEvaluation",
    "CandidateEvaluationError",
    "CandidateEvaluationResult",
    "ConstructionExecutionApproval",
    "ConstructionExecutionAuthorization",
    "ConstructionExecutionDecision",
    "ConstructionExecutionNotAuthorized",
    "ConstructionExecutionPolicy",
    "ConstructionExecutionResult",
    "GitRepository",
    "GitResolutionError",
    "GitSnapshot",
    "GovernedCaseEvaluationResult",
    "GovernanceSupport",
    "GovernanceValidationError",
    "IdentityPlane",
    "ModelAdjudicationDraft",
    "ModelAdjudicationInvocationError",
    "ModelAdjudicator",
    "ModelAdjudicatorConfig",
    "OpenRouterAdjudicatorTransport",
    "PreviousUnresolvedAttempt",
    "REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT",
    "REASON_REQUIRED_SEMANTIC_CONSTRUCTION",
    "ReferentResolution",
    "SemanticConstructionCycleResult",
    "SupportMode",
    "adjudicate_governance_case",
    "advance_semantic_construction_cycle",
    "approval_required_class_membership_policy",
    "authorize_construction_execution",
    "auto_allowed_class_membership_policy",
    "build_case_evidence_catalog",
    "build_governance_revision_brief",
    "classify_required_obligations",
    "compile_model_adjudication_draft",
    "construction_execution_approval",
    "create_governance_adjudication",
    "decide_candidate_adoption",
    "decide_construction_execution",
    "decide_semantic_construction_required",
    "evaluate_assembled_candidate_case",
    "execute_construction_obligation",
    "evaluate_candidate",
    "evaluate_git_candidate",
    "governance_adjudication_schema",
    "identity_plane",
    "load_governance_adjudication",
    "model_adjudication_draft_schema",
    "namespaced_referent_id",
    "required_obligations_for_execution",
    "select_canonical_obligation",
    "validate_candidate_adoption_decision",
    "validate_governance_adjudication",
    "validate_relation_identity_planes",
    "write_candidate_adoption",
    "write_governance_adjudication",
    "write_governance_adjudication_invocation",
    "write_governance_revision_brief",
    "GENERATION_METHOD",
    "STATUS_CANNOT_SYNTHESIZE",
    "STATUS_SYNTHESIZED",
    "SYNTHESIS_PROFILE",
    "MembershipObligationContext",
    "ObligationSynthesisFailure",
    "PendingConstructionObligations",
    "SynthesizedClassMembershipObligation",
    "class_membership_obligation_key",
    "collect_pending_class_membership_obligations",
    "context_from_invariant_definition",
    "membership_obligation_context",
    "pending_class_membership_obligations_from_derivation",
    "synthesize_class_membership_obligation",
    "STATUS_CONSTRUCTION_REQUIRED",
    "STATUS_READY_FOR_ADJUDICATION",
    "ConstructionRequired",
    "GovernanceCaseReadiness",
    "RequiredConstructionObligation",
    "assess_governance_case_readiness",
    "attach_construction_context",
    "CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID",
    "CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION",
    "CHECKOUT_PROVIDER_BOUNDARY_KIND",
    "CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE",
    "INVARIANT_DEFINITION_SCHEMA",
    "INVARIANT_EVALUATION_SCHEMA",
    "ScopedInvariantDefinition",
    "ScopedInvariantEvaluation",
    "aggregate_checkout_provider_boundary_truth",
    "evaluate_checkout_provider_boundary",
    "invariant_context_for_case",
]
