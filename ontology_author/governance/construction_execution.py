"""Application-layer construction execution policy for one required obligation.

This is workflow configuration, not World knowledge. It decides whether a
single required ConstructionObligation may be executed, must be approved, or
must remain deferred. Execution, admission, and publication remain later
steps.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ontology_author.semantic_binding.schemas import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    ConstructionObligation,
    SemanticCandidate,
    SemanticConstructionInvocationError,
    copy_json,
    digest,
)
from ontology_author.governance.obligation_synthesis import (
    PendingConstructionObligations,
    SynthesizedClassMembershipObligation,
)

POLICY_SCHEMA = "construction_execution_policy/v0"
POLICY_ID = "construction-execution/v0"
POLICY_VERSION = "v0"
DECISION_SCHEMA = "construction_execution_decision/v0"
RESULT_SCHEMA = "construction_execution_result/v0"
MAX_ATTEMPTS = 1

AUTHORITY_AUTO_ALLOWED = "AUTO_ALLOWED"
AUTHORITY_APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
AUTHORITY_DISALLOWED = "DISALLOWED"
CONSTRUCTION_AUTHORITIES = frozenset(
    {
        AUTHORITY_AUTO_ALLOWED,
        AUTHORITY_APPROVAL_REQUIRED,
        AUTHORITY_DISALLOWED,
    }
)

RESOURCE_AVAILABLE = "AVAILABLE"
RESOURCE_UNAVAILABLE = "UNAVAILABLE"
RESOURCE_PERMISSIONS = frozenset({RESOURCE_AVAILABLE, RESOURCE_UNAVAILABLE})

ACTION_EXECUTE = "EXECUTE"
ACTION_REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
ACTION_DEFER = "DEFER"
EXECUTION_ACTIONS = frozenset(
    {ACTION_EXECUTE, ACTION_REQUIRE_APPROVAL, ACTION_DEFER}
)

STATUS_DECIDED = "DECIDED"
STATUS_NOT_REQUIRED = "NOT_REQUIRED"
STATUS_MULTIPLE_UNSUPPORTED = "MULTIPLE_REQUIRED_OBLIGATIONS_UNSUPPORTED"

RESULT_CANDIDATE_PRODUCED = "CANDIDATE_PRODUCED"
RESULT_SEMANTICALLY_UNRESOLVED = "SEMANTICALLY_UNRESOLVED"
RESULT_EXECUTION_FAILED = "EXECUTION_FAILED"

REASON_NOT_REQUIRED = "NO_REQUIRED_CONSTRUCTION_OBLIGATION"
REASON_MULTIPLE_UNSUPPORTED = "MULTIPLE_REQUIRED_OBLIGATIONS_UNSUPPORTED"
REASON_CONSTRUCTOR_NOT_CONFIGURED = "CONSTRUCTOR_NOT_CONFIGURED"
REASON_CONSTRUCTION_DISALLOWED = "CONSTRUCTION_DISALLOWED"
REASON_UNKNOWN_AUTHORITY = "UNKNOWN_EXECUTION_AUTHORITY"
REASON_APPROVAL_REQUIRED = "EXECUTION_AUTHORITY_REQUIRES_APPROVAL"
REASON_RESOURCE_UNAVAILABLE = "RESOURCE_PERMISSION_UNAVAILABLE"
REASON_AUTO_ALLOWED_AND_AVAILABLE = "AUTO_ALLOWED_AND_RESOURCE_AVAILABLE"
REASON_NOT_AUTHORIZED = "EXECUTION_NOT_AUTHORIZED"
REASON_OBLIGATION_MISMATCH = "EXECUTION_DECISION_OBLIGATION_MISMATCH"
REASON_MEMBER_CANDIDATE = "VALID_SEMANTIC_CANDIDATE_PRODUCED"
REASON_UNRESOLVED = "CONSTRUCTOR_RETURNED_UNRESOLVED"
REASON_INVALID_OUTPUT = "CONSTRUCTOR_OUTPUT_INVALID"
REASON_PROVIDER_FAILED = "CONSTRUCTOR_PROVIDER_FAILED"
REASON_UNEXPECTED_RESULT = "CONSTRUCTOR_RESULT_NOT_MEMBER_OR_UNRESOLVED"

CLASS_MEMBERSHIP_CONSTRUCTOR = "bounded-semantic-constructor/v0"


class ConstructionExecutionNotAuthorized(ValueError):
    """Execution was requested without a legal authorization."""

    def __init__(self, decision: ConstructionExecutionDecision, reason: str):
        self.decision = decision
        self.reason = reason
        super().__init__(
            f"construction execution is not authorized: {reason}"
            f" (action={decision.action})"
        )


def _as_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return copy_json(value.to_dict())
    if isinstance(value, Mapping):
        return copy_json(value)
    return {}


def _as_obligation(value: Any) -> ConstructionObligation:
    if isinstance(value, ConstructionObligation):
        return value
    if isinstance(value, SynthesizedClassMembershipObligation):
        return value.obligation
    if isinstance(value, Mapping):
        payload = value.get("obligation") if "obligation" in value else value
        return ConstructionObligation.from_dict(payload)
    raise TypeError("required construction item is not a ConstructionObligation")


def _obligations(
    values: Sequence[Any] | PendingConstructionObligations | None,
) -> tuple[ConstructionObligation, ...]:
    if values is None:
        return ()
    if isinstance(values, PendingConstructionObligations):
        return values.obligations
    return tuple(_as_obligation(item) for item in values)


@dataclass(frozen=True)
class ConstructionExecutionPolicy:
    """Trusted application configuration for construction execution authority.

    This is not World knowledge. Composers, SemanticCandidates,
    ConstructionObligations, and MembershipGaps do not choose it.
    """

    profile_authorities: Mapping[str, str]
    constructor_profiles: Mapping[str, str] = field(default_factory=dict)
    obligation_authorities: Mapping[str, str] = field(default_factory=dict)
    policy_id: str = POLICY_ID
    version: str = POLICY_VERSION
    contract: str = POLICY_SCHEMA
    max_attempts: int = MAX_ATTEMPTS

    def __post_init__(self) -> None:
        authorities = {
            str(profile): str(authority).upper()
            for profile, authority in dict(self.profile_authorities).items()
            if str(profile).strip()
        }
        object.__setattr__(self, "profile_authorities", dict(sorted(authorities.items())))
        constructors = dict(self.constructor_profiles)
        if not constructors:
            constructors = {CLASS_MEMBERSHIP_ADMISSION_PROFILE: CLASS_MEMBERSHIP_CONSTRUCTOR}
        mapped = {
            str(profile): str(constructor)
            for profile, constructor in dict(constructors).items()
            if str(profile).strip() and str(constructor).strip()
        }
        object.__setattr__(self, "constructor_profiles", dict(sorted(mapped.items())))
        overlays = {
            str(obligation_id): str(authority).upper()
            for obligation_id, authority in dict(self.obligation_authorities).items()
            if str(obligation_id).strip() and str(authority).strip()
        }
        object.__setattr__(self, "obligation_authorities", dict(sorted(overlays.items())))
        object.__setattr__(self, "policy_id", str(self.policy_id or POLICY_ID))
        object.__setattr__(self, "version", str(self.version or POLICY_VERSION))
        object.__setattr__(self, "contract", str(self.contract or POLICY_SCHEMA))
        object.__setattr__(self, "max_attempts", MAX_ATTEMPTS)

    def authority_for(self, construction_profile: str, obligation_id: str = "") -> str:
        overlay = self.obligation_authorities.get(str(obligation_id or ""))
        if overlay:
            return overlay
        return self.profile_authorities.get(
            str(construction_profile or ""), AUTHORITY_DISALLOWED
        )

    def constructor_for(self, construction_profile: str) -> str:
        return self.constructor_profiles.get(str(construction_profile or ""), "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "policy_id": self.policy_id,
            "version": self.version,
            "profile_authorities": dict(self.profile_authorities),
            "constructor_profiles": dict(self.constructor_profiles),
            "obligation_authorities": dict(self.obligation_authorities),
            "max_attempts": self.max_attempts,
        }


def auto_allowed_class_membership_policy() -> ConstructionExecutionPolicy:
    return ConstructionExecutionPolicy(
        profile_authorities={
            CLASS_MEMBERSHIP_ADMISSION_PROFILE: AUTHORITY_AUTO_ALLOWED
        }
    )


def approval_required_class_membership_policy() -> ConstructionExecutionPolicy:
    return ConstructionExecutionPolicy(
        profile_authorities={
            CLASS_MEMBERSHIP_ADMISSION_PROFILE: AUTHORITY_APPROVAL_REQUIRED
        }
    )


@dataclass(frozen=True)
class ConstructionExecutionDecision:
    """Workflow authorization for one required construction obligation.

    EXECUTE authorizes a later execution operation. It does not mean a
    constructor ran, a model was called, semantic truth was established, or
    the candidate may proceed.
    """

    status: str
    action: str
    obligation_id: str
    policy_id: str
    policy_version: str
    reason: str
    construction_profile: str
    execution_authority: str
    resource_permission: str
    constructor_id: str
    required_obligation_ids: tuple[str, ...]
    decision_id: str = ""
    constructor_invoked: bool = False
    model_invoked: bool = False
    contract: str = DECISION_SCHEMA

    def __post_init__(self) -> None:
        payload = {
            "status": self.status,
            "action": self.action,
            "obligation_id": self.obligation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "reason": self.reason,
            "construction_profile": self.construction_profile,
            "execution_authority": self.execution_authority,
            "resource_permission": self.resource_permission,
            "constructor_id": self.constructor_id,
            "required_obligation_ids": list(self.required_obligation_ids),
        }
        object.__setattr__(
            self,
            "decision_id",
            self.decision_id or digest(payload, "construction-execution-decision"),
        )
        object.__setattr__(self, "constructor_invoked", False)
        object.__setattr__(self, "model_invoked", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "decision_id": self.decision_id,
            "status": self.status,
            "action": self.action,
            "obligation_id": self.obligation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "reason": self.reason,
            "construction_profile": self.construction_profile,
            "execution_authority": self.execution_authority,
            "resource_permission": self.resource_permission,
            "constructor_id": self.constructor_id,
            "required_obligation_ids": list(self.required_obligation_ids),
            "constructor_invoked": False,
            "model_invoked": False,
        }


@dataclass(frozen=True)
class ConstructionExecutionResult:
    """Outcome of one authorized construction attempt.

    CANDIDATE_PRODUCED is still not admission or World publication.
    SEMANTICALLY_UNRESOLVED is constructor uncertainty, not operational failure.
    """

    status: str
    obligation_id: str
    execution_decision_id: str
    construction_profile: str
    constructor_id: str
    attempt_number: int
    constructor_invoked: bool
    model_invoked: bool
    reason: str
    candidate: SemanticCandidate | None = None
    catalog: Mapping[str, Any] | None = None
    receipt: Mapping[str, Any] | None = None
    constructor_metadata: Mapping[str, Any] = field(default_factory=dict)
    world_written: bool = False
    admission_performed: bool = False
    invocation_count: int = 0
    approval_id: str = ""
    authorization_status: str = ""
    consumed_approval_id: str = ""
    contract: str = RESULT_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "constructor_metadata",
            copy_json(self.constructor_metadata or {}),
        )
        object.__setattr__(self, "world_written", False)
        object.__setattr__(self, "admission_performed", False)
        if self.catalog is not None:
            object.__setattr__(self, "catalog", copy_json(self.catalog))
        if self.receipt is not None:
            object.__setattr__(self, "receipt", copy_json(self.receipt))

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "status": self.status,
            "obligation_id": self.obligation_id,
            "execution_decision_id": self.execution_decision_id,
            "construction_profile": self.construction_profile,
            "constructor_id": self.constructor_id,
            "attempt_number": self.attempt_number,
            "constructor_invoked": self.constructor_invoked,
            "model_invoked": self.model_invoked,
            "invocation_count": self.invocation_count,
            "approval_id": self.approval_id,
            "authorization_status": self.authorization_status,
            "consumed_approval_id": self.consumed_approval_id,
            "reason": self.reason,
            "candidate": self.candidate.to_dict() if self.candidate is not None else None,
            "catalog": copy_json(self.catalog) if self.catalog is not None else None,
            "receipt": copy_json(self.receipt) if self.receipt is not None else None,
            "constructor_metadata": copy_json(self.constructor_metadata),
            "world_written": False,
            "admission_performed": False,
        }


def required_obligations_for_execution(
    pending: PendingConstructionObligations | Sequence[Any] | None,
    readiness: Mapping[str, Any] | Any,
) -> tuple[ConstructionObligation, ...]:
    """Return pending obligations whose IDs are required for this case.

    This is identity filtering, not ranking or scheduling.
    """

    payload = _as_mapping(readiness)
    required_ids = [
        str(item)
        for item in payload.get("required_obligation_ids") or ()
        if str(item)
    ]
    if not required_ids:
        return ()
    wanted = set(required_ids)
    selected = [
        obligation
        for obligation in _obligations(pending)
        if obligation.obligation_id in wanted
    ]
    by_id = {item.obligation_id: item for item in selected}
    return tuple(by_id[item] for item in required_ids if item in by_id)


def _action_for(
    *,
    authority: str,
    resource_permission: str,
    constructor_id: str,
) -> tuple[str, str]:
    if not constructor_id:
        return ACTION_DEFER, REASON_CONSTRUCTOR_NOT_CONFIGURED
    if authority == AUTHORITY_DISALLOWED:
        return ACTION_DEFER, REASON_CONSTRUCTION_DISALLOWED
    if authority not in CONSTRUCTION_AUTHORITIES:
        return ACTION_DEFER, REASON_UNKNOWN_AUTHORITY
    if authority == AUTHORITY_APPROVAL_REQUIRED:
        return ACTION_REQUIRE_APPROVAL, REASON_APPROVAL_REQUIRED
    if resource_permission != RESOURCE_AVAILABLE:
        return ACTION_DEFER, REASON_RESOURCE_UNAVAILABLE
    return ACTION_EXECUTE, REASON_AUTO_ALLOWED_AND_AVAILABLE


def decide_construction_execution(
    required_obligations: Sequence[Any] | PendingConstructionObligations | None,
    *,
    policy: ConstructionExecutionPolicy,
    resource_permission: str = RESOURCE_AVAILABLE,
) -> ConstructionExecutionDecision:
    """Decide execution authority for exactly one required obligation.

    Zero required obligations yield NOT_REQUIRED. More than one yields
    MULTIPLE_REQUIRED_OBLIGATIONS_UNSUPPORTED and chooses none. The call does
    not mutate obligations, cases, candidates, or Worlds.
    """

    selected = _obligations(required_obligations)
    ids = tuple(item.obligation_id for item in selected)
    permission = str(resource_permission or "").upper() or RESOURCE_UNAVAILABLE
    if permission not in RESOURCE_PERMISSIONS:
        permission = RESOURCE_UNAVAILABLE
    if not selected:
        return ConstructionExecutionDecision(
            status=STATUS_NOT_REQUIRED,
            action="",
            obligation_id="",
            policy_id=policy.policy_id,
            policy_version=policy.version,
            reason=REASON_NOT_REQUIRED,
            construction_profile="",
            execution_authority="",
            resource_permission=permission,
            constructor_id="",
            required_obligation_ids=(),
        )
    if len(selected) > 1:
        return ConstructionExecutionDecision(
            status=STATUS_MULTIPLE_UNSUPPORTED,
            action="",
            obligation_id="",
            policy_id=policy.policy_id,
            policy_version=policy.version,
            reason=REASON_MULTIPLE_UNSUPPORTED,
            construction_profile="",
            execution_authority="",
            resource_permission=permission,
            constructor_id="",
            required_obligation_ids=ids,
        )
    obligation = selected[0]
    profile = obligation.admission_profile
    authority = policy.authority_for(profile, obligation.obligation_id)
    constructor_id = policy.constructor_for(profile)
    action, reason = _action_for(
        authority=authority,
        resource_permission=permission,
        constructor_id=constructor_id,
    )
    return ConstructionExecutionDecision(
        status=STATUS_DECIDED,
        action=action,
        obligation_id=obligation.obligation_id,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        reason=reason,
        construction_profile=profile,
        execution_authority=authority,
        resource_permission=permission,
        constructor_id=constructor_id,
        required_obligation_ids=ids,
    )


class _CountingTransport:
    def __init__(self, inner: Any):
        self.inner = inner
        self.calls = 0

    def generate(self, request: Any) -> Any:
        self.calls += 1
        return self.inner.generate(request)


def _as_decision(
    execution_decision: ConstructionExecutionDecision | Mapping[str, Any],
    obligation: ConstructionObligation,
) -> ConstructionExecutionDecision:
    if isinstance(execution_decision, ConstructionExecutionDecision):
        return execution_decision
    return ConstructionExecutionDecision(
        status=str(execution_decision.get("status") or STATUS_DECIDED),
        action=str(execution_decision.get("action") or ""),
        obligation_id=str(execution_decision.get("obligation_id") or ""),
        policy_id=str(execution_decision.get("policy_id") or POLICY_ID),
        policy_version=str(execution_decision.get("policy_version") or POLICY_VERSION),
        reason=str(execution_decision.get("reason") or ""),
        construction_profile=str(
            execution_decision.get("construction_profile") or obligation.admission_profile
        ),
        execution_authority=str(execution_decision.get("execution_authority") or ""),
        resource_permission=str(execution_decision.get("resource_permission") or ""),
        constructor_id=str(execution_decision.get("constructor_id") or ""),
        required_obligation_ids=tuple(
            execution_decision.get("required_obligation_ids") or ()
        ),
        decision_id=str(execution_decision.get("decision_id") or ""),
    )


def execute_construction_obligation(
    obligation: ConstructionObligation | Mapping[str, Any] | SynthesizedClassMembershipObligation,
    execution_decision: ConstructionExecutionDecision | Mapping[str, Any],
    *,
    constructor: Any,
    case: Mapping[str, Any],
    bounded_program_source: Sequence[Mapping[str, Any]] = (),
    maintenance_dependencies: Sequence[Mapping[str, Any]] = (),
    completeness_receipts: Sequence[Mapping[str, Any]] = (),
    program_endpoint_kinds: Mapping[str, str] | None = None,
    constructor_metadata: Mapping[str, Any] | None = None,
    output_dir: Path | str | None = None,
    execution_authorization: Any | None = None,
    consumed_approval_ids: Sequence[str] = (),
) -> ConstructionExecutionResult:
    """Run one authorized construction attempt through the existing pipeline.

    Legal when ``decision.action == EXECUTE``, or when ``action ==
    REQUIRE_APPROVAL`` and a matching ``AUTHORIZED`` authorization is supplied.
    Does not admit the resulting candidate or write a World. Approval is not
    passed into the constructor catalog or prompt.
    """

    from .construction_approval import (
        AUTHORIZATION_AUTHORIZED,
        execution_permitted,
    )

    selected = _as_obligation(obligation)
    decision = _as_decision(execution_decision, selected)
    permitted, permit_reason = execution_permitted(
        decision,
        selected.obligation_id,
        execution_authorization,
        consumed_approval_ids,
    )
    if not permitted:
        raise ConstructionExecutionNotAuthorized(decision, permit_reason)

    from ontology_author.semantic_binding.construction import (
        build_semantic_construction_catalog,
        construct_semantic_candidate,
    )

    metadata = copy_json(constructor_metadata or {})
    transport = _CountingTransport(constructor)
    catalog = build_semantic_construction_catalog(
        selected,
        case,
        bounded_program_source=bounded_program_source,
        maintenance_dependencies=maintenance_dependencies,
        completeness_receipts=completeness_receipts,
        program_endpoint_kinds=program_endpoint_kinds,
    )
    approval_id = ""
    authorization_status = ""
    consumed_approval_id = ""
    if execution_authorization is not None and decision.action == ACTION_REQUIRE_APPROVAL:
        approval_id = str(getattr(execution_authorization, "approval_id", "") or "")
        authorization_status = str(
            getattr(execution_authorization, "status", "") or AUTHORIZATION_AUTHORIZED
        )
        consumed_approval_id = approval_id
    approval_fields = {
        "approval_id": approval_id,
        "authorization_status": authorization_status,
        "consumed_approval_id": consumed_approval_id,
    }
    try:
        candidate = construct_semantic_candidate(
            selected,
            case,
            transport=transport,
            bounded_program_source=bounded_program_source,
            maintenance_dependencies=maintenance_dependencies,
            completeness_receipts=completeness_receipts,
            program_endpoint_kinds=program_endpoint_kinds,
            constructor_metadata=metadata,
            output_dir=output_dir,
            max_attempts=MAX_ATTEMPTS,
        )
    except SemanticConstructionInvocationError as exc:
        receipt = _as_mapping(getattr(exc, "receipt", {}) or {})
        reason = (
            REASON_PROVIDER_FAILED
            if receipt.get("runtime_status") == "FAILED_PROVIDER"
            else REASON_INVALID_OUTPUT
        )
        return ConstructionExecutionResult(
            status=RESULT_EXECUTION_FAILED,
            obligation_id=selected.obligation_id,
            execution_decision_id=decision.decision_id,
            construction_profile=decision.construction_profile or selected.admission_profile,
            constructor_id=decision.constructor_id,
            attempt_number=MAX_ATTEMPTS,
            constructor_invoked=True,
            model_invoked=transport.calls > 0,
            invocation_count=transport.calls,
            reason=reason,
            catalog=catalog,
            receipt=receipt,
            constructor_metadata=metadata,
            **approval_fields,
        )
    except Exception as exc:
        return ConstructionExecutionResult(
            status=RESULT_EXECUTION_FAILED,
            obligation_id=selected.obligation_id,
            execution_decision_id=decision.decision_id,
            construction_profile=decision.construction_profile or selected.admission_profile,
            constructor_id=decision.constructor_id,
            attempt_number=MAX_ATTEMPTS,
            constructor_invoked=True,
            model_invoked=transport.calls > 0,
            invocation_count=transport.calls,
            reason=REASON_PROVIDER_FAILED,
            catalog=catalog,
            receipt={"error_type": type(exc).__name__, "error": str(exc)[:500]},
            constructor_metadata=metadata,
            **approval_fields,
        )

    if candidate.membership_result == "UNRESOLVED":
        return ConstructionExecutionResult(
            status=RESULT_SEMANTICALLY_UNRESOLVED,
            obligation_id=selected.obligation_id,
            execution_decision_id=decision.decision_id,
            construction_profile=decision.construction_profile or selected.admission_profile,
            constructor_id=decision.constructor_id,
            attempt_number=MAX_ATTEMPTS,
            constructor_invoked=True,
            model_invoked=transport.calls > 0,
            invocation_count=transport.calls,
            reason=REASON_UNRESOLVED,
            candidate=candidate,
            catalog=catalog,
            constructor_metadata=metadata,
            **approval_fields,
        )
    if candidate.membership_result == "MEMBER":
        return ConstructionExecutionResult(
            status=RESULT_CANDIDATE_PRODUCED,
            obligation_id=selected.obligation_id,
            execution_decision_id=decision.decision_id,
            construction_profile=decision.construction_profile or selected.admission_profile,
            constructor_id=decision.constructor_id,
            attempt_number=MAX_ATTEMPTS,
            constructor_invoked=True,
            model_invoked=transport.calls > 0,
            invocation_count=transport.calls,
            reason=REASON_MEMBER_CANDIDATE,
            candidate=candidate,
            catalog=catalog,
            constructor_metadata=metadata,
            **approval_fields,
        )
    return ConstructionExecutionResult(
        status=RESULT_EXECUTION_FAILED,
        obligation_id=selected.obligation_id,
        execution_decision_id=decision.decision_id,
        construction_profile=decision.construction_profile or selected.admission_profile,
        constructor_id=decision.constructor_id,
        attempt_number=MAX_ATTEMPTS,
        constructor_invoked=True,
        model_invoked=transport.calls > 0,
        invocation_count=transport.calls,
        reason=REASON_UNEXPECTED_RESULT,
        candidate=candidate,
        catalog=catalog,
        constructor_metadata=metadata,
        **approval_fields,
    )
