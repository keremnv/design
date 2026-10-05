"""Phase 1 provenance conformance for retained authority evidence."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ontology_author.authority import construct_authority_world, observations_for_assertion
from ontology_author.authority.evidence import (
    reconstruct_authority_observation,
    retained_authority_sources,
)
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import (
    MD,
    PROFILE,
    PURPOSE,
    TS_A,
    TYPESCRIPT_MODULE,
    _build_authority,
    _spine,
    _universe,
    _write,
)

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not TYPESCRIPT_MODULE.exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def test_authority_publication_reconstructs_after_external_markdown_is_removed(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(workspace, MD)
    spine = _spine(workspace, TS_A, "program-world")
    authority_world = tmp_path / "authority-world"

    result = construct_authority_world(
        spine.world_dir,
        authority_world,
        _universe(workspace),
        _build_authority,
        construction_id="phase1-authority-retention",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert result.succeeded, result.errors

    world = ConstructionWorld.open(authority_world, read_only=True)
    try:
        assertion_rows = world.query(
            "SELECT assertion_id FROM _world_assertions "
            "WHERE relation_name='enters_flow' ORDER BY assertion_id"
        )
        assert len(assertion_rows) == 1
        observations = observations_for_assertion(
            world,
            str(assertion_rows[0]["assertion_id"]),
        )
        assert observations
    finally:
        world.close()

    for name in MD:
        (workspace / name).unlink()

    retained = retained_authority_sources(authority_world)
    assert set(retained) == set(MD)
    first = observations[0]
    assert retained[first.native_handle].reconstruct(first)

    world = ConstructionWorld.open(authority_world, read_only=True)
    try:
        text, status = reconstruct_authority_observation(world, first)
    finally:
        world.close()
    assert status == "OK"
    assert "Cancel subscription" in text
