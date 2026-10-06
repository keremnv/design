"""Phase 1 provenance conformance for observation revision qualification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ontology_author.evidence.program_source import (
    PROGRAM_INPUTS_DIR,
    reconstruct_program_observation,
)
from ontology_author.software_governance.evidence import reconstruct_governance_observation
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_software_governance_construction import (
    _authority_observation,
    _sample_world,
)


def _mapping(observation: SourceObservation) -> dict[str, str]:
    return {
        "provider": observation.provider,
        "native_handle": observation.native_handle,
        "source_revision": observation.source_revision,
        "native_location": observation.native_location,
    }


def test_governance_reconstruction_rejects_contradictory_source_revision(
    tmp_path: Path,
) -> None:
    world = _sample_world(tmp_path)
    try:
        observation = _authority_observation(
            world,
            "policy.md",
            "A stated requirement.",
        )
        good = _mapping(observation)
        text, status = reconstruct_governance_observation(world, good)
        assert status == "OK"
        assert text == "A stated requirement."

        forged = {**good, "source_revision": "sha256:" + "f" * 64}
        assert reconstruct_governance_observation(world, forged) == ("", "FAILED")
    finally:
        world.close()


def test_program_reconstruction_rejects_revision_outside_snapshot_contract(
    tmp_path: Path,
) -> None:
    payload = b"export const retained = true;\n"
    digest = hashlib.sha256(payload).hexdigest()
    source_state = "snapshot-source-state:test"
    observation = SourceObservation(
        provider="typescript",
        native_handle=f"src/example.ts@sha256:{digest}",
        source_revision=source_state,
        native_location=f"bytes:0:{len(payload)}",
    )

    world = ConstructionWorld.create(tmp_path / "world.sqlite", world_id="program-revision-test")
    try:
        world.add_referent("snapshot:test", label="snapshot:test")
        world.declare_relation(
            "program_snapshot",
            [
                Role("snapshot", RoleType.REFERENT),
                Role("source_state", RoleType.TEXT),
            ],
            description="Minimal snapshot revision contract for evidence reconstruction.",
        )
        world.assert_tuple(
            "program_snapshot",
            {"snapshot": "snapshot:test", "source_state": source_state},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding(
                (observation,),
                construction_method="phase1 revision qualification fixture",
            ),
        )
        directory = world.path.parent / PROGRAM_INPUTS_DIR
        directory.mkdir(parents=True, exist_ok=True)
        (directory / digest).write_bytes(payload)

        good = _mapping(observation)
        text, status = reconstruct_program_observation(world, good)
        assert status == "OK"
        assert text == payload.decode("utf-8")

        forged = {**good, "source_revision": "snapshot-source-state:other"}
        assert reconstruct_program_observation(world, forged) == ("", "FAILED")
    finally:
        world.close()

def test_program_reconstruction_rejects_snapshotless_revision_claim(
    tmp_path: Path,
) -> None:
    payload = b"export const retained = true;\n"
    digest = hashlib.sha256(payload).hexdigest()
    observation = SourceObservation(
        provider="typescript",
        native_handle=f"src/example.ts@sha256:{digest}",
        source_revision="arbitrary-garbage",
        native_location=f"bytes:0:{len(payload)}",
    )
    world = ConstructionWorld.create(
        tmp_path / "snapshotless.sqlite",
        world_id="snapshotless-program-revision-test",
    )
    try:
        directory = world.path.parent / PROGRAM_INPUTS_DIR
        directory.mkdir(parents=True, exist_ok=True)
        (directory / digest).write_bytes(payload)

        assert reconstruct_program_observation(world, _mapping(observation)) == (
            "",
            "FAILED",
        )
    finally:
        world.close()

