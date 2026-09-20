"""Generated construction receipt for a sealed World bundle.

This records which construction.py produced the artifact. It is not a
dependency graph, not semantic staleness, and not World-kernel state.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

RECEIPT_SCHEMA = "world_construction_receipt/v0"
RECEIPT_FILENAME = "world.construction-receipt.json"


def constructor_source_digest(path: Path | str) -> str:
    """SHA-256 of the construction entrypoint bytes."""

    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_construction_receipt(
    *,
    entrypoint: Path | str,
    workspace: Path | str,
    runtime_world_id: str,
    contract_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the generated receipt payload for one construction run."""

    entrypoint_path = Path(entrypoint)
    workspace_path = Path(workspace)
    try:
        relative = str(entrypoint_path.resolve().relative_to(workspace_path.resolve()))
    except ValueError:
        relative = entrypoint_path.name
    return {
        "contract": RECEIPT_SCHEMA,
        "entrypoint": relative.replace("\\", "/"),
        "source_digest": constructor_source_digest(entrypoint_path),
        "runtime_world_id": str(runtime_world_id or ""),
        "contract_identity": dict(contract_identity or {}),
    }


def write_construction_receipt(directory: Path | str, payload: Mapping[str, Any]) -> Path:
    path = Path(directory) / RECEIPT_FILENAME
    path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def read_construction_receipt(world_sqlite: Path | str) -> dict[str, Any] | None:
    path = Path(world_sqlite).with_suffix(".construction-receipt.json")
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def constructor_matches_receipt(
    construction_path: Path | str,
    receipt: Mapping[str, Any] | None,
) -> bool:
    """Whether the checked-in constructor is the one named by the receipt."""

    if not receipt:
        return False
    return constructor_source_digest(construction_path) == str(
        receipt.get("source_digest") or ""
    )
