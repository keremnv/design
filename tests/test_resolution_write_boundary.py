from __future__ import annotations

from pathlib import Path

import pytest

from ontology_author.world import Contract, resolve_world
from ontology_author.world.core.kernel import SemanticWorld
from ontology_author.world.core.model import Role, RoleType, ResolutionStatus
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding
from ontology_author.world.runtime.world import ConstructionWorld


RESOLUTION_CONTRACT = Contract(
    "resolution-boundary-test",
    "1",
    semantic_origins=frozenset({ConstructionOrigin.SEMANTIC.value}),
)


def test_world_layers_do_not_expose_a_public_resolution_writer(tmp_path: Path):
    semantic = SemanticWorld(
        tmp_path / "semantic.sqlite",
        world_id="semantic-world",
        contract_id=RESOLUTION_CONTRACT.contract_id,
        contract_revision=RESOLUTION_CONTRACT.contract_revision,
    )
    try:
        assert not hasattr(semantic, "record_resolution")
        assert not hasattr(semantic._store, "record_resolution")
        with pytest.raises(AttributeError):
            getattr(semantic, "record_resolution")
    finally:
        semantic.close()

    construction = ConstructionWorld.create(
        tmp_path / "construction.sqlite",
        world_id="construction-world",
        contract=RESOLUTION_CONTRACT,
    )
    try:
        assert not hasattr(construction, "record_resolution")
        with pytest.raises(AttributeError):
            getattr(construction, "record_resolution")
    finally:
        construction.close()


def test_resolver_materializes_replaces_and_reopens_current_resolution(
    tmp_path: Path,
):
    path = tmp_path / "world.sqlite"
    world = ConstructionWorld.create(
        path,
        world_id="resolution-world",
        contract=RESOLUTION_CONTRACT,
    )
    try:
        world.add_obligation("O1", question="Which Commitment governs?")

        first = resolve_world(world, RESOLUTION_CONTRACT)
        assert first[0].status is ResolutionStatus.NO_CANDIDATE
        assert world.resolution("O1")["status"] == "NO_CANDIDATE"

        world.add_referent("a")
        world.declare_relation("fact", [Role("subject", RoleType.REFERENT)])
        commitment = world.assert_tuple(
            "fact",
            {"subject": "a"},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(), construction_method="resolver boundary fixture"
            ),
        )
        world.add_candidate("O1", commitment.assertion_id)

        second = resolve_world(world, RESOLUTION_CONTRACT)
        assert second[0].status is ResolutionStatus.INSUFFICIENT_WARRANT
        materialized = world.resolution("O1")
        assert materialized["status"] == "INSUFFICIENT_WARRANT"
        assert materialized["selected_commitment_id"] is None
        assert materialized["candidate_assessments"][0]["commitment_id"] == (
            commitment.assertion_id
        )

        before_repeat = dict(materialized)
        repeated = resolve_world(world, RESOLUTION_CONTRACT)
        assert repeated == second
        assert world.resolution("O1") == before_repeat
    finally:
        world.close()

    reopened = ConstructionWorld.open(path, world_id="resolution-world")
    try:
        assert reopened.resolution("O1") == before_repeat
        assert reopened.resolutions() == [before_repeat]
    finally:
        reopened.close()
