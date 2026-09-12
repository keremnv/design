from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from ontology_author.world import Project
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.commit import fingerprint_world
from ontology_author.world.runtime.entry import rebuild
from ontology_author.world.server import build_app

from profiles.design_checkout import DESIGN_CONTRACT, DESIGN_LAW


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"


SCENARIO_CONSTRUCTION = '''
import json


def construct(source, world, purpose):
    scenario = json.loads(source.read_text("resolution-scenario.json"))
    referents = ("order_summary", "payment_entry", "mobile_checkout")
    for referent in referents:
        world.add_referent(referent, label=referent.replace("_", " "))

    world.add_obligation(
        "O7",
        question="What availability relationship should hold?",
    )
    availability_roles = [
        Role("subject", RoleType.REFERENT),
        Role("activity", RoleType.REFERENT),
        Role("context", RoleType.REFERENT),
    ]
    for relation in (
        "remains_available_during",
        "does_not_remain_available_during",
    ):
        world.declare_relation(
            relation,
            availability_roles,
            description="Scenario availability answer.",
            scope="WORLD",
        )

    commitments = []
    for candidate in scenario.get("candidates", []):
        relation = candidate["relation"]
        values = {
            "subject": "order_summary",
            "activity": "payment_entry",
            "context": "mobile_checkout",
        }
        authorities = candidate.get("authorities", [candidate["authority"]])
        commitment = None
        for authority in authorities:
            observations = ()
            if authority == "APPROVED_REQUIREMENT":
                observations = (
                    SourceObservation(
                        provider="fixture",
                        native_handle="checkout-requirements.md",
                        source_revision="requirements-r1",
                        native_location="approved availability requirement",
                    ),
                )
            elif authority == "IMPLEMENTATION_OBSERVATION":
                observations = (
                    SourceObservation(
                        provider="fixture",
                        native_handle="Checkout.tsx",
                        source_revision="checkout-r1",
                        native_location="current availability manifestation",
                    ),
                )
            commitment = world.assert_tuple(
                relation,
                values,
                origin=ConstructionOrigin.SEMANTIC,
                grounding=AssertionGrounding(
                    observations=observations,
                    construction_method="bounded resolution scenario fixture",
                    extra={"resolution_authority": authority},
                ),
            )
        commitments.append(commitment.assertion_id)

    world.declare_relation(
        "candidate_for",
        [
            Role(
                "obligation",
                RoleType.TEXT,
                reference_kind=SemanticRefKind.OBLIGATION,
            ),
            Role(
                "commitment",
                RoleType.TEXT,
                reference_kind=SemanticRefKind.COMMITMENT,
            ),
        ],
        description="Scenario candidate relationship.",
        scope="WORLD",
    )
    for commitment_id in commitments:
        world.assert_tuple(
            "candidate_for",
            {"obligation": "O7", "commitment": commitment_id},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(),
                construction_method="bounded resolution scenario candidate",
            ),
        )
'''


def _scenario_root(tmp_path: Path, *, candidates: list[dict]) -> Path:
    root = tmp_path / "resolution-world"
    shutil.copytree(FIXTURE, root)
    (root / "construction.py").write_text(SCENARIO_CONSTRUCTION, encoding="utf-8")
    (root / "resolution-scenario.json").write_text(
        json.dumps({"candidates": candidates}), encoding="utf-8"
    )
    return root


def _evaluate(root: Path):
    result = rebuild(root, contract=DESIGN_CONTRACT, governance=DESIGN_LAW)
    assert result.succeeded, result.errors
    world = Project(root).open_world()
    return result, world


@pytest.mark.parametrize(
    ("authority", "expected_status"),
    [
        ("IMPLEMENTATION_OBSERVATION", "INSUFFICIENT_WARRANT"),
        ("AGENT_JUDGMENT", "INSUFFICIENT_WARRANT"),
    ],
)
def test_admitted_candidate_without_authoritative_warrant_stays_unresolved(
    tmp_path: Path,
    authority: str,
    expected_status: str,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "authority": authority,
            }
        ],
    )
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == expected_status
        assert resolution["selected_commitment_id"] is None
        assert resolution["candidate_assessments"][0]["status"] == "INSUFFICIENT"
        assert world.obligation("O7")["state"] == "UNRESOLVED"
        assert world.relation_rows("candidate_for")
    finally:
        world.close()


def test_authoritative_requirement_resolves_and_survives_reopen_and_read_surface(
    tmp_path: Path,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "authority": "APPROVED_REQUIREMENT",
            }
        ],
    )
    _result, world = _evaluate(root)
    try:
        commitment_id = world.relation_rows("candidate_for")[0]["commitment"]
        assert world.obligation("O7")["state"] == "RESOLVED"
        resolution = world.resolution("O7")
        assert resolution["status"] == "RESOLVED"
        assert resolution["selected_commitment_id"] == commitment_id
        assert resolution["candidate_assessments"][0]["status"] == "SUFFICIENT"
    finally:
        world.close()

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        demand = explorer.demand()
        item = demand["obligations"][0]
        assert item["resolution"]["status"] == "RESOLVED"
        assert item["resolution"]["selected_commitment_id"] == commitment_id
        assert explorer.resolution("O7")["status"] == "RESOLVED"

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        payload = client.get("/world/resolution", params={"obligation_id": "O7"}).json()
        assert payload["status"] == "RESOLVED"
        obligations = client.get("/world/obligations").json()
        assert obligations["resolutions"]["O7"]["status"] == "RESOLVED"


def test_no_candidate_is_a_persisted_unresolved_resolution(tmp_path: Path):
    root = _scenario_root(tmp_path, candidates=[])
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == "NO_CANDIDATE"
        assert resolution["candidate_assessments"] == []
        assert world.obligation("O7")["state"] == "UNRESOLVED"
    finally:
        world.close()

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        item = explorer.demand()["obligations"][0]
        assert item["resolution"]["status"] == "NO_CANDIDATE"
        assert item["resolution"]["reason"]


def test_two_sufficient_incompatible_answers_are_conflict_without_selection(
    tmp_path: Path,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "authority": "APPROVED_REQUIREMENT",
            },
            {
                "relation": "does_not_remain_available_during",
                "authority": "APPROVED_REQUIREMENT",
            },
        ],
    )
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == "CONFLICT"
        assert resolution["selected_commitment_id"] is None
        assert [
            item["status"] for item in resolution["candidate_assessments"]
        ] == ["SUFFICIENT", "SUFFICIENT"]
        assert world.obligation("O7")["state"] == "UNRESOLVED"
    finally:
        world.close()


def test_sufficient_answer_is_not_defeated_by_incompatible_weak_candidate(
    tmp_path: Path,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "authority": "APPROVED_REQUIREMENT",
            },
            {
                "relation": "does_not_remain_available_during",
                "authority": "IMPLEMENTATION_OBSERVATION",
            },
        ],
    )
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == "RESOLVED"
        selected = resolution["selected_commitment_id"]
        assert selected == world.relation_rows("candidate_for")[0]["commitment"]
        assert {
            item["status"] for item in resolution["candidate_assessments"]
        } == {"INSUFFICIENT", "SUFFICIENT"}
    finally:
        world.close()


def test_same_proposition_with_multiple_support_paths_has_one_commitment(
    tmp_path: Path,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "authority": "AGENT_JUDGMENT",
                "authorities": ["AGENT_JUDGMENT", "APPROVED_REQUIREMENT"],
            }
        ],
    )
    _result, world = _evaluate(root)
    try:
        commitment_rows = world.query(
            "SELECT assertion_id FROM _world_assertions "
            "WHERE relation_name = 'remains_available_during'"
        )
        assert len(commitment_rows) == 1
        commitment_id = commitment_rows[0]["assertion_id"]
        assert world.relation_rows("candidate_for") == [
            {"obligation": "O7", "commitment": commitment_id}
        ]
        warrant = world.warrant_for_assertion(commitment_id)
        assert len(warrant["bases"]) == 3
        assert world.resolution("O7")["status"] == "RESOLVED"
        assert world.resolution("O7")["selected_commitment_id"] == commitment_id
    finally:
        world.close()


def test_resolution_failure_preserves_previous_sealed_world(tmp_path: Path):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "authority": "APPROVED_REQUIREMENT",
            }
        ],
    )
    assert rebuild(root, contract=DESIGN_CONTRACT, governance=DESIGN_LAW).succeeded
    before = fingerprint_world(root / "world")

    broken = (root / "construction.py").read_text(encoding="utf-8")
    broken = broken.replace(
        '"obligation": "O7", "commitment": commitment_id',
        '"obligation": "missing", "commitment": commitment_id',
    )
    (root / "construction.py").write_text(broken, encoding="utf-8")
    result = rebuild(root, contract=DESIGN_CONTRACT, governance=DESIGN_LAW)
    assert not result.succeeded
    assert fingerprint_world(root / "world") == before
