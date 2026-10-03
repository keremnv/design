"""Test-local route edit, independent observation, and pre-Construction handoff."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from ontology_author.world.runtime.world import ConstructionError
from profiles.software_governance_config_v0.produce import _object_span


SOURCE = Path(__file__).resolve().parents[1] / "profiles/software_governance_config_v0/software.json"
CAPABILITY = {
    "id": "fixture.config_route_path_edit",
    "version": "v0",
    "target_kind": "config-route-document",
    "accepted_inputs": ("route_id", "expected_path", "desired_path"),
    "precondition": "exact SHA-256 of starting source bytes",
}
OBSERVER = "fixture.config_route_observation/v0"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file(tmp_path: Path) -> Path:
    target = tmp_path / "software.json"
    shutil.copyfile(SOURCE, target)
    return target


def _request(target: Path, *, actor: str = "human", expected_revision: str | None = None,
             route_id: str = "customer-export", expected_path: str = "/customers/export",
             desired_path: str = "/internal/export") -> dict:
    return {
        "request_id": "fixture:change-export-route", "actor": actor,
        "target": str(target), "route_id": route_id,
        "expected_path": expected_path, "desired_path": desired_path,
        "expected_starting_revision": expected_revision or _sha(target.read_bytes()),
    }


def _set_path_uninstrumented(target: Path, route_id: str, path: str) -> None:
    """Stand-in for a human or competing writer; no Design action result."""
    document = json.loads(target.read_bytes())
    route = next(item for item in document["routes"] if item["id"] == route_id)
    route["path"] = path
    target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _invoke(request: dict, *, fault: str | None = None) -> dict:
    """One bounded external capability; it never constructs or publishes."""
    target = Path(request["target"])
    before = target.read_bytes()
    actual_before = _sha(before)
    base = {
        "request_id": request["request_id"], "capability": dict(CAPABILITY),
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
    if fault == "fail_before_write":
        return {**base, "outcome": "FAILED", "reported_written_revision": None,
                "error": "injected tool error before write"}
    matching[0]["path"] = request["desired_path"]
    replacement = (json.dumps(document, indent=2) + "\n").encode()
    reported = _sha(replacement)
    if fault == "report_success_without_write":
        return {**base, "outcome": "SUCCESS", "reported_written_revision": reported,
                "error": None}
    target.write_bytes(replacement)
    if fault == "fail_after_write":
        return {**base, "outcome": "FAILED", "reported_written_revision": reported,
                "error": "injected tool error after write"}
    return {**base, "outcome": "SUCCESS", "reported_written_revision": reported,
            "error": None}


def _observe(target: Path) -> dict:
    """Independent bounded read using the config producer's supported locator."""
    try:
        data = target.read_bytes()
    except OSError as exc:
        return {"target": str(target), "method": OBSERVER, "status": "UNAVAILABLE",
                "error": type(exc).__name__, "revision": None, "retained_bytes": None}
    result = {"target": str(target), "method": OBSERVER,
              "revision": _sha(data), "source_locator": f"bytes:0:{len(data)}",
              "retained_bytes": data, "routes": {}, "spans": {}}
    try:
        routes, spans = _supported_routes(data)
    except (ValueError, KeyError, TypeError, ConstructionError) as exc:
        return {**result, "status": "UNSUPPORTED", "error": str(exc),
                "routes": {}, "spans": {}}
    return {**result, "status": "OK", "error": None,
            "routes": routes, "spans": spans}


def _supported_routes(data: bytes) -> tuple[dict, dict]:
    document = json.loads(data)
    records = document["routes"]
    if not isinstance(records, list) or not records:
        raise ValueError("route list is empty or unsupported")
    routes, spans = {}, {}
    for route in records:
        if (not isinstance(route, dict) or not isinstance(route.get("id"), str)
                or not isinstance(route.get("path"), str)
                or not isinstance(route.get("handler"), str)):
            raise ValueError("unsupported route record")
        key = route["id"]
        if key in routes:
            raise ValueError("duplicate route id")
        start, end = _object_span(data, key)
        routes[key] = {"path": route["path"], "handler": route["handler"]}
        spans[key] = f"bytes:{start}:{end}"
    return routes, spans


def _handoff(observation: dict, target: Path, *, mode: str = "live") -> dict:
    """Eligibility only; no producer construction or semantic interpretation."""
    if observation["target"] != str(target) or observation["method"] != OBSERVER:
        return {"eligible": False, "reason": "wrong observation target or method"}
    retained = observation.get("retained_bytes")
    if (observation["status"] != "OK" or not isinstance(retained, bytes)
            or _sha(retained) != observation["revision"]):
        return {"eligible": False, "reason": "no valid reconstructible observation"}
    try:
        routes, spans = _supported_routes(retained)
    except (ValueError, KeyError, TypeError, ConstructionError):
        return {"eligible": False, "reason": "retained source is not producer-readable"}
    if (observation.get("routes") != routes or observation.get("spans") != spans
            or observation.get("source_locator") != f"bytes:0:{len(retained)}"):
        return {"eligible": False, "reason": "observation facts do not match retained source"}
    if mode == "historical":
        return {"eligible": True, "mode": mode, "revision": observation["revision"],
                "source_bytes": retained, "reason": "retained exact observation"}
    if mode != "live":
        raise ValueError(mode)
    try:
        now = _sha(target.read_bytes())
    except OSError:
        return {"eligible": False, "reason": "current target unavailable"}
    if now != observation["revision"]:
        return {"eligible": False, "reason": "source changed since observation",
                "observed_revision": observation["revision"], "current_revision": now}
    return {"eligible": True, "mode": mode, "revision": now,
            "construction_precondition": now, "source_bytes": retained,
            "reason": "producer-readable observation still matches live source"}


def _feedback(request: dict, outcome: dict, observation: dict) -> dict:
    observed = observation.get("routes", {}).get(request["route_id"], {})
    return {"request_id": request["request_id"], "reported_outcome": outcome["outcome"],
            "observed_revision": observation["revision"],
            "observed_path": observed.get("path"),
            "requested_path_observed": observed.get("path") == request["desired_path"]}


def test_normal_success_requires_independent_observation(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    outcome = _invoke(request)
    assert outcome["invoked"] and outcome["outcome"] == "SUCCESS"
    observation = _observe(target)
    assert observation["method"] == OBSERVER and observation["status"] == "OK"
    assert observation["revision"] == outcome["reported_written_revision"]
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    assert _feedback(request, outcome, observation)["requested_path_observed"]
    handoff = _handoff(observation, target)
    assert handoff["eligible"] and handoff["revision"] == observation["revision"]
    assert handoff["construction_precondition"] == observation["revision"]


def test_request_without_invocation_changes_nothing(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    observation = _observe(target)
    assert request["desired_path"] != observation["routes"]["customer-export"]["path"]
    assert _handoff(observation, target)["eligible"]


def test_failed_execution_observes_r0_not_requested_state(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    outcome = _invoke(request, fault="fail_before_write")
    observation = _observe(target)
    assert outcome["outcome"] == "FAILED"
    assert observation["revision"] == request["expected_starting_revision"]
    assert observation["routes"]["customer-export"]["path"] == "/customers/export"
    assert not _feedback(request, outcome, observation)["requested_path_observed"]
    assert _handoff(observation, target)["eligible"]


def test_expected_revision_refuses_competing_pre_execution_edit(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    _set_path_uninstrumented(target, "customer-export", "/manual/export")
    outcome = _invoke(request)
    observation = _observe(target)
    assert outcome["outcome"] == "PRECONDITION_FAILED"
    assert outcome["actual_before"] != outcome["expected_before"]
    assert observation["routes"]["customer-export"]["path"] == "/manual/export"
    assert observation["revision"] == outcome["actual_before"]
    assert _handoff(observation, target)["eligible"]


def test_competing_edit_after_execution_before_observation_wins(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    outcome = _invoke(request)
    assert outcome["outcome"] == "SUCCESS"
    _set_path_uninstrumented(target, "customer-export", "/other/export")
    observation = _observe(target)
    assert observation["status"] == "OK"
    assert observation["revision"] != outcome["reported_written_revision"]
    assert observation["routes"]["customer-export"]["path"] == "/other/export"
    assert not _feedback(request, outcome, observation)["requested_path_observed"]
    handoff = _handoff(observation, target)
    assert handoff["eligible"] and handoff["revision"] == observation["revision"]
    assert b"/other/export" in handoff["source_bytes"]
    assert b"/internal/export" not in handoff["source_bytes"]


def test_competing_edit_after_observation_requires_live_recheck(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    _invoke(request)
    observation = _observe(target)
    r1 = observation["revision"]
    assert _handoff(observation, target)["eligible"]
    _set_path_uninstrumented(target, "customer-export", "/other/export")
    live = _handoff(observation, target)
    historical = _handoff(observation, target, mode="historical")
    assert not live["eligible"] and live["reason"] == "source changed since observation"
    assert live["observed_revision"] == r1 and live["current_revision"] != r1
    assert historical["eligible"] and historical["revision"] == r1
    assert b"/internal/export" in historical["source_bytes"]
    # The current config constructor reads a live path. A retained historical
    # observation would need to be supplied as an explicit immutable input.


def test_partial_two_field_attempt_keeps_each_actual_result(tmp_path):
    target = _file(tmp_path)
    first = _request(target)
    first_outcome = _invoke(first)
    second = _request(target, route_id="health", expected_path="/wrong-health",
                      desired_path="/internal/health")
    second_outcome = _invoke(second)
    observation = _observe(target)
    assert first_outcome["outcome"] == "SUCCESS"
    assert second_outcome["outcome"] == "FAILED"
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    assert observation["routes"]["health"]["path"] == "/health"
    assert _handoff(observation, target)["eligible"]
    assert {"first": first_outcome["outcome"], "second": second_outcome["outcome"]} == {
        "first": "SUCCESS", "second": "FAILED",
    }


def test_failure_after_write_does_not_imply_unchanged_source(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    outcome = _invoke(request, fault="fail_after_write")
    observation = _observe(target)
    assert outcome["outcome"] == "FAILED"
    assert observation["routes"]["customer-export"]["path"] == "/internal/export"
    assert observation["revision"] != request["expected_starting_revision"]
    assert _handoff(observation, target)["eligible"]


def test_misreported_success_is_defeated_by_observation(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    outcome = _invoke(request, fault="report_success_without_write")
    observation = _observe(target)
    assert outcome["outcome"] == "SUCCESS"
    assert outcome["reported_written_revision"] != observation["revision"]
    assert observation["routes"]["customer-export"]["path"] == "/customers/export"
    assert not _feedback(request, outcome, observation)["requested_path_observed"]
    assert _handoff(observation, target)["eligible"]  # R0, not requested X


def test_manual_edit_needs_no_request_or_capability_record(tmp_path):
    target = _file(tmp_path)
    _set_path_uninstrumented(target, "customer-export", "/manual/export")
    observation = _observe(target)
    assert observation["routes"]["customer-export"]["path"] == "/manual/export"
    assert _handoff(observation, target)["eligible"]


def test_agent_edit_has_no_special_evidentiary_standing(tmp_path):
    target = _file(tmp_path)
    request = _request(target, actor="agent")
    outcome = _invoke(request)
    observation = _observe(target)
    assert outcome["actor"] == "agent" and outcome["outcome"] == "SUCCESS"
    assert _handoff(observation, target)["eligible"]
    assert _feedback(request, outcome, observation)["requested_path_observed"]


def test_raw_digest_or_unsupported_source_form_is_not_eligible(tmp_path):
    target = _file(tmp_path)
    raw = target.read_bytes()
    bytes_only = {"target": str(target), "method": OBSERVER, "status": "BYTES_ONLY",
                  "revision": _sha(raw), "retained_bytes": raw}
    assert not _handoff(bytes_only, target)["eligible"]
    compact = json.dumps(json.loads(raw), separators=(",", ":")).encode()
    target.write_bytes(compact)
    observation = _observe(target)
    assert observation["revision"] == _sha(compact)
    assert observation["status"] == "UNSUPPORTED"
    assert not _handoff(observation, target)["eligible"]


def test_retained_observation_and_method_identity_are_verified(tmp_path):
    target = _file(tmp_path)
    observation = _observe(target)
    assert observation["status"] == "OK"
    assert observation["spans"]["customer-export"].startswith("bytes:")
    assert observation["source_locator"] == f"bytes:0:{len(target.read_bytes())}"
    assert not _handoff({**observation, "retained_bytes": b"forged"}, target)["eligible"]
    assert not _handoff({**observation, "routes": {"customer-export": {
        "path": "/forged", "handler": "other"}}}, target)["eligible"]
    assert not _handoff({**observation, "source_locator": "bytes:0:1"}, target)["eligible"]
    assert not _handoff({**observation, "method": "other/v1"}, target)["eligible"]
    assert not _handoff(observation, tmp_path / "different.json")["eligible"]


def test_probe_never_constructs_or_publishes(tmp_path):
    target = _file(tmp_path)
    request = _request(target)
    _invoke(request)
    observation = _observe(target)
    handoff = _handoff(observation, target)
    assert handoff["eligible"]
    assert list(tmp_path.rglob("world.sqlite")) == []
    assert list(tmp_path.rglob("*.json")) == [target]
