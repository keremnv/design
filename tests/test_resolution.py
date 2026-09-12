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

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    DESIGN_EVIDENCE_AUTHORITY,
    DESIGN_LAW,
    load_evidence_authority,
)


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
        supports = candidate.get("supports")
        if supports is None:
            supports = [candidate.get("support", "agent")]
        commitment = None
        for support in supports:
            observations = ()
            if support == "approved_requirement":
                observations = (
                    SourceObservation(
                        provider="file",
                        native_handle="checkout-requirements.md",
                        source_revision=source.file_hash("checkout-requirements.md"),
                        native_location="approved availability requirement",
                    ),
                )
            elif support == "implementation":
                observations = (
                    SourceObservation(
                        provider="file",
                        native_handle="Checkout.tsx",
                        source_revision=source.file_hash("Checkout.tsx"),
                        native_location="current availability manifestation",
                    ),
                )
            elif support == "unbound":
                observations = (
                    SourceObservation(
                        provider="file",
                        native_handle="unbound-evidence.md",
                        source_revision="unbound-r1",
                        native_location="unbound evidence",
                    ),
                )
            elif support != "agent":
                raise ValueError(f"unknown scenario support {support!r}")
            extra = {"interpretation": "bounded resolution scenario fixture"}
            if candidate.get("claimed_authority"):
                extra["claimed_authority"] = candidate["claimed_authority"]
            commitment = world.assert_tuple(
                relation,
                values,
                origin=ConstructionOrigin.SEMANTIC,
                grounding=AssertionGrounding(
                    observations=observations,
                    construction_method="bounded resolution scenario fixture",
                    extra=extra,
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
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
    )
    assert result.succeeded, result.errors
    world = Project(root).open_world()
    return result, world


@pytest.mark.parametrize(
    ("support", "expected_status"),
    [
        ("implementation", "INSUFFICIENT_WARRANT"),
        ("agent", "INSUFFICIENT_WARRANT"),
    ],
)
def test_admitted_candidate_without_authoritative_warrant_stays_unresolved(
    tmp_path: Path,
    support: str,
    expected_status: str,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "support": support,
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
                "support": "approved_requirement",
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
        assessment = resolution["candidate_assessments"][0]
        assert assessment["warrant_authorities"] == ["APPROVED_REQUIREMENT"]
        assert assessment["authority_basis"][0]["source_id"] == (
            "file://checkout-requirements.md"
        )
        assert assessment["authority_basis"][0]["authority_id"] == (
            "design-mobile-checkout-evidence"
        )
    finally:
        world.close()

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        demand = explorer.demand()
        item = demand["obligations"][0]
        assert item["resolution"]["status"] == "RESOLVED"
        assert item["resolution"]["selected_commitment_id"] == commitment_id
        assert explorer.resolution("O7")["status"] == "RESOLVED"
        assert explorer.evidence_authority()["identity"] == {
            "authority_id": "design-mobile-checkout-evidence",
            "revision": "1",
        }
        assert explorer.evidence_authority()["bindings"] == [
            {
                "authority": "APPROVED_REQUIREMENT",
                "source_id": "file://checkout-requirements.md",
            },
            {
                "authority": "IMPLEMENTATION_OBSERVATION",
                "source_id": "file://Checkout.tsx",
            },
        ]

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        payload = client.get("/world/resolution", params={"obligation_id": "O7"}).json()
        assert payload["status"] == "RESOLVED"
        obligations = client.get("/world/obligations").json()
        assert obligations["resolutions"]["O7"]["status"] == "RESOLVED"
        assert client.get("/world/evidence-authority").json()["identity"] == {
            "authority_id": "design-mobile-checkout-evidence",
            "revision": "1",
        }


def test_removing_external_authority_binding_changes_the_same_candidate_to_insufficient(
    tmp_path: Path,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "support": "approved_requirement",
            }
        ],
    )
    _result, world = _evaluate(root)
    try:
        commitment_id = world.relation_rows("candidate_for")[0]["commitment"]
        warrant_before = world.warrant_for_assertion(commitment_id)
        assert world.resolution("O7")["status"] == "RESOLVED"
    finally:
        world.close()

    manifest_path = root / "evidence-authorities.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bindings"] = [
        item
        for item in manifest["bindings"]
        if item["source_id"] != "file://checkout-requirements.md"
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    reduced_authority = load_evidence_authority(root)
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=reduced_authority,
    )
    assert result.succeeded, result.errors
    world = Project(root).open_world()
    try:
        assert world.relation_rows("candidate_for")[0]["commitment"] == commitment_id
        assert world.warrant_for_assertion(commitment_id) == warrant_before
        resolution = world.resolution("O7")
        assert resolution["status"] == "INSUFFICIENT_WARRANT"
        assert resolution["candidate_assessments"][0]["authority_basis"] == []
        assert resolution["candidate_assessments"][0]["warrant_authorities"] == []
    finally:
        world.close()


def test_constructor_claimed_authority_cannot_create_sufficient_evidence(
    tmp_path: Path,
):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "support": "agent",
                "claimed_authority": "APPROVED_REQUIREMENT",
            }
        ],
    )
    _result, world = _evaluate(root)
    try:
        commitment_id = world.relation_rows("candidate_for")[0]["commitment"]
        resolution = world.resolution("O7")
        assert resolution["status"] == "INSUFFICIENT_WARRANT"
        assert resolution["candidate_assessments"][0]["authority_basis"] == []
        warrant = world.warrant_for_assertion(commitment_id)
        world_bases = [item for item in warrant["bases"] if item["kind"] == "WORLD"]
        assert world_bases[0]["detail"]["extra"]["claimed_authority"] == (
            "APPROVED_REQUIREMENT"
        )
    finally:
        world.close()


def test_unbound_evidence_remains_inspectable_but_is_insufficient(tmp_path: Path):
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": "remains_available_during",
                "support": "unbound",
            }
        ],
    )
    _result, world = _evaluate(root)
    try:
        commitment_id = world.relation_rows("candidate_for")[0]["commitment"]
        resolution = world.resolution("O7")
        assert resolution["status"] == "INSUFFICIENT_WARRANT"
        assert resolution["candidate_assessments"][0]["authority_basis"] == []
        warrant = world.warrant_for_assertion(commitment_id)
        assert any(
            base["kind"] == "SOURCE"
            and base["detail"]["native_handle"] == "unbound-evidence.md"
            for base in warrant["bases"]
        )
    finally:
        world.close()


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
                "support": "approved_requirement",
            },
            {
                "relation": "does_not_remain_available_during",
                "support": "approved_requirement",
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
                "support": "approved_requirement",
            },
            {
                "relation": "does_not_remain_available_during",
                "support": "implementation",
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
                "supports": ["agent", "approved_requirement"],
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
                "support": "approved_requirement",
            }
        ],
    )
    assert rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
    ).succeeded
    before = fingerprint_world(root / "world")

    broken = (root / "construction.py").read_text(encoding="utf-8")
    broken = broken.replace(
        '"obligation": "O7", "commitment": commitment_id',
        '"obligation": "missing", "commitment": commitment_id',
    )
    (root / "construction.py").write_text(broken, encoding="utf-8")
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
    )
    assert not result.succeeded
    assert fingerprint_world(root / "world") == before
