"""Durable value objects for one current obligation resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ontology_author.world.core.contract import (
    AdjudicationAssessment,
    CandidateAssessment,
)
from ontology_author.world.core.model import ResolutionStatus


@dataclass(frozen=True)
class Resolution:
    """The current deterministic evaluation of one durable Obligation."""

    obligation_id: str
    status: ResolutionStatus | str
    selected_commitment_id: str | None
    reason: str
    contract_id: str
    contract_revision: str
    candidate_assessments: tuple[CandidateAssessment, ...] = ()
    adjudication_assessments: tuple[AdjudicationAssessment, ...] = ()
    resolution_basis: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        status = ResolutionStatus(self.status)
        object.__setattr__(self, "status", status)
        if status is ResolutionStatus.RESOLVED and not self.selected_commitment_id:
            raise ValueError("a RESOLVED Resolution needs selected_commitment_id")
        if status is not ResolutionStatus.RESOLVED and self.selected_commitment_id:
            raise ValueError(
                f"{status.value} Resolution cannot select a Commitment"
            )

    @property
    def resolution_id(self) -> str:
        return f"resolution:{self.obligation_id}"

    def as_payload(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "obligation_id": self.obligation_id,
            "status": self.status.value,
            "selected_commitment_id": self.selected_commitment_id,
            "reason": self.reason,
            "contract_id": self.contract_id,
            "contract_revision": self.contract_revision,
            "candidate_assessments": [
                item.as_payload() for item in self.candidate_assessments
            ],
            "adjudication_assessments": [
                item.as_payload() for item in self.adjudication_assessments
            ],
            "resolution_basis": [dict(item) for item in self.resolution_basis],
        }


__all__ = ["Resolution"]
