"""Deterministic reproduction of a recorded material evidence observation.

This compares a constructor-declared region to the current source. It does not
search a file, interpret English, or grant authority.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ontology_author.world.runtime.source_helpers import Source

SUPPORT_PRESERVED = "PRESERVED"
SUPPORT_CHANGED = "CHANGED"
SUPPORT_MISSING = "MISSING"
SUPPORT_UNKNOWN = "UNKNOWN"

_LINE_RANGE = re.compile(r"^lines:(?P<start>\d+)(?:-(?P<end>\d+))?$")


def content_digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_line_range(location: str) -> tuple[int, int] | None:
    match = _LINE_RANGE.match(str(location or "").strip())
    if match is None:
        return None
    start = int(match.group("start"))
    end = int(match.group("end") or start)
    if start < 1 or end < start:
        return None
    return start, end


def extract_line_range(text: str, start: int, end: int) -> str | None:
    lines = str(text or "").splitlines()
    if end > len(lines):
        return None
    return "\n".join(lines[start - 1 : end])


def recorded_material_support(warrant: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Read the constructor-declared material-support record from a Warrant."""

    if not isinstance(warrant, Mapping):
        return None
    for base in warrant.get("bases") or ():
        if not isinstance(base, Mapping) or str(base.get("kind")) != "WORLD":
            continue
        detail = base.get("detail")
        if not isinstance(detail, Mapping):
            continue
        extra = detail.get("extra")
        if not isinstance(extra, Mapping):
            continue
        recorded = extra.get("material_support")
        if isinstance(recorded, Mapping) and recorded.get("content_digest"):
            return {
                "native_handle": str(recorded.get("native_handle") or ""),
                "native_location": str(recorded.get("native_location") or ""),
                "content_digest": str(recorded.get("content_digest") or ""),
                "source_revision": str(recorded.get("source_revision") or ""),
                "kind": str(recorded.get("kind") or "LINE_RANGE"),
            }
    return None


def reproduce_material_support(
    recorded: Mapping[str, Any],
    source: Source,
) -> dict[str, Any]:
    """Compare one recorded region to the current source. No file search."""

    handle = str(recorded.get("native_handle") or "").strip()
    location = str(recorded.get("native_location") or "").strip()
    expected = str(recorded.get("content_digest") or "").strip()
    payload = {
        "native_handle": handle,
        "native_location": location,
        "recorded_digest": expected,
        "recorded_source_revision": str(recorded.get("source_revision") or ""),
    }
    if not handle or not expected:
        return {
            **payload,
            "status": SUPPORT_UNKNOWN,
            "reason": "recorded material support is incomplete",
        }
    path = source.root / handle
    if not path.exists():
        return {
            **payload,
            "status": SUPPORT_MISSING,
            "reason": f"source {handle!r} is not present",
        }
    current_revision = source.file_hash(handle)
    payload["current_source_revision"] = current_revision
    rng = parse_line_range(location)
    if rng is None:
        return {
            **payload,
            "status": SUPPORT_UNKNOWN,
            "reason": "native_location is not a reconstructible line range",
        }
    region = extract_line_range(source.read_text(handle), rng[0], rng[1])
    if region is None:
        return {
            **payload,
            "status": SUPPORT_MISSING,
            "reason": f"line range {location} is not present in {handle}",
        }
    digest = content_digest(region)
    payload["current_digest"] = digest
    if digest == expected:
        return {
            **payload,
            "status": SUPPORT_PRESERVED,
            "reason": "recorded material region reproduces identically",
        }
    return {
        **payload,
        "status": SUPPORT_CHANGED,
        "reason": "recorded material region content is not identical",
    }


def material_support_for_warrant(
    warrant: Mapping[str, Any] | None,
    source: Source | None,
) -> dict[str, Any] | None:
    recorded = recorded_material_support(warrant)
    if recorded is None:
        return None
    if source is None:
        return {
            **recorded,
            "status": SUPPORT_UNKNOWN,
            "reason": "current source is not available for reproduction",
        }
    return reproduce_material_support(recorded, source)


def workspace_source_root(world_sqlite: Path | str) -> Path:
    """Ordinary project tree for a sealed ``world/world.sqlite`` bundle."""

    return Path(world_sqlite).resolve().parent.parent
