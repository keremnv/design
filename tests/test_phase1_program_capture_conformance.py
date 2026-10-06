"""Phase 1 publication-boundary conformance for program input retention.

Phase 2 moved the acceptance boundary from legacy replacement to fresh
publication; the fail-closed guarantees below are unchanged.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ontology_author.evidence.program_source import PROGRAM_INPUTS_DIR
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.commit import publish_candidate
from ontology_author.world.runtime.publication import PublicationRef
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld


def _candidate(
    root: Path,
    *,
    payload: bytes,
    retain_blob: bool,
) -> Path:
    root.mkdir(parents=True)
    digest = hashlib.sha256(payload).hexdigest()
    source_state = "snapshot-source-state:test"
    observation = SourceObservation(
        provider="typescript",
        native_handle=f"src/test.ts@sha256:{digest}",
        source_revision=source_state,
        native_location=f"bytes:0:{len(payload)}",
    )
    world = ConstructionWorld.create(root / "world.sqlite", world_id="phase1-program-capture")
    try:
        world.add_referent(
            "program:test",
            label="program:test",
            observations=(observation,),
        )
        world.add_referent("snapshot:test", label="snapshot:test")
        world.declare_relation(
            "program_snapshot",
            [Role("snapshot", RoleType.REFERENT), Role("source_state", RoleType.TEXT)],
            description="Snapshot revision contract qualifying the recorded observation.",
        )
        world.assert_tuple(
            "program_snapshot",
            {"snapshot": "snapshot:test", "source_state": source_state},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding(
                (observation,), construction_method="phase1 capture fixture"
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
    published = _candidate(
        tmp_path / "candidate-w1",
        payload=b"export const retained = true;\n",
        retain_blob=True,
    )
    first = tmp_path / "published-w1"
    publish_candidate(published, first)
    before = (first / "world.sqlite").read_bytes()

    candidate = _candidate(
        tmp_path / "candidate",
        payload=b"export const captured = true;\n",
        retain_blob=False,
    )
    output = tmp_path / "published-w2"

    with pytest.raises(ConstructionError, match="retained program evidence verification failed"):
        publish_candidate(candidate, output)

    assert (first / "world.sqlite").read_bytes() == before
    assert candidate.exists()
    assert not output.exists()
    assert list(tmp_path.glob(".published-w2.staging-*")) == []


def test_publication_accepts_reconstructible_program_input(tmp_path: Path) -> None:
    payload = b"export const captured = true;\n"
    candidate = _candidate(
        tmp_path / "candidate-ok",
        payload=payload,
        retain_blob=True,
    )
    output = tmp_path / "published-ok"

    ref = publish_candidate(candidate, output)

    assert (output / "world.sqlite").exists()
    assert (output / PROGRAM_INPUTS_DIR / hashlib.sha256(payload).hexdigest()).read_bytes() == payload
    assert not candidate.exists()
    opened = ConstructionWorld.open(output / "world.sqlite", read_only=True)
    try:
        assert ref == PublicationRef.from_world(opened)
    finally:
        opened.close()
