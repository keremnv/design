"""Exact, one-shot approval for REQUIRE_APPROVAL construction execution.

This is workflow authority, not semantic evidence and not candidate-adoption
approval. It authorizes one constructor attempt for one exact
ConstructionObligation bound to one exact ConstructionExecutionDecision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ontology_author.semantic_binding.schemas import copy_json, digest

from .construction_execution import (
    ACTION_DEFER,
    ACTION_EXECUTE,
    ACTION_REQUIRE_APPROVAL,
    AUTHORITY_DISALLOWED,
    MAX_ATTEMPTS,
    RESOURCE_UNAVAILABLE,
    ConstructionExecutionDecision,
)

APPROVAL_SCHEMA = "construction_execution_approval/v0"
AUTHORIZATION_SCHEMA = "construction_execution_authorization/v0"
APPROVAL_KIND = "CONSTRUCTION_EXECUTION_APPROVAL"
SCOPE_ONE_ATTEMPT = "ONE_EXECUTION_ATTEMPT"

APPROVAL_APPROVED = "APPROVED"
APPROVAL_DENIED = "DENIED"

AUTHORIZATION_AUTHORIZED = "AUTHORIZED"
AUTHORIZATION_NOT_AUTHORIZED = "NOT_AUTHORIZED"
AUTHORIZATION_DENIED = "DENIED"

REASON_AUTHORIZED = "EXPLICIT_APPROVAL_AUTHORIZES_ONE_ATTEMPT"
REASON_DENIED = "EXPLICIT_APPROVAL_DENIED"
REASON_MISSING_APPROVAL = "REQUIRE_APPROVAL_HAS_NO_AUTHORIZATION"
REASON_DECISION_NOT_REQUIRE_APPROVAL = "DECISION_IS_NOT_REQUIRE_APPROVAL"
REASON_DEFER_CANNOT_BE_APPROVED = "DEFER_CANNOT_BE_OVERRIDDEN_BY_APPROVAL"
REASON_DISALLOWED_CANNOT_BE_APPROVED = "DISALLOWED_CANNOT_BE_OVERRIDDEN_BY_APPROVAL"
REASON_RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE_CANNOT_BE_OVERRIDDEN_BY_APPROVAL"
REASON_APPROVAL_MISMATCH = "APPROVAL_DOES_NOT_BIND_TO_DECISION"
REASON_APPROVAL_CONSUMED = "APPROVAL_ALREADY_CONSUMED"
REASON_WRONG_OBLIGATION = "APPROVAL_OBLIGATION_MISMATCH"
REASON_WRONG_DECISION = "APPROVAL_DECISION_ID_MISMATCH"
REASON_WRONG_POLICY = "APPROVAL_POLICY_MISMATCH"
REASON_WRONG_CONSTRUCTOR = "APPROVAL_CONSTRUCTOR_MISMATCH"
REASON_WRONG_SCOPE = "APPROVAL_SCOPE_NOT_ONE_ATTEMPT"

DEFAULT_APPROVAL_SOURCE = "explicit-external-approval/v0"


def _text(value: Any) -> str:
    return str(value or "").strip()


@dataclass(frozen=True)
class ConstructionExecutionApproval:
    """Explicit workflow approval for one construction-execution decision.

    APPROVED means the named constructor may be attempted once for this exact
    obligation and decision. It does not mean the semantic answer is true,
    should persist, or that the candidate may be adopted.
    """

    execution_decision_id: str
    obligation_id: str
    policy_id: str
    policy_version: str
    approved_constructor_id: str
    decision: str
    source: str = DEFAULT_APPROVAL_SOURCE
    scope: str = SCOPE_ONE_ATTEMPT
    created_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    approval_id: str = ""
    kind: str = APPROVAL_KIND
    contract: str = APPROVAL_SCHEMA

    def __post_init__(self) -> None:
        outcome = _text(self.decision).upper()
        if outcome not in {APPROVAL_APPROVED, APPROVAL_DENIED}:
            raise ValueError(f"unsupported construction approval decision: {self.decision!r}")
        object.__setattr__(self, "decision", outcome)
        object.__setattr__(self, "execution_decision_id", _text(self.execution_decision_id))
        object.__setattr__(self, "obligation_id", _text(self.obligation_id))
        object.__setattr__(self, "policy_id", _text(self.policy_id))
        object.__setattr__(self, "policy_version", _text(self.policy_version))
        object.__setattr__(
            self, "approved_constructor_id", _text(self.approved_constructor_id)
        )
        object.__setattr__(self, "source", _text(self.source) or DEFAULT_APPROVAL_SOURCE)
        object.__setattr__(self, "scope", _text(self.scope) or SCOPE_ONE_ATTEMPT)
        object.__setattr__(self, "kind", APPROVAL_KIND)
        object.__setattr__(self, "contract", APPROVAL_SCHEMA)
        object.__setattr__(self, "metadata", copy_json(self.metadata or {}))
        payload = {
            "execution_decision_id": self.execution_decision_id,
            "obligation_id": self.obligation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "approved_constructor_id": self.approved_constructor_id,
            "decision": self.decision,
            "source": self.source,
            "scope": self.scope,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }
        object.__setattr__(
            self,
            "approval_id",
            self.approval_id or digest(payload, "construction-execution-approval"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "kind": self.kind,
            "approval_id": self.approval_id,
            "execution_decision_id": self.execution_decision_id,
            "obligation_id": self.obligation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "approved_constructor_id": self.approved_constructor_id,
            "scope": self.scope,
            "decision": self.decision,
            "source": self.source,
            "created_at": self.created_at,
            "metadata": copy_json(self.metadata),
        }


@dataclass(frozen=True)
class ConstructionExecutionAuthorization:
    """Deterministic permission to run one already-decided construction.

    AUTHORIZED does not mutate the original REQUIRE_APPROVAL policy decision.
    """

    status: str
    obligation_id: str
    execution_decision_id: str
    approval_id: str
    constructor_id: str
    reason: str
    max_attempts: int = MAX_ATTEMPTS
    contract: str = AUTHORIZATION_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "status": self.status,
            "obligation_id": self.obligation_id,
            "execution_decision_id": self.execution_decision_id,
            "approval_id": self.approval_id,
            "constructor_id": self.constructor_id,
            "max_attempts": self.max_attempts,
            "reason": self.reason,
        }


def construction_execution_approval(
    decision: ConstructionExecutionDecision,
    *,
    outcome: str = APPROVAL_APPROVED,
    source: str = DEFAULT_APPROVAL_SOURCE,
    constructor_id: str | None = None,
    obligation_id: str | None = None,
    execution_decision_id: str | None = None,
    policy_id: str | None = None,
    policy_version: str | None = None,
    scope: str = SCOPE_ONE_ATTEMPT,
    created_at: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> ConstructionExecutionApproval:
    """Build an explicit approval bound to one policy decision."""

    return ConstructionExecutionApproval(
        execution_decision_id=execution_decision_id
        if execution_decision_id is not None
        else decision.decision_id,
        obligation_id=obligation_id if obligation_id is not None else decision.obligation_id,
        policy_id=policy_id if policy_id is not None else decision.policy_id,
        policy_version=policy_version
        if policy_version is not None
        else decision.policy_version,
        approved_constructor_id=constructor_id
        if constructor_id is not None
        else decision.constructor_id,
        decision=outcome,
        source=source,
        scope=scope,
        created_at=created_at,
        metadata=metadata or {"note": "explicit workflow approval; not semantic evidence"},
    )


def _mismatch_reason(approval: ConstructionExecutionApproval, decision: ConstructionExecutionDecision) -> str:
    if approval.execution_decision_id != decision.decision_id:
        return REASON_WRONG_DECISION
    if approval.obligation_id != decision.obligation_id:
        return REASON_WRONG_OBLIGATION
    if (
        approval.policy_id != decision.policy_id
        or approval.policy_version != decision.policy_version
    ):
        return REASON_WRONG_POLICY
    if approval.approved_constructor_id != decision.constructor_id:
        return REASON_WRONG_CONSTRUCTOR
    if approval.scope != SCOPE_ONE_ATTEMPT:
        return REASON_WRONG_SCOPE
    return ""


def authorize_construction_execution(
    decision: ConstructionExecutionDecision,
    approval: ConstructionExecutionApproval | Mapping[str, Any] | None,
    *,
    consumed_approval_ids: Sequence[str] = (),
) -> ConstructionExecutionAuthorization:
    """Authorize one attempt from an explicit approval. Does not run a constructor.

    Does not mutate the policy decision. EXECUTE decisions do not use this
    path. DEFER and DISALLOWED cannot be overridden.
    """

    consumed = {str(item) for item in consumed_approval_ids if str(item)}
    approval_value = (
        approval
        if isinstance(approval, ConstructionExecutionApproval) or approval is None
        else ConstructionExecutionApproval(
            execution_decision_id=str(approval.get("execution_decision_id") or ""),
            obligation_id=str(approval.get("obligation_id") or ""),
            policy_id=str(approval.get("policy_id") or ""),
            policy_version=str(approval.get("policy_version") or ""),
            approved_constructor_id=str(approval.get("approved_constructor_id") or ""),
            decision=str(approval.get("decision") or ""),
            source=str(approval.get("source") or DEFAULT_APPROVAL_SOURCE),
            scope=str(approval.get("scope") or SCOPE_ONE_ATTEMPT),
            created_at=str(approval.get("created_at") or ""),
            metadata=dict(approval.get("metadata") or {}),
            approval_id=str(approval.get("approval_id") or ""),
        )
    )
    approval_id = approval_value.approval_id if approval_value is not None else ""
    base = {
        "obligation_id": decision.obligation_id,
        "execution_decision_id": decision.decision_id,
        "approval_id": approval_id,
        "constructor_id": decision.constructor_id,
        "max_attempts": MAX_ATTEMPTS,
    }
    if decision.execution_authority == AUTHORITY_DISALLOWED:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=REASON_DISALLOWED_CANNOT_BE_APPROVED,
            **base,
        )
    if decision.resource_permission == RESOURCE_UNAVAILABLE or decision.action == ACTION_DEFER:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=REASON_DEFER_CANNOT_BE_APPROVED
            if decision.action == ACTION_DEFER
            else REASON_RESOURCE_UNAVAILABLE,
            **base,
        )
    if decision.action == ACTION_EXECUTE:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=REASON_DECISION_NOT_REQUIRE_APPROVAL,
            **base,
        )
    if decision.action != ACTION_REQUIRE_APPROVAL:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=REASON_DECISION_NOT_REQUIRE_APPROVAL,
            **base,
        )
    if approval_value is None:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=REASON_MISSING_APPROVAL,
            **base,
        )
    mismatch = _mismatch_reason(approval_value, decision)
    if mismatch:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=mismatch,
            **base,
        )
    if approval_value.approval_id in consumed:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_NOT_AUTHORIZED,
            reason=REASON_APPROVAL_CONSUMED,
            **base,
        )
    if approval_value.decision == APPROVAL_DENIED:
        return ConstructionExecutionAuthorization(
            status=AUTHORIZATION_DENIED,
            reason=REASON_DENIED,
            **base,
        )
    return ConstructionExecutionAuthorization(
        status=AUTHORIZATION_AUTHORIZED,
        reason=REASON_AUTHORIZED,
        **base,
    )


def execution_permitted(
    decision: ConstructionExecutionDecision,
    obligation_id: str,
    authorization: ConstructionExecutionAuthorization | None,
    consumed_approval_ids: Sequence[str] = (),
) -> tuple[bool, str]:
    """Return whether the guarded executor may invoke a constructor."""

    if decision.obligation_id != obligation_id:
        return False, REASON_WRONG_OBLIGATION
    if decision.action == ACTION_EXECUTE:
        return True, ""
    if decision.action != ACTION_REQUIRE_APPROVAL:
        return False, REASON_DEFER_CANNOT_BE_APPROVED
    if authorization is None or authorization.status != AUTHORIZATION_AUTHORIZED:
        if authorization is not None and authorization.status == AUTHORIZATION_DENIED:
            return False, REASON_DENIED
        return False, REASON_MISSING_APPROVAL
    if authorization.execution_decision_id != decision.decision_id:
        return False, REASON_WRONG_DECISION
    if authorization.obligation_id != obligation_id:
        return False, REASON_WRONG_OBLIGATION
    if authorization.approval_id in {str(item) for item in consumed_approval_ids}:
        return False, REASON_APPROVAL_CONSUMED
    if decision.execution_authority == AUTHORITY_DISALLOWED:
        return False, REASON_DISALLOWED_CANNOT_BE_APPROVED
    if decision.resource_permission == RESOURCE_UNAVAILABLE:
        return False, REASON_RESOURCE_UNAVAILABLE
    return True, ""
