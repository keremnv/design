"""Phase 1 publication-boundary conformance for program input retention."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ontology_author.evidence.program_source import PROGRAM_INPUTS_DIR
from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.commit import _replace_candidate
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld


def _candidate(
    root: Path,
    *,
    payload: bytes,
    retain_blob: bool,
) -> Path:
    root.mkdir(parents=True)
    digest = hashlib.sha256(payload).hexdigest()
    world = ConstructionWorld.create(root / "world.sqlite", world_id="phase1-program-capture")
    try:
        world.add_referent(
            "program:test",
            label="program:test",
            observations=(
                SourceObservation(
                    provider="typescript",
                    native_handle=f"src/test.ts@sha256:{digest}",
                    source_revision="snapshot-source-state:test",
                    native_location=f"bytes:0:{len(payload)}",
                ),
            ),
        )
    finally:
        world.close()
    if retain_blob:
        directory = root / PROGRAM_INPUTS_DIR
        directory.mkdir(parents=True)
        (directory / digest).write_bytes(payload)
    return root


def test_publication_rejects_missing_program_input_and_preserves_old_world(
    tmp_path: Path,
) -> None:
    output = tmp_path / "published"
    output.mkdir()
    marker = output / "old-publication.txt"
    marker.write_text("retained", encoding="utf-8")

    candidate = _candidate(
        tmp_path / "candidate",
        payload=b"export const captured = true;\n",
        retain_blob=False,
    )

    with pytest.raises(ConstructionError, match="retained program evidence verification failed"):
        _replace_candidate(candidate, output)

    assert marker.read_text(encoding="utf-8") == "retained"
    assert candidate.exists()
    assert not (tmp_path / "published.staging").exists()


def test_publication_accepts_reconstructible_program_input(tmp_path: Path) -> None:
    payload = b"export const captured = true;\n"
    candidate = _candidate(
        tmp_path / "candidate-ok",
        payload=payload,
        retain_blob=True,
    )
    output = tmp_path / "published-ok"

    _replace_candidate(candidate, output)

    assert (output / "world.sqlite").exists()
    assert (output / PROGRAM_INPUTS_DIR / hashlib.sha256(payload).hexdigest()).read_bytes() == payload
    assert not candidate.exists()
