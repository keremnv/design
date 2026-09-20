"""Deterministic MembershipGap -> CLASS_MEMBERSHIP ConstructionObligation.

This is application/workflow machinery, not a World-kernel primitive and not
a semantic planner.  It copies the already-specified class and snapshot-local
subject from a supported MembershipGap.  It does not search a repository,
invoke a model, choose a different referent, or execute construction.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ontology_author.semantic_binding.schemas import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    ConstructionObligation,
    copy_json,
    digest,
)
from ontology_author.governance.checkout_invariant import CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE
from ontology_author.semantic_binding.membership import (
    GAP_REASON_NO_EVIDENCE,
    MEMBERSHIP_STATUS_ESTABLISHED,
    MEMBERSHIP_STATUS_PRESERVED,
    MEMBERSHIP_STATUS_UNKNOWN,
    MembershipGap,
    class_membership_obligation,
)

SYNTHESIS_PROFILE = "membership-gap-obligation-synthesis/v1"
SYNTHESIS_VERSION = 1
GENERATION_METHOD = "DETERMINISTIC_GAP_SYNTHESIS"
TRIGGER_MEMBERSHIP_GAP = "MEMBERSHIP_GAP"
STATUS_SYNTHESIZED = "SYNTHESIZED"
STATUS_CANNOT_SYNTHESIZE = "CANNOT_SYNTHESIZE"
STATUS_NOT_REQUIRED = "NOT_REQUIRED"
REASON_MISSING_SEMANTIC_CLASS = "MISSING_SEMANTIC_CLASS"
REASON_MISSING_PROGRAM_SUBJECT = "MISSING_PROGRAM_SUBJECT"
REASON_MISSING_SNAPSHOT = "MISSING_SNAPSHOT"
REASON_MISSING_REQUESTING_CONSUMER = "MISSING_REQUESTING_CONSUMER"
REASON_MISSING_AUTHORITY_REFS = "MISSING_AUTHORITY_REFS"
REASON_UNSUPPORTED_GAP_KIND = "UNSUPPORTED_GAP_KIND"
REASON_AMBIGUOUS_SCOPE = "AMBIGUOUS_SCOPE"
REASON_MALFORMED_GAP = "MALFORMED_GAP"
REASON_MEMBERSHIP_ALREADY_RESOLVED = "MEMBERSHIP_ALREADY_RESOLVED"
SUPPORTED_GAP_REASONS = frozenset({GAP_REASON_NO_EVIDENCE})
RESOLVED_MEMBERSHIP_STATUSES = frozenset(
    {MEMBERSHIP_STATUS_ESTABLISHED, MEMBERSHIP_STATUS_PRESERVED}
)
_ANSWER_KEYS = (
    "membership_result",
    "result",
    "preferred_model",
    "confidence",
    "expected_result",
    "NON_MEMBER",
    "IS_NOT_PROVIDER",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def parse_membership_gap(gap: MembershipGap | Mapping[str, Any] | None) -> MembershipGap | None:
    if isinstance(gap, MembershipGap):
        return gap
    payload = _as_mapping(gap)
    if payload is None:
        return None
    return MembershipGap.from_dict(payload)


@dataclass(frozen=True)
class MembershipObligationContext:
    """Deterministic references already known to the requesting consumer."""

    purpose: str
    program_scope: str
    authority_refs: tuple[str, ...]
    requesting_definition_id: str = ""
    evaluator_id: str = ""
    membership_status: str = MEMBERSHIP_STATUS_UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose,
            "program_scope": self.program_scope,
            "authority_refs": list(self.authority_refs),
            "requesting_definition_id": self.requesting_definition_id,
            "evaluator_id": self.evaluator_id,
            "membership_status": self.membership_status,
        }


def membership_obligation_context(
    *,
    purpose: str = "",
    program_scope: str = "",
    authority_refs: Sequence[str] = (),
    requesting_definition_id: str = "",
    evaluator_id: str = "",
    membership_status: str = MEMBERSHIP_STATUS_UNKNOWN,
) -> MembershipObligationContext:
    refs = tuple(
        dict.fromkeys(_text(item) for item in authority_refs if _text(item))
    )
    return MembershipObligationContext(
        purpose=_text(purpose),
        program_scope=_text(program_scope),
        authority_refs=refs,
        requesting_definition_id=_text(requesting_definition_id),
        evaluator_id=_text(evaluator_id),
        membership_status=_text(membership_status) or MEMBERSHIP_STATUS_UNKNOWN,
    )


def context_from_invariant_definition(
    definition: Any,
    *,
    membership_status: str = MEMBERSHIP_STATUS_UNKNOWN,
) -> MembershipObligationContext:
    payload = definition.to_dict() if hasattr(definition, "to_dict") else dict(definition)
    klass = _text(payload.get("provider_semantic"))
    return membership_obligation_context(
        purpose=f"class-membership:{klass}" if klass else "",
        program_scope=CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE,
        authority_refs=tuple(payload.get("authority_refs") or ()),
        requesting_definition_id=_text(payload.get("definition_id")),
        evaluator_id=_text(payload.get("evaluator_id")),
        membership_status=membership_status,
    )


def class_membership_obligation_key(
    *,
    semantic_class: str,
    program_subject: str,
    snapshot: str,
    purpose: str,
    program_scope: str,
) -> str:
    return digest(
        {
            "obligation_kind": CLASS_MEMBERSHIP_OBLIGATION_KIND,
            "semantic_class": semantic_class,
            "program_subject": program_subject,
            "snapshot": snapshot,
            "purpose": purpose,
            "program_scope": program_scope,
            "synthesis_profile": SYNTHESIS_PROFILE,
            "synthesis_version": SYNTHESIS_VERSION,
        },
        "construction-obligation",
    )


@dataclass(frozen=True)
class ObligationSynthesisFailure:
    reason: str
    status: str = STATUS_CANNOT_SYNTHESIZE
    gap: Mapping[str, Any] | None = None
    model_invoked: bool = False
    repository_searched: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "gap": copy_json(self.gap) if self.gap is not None else None,
            "obligation": None,
            "model_invoked": False,
            "repository_searched": False,
        }


@dataclass(frozen=True)
class SynthesizedClassMembershipObligation:
    obligation: ConstructionObligation
    gap: MembershipGap
    provenance: Mapping[str, Any]
    construction_context: Mapping[str, Any]
    status: str = STATUS_SYNTHESIZED
    model_invoked: bool = False
    repository_searched: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = self.obligation.to_dict()
        return {
            "status": self.status,
            "obligation": payload,
            "gap": self.gap.to_dict(),
            "provenance": copy_json(self.provenance),
            "construction_context": copy_json(self.construction_context),
            "model_invoked": False,
            "repository_searched": False,
        }


@dataclass(frozen=True)
class PendingConstructionObligations:
    """Application view of explicitly synthesized pending obligations.

    Derived only from supplied MembershipGaps, never from repository-wide
    semantic discovery.  This is not a scheduler.
    """

    items: tuple[SynthesizedClassMembershipObligation, ...]
    failures: tuple[ObligationSynthesisFailure, ...] = ()
    suppressed: tuple[ObligationSynthesisFailure, ...] = ()
    model_invoked: bool = False
    repository_searched: bool = False

    @property
    def obligations(self) -> tuple[ConstructionObligation, ...]:
        return tuple(item.obligation for item in self.items)

    @property
    def fan_out(self) -> int:
        return len(self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligations": [item.obligation.to_dict() for item in self.items],
            "items": [item.to_dict() for item in self.items],
            "failures": [item.to_dict() for item in self.failures],
            "suppressed": [item.to_dict() for item in self.suppressed],
            "fan_out": self.fan_out,
            "model_invoked": False,
            "repository_searched": False,
        }


def _failure(
    reason: str,
    gap: MembershipGap | Mapping[str, Any] | None = None,
    *,
    status: str = STATUS_CANNOT_SYNTHESIZE,
) -> ObligationSynthesisFailure:
    payload = None
    if isinstance(gap, MembershipGap):
        payload = gap.to_dict()
    elif isinstance(gap, Mapping):
        payload = dict(gap)
    return ObligationSynthesisFailure(reason=reason, status=status, gap=payload)


def _purpose_for(gap: MembershipGap, context: MembershipObligationContext) -> str:
    if context.purpose:
        return context.purpose
    if gap.semantic_class:
        return f"class-membership:{gap.semantic_class}"
    return ""


def _construction_context(
    gap: MembershipGap,
    context: MembershipObligationContext,
    requested_by: Sequence[str],
) -> dict[str, Any]:
    return {
        "semantic_class": gap.semantic_class,
        "program_subject": gap.program_subject,
        "snapshot": gap.snapshot,
        "declared_scope": context.program_scope,
        "requesting_invariants": list(requested_by),
        "required_construction_profile": CLASS_MEMBERSHIP_ADMISSION_PROFILE,
        "evaluator_id": context.evaluator_id,
        "purpose": _purpose_for(gap, context),
    }


def _provenance(
    gaps: Sequence[MembershipGap],
    context: MembershipObligationContext,
) -> dict[str, Any]:
    snapshots = tuple(dict.fromkeys(item.snapshot for item in gaps))
    reasons = tuple(dict.fromkeys(item.reason for item in gaps))
    requested = tuple(dict.fromkeys(item.requested_by for item in gaps if item.requested_by))
    return {
        "trigger": TRIGGER_MEMBERSHIP_GAP,
        "trigger_gap_id": gaps[0].gap_id if len(gaps) == 1 else "",
        "trigger_gap_ids": [item.gap_id for item in gaps],
        "requested_by": list(requested),
        "source_snapshot": snapshots[0] if len(snapshots) == 1 else "",
        "source_snapshots": list(snapshots),
        "gap_reason": reasons[0] if len(reasons) == 1 else "",
        "gap_reasons": list(reasons),
        "generation_method": GENERATION_METHOD,
        "generation_profile": SYNTHESIS_PROFILE,
        "generation_version": SYNTHESIS_VERSION,
        "evaluator_id": context.evaluator_id,
    }


def _assert_no_semantic_answer(obligation: ConstructionObligation) -> None:
    payload = obligation.to_dict()
    for key in _ANSWER_KEYS:
        if key in payload:
            raise ValueError(f"synthesized obligation must not carry {key}")


def synthesize_class_membership_obligation(
    gap: MembershipGap | Mapping[str, Any] | None,
    context: MembershipObligationContext | Mapping[str, Any] | None = None,
) -> SynthesizedClassMembershipObligation | ObligationSynthesisFailure:
    """Copy a supported MembershipGap into one CLASS_MEMBERSHIP obligation.

    Returns CANNOT_SYNTHESIZE rather than a malformed obligation.  Does not
    execute construction.
    """

    parsed = parse_membership_gap(gap)
    if parsed is None:
        return _failure(REASON_MALFORMED_GAP, gap)
    ctx_payload = _normalized_context(context)
    if ctx_payload.membership_status in RESOLVED_MEMBERSHIP_STATUSES:
        return _failure(
            REASON_MEMBERSHIP_ALREADY_RESOLVED,
            parsed,
            status=STATUS_NOT_REQUIRED,
        )
    klass = _text(parsed.semantic_class)
    subject = _text(parsed.program_subject)
    snapshot = _text(parsed.snapshot)
    requested_by = _text(parsed.requested_by)
    reason = _text(parsed.reason)
    if not klass:
        return _failure(REASON_MISSING_SEMANTIC_CLASS, parsed)
    if not subject:
        return _failure(REASON_MISSING_PROGRAM_SUBJECT, parsed)
    if not snapshot:
        return _failure(REASON_MISSING_SNAPSHOT, parsed)
    if not requested_by:
        return _failure(REASON_MISSING_REQUESTING_CONSUMER, parsed)
    if reason not in SUPPORTED_GAP_REASONS:
        return _failure(REASON_UNSUPPORTED_GAP_KIND, parsed)
    purpose = _purpose_for(parsed, ctx_payload)
    program_scope = ctx_payload.program_scope
    if not purpose or not program_scope:
        return _failure(REASON_AMBIGUOUS_SCOPE, parsed)
    if not ctx_payload.authority_refs:
        return _failure(REASON_MISSING_AUTHORITY_REFS, parsed)
    obligation_id = class_membership_obligation_key(
        semantic_class=klass,
        program_subject=subject,
        snapshot=snapshot,
        purpose=purpose,
        program_scope=program_scope,
    )
    obligation = class_membership_obligation(
        obligation_id=obligation_id,
        purpose=purpose,
        authority_refs=ctx_payload.authority_refs,
        semantic_class=klass,
        program_subject=subject,
        program_scope=program_scope,
    )
    _assert_no_semantic_answer(obligation)
    return SynthesizedClassMembershipObligation(
        obligation=obligation,
        gap=parsed,
        provenance=_provenance((parsed,), ctx_payload),
        construction_context=_construction_context(parsed, ctx_payload, (requested_by,)),
    )


def _normalized_context(
    context: MembershipObligationContext | Mapping[str, Any] | None,
    synthesized: SynthesizedClassMembershipObligation | None = None,
) -> MembershipObligationContext:
    if isinstance(context, MembershipObligationContext):
        return context
    mapping = _as_mapping(context) or {}
    if synthesized is not None:
        requested = tuple(synthesized.provenance.get("requested_by") or ())
        return membership_obligation_context(
            purpose=synthesized.obligation.purpose,
            program_scope=synthesized.obligation.program_scope,
            authority_refs=synthesized.obligation.authority_refs,
            requesting_definition_id=_text(requested[0] if requested else ""),
            evaluator_id=_text(synthesized.provenance.get("evaluator_id")),
            membership_status=MEMBERSHIP_STATUS_UNKNOWN,
        )
    return membership_obligation_context(
        purpose=_text(mapping.get("purpose")),
        program_scope=_text(mapping.get("program_scope")),
        authority_refs=tuple(mapping.get("authority_refs") or ()),
        requesting_definition_id=_text(
            mapping.get("requesting_definition_id") or mapping.get("definition_id")
        ),
        evaluator_id=_text(mapping.get("evaluator_id")),
        membership_status=_text(mapping.get("membership_status"))
        or MEMBERSHIP_STATUS_UNKNOWN,
    )


def collect_pending_class_membership_obligations(
    gaps: Sequence[MembershipGap | Mapping[str, Any] | None],
    context: MembershipObligationContext | Mapping[str, Any] | None,
) -> PendingConstructionObligations:
    """Deduplicate equivalent CLASS_MEMBERSHIP questions; keep gap provenance."""

    synthesized: dict[str, SynthesizedClassMembershipObligation] = {}
    gap_groups: dict[str, list[MembershipGap]] = {}
    failures: list[ObligationSynthesisFailure] = []
    suppressed: list[ObligationSynthesisFailure] = []
    for item in gaps:
        result = synthesize_class_membership_obligation(item, context)
        if isinstance(result, ObligationSynthesisFailure):
            if result.status == STATUS_NOT_REQUIRED:
                suppressed.append(result)
            else:
                failures.append(result)
            continue
        key = result.obligation.obligation_id
        gap_groups.setdefault(key, []).append(result.gap)
        if key not in synthesized:
            synthesized[key] = result
            continue
        merged_gaps = gap_groups[key]
        ctx = _normalized_context(context, result)
        requested = tuple(
            dict.fromkeys(gap.requested_by for gap in merged_gaps if gap.requested_by)
        )
        synthesized[key] = SynthesizedClassMembershipObligation(
            obligation=result.obligation,
            gap=merged_gaps[0],
            provenance=_provenance(merged_gaps, ctx),
            construction_context=_construction_context(merged_gaps[0], ctx, requested),
        )
    return PendingConstructionObligations(
        items=tuple(synthesized.values()),
        failures=tuple(failures),
        suppressed=tuple(suppressed),
    )


def pending_class_membership_obligations_from_derivation(
    derivation: Any,
    context: MembershipObligationContext | Mapping[str, Any] | None,
) -> PendingConstructionObligations:
    receipt = {}
    if hasattr(derivation, "evaluation_receipt"):
        receipt = dict(derivation.evaluation_receipt or {})
    elif isinstance(derivation, Mapping):
        receipt = dict(derivation.get("evaluation_receipt") or derivation)
    gaps = list(receipt.get("membership_gaps") or [])
    return collect_pending_class_membership_obligations(gaps, context)
