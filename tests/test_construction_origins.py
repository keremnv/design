from __future__ import annotations

import pytest

from ontology_author.world.core.kernel import SemanticWorld
from ontology_author.world.core.model import (
    Completeness,
    CompletenessStatus,
    GroundingKind,
    RelationMode,
    Role,
    RoleType,
)
from ontology_author.world.core.origins import (
    ConstructionOrigin,
    OriginMetadataError,
)
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.explorer import WorldExplorerAdapter


def _world(tmp_path):
    return SemanticWorld(
        tmp_path / "world.sqlite",
        world_id="origin-test",
        contract_id="origin-contract",
        contract_revision="1",
    )


def _fact(world: SemanticWorld) -> dict[str, str]:
    world.add_referent("a", label="A")
    world.declare_relation("fact", [Role("subject", RoleType.REFERENT)])
    return {"subject": "a"}


def test_one_commitment_keeps_distinct_support_path_origins_after_reopen(tmp_path):
    world = _world(tmp_path)
    values = _fact(world)
    try:
        first = world.assert_tuple(
            "fact",
            values,
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(),
                construction_method="agent interpretation",
            ),
        )
        second = world.assert_tuple(
            "fact",
            values,
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding(
                observations=(
                    SourceObservation(
                        provider="workspace",
                        native_handle="evidence.md",
                        source_revision="evidence-r1",
                        native_location="fact",
                    ),
                ),
                construction_method="mechanical extraction",
            ),
        )

        assert first.assertion_id == second.assertion_id
        assert first.inserted is True
        assert second.inserted is False
        assert world.origins_for_assertion(first.assertion_id) == [
            "MECHANICAL",
            "SEMANTIC",
        ]
        with pytest.raises(OriginMetadataError, match="multiple construction origins"):
            world.origin_for_assertion(first.assertion_id)

        warrant = world.warrant_for_assertion(first.assertion_id)
        assert warrant["recorded_construction_origin"] == "MULTIPLE"
        assert warrant["construction_origins"] == ["MECHANICAL", "SEMANTIC"]
        world_bases = [
            item for item in warrant["bases"] if item["kind"] == GroundingKind.WORLD
        ]
        assert {item["construction_origin"] for item in world_bases} == {
            "MECHANICAL",
            "SEMANTIC",
        }
        assert any(item["kind"] == GroundingKind.SOURCE for item in warrant["bases"])

        inspected = world.inspect_tuple("fact", values)
        assert inspected["construction_origins"] == ["MECHANICAL", "SEMANTIC"]
        assert inspected["construction_origin"] == "MULTIPLE"
        assert not (tmp_path / "world.sqlite.origins.json").exists()
    finally:
        world.close()

    reopened = SemanticWorld(
        tmp_path / "world.sqlite",
        world_id="origin-test",
        read_only=True,
    )
    try:
        assert reopened.origins_for_assertion(first.assertion_id) == [
            "MECHANICAL",
            "SEMANTIC",
        ]
        assert reopened.warrant_for_assertion(first.assertion_id)[
            "construction_origins"
        ] == ["MECHANICAL", "SEMANTIC"]
    finally:
        reopened.close()


def test_explorer_reports_all_support_origins_without_sidecar(tmp_path):
    world = _world(tmp_path)
    values = _fact(world)
    try:
        assertion = world.assert_tuple(
            "fact",
            values,
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(), construction_method="semantic support"
            ),
        )
        world.assert_tuple(
            "fact",
            values,
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding(
                observations=(
                    SourceObservation(
                        provider="workspace",
                        native_handle="evidence.md",
                        source_revision="evidence-r1",
                        native_location="fact",
                    ),
                ),
                construction_method="mechanical support",
            ),
        )
    finally:
        world.close()

    with WorldExplorerAdapter(tmp_path / "world.sqlite") as explorer:
        assert explorer.rows("fact")["rows"][0]["origins"] == [
            "MECHANICAL",
            "SEMANTIC",
        ]
        fact_schema = next(item for item in explorer.schema() if item["name"] == "fact")
        assert fact_schema["origins"] == ["MECHANICAL", "SEMANTIC"]
        inspected = explorer.assertion(assertion.assertion_id)
        assert inspected["origins"] == ["MECHANICAL", "SEMANTIC"]
        assert inspected["origin"] == "MULTIPLE"
        assert explorer.overview()["origins"] == {"MECHANICAL": 1, "SEMANTIC": 1}


def test_derived_assertion_keeps_derivation_lineage_as_derived_origin(tmp_path):
    world = _world(tmp_path)
    try:
        _fact(world)
        world.assert_tuple(
            "fact",
            {"subject": "a"},
            origin=ConstructionOrigin.MECHANICAL,
        )
        world.declare_relation(
            "selected",
            [Role("subject", RoleType.REFERENT)],
            mode=RelationMode.DERIVED,
        )
        world.register_derivation(
            "selected",
            sql="SELECT subject_id FROM fact",
            inputs=["fact"],
        )
        world.rerun(
            "selected",
            completeness=Completeness(
                CompletenessStatus.COMPLETE,
                universe="fact",
                basis="all facts selected",
            ),
        )
        assertion_id = world.query(
            "SELECT _assertion_id FROM selected"
        )[0]["_assertion_id"]

        assert world.origins_for_assertion(assertion_id) == ["DERIVED"]
        warrant = world.warrant_for_assertion(assertion_id)
        assert warrant["assertion_origin"] == "DERIVED"
        assert warrant["construction_origins"] == ["DERIVED"]
        assert [item["kind"] for item in warrant["bases"]] == [
            GroundingKind.DERIVATION.value
        ]
        assert world.inspect_tuple("selected", {"subject": "a"})[
            "construction_origin"
        ] == "DERIVED"
        assert not (tmp_path / "world.sqlite.origins.json").exists()
    finally:
        world.close()
