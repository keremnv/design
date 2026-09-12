from __future__ import annotations

from pathlib import Path

from ontology_author.world import Contract, Project
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.commit import fingerprint_world
from ontology_author.world.runtime.entry import rebuild


DESIGN_CONTRACT = Contract(
    "design-core",
    "1",
    semantic_origins=frozenset({ConstructionOrigin.SEMANTIC.value}),
)


DESIGN_CONSTRUCTION = '''def construct(source, world, purpose):
    assert contract.contract_id == "design-core"
    assert contract.contract_revision == "1"
    for referent in ("order_total", "promo_code", "checkout_commitment"):
        world.add_referent(referent, label=referent.replace("_", " "))

    world.add_obligation(
        "O7",
        question="Determine relative prominence of total versus promo at checkout commitment.",
    )
    world.declare_relation(
        "relative_prominence",
        [
            Role("more", RoleType.REFERENT),
            Role("less", RoleType.REFERENT),
            Role("context", RoleType.REFERENT),
        ],
        scope="WORLD",
    )
    commitment = world.assert_tuple(
        "relative_prominence",
        {
            "more": "order_total",
            "less": "promo_code",
            "context": "checkout_commitment",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(),
            construction_method="agent design judgment from requirements and code",
        ),
    )
    world.add_candidate("O7", commitment.assertion_id)
'''


def _workspace(tmp_path: Path, construction: str) -> Path:
    root = tmp_path / "design-world"
    root.mkdir(parents=True)
    (root / "PURPOSE.md").write_text(
        "# Purpose\n\nDetermine checkout prominence.\n", encoding="utf-8"
    )
    (root / "construction.py").write_text(construction, encoding="utf-8")
    return root


def test_design_contract_constructs_and_publishes_first_slice(tmp_path):
    root = _workspace(tmp_path, DESIGN_CONSTRUCTION)
    result = rebuild(root, contract=DESIGN_CONTRACT)
    assert result.succeeded, result.errors

    world = Project(root).open_world()
    try:
        assert world.contract_identity() == {
            "contract_id": "design-core",
            "contract_revision": "1",
        }
        obligation = world.obligation("O7")
        assert obligation is not None
        assert obligation["question"].startswith("Determine relative prominence")
        assert obligation["state"] == "UNRESOLVED"

        commitment_id = world.query(
            "SELECT assertion_id FROM _world_assertions "
            "WHERE relation_name = 'relative_prominence'"
        )[0]["assertion_id"]
        assert world.candidates_for("O7") == [commitment_id]
        assert world.obligations_for(commitment_id) == ["O7"]

        warrant = world.warrant_for_assertion(commitment_id)
        assert warrant["commitment_id"] == commitment_id
        assert warrant["construction_origins"] == ["SEMANTIC"]
        assert {item["kind"] for item in warrant["bases"]} == {"WORLD"}
        assert all(
            row["kind"] != "SOURCE"
            for row in world.query(
                "SELECT kind FROM _world_groundings "
                "WHERE subject_type = 'ASSERTION'"
            )
        )
    finally:
        world.close()

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert explorer.identity()["contract"] == {
            "contract_id": "design-core",
            "contract_revision": "1",
        }
        demand = explorer.demand()
        assert demand is not None
        assert demand["obligations"] == [
            {
                "obligation_id": "O7",
                "question": "Determine relative prominence of total versus promo at checkout commitment.",
                "relation": None,
                "values": {},
                "reason": None,
                "demanded_by": {
                    "kind": "contract",
                    "name": "O7",
                    "contract_id": "design-core",
                    "contract_revision": "1",
                },
                "state": "UNRESOLVED",
                "assertion_id": None,
                "record_id": None,
                "grounding_ref": None,
                "contract_id": "design-core",
                "contract_revision": "1",
                "candidates": [
                    {
                        "relation": "candidate_for",
                        "association_id": demand["obligations"][0]["candidates"][0]["association_id"],
                        "commitment_id": demand["obligations"][0]["candidates"][0]["commitment_id"],
                        "created_revision": demand["obligations"][0]["candidates"][0]["created_revision"],
                    }
                ],
            }
        ]
        commitment = explorer.assertion(commitment_id)
        assert commitment["commitment_id"] == commitment_id
        assert commitment["warrant"]["construction_origins"] == ["SEMANTIC"]


def test_default_contract_still_rejects_ungrounded_world_base(tmp_path):
    root = _workspace(
        tmp_path,
        '''def construct(source, world, purpose):
    world.declare_relation("fact", [Role("subject", RoleType.REFERENT)], scope="WORLD")
    world.add_referent("thing")
    world.assert_tuple(
        "fact",
        {"subject": "thing"},
        origin=ConstructionOrigin.MECHANICAL,
    )
''',
    )
    result = rebuild(root)
    assert not result.succeeded
    assert result.reason == "ungrounded_world_base"
    assert not (root / "world").exists()


def test_semantic_judgment_requires_contract_authorization(tmp_path):
    root = _workspace(
        tmp_path,
        '''def construct(source, world, purpose):
    world.declare_relation("judgment", [Role("statement", RoleType.TEXT)], scope="WORLD")
    world.assert_tuple(
        "judgment",
        {"statement": "total is more prominent than promo"},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=(), construction_method="agent design judgment"
        ),
    )
''',
    )
    result = rebuild(root)
    assert not result.succeeded
    assert result.reason == "ungrounded_world_base"

    authorized = rebuild(root, contract=DESIGN_CONTRACT)
    assert authorized.succeeded, authorized.errors


def test_candidate_reference_targets_are_hard_and_candidate_does_not_resolve(tmp_path):
    for role, _value, expected in (
        ("obligation", "missing-obligation", "unknown candidate obligation"),
        ("commitment", "assertion:not-real", "unknown candidate commitment"),
    ):
        construction = DESIGN_CONSTRUCTION
        if role == "obligation":
            construction = construction.replace(
                'world.add_candidate("O7", commitment.assertion_id)',
                'world.add_candidate("missing-obligation", commitment.assertion_id)',
            )
        else:
            construction = construction.replace(
                'world.add_candidate("O7", commitment.assertion_id)',
                'world.add_candidate("O7", "assertion:not-real")',
            )
        root = _workspace(tmp_path / role, construction)
        result = rebuild(root, contract=DESIGN_CONTRACT)
        assert not result.succeeded
        assert expected in " ".join(result.errors)

    root = _workspace(tmp_path / "valid", DESIGN_CONSTRUCTION)
    result = rebuild(root, contract=DESIGN_CONTRACT)
    assert result.succeeded, result.errors
    world = Project(root).open_world()
    try:
        assert world.obligation("O7")["state"] == "UNRESOLVED"
    finally:
        world.close()


def test_failed_contract_publication_leaves_previous_world_untouched(tmp_path):
    root = _workspace(tmp_path, DESIGN_CONSTRUCTION)
    assert rebuild(root, contract=DESIGN_CONTRACT).succeeded
    before = fingerprint_world(root / "world")
    bypass = DESIGN_CONSTRUCTION.replace(
        'grounding=AssertionGrounding(\n            observations=(),\n            construction_method="agent design judgment from requirements and code",\n        ),',
        "grounding=None,",
    )
    bypass = bypass.replace(
        "world.assert_tuple(\n        \"relative_prominence\",",
        "world._inner.assert_tuple(\n        \"relative_prominence\",",
        1,
    )
    root.joinpath("construction.py").write_text(bypass, encoding="utf-8")
    result = rebuild(root, contract=DESIGN_CONTRACT)
    assert not result.succeeded
    assert result.reason == "contract_admission"
    assert fingerprint_world(root / "world") == before
