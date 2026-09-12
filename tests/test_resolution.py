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
    DESIGN_ADJUDICATION_AUTHORITY,
    DESIGN_CONTRACT,
    DESIGN_EVIDENCE_AUTHORITY,
    DESIGN_LAW,
    load_adjudication_authority,
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

    orphan_commitment = None
    if scenario.get("orphan_commitment"):
        orphan_commitment = world.assert_tuple(
            "remains_available_during",
            {
                "subject": "order_summary",
                "activity": "payment_entry",
                "context": "mobile_checkout",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(),
                construction_method="unlinked adjudication target fixture",
            ),
        ).assertion_id

    for commitment_id in commitments:
        world.add_candidate("O7", commitment_id)

    for record in scenario.get("adjudications", []):
        candidate_index = record.get("candidate_index")
        selected_commitment = (
            commitments[int(candidate_index)]
            if candidate_index is not None
            else (
                orphan_commitment
                if record.get("select_orphan")
                else str(record.get("selected_commitment_id") or "missing-commitment")
            )
        )
        basis = {
            "source_id": str(record.get("source_id") or "unbound-review-decision"),
            "source_revision": str(record.get("source_revision") or "review-r1"),
            "source_location": str(record.get("source_location") or "decision selection"),
        }
        if record.get("claimed_authority"):
            basis["claimed_authority"] = record["claimed_authority"]
        world.add_adjudication(
            adjudication_id=str(record["adjudication_id"]),
            obligation_id=str(record.get("obligation_id") or "O7"),
            selected_commitment_id=selected_commitment,
            authority_basis=basis,
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
        adjudication_authority=DESIGN_ADJUDICATION_AUTHORITY,
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
        assert world.candidates_for("O7")
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
        commitment_id = world.candidates_for("O7")[0]
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
        governed = explorer.obligations()
        item = governed["obligations"][0]
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
        assert next(
            item["resolution"]["status"]
            for item in obligations["obligations"]
            if item["obligation_id"] == "O7"
        ) == "RESOLVED"
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
        commitment_id = world.candidates_for("O7")[0]
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
        assert world.candidates_for("O7")[0] == commitment_id
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
        commitment_id = world.candidates_for("O7")[0]
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
        commitment_id = world.candidates_for("O7")[0]
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
        item = explorer.obligations()["obligations"][0]
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


def test_unauthorized_adjudication_is_inspectable_but_does_not_break_conflict(
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
    (root / "resolution-scenario.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "relation": "remains_available_during",
                        "support": "approved_requirement",
                    },
                    {
                        "relation": "does_not_remain_available_during",
                        "support": "approved_requirement",
                    },
                ],
                "adjudications": [
                    {
                        "adjudication_id": "A1",
                        "candidate_index": 0,
                        "source_id": "unbound-review-decision",
                        "claimed_authority": "AUTHORIZED_ADJUDICATION",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == "CONFLICT"
        assert world.adjudication("A1")["selected_commitment_id"]
        assert resolution["adjudication_assessments"] == [
            {
                "adjudication_id": "A1",
                "selected_commitment_id": world.adjudication("A1")[
                    "selected_commitment_id"
                ],
                "status": "INSUFFICIENT",
                "reason": "Adjudication A1 has no external adjudicative authority binding.",
                "adjudicative_authorities": [],
                "authority_basis": [],
            }
        ]
        assert world.adjudication("A1")["authority_basis"]["claimed_authority"] == (
            "AUTHORIZED_ADJUDICATION"
        )
    finally:
        world.close()


def test_authorized_adjudication_resolves_conflict_without_erasing_candidates(
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
    (root / "resolution-scenario.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "relation": "remains_available_during",
                        "support": "approved_requirement",
                    },
                    {
                        "relation": "does_not_remain_available_during",
                        "support": "approved_requirement",
                    },
                ],
                "adjudications": [
                    {
                        "adjudication_id": "A1",
                        "candidate_index": 0,
                        "source_id": "design-review-decision",
                        "source_location": "review decision: select C1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _result, world = _evaluate(root)
    try:
        candidates = world.candidates_for("O7")
        selected = candidates[0]
        resolution = world.resolution("O7")
        assert resolution["status"] == "RESOLVED"
        assert resolution["selected_commitment_id"] == selected
        assert [item["status"] for item in resolution["candidate_assessments"]] == [
            "SUFFICIENT",
            "SUFFICIENT",
        ]
        assert resolution["adjudication_assessments"][0]["status"] == "SUFFICIENT"
        assert resolution["adjudication_assessments"][0][
            "adjudicative_authorities"
        ] == ["AUTHORIZED_ADJUDICATION"]
        assert resolution["resolution_basis"] == [
            {
                "kind": "ADJUDICATION",
                "adjudication_id": "A1",
                "selected_commitment_id": selected,
                "adjudicative_authorities": ["AUTHORIZED_ADJUDICATION"],
                "authority_basis": [
                    {
                        "authority": "AUTHORIZED_ADJUDICATION",
                        "authority_domain": "ADJUDICATION",
                        "authority_id": "design-mobile-checkout-adjudication",
                        "authority_manifest": "adjudication-authorities.json",
                        "authority_revision": "1",
                        "source_id": "design-review-decision",
                        "source_location": "review decision: select C1",
                        "source_revision": "review-r1",
                    }
                ],
            }
        ]
        assert len(world.candidates_for("O7")) == 2
        assert len(world.adjudications()) == 1
    finally:
        world.close()

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert explorer.adjudication("A1")["selected_commitment_id"] == selected
        item = explorer.obligations()["obligations"][0]
        assert item["resolution"]["status"] == "RESOLVED"
        assert item["resolution"]["resolution_basis"][0]["adjudication_id"] == "A1"
        assert explorer.adjudication_authority()["identity"] == {
            "authority_id": "design-mobile-checkout-adjudication",
            "revision": "1",
        }
        assert explorer.adjudications() == [explorer.adjudication("A1")]

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        assert client.get("/world/adjudications").json()["adjudications"][0][
            "adjudication_id"
        ] == "A1"
        assert client.get("/world/adjudication?id=A1").json()[
            "selected_commitment_id"
        ] == selected
        assert client.get("/world/adjudication-authority").json()["identity"] == {
            "authority_id": "design-mobile-checkout-adjudication",
            "revision": "1",
        }


@pytest.mark.parametrize(
    "adjudication_record",
    [
        {
            "adjudication_id": "A-missing-obligation",
            "candidate_index": 0,
            "obligation_id": "missing-obligation",
        },
        {
            "adjudication_id": "A-missing-commitment",
            "selected_commitment_id": "assertion:not-a-commitment",
        },
        {
            "adjudication_id": "A-not-a-candidate",
            "select_orphan": True,
            "orphan_commitment": True,
        },
    ],
)
def test_adjudication_must_reference_an_existing_candidate(
    tmp_path: Path,
    adjudication_record: dict,
):
    candidate_relation = (
        "does_not_remain_available_during"
        if adjudication_record.get("orphan_commitment")
        else "remains_available_during"
    )
    root = _scenario_root(
        tmp_path,
        candidates=[
            {
                "relation": candidate_relation,
                "support": "approved_requirement",
            }
        ],
    )
    (root / "resolution-scenario.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "relation": candidate_relation,
                        "support": "approved_requirement",
                    }
                ],
                "orphan_commitment": bool(
                    adjudication_record.get("orphan_commitment")
                ),
                "adjudications": [adjudication_record],
            }
        ),
        encoding="utf-8",
    )
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
        adjudication_authority=DESIGN_ADJUDICATION_AUTHORITY,
    )
    assert not result.succeeded
    assert result.reason == "construction_error"
    assert not (root / "world").exists()


def test_adjudication_selecting_insufficient_candidate_does_not_rescue_it(
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
    (root / "resolution-scenario.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "relation": "remains_available_during",
                        "support": "approved_requirement",
                    },
                    {
                        "relation": "does_not_remain_available_during",
                        "support": "implementation",
                    },
                ],
                "adjudications": [
                    {
                        "adjudication_id": "A-weak",
                        "candidate_index": 1,
                        "source_id": "design-review-decision",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        candidate_rows = world.candidates_for("O7")
        assert resolution["status"] == "RESOLVED"
        assert resolution["selected_commitment_id"] == candidate_rows[0]
        assert resolution["resolution_basis"] == []
        assert world.adjudication("A-weak") is not None
    finally:
        world.close()


def test_competing_authorized_adjudications_remain_conflict(tmp_path: Path):
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
    (root / "resolution-scenario.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "relation": "remains_available_during",
                        "support": "approved_requirement",
                    },
                    {
                        "relation": "does_not_remain_available_during",
                        "support": "approved_requirement",
                    },
                ],
                "adjudications": [
                    {
                        "adjudication_id": "A1",
                        "candidate_index": 0,
                        "source_id": "design-review-decision",
                    },
                    {
                        "adjudication_id": "A2",
                        "candidate_index": 1,
                        "source_id": "design-review-decision",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    _result, world = _evaluate(root)
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == "CONFLICT"
        assert resolution["selected_commitment_id"] is None
        assert "competing authorized adjudications" in resolution["reason"]
        assert [item["adjudication_id"] for item in resolution[
            "adjudication_assessments"
        ]] == ["A1", "A2"]
    finally:
        world.close()


def test_removing_adjudication_authority_binding_restores_conflict(tmp_path: Path):
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
    (root / "resolution-scenario.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "relation": "remains_available_during",
                        "support": "approved_requirement",
                    },
                    {
                        "relation": "does_not_remain_available_during",
                        "support": "approved_requirement",
                    },
                ],
                "adjudications": [
                    {
                        "adjudication_id": "A1",
                        "candidate_index": 0,
                        "source_id": "design-review-decision",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _result, world = _evaluate(root)
    try:
        selected = world.resolution("O7")["selected_commitment_id"]
        assert selected is not None
    finally:
        world.close()

    manifest_path = root / "adjudication-authorities.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bindings"] = []
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    authority = load_adjudication_authority(root)
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
        adjudication_authority=authority,
    )
    assert result.succeeded, result.errors
    world = Project(root).open_world()
    try:
        resolution = world.resolution("O7")
        assert resolution["status"] == "CONFLICT"
        assert resolution["selected_commitment_id"] is None
        assert world.adjudication("A1") is not None
        assert resolution["adjudication_assessments"][0]["status"] == "INSUFFICIENT"
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
        assert selected == world.candidates_for("O7")[0]
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
        assert world.candidates_for("O7") == [commitment_id]
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
        'world.add_candidate("O7", commitment_id)',
        'world.add_candidate("missing", commitment_id)',
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
