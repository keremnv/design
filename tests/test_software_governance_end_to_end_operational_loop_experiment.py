"""Test-local end-to-end operational loop: request to sealed publication.

One bounded config change request drives a capability invocation, an
independent observation, exact-revision Construction intake, and a fresh
sealed World. Each stage stays distinct: requested state never outranks
observed state, and publication truth never claims current alignment.
Nothing here changes OA Core, accepted Construction semantics, Decision,
Action, authorization, renewal, or any production package.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ontology_author.software_governance import (
    BindingSpec,
    CompletenessSpec,
    GovernanceConstructionResult,
    ManifestationSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
    open_governance_world,
)
from ontology_author.software_governance.evidence import reconstruct_governance_observation
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from profiles.software_governance_config_v0.build import (
    EXPORT,
    EXPORT_ID,
    GOVERNANCE,
    PROFILE_ID,
    SOFTWARE_EVIDENCE,
    _excerpt,
)
from profiles.software_governance_config_v0.produce import (
    CAPABILITY,
    KIND,
    SCHEME,
    VERSION,
    ProducedRoutes,
)
from tests.test_config_route_correspondence_contract_experiment import BASE, _publish
from tests.test_software_governance_construction_intake_integrity_experiment import (
    _install_read_hook,
    _live_current_construct,
)
from tests.test_software_governance_execution_observation_handoff_experiment import (
    _feedback,
    _handoff,
    _invoke,
    _observe,
    _request,
    _set_path_uninstrumented,
    _sha,
)


def _seal_from_produced(root: Path, staging: Path, produced: ProducedRoutes, *,
                        binding: bool = False,
                        binding_subject: str | None = None) -> GovernanceConstructionResult:
    """Governance Construction plus fresh-address publication; result returned."""
    root.mkdir(parents=True, exist_ok=True)
    blobs = dict(produced.blobs)
    evidence = _excerpt(GOVERNANCE, EXPORT, blobs)
    export = next(item for item in produced.routes if item.route_id == "customer-export")
    bindings = (
        (BindingSpec(
            proposition_id=EXPORT_ID,
            software_subject=binding_subject or export.subject_id,
            support="SOURCE_EXPLICIT", endpoint_resolution="DETERMINISTIC",
            construction_method="end-to-end fixture binding",
            observations=(evidence,), software_evidence=SOFTWARE_EVIDENCE,
        ),) if binding else ()
    )
    return construct_software_governance(
        software_world=staging, output=root / "world", profile_id=PROFILE_ID,
        evidence_blobs=blobs,
        propositions=(PropositionSpec(
            proposition_id=EXPORT_ID, statement=EXPORT,
            domain_relation="customer_export_route", observations=(evidence,),
        ),),
        bindings=bindings,
        subjects=tuple(
            SoftwareSubjectSpec(
                subject_id=item.subject_id, snapshot_id=produced.snapshot_id,
                kind=KIND, capability=CAPABILITY, version=VERSION,
                observations=(item.document_observation,),
            ) for item in produced.routes
        ),
        manifestations=tuple(
            ManifestationSpec(
                subject_id=item.subject_id, scheme=SCHEME, location=item.location,
                capability=f"{CAPABILITY}/{VERSION}",
                observations=(item.manifestation_observation,),
            ) for item in produced.routes
        ),
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY, status="INCOMPLETE",
            universe=produced.snapshot_id,
            basis="only end-to-end loop correspondences are recorded",
            known_gaps=("loop_probe_only",),
        ),
    )


def _route_fact(publication: Path, route_id: str) -> dict:
    view = open_governance_world(publication)
    try:
        rows = [dict(row) for row in view.world.relation_rows("config_route")
                if row["record_id"] == route_id]
        assert len(rows) == 1
        return rows[0]
    finally:
        view.world.close()


def _published_snapshot(publication: Path) -> str:
    view = open_governance_world(publication)
    try:
        snapshots = {str(row["snapshot"])
                     for row in view.world.relation_rows("software_subject")}
        assert len(snapshots) == 1
        return snapshots.pop()
    finally:
        view.world.close()


def _bindings(publication: Path) -> list[dict]:
    view = open_governance_world(publication)
    try:
        return [dict(row) for row in view.world.relation_rows("governance_binding")]
    finally:
        view.world.close()


def _sealed_bytes(publication: Path) -> bytes:
    return (publication / "world.sqlite").read_bytes()


def _sealed_publications(root: Path) -> list[Path]:
    """Sealed publication dirs only; producer staging is construction state."""
    return sorted(path.parent for path in root.rglob("world.sqlite")
                  if path.parent.name == "world")


def _reconstructed_route_texts(publication: Path) -> list[str]:
    """Every retained source text behind the published software subjects."""
    view = open_governance_world(publication)
    try:
        world = view.world
        texts = []
        for row in world.relation_rows("software_subject"):
            assertion_id = world._inner._store.assertion_id_for_tuple(
                "software_subject", dict(row))
            warrant = world.warrant_for_assertion(assertion_id)
            for base in warrant["bases"]:
                for item in (base.get("detail") or {}).get("observations") or []:
                    text, status = reconstruct_governance_observation(world, item)
                    assert status == "OK"
                    texts.append(text)
        assert texts
        return texts
    finally:
        view.world.close()


def _warrant_dump(publication: Path) -> str:
    """All assertion warrants in a sealed World, as one JSON string."""
    view = open_governance_world(publication)
    try:
        world = view.world
        warrants = []
        for entry in world.query("SELECT name FROM _world_relations ORDER BY name"):
            relation = str(entry["name"])
            try:
                rows = world.relation_rows(relation)
            except Exception:
                continue
            for row in rows:
                assertion_id = world._inner._store.assertion_id_for_tuple(
                    relation, dict(row))
                warrants.append(world.warrant_for_assertion(assertion_id))
        assert warrants
        return json.dumps(warrants, sort_keys=True, default=str)
    finally:
        view.world.close()


def _loop_trace(request: dict, outcome: dict, observation: dict,
                consumed: str, publication: Path) -> dict:
    """Cross-stage audit answer assembled from existing records only."""
    return {
        "request_id": request["request_id"],
        "requested_path": request["desired_path"],
        "capability": outcome["capability"]["id"],
        "capability_outcome": outcome["outcome"],
        "reported_revision": outcome["reported_written_revision"],
        "observed_revision": observation["revision"],
        "observed_path": observation["routes"]["customer-export"]["path"],
        "consumed_revision": consumed,
        "published_snapshot": _published_snapshot(publication),
        "publication": str(publication),
    }


def test_happy_path_request_to_publication(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    r0 = _sha(source.read_bytes())
    request = _request(source, expected_revision=r0)
    assert request["expected_starting_revision"] == r0
    assert request["desired_path"] == "/internal/export"

    outcome = _invoke(request)
    assert outcome["outcome"] == "SUCCESS" and outcome["invoked"]
    assert outcome["capability"]["id"] == "fixture.config_route_path_edit"

    observation = _observe(source)
    assert observation["status"] == "OK"
    r1 = observation["revision"]
    assert r1 == outcome["reported_written_revision"] and r1 != r0
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    assert _feedback(request, outcome, observation)["requested_path_observed"]

    handoff = _handoff(observation, source)
    assert handoff["eligible"] and handoff["construction_precondition"] == r1
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED" and intake["consumed_revision"] == r1

    before_publish = source.read_bytes()
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    assert source.read_bytes() == before_publish  # publication mutates no source
    assert w1 != w0 and (w1 / "world.sqlite").is_file()

    assert _published_snapshot(w1) == f"snapshot:{r1[:32]}"
    assert _route_fact(w1, "customer-export")["path"] == "/internal/export"
    texts = _reconstructed_route_texts(w1)
    assert any("/internal/export" in text for text in texts)
    assert all("/customers/export" not in text for text in texts)
    assert _sealed_bytes(w0) == w0_bytes

    trace = _loop_trace(request, outcome, observation, intake["consumed_revision"], w1)
    assert trace["observed_revision"] == trace["consumed_revision"] == r1
    assert trace["published_snapshot"] == f"snapshot:{r1[:32]}"


def test_no_automatic_governance_carry_forward(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    assert _bindings(w0) == [{"proposition": EXPORT_ID,
                              "software_subject": _route_fact(w0, "customer-export")["subject"]}]
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    observation = _observe(source)
    r1 = observation["revision"]
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=r1)
    assert intake["outcome"] == "CONSUMED"
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    assert _bindings(w1) == []  # nothing carried; no new binding was supplied
    old_subject = _route_fact(w0, "customer-export")["subject"]
    new_subject = _route_fact(w1, "customer-export")["subject"]
    assert old_subject != new_subject  # revision-scoped identity cannot transfer

    explicit = _seal_from_produced(tmp_path / "w1b", intake["staging"],
                                   intake["produced"], binding=True)
    assert explicit.succeeded, explicit.errors
    assert _bindings(explicit.world_dir) == [{"proposition": EXPORT_ID,
                                              "software_subject": new_subject}]


def test_execution_x_observation_y_publishes_y_not_x(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    request = _request(source)
    outcome = _invoke(request)
    assert outcome["outcome"] == "SUCCESS"
    _set_path_uninstrumented(source, "customer-export", "/other/export")

    observation = _observe(source)
    assert observation["status"] == "OK"
    assert observation["revision"] != outcome["reported_written_revision"]
    assert observation["routes"]["customer-export"]["path"] == "/other/export"
    assert not _feedback(request, outcome, observation)["requested_path_observed"]
    handoff = _handoff(observation, source)
    assert handoff["eligible"]
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED"
    result = _seal_from_produced(tmp_path / "wy", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    wy = result.world_dir

    assert _route_fact(wy, "customer-export")["path"] == "/other/export"
    texts = _reconstructed_route_texts(wy)
    assert any("/other/export" in text for text in texts)
    assert all("/internal/export" not in text for text in texts)
    assert _sealed_bytes(w0) == w0_bytes

    trace = _loop_trace(request, outcome, observation, intake["consumed_revision"], wy)
    assert trace["requested_path"] == "/internal/export"  # intent = X
    assert trace["reported_revision"] != trace["observed_revision"]
    assert trace["observed_path"] == "/other/export"  # observation = Y
    assert trace["consumed_revision"] == trace["observed_revision"]  # consumed = Y
    assert trace["published_snapshot"] == f"snapshot:{trace['observed_revision'][:32]}"


def test_unsupported_observation_y_publishes_neither_x_nor_y(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    compact = json.dumps(json.loads(source.read_bytes()), separators=(",", ":")).encode()
    source.write_bytes(compact)

    observation = _observe(source)
    assert observation["status"] == "UNSUPPORTED"
    assert not _handoff(observation, source)["eligible"]
    assert _sealed_publications(tmp_path) == [w0]
    assert _sealed_bytes(w0) == w0_bytes


def test_race_between_observation_and_acquisition_refuses(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    observation = _observe(source)
    r1 = observation["revision"]
    assert _handoff(observation, source)["eligible"]
    _set_path_uninstrumented(source, "customer-export", "/other/export")
    r2 = _sha(source.read_bytes())
    assert r2 != r1

    staging = tmp_path / "staging"
    intake = _live_current_construct(source, staging, expected_revision=r1)
    assert intake["outcome"] == "REFUSED"
    assert intake["expected_revision"] == r1 and intake["consumed_revision"] == r2
    assert not staging.exists()
    assert _sealed_publications(tmp_path) == [w0]
    assert _sealed_bytes(w0) == w0_bytes
    assert _sha(source.read_bytes()) == r2  # no auto-retry against R2


def test_change_after_acquisition_publishes_truthful_misaligned_world(tmp_path, monkeypatch):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    r1 = _sha(source.read_bytes())
    calls, guard = _install_read_hook(
        monkeypatch, source,
        after_first=lambda: _set_path_uninstrumented(
            source, "customer-export", "/other/export"),
    )
    intake = _live_current_construct(source, tmp_path / "staging", expected_revision=r1)
    guard["enabled"] = False
    r2 = _sha(source.read_bytes())
    assert len(calls) == 1 and _sha(calls[0]) == r1 and r2 != r1
    assert intake["outcome"] == "CONSUMED" and intake["consumed_revision"] == r1

    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    assert _published_snapshot(w1) == f"snapshot:{r1[:32]}"
    assert _route_fact(w1, "customer-export")["path"] == "/internal/export"
    texts = _reconstructed_route_texts(w1)
    assert any("/internal/export" in text for text in texts)
    assert _sealed_bytes(w0) == w0_bytes
    assert _sha(source.read_bytes()) == r2
    assert _published_snapshot(w1) != f"snapshot:{r2[:32]}"  # truthful, misaligned


def test_change_after_publication_keeps_history(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    r1 = _sha(source.read_bytes())
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=r1)
    assert intake["outcome"] == "CONSUMED"
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    w1_bytes = _sealed_bytes(w1)

    _set_path_uninstrumented(source, "customer-export", "/other/export")
    r2 = _sha(source.read_bytes())
    assert r2 != r1
    assert _sealed_bytes(w1) == w1_bytes
    assert _published_snapshot(w1) == f"snapshot:{r1[:32]}"
    assert _route_fact(w1, "customer-export")["path"] == "/internal/export"
    texts = _reconstructed_route_texts(w1)
    assert any("/internal/export" in text for text in texts)
    assert all("/other/export" not in text for text in texts)


def test_failed_execution_builds_nothing_from_request(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    r0 = _sha(source.read_bytes())
    request = _request(source, expected_revision=r0)
    outcome = _invoke(request, fault="fail_before_write")
    assert outcome["outcome"] == "FAILED"

    observation = _observe(source)
    assert observation["revision"] == r0
    assert observation["routes"]["customer-export"]["path"] == "/customers/export"
    assert not _feedback(request, outcome, observation)["requested_path_observed"]
    assert _handoff(observation, source)["eligible"]  # R0 remains valid input
    assert _sealed_publications(tmp_path) == [w0]
    assert _sealed_bytes(w0) == w0_bytes


def test_failure_after_write_can_construct_observed_state(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    request = _request(source)
    outcome = _invoke(request, fault="fail_after_write")
    assert outcome["outcome"] == "FAILED"
    assert outcome["reported_written_revision"] is not None

    observation = _observe(source)
    r1 = observation["revision"]
    assert r1 == outcome["reported_written_revision"]
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    handoff = _handoff(observation, source)
    assert handoff["eligible"]
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED" and intake["consumed_revision"] == r1
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    assert _route_fact(result.world_dir, "customer-export")["path"] == "/internal/export"


def test_construction_failure_after_successful_mutation(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    observation = _observe(source)
    r1 = observation["revision"]
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=r1)
    assert intake["outcome"] == "CONSUMED" and intake["consumed_revision"] == r1

    result = _seal_from_produced(
        tmp_path / "w1", intake["staging"], intake["produced"],
        binding=True, binding_subject="route:deadbeef:customer-export")
    assert not result.succeeded and result.world_dir is None
    assert result.errors
    assert not (tmp_path / "w1" / "world").exists()
    assert _sha(source.read_bytes()) == r1  # source changed; no rollback fiction
    assert _sealed_publications(tmp_path) == [w0]
    assert (tmp_path / "staging" / "world.sqlite").is_file()  # unsealed candidate only
    assert _sealed_bytes(w0) == w0_bytes


def test_publication_failure_after_successful_construction(tmp_path, monkeypatch):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    w0_bytes = _sealed_bytes(w0)
    request = _request(source)
    assert _invoke(request)["outcome"] == "SUCCESS"
    r1 = _sha(source.read_bytes())
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=r1)
    assert intake["outcome"] == "CONSUMED"

    destination = tmp_path / "w1" / "world"
    original_rename = Path.rename
    observed_candidate = []

    def fail_final_rename(path: Path, target: Path):
        if path == destination.with_name("world.sg-work") and Path(target) == destination:
            observed_candidate.append((path / "world.sqlite").is_file())
            raise OSError("injected publication failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_final_rename)
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert not result.succeeded and result.world_dir is None
    assert any("injected publication failure" in error for error in result.errors)
    assert observed_candidate == [True]
    assert not destination.exists()
    assert not destination.with_name("world.sg-work").exists()
    assert _sha(source.read_bytes()) == r1
    assert _sealed_bytes(w0) == w0_bytes


def test_audit_trail_keeps_provenance_out_of_support(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    request = _request(source, actor="human")
    outcome = _invoke(request)
    assert outcome["outcome"] == "SUCCESS"
    observation = _observe(source)
    r1 = observation["revision"]
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=r1)
    assert intake["outcome"] == "CONSUMED"
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir

    trace = _loop_trace(request, outcome, observation, intake["consumed_revision"], w1)
    assert trace["requested_path"] == "/internal/export"
    assert trace["capability_outcome"] == "SUCCESS"
    assert trace["reported_revision"] == trace["observed_revision"] == r1
    assert trace["observed_path"] == "/internal/export"
    assert trace["consumed_revision"] == r1
    assert trace["published_snapshot"] == f"snapshot:{r1[:32]}"
    assert trace["publication"] == str(w1)

    dump = _warrant_dump(w1)
    assert request["request_id"] not in dump
    assert '"actor"' not in dump
    assert f"sha256:{r1}" in dump  # support names evidence, not the request


def test_agent_actor_has_same_evidentiary_standing(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    request = _request(source, actor="agent")
    outcome = _invoke(request)
    assert outcome["actor"] == "agent" and outcome["outcome"] == "SUCCESS"
    observation = _observe(source)
    r1 = observation["revision"]
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    assert _feedback(request, outcome, observation)["requested_path_observed"]
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=r1)
    assert intake["outcome"] == "CONSUMED" and intake["consumed_revision"] == r1
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    assert _published_snapshot(w1) == f"snapshot:{r1[:32]}"
    assert _route_fact(w1, "customer-export")["path"] == "/internal/export"
    dump = _warrant_dump(w1)
    assert "agent" not in dump
    assert f"sha256:{r1}" in dump
