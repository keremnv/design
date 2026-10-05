"""Retained evidence for authority publications.

Authority construction uses the Markdown source driver for exact byte-region
observations.  Accepted publications must not depend on the original workspace
files remaining present, so the exact Markdown bytes are retained by content
revision beside the World and can be reopened with the original logical
handles.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

from ontology_author.evidence import EvidenceError
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld

AUTHORITY_EVIDENCE_DIR = "authority_evidence"
_REVISION_PREFIX = "sha256:"


def _digest_from_revision(revision: str) -> str:
    value = str(revision or "")
    if not value.startswith(_REVISION_PREFIX):
        raise EvidenceError(f"authority source revision is not content-addressed: {revision!r}")
    digest = value[len(_REVISION_PREFIX):]
    if len(digest) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in digest):
        raise EvidenceError(f"authority source revision has invalid sha256 digest: {revision!r}")
    return digest.lower()


def retain_authority_sources(
    world_dir: Path | str,
    sources: Mapping[str, MarkdownSource],
) -> None:
    """Retain every declared Markdown source under its exact content digest."""

    directory = Path(world_dir) / AUTHORITY_EVIDENCE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for handle, source in sorted(sources.items()):
        if str(handle) != source.handle:
            raise EvidenceError(
                f"authority source mapping handle {handle!r} differs from source handle {source.handle!r}"
            )
        digest = _digest_from_revision(source.revision)
        if hashlib.sha256(source.data).hexdigest() != digest:
            raise EvidenceError(f"authority source {handle!r} bytes do not match {source.revision}")
        target = directory / digest
        if target.exists():
            if target.read_bytes() != source.data:
                raise EvidenceError(f"retained authority blob collision for {source.revision}")
            continue
        target.write_bytes(source.data)


def reconstruct_authority_observation(
    world: ConstructionWorld,
    observation: SourceObservation | Mapping[str, str],
) -> tuple[str, str]:
    """Return ``(text, OK|FAILED)`` using only retained publication bytes."""

    if isinstance(observation, SourceObservation):
        value = observation
    else:
        try:
            value = SourceObservation(
                provider=str(observation.get("provider") or ""),
                native_handle=str(observation.get("native_handle") or ""),
                source_revision=str(observation.get("source_revision") or ""),
                native_location=str(observation.get("native_location") or ""),
            )
        except Exception:
            return "", "FAILED"
    if value.provider != "markdown" or not value.native_handle or not value.native_location:
        return "", "FAILED"
    try:
        digest = _digest_from_revision(value.source_revision)
        payload = (world.path.parent / AUTHORITY_EVIDENCE_DIR / digest).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            return "", "FAILED"
        source = MarkdownSource(
            world.path.parent / AUTHORITY_EVIDENCE_DIR / digest,
            handle=value.native_handle,
            data=payload,
        )
        return source.reconstruct(value), "OK"
    except (OSError, EvidenceError):
        return "", "FAILED"


def retained_authority_sources(
    world: ConstructionWorld | Path | str,
) -> dict[str, MarkdownSource]:
    """Reopen all authority sources from one retained publication only."""

    opened = world if isinstance(world, ConstructionWorld) else ConstructionWorld.open(world, read_only=True)
    close = not isinstance(world, ConstructionWorld)
    try:
        result: dict[str, MarkdownSource] = {}
        directory = opened.path.parent / AUTHORITY_EVIDENCE_DIR
        for row in opened.relation_rows("authority_source"):
            handle = str(row["source_handle"])
            revision = str(row["content_revision"])
            digest = _digest_from_revision(revision)
            payload = (directory / digest).read_bytes()
            if hashlib.sha256(payload).hexdigest() != digest:
                raise EvidenceError(f"retained authority source {handle!r} failed digest verification")
            source = MarkdownSource(directory / digest, handle=handle, data=payload)
            if source.revision != revision:
                raise EvidenceError(f"retained authority source {handle!r} revision mismatch")
            result[handle] = source
        return result
    finally:
        if close:
            opened.close()
