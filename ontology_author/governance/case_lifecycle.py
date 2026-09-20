"""Pre-adjudication candidate orchestration for semantic construction readiness.

AdoptionPolicy is unchanged. This layer intercepts CONSTRUCTION_REQUIRED
before adjudication and returns CONTEXT_REQUIRED with semantic-construction
provenance. It does not execute obligations or invoke Composer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ontology_author.authority.case import write_case

from .adjudication import (
    load_governance_adjudication,
    validate_governance_adjudication,
    write_governance_adjudication,
)
from .candidate import (
    AdoptionPolicy,
    CandidateEvaluationError,
    _copy,
    _pretty_json,
    decide_candidate_adoption,
    decide_semantic_construction_required,
    write_candidate_adoption,
)
from .model_adjudicator import (
    AdjudicatorTransport,
    ModelAdjudicatorConfig,
    adjudicate_governance_case,
)


def _as_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return _copy(value.to_dict())
    if isinstance(value, Mapping):
        return _copy(value)
    return {}


@dataclass(frozen=True)
class GovernedCaseEvaluationResult:
    """Lifecycle result after case assembly: readiness then adoption or adjudication."""

    case: Mapping[str, Any]
    readiness: Mapping[str, Any]
    adoption_decision: Mapping[str, Any]
    adjudication: Mapping[str, Any] | None
    pending_obligations: Mapping[str, Any] | None
    artifacts: Mapping[str, str]
    adjudicator_invoked: bool
    constructor_invoked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": _copy(self.case),
            "readiness": _copy(self.readiness),
            "adoption_decision": _copy(self.adoption_decision),
            "adjudication": _copy(self.adjudication) if self.adjudication is not None else None,
            "pending_obligations": _copy(self.pending_obligations)
            if self.pending_obligations is not None
            else None,
            "artifacts": dict(self.artifacts),
            "adjudicator_invoked": self.adjudicator_invoked,
            "constructor_invoked": False,
        }


def evaluate_assembled_candidate_case(
    case: Mapping[str, Any],
    *,
    pending_obligations: Any = None,
    derivation: Mapping[str, Any] | Any | None = None,
    membership_gaps: Sequence[Any] | None = None,
    candidate: Mapping[str, Any] | None = None,
    policy: AdoptionPolicy | Mapping[str, Any] | str | None = None,
    adjudication: Mapping[str, Any] | Path | str | None = None,
    adjudicator_config: ModelAdjudicatorConfig | Mapping[str, Any] | None = None,
    adjudicator_transport: AdjudicatorTransport | None = None,
    output_dir: Path | str | None = None,
) -> GovernedCaseEvaluationResult:
    """Branch on case readiness before adjudication.

    CONSTRUCTION_REQUIRED skips the adjudicator and returns CONTEXT_REQUIRED.
    READY_FOR_ADJUDICATION uses the existing adjudication and AdoptionPolicy.
    """

    from ontology_author.governance.case_readiness import (
        STATUS_CONSTRUCTION_REQUIRED,
        assess_governance_case_readiness,
        attach_construction_context,
    )

    selected_policy = AdoptionPolicy.from_value(policy)
    pending_payload = None
    if pending_obligations is not None:
        pending_payload = _as_mapping(pending_obligations)
    readiness = assess_governance_case_readiness(
        pending_obligations=pending_obligations,
        derivation=derivation,
        case=case,
        membership_gaps=membership_gaps,
    )
    case_with_context = attach_construction_context(case, readiness)
    directory = Path(output_dir).resolve() if output_dir is not None else None
    if directory is not None:
        directory.mkdir(parents=True, exist_ok=True)
        write_case(case_with_context, directory)
        (directory / "governance.case.readiness.json").write_text(
            _pretty_json(readiness.to_dict()), encoding="utf-8"
        )

    if readiness.status == STATUS_CONSTRUCTION_REQUIRED:
        decision = decide_semantic_construction_required(
            case_with_context,
            readiness,
            candidate=candidate,
            policy=selected_policy,
        )
        adoption_payload = decision.to_dict()
        if directory is not None:
            write_candidate_adoption(
                adoption_payload,
                directory,
                case=case_with_context,
                policy=selected_policy,
            )
        artifacts = _lifecycle_artifacts(directory)
        return GovernedCaseEvaluationResult(
            case=case_with_context,
            readiness=readiness.to_dict(),
            adoption_decision=adoption_payload,
            adjudication=None,
            pending_obligations=pending_payload,
            artifacts=artifacts,
            adjudicator_invoked=False,
        )

    if adjudication is None and adjudicator_config is None:
        raise CandidateEvaluationError(
            "READY_FOR_ADJUDICATION requires --adjudication or explicit "
            "adjudicator_config; a fake adjudicator is never substituted"
        )
    adjudicator_invoked = False
    if adjudication is not None:
        if isinstance(adjudication, Mapping):
            adjudication_payload = _copy(adjudication)
        else:
            adjudication_payload = load_governance_adjudication(adjudication)
        adjudication_errors = validate_governance_adjudication(
            adjudication_payload, case_with_context
        )
        if adjudication_errors:
            raise CandidateEvaluationError(
                "supplied adjudication is invalid: " + "; ".join(adjudication_errors)
            )
        if directory is not None:
            write_governance_adjudication(adjudication_payload, directory)
    else:
        adjudication_payload = adjudicate_governance_case(
            case_with_context,
            adjudicator_config=adjudicator_config,  # type: ignore[arg-type]
            transport=adjudicator_transport,
            output_dir=directory,
        )
        adjudicator_invoked = True

    adoption = decide_candidate_adoption(
        case_with_context,
        adjudication_payload,
        selected_policy,
        candidate=candidate,
    )
    adoption_payload = adoption.to_dict()
    if directory is not None:
        write_candidate_adoption(
            adoption_payload,
            directory,
            case=case_with_context,
            adjudication=adjudication_payload,
            policy=selected_policy,
        )
    return GovernedCaseEvaluationResult(
        case=case_with_context,
        readiness=readiness.to_dict(),
        adoption_decision=adoption_payload,
        adjudication=adjudication_payload,
        pending_obligations=pending_payload,
        artifacts=_lifecycle_artifacts(directory),
        adjudicator_invoked=adjudicator_invoked,
    )


def _lifecycle_artifacts(directory: Path | None) -> dict[str, str]:
    if directory is None:
        return {}
    names = (
        "governance.case.json",
        "governance.case.readiness.json",
        "governance.adjudication.json",
        "governance.adjudication.invocation.json",
        "candidate.adoption.json",
    )
    return {
        name: str(directory / name)
        for name in names
        if (directory / name).exists()
    }


__all__ = [
    "GovernedCaseEvaluationResult",
    "evaluate_assembled_candidate_case",
]
