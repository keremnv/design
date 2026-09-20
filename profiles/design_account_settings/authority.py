"""External evidence-authority bindings for the account-settings profile."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvidenceAuthorityBinding:
    source_id: str
    authority: str

    def __post_init__(self) -> None:
        source_id = str(self.source_id).strip()
        authority = str(self.authority).strip().upper()
        if not source_id or not authority:
            raise ValueError("evidence authority bindings need source_id and authority")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "authority", authority)

    def as_payload(self) -> dict[str, str]:
        return {"source_id": self.source_id, "authority": self.authority}


@dataclass(frozen=True)
class EvidenceAuthorityConfiguration:
    authority_id: str
    revision: str
    manifest_path: str
    bindings: tuple[EvidenceAuthorityBinding, ...]
    selection_method: str = "explicit evidence-authority manifest"

    def __post_init__(self) -> None:
        authority_id = str(self.authority_id).strip()
        revision = str(self.revision).strip()
        if not authority_id or not revision:
            raise ValueError("evidence authority identity and revision are required")
        seen: set[str] = set()
        normalized: list[EvidenceAuthorityBinding] = []
        for binding in self.bindings:
            item = (
                binding
                if isinstance(binding, EvidenceAuthorityBinding)
                else EvidenceAuthorityBinding(**binding)
            )
            if item.source_id in seen:
                raise ValueError(f"duplicate evidence authority source {item.source_id!r}")
            seen.add(item.source_id)
            normalized.append(item)
        object.__setattr__(self, "authority_id", authority_id)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "manifest_path", str(self.manifest_path))
        object.__setattr__(self, "bindings", tuple(normalized))

    def identity(self) -> dict[str, str]:
        return {"authority_id": self.authority_id, "revision": self.revision}

    def inspection_payload(self) -> dict[str, object]:
        return {
            "state": "EFFECTIVE",
            "identity": self.identity(),
            "manifest_path": self.manifest_path,
            "selection_method": self.selection_method,
            "bindings": [item.as_payload() for item in self.bindings],
        }

    def assess_warrant(self, warrant: Mapping[str, Any]) -> dict[str, object]:
        """Grant standing only to explicitly bound Warrant source bases."""

        by_source = {item.source_id: item for item in self.bindings}
        authorities: set[str] = set()
        basis: list[dict[str, object]] = []
        raw_bases = warrant.get("bases", ())
        if not isinstance(raw_bases, (list, tuple)):
            raw_bases = ()
        for base in raw_bases:
            if not isinstance(base, Mapping) or str(base.get("kind")) != "SOURCE":
                continue
            detail = base.get("detail")
            if not isinstance(detail, Mapping):
                continue
            provider = str(detail.get("provider") or "").strip()
            native_handle = str(detail.get("native_handle") or "").strip()
            if not provider or not native_handle:
                continue
            source_id = f"{provider}://{native_handle}"
            binding = by_source.get(source_id)
            if binding is None:
                continue
            authorities.add(binding.authority)
            basis.append(
                {
                    "source_id": source_id,
                    "source_revision": str(detail.get("source_revision") or ""),
                    "source_location": str(detail.get("native_location") or ""),
                    "authority": binding.authority,
                    "authority_id": self.authority_id,
                    "authority_revision": self.revision,
                    "authority_manifest": self.manifest_path,
                }
            )
        basis.sort(
            key=lambda item: (
                str(item.get("source_id")),
                str(item.get("source_revision")),
                str(item.get("source_location")),
            )
        )
        return {
            "authority_kinds": tuple(sorted(authorities)),
            "authority_basis": tuple(basis),
        }


def load_evidence_authority(
    directory: Path | str,
) -> EvidenceAuthorityConfiguration:
    """Load exactly the selected account-settings authority manifest."""

    root = Path(directory)
    path = root / "evidence-authorities.json"
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"invalid evidence-authorities.json: {error}") from error
    if not isinstance(payload, Mapping):
        raise ValueError("evidence-authorities.json must contain an object")
    raw_bindings = payload.get("bindings", ())
    if not isinstance(raw_bindings, list):
        raise ValueError("evidence-authorities.json bindings must be a list")
    bindings = tuple(
        EvidenceAuthorityBinding(
            source_id=str(raw.get("source_id") or ""),
            authority=str(raw.get("authority") or ""),
        )
        for raw in raw_bindings
        if isinstance(raw, Mapping)
    )
    if len(bindings) != len(raw_bindings):
        raise ValueError("each evidence authority binding must be an object")
    return EvidenceAuthorityConfiguration(
        authority_id=str(payload.get("authority_id") or ""),
        revision=str(payload.get("revision") or ""),
        manifest_path=path.name,
        bindings=bindings,
    )


__all__ = [
    "EvidenceAuthorityBinding",
    "EvidenceAuthorityConfiguration",
    "load_evidence_authority",
]
