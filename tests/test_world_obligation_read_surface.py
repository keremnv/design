from __future__ import annotations

import shutil
from pathlib import Path

from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.entry import rebuild
from ontology_author.world.server import build_app
from profiles.design_checkout import (
    DESIGN_ADJUDICATION_AUTHORITY,
    DESIGN_CONTRACT,
    DESIGN_EVIDENCE_AUTHORITY,
    DESIGN_LAW,
)


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"


def _checkout_world(tmp_path: Path, *, include_purpose: bool = True) -> Path:
    root = tmp_path / "checkout-world"
    shutil.copytree(FIXTURE, root)
    if not include_purpose:
        (root / "PURPOSE.md").unlink()
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
        adjudication_authority=DESIGN_ADJUDICATION_AUTHORITY,
    )
    assert result.succeeded, result.errors
    return root


def _obligation_id(explorer: WorldExplorerAdapter, dimension: str) -> str:
    return next(
        item["obligation_id"]
        for item in explorer.obligations()["obligations"]
        if item.get("dimension") == dimension
    )


def test_selected_obligation_read_joins_question_candidates_and_authority(tmp_path: Path):
    root = _checkout_world(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _obligation_id(explorer, "availability")
        detail = explorer.obligation(obligation_id)
        assert detail is not None
        assert detail["obligation_id"] == obligation_id
        assert detail["generated_by_rule"].startswith(
            "rule:checkout_design_governance:availability"
        )
        assert detail["law_provenance"]["source_id"] == "checkout-design-governance"
        assert detail["structural_bindings"] == {
            "activity": "payment_entry",
            "context": "mobile_checkout",
            "subject": "order_summary",
        }
        assert detail["context"] == {
            "contract": {
                "contract_id": "design-mobile-checkout",
                "contract_revision": "1",
            },
            "governance": {
                "law_id": "design-mobile-checkout-law",
                "revision": DESIGN_LAW.revision,
            },
            "evidence_authority": {
                "authority_id": "design-mobile-checkout-evidence",
                "revision": "1",
            },
            "adjudication_authority": {
                "authority_id": "design-mobile-checkout-adjudication",
                "revision": "1",
            },
        }

        candidate = detail["candidates"][0]
        assert candidate["commitment"]["relation"] == "remains_available_during"
        assert candidate["commitment"]["values"] == {
            "subject": "order_summary",
            "activity": "payment_entry",
            "context": "mobile_checkout",
        }
        assert candidate["warrant"]["bases"]
        assert candidate["assessment"]["status"] == "SUFFICIENT"
        assert candidate["assessment"]["warrant_authorities"] == [
            "APPROVED_REQUIREMENT",
            "IMPLEMENTATION_OBSERVATION",
        ]
        assert candidate["governing"] is True
        assert detail["resolution"]["status"] == "RESOLVED"
        assert detail["resolution"]["selected_commitment_id"] == candidate[
            "commitment_id"
        ]

        commitment = explorer.assertion(candidate["commitment_id"])
        assert commitment["candidate_for"] == [obligation_id]
        assert commitment["governing_obligations"] == [obligation_id]
        assert commitment["candidate_assessments"][0]["status"] == "SUFFICIENT"


def test_selected_obligation_route_is_one_read_plane_aggregate(tmp_path: Path):
    root = _checkout_world(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _obligation_id(explorer, "priority")

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        response = client.get(
            "/world/obligation", params={"obligation_id": obligation_id}
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["obligation_id"] == obligation_id
        assert payload["candidates"][0]["assessment"]["status"] == (
            "INSUFFICIENT"
        )
        assert payload["resolution"]["status"] == "INSUFFICIENT_WARRANT"


def test_selected_obligation_read_preserves_conflict_and_adjudication_basis(
    tmp_path: Path,
):
    root = _checkout_world(tmp_path)
    (root / "construction.py").write_text(
        '''def construct(source, world, purpose):
    for referent in ("order_summary", "payment_entry", "mobile_checkout"):
        world.add_referent(referent)
    world.add_obligation("O7", question="What availability relationship should hold?")
    roles = [
        Role("subject", RoleType.REFERENT),
        Role("activity", RoleType.REFERENT),
        Role("context", RoleType.REFERENT),
    ]
    for relation in ("remains_available_during", "does_not_remain_available_during"):
        world.declare_relation(relation, roles, scope="WORLD")
    observation = SourceObservation(
        provider="file",
        native_handle="checkout-requirements.md",
        source_revision=source.file_hash("checkout-requirements.md"),
        native_location="availability decision",
    )
    values = {
        "subject": "order_summary",
        "activity": "payment_entry",
        "context": "mobile_checkout",
    }
    commitments = []
    for relation in ("remains_available_during", "does_not_remain_available_during"):
        commitment = world.assert_tuple(
            relation,
            values,
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(observation,),
                construction_method="conflict inspection fixture",
            ),
        )
        commitments.append(commitment.assertion_id)
    for commitment_id in commitments:
        world.add_candidate("O7", commitment_id)
    world.add_adjudication(
        adjudication_id="A1",
        obligation_id="O7",
        selected_commitment_id=commitments[0],
        authority_basis={
            "source_id": "design-review-decision",
            "source_revision": "review-r1",
            "source_location": "select first availability answer",
        },
    )
''',
        encoding="utf-8",
    )
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
        adjudication_authority=DESIGN_ADJUDICATION_AUTHORITY,
    )
    assert result.succeeded, result.errors

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        detail = explorer.obligation("O7")
        assert detail is not None
        assert [item["assessment"]["status"] for item in detail["candidates"]] == [
            "SUFFICIENT",
            "SUFFICIENT",
        ]
        assert detail["resolution"]["status"] == "RESOLVED"
        assert detail["resolution"]["resolution_basis"][0]["adjudication_id"] == "A1"
        assert detail["adjudications"][0]["record"]["selected_commitment_id"] == (
            detail["resolution"]["selected_commitment_id"]
        )
        assert detail["adjudications"][0]["assessment"]["status"] == "SUFFICIENT"


def _mixed_world(tmp_path: Path) -> Path:
    root = tmp_path / "mixed-world"
    root.mkdir()
    (root / "PURPOSE.md").write_text(
        "# Purpose\n\nKeep the legacy task expectation visible.\n",
        encoding="utf-8",
    )
    (root / "construction.py").write_text(
        '''def construct(source, world, purpose):
    purpose.unresolved(
        "legacy.missing-fact",
        subject={"subject": "thing"},
        relation="legacy_fact",
        reason="the legacy Purpose requirement remains open",
    )
    world.add_obligation(
        "O7",
        question="What governed question remains open?",
    )
''',
        encoding="utf-8",
    )
    result = rebuild(root, purpose=root / "PURPOSE.md")
    assert result.succeeded, result.errors
    return root


def test_demand_and_governed_obligation_reads_are_disjoint(tmp_path: Path):
    root = _mixed_world(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        demand = explorer.demand()
        assert demand is not None
        assert demand["demanded"] == 1
        assert len(demand["obligations"]) == 1
        assert "contract" not in demand
        assert "obligation_id" not in demand["obligations"][0]
        assert demand["obligations"][0]["demanded_by"]["kind"] == "requirement"

        governed = explorer.obligations()
        assert "purpose" not in governed
        assert governed["obligations"] == [
            {
                "obligation_id": "O7",
                "question": "What governed question remains open?",
                "relation": None,
                "values": {},
                "reason": None,
                "demanded_by": {
                    "kind": "contract",
                    "name": "O7",
                    "contract_id": "ontology-author-default",
                    "contract_revision": "1",
                },
                "state": "UNRESOLVED",
                "assertion_id": None,
                "record_id": None,
                "grounding_ref": None,
                "contract_id": "ontology-author-default",
                "contract_revision": "1",
                "candidates": [],
            }
        ]

        overview = explorer.overview()
        assert overview["demand"]["obligations"] == 1
        assert overview["governed_obligations"] == {
            "count": 1,
            "resolved": 0,
            "unresolved": 1,
        }

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        legacy_payload = client.get("/world/demand").json()
        assert len(legacy_payload["demand"]["obligations"]) == 1
        assert "obligation_id" not in legacy_payload["demand"]["obligations"][0]
        governed_payload = client.get("/world/obligations").json()
        assert [item["obligation_id"] for item in governed_payload["obligations"]] == [
            "O7"
        ]


def test_governed_obligations_are_read_without_a_loaded_purpose(tmp_path: Path):
    root = _checkout_world(tmp_path, include_purpose=False)

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert explorer.demand() is None
        assert len(explorer.obligations()["obligations"]) == 3
        assert explorer.overview()["demand"] is None
        assert explorer.overview()["governed_obligations"] == {
            "count": 3,
            "resolved": 1,
            "unresolved": 2,
        }

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        assert client.get("/world/demand").json()["demand"] is None
        governed = client.get("/world/obligations").json()["obligations"]
        assert len(governed) == 3
        detail = client.get(
            "/world/obligation",
            params={"obligation_id": governed[0]["obligation_id"]},
        )
        assert detail.status_code == 200
        assert detail.json()["obligation_id"] == governed[0]["obligation_id"]


def test_frontend_read_types_do_not_use_a_mixed_demand_discriminator():
    api = (Path(__file__).parents[1] / "frontend" / "src" / "api" / "world.ts").read_text(
        encoding="utf-8"
    )
    frontier = (Path(__file__).parents[1] / "frontend" / "src" / "world" / "FrontierTable.tsx").read_text(
        encoding="utf-8"
    )
    page = (Path(__file__).parents[1] / "frontend" / "src" / "world" / "WorldPage.tsx").read_text(
        encoding="utf-8"
    )
    assert "obligations: LegacyWorldObligation[];" in api
    assert "(LegacyWorldObligation | WorldObligation)[]" not in api
    assert "isWorldObligation" not in frontier
    assert "isWorldObligation" not in page
