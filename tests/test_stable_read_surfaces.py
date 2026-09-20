"""Compatibility shape of deliberately stable conceptual reads.

These tests pin semantic shape, not serialization detail or raw relation
names. Relation names, rows, and arbitrary SQL remain evolvable; see
docs/ARCHITECTURE.md section 6.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from ontology_author.world.core.model import ObligationState, ResolutionStatus
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.entry import rebuild

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    load_design_law,
    load_evidence_authority,
)

FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"


def _sealed(tmp_path: Path) -> Path:
    root = tmp_path / "stable-reads"
    shutil.copytree(FIXTURE, root)
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=load_design_law(root),
        evidence_authority=load_evidence_authority(root),
    )
    assert result.succeeded, result.errors
    return root


def _first_obligation(explorer: WorldExplorerAdapter) -> dict:
    obligations = explorer.obligations()["obligations"]
    assert obligations, "stable fixture must publish at least one obligation"
    return obligations[0]


def test_obligations_read_exposes_identity_question_and_state(tmp_path: Path):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        payload = explorer.obligations()
        assert payload["contract"] == DESIGN_CONTRACT.identity()
        for item in payload["obligations"]:
            assert item["obligation_id"]
            assert item["question"]
            assert item["state"] in {
                ObligationState.RESOLVED.value,
                ObligationState.UNRESOLVED.value,
            }
            resolution = item.get("resolution")
            assert resolution is not None
            assert resolution["status"] in {status.value for status in ResolutionStatus}
            assert resolution["reason"]


def test_selected_obligation_joins_candidates_and_context(tmp_path: Path):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        target = _first_obligation(explorer)
        detail = explorer.obligation(target["obligation_id"])
        assert detail is not None
        assert detail["obligation_id"] == target["obligation_id"]
        assert isinstance(detail["candidates"], list)
        assert "contract" in detail["context"]
        assert "evidence_authority" in detail["context"]


def test_recorded_resolution_is_historical_and_current_is_an_overlay(
    tmp_path: Path,
):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        target = _first_obligation(explorer)
        recorded = explorer.resolution(target["obligation_id"])
        assert recorded is not None
        assert recorded["status"] in {status.value for status in ResolutionStatus}
        current = explorer.current_resolution(
            target["obligation_id"], source_root=root
        )
        assert current is not None
        assert current["obligation_id"] == target["obligation_id"]
        # The overlay re-evaluates material currency; the recorded history it
        # was computed from must be unchanged afterwards.
        assert explorer.resolution(target["obligation_id"]) == recorded


def test_claim_support_separates_recorded_current_and_authority(
    tmp_path: Path,
):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        target = _first_obligation(explorer)
        recorded = explorer.resolution(target["obligation_id"])
        assessments = recorded.get("candidate_assessments") or []
        assert assessments, "stable fixture must record candidate assessments"
        commitment_id = assessments[0]["commitment_id"]
        support = explorer.claim_support(commitment_id, source_root=root)
        assert support["commitment_id"] == commitment_id
        assert "recorded" in support
        assert "current" in support
        assert "authority" in support
        if support["current"] is not None:
            assert support["current"]["status"] in {
                "PRESERVED",
                "CHANGED",
                "MISSING",
                "UNKNOWN",
            }


def test_construction_receipt_names_the_producing_constructor(tmp_path: Path):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        receipt = explorer.construction_receipt()
        assert receipt is not None
        assert str(receipt["entrypoint"]).endswith("construction.py")
        expected = "sha256:" + hashlib.sha256(
            (root / receipt["entrypoint"]).read_bytes()
        ).hexdigest()
        assert receipt["source_digest"] == expected
        assert receipt["contract_identity"] == DESIGN_CONTRACT.identity()


def test_schema_inspection_exposes_roles_types_and_mode(tmp_path: Path):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        schema = explorer.schema()
        assert schema, "stable fixture must declare relations"
        for relation in schema:
            assert relation["name"]
            assert relation["mode"] in {"BASE", "DERIVED"}
            assert relation["roles"], relation["name"]
            for role in relation["roles"]:
                assert role["name"]
                assert role["type"] in {
                    "REFERENT",
                    "TEXT",
                    "INTEGER",
                    "REAL",
                    "BOOLEAN",
                }


def test_identity_exposes_world_contract_and_authority(tmp_path: Path):
    root = _sealed(tmp_path)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        identity = explorer.identity()
        assert identity["world_id"]
        assert isinstance(identity["revision"], int)
        assert identity["contract"] == DESIGN_CONTRACT.identity()
        assert identity["governance"] is not None
        assert identity["evidence_authority"] is not None
        assert explorer.governance() is not None
        assert explorer.evidence_authority() is not None
        assert explorer.structure() is not None
