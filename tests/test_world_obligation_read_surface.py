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


def _checkout_world(tmp_path: Path) -> Path:
    root = tmp_path / "checkout-world"
    shutil.copytree(FIXTURE, root)
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
        for item in explorer.demand()["obligations"]
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
