"""Executable construction-adequacy contract for design_checkout.

These tests are the application adequacy boundary. They do not freeze relation
names, row sets, or constructor internals. PURPOSE.md is not a correctness
oracle.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ontology_author.world.core.model import ObligationState, ResolutionStatus
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.construction_receipt import (
    RECEIPT_SCHEMA,
    constructor_matches_receipt,
    constructor_source_digest,
)
from ontology_author.world.runtime.entry import rebuild
from ontology_author.world.server import build_app

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    extract_frontend_structure,
    load_design_law,
    load_evidence_authority,
)


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"

UNRESOLVED_STATUSES = {
    ResolutionStatus.INSUFFICIENT_WARRANT.value,
    ResolutionStatus.NO_CANDIDATE.value,
    ResolutionStatus.CONFLICT.value,
    ResolutionStatus.AMBIGUOUS.value,
}


def _copy_fixture(tmp_path: Path, name: str = "checkout-adequacy") -> Path:
    root = tmp_path / name
    shutil.copytree(FIXTURE, root)
    return root


def _rebuild(root: Path, *, evidence_authority=None):
    law = load_design_law(root)
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=law,
        evidence_authority=evidence_authority or load_evidence_authority(root),
    )
    assert result.succeeded, result.errors
    return law


def _generated_obligations(root: Path):
    law = load_design_law(root)
    structure = extract_frontend_structure(
        (root / "Checkout.tsx").read_text(encoding="utf-8")
    )
    return law.enumerate_obligations(structure)


def _accounted_obligations(explorer: WorldExplorerAdapter) -> dict[str, dict]:
    return {
        item["obligation_id"]: item for item in explorer.obligations()["obligations"]
    }


def assert_world_accounts_for_generated_obligations(
    root: Path, explorer: WorldExplorerAdapter
) -> None:
    generated = _generated_obligations(root)
    sealed = _accounted_obligations(explorer)
    generated_ids = {item.obligation_id for item in generated}
    sealed_ids = set(sealed)
    assert sealed_ids == generated_ids
    for obligation in generated:
        item = sealed[obligation.obligation_id]
        assert item["question"]
        assert item["state"] in {
            ObligationState.RESOLVED.value,
            ObligationState.UNRESOLVED.value,
        }
        resolution = item.get("resolution")
        assert resolution, obligation.obligation_id
        status = resolution["status"]
        if item["state"] == ObligationState.RESOLVED.value:
            assert status == ResolutionStatus.RESOLVED.value
            assert resolution["selected_commitment_id"]
        else:
            assert status in UNRESOLVED_STATUSES
            assert resolution["reason"]
            assert resolution.get("selected_commitment_id") in (None, "")


def test_every_applicable_governed_question_is_accounted_for(tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert_world_accounts_for_generated_obligations(root, explorer)
        generated = _generated_obligations(root)
        sealed = _accounted_obligations(explorer)
        assert {item.dimension for item in generated} == {
            "availability",
            "priority",
            "goal_support",
        }
        by_dimension = {
            item.dimension: sealed[item.obligation_id] for item in generated
        }
        assert by_dimension["availability"]["state"] == ObligationState.RESOLVED.value
        assert by_dimension["priority"]["state"] == ObligationState.UNRESOLVED.value
        assert by_dimension["goal_support"]["state"] == ObligationState.UNRESOLVED.value


def test_resolved_question_exposes_selected_commitment_and_basis(tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        generated = next(
            item
            for item in _generated_obligations(root)
            if item.dimension == "availability"
        )
        detail = explorer.obligation(generated.obligation_id)
        assert detail["state"] == ObligationState.RESOLVED.value
        selected = detail["resolution"]["selected_commitment_id"]
        assert selected
        candidate = next(
            item for item in detail["candidates"] if item["commitment_id"] == selected
        )
        assert candidate["assessment"]["status"] == "SUFFICIENT"
        assert candidate["warrant"]["bases"]
        commitment = explorer.assertion(selected)
        assert commitment["commitment_id"] == selected
        assert generated.obligation_id in commitment["governing_obligations"]


def test_insufficient_warrant_remains_explicitly_unresolved(tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        unresolved = [
            item
            for item in explorer.obligations()["obligations"]
            if item["state"] == ObligationState.UNRESOLVED.value
        ]
        assert unresolved
        for item in unresolved:
            assert item["resolution"]["status"] == (
                ResolutionStatus.INSUFFICIENT_WARRANT.value
            )
            assert item["resolution"]["reason"]
            assert not item["resolution"]["selected_commitment_id"]
            detail = explorer.obligation(item["obligation_id"])
            assert detail["candidates"]
            assert all(
                candidate["assessment"]["status"] == "INSUFFICIENT"
                for candidate in detail["candidates"]
            )


def test_agent_can_navigate_question_to_candidate_to_grounding(tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        question = explorer.obligations()["obligations"][0]
        detail = explorer.obligation(question["obligation_id"])
        candidate = detail["candidates"][0]
        assertion = explorer.assertion(candidate["commitment_id"])
        assert assertion["grounding"]
        assert assertion["warrant"]["bases"]
        kinds = {base["kind"] for base in assertion["warrant"]["bases"]}
        assert "SOURCE" in kinds
        assert assertion["origin"] in {"MECHANICAL", "SEMANTIC"}


def test_no_applicable_question_silently_disappears(tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        generated_ids = {item.obligation_id for item in _generated_obligations(root)}
        sealed_ids = set(_accounted_obligations(explorer))
        assert generated_ids == sealed_ids


def test_adequate_world_may_leave_priority_and_goal_support_unresolved(tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert_world_accounts_for_generated_obligations(root, explorer)
        overview = explorer.overview()["governed_obligations"]
        assert overview["count"] == 3
        assert overview["resolved"] == 1
        assert overview["unresolved"] == 2


def test_removing_approved_requirement_authority_unresolves_availability(tmp_path: Path):
    root = _copy_fixture(tmp_path, "authority-change")
    _rebuild(root)
    generated_before = _generated_obligations(root)
    availability_id = next(
        item.obligation_id
        for item in generated_before
        if item.dimension == "availability"
    )
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        before = explorer.obligation(availability_id)
        assert before["state"] == ObligationState.RESOLVED.value
        selected = before["resolution"]["selected_commitment_id"]

    manifest = json.loads((root / "evidence-authorities.json").read_text(encoding="utf-8"))
    manifest["bindings"] = [
        item
        for item in manifest["bindings"]
        if item["authority"] != "APPROVED_REQUIREMENT"
    ]
    (root / "evidence-authorities.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    _rebuild(root)
    generated_after = _generated_obligations(root)
    assert {item.obligation_id for item in generated_after} == {
        item.obligation_id for item in generated_before
    }
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert_world_accounts_for_generated_obligations(root, explorer)
        after = explorer.obligation(availability_id)
        assert after["state"] == ObligationState.UNRESOLVED.value
        assert after["resolution"]["status"] == (
            ResolutionStatus.INSUFFICIENT_WARRANT.value
        )
        assert after["resolution"]["reason"]
        candidates = {item["commitment_id"] for item in after["candidates"]}
        assert selected in candidates
        assert after["resolution"]["selected_commitment_id"] in (None, "")


def test_removing_governed_structure_changes_the_question_set(tmp_path: Path):
    root = _copy_fixture(tmp_path, "structure-change")
    _rebuild(root)
    before = {item.obligation_id: item.dimension for item in _generated_obligations(root)}
    assert set(before.values()) == {"availability", "priority", "goal_support"}
    checkout = (root / "Checkout.tsx").read_text(encoding="utf-8")
    (root / "Checkout.tsx").write_text(
        checkout.replace('data-region="order-summary"', 'data-region="order-details"'),
        encoding="utf-8",
    )
    _rebuild(root)
    after = {item.obligation_id: item.dimension for item in _generated_obligations(root)}
    assert set(after.values()) == {"priority"}
    dropped = set(before) - set(after)
    assert dropped
    assert {before[item_id] for item_id in dropped} == {"availability", "goal_support"}
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert_world_accounts_for_generated_obligations(root, explorer)
        sealed = _accounted_obligations(explorer)
        assert set(sealed) == set(after)
        for obligation_id in dropped:
            assert obligation_id not in sealed


def test_purpose_prose_is_not_the_adequacy_oracle(tmp_path: Path):
    root = _copy_fixture(tmp_path, "no-purpose")
    (root / "PURPOSE.md").write_text(
        "# Purpose\n\nThis wording is deliberately false and must not decide adequacy.\n",
        encoding="utf-8",
    )
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert_world_accounts_for_generated_obligations(root, explorer)
        assert explorer.demand() is None
        assert (root / "PURPOSE.md").read_text(encoding="utf-8").startswith("# Purpose")


def test_fresh_agent_can_inspect_questions_resolutions_and_provenance(tmp_path: Path):
    root = _copy_fixture(tmp_path, "inspection")
    law = _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        governed = explorer.obligations()["obligations"]
        assert governed
        assert explorer.governance()["identity"] == law.identity()
        for item in governed:
            detail = explorer.obligation(item["obligation_id"])
            assert detail["question"]
            assert detail["generated_by_rule"]
            assert detail["law_provenance"]["source_id"]
            assert detail["structural_bindings"]
            assert detail["candidates"]
            if detail["state"] == ObligationState.RESOLVED.value:
                selected = explorer.assertion(
                    detail["resolution"]["selected_commitment_id"]
                )
                assert selected["warrant"]["recorded_construction_origin"]
                assert selected["warrant"]["bases"]
            else:
                assert detail["resolution"]["reason"]
        receipt = explorer.construction_receipt()
        assert receipt is not None
        assert receipt["contract"] == RECEIPT_SCHEMA
        assert constructor_matches_receipt(root / "construction.py", receipt)

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        assert client.get("/world/construction-receipt").json()["source_digest"] == (
            constructor_source_digest(root / "construction.py")
        )
        payload = client.get("/world/obligations").json()
        assert {item["obligation_id"] for item in payload["obligations"]} == {
            item.obligation_id for item in _generated_obligations(root)
        }


def test_construction_receipt_detects_unchecked_constructor_change(tmp_path: Path):
    root = _copy_fixture(tmp_path, "receipt-mismatch")
    _rebuild(root)
    producing = constructor_source_digest(root / "construction.py")
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        receipt = explorer.construction_receipt()
        assert receipt["source_digest"] == producing
        assert constructor_matches_receipt(root / "construction.py", receipt)

    original = (root / "construction.py").read_text(encoding="utf-8")
    (root / "construction.py").write_text(
        original + "\n# constructor revision Y\n", encoding="utf-8"
    )
    current = constructor_source_digest(root / "construction.py")
    assert current != producing
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        receipt = explorer.construction_receipt()
        assert receipt["source_digest"] == producing
        assert not constructor_matches_receipt(root / "construction.py", receipt)
        assert explorer.identity()["construction_receipt"]["source_digest"] == producing

    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        rebuilt = explorer.construction_receipt()
        assert rebuilt["source_digest"] == current
        assert constructor_matches_receipt(root / "construction.py", rebuilt)
        assert rebuilt["entrypoint"] == "construction.py"
        assert rebuilt["runtime_world_id"] == "v0"
        assert rebuilt["contract_identity"] == DESIGN_CONTRACT.identity()
