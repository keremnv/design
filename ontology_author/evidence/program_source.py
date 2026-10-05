"""Reconstruct bounded program source from sealed World input blobs.

The path is grounding → SourceObservation → digest-addressed snapshot bytes.
This module does not open workspace paths or search the repository.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from ontology_author.world.runtime.world import ConstructionWorld

# On-disk layout for digest-addressed program input blobs. The spine
# builder writes this layout; this module reads it. The name lives here
# because evidence owns how program sources are addressed on disk.
PROGRAM_INPUTS_DIR = "program_inputs"


_BYTE_LOCATION = re.compile(r"^bytes:(\d+):(\d+)$")
_HANDLE_DIGEST = re.compile(r"@sha256:([0-9a-fA-F]+)$")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:32]


def program_source_observations(world: ConstructionWorld, entity_id: str) -> list[dict[str, str]]:
    rows = world.query(
        "SELECT reference, detail FROM _world_groundings "
        "WHERE subject_type='REFERENT' AND subject_id=? AND kind='SOURCE' "
        "ORDER BY reference, detail",
        (entity_id,),
    )
    observations: list[dict[str, str]] = []
    for row in rows:
        try:
            detail = json.loads(row.get("detail") or "{}")
        except json.JSONDecodeError:
            continue
        if not isinstance(detail, Mapping):
            continue
        observations.append(
            {
                "provider": str(detail.get("provider") or ""),
                "native_handle": str(detail.get("native_handle") or ""),
                "source_revision": str(detail.get("source_revision") or ""),
                "native_location": str(detail.get("native_location") or ""),
            }
        )
    return observations


def _digest_from_handle(handle: str) -> str:
    match = _HANDLE_DIGEST.search(handle)
    return match.group(1) if match else ""


def _path_from_handle(handle: str) -> str:
    return handle.split("@sha256:", 1)[0]


def reconstruct_program_observation(world: ConstructionWorld, observation: Mapping[str, str]) -> tuple[str, str]:
    """Return (text, OK|FAILED) from sealed ``program_inputs`` blobs only."""

    handle = str(observation.get("native_handle") or "")
    location = str(observation.get("native_location") or "")
    digest_hex = _digest_from_handle(handle)
    if not digest_hex:
        return "", "FAILED"
    match = _BYTE_LOCATION.match(location)
    if match is None:
        return "", "FAILED"
    blob = world.path.parent / PROGRAM_INPUTS_DIR / digest_hex
    try:
        payload = blob.read_bytes()
    except OSError:
        return "", "FAILED"
    if hashlib.sha256(payload).hexdigest() != digest_hex:
        return "", "FAILED"
    start, end = int(match.group(1)), int(match.group(2))
    if start < 0 or end < start or end > len(payload):
        return "", "FAILED"
    try:
        return payload[start:end].decode("utf-8"), "OK"
    except UnicodeDecodeError:
        return "", "FAILED"


def source_evidence_record(
    *,
    world: ConstructionWorld,
    entity: str,
    side: str,
    snapshot_id: str,
    inclusion_reason: str,
    selected_by: str,
    observation: Mapping[str, str],
) -> dict[str, Any]:
    text, status = reconstruct_program_observation(world, observation)
    handle = str(observation.get("native_handle") or "")
    key = {
        "side": side,
        "snapshot": snapshot_id,
        "program_entity": entity,
        "provider": observation.get("provider") or "",
        "handle": handle,
        "source_revision": observation.get("source_revision") or "",
        "native_location": observation.get("native_location") or "",
        "inclusion_reason": inclusion_reason,
    }
    return {
        "evidence_id": "psrc:" + _digest(key),
        "program_entity": entity,
        "side": side,
        "snapshot": snapshot_id,
        "provider": str(observation.get("provider") or ""),
        # ``native_handle`` is the canonical SourceObservation field used by
        # semantic persistence.  Keep the historical ``handle`` alias for
        # existing application/read surfaces while consumers migrate.
        "native_handle": handle,
        "handle": handle,
        "path": _path_from_handle(handle),
        "source_revision": str(observation.get("source_revision") or ""),
        "native_location": str(observation.get("native_location") or ""),
        "reconstructed_text": text,
        "reconstruction": status,
        "inclusion_reason": inclusion_reason,
        "selected_by": [selected_by],
    }
