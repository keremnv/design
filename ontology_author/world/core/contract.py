"""Minimal executable Contract admission seam.

This is deliberately a small policy object, not a general Contract language.
It answers one question at the construction boundary: whether the available
provenance is sufficient to admit one asserted semantic tuple for this Contract.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ontology_author.world.core.origins import ConstructionOrigin


class ContractAdmissionError(ValueError):
    """The Contract does not admit an assertion's current basis."""

    def __init__(self, message: str, *, reason: str = "contract_admission") -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class CandidateAssessment:
    """Contract evaluation of one already-recorded Commitment candidate."""

    commitment_id: str
    status: str
    reason: str
    warrant_authorities: tuple[str, ...] = ()
    authority_basis: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        value = str(self.status).strip().upper()
        if value not in {"SUFFICIENT", "INSUFFICIENT"}:
            raise ValueError(f"unknown candidate assessment status {self.status!r}")
        object.__setattr__(self, "status", value)
        object.__setattr__(
            self,
            "warrant_authorities",
            tuple(
                sorted(
                    {
                        str(item).strip().upper()
                        for item in self.warrant_authorities
                        if str(item).strip()
                    }
                )
            ),
        )
        basis: list[Mapping[str, Any]] = []
        for item in self.authority_basis:
            if isinstance(item, Mapping):
                basis.append({str(key): value for key, value in item.items()})
        basis.sort(key=lambda item: repr(sorted(item.items())))
        object.__setattr__(self, "authority_basis", tuple(basis))

    def as_payload(self) -> dict[str, object]:
        return {
            "commitment_id": self.commitment_id,
            "status": self.status,
            "reason": self.reason,
            "warrant_authorities": list(self.warrant_authorities),
            "authority_basis": [dict(item) for item in self.authority_basis],
        }


@dataclass(frozen=True)
class Contract:
    """A minimal Contract identity plus executable admission rules.

    Source-backed World BASE assertions remain the default. A Contract must
    explicitly list construction origins it accepts without SOURCE grounding.
    An application may additionally name the relation vocabulary that those
    semantic origins may populate; semantic-reference relations separately
    need explicit permission. ``resolution_warrant_kinds`` is a separate,
    conservative standard for deciding which externally assigned
    evidence-authority classes may govern an Obligation; it does not affect
    admission.
    """

    contract_id: str
    contract_revision: str
    semantic_origins: frozenset[str] = field(default_factory=frozenset)
    allow_semantic_reference_relations: bool = False
    semantic_relations: frozenset[str] = field(default_factory=frozenset)
    resolution_warrant_kinds: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        identity = str(self.contract_id or "").strip()
        revision = str(self.contract_revision or "").strip()
        if not identity or not revision:
            raise ValueError("contract identity and revision must both be non-empty")
        object.__setattr__(self, "contract_id", identity)
        object.__setattr__(self, "contract_revision", revision)
        object.__setattr__(
            self,
            "semantic_origins",
            frozenset(
                str(item.value if hasattr(item, "value") else item).strip()
                for item in self.semantic_origins
                if str(item.value if hasattr(item, "value") else item).strip()
            ),
        )
        object.__setattr__(
            self,
            "semantic_relations",
            frozenset(
                str(item).strip()
                for item in self.semantic_relations
                if str(item).strip()
            ),
        )
        object.__setattr__(
            self,
            "resolution_warrant_kinds",
            frozenset(
                str(item).strip().upper()
                for item in self.resolution_warrant_kinds
                if str(item).strip()
            ),
        )

    @classmethod
    def default(cls) -> "Contract":
        """The legacy construction regime: World BASE requires SOURCE."""

        return cls("ontology-author-default", "1")

    @classmethod
    def from_identity(cls, identity: dict[str, Any] | None) -> "Contract":
        """Reconstruct a conservative read-side Contract from stored identity."""

        if not identity:
            return cls.default()
        return cls(
            str(identity["contract_id"]),
            str(identity["contract_revision"]),
        )

    def identity(self) -> dict[str, str]:
        return {
            "contract_id": self.contract_id,
            "contract_revision": self.contract_revision,
        }

    def assess_candidate(
        self,
        *,
        obligation: Mapping[str, Any],
        commitment: Mapping[str, Any],
        warrant: Mapping[str, Any],
        warrant_authorities: Iterable[str] = (),
        authority_basis: Iterable[Mapping[str, Any]] = (),
    ) -> CandidateAssessment:
        """Assess warrant sufficiency for resolution, separately from admission.

        ``warrant_authorities`` and ``authority_basis`` are supplied by the
        runtime after it has joined Warrant source identities to an external
        evidence-authority configuration. The Contract sees only the resulting
        authority classes; it never treats Warrant prose, filenames, origins,
        or constructor metadata as authority.
        """

        commitment_id = str(commitment.get("commitment_id") or "")
        obligation_id = str(obligation.get("obligation_id") or "")
        del warrant
        authorities = tuple(
            sorted({str(item).strip().upper() for item in warrant_authorities if str(item).strip()})
        )
        basis = tuple(authority_basis)
        sufficient = tuple(sorted(set(authorities) & set(self.resolution_warrant_kinds)))
        if sufficient:
            return CandidateAssessment(
                commitment_id=commitment_id,
                status="SUFFICIENT",
                reason=(
                    f"Commitment {commitment_id} has Contract-authorized "
                    f"resolution authority for {obligation_id}: {', '.join(sufficient)}."
                ),
                warrant_authorities=authorities,
                authority_basis=basis,
            )
        if not self.resolution_warrant_kinds:
            reason = (
                f"Contract {self.contract_id}@{self.contract_revision} has no "
                "configured resolution warrant standard."
            )
        elif authorities:
            reason = (
                f"Commitment {commitment_id} has warrant authorities "
                f"{', '.join(authorities)}, none accepted for resolution by "
                f"Contract {self.contract_id}@{self.contract_revision}."
            )
        else:
            reason = (
                f"Commitment {commitment_id} has no structured resolution "
                "authority binding for its Warrant evidence."
            )
        return CandidateAssessment(
            commitment_id=commitment_id,
            status="INSUFFICIENT",
            reason=reason,
            warrant_authorities=authorities,
            authority_basis=basis,
        )

    def admit_assertion(
        self,
        *,
        relation: str,
        scope: str,
        mode: str,
        origin: ConstructionOrigin | str,
        has_source_grounding: bool,
        has_provenance: bool,
        has_construction_method: bool,
        semantic_reference_kinds: Iterable[str] = (),
        authority: Any | None = None,
    ) -> None:
        """Admit one asserted tuple or raise ``ContractAdmissionError``.

        ``authority`` is intentionally an unused extension point. No authority
        model is introduced in this slice, but admission has a stable place to
        receive one later.
        """

        del authority
        relation_name = str(relation)
        scope_name = str(scope)
        mode_name = str(mode)
        origin_name = str(origin.value if hasattr(origin, "value") else origin)
        references = tuple(str(item) for item in semantic_reference_kinds)

        if mode_name == "DERIVED":
            return
        if not has_provenance:
            raise ContractAdmissionError(
                f"Contract {self.contract_id!r} cannot admit {relation_name!r}: "
                "the assertion has no provenance"
            )
        if scope_name == "PURPOSE":
            return
        if scope_name != "WORLD":
            raise ContractAdmissionError(
                f"Contract {self.contract_id!r} cannot admit {relation_name!r}: "
                f"unknown admission scope {scope_name!r}"
            )

        if references and not self.allow_semantic_reference_relations:
            raise ContractAdmissionError(
                f"Contract {self.contract_id!r} does not authorize semantic-reference "
                f"relation {relation_name!r}"
            )

        if origin_name in self.semantic_origins:
            # An empty allow-list preserves the first kernel slice's
            # origin-level behavior. A non-empty list lets an application
            # Contract name the semantic decision vocabulary it admits.
            if (
                self.semantic_relations
                and not references
                and relation_name not in self.semantic_relations
            ):
                raise ContractAdmissionError(
                    f"Contract {self.contract_id!r} does not authorize semantic "
                    f"relation {relation_name!r}",
                    reason="semantic_relation_not_authorized",
                )
            if has_source_grounding:
                return
            if not has_construction_method:
                raise ContractAdmissionError(
                    f"Contract {self.contract_id!r} requires a construction method "
                    f"for semantic assertion {relation_name!r}"
                )
            return

        if has_source_grounding:
            return

        raise ContractAdmissionError(
            f"WORLD BASE {relation_name!r} requires SOURCE grounding under Contract "
            f"{self.contract_id!r}",
            reason="ungrounded_world_base",
        )
