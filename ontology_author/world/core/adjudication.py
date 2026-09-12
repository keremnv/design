"""Durable value object for one recorded adjudicative determination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Adjudication:
    """An immutable selection of an existing candidate for an Obligation.

    ``authority_basis`` records what external decision/source identity the
    adjudication cites.  It deliberately does not contain trusted authority;
    the resolver derives that separately from the adjudication-authority
    configuration.
    """

    adjudication_id: str
    obligation_id: str
    selected_commitment_id: str
    authority_basis: Mapping[str, Any]
    contract_id: str
    contract_revision: str
    created_revision: int | None = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "adjudication_id": self.adjudication_id,
            "obligation_id": self.obligation_id,
            "selected_commitment_id": self.selected_commitment_id,
            "authority_basis": dict(self.authority_basis),
            "contract_id": self.contract_id,
            "contract_revision": self.contract_revision,
            "created_revision": self.created_revision,
        }


__all__ = ["Adjudication"]
