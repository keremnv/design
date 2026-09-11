from __future__ import annotations

import shutil
from pathlib import Path

from ontology_author.world import Project
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.entry import rebuild

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    DESIGN_OBLIGATIONS,
    DESIGN_REFERENTS,
    DESIGN_RELATIONS,
)


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"


def _copy_fixture(tmp_path: Path, name: str = "design-world") -> Path:
    root = tmp_path / name
    shutil.copytree(FIXTURE, root)
    return root


def _assertion_id(world, relation: str) -> str:
    return str(
        world.query(
            "SELECT assertion_id FROM _world_assertions "
            "WHERE relation_name = ? ORDER BY assertion_id",
            (relation,),
        )[0]["assertion_id"]
    )


def test_mobile_checkout_profile_constructs_through_project_lifecycle(tmp_path):
    root = _copy_fixture(tmp_path)
    result = rebuild(root, contract=DESIGN_CONTRACT)
    assert result.succeeded, result.errors

    world = Project(root).open_world()
    try:
        assert world.contract_identity() == {
            "contract_id": "design-mobile-checkout",
            "contract_revision": "1",
        }
        assert {
            row["id"] for row in world.query("SELECT id FROM _world_referents")
        } == set(DESIGN_REFERENTS)
        assert world.obligations() == [
            {
                "obligation_id": obligation_id,
                "question": question,
                "state": "UNRESOLVED",
                "reason": "A candidate is recorded, but no resolver runs in this slice.",
                "contract_id": "design-mobile-checkout",
                "contract_revision": "1",
                "created_revision": world.obligation(obligation_id)["created_revision"],
            }
            for obligation_id, question in sorted(DESIGN_OBLIGATIONS.items())
        ]

        assert world.relation_rows("relative_prominence") == [
            {
                "more": "order_total",
                "less": "promo_code",
                "context": "checkout_commitment",
            }
        ]
        assert world.relation_rows("remains_available_during") == [
            {
                "subject": "order_summary",
                "activity": "payment_entry",
                "context": "mobile_checkout",
            }
        ]
        assert world.relation_rows("supports") == [
            {
                "subject": "order_summary",
                "goal": "purchase_confidence",
                "context": "checkout_commitment",
            }
        ]

        prominent_id = _assertion_id(world, "relative_prominence")
        available_id = _assertion_id(world, "remains_available_during")
        supports_id = _assertion_id(world, "supports")
        candidate_rows = world.relation_rows("candidate_for")
        assert {row["obligation"] for row in candidate_rows} == set(DESIGN_OBLIGATIONS)
        assert {row["commitment"] for row in candidate_rows} == {
            prominent_id,
            available_id,
            supports_id,
        }

        prominent_warrant = world.warrant_for_assertion(prominent_id)
        assert prominent_warrant["recorded_construction_origin"] == "SEMANTIC"
        assert {base["kind"] for base in prominent_warrant["bases"]} == {
            "SOURCE",
            "WORLD",
        }
        assert any(
            "agent design judgment" in str(base.get("detail", {}).get("construction_method", ""))
            for base in prominent_warrant["bases"]
            if base["kind"] == "WORLD"
        )

        available_warrant = world.warrant_for_assertion(available_id)
        assert available_warrant["recorded_construction_origin"] == "MECHANICAL"
        assert {base["kind"] for base in available_warrant["bases"]} == {
            "SOURCE",
            "WORLD",
        }
        assert any(
            "explicit checkout requirement"
            in str(base.get("detail", {}).get("construction_method", ""))
            for base in available_warrant["bases"]
            if base["kind"] == "WORLD"
        )
    finally:
        world.close()

    # The ordinary read-side object reopens the sealed bundle, rather than
    # relying on the mutable ConstructionWorld that produced it.
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert explorer.identity()["contract"] == {
            "contract_id": "design-mobile-checkout",
            "contract_revision": "1",
        }
        assert {item["id"] for item in explorer.referents()} == set(DESIGN_REFERENTS)

        schema = {item["name"]: item for item in explorer.schema()}
        assert (
            set(DESIGN_RELATIONS) - {"does_not_remain_available_during"}
        ).issubset(schema)
        assert schema["candidate_for"]["roles"] == [
            {
                "name": "obligation",
                "type": "TEXT",
                "column": "obligation",
                "referent": False,
                "kinds": [],
                "reference_kind": "OBLIGATION",
            },
            {
                "name": "commitment",
                "type": "TEXT",
                "column": "commitment",
                "referent": False,
                "kinds": [],
                "reference_kind": "COMMITMENT",
            },
        ]

        demand = explorer.demand()
        assert demand is not None
        assert demand["demanded"] == len(DESIGN_OBLIGATIONS)
        assert len(demand["obligations"]) == len(DESIGN_OBLIGATIONS)
        for obligation in demand["obligations"]:
            assert obligation["state"] == "UNRESOLVED"
            assert obligation["reason"]
            assert len(obligation["candidates"]) == 1

        prominent_id = explorer.rows("relative_prominence")["rows"][0]["assertion_id"]
        commitment = explorer.assertion(prominent_id)
        assert commitment["commitment_id"] == prominent_id
        assert commitment["values"] == {
            "more": "order_total",
            "less": "promo_code",
            "context": "checkout_commitment",
        }
        assert commitment["warrant"]["recorded_construction_origin"] == "SEMANTIC"
        assert explorer.rows("candidate_for")["total"] == len(DESIGN_OBLIGATIONS)


def test_design_contract_rejects_unlisted_semantic_decisions(tmp_path):
    root = _copy_fixture(tmp_path, "unauthorized")
    (root / "construction.py").write_text(
        '''def construct(source, world, purpose):
    world.add_referent("order_total")
    world.declare_relation(
        "unlisted_design_decision",
        [Role("subject", RoleType.REFERENT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "unlisted_design_decision",
        {"subject": "order_total"},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(), construction_method="agent design judgment"
        ),
    )
''',
        encoding="utf-8",
    )

    result = rebuild(root, contract=DESIGN_CONTRACT)
    assert not result.succeeded
    assert result.reason == "semantic_relation_not_authorized"
    assert not (root / "world").exists()


def test_design_contract_keeps_nonsemantic_world_facts_source_grounded(tmp_path):
    root = _copy_fixture(tmp_path, "source-required")
    (root / "construction.py").write_text(
        '''def construct(source, world, purpose):
    world.add_referent("order_total")
    world.declare_relation(
        "source_fact",
        [Role("subject", RoleType.REFERENT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "source_fact",
        {"subject": "order_total"},
        origin=ConstructionOrigin.MECHANICAL,
        grounding=None,
    )
''',
        encoding="utf-8",
    )

    rejected = rebuild(root, contract=DESIGN_CONTRACT)
    assert not rejected.succeeded
    assert rejected.reason == "ungrounded_world_base"

    (root / "construction.py").write_text(
        '''def construct(source, world, purpose):
    world.add_referent("order_total")
    world.declare_relation(
        "source_fact",
        [Role("subject", RoleType.REFERENT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "source_fact",
        {"subject": "order_total"},
        origin=ConstructionOrigin.MECHANICAL,
        grounding=source.grounding("checkout-requirements.md", "order total is present"),
    )
''',
        encoding="utf-8",
    )
    accepted = rebuild(root, contract=DESIGN_CONTRACT)
    assert accepted.succeeded, accepted.errors


def _write_counterfactual(
    root: Path,
    *,
    more: str,
    less: str,
    availability_relation: str,
) -> None:
    root.mkdir()
    (root / "PURPOSE.md").write_text("# Purpose\n\nCounterfactual adequacy.\n", encoding="utf-8")
    (root / "construction.py").write_text(
        f'''def construct(source, world, purpose):
    for referent in ("mobile_checkout", "checkout_commitment", "order_total", "promo_code", "order_summary", "payment_entry"):
        world.add_referent(referent)
    world.declare_relation(
        "relative_prominence",
        [Role("more", RoleType.REFERENT), Role("less", RoleType.REFERENT), Role("context", RoleType.REFERENT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "relative_prominence",
        {{"more": "{more}", "less": "{less}", "context": "checkout_commitment"}},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(observations=(), construction_method="counterfactual judgment"),
    )
    world.declare_relation(
        "{availability_relation}",
        [Role("subject", RoleType.REFERENT), Role("activity", RoleType.REFERENT), Role("context", RoleType.REFERENT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "{availability_relation}",
        {{"subject": "order_summary", "activity": "payment_entry", "context": "mobile_checkout"}},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(observations=(), construction_method="counterfactual judgment"),
    )
''',
        encoding="utf-8",
    )


def test_design_profile_preserves_direction_and_positive_negative_availability(tmp_path):
    prominence_a = tmp_path / "prominence-a"
    prominence_b = tmp_path / "prominence-b"
    _write_counterfactual(
        prominence_a,
        more="order_total",
        less="promo_code",
        availability_relation="remains_available_during",
    )
    _write_counterfactual(
        prominence_b,
        more="promo_code",
        less="order_total",
        availability_relation="remains_available_during",
    )
    assert rebuild(prominence_a, contract=DESIGN_CONTRACT).succeeded
    assert rebuild(prominence_b, contract=DESIGN_CONTRACT).succeeded
    first = Project(prominence_a).open_world()
    second = Project(prominence_b).open_world()
    try:
        assert {
            tuple(row.values()) for row in first.relation_rows("relative_prominence")
        } != {
            tuple(row.values()) for row in second.relation_rows("relative_prominence")
        }
    finally:
        first.close()
        second.close()

    available = tmp_path / "availability-positive"
    unavailable = tmp_path / "availability-negative"
    _write_counterfactual(
        available,
        more="order_total",
        less="promo_code",
        availability_relation="remains_available_during",
    )
    _write_counterfactual(
        unavailable,
        more="order_total",
        less="promo_code",
        availability_relation="does_not_remain_available_during",
    )
    assert rebuild(available, contract=DESIGN_CONTRACT).succeeded
    assert rebuild(unavailable, contract=DESIGN_CONTRACT).succeeded
    positive = Project(available).open_world()
    negative = Project(unavailable).open_world()
    try:
        expected = ("order_summary", "payment_entry", "mobile_checkout")
        assert {
            tuple(row.values()) for row in positive.relation_rows("remains_available_during")
        } == {expected}
        assert {
            tuple(row.values())
            for row in negative.relation_rows("does_not_remain_available_during")
        } == {expected}
        assert "remains_available_during" not in {
            row["name"]
            for row in negative.query("SELECT name FROM _world_relations")
        }
    finally:
        positive.close()
        negative.close()
