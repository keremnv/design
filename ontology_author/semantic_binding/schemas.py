"""Record schemas for the bounded semantic persistence experiment.

These are application records, not World primitives and not executable
contracts.  In particular, a ``SemanticCandidate`` is never itself a World
assertion and does not carry a model-authored persistence decision.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ontology_author.authority.schemas import (
    RelationSupport,
)

OBLIGATION_SCHEMA = "construction_obligation/v0"
CANDIDATE_SCHEMA = "semantic_candidate/v0"
ADMISSION_DECISION_SCHEMA = "persistence_admission/v0"
WARRANT_SCHEMA = "semantic_commitment_warrant/v0"
PERSISTENCE_OUTCOMES = frozenset(
    {
        "DROP",
        "RECORD_UNRESOLVED",
        "PERSIST_SNAPSHOT_FACT",
        "PERSIST_COMMITMENT",
    }
)
CONSTRUCTION_OBLIGATION_KIND = "PROGRAM_REALIZATION"
PROGRAM_RELATIONSHIP_OBLIGATION_KIND = "PROGRAM_RELATIONSHIP"
PROGRAM_INVARIANT_OBLIGATION_KIND = "PROGRAM_INVARIANT"
CLASS_MEMBERSHIP_OBLIGATION_KIND = "CLASS_MEMBERSHIP"
CONSTRUCTION_OBLIGATION_KINDS = frozenset(
    {
        CONSTRUCTION_OBLIGATION_KIND,
        PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        PROGRAM_INVARIANT_OBLIGATION_KIND,
        CLASS_MEMBERSHIP_OBLIGATION_KIND,
    }
)
CLASS_MEMBERSHIP_ADMISSION_PROFILE = "semantic-class-membership/v1"
CLASS_MEMBERSHIP_RELATION = "semantic_program_membership"
CLASS_MEMBERSHIP_TUPLE_SHAPE = {
    "semantic_class": "SEMANTIC",
    "program_manifestation": "PROGRAM",
}
CLASS_MEMBERSHIP_PROGRAM_ROLE_KINDS = {
    "program_manifestation": ("callable", "method"),
}
CLASS_MEMBERSHIP_RESULTS = frozenset({"MEMBER", "UNRESOLVED"})
# Trusted structural typing for the v0 relational construction profile.  This
# says what kind of program spine entity may fill each role; it deliberately
# does not identify which entity is the semantic answer.
PROGRAM_RELATIONSHIP_PROGRAM_ROLE_KINDS = {
    "checkout_entry": ("call_site",),
    "service": ("callable", "method"),
    "service_call_site": ("call_site",),
    "gateway": ("callable", "method"),
    "gateway_call_site": ("call_site",),
    "provider": ("callable", "method"),
}
PROGRAM_INVARIANT_PROGRAM_ROLE_KINDS = {
    "scope_root": ("callable", "method"),
}
MAINTENANCE_DEPENDENCY_KINDS = frozenset(
    {
        "program_identity",
        "relation_tuple",
        "structural_context",
        "manifestation_property",
    }
)


class EvidenceClass(StrEnum):
    AUTHORITY_GROUNDING = "AUTHORITY_GROUNDING"
    PROGRAM_GROUNDING = "PROGRAM_GROUNDING"
    MECHANICAL_GROUNDING = "MECHANICAL_GROUNDING"
    SUPPORTING_MATERIAL = "SUPPORTING_MATERIAL"


class SemanticPolarity(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class CandidateValidationError(ValueError):
    """A candidate is malformed or outside its declared bounded input."""

    def __init__(self, errors: Sequence[str] | str):
        if isinstance(errors, str):
            values = [errors]
        else:
            values = [str(item) for item in errors if str(item)]
        self.errors = tuple(sorted(set(values)))
        super().__init__("; ".join(self.errors) or "invalid semantic candidate")


class SemanticPersistenceError(ValueError):
    """The deterministic semantic persistence boundary was violated."""


class SemanticConstructionInvocationError(SemanticPersistenceError):
    """A bounded semantic-construction invocation failed at runtime."""

    def __init__(self, message: str, receipt: Mapping[str, Any]):
        super().__init__(message)
        self.receipt = copy_json(receipt)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any, prefix: str) -> str:
    return f"{prefix}:{hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()[:32]}"


def copy_json(value: Any) -> Any:
    return json.loads(canonical_json(value))


def _nonempty(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _strings(values: Sequence[Any], field_name: str) -> tuple[str, ...]:
    result = tuple(sorted({str(item).strip() for item in values if str(item).strip()}))
    if not result:
        raise ValueError(f"{field_name} must contain at least one value")
    return result


@dataclass(frozen=True)
class ConstructionObligation:
    """A narrow semantic question that construction is allowed to answer."""

    obligation_id: str
    purpose: str
    authority_refs: tuple[str, ...]
    semantic_subject: str
    semantic_relation: str
    question: str
    program_scope: str
    allowed_program_endpoints: tuple[str, ...]
    required_evidence_classes: tuple[str, ...]
    tuple_shape: Mapping[str, str]
    obligation_kind: str = CONSTRUCTION_OBLIGATION_KIND
    admission_profile: str = "semantic-binding/v1"
    contract: str = OBLIGATION_SCHEMA

    def __post_init__(self) -> None:
        if self.contract != OBLIGATION_SCHEMA:
            raise ValueError(
                f"unsupported ConstructionObligation schema: {self.contract}"
            )
        object.__setattr__(
            self, "obligation_id", _nonempty(self.obligation_id, "obligation_id")
        )
        object.__setattr__(self, "purpose", _nonempty(self.purpose, "purpose"))
        object.__setattr__(
            self, "authority_refs", _strings(self.authority_refs, "authority_refs")
        )
        object.__setattr__(
            self,
            "semantic_subject",
            _nonempty(self.semantic_subject, "semantic_subject"),
        )
        object.__setattr__(
            self,
            "semantic_relation",
            _nonempty(self.semantic_relation, "semantic_relation"),
        )
        object.__setattr__(self, "question", _nonempty(self.question, "question"))
        object.__setattr__(
            self,
            "obligation_kind",
            _nonempty(self.obligation_kind, "obligation_kind").upper(),
        )
        if self.obligation_kind not in CONSTRUCTION_OBLIGATION_KINDS:
            raise ValueError(
                "v0 ConstructionObligation kind must be one of "
                + ", ".join(sorted(CONSTRUCTION_OBLIGATION_KINDS))
            )
        object.__setattr__(
            self, "program_scope", _nonempty(self.program_scope, "program_scope")
        )
        object.__setattr__(
            self,
            "allowed_program_endpoints",
            _strings(self.allowed_program_endpoints, "allowed_program_endpoints"),
        )
        classes = _strings(self.required_evidence_classes, "required_evidence_classes")
        unknown = set(classes) - {item.value for item in EvidenceClass}
        if unknown:
            raise ValueError(f"unknown evidence classes: {sorted(unknown)}")
        object.__setattr__(self, "required_evidence_classes", classes)
        shape = {
            str(key): str(value).upper()
            for key, value in dict(self.tuple_shape).items()
        }
        if not shape:
            raise ValueError("tuple_shape must contain at least one role")
        if any(value not in {"SEMANTIC", "PROGRAM"} for value in shape.values()):
            raise ValueError("tuple_shape values must be SEMANTIC or PROGRAM")
        if sum(value == "PROGRAM" for value in shape.values()) < 1:
            raise ValueError("tuple_shape must include a PROGRAM role")
        object.__setattr__(self, "tuple_shape", dict(sorted(shape.items())))
        object.__setattr__(
            self,
            "admission_profile",
            _nonempty(self.admission_profile, "admission_profile"),
        )
        if self.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND:
            if self.admission_profile != CLASS_MEMBERSHIP_ADMISSION_PROFILE:
                raise ValueError(
                    "CLASS_MEMBERSHIP requires admission profile "
                    + CLASS_MEMBERSHIP_ADMISSION_PROFILE
                )
            if dict(self.tuple_shape) != CLASS_MEMBERSHIP_TUPLE_SHAPE:
                raise ValueError(
                    "CLASS_MEMBERSHIP requires tuple_shape "
                    + str(CLASS_MEMBERSHIP_TUPLE_SHAPE)
                )
            if self.semantic_relation != CLASS_MEMBERSHIP_RELATION:
                raise ValueError(
                    "CLASS_MEMBERSHIP relation is "
                    + CLASS_MEMBERSHIP_RELATION
                    + "; the constructor cannot choose it"
                )
            if len(self.allowed_program_endpoints) != 1:
                raise ValueError(
                    "CLASS_MEMBERSHIP program subject must be exactly one "
                    "snapshot-local manifestation"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ConstructionObligation:
        return cls(
            obligation_id=str(payload.get("obligation_id") or payload.get("id") or ""),
            purpose=str(payload.get("purpose") or ""),
            authority_refs=tuple(payload.get("authority_refs") or ()),
            semantic_subject=str(payload.get("semantic_subject") or ""),
            semantic_relation=str(payload.get("semantic_relation") or ""),
            question=str(payload.get("question") or ""),
            obligation_kind=str(
                payload.get("obligation_kind")
                or payload.get("kind")
                or CONSTRUCTION_OBLIGATION_KIND
            ),
            program_scope=str(payload.get("program_scope") or ""),
            allowed_program_endpoints=tuple(
                payload.get("allowed_program_endpoints") or ()
            ),
            required_evidence_classes=tuple(
                payload.get("required_evidence_classes") or ()
            ),
            tuple_shape=dict(payload.get("tuple_shape") or {}),
            admission_profile=str(
                payload.get("admission_profile") or "semantic-binding/v1"
            ),
            contract=str(payload.get("contract") or OBLIGATION_SCHEMA),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "obligation_id": self.obligation_id,
            "purpose": self.purpose,
            "authority_refs": list(self.authority_refs),
            "semantic_subject": self.semantic_subject,
            "semantic_relation": self.semantic_relation,
            "question": self.question,
            "obligation_kind": self.obligation_kind,
            "program_scope": self.program_scope,
            "allowed_program_endpoints": list(self.allowed_program_endpoints),
            "required_evidence_classes": list(self.required_evidence_classes),
            "tuple_shape": dict(self.tuple_shape),
            "admission_profile": self.admission_profile,
        }


@dataclass(frozen=True)
class SemanticCandidate:
    """A bounded semantic proposal, never a durable World assertion."""

    obligation_id: str
    claim_kind: str
    relation_name: str
    tuple: Mapping[str, str]
    polarity: str
    semantic_endpoint_refs: tuple[str, ...]
    program_endpoint_refs: tuple[str, ...]
    support_kind: str
    endpoint_resolution: Mapping[str, str]
    evidence_refs: tuple[Mapping[str, str], ...]
    program_scope: str
    maintenance_dependencies: tuple[Mapping[str, Any], ...] = ()
    completeness_refs: tuple[str, ...] = ()
    construction_method: str = ""
    membership_result: str = ""
    candidate_id: str = ""
    contract: str = CANDIDATE_SCHEMA

    def __post_init__(self) -> None:
        if self.contract != CANDIDATE_SCHEMA:
            raise ValueError(f"unsupported SemanticCandidate schema: {self.contract}")
        object.__setattr__(
            self, "obligation_id", _nonempty(self.obligation_id, "obligation_id")
        )
        object.__setattr__(
            self, "claim_kind", _nonempty(self.claim_kind, "claim_kind").upper()
        )
        object.__setattr__(
            self, "relation_name", _nonempty(self.relation_name, "relation_name")
        )
        tuple_values = {
            str(key): _nonempty(value, f"tuple.{key}")
            for key, value in dict(self.tuple).items()
        }
        if not tuple_values:
            raise ValueError("candidate tuple must be non-empty")
        object.__setattr__(self, "tuple", dict(sorted(tuple_values.items())))
        try:
            polarity = SemanticPolarity(self.polarity).value
        except ValueError as exc:
            raise ValueError(f"unknown candidate polarity: {self.polarity}") from exc
        object.__setattr__(self, "polarity", polarity)
        object.__setattr__(
            self,
            "semantic_endpoint_refs",
            _strings(self.semantic_endpoint_refs, "semantic_endpoint_refs"),
        )
        object.__setattr__(
            self,
            "program_endpoint_refs",
            _strings(self.program_endpoint_refs, "program_endpoint_refs"),
        )
        try:
            support = RelationSupport(self.support_kind).value
        except ValueError as exc:
            raise ValueError(
                f"unknown candidate support kind: {self.support_kind}"
            ) from exc
        object.__setattr__(self, "support_kind", support)
        resolutions = {
            str(key): str(value).upper()
            for key, value in dict(self.endpoint_resolution).items()
        }
        object.__setattr__(
            self, "endpoint_resolution", dict(sorted(resolutions.items()))
        )
        refs = tuple(
            {
                "kind": _nonempty(item.get("kind"), "evidence kind"),
                "id": _nonempty(item.get("id"), "evidence id"),
            }
            for item in self.evidence_refs
        )
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(
            self, "program_scope", _nonempty(self.program_scope, "program_scope")
        )
        deps = tuple(copy_json(item) for item in self.maintenance_dependencies)
        object.__setattr__(self, "maintenance_dependencies", deps)
        object.__setattr__(
            self,
            "completeness_refs",
            tuple(sorted({str(item) for item in self.completeness_refs if str(item)})),
        )
        object.__setattr__(
            self, "construction_method", str(self.construction_method or "")
        )
        membership_result = str(self.membership_result or "").strip().upper()
        if membership_result and membership_result not in CLASS_MEMBERSHIP_RESULTS:
            raise ValueError(f"unknown membership result: {self.membership_result}")
        object.__setattr__(self, "membership_result", membership_result)
        if not self.candidate_id:
            object.__setattr__(
                self,
                "candidate_id",
                digest(self._identity_payload(), "semantic-candidate"),
            )
        else:
            object.__setattr__(
                self, "candidate_id", _nonempty(self.candidate_id, "candidate_id")
            )

    def _identity_payload(self) -> dict[str, Any]:
        payload = {
            "obligation_id": self.obligation_id,
            "claim_kind": self.claim_kind,
            "relation_name": self.relation_name,
            "tuple": dict(self.tuple),
            "polarity": self.polarity,
            "semantic_endpoint_refs": list(self.semantic_endpoint_refs),
            "program_endpoint_refs": list(self.program_endpoint_refs),
            "support_kind": self.support_kind,
            "evidence_refs": [dict(item) for item in self.evidence_refs],
            "program_scope": self.program_scope,
            "maintenance_dependencies": list(self.maintenance_dependencies),
            "completeness_refs": list(self.completeness_refs),
        }
        if self.membership_result:
            payload["membership_result"] = self.membership_result
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SemanticCandidate:
        return cls(
            obligation_id=str(payload.get("obligation_id") or ""),
            claim_kind=str(payload.get("claim_kind") or ""),
            relation_name=str(payload.get("relation_name") or ""),
            tuple=dict(payload.get("tuple") or {}),
            polarity=str(payload.get("polarity") or ""),
            semantic_endpoint_refs=tuple(payload.get("semantic_endpoint_refs") or ()),
            program_endpoint_refs=tuple(payload.get("program_endpoint_refs") or ()),
            support_kind=str(payload.get("support_kind") or ""),
            endpoint_resolution=dict(payload.get("endpoint_resolution") or {}),
            evidence_refs=tuple(payload.get("evidence_refs") or ()),
            program_scope=str(payload.get("program_scope") or ""),
            maintenance_dependencies=tuple(
                payload.get("maintenance_dependencies") or ()
            ),
            completeness_refs=tuple(payload.get("completeness_refs") or ()),
            construction_method=str(payload.get("construction_method") or ""),
            membership_result=str(payload.get("membership_result") or ""),
            candidate_id=str(payload.get("candidate_id") or ""),
            contract=str(payload.get("contract") or CANDIDATE_SCHEMA),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "candidate_id": self.candidate_id,
            "obligation_id": self.obligation_id,
            "claim_kind": self.claim_kind,
            "relation_name": self.relation_name,
            "tuple": copy_json(self.tuple),
            "polarity": self.polarity,
            "semantic_endpoint_refs": list(self.semantic_endpoint_refs),
            "program_endpoint_refs": list(self.program_endpoint_refs),
            "support_kind": self.support_kind,
            "endpoint_resolution": copy_json(self.endpoint_resolution),
            "evidence_refs": [copy_json(item) for item in self.evidence_refs],
            "program_scope": self.program_scope,
            "maintenance_dependencies": [
                copy_json(item) for item in self.maintenance_dependencies
            ],
            "completeness_refs": list(self.completeness_refs),
            "construction_method": self.construction_method,
            "membership_result": self.membership_result,
        }


@dataclass(frozen=True)
class PersistenceAdmissionDecision:
    """Deterministic admission outcome; never supplied by a constructor."""

    candidate_id: str
    obligation_id: str
    outcome: str
    reason: str
    admission_profile: str
    evidence_refs: tuple[Mapping[str, str], ...] = ()
    completeness_refs: tuple[str, ...] = ()
    maintenance_dependency_ids: tuple[str, ...] = ()
    snapshot_id: str = ""
    decision_id: str = ""
    contract: str = ADMISSION_DECISION_SCHEMA

    def __post_init__(self) -> None:
        if self.contract != ADMISSION_DECISION_SCHEMA:
            raise ValueError(
                f"unsupported admission decision schema: {self.contract}"
            )
        if self.outcome not in PERSISTENCE_OUTCOMES:
            raise ValueError(f"unknown persistence outcome: {self.outcome}")
        object.__setattr__(
            self, "candidate_id", _nonempty(self.candidate_id, "candidate_id")
        )
        object.__setattr__(
            self, "obligation_id", _nonempty(self.obligation_id, "obligation_id")
        )
        object.__setattr__(self, "reason", _nonempty(self.reason, "reason"))
        object.__setattr__(
            self,
            "admission_profile",
            _nonempty(self.admission_profile, "admission_profile"),
        )
        object.__setattr__(self, "snapshot_id", str(self.snapshot_id or ""))
        object.__setattr__(
            self, "evidence_refs", tuple(copy_json(item) for item in self.evidence_refs)
        )
        object.__setattr__(
            self,
            "completeness_refs",
            tuple(sorted({str(item) for item in self.completeness_refs if str(item)})),
        )
        object.__setattr__(
            self,
            "maintenance_dependency_ids",
            tuple(
                sorted(
                    {str(item) for item in self.maintenance_dependency_ids if str(item)}
                )
            ),
        )
        if not self.decision_id:
            object.__setattr__(
                self,
                "decision_id",
                digest(
                    {
                        "candidate_id": self.candidate_id,
                        "obligation_id": self.obligation_id,
                        "outcome": self.outcome,
                        "reason": self.reason,
                        "admission_profile": self.admission_profile,
                        "evidence_refs": list(self.evidence_refs),
                        "completeness_refs": list(self.completeness_refs),
                        "maintenance_dependency_ids": list(
                            self.maintenance_dependency_ids
                        ),
                        "snapshot_id": self.snapshot_id,
                    },
                    "admission",
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "decision_id": self.decision_id,
            "candidate_id": self.candidate_id,
            "obligation_id": self.obligation_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "admission_profile": self.admission_profile,
            "evidence_refs": [copy_json(item) for item in self.evidence_refs],
            "completeness_refs": list(self.completeness_refs),
            "maintenance_dependency_ids": list(self.maintenance_dependency_ids),
            "snapshot_id": self.snapshot_id,
        }


@dataclass(frozen=True)
class SemanticCommitmentWarrant:
    """A compact, inspectable dependency record for an admitted commitment."""

    assertion_id: str
    obligation_id: str
    snapshot_id: str
    evidence_refs: tuple[Mapping[str, str], ...]
    support_kind: str
    resolution_basis: Mapping[str, str]
    depends_on: tuple[Mapping[str, Any], ...]
    admission_profile: str
    admission_decision_id: str
    contract: str = WARRANT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "assertion_id": self.assertion_id,
            "obligation_id": self.obligation_id,
            "snapshot_id": self.snapshot_id,
            "evidence_refs": [copy_json(item) for item in self.evidence_refs],
            "support_kind": self.support_kind,
            "resolution_basis": copy_json(self.resolution_basis),
            "depends_on": [copy_json(item) for item in self.depends_on],
            "admission_profile": self.admission_profile,
            "admission_decision_id": self.admission_decision_id,
        }


def write_json_artifact(payload: Mapping[str, Any], path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target
