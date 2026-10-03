"""Test-local change-to-reconsideration probe for config.routes/v1.

After a bounded operation publishes W1 with a new subject A1 and no carried
binding, what evidence licenses historical governance_binding(P, A0) to enter
an ordinary Case(P, A1) for reconsideration? Bridges may license inquiry;
they never license renewal, identity, or publication. Nothing here changes OA
Core, accepted Construction/Judgment/Investigation semantics, Decision,
admission, maintenance, or any production package.
"""

from __future__ import annotations

import json
from pathlib import Path

from ontology_author.software_governance import (
    BindingSpec,
    CompletenessSpec,
    ManifestationSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
    open_governance_world,
)
from ontology_author.software_governance.investigation import make_proposal
from ontology_author.software_governance.judgment import assemble_case, verify_case
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from profiles.software_governance_config_v0.build import (
    EXPORT,
    EXPORT_ID,
    GOVERNANCE,
    PROFILE_ID,
    SOFTWARE_EVIDENCE,
    STATUS,
    STATUS_ID,
    _excerpt,
)
from profiles.software_governance_config_v0.produce import (
    CAPABILITY as PRODUCER_CAPABILITY,
    KIND as PRODUCER_KIND,
    SCHEME as PRODUCER_SCHEME,
    VERSION as PRODUCER_VERSION,
)
from profiles.software_governance_config_v0.judge import judge as judge_config
from profiles.software_governance_config_v0.produce import produce_routes
from tests.test_config_route_correspondence_contract_experiment import BASE, _publish
from tests.test_software_governance_construction_intake_integrity_experiment import (
    _live_current_construct,
)
from tests.test_software_governance_end_to_end_operational_loop_experiment import (
    _bindings,
    _route_fact,
    _seal_from_produced,
    _sealed_bytes,
)
from tests.test_software_governance_execution_observation_handoff_experiment import (
    CAPABILITY,
    _handoff,
    _invoke,
    _observe,
    _request,
    _set_path_uninstrumented,
    _sha,
)

OPERATION_BRIDGE = "fixture.operation-continuity/v0"
SUPPLIED_BRIDGE = "fixture.supplied-correspondence/v0"
CONDITIONAL_PRODUCER_BRIDGE = "config.routes.correspondence/v0 (hypothetical)"


def _run_loop(source: Path, workdir: Path, *, actor: str = "human",
              route_id: str = "customer-export",
              expected_path: str = "/customers/export",
              desired_path: str = "/internal/export") -> dict:
    """Request, execute, observe, handoff, exact-revision intake, publish."""
    request = _request(source, actor=actor, route_id=route_id,
                       expected_path=expected_path, desired_path=desired_path)
    outcome = _invoke(request)
    assert outcome["outcome"] == "SUCCESS", outcome
    observation = _observe(source)
    assert observation["status"] == "OK", observation
    handoff = _handoff(observation, source)
    assert handoff["eligible"], handoff
    intake = _live_current_construct(
        source, workdir / "staging",
        expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED", intake
    result = _seal_from_produced(workdir / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    return {"request": request, "outcome": outcome, "observation": observation,
            "consumed_revision": intake["consumed_revision"], "w1": result.world_dir}


def _subject_for_route(publication: Path, route_id: str) -> str | None:
    view = open_governance_world(publication)
    try:
        found = [str(row["subject"]) for row in view.world.relation_rows("config_route")
                 if row["record_id"] == route_id]
        return found[0] if len(found) == 1 else None
    finally:
        view.world.close()


def _snapshot(publication: Path) -> str:
    view = open_governance_world(publication)
    try:
        snapshots = {str(row["snapshot"])
                     for row in view.world.relation_rows("software_subject")}
        assert len(snapshots) == 1
        return snapshots.pop()
    finally:
        view.world.close()


def _link_pre_operation(w0: Path, request: dict) -> dict | None:
    """Tie the request's target to a W0 SoftwareSubject, or nothing.

    The tie needs W0's exact source revision, the named route record, and
    the expected value. A bare route-id mention is not a tie.
    """
    if _snapshot(w0) != f"snapshot:{request['expected_starting_revision'][:32]}":
        return None
    subject = _subject_for_route(w0, request["route_id"])
    if subject is None:
        return None
    if _route_fact(w0, request["route_id"])["path"] != request["expected_path"]:
        return None
    return {"subject": subject, "snapshot": _snapshot(w0)}


def _link_post_operation(w1: Path, observation: dict, route_id: str) -> dict | None:
    """Tie the observed post-operation source to a W1 SoftwareSubject."""
    if observation["status"] != "OK":
        return None
    if _snapshot(w1) != f"snapshot:{observation['revision'][:32]}":
        return None
    subject = _subject_for_route(w1, route_id)
    if subject is None:
        return None
    return {"subject": subject, "snapshot": _snapshot(w1)}


def _operation_bridge(w0: Path, w1: Path, request: dict, outcome: dict,
                      observation: dict) -> dict:
    """A bounded in-place edit may license reconsideration inquiry.

    The bridge claims only: A1 is the post-operation subject reconstructed
    from observed R1 after a bounded mutation targeting A0's occurrence.
    It claims no identity, no persistence, no binding, and no renewal.
    """
    refusal = {"status": "REFUSED", "method": OPERATION_BRIDGE}
    if outcome["capability"]["id"] != CAPABILITY["id"]:
        return {**refusal, "reason": "capability is not the bounded in-place edit"}
    if outcome["outcome"] != "SUCCESS":
        return {**refusal, "reason": "operation did not report success"}
    if observation["status"] != "OK":
        return {**refusal, "reason": "no valid observation"}
    if observation["revision"] != outcome["reported_written_revision"]:
        return {**refusal, "reason": "observed state differs from the reported edit"}
    before = _link_pre_operation(w0, request)
    if before is None:
        return {**refusal, "reason": "request target is not tied to a W0 subject"}
    after = _link_post_operation(w1, observation, request["route_id"])
    if after is None:
        return {**refusal, "reason": "observed result is not tied to a W1 subject"}
    return {
        "status": "LICENSED", "method": OPERATION_BRIDGE,
        "w0_address": str(w0), "a0": before["subject"],
        "request_id": request["request_id"], "actor": request["actor"],
        "route_id": request["route_id"],
        "capability": f"{CAPABILITY['id']}/{CAPABILITY['version']}",
        "expected_revision": request["expected_starting_revision"],
        "reported_revision": outcome["reported_written_revision"],
        "observed_revision": observation["revision"],
        "w1_address": str(w1), "a1": after["subject"],
        "basis": "bounded in-place record edit verified by the exact revision chain",
        "limitations": ("event-scoped to this operation; not subject identity, "
                        "not semantic identity, not a current binding"),
    }


def _verify_bridge(bridge: dict, w0_address: Path, w1_address: Path) -> list[str]:
    """Recheck a bridge against exact reopened publications."""
    errors = []
    if bridge.get("status") != "LICENSED":
        return ["bridge is not licensed"]
    if bridge["w0_address"] != str(w0_address) or bridge["w1_address"] != str(w1_address):
        return ["bridge names different publication addresses"]
    if not (w0_address / "world.sqlite").is_file():
        return ["prior publication missing"]
    if not (w1_address / "world.sqlite").is_file():
        return ["current publication missing"]
    if _snapshot(w0_address) != f"snapshot:{bridge['expected_revision'][:32]}":
        errors.append("W0 snapshot does not match the bridged prior revision")
    if _snapshot(w1_address) != f"snapshot:{bridge['observed_revision'][:32]}":
        errors.append("W1 snapshot does not match the bridged observed revision")
    if _subject_for_route(w0_address, bridge["route_id"]) != bridge["a0"]:
        errors.append("A0 is not the bridged route subject in W0")
    if _subject_for_route(w1_address, bridge["route_id"]) != bridge["a1"]:
        errors.append("A1 is not the bridged route subject in W1")
    if bridge["reported_revision"] != bridge["observed_revision"]:
        errors.append("reported and observed revisions differ")
    return errors


def _reconsideration_candidates(w0: Path, bridges: list[dict]) -> list[dict]:
    """Historical bindings with a licensed bridge become inquiry candidates."""
    candidates = []
    for row in _bindings(w0):
        for bridge in bridges:
            if (bridge.get("status") == "LICENSED"
                    and bridge["w0_address"] == str(w0)
                    and bridge["a0"] == row["software_subject"]):
                candidates.append({"proposition": row["proposition"],
                                   "current_subject": bridge["a1"],
                                   "bridge": bridge})
    return candidates


def _reconsideration_case(w1: Path, proposition: str, subject: str,
                          bridge: dict, *, case_id: str) -> tuple[dict, object]:
    """Ordinary Case assembly; lineage travels in the question, not support."""
    view = open_governance_world(w1)
    propositions = {str(row["proposition"])
                    for row in view.world.relation_rows("governance_proposition")}
    subjects = {str(row["subject"]) for row in view.world.relation_rows("software_subject")}
    if proposition not in propositions or subject not in subjects:
        view.world.close()
        raise KeyError((proposition, subject))
    question = (
        f"Reconsider {proposition} for {subject}. Bridge {bridge['method']} links "
        f"{bridge['w0_address']} subject {bridge['a0']} (historically bound) to "
        f"{bridge['w1_address']} subject {subject}. No current binding is asserted."
    )
    case = assemble_case(view, case_id=case_id, question=question,
                         proposition_ids=(proposition,), subject_ids=(subject,))
    assert case["world_address"] == str(w1)
    assert verify_case(view, case) == []
    assert "bridge" not in case
    return case, view


def _cited_ids(artifact: dict) -> set[str]:
    parts = [artifact["applicability"], *artifact["program_findings"]]
    if artifact["conformance"] is not None:
        parts.append(artifact["conformance"])
    return {assertion_id for part in parts for assertion_id in part["assertion_ids"]}


def _invoke_delete_add(request: dict, *, replacement: dict) -> dict:
    """Test-local removal variant: same precondition discipline, no in-place edit."""
    target = Path(request["target"])
    before = target.read_bytes()
    actual_before = _sha(before)
    base = {
        "request_id": request["request_id"],
        "capability": {"id": "fixture.config_route_delete_add",
                       "version": "v0",
                       "target_kind": "config-route-document"},
        "target": str(target), "actor": request["actor"],
        "expected_before": request["expected_starting_revision"],
        "actual_before": actual_before, "invoked": True,
    }
    if actual_before != request["expected_starting_revision"]:
        return {**base, "outcome": "PRECONDITION_FAILED",
                "reported_written_revision": None, "error": "source revision changed"}
    document = json.loads(before)
    routes = document["routes"]
    matching = [item for item in routes if item.get("id") == request["route_id"]]
    if len(matching) != 1 or matching[0].get("path") != request["expected_path"]:
        return {**base, "outcome": "FAILED", "reported_written_revision": None,
                "error": "route or expected path did not match"}
    remaining = [item for item in routes if item.get("id") != request["route_id"]]
    remaining.append(dict(replacement))
    rewritten = (json.dumps({"routes": remaining}, indent=2) + "\n").encode()
    target.write_bytes(rewritten)
    return {**base, "outcome": "SUCCESS", "reported_written_revision": _sha(rewritten),
            "removed": request["route_id"], "added": replacement["id"], "error": None}


def _invoke_split(request: dict, *, first_id: str, second_id: str) -> dict:
    """Test-local split variant: one targeted record becomes two new records."""
    target = Path(request["target"])
    before = target.read_bytes()
    actual_before = _sha(before)
    base = {
        "request_id": request["request_id"],
        "capability": {"id": "fixture.config_route_split",
                       "version": "v0",
                       "target_kind": "config-route-document"},
        "target": str(target), "actor": request["actor"],
        "expected_before": request["expected_starting_revision"],
        "actual_before": actual_before, "invoked": True,
    }
    if actual_before != request["expected_starting_revision"]:
        return {**base, "outcome": "PRECONDITION_FAILED",
                "reported_written_revision": None, "error": "source revision changed"}
    document = json.loads(before)
    routes = document["routes"]
    matching = [item for item in routes if item.get("id") == request["route_id"]]
    if len(matching) != 1 or matching[0].get("path") != request["expected_path"]:
        return {**base, "outcome": "FAILED", "reported_written_revision": None,
                "error": "route or expected path did not match"}
    record = matching[0]
    remaining = [item for item in routes if item.get("id") != request["route_id"]]
    remaining.append({"id": first_id, "path": record["path"] + "/a",
                      "handler": record["handler"]})
    remaining.append({"id": second_id, "path": record["path"] + "/b",
                      "handler": record["handler"]})
    rewritten = (json.dumps({"routes": remaining}, indent=2) + "\n").encode()
    target.write_bytes(rewritten)
    return {**base, "outcome": "SUCCESS", "reported_written_revision": _sha(rewritten),
            "removed": request["route_id"], "added": [first_id, second_id],
            "error": None}


def test_baseline_new_subject_without_binding(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    assert _bindings(w0) == [{"proposition": EXPORT_ID, "software_subject": a0}]
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    a1 = _subject_for_route(w1, "customer-export")
    assert a1 is not None and a1 != a0
    assert _bindings(w1) == []
    assert _route_fact(w1, "customer-export")["path"] == "/internal/export"
    view = open_governance_world(w1)
    try:
        propositions = {str(row["proposition"])
                        for row in view.world.relation_rows("governance_proposition")}
    finally:
        view.world.close()
    assert EXPORT_ID in propositions  # same proposition identity, no binding


def test_operation_bridge_links_a0_to_a1_without_identity(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    bridge = _operation_bridge(w0, w1, run["request"], run["outcome"], run["observation"])
    assert bridge["status"] == "LICENSED"
    assert bridge["a0"] == a0
    assert bridge["a1"] == _subject_for_route(w1, "customer-export")
    assert bridge["observed_revision"] == run["observation"]["revision"]
    assert bridge["w0_address"] == str(w0) and bridge["w1_address"] == str(w1)
    assert _verify_bridge(bridge, w0, w1) == []
    text = json.dumps(bridge)
    assert "identity" in bridge["limitations"]  # disclaimed, not claimed
    assert "not a current binding" in bridge["limitations"]
    assert _bindings(w1) == []
    candidates = _reconsideration_candidates(w0, [bridge])
    assert [(item["proposition"], item["current_subject"]) for item in candidates] == [
        (EXPORT_ID, bridge["a1"])]


def test_pre_operation_target_linkage(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    request = _request(source)
    assert _link_pre_operation(w0, request)["subject"] == a0
    assert _link_pre_operation(
        w0, {**request, "expected_starting_revision": "0" * 64}) is None
    assert _link_pre_operation(
        w0, {**request, "route_id": "missing-route"}) is None
    assert _link_pre_operation(
        w0, {**request, "expected_path": "/wrong/path"}) is None
    health = _request(source, route_id="health", expected_path="/health",
                      desired_path="/internal/health")
    assert _link_pre_operation(w0, health)["subject"] == _subject_for_route(w0, "health")


def test_post_operation_subject_lookup(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    found = _link_post_operation(w1, run["observation"], "customer-export")
    assert found["subject"] == _subject_for_route(w1, "customer-export")
    assert _link_post_operation(w1, run["observation"], "missing-route") is None
    assert _link_post_operation(
        w1, {**run["observation"], "revision": "0" * 64}, "customer-export") is None
    stale = _observe(source)
    _set_path_uninstrumented(source, "customer-export", "/other/export")
    assert _link_post_operation(w1, stale, "customer-export")["subject"] == found["subject"]
    assert _handoff(stale, source)["eligible"] is False  # live moved on regardless


def test_operation_bridge_is_event_scoped(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    first = _run_loop(source, tmp_path / "loop1")
    w1 = first["w1"]
    bridge1 = _operation_bridge(w0, w1, first["request"], first["outcome"],
                               first["observation"])
    assert bridge1["status"] == "LICENSED"
    second = _run_loop(source, tmp_path / "loop2", expected_path="/internal/export",
                       desired_path="/other/export")
    w2 = second["w1"]
    bridge2 = _operation_bridge(w1, w2, second["request"], second["outcome"],
                               second["observation"])
    assert bridge2["status"] == "LICENSED"
    assert bridge2["a0"] == bridge1["a1"]
    assert bridge1["a1"] != bridge2["a1"]
    assert _verify_bridge(bridge1, w0, w2) != []  # bridge1 says nothing about W2
    assert _verify_bridge(bridge2, w0, w2) != []  # bridge2 starts at W1, not W0


def test_delete_replacement_produces_no_successor(tmp_path):
    for name, replacement in (
        ("reuse", {"id": "customer-export", "path": "/elsewhere",
                   "handler": "OtherHandler"}),
        ("fresh", {"id": "replacement", "path": "/elsewhere", "handler": "OtherHandler"}),
    ):
        root = tmp_path / name
        w0, source = _publish(root / "w0", BASE, binding=True)
        request = _request(source)
        outcome = _invoke_delete_add(request, replacement=replacement)
        assert outcome["outcome"] == "SUCCESS", outcome
        assert outcome["removed"] == "customer-export"
        observation = _observe(source)
        assert observation["status"] == "OK", observation
        handoff = _handoff(observation, source)
        assert handoff["eligible"], handoff
        intake = _live_current_construct(
            source, root / "staging",
            expected_revision=handoff["construction_precondition"])
        assert intake["outcome"] == "CONSUMED", intake
        w1 = _seal_custom(root / "w1", intake["staging"], intake["produced"],
                          propositions=((EXPORT_ID, EXPORT),), bindings=())
        bridge = _operation_bridge(w0, w1, request, outcome, observation)
        assert bridge["status"] == "REFUSED", (name, bridge)
        assert _reconsideration_candidates(w0, [bridge]) == []
        if name == "reuse":
            # The trap: the same record ID exists post-operation, yet no
            # continuity is licensed. The operation removed the target.
            assert _subject_for_route(w1, "customer-export") is not None
            assert bridge["reason"] == "capability is not the bounded in-place edit"


def test_overwritten_operation_yields_knowledge_without_continuity(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    request = _request(source)
    outcome = _invoke(request)
    assert outcome["outcome"] == "SUCCESS"
    _set_path_uninstrumented(source, "customer-export", "/other/export")
    observation = _observe(source)
    assert observation["revision"] != outcome["reported_written_revision"]
    handoff = _handoff(observation, source)
    assert handoff["eligible"], handoff
    intake = _live_current_construct(
        source, tmp_path / "staging",
        expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED", intake
    result = _seal_from_produced(tmp_path / "wy", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    wy = result.world_dir
    assert _route_fact(wy, "customer-export")["path"] == "/other/export"
    bridge = _operation_bridge(w0, wy, request, outcome, observation)
    assert bridge["status"] == "REFUSED"
    assert bridge["reason"] == "observed state differs from the reported edit"
    assert _reconsideration_candidates(w0, [bridge]) == []


def test_split_preserves_ambiguity_without_winner(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    request = _request(source)
    outcome = _invoke_split(request, first_id="customer-export-a",
                            second_id="customer-export-b")
    assert outcome["outcome"] == "SUCCESS", outcome
    observation = _observe(source)
    assert observation["status"] == "OK", observation
    handoff = _handoff(observation, source)
    assert handoff["eligible"], handoff
    intake = _live_current_construct(
        source, tmp_path / "staging",
        expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED", intake
    w1 = _seal_custom(tmp_path / "w1", intake["staging"], intake["produced"],
                      propositions=((EXPORT_ID, EXPORT),), bindings=())
    successors = [_subject_for_route(w1, "customer-export-a"),
                  _subject_for_route(w1, "customer-export-b")]
    assert all(subject is not None for subject in successors)
    assert _subject_for_route(w1, "customer-export") is None
    bridge = _operation_bridge(w0, w1, request, outcome, observation)
    assert bridge["status"] == "REFUSED"  # split is not an in-place edit
    ambiguous = {"status": "AMBIGUOUS_SUCCESSORS", "method": OPERATION_BRIDGE,
                 "w0_address": str(w0), "w1_address": str(w1),
                 "candidates": sorted(successors)}
    assert len(ambiguous["candidates"]) == 2
    assert _reconsideration_candidates(w0, [bridge, ambiguous]) == []


def _seal_custom(root: Path, staging: Path, produced, *, propositions: tuple,
                 bindings: tuple) -> Path:
    """Seal a world with caller-chosen propositions and bindings."""
    root.mkdir(parents=True, exist_ok=True)
    blobs = dict(produced.blobs)
    texts = {name: _excerpt(GOVERNANCE, text, blobs) for name, text in propositions}
    by_route = {item.route_id: item for item in produced.routes}
    result = construct_software_governance(
        software_world=staging, output=root / "world", profile_id=PROFILE_ID,
        evidence_blobs=blobs,
        propositions=tuple(
            PropositionSpec(proposition_id=name, statement=text,
                            domain_relation=name.split(":")[1].replace("-", "_"),
                            observations=(texts[name],))
            for name, text in propositions
        ),
        bindings=tuple(
            BindingSpec(
                proposition_id=name, software_subject=by_route[route_id].subject_id,
                support="SOURCE_EXPLICIT", endpoint_resolution="DETERMINISTIC",
                construction_method="reconsideration fixture binding",
                observations=(texts[name],), software_evidence=SOFTWARE_EVIDENCE,
            ) for name, route_id in bindings
        ),
        subjects=tuple(
            SoftwareSubjectSpec(
                subject_id=item.subject_id, snapshot_id=produced.snapshot_id,
                kind=PRODUCER_KIND, capability=PRODUCER_CAPABILITY,
                version=PRODUCER_VERSION,
                observations=(item.document_observation,),
            ) for item in produced.routes
        ),
        manifestations=tuple(
            ManifestationSpec(
                subject_id=item.subject_id, scheme=PRODUCER_SCHEME,
                location=item.location,
                capability=f"{PRODUCER_CAPABILITY}/{PRODUCER_VERSION}",
                observations=(item.manifestation_observation,),
            ) for item in produced.routes
        ),
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY, status="INCOMPLETE",
            universe=produced.snapshot_id,
            basis="only reconsideration fixture correspondences are recorded",
            known_gaps=("reconsideration_probe_only",),
        ),
    )
    assert result.succeeded, result.errors
    return result.world_dir


def _supplied_bridge(w0: Path, a0: str, w1: Path, a1: str, *, provenance: dict) -> dict:
    """Explicit supplied correspondence; endpoints grounded, claim supplied."""
    view0 = open_governance_world(w0)
    try:
        priors = {str(row["subject"]) for row in view0.world.relation_rows("software_subject")}
    finally:
        view0.world.close()
    view1 = open_governance_world(w1)
    try:
        currents = {str(row["subject"]) for row in view1.world.relation_rows("software_subject")}
    finally:
        view1.world.close()
    if a0 not in priors or a1 not in currents:
        return {"status": "REFUSED", "method": SUPPLIED_BRIDGE,
                "reason": "bridge endpoint is not a published subject"}
    return {
        "status": "LICENSED", "method": SUPPLIED_BRIDGE,
        "w0_address": str(w0), "a0": a0, "w1_address": str(w1), "a1": a1,
        "provenance": dict(provenance),
        "basis": "explicit supplied correspondence assertion",
        "limitations": "supplied, not verified; not identity; not a current binding",
    }


def _conditional_producer_pair(w0: Path, a0: str, w1: Path, a1: str) -> dict:
    """The hypothetical correspondence shape, labeled as not established."""
    return {
        "status": "LICENSED", "method": CONDITIONAL_PRODUCER_BRIDGE,
        "w0_address": str(w0), "a0": a0, "w1_address": str(w1), "a1": a1,
        "basis": "hypothetical persistent-key contract (not established)",
        "limitations": ("conditional mechanical entailment only; not an accepted "
                        "producer fact; not a current binding"),
    }


def test_merge_surfaces_both_contexts_only_via_supplied_bridges(tmp_path):
    _, source = _publish(tmp_path / "w0base", BASE, binding=True)
    produced0 = produce_routes(tmp_path / "reproduce0", source)
    w0 = _seal_custom(tmp_path / "w0", tmp_path / "reproduce0", produced0,
                      propositions=((EXPORT_ID, EXPORT), (STATUS_ID, STATUS)),
                      bindings=((EXPORT_ID, "customer-export"), (STATUS_ID, "health")))
    a0 = _subject_for_route(w0, "customer-export")
    h0 = _subject_for_route(w0, "health")
    assert len(_bindings(w0)) == 2
    # Manual merge: no Design operation, so no operation bridge is buildable.
    source.write_text(json.dumps({"routes": [
        {"id": "customer-export", "path": "/unified", "handler": "CustomerExport"},
    ]}, indent=2) + "\n", encoding="utf-8")
    observation = _observe(source)
    assert observation["status"] == "OK", observation
    handoff = _handoff(observation, source)
    assert handoff["eligible"], handoff
    intake = _live_current_construct(
        source, tmp_path / "staging",
        expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED", intake
    w1 = _seal_custom(tmp_path / "w1", intake["staging"], intake["produced"],
                      propositions=((EXPORT_ID, EXPORT), (STATUS_ID, STATUS)),
                      bindings=())
    m1 = _subject_for_route(w1, "customer-export")
    assert _bindings(w1) == []
    assert _reconsideration_candidates(w0, []) == []
    supplied = [
        _supplied_bridge(w0, a0, w1, m1, provenance={"asserter": "human:merger",
                                                    "note": "export merged into unified"}),
        _supplied_bridge(w0, h0, w1, m1, provenance={"asserter": "human:merger",
                                                    "note": "health merged into unified"}),
    ]
    assert all(item["status"] == "LICENSED" for item in supplied)
    candidates = _reconsideration_candidates(w0, supplied)
    assert {(item["proposition"], item["current_subject"]) for item in candidates} == {
        (EXPORT_ID, m1), (STATUS_ID, m1)}
    for item in candidates:
        case, view = _reconsideration_case(w1, item["proposition"], m1, item["bridge"],
                                           case_id=f"merge-{item['proposition']}")
        try:
            assert judge_config(case)["applicability"]["result"] == "UNKNOWN"
        finally:
            view.world.close()


def test_conditional_producer_pair_is_consumable_but_not_established(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    a0 = _subject_for_route(w0, "customer-export")
    a1 = _subject_for_route(w1, "customer-export")
    produced = produce_routes(tmp_path / "reproduce", source)
    assert not hasattr(produced, "correspondence")
    view = open_governance_world(w1)
    try:
        names = [str(entry["name"])
                 for entry in view.world.query("SELECT name FROM _world_relations")]
    finally:
        view.world.close()
    assert not [name for name in names if "correspond" in name]
    pair = _conditional_producer_pair(w0, a0, w1, a1)
    assert pair["status"] == "LICENSED"
    assert "not established" in pair["basis"] or "hypothetical" in pair["method"]
    candidates = _reconsideration_candidates(w0, [pair])
    assert [(item["proposition"], item["current_subject"]) for item in candidates] == [
        (EXPORT_ID, a1)]
    case, case_view = _reconsideration_case(w1, EXPORT_ID, a1, pair, case_id="conditional")
    try:
        assert CONDITIONAL_PRODUCER_BRIDGE in case["question"]
        assert judge_config(case)["applicability"]["result"] == "UNKNOWN"
    finally:
        case_view.world.close()


def test_supplied_correspondence_licenses_inquiry_not_applicability(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    _set_path_uninstrumented(source, "customer-export", "/manual/export")
    observation = _observe(source)
    assert observation["status"] == "OK", observation
    handoff = _handoff(observation, source)
    assert handoff["eligible"], handoff
    intake = _live_current_construct(
        source, tmp_path / "staging",
        expected_revision=handoff["construction_precondition"])
    assert intake["outcome"] == "CONSUMED", intake
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    a1 = _subject_for_route(w1, "customer-export")
    assert _reconsideration_candidates(w0, []) == []
    bridge = _supplied_bridge(w0, a0, w1, a1,
                              provenance={"asserter": "human:reviewer",
                                          "note": "same route after manual edit"})
    assert bridge["status"] == "LICENSED"
    assert bridge["provenance"]["asserter"] == "human:reviewer"
    candidates = _reconsideration_candidates(w0, [bridge])
    assert [(item["proposition"], item["current_subject"]) for item in candidates] == [
        (EXPORT_ID, a1)]
    case, view = _reconsideration_case(w1, EXPORT_ID, a1, bridge, case_id="supplied")
    try:
        assert SUPPLIED_BRIDGE in case["question"]
        conclusion = judge_config(case)
        assert conclusion["applicability"]["result"] == "UNKNOWN"
        assert conclusion["conformance"] is None
    finally:
        view.world.close()
    refused = _supplied_bridge(w0, "route:missing:subject", w1, a1,
                               provenance={"asserter": "human:reviewer"})
    assert refused["status"] == "REFUSED"


def test_manual_change_without_bridge_surfaces_nothing(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    _set_path_uninstrumented(source, "customer-export", "/manual/export")
    observation = _observe(source)
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=observation["revision"])
    assert intake["outcome"] == "CONSUMED", intake
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    a1 = _subject_for_route(w1, "customer-export")
    assert a1 is not None and a1 != a0  # same record ID, no licensed bridge
    assert _reconsideration_candidates(w0, []) == []
    before = open_governance_world(w0)
    try:
        assert before.propositions_for_subject(a0) == [EXPORT_ID]
    finally:
        before.world.close()
    after = open_governance_world(w1)
    try:
        assert after.propositions_for_subject(a1) == []
        assert not after.absence_is_negative(a1)
    finally:
        after.world.close()


def test_bridge_requires_exact_publications(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    bridge = _operation_bridge(w0, w1, run["request"], run["outcome"], run["observation"])
    assert bridge["status"] == "LICENSED"
    twin0, _ = _publish(tmp_path / "twin0", BASE, binding=True)
    assert _snapshot(twin0) == _snapshot(w0) and twin0 != w0
    assert _verify_bridge(bridge, twin0, w1) == ["bridge names different publication addresses"]
    twin_source = tmp_path / "twin-source.json"
    twin_source.write_bytes(source.read_bytes())
    twin_intake = _live_current_construct(
        twin_source, tmp_path / "twin-staging",
        expected_revision=run["observation"]["revision"])
    assert twin_intake["outcome"] == "CONSUMED", twin_intake
    twin_result = _seal_from_produced(tmp_path / "twin1", twin_intake["staging"],
                                      twin_intake["produced"])
    assert twin_result.succeeded, twin_result.errors
    twin1 = twin_result.world_dir
    assert _snapshot(twin1) == _snapshot(w1) and twin1 != w1
    assert _verify_bridge(bridge, w0, twin1) == ["bridge names different publication addresses"]
    tampered = {**bridge, "a1": bridge["a0"]}
    assert any("A1" in error for error in _verify_bridge(tampered, w0, w1))


def _binding_assertion_id(publication: Path, proposition: str, subject: str) -> str:
    view = open_governance_world(publication)
    try:
        return view.world._inner._store.assertion_id_for_tuple(
            "governance_binding",
            {"proposition": proposition, "software_subject": subject})
    finally:
        view.world.close()


def test_reconsideration_case_carries_lineage_outside_support(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    bridge = _operation_bridge(w0, w1, run["request"], run["outcome"], run["observation"])
    assert bridge["status"] == "LICENSED"
    candidates = _reconsideration_candidates(w0, [bridge])
    assert len(candidates) == 1
    a1 = candidates[0]["current_subject"]
    case, view = _reconsideration_case(w1, EXPORT_ID, a1, bridge, case_id="reconsider")
    try:
        assert OPERATION_BRIDGE in case["question"]
        assert str(w0) in case["question"]  # lineage is case context narrative
        assert case["world_address"] == str(w1)
        conclusion = judge_config(case)
        assert conclusion["applicability"]["result"] == "UNKNOWN"
        assert conclusion["conformance"] is None
        assert conclusion["context_requests"] == []
        included = {fact["assertion_id"] for fact in case["facts"]}
        cited = _cited_ids(conclusion)
        assert cited < included  # support is a proper subset of context
        historical = _binding_assertion_id(w0, EXPORT_ID, a0)
        assert historical not in cited  # the W0 binding never supports the verdict
    finally:
        view.world.close()
    assert _bindings(w1) == []  # inquiry created no binding


def test_independent_current_binding_judges_without_inheritance(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    run = _run_loop(source, tmp_path / "loop")
    a1 = _subject_for_route(run["w1"], "customer-export")
    assert a1 is not None
    # W1b: the same R1 software, plus an independently supplied binding.
    produced = produce_routes(tmp_path / "reproduce", source)
    assert produced.snapshot_id == _snapshot(run["w1"])
    bound = _seal_custom(tmp_path / "w1b", tmp_path / "reproduce", produced,
                         propositions=((EXPORT_ID, EXPORT),),
                         bindings=((EXPORT_ID, "customer-export"),))
    assert _bindings(bound) == [{"proposition": EXPORT_ID, "software_subject": a1}]
    bridge = _operation_bridge(w0, bound, run["request"], run["outcome"],
                               run["observation"])
    assert bridge["status"] == "LICENSED"
    assert bridge["a1"] == a1
    before = _sealed_bytes(bound)
    case, view = _reconsideration_case(bound, EXPORT_ID, a1, bridge, case_id="bound")
    try:
        conclusion = judge_config(case)
        assert conclusion["applicability"]["result"] == "APPLIES"
        assert conclusion["conformance"]["result"] == "CONFLICTS"
        assert conclusion["conformance"]["rule"]["observed_path"] == "/internal/export"
    finally:
        view.world.close()
    assert _sealed_bytes(bound) == before  # judging publishes nothing
    assert len(_bindings(bound)) == 1  # the verdict is not a second binding
    # Conforming leg: an unchanged export record, republished and bound.
    steady, _ = _publish(tmp_path / "steady", BASE, binding=True)
    steady_subject = _subject_for_route(steady, "customer-export")
    steady_bridge = _supplied_bridge(w0, _subject_for_route(w0, "customer-export"),
                                     steady, steady_subject,
                                     provenance={"asserter": "human:reviewer"})
    steady_case, steady_view = _reconsideration_case(
        steady, EXPORT_ID, steady_subject, steady_bridge, case_id="steady")
    try:
        steady_conclusion = judge_config(steady_case)
        assert steady_conclusion["applicability"]["result"] == "APPLIES"
        assert steady_conclusion["conformance"]["result"] == "CONFORMS"
    finally:
        steady_view.world.close()


def test_replacement_inquiry_can_be_refused_by_evaluator(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    request = _request(source)
    outcome = _invoke_delete_add(
        request, replacement={"id": "customer-export", "path": "/elsewhere",
                              "handler": "OtherHandler"})
    assert outcome["outcome"] == "SUCCESS", outcome
    observation = _observe(source)
    assert observation["status"] == "OK", observation
    intake = _live_current_construct(
        source, tmp_path / "staging", expected_revision=observation["revision"])
    assert intake["outcome"] == "CONSUMED", intake
    result = _seal_from_produced(tmp_path / "w1", intake["staging"], intake["produced"])
    assert result.succeeded, result.errors
    w1 = result.world_dir
    b1 = _subject_for_route(w1, "customer-export")
    assert _operation_bridge(w0, w1, request, outcome, observation)["status"] == "REFUSED"
    bridge = _supplied_bridge(w0, a0, w1, b1,
                              provenance={"asserter": "human:reviewer",
                                          "note": "replacement record offered for inquiry"})
    assert bridge["status"] == "LICENSED"
    case, view = _reconsideration_case(w1, EXPORT_ID, b1, bridge, case_id="replacement")
    try:
        conclusion = judge_config(case)
        assert conclusion["applicability"]["result"] == "DOES_NOT_APPLY"
        assert conclusion["conformance"] is None
        assert conclusion["applicability"]["rule"]["observed_handler"] == "OtherHandler"
        assert len(conclusion["applicability"]["assertion_ids"]) == 2
    finally:
        view.world.close()
    assert _bindings(w1) == []


def _maybe_propose_binding(w1: Path, case: dict, artifact: dict, bridge: dict) -> dict:
    """Test-local proposal rule: expressible only when no binding is published."""
    if _bindings(w1):
        subjects = {row["software_subject"] for row in _bindings(w1)}
        if case["subject_ids"][0] in subjects:
            return {"proposed": False,
                    "reason": "binding already published; judgment adds no binding"}
    proposal = make_proposal(
        proposal_id="fixture:bind-export-after-change",
        originating_case_id=case["case_id"],
        originating_question_id="fixture:reconsider-export",
        epistemic_class="semantic",
        payload={"relation": "governance_binding", "proposition": EXPORT_ID,
                 "software_subject": case["subject_ids"][0]},
        basis={"w1_address": str(w1), "bridge_method": bridge["method"],
               "applicability": artifact["applicability"]["result"]},
        method={"id": "fixture.reconsideration-proposal/v0"},
        reason="binding absent from W1; proposal only, not admitted or published",
    )
    return {"proposed": True, "proposal": proposal}


def test_proposal_expresses_candidate_binding_without_publication(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    bridge = _operation_bridge(w0, w1, run["request"], run["outcome"], run["observation"])
    assert bridge["status"] == "LICENSED"
    a1 = bridge["a1"]
    case, view = _reconsideration_case(w1, EXPORT_ID, a1, bridge, case_id="propose")
    try:
        artifact = judge_config(case)
        assert artifact["applicability"]["result"] == "UNKNOWN"
        before = _sealed_bytes(w1)
        decision = _maybe_propose_binding(w1, case, artifact, bridge)
        assert decision["proposed"] is True
        proposal = decision["proposal"]
        assert proposal["epistemic_class"] == "semantic"
        assert "assertion_id" not in proposal
        assert proposal["basis"]["applicability"] == "UNKNOWN"
        assert _bindings(w1) == []
        assert _sealed_bytes(w1) == before
    finally:
        view.world.close()
    # Where a binding is already published, APPLIES motivates no proposal.
    produced = produce_routes(tmp_path / "reproduce", source)
    bound = _seal_custom(tmp_path / "w1b", tmp_path / "reproduce", produced,
                         propositions=((EXPORT_ID, EXPORT),),
                         bindings=((EXPORT_ID, "customer-export"),))
    bound_bridge = _operation_bridge(w0, bound, run["request"], run["outcome"],
                                     run["observation"])
    assert bound_bridge["status"] == "LICENSED"
    bound_case, bound_view = _reconsideration_case(bound, EXPORT_ID, a1, bound_bridge,
                                                   case_id="bound-propose")
    try:
        bound_artifact = judge_config(bound_case)
        assert bound_artifact["applicability"]["result"] == "APPLIES"
        refused = _maybe_propose_binding(bound, bound_case, bound_artifact, bridge)
        assert refused == {"proposed": False,
                           "reason": "binding already published; judgment adds no binding"}
    finally:
        bound_view.world.close()


def test_agent_operation_bridge_same_standing(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    run = _run_loop(source, tmp_path / "loop", actor="agent")
    assert run["outcome"]["actor"] == "agent"
    w1 = run["w1"]
    bridge = _operation_bridge(w0, w1, run["request"], run["outcome"], run["observation"])
    assert bridge["status"] == "LICENSED"
    assert bridge["actor"] == "agent"
    assert bridge["method"] == OPERATION_BRIDGE
    assert bridge["basis"] == ("bounded in-place record edit verified by the exact "
                               "revision chain")
    assert _verify_bridge(bridge, w0, w1) == []
    candidates = _reconsideration_candidates(w0, [bridge])
    assert [(item["proposition"], item["current_subject"]) for item in candidates] == [
        (EXPORT_ID, bridge["a1"])]


def test_product_answer_distinguishes_historical_candidate_and_current(tmp_path):
    w0, source = _publish(tmp_path / "w0", BASE, binding=True)
    a0 = _subject_for_route(w0, "customer-export")
    run = _run_loop(source, tmp_path / "loop")
    w1 = run["w1"]
    bridge = _operation_bridge(w0, w1, run["request"], run["outcome"], run["observation"])
    assert bridge["status"] == "LICENSED"
    candidates = _reconsideration_candidates(w0, [bridge])
    assert len(candidates) == 1
    a1 = candidates[0]["current_subject"]
    case, view = _reconsideration_case(w1, EXPORT_ID, a1, bridge, case_id="product")
    try:
        conclusion = judge_config(case)
        answer = {
            "changed_subject": (a1, str(w1)),
            "historical_subject": (a0, str(w0)),
            "why_related": (bridge["method"], bridge["basis"]),
            "historical_governance": [(row["proposition"], row["software_subject"])
                                      for row in _bindings(w0)
                                      if row["software_subject"] == a0],
            "current_governance": [row for row in _bindings(w1)
                                   if row["software_subject"] == a1],
            "reconsideration": (case["case_id"], case["question"]),
            "judgment": (conclusion["applicability"]["result"],
                         conclusion["applicability"]["because"]),
            "new_binding_published": _bindings(w1),
        }
    finally:
        view.world.close()
    assert answer["historical_governance"] == [(EXPORT_ID, a0)]
    assert answer["current_governance"] == []
    assert answer["judgment"][0] == "UNKNOWN"
    assert answer["new_binding_published"] == []
    assert answer["changed_subject"][0] != answer["historical_subject"][0]
    assert answer["why_related"][0] == OPERATION_BRIDGE
