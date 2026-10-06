"""Digest-addressed bytes for authoritative governance evidence.

Program snapshot inputs live under ``program_inputs``. Governance evidence
uses this directory so a policy file and a program file stay different
evidence records even when both are retained as immutable digest blobs.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path

from ontology_author.world.runtime.world import ConstructionWorld

GOVERNANCE_EVIDENCE_DIR = "governance_evidence"

_BYTE_LOCATION = re.compile(r"^bytes:(\d+):(\d+)$")
_HANDLE_DIGEST = re.compile(r"@sha256:([0-9a-fA-F]+)$")


def write_governance_evidence(world_dir: Path, blobs: Mapping[str, bytes]) -> None:
    directory = world_dir / GOVERNANCE_EVIDENCE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for digest, payload in blobs.items():
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"governance evidence blob {digest} does not match its bytes")
        target = directory / digest
        if not target.exists():
            target.write_bytes(payload)


def reconstruct_governance_observation(
    world: ConstructionWorld,
    observation: Mapping[str, str],
) -> tuple[str, str]:
    """Return (text, OK|FAILED) from sealed governance evidence blobs only."""

    handle = str(observation.get("native_handle") or "")
    revision = str(observation.get("source_revision") or "")
    location = str(observation.get("native_location") or "")
    match = _HANDLE_DIGEST.search(handle)
    if match is None:
        return "", "FAILED"
    digest = match.group(1).lower()
    # This evidence store is explicitly content-revisioned.  A retained blob
    # matching the handle must not validate an observation that claims a
    # different source state.
    if revision != f"sha256:{digest}":
        return "", "FAILED"
    located = _BYTE_LOCATION.match(location)
    if located is None:
        return "", "FAILED"
    blob = world.path.parent / GOVERNANCE_EVIDENCE_DIR / digest
    try:
        payload = blob.read_bytes()
    except OSError:
        return "", "FAILED"
    if hashlib.sha256(payload).hexdigest() != digest:
        return "", "FAILED"
    start, end = int(located.group(1)), int(located.group(2))
    if start < 0 or end < start or end > len(payload):
        return "", "FAILED"
    try:
        return payload[start:end].decode("utf-8"), "OK"
    except UnicodeDecodeError:
        return "", "FAILED"
