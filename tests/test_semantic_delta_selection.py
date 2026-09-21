"""Delta-driven selection of persisted semantic commitments.

A sealed World plus a ProgramDelta comparison selects exactly those
persisted semantic commitments whose recorded maintenance basis is no
longer preserved. No authority attachment, case, model call, search, or
verdict is involved; the sealed World is never mutated.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from experiments import run_payment_semantic_persistence_experiment as payment
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.program_spine import compare_program_spines
from ontology_author.semantic_binding import (
    PROGRAM_RELATIONSHIP_RELATION,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
    maintain_semantic_commitment,
    materialize_semantic_commitment_revision,
    select_affected_semantic_commitments,
)
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import _spine

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "node_modules"
        / "typescript"
    ).exists(),
    reason="the TypeScript compiler API dependency is not installed",
)

_VERDICT_TOKENS = ("violat", "broken", "noncompliant", "unauthorized")


@pytest.fixture(scope="module")
def selection_worlds(tmp_path_factory):
    scratch = tmp_path_factory.mktemp("delta-selection")
    old, new, comparison, _maintenance, _impact, case, endpoints, relations = (
        payment._setup(scratch)
    )
    try:
        old_snapshot = snapshot_id(old)
        source = payment._bounded_source(
            old, endpoints, endpoints["checkout_entry"], old_snapshot
        )
        dependencies = payment._payment_dependencies(endpoints, relations)
        catalog = build_semantic_construction_catalog(
            payment._obligation(case, endpoints),
            case,
            bounded_program_source=source,
            maintenance_dependencies=dependencies,
            program_endpoint_kinds=payment._program_endpoint_kinds(old),
        )
        obligation = payment._obligation(case, endpoints)

        def _persist(target_name: str, aliases: list[str] | None):
            draft = payment._draft(
                obligation,
                catalog,
                endpoints,
                relations,
                dependencies=aliases,
            )
            candidate = compile_semantic_candidate_draft(
                obligation,
                catalog,
                draft,
                construction_method="deterministic selection control",
            )
            decision = admit_semantic_candidate(
                obligation, candidate, catalog, snapshot_id=snapshot_id(old)
            )
            assert decision.outcome == "PERSIST_COMMITMENT"
            return materialize_semantic_commitment_revision(
                old,
                scratch / target_name,
                obligation,
                candidate,
                decision,
                catalog,
                snapshot_id=snapshot_id(old),
            )

        full = _persist("g1-full", None)
        tuple_aliases = [
            str(item["alias"])
            for item in catalog["entries"]
            if item.get("category") == "MAINTENANCE_DEPENDENCY"
            and (item.get("dependency") or {}).get("kind") == "relation_tuple"
        ]
        assert tuple_aliases, "catalog must declare relation_tuple dependencies"
        tuples_only = _persist("g1-tuples", tuple_aliases)

        unrelated_files = dict(payment.PAYMENT_S0)
        unrelated_files["src/unrelated.ts"] = (
            "export function helper(): number { return 41; }\n"
        )
        _spine(scratch, unrelated_files, "unrelated-spine")
        unrelated = compare_program_spines(
            scratch / "baseline-spine", scratch / "unrelated-spine"
        )
        empty = compare_program_spines(
            scratch / "baseline-spine", scratch / "baseline-spine"
        )
        moved_files = dict(payment.PAYMENT_S0)
        moved_files["src/payment-gateway.ts"] = (
            "import { throughGateway } from './payment-service';\n"
        )
        moved_files["src/payment-service.ts"] = (
            payment.PAYMENT_S0["src/payment-service.ts"]
            + "\nexport function throughGateway(amount: number): string "
            + "{ return 'gateway:' + amount; }\n"
        )
        _spine(scratch, moved_files, "moved-spine")
        moved = compare_program_spines(
            scratch / "baseline-spine", scratch / "moved-spine"
        )
        g1_full = ConstructionWorld.open(
            scratch / "g1-full" / "world.sqlite", read_only=True
        )
        g1_tuples = ConstructionWorld.open(
            scratch / "g1-tuples" / "world.sqlite", read_only=True
        )
        yield {
            "endpoints": endpoints,
            "comparison": comparison,
            "unrelated": unrelated,
            "empty": empty,
            "moved": moved,
            "g1_full": g1_full,
            "g1_tuples": g1_tuples,
            "full_warrant": full["warrant"],
            "tuples_warrant": tuples_only["warrant"],
            "old_snapshot": old_snapshot,
        }
    finally:
        old.close()
        new.close()


@pytest.fixture
def worlds(selection_worlds):
    yield selection_worlds


def _assert_no_verdict_language(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    for token in _VERDICT_TOKENS:
        assert token not in text, f"manufactured verdict language: {token}"


def test_retarget_surfaces_persisted_commitment(worlds):
    before = worlds["g1_full"].path.read_bytes()
    selection = select_affected_semantic_commitments(
        worlds["g1_full"], worlds["comparison"]
    )
    assert worlds["g1_full"].path.read_bytes() == before
    assert selection["schema"] == "semantic_delta_selection/v0"
    assert selection["warrants_considered"] == 1
    assert (
        selection["comparison_id"] == worlds["comparison"].receipt.comparison_id
    )
    assert len(selection["selected"]) == 1
    entry = selection["selected"][0]
    assert entry["relation_name"] == PROGRAM_RELATIONSHIP_RELATION
    assert entry["tuple"]["checkout_entry"] == worlds["endpoints"]["checkout_entry"]
    assert entry["tuple"]["service"] == worlds["endpoints"]["service"]
    assert entry["tuple"]["gateway"] == worlds["endpoints"]["gateway"]
    assert entry["tuple"]["provider"] == worlds["endpoints"]["provider"]
    assert entry["snapshot_id"] == worlds["old_snapshot"]
    assert entry["warrant"]["obligation_id"]
    assert entry["warrant"]["admission_decision_id"]
    assert entry["warrant"]["assertion_id"] == entry["assertion_id"]
    assert entry["observations"], "inspectable grounding must be attached"
    for observation in entry["observations"]:
        assert observation["provider"]
        assert observation["native_handle"]
        assert observation["source_revision"]
        assert observation["native_location"]

    maintenance = entry["maintenance"]
    assert maintenance["status"] == "CHANGED"
    assert maintenance["model_invoked"] is False
    assert maintenance["transferred"] is False
    changed = [
        item
        for item in maintenance["assessments"]
        if item["status"] == "CHANGED"
    ]
    retargeted = [
        item
        for item in changed
        if item["dependency"].get("kind") == "relation_tuple"
        and item["evidence"].get("bucket") == "retargeted"
    ]
    assert retargeted, "exact changed program_invokes dependency must surface"
    assert retargeted[0]["evidence"]["evidence"].get("old")
    assert retargeted[0]["evidence"]["evidence"].get("new")
    # No transfer: the selected tuple is exactly the persisted historical row.
    persisted = worlds["g1_full"].relation_rows(PROGRAM_RELATIONSHIP_RELATION)
    assert len(persisted) == 1
    assert entry["tuple"] == persisted[0]
    _assert_no_verdict_language(selection)


def test_unrelated_change_preserves_full_commitment(worlds):
    direct = maintain_semantic_commitment(
        worlds["full_warrant"], worlds["unrelated"]
    )
    assert direct["status"] == "PRESERVED"
    selection = select_affected_semantic_commitments(
        worlds["g1_full"], worlds["unrelated"]
    )
    assert selection["warrants_considered"] == 1
    assert selection["selected"] == []
    assert (
        select_affected_semantic_commitments(worlds["g1_full"], worlds["empty"])[
            "selected"
        ]
        == []
    )

    # Non-vacuity: the unrelated delta is real (added entities exist), the
    # tuple-only warrant behaves the same way, and it still selects under
    # the retargeting delta.
    assert worlds["unrelated"].delta.identity.get("added")
    tuples_selection = select_affected_semantic_commitments(
        worlds["g1_tuples"], worlds["unrelated"]
    )
    assert tuples_selection["selected"] == []
    tuples_under_retarget = select_affected_semantic_commitments(
        worlds["g1_tuples"], worlds["comparison"]
    )
    assert len(tuples_under_retarget["selected"]) == 1
    assert tuples_under_retarget["selected"][0]["maintenance"]["status"] == (
        "CHANGED"
    )


def test_unresolved_move_surfaces_not_comparable_without_verdict(worlds):
    selection = select_affected_semantic_commitments(
        worlds["g1_full"], worlds["moved"]
    )
    assert selection["warrants_considered"] == 1
    assert len(selection["selected"]) == 1
    entry = selection["selected"][0]
    maintenance = entry["maintenance"]
    assert maintenance["status"] == "NOT_COMPARABLE"
    assert maintenance["model_invoked"] is False
    assert maintenance["transferred"] is False
    gateway = worlds["endpoints"]["gateway"]
    identity = [
        item
        for item in maintenance["assessments"]
        if item["dependency"].get("kind") == "program_identity"
        and item["dependency"].get("program_entity") == gateway
    ]
    assert len(identity) == 1
    assert identity[0]["status"] == "NOT_COMPARABLE"
    assert "unresolved" in str(identity[0]["evidence"])
    assert entry["tuple"]["gateway"] == gateway
    assert entry["warrant"]["assertion_id"] == entry["assertion_id"]
    _assert_no_verdict_language(selection)


def test_selection_leaves_sealed_world_unchanged(worlds):
    path = worlds["g1_full"].path
    before = path.read_bytes()
    select_affected_semantic_commitments(worlds["g1_full"], worlds["comparison"])
    select_affected_semantic_commitments(worlds["g1_full"], worlds["unrelated"])
    select_affected_semantic_commitments(worlds["g1_full"], worlds["empty"])
    assert path.read_bytes() == before
