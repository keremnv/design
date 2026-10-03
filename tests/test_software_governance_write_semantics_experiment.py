"""Test-local source and publication transitions; no Design write API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.investigation import make_proposal
from ontology_author.world.runtime.world import ConstructionError
from profiles.software_governance_config_v0.build import EXPORT_ID
from profiles.software_governance_config_v0.produce import produce_routes
from tests.test_config_route_correspondence_contract_experiment import BASE, _publish, _route


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _published_snapshot(publication: Path) -> str:
    view = open_governance_world(publication)
    try:
        snapshots = {str(row["snapshot"]) for row in view.world.relation_rows("software_subject")}
        assert len(snapshots) == 1
        return snapshots.pop()
    finally:
        view.world.close()


def _source_alignment(publication: Path, source: Path) -> dict:
    """Fixture-local comparison, not a generic semantic staleness service."""
    observed = _digest(source.read_bytes())
    published = _published_snapshot(publication)
    return {
        "publication": str(publication), "published_snapshot": published,
        "observed_source_sha256": observed,
        "source_revision_matches": published == f"snapshot:{observed[:32]}",
    }


def _binding(publication: Path, route_id: str = "customer-export") -> list[str]:
    view = open_governance_world(publication)
    try:
        subjects = [str(row["subject"]) for row in view.world.relation_rows("config_route")
                    if row["record_id"] == route_id]
        assert len(subjects) == 1
        return view.propositions_for_subject(subjects[0])
    finally:
        view.world.close()


def _replace_source(source: Path, old: bytes, new: bytes, *, actor: str) -> dict:
    """One fixture-specific action result, kept outside any World."""
    before = source.read_bytes()
    receipt = {
        "method": "fixture.byte-replacement/v0", "actor": actor,
        "target": str(source), "intent": {"old": old.decode(), "new": new.decode()},
        "started_from": _digest(before), "attempted": True,
    }
    if old not in before:
        return {**receipt, "outcome": "FAILED", "error": "expected bytes absent",
                "observed_after": _digest(source.read_bytes())}
    source.write_bytes(before.replace(old, new, 1))
    observed = source.read_bytes()
    return {**receipt, "outcome": "SUCCEEDED", "observed_after": _digest(observed)}


def _same_world_bytes(publication: Path, expected: str) -> None:
    assert _digest((publication / "world.sqlite").read_bytes()) == expected


def _publication_paths(root: Path) -> list[Path]:
    # The config producer also leaves an unsealed `producer/world.sqlite`.
    # Its existence is construction state, not a sealed Design publication.
    return sorted(path.parent for path in root.rglob("world.sqlite")
                  if path.parent.name == "world")


def test_ontology_only_publication_changes_knowledge_not_source(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=False)
    original_source = source.read_bytes()
    original_world = _digest((w0 / "world.sqlite").read_bytes())
    w1, same_source = _publish(tmp_path / "w1", BASE, binding=True)
    assert source.read_bytes() == same_source.read_bytes() == original_source
    assert _published_snapshot(w0) == _published_snapshot(w1)
    assert w0 != w1 and _binding(w0) == [] and _binding(w1) == [EXPORT_ID]
    _same_world_bytes(w0, original_world)
    assert _source_alignment(w0, source)["source_revision_matches"]
    assert _source_alignment(w1, same_source)["source_revision_matches"]


def test_source_only_mutation_leaves_latest_world_about_prior_source(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    original_world = _digest((w0 / "world.sqlite").read_bytes())
    result = _replace_source(source, b"/customers/export", b"/internal/export", actor="human")
    assert result["outcome"] == "SUCCEEDED"
    assert result["started_from"] != result["observed_after"]
    assert not _source_alignment(w0, source)["source_revision_matches"]
    assert _publication_paths(tmp_path) == [w0]
    _same_world_bytes(w0, original_world)
    view = open_governance_world(w0)
    try:
        subject = next(str(row["subject"]) for row in view.world.relation_rows("config_route")
                       if row["record_id"] == "customer-export")
        manifestation = view.local_manifestation_for_subject(subject)
        assert manifestation["status"] == "OK"
        assert "/customers/export" in manifestation["content"]
    finally:
        view.world.close()


def test_source_mutation_observation_and_publication_are_separate_events(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    old = _digest((w0 / "world.sqlite").read_bytes())
    action = _replace_source(source, b"/customers/export", b"/internal/export", actor="agent")
    assert action["outcome"] == "SUCCEEDED"
    assert not _source_alignment(w0, source)["source_revision_matches"]
    observed = _digest(source.read_bytes())
    assert observed == action["observed_after"]
    changed = [_route("customer-export", "/internal/export", "CustomerExport"), BASE[1]]
    w1, source_copy = _publish(tmp_path / "w1", changed, binding=False)
    assert _digest(source_copy.read_bytes()) == observed
    assert _source_alignment(w1, source_copy)["source_revision_matches"]
    assert _binding(w0) == [EXPORT_ID] and _binding(w1) == []
    _same_world_bytes(w0, old)


def test_failed_external_attempt_does_not_publish_desired_state(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    original = source.read_bytes()
    result = _replace_source(source, b"/missing-route", b"/desired", actor="agent")
    assert result["attempted"] and result["outcome"] == "FAILED"
    assert result["started_from"] == result["observed_after"] == _digest(original)
    assert source.read_bytes() == original
    assert _source_alignment(w0, source)["source_revision_matches"]
    assert _publication_paths(tmp_path) == [w0]
    assert not (w0 / "action.json").exists()


def test_external_success_construction_failure_leaves_real_source_ahead(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    old_world = _digest((w0 / "world.sqlite").read_bytes())
    action = _replace_source(source, b'"routes": [', b'"routes": {', actor="human")
    assert action["outcome"] == "SUCCEEDED"
    with pytest.raises((ValueError, ConstructionError)):
        produce_routes(tmp_path / "failed-construction", source)
    assert not (tmp_path / "w1" / "world").exists()
    assert not _source_alignment(w0, source)["source_revision_matches"]
    assert action["observed_after"] == _digest(source.read_bytes())
    _same_world_bytes(w0, old_world)


def test_valid_candidate_not_publication_when_final_rename_fails(tmp_path, monkeypatch):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    old_world = _digest((w0 / "world.sqlite").read_bytes())
    action = _replace_source(source, b"/customers/export", b"/internal/export", actor="agent")
    assert action["outcome"] == "SUCCEEDED"
    changed = [_route("customer-export", "/internal/export", "CustomerExport"), BASE[1]]
    destination = tmp_path / "w1" / "world"
    original_rename = Path.rename
    observed_candidate = []

    def fail_final_rename(path: Path, target: Path):
        if path == destination.with_name("world.sg-work") and Path(target) == destination:
            observed_candidate.append((path / "world.sqlite").is_file())
            raise OSError("injected publication failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_final_rename)
    with pytest.raises(AssertionError, match="injected publication failure"):
        _publish(tmp_path / "w1", changed, binding=False)
    assert observed_candidate == [True]
    assert not destination.exists()
    assert not destination.with_name("world.sg-work").exists()
    assert not _source_alignment(w0, source)["source_revision_matches"]
    _same_world_bytes(w0, old_world)


def test_rejected_proposal_is_not_negative_world_knowledge(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=False)
    old_world = _digest((w0 / "world.sqlite").read_bytes())
    proposal = make_proposal(
        proposal_id="fixture:route-binding", originating_case_id="fixture:case",
        originating_question_id="fixture:question", epistemic_class="semantic",
        payload={"proposition": EXPORT_ID, "route_id": "customer-export"},
        basis={"publication": str(w0), "source_sha256": _digest(source.read_bytes())},
        method={"id": "fixture.proposal/v0"}, reason="candidate interpretation",
    )
    rejection = {"proposal_id": proposal["proposal_id"], "outcome": "REJECTED",
                 "reason": "basis not admitted"}
    assert "assertion_id" not in proposal
    assert rejection["outcome"] == "REJECTED"
    assert _binding(w0) == []
    _same_world_bytes(w0, old_world)
    assert _source_alignment(w0, source)["source_revision_matches"]


def test_source_reversion_does_not_erase_intermediate_publication(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    original = source.read_bytes()
    _replace_source(source, b"/customers/export", b"/internal/export", actor="human")
    changed = [_route("customer-export", "/internal/export", "CustomerExport"), BASE[1]]
    w1, changed_copy = _publish(tmp_path / "w1", changed, binding=False)
    w1_digest = _digest((w1 / "world.sqlite").read_bytes())
    assert changed_copy.read_bytes() == source.read_bytes()
    reverted = _replace_source(source, b"/internal/export", b"/customers/export", actor="human")
    assert reverted["outcome"] == "SUCCEEDED" and source.read_bytes() == original
    assert _source_alignment(w0, source)["source_revision_matches"]
    assert not _source_alignment(w1, source)["source_revision_matches"]
    _same_world_bytes(w1, w1_digest)
    view = open_governance_world(w1)
    try:
        subject = next(str(row["subject"]) for row in view.world.relation_rows("config_route")
                       if row["record_id"] == "customer-export")
        assert "/internal/export" in view.local_manifestation_for_subject(subject)["content"]
    finally:
        view.world.close()


def test_irrelevant_source_format_edit_does_not_force_governance_publication(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    original_routes = json.loads(source.read_bytes())["routes"]
    old_world = _digest((w0 / "world.sqlite").read_bytes())
    source.write_bytes(b"\n" + source.read_bytes())
    observed_routes = json.loads(source.read_bytes())["routes"]
    assert observed_routes == original_routes
    assert not _source_alignment(w0, source)["source_revision_matches"]
    assert _binding(w0) == [EXPORT_ID]
    assert _publication_paths(tmp_path) == [w0]
    _same_world_bytes(w0, old_world)
    # W0 remains evidence about its retained source revision. The fresh parse
    # supports a local no-modeled-route-change observation, not a W0 rewrite.


def test_partial_external_success_requires_reobserving_every_target(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    other = tmp_path / "missing-second-config.json"
    first = _replace_source(source, b"/customers/export", b"/internal/export", actor="agent")
    try:
        other.write_bytes(other.read_bytes().replace(b"old", b"new"))
    except FileNotFoundError as exc:
        second = {"target": str(other), "attempted": True, "outcome": "FAILED",
                  "error": type(exc).__name__, "observed_after": None}
    receipt = {"method": "fixture.two-file-change/v0", "outcome": "PARTIAL",
               "results": [first, second]}
    assert first["outcome"] == "SUCCEEDED" and second["outcome"] == "FAILED"
    assert receipt["outcome"] == "PARTIAL"
    assert _digest(source.read_bytes()) == first["observed_after"]
    assert not other.exists()
    assert not _source_alignment(w0, source)["source_revision_matches"]
    assert _publication_paths(tmp_path) == [w0]


def test_uninstrumented_manual_change_can_be_observed_and_reconstructed(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    prior = _digest(source.read_bytes())
    # This bypasses Design's test-local action helper entirely.
    source.write_bytes(source.read_bytes().replace(b"/customers/export", b"/manual/export", 1))
    observed = _digest(source.read_bytes())
    assert observed != prior
    assert not _source_alignment(w0, source)["source_revision_matches"]
    changed = [_route("customer-export", "/manual/export", "CustomerExport"), BASE[1]]
    w1, copied_source = _publish(tmp_path / "w1", changed, binding=False)
    assert _digest(copied_source.read_bytes()) == observed
    assert _source_alignment(w1, copied_source)["source_revision_matches"]
    assert _binding(w0) == [EXPORT_ID] and _binding(w1) == []


def test_reported_action_success_without_result_observation_is_not_source_evidence(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=False)
    current = _digest(source.read_bytes())
    declared = {"target": str(source), "outcome": "SUCCEEDED",
                "desired_path": "/not-actually-written", "observed_after": None}
    assert declared["outcome"] == "SUCCEEDED"
    assert declared["observed_after"] is None
    assert _digest(source.read_bytes()) == current
    assert b"/not-actually-written" not in source.read_bytes()
    assert _publication_paths(tmp_path) == [w0]


@pytest.mark.parametrize("actor", ["human", "agent"])
def test_manual_and_agent_edits_have_same_evidence_requirement(tmp_path, actor):
    w0, source = _publish(tmp_path / "w0", BASE, binding=False)
    result = _replace_source(source, b"/customers/export", b"/internal/export", actor=actor)
    assert result["actor"] == actor and result["outcome"] == "SUCCEEDED"
    assert not _source_alignment(w0, source)["source_revision_matches"]
    assert result["observed_after"] == _digest(source.read_bytes())
    assert _binding(w0) == []


def test_publication_can_become_source_misaligned_immediately(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    first = _replace_source(source, b"/customers/export", b"/internal/export", actor="human")
    assert first["outcome"] == "SUCCEEDED"
    changed = [_route("customer-export", "/internal/export", "CustomerExport"), BASE[1]]
    w1, source_copy = _publish(tmp_path / "w1", changed, binding=False)
    assert _source_alignment(w1, source_copy)["source_revision_matches"]
    second = _replace_source(source_copy, b"/internal/export", b"/other/export", actor="human")
    assert second["outcome"] == "SUCCEEDED"
    assert not _source_alignment(w1, source_copy)["source_revision_matches"]
    assert _binding(w0) == [EXPORT_ID] and _binding(w1) == []
