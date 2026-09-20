"""Native program-spine capability identities and construction receipts.

This module defines the application-level envelope around a mechanically
constructed World.  It intentionally does not add storage primitives or a
plugin protocol.  Capability facts remain ordinary World relations; the
receipt summarizes those authoritative records for inspection and admission.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


CORE_SPEC_ID = "spine_core"
CORE_SPEC_VERSION = "v1"
RECEIPT_VERSION = "spine_construction_receipt/v1"

CAPABILITY_STATUS = {
    "COMPLETE",
    "STATIC_COMPLETE",
    "PARTIAL",
    "INCOMPLETE",
    "UNKNOWN",
    "NOT_PRODUCED",
}
LOSS_CATEGORIES = {"COLLAPSES", "DOES_NOT_REPRESENT", "UNKNOWN"}
RESOLUTION_STATUSES = {"RESOLVED", "MULTIPLE_CANDIDATES", "UNRESOLVED"}

CAPABILITY_VERSIONS = {
    "spine.code_structure/v1": "v1",
    "spine.imports/v1": "v1",
    "spine.calls/v1": "v1",
    "spine.type_relations/v1": "v1",
}


class SpineReceiptError(ValueError):
    """A receipt does not satisfy the native spine receipt schema."""


def _copy(value: Any) -> Any:
    """Copy JSON-shaped values without exposing mutable receipt internals."""

    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


@dataclass(frozen=True)
class SpineConstructionReceipt:
    """Inspectable conformance and construction summary for one spine."""

    receipt_version: str
    construction_id: str
    conformance: Mapping[str, Any]
    snapshot: Mapping[str, Any]
    capabilities: tuple[Mapping[str, Any], ...]
    identity_surfaces: tuple[Mapping[str, Any], ...]
    resolution_summary: Mapping[str, Any]
    boundary_summary: Mapping[str, Any]
    losses: tuple[Mapping[str, Any], ...]
    representative_examples: tuple[Mapping[str, Any], ...]
    comparison_readiness: Mapping[str, Any]
    acceptance: Mapping[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SpineConstructionReceipt":
        required = {
            "receipt_version",
            "construction_id",
            "conformance",
            "snapshot",
            "capabilities",
            "identity_surfaces",
            "resolution_summary",
            "boundary_summary",
            "losses",
            "representative_examples",
            "comparison_readiness",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise SpineReceiptError(f"receipt missing {', '.join(missing)}")
        return cls(
            receipt_version=str(payload["receipt_version"]),
            construction_id=str(payload["construction_id"]),
            conformance=_copy(payload["conformance"]),
            snapshot=_copy(payload["snapshot"]),
            capabilities=tuple(_copy(item) for item in payload["capabilities"]),
            identity_surfaces=tuple(_copy(item) for item in payload["identity_surfaces"]),
            resolution_summary=_copy(payload["resolution_summary"]),
            boundary_summary=_copy(payload["boundary_summary"]),
            losses=tuple(_copy(item) for item in payload["losses"]),
            representative_examples=tuple(_copy(item) for item in payload["representative_examples"]),
            comparison_readiness=_copy(payload["comparison_readiness"]),
            acceptance=_copy(payload["acceptance"]) if payload.get("acceptance") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_version": self.receipt_version,
            "construction_id": self.construction_id,
            "conformance": _copy(self.conformance),
            "snapshot": _copy(self.snapshot),
            "capabilities": [_copy(item) for item in self.capabilities],
            "identity_surfaces": [_copy(item) for item in self.identity_surfaces],
            "resolution_summary": _copy(self.resolution_summary),
            "boundary_summary": _copy(self.boundary_summary),
            "losses": [_copy(item) for item in self.losses],
            "representative_examples": [_copy(item) for item in self.representative_examples],
            "comparison_readiness": _copy(self.comparison_readiness),
            "acceptance": _copy(self.acceptance) if self.acceptance is not None else None,
        }

    def validate(self, manifest: Mapping[str, Any] | None = None) -> list[str]:
        """Return receipt errors without changing the World or receipt."""

        errors: list[str] = []
        if self.receipt_version != RECEIPT_VERSION:
            errors.append(f"unsupported receipt version: {self.receipt_version}")
        if not self.construction_id.strip():
            errors.append("receipt construction_id is empty")
        if not isinstance(self.conformance, Mapping):
            errors.append("receipt conformance must be an object")
        else:
            status = self.conformance.get("status")
            if status not in {"PASS", "CONTRACT_FAILURE"}:
                errors.append(f"invalid receipt conformance status: {status}")
            if status == "PASS" and self.conformance.get("diagnostics"):
                errors.append("PASS receipt cannot contain conformance diagnostics")

        snapshot = self.snapshot
        for key in (
            "id",
            "source_state",
            "declared_boundary",
            "effective_inputs",
            "configuration",
            "extractor",
            "core_contract",
            "capability_profiles",
        ):
            if key not in snapshot:
                errors.append(f"receipt snapshot missing {key}")
        if manifest is not None:
            if snapshot.get("id") != manifest.get("snapshot_id"):
                errors.append("receipt snapshot does not match manifest")
            if snapshot.get("declared_boundary") != manifest.get("boundary"):
                errors.append("receipt boundary does not match manifest")
            if snapshot.get("effective_inputs") != manifest.get("effective_inputs"):
                errors.append("receipt effective inputs do not match manifest")

        core = snapshot.get("core_contract")
        if not isinstance(core, Mapping) or core.get("id") != CORE_SPEC_ID or core.get("version") != CORE_SPEC_VERSION:
            errors.append("receipt does not identify spine_core/v1")
        if not isinstance(snapshot.get("effective_inputs"), list) or not snapshot.get("effective_inputs"):
            errors.append("receipt effective inputs are missing or empty")
        if not isinstance(snapshot.get("capability_profiles"), list):
            errors.append("receipt capability_profiles must be a list")

        seen_capabilities: set[str] = set()
        for item in self.capabilities:
            if not isinstance(item, Mapping):
                errors.append("receipt capability entry must be an object")
                continue
            capability = str(item.get("id") or "")
            version = str(item.get("version") or "")
            status = item.get("status")
            if not capability or not version:
                errors.append("receipt capability needs id and version")
            key = f"{capability}/{version}"
            if key in seen_capabilities:
                errors.append(f"duplicate receipt capability: {key}")
            seen_capabilities.add(key)
            if status not in CAPABILITY_STATUS:
                errors.append(f"invalid capability status: {status}")
            if not str(item.get("scope") or "").strip():
                errors.append(f"capability lacks scope: {key}")
            refs = item.get("completeness_receipt_refs", [])
            if not isinstance(refs, list) or any(not str(ref).strip() for ref in refs):
                errors.append(f"invalid completeness references: {key}")
            if status == "NOT_PRODUCED" and refs:
                errors.append(f"NOT_PRODUCED capability has completeness references: {key}")
            if status != "NOT_PRODUCED" and not refs:
                errors.append(f"produced capability lacks completeness references: {key}")
            if status != "NOT_PRODUCED" and not str(item.get("completeness_basis") or "").strip():
                errors.append(f"produced capability lacks completeness basis: {key}")

        surface_kinds: set[str] = set()
        for item in self.identity_surfaces:
            kind = str(item.get("kind") or "") if isinstance(item, Mapping) else ""
            if not kind:
                errors.append("identity surface lacks kind")
            if kind in surface_kinds:
                errors.append(f"duplicate identity surface: {kind}")
            surface_kinds.add(kind)
            count = item.get("emitted_count") if isinstance(item, Mapping) else None
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                errors.append(f"invalid identity surface count: {kind}")

        if not isinstance(self.boundary_summary, Mapping):
            errors.append("boundary_summary must be an object")
        else:
            for key in ("IN_SCOPE", "EXTERNAL_BOUNDARY", "ANALYSIS_SUPPORT"):
                value = self.boundary_summary.get(key)
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    errors.append(f"invalid boundary summary count: {key}")

        if not isinstance(self.resolution_summary, Mapping):
            errors.append("resolution_summary must be an object")
        else:
            for capability, values in self.resolution_summary.items():
                if not isinstance(values, Mapping):
                    errors.append(f"resolution summary must be an object: {capability}")
                    continue
                for status, count in values.items():
                    if status not in RESOLUTION_STATUSES:
                        errors.append(f"invalid resolution status in receipt: {status}")
                    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                        errors.append(f"invalid resolution count: {capability}/{status}")

        for item in self.losses:
            if not isinstance(item, Mapping) or item.get("category") not in LOSS_CATEGORIES:
                errors.append("invalid receipt loss category")
            elif not str(item.get("statement") or "").strip():
                errors.append("receipt loss lacks statement")

        if not isinstance(self.comparison_readiness, Mapping) or not isinstance(self.comparison_readiness.get("observations"), list):
            errors.append("comparison_readiness.observations must be a list")
        if not isinstance(self.representative_examples, tuple):
            errors.append("representative_examples must be a list")
        return sorted(set(errors))

    def write(self, path: Path | str) -> None:
        errors = self.validate()
        if errors:
            raise SpineReceiptError("cannot write invalid receipt: " + "; ".join(errors))
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def load_receipt(path: Path | str) -> SpineConstructionReceipt:
    return SpineConstructionReceipt.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


__all__ = [
    "CAPABILITY_VERSIONS",
    "CAPABILITY_STATUS",
    "CORE_SPEC_ID",
    "CORE_SPEC_VERSION",
    "LOSS_CATEGORIES",
    "RECEIPT_VERSION",
    "SpineConstructionReceipt",
    "SpineReceiptError",
    "load_receipt",
]
