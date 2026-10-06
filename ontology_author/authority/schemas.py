"""Application-level authority-construction record schemas.

These types are not kernel primitives and not executable contracts.
Domain predicates remain open; this module only names standing, support,
resolution, claim kinds, and the inspectable construction receipt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


MECHANISM_ID = "authority_construction"
MECHANISM_VERSION = "v0"
MECHANISM_KEY = f"{MECHANISM_ID}/{MECHANISM_VERSION}"
RECEIPT_VERSION = "authority_construction_receipt/v1"
CONSTRUCTOR_ID = "ontology_author.authority.construction"
CONSTRUCTOR_VERSION = "v1"
DEFAULT_PROFILE = "authority-construction-v0"


class SourceStanding(StrEnum):
    AUTHORITATIVE = "AUTHORITATIVE"
    AVAILABLE = "AVAILABLE"
    ANALYSIS_SUPPORT = "ANALYSIS_SUPPORT"


class RelationSupport(StrEnum):
    SOURCE_NATIVE = "SOURCE_NATIVE"
    SOURCE_EXPLICIT = "SOURCE_EXPLICIT"
    SOURCE_STRUCTURAL = "SOURCE_STRUCTURAL"
    CROSS_EVIDENCE_INFERRED = "CROSS_EVIDENCE_INFERRED"
    HYPOTHESIZED = "HYPOTHESIZED"


class ReferentResolution(StrEnum):
    NATIVE_ID = "NATIVE_ID"
    DETERMINISTIC = "DETERMINISTIC"
    SOURCE_DEFINED = "SOURCE_DEFINED"
    AGENT_RESOLVED = "AGENT_RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


class ClaimKind(StrEnum):
    SOURCE_PROPOSITION = "SOURCE_PROPOSITION"
    SOURCE_SEMANTIC = "SOURCE_SEMANTIC"
    SOURCE_PROGRAM = "SOURCE_PROGRAM"
    SEMANTIC_PROGRAM = "SEMANTIC_PROGRAM"
    UNRESOLVED_RECORD = "UNRESOLVED_RECORD"


class UnresolvedKind(StrEnum):
    UNBOUND_REGION = "UNBOUND_REGION"
    IDENTITY_NOT_WARRANTED = "IDENTITY_NOT_WARRANTED"
    ENDPOINT_UNRESOLVED = "ENDPOINT_UNRESOLVED"
    AMBIGUOUS_REFERENT = "AMBIGUOUS_REFERENT"
    SPINE_SURFACE_MISSING = "SPINE_SURFACE_MISSING"
    STANDING_INSUFFICIENT = "STANDING_INSUFFICIENT"


class CompletenessScope(StrEnum):
    ADDRESSABILITY = "ADDRESSABILITY"
    CONSTRUCTION = "CONSTRUCTION"
    ATTACHMENT = "ATTACHMENT"


class AdequacyOutcome(StrEnum):
    SATISFIED = "SATISFIED"
    UNRESOLVED = "UNRESOLVED"
    INADEQUATE = "INADEQUATE"
    FAILED = "FAILED"


class AuthorityReceiptError(ValueError):
    """A receipt does not satisfy the authority-construction receipt contract."""


class AuthorityConstructionError(ValueError):
    """Authority construction or admission failed."""


def _copy(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


@dataclass(frozen=True)
class AuthorityConstructionReceipt:
    """Inspectable summary of one authority construction. Not a second truth system."""

    receipt_version: str
    construction_id: str
    contract: str
    purpose: str
    profile: str
    constructor: Mapping[str, Any]
    authorized_source_universe: Mapping[str, Any]
    source_revisions: Mapping[str, str]
    source_standing_summary: Mapping[str, int]
    program_snapshot_id: str
    program_universe: str
    source_regions_examined: Mapping[str, Any]
    exploration_provenance: tuple[Mapping[str, Any], ...]
    source_native_relationships_used: tuple[Mapping[str, Any], ...]
    semantic_referents_created: tuple[str, ...]
    semantic_referents_reused: tuple[str, ...]
    claims_persisted: Mapping[str, int]
    direct_source_program_links: int
    semantic_program_links: int
    source_semantic_links: int
    relation_support_summary: Mapping[str, int]
    resolution_summary: Mapping[str, int]
    unresolved_records: tuple[Mapping[str, Any], ...]
    known_unbound_material: tuple[str, ...]
    known_losses: tuple[str, ...]
    reusable_resolvers: tuple[str, ...]
    representative_examples: tuple[Mapping[str, Any], ...]
    completeness_references: tuple[Mapping[str, Any], ...]
    adequacy_probe_results: tuple[Mapping[str, Any], ...]
    acceptance: Mapping[str, Any] | None = None
    construction_basis: Mapping[str, Any] | None = None
    construction_contract: Mapping[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AuthorityConstructionReceipt":
        required = {
            "receipt_version",
            "construction_id",
            "contract",
            "purpose",
            "profile",
            "constructor",
            "authorized_source_universe",
            "source_revisions",
            "source_standing_summary",
            "program_snapshot_id",
            "program_universe",
            "source_regions_examined",
            "exploration_provenance",
            "source_native_relationships_used",
            "semantic_referents_created",
            "semantic_referents_reused",
            "claims_persisted",
            "direct_source_program_links",
            "semantic_program_links",
            "source_semantic_links",
            "relation_support_summary",
            "resolution_summary",
            "unresolved_records",
            "known_unbound_material",
            "known_losses",
            "reusable_resolvers",
            "representative_examples",
            "completeness_references",
            "adequacy_probe_results",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise AuthorityReceiptError(f"receipt missing {', '.join(missing)}")
        return cls(
            receipt_version=str(payload["receipt_version"]),
            construction_id=str(payload["construction_id"]),
            contract=str(payload["contract"]),
            purpose=str(payload["purpose"]),
            profile=str(payload["profile"]),
            constructor=_copy(payload["constructor"]),
            authorized_source_universe=_copy(payload["authorized_source_universe"]),
            source_revisions={str(key): str(value) for key, value in dict(payload["source_revisions"]).items()},
            source_standing_summary={str(key): int(value) for key, value in dict(payload["source_standing_summary"]).items()},
            program_snapshot_id=str(payload["program_snapshot_id"]),
            program_universe=str(payload["program_universe"]),
            source_regions_examined=_copy(payload["source_regions_examined"]),
            exploration_provenance=tuple(_copy(item) for item in payload["exploration_provenance"]),
            source_native_relationships_used=tuple(_copy(item) for item in payload["source_native_relationships_used"]),
            semantic_referents_created=tuple(str(item) for item in payload["semantic_referents_created"]),
            semantic_referents_reused=tuple(str(item) for item in payload["semantic_referents_reused"]),
            claims_persisted={str(key): int(value) for key, value in dict(payload["claims_persisted"]).items()},
            direct_source_program_links=int(payload["direct_source_program_links"]),
            semantic_program_links=int(payload["semantic_program_links"]),
            source_semantic_links=int(payload["source_semantic_links"]),
            relation_support_summary={str(key): int(value) for key, value in dict(payload["relation_support_summary"]).items()},
            resolution_summary={str(key): int(value) for key, value in dict(payload["resolution_summary"]).items()},
            unresolved_records=tuple(_copy(item) for item in payload["unresolved_records"]),
            known_unbound_material=tuple(str(item) for item in payload["known_unbound_material"]),
            known_losses=tuple(str(item) for item in payload["known_losses"]),
            reusable_resolvers=tuple(str(item) for item in payload["reusable_resolvers"]),
            representative_examples=tuple(_copy(item) for item in payload["representative_examples"]),
            completeness_references=tuple(_copy(item) for item in payload["completeness_references"]),
            adequacy_probe_results=tuple(_copy(item) for item in payload["adequacy_probe_results"]),
            acceptance=_copy(payload["acceptance"]) if payload.get("acceptance") is not None else None,
            construction_basis=_copy(payload["construction_basis"]) if payload.get("construction_basis") is not None else None,
            construction_contract=_copy(payload["construction_contract"]) if payload.get("construction_contract") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_version": self.receipt_version,
            "construction_id": self.construction_id,
            "contract": self.contract,
            "purpose": self.purpose,
            "profile": self.profile,
            "constructor": _copy(self.constructor),
            "authorized_source_universe": _copy(self.authorized_source_universe),
            "source_revisions": _copy(self.source_revisions),
            "source_standing_summary": _copy(self.source_standing_summary),
            "program_snapshot_id": self.program_snapshot_id,
            "program_universe": self.program_universe,
            "source_regions_examined": _copy(self.source_regions_examined),
            "exploration_provenance": [_copy(item) for item in self.exploration_provenance],
            "source_native_relationships_used": [_copy(item) for item in self.source_native_relationships_used],
            "semantic_referents_created": list(self.semantic_referents_created),
            "semantic_referents_reused": list(self.semantic_referents_reused),
            "claims_persisted": _copy(self.claims_persisted),
            "direct_source_program_links": self.direct_source_program_links,
            "semantic_program_links": self.semantic_program_links,
            "source_semantic_links": self.source_semantic_links,
            "relation_support_summary": _copy(self.relation_support_summary),
            "resolution_summary": _copy(self.resolution_summary),
            "unresolved_records": [_copy(item) for item in self.unresolved_records],
            "known_unbound_material": list(self.known_unbound_material),
            "known_losses": list(self.known_losses),
            "reusable_resolvers": list(self.reusable_resolvers),
            "representative_examples": [_copy(item) for item in self.representative_examples],
            "completeness_references": [_copy(item) for item in self.completeness_references],
            "adequacy_probe_results": [_copy(item) for item in self.adequacy_probe_results],
            "acceptance": _copy(self.acceptance) if self.acceptance is not None else None,
            "construction_basis": _copy(self.construction_basis) if self.construction_basis is not None else None,
            "construction_contract": _copy(self.construction_contract) if self.construction_contract is not None else None,
        }

    def write(self, path: Path | str) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def load_receipt(path: Path | str) -> AuthorityConstructionReceipt:
    return AuthorityConstructionReceipt.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
