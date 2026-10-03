"""Test-local Construction-intake integrity probe for config.routes/v1.

Live-current intake refuses when the revision actually consumed differs from
the handoff's expected revision. Retained-historical intake consumes verified
retained bytes while the live source has moved on. Nothing here changes OA
Core, accepted Construction semantics, or any production package.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import shutil
from pathlib import Path

import pytest

from ontology_author.software_governance import (
    BindingSpec,
    CompletenessSpec,
    ManifestationSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
    open_governance_world,
)
from ontology_author.software_governance.evidence import reconstruct_governance_observation
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld
from profiles.software_governance_config_v0 import produce as produce_module
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
    _object_span,
    produce_routes,
)

SOURCE = Path(__file__).resolve().parents[1] / "profiles/software_governance_config_v0/software.json"
OBSERVER = "fixture.config_route_observation/v0"
INTAKE = "fixture.config_construction_intake/v0"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_routes(document: Path, routes: list[dict]) -> bytes:
    payload = (json.dumps({"routes": routes}, indent=2) + "\n").encode()
    document.write_bytes(payload)
    return payload


def _base_routes() -> list[dict]:
    return [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ]


def _file(tmp_path: Path) -> Path:
    target = tmp_path / "software.json"
    shutil.copyfile(SOURCE, target)
    return target


def _set_path(document: Path, route_id: str, path: str) -> bytes:
    payload = json.loads(document.read_bytes())
    route = next(item for item in payload["routes"] if item["id"] == route_id)
    route["path"] = path
    return _write_routes(document, payload["routes"])


def _observe(document: Path) -> dict:
    """Independent bounded read in the prior handoff experiment's shape."""
    data = document.read_bytes()
    record = {
        "target": str(document), "method": OBSERVER, "revision": _sha(data),
        "source_locator": f"bytes:0:{len(data)}", "retained_bytes": data,
        "routes": {}, "spans": {},
    }
    try:
        routes, spans = _supported_routes(data)
    except (ValueError, KeyError, TypeError, ConstructionError) as exc:
        return {**record, "status": "UNSUPPORTED", "error": str(exc)}
    return {**record, "status": "OK", "error": None, "routes": routes, "spans": spans}


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


def _live_handoff(observation: dict, document: Path) -> dict:
    """Pre-read eligibility only; it cannot bind the producer's later read."""
    if observation["target"] != str(document) or observation["method"] != OBSERVER:
        return {"eligible": False, "reason": "wrong observation target or method"}
    retained = observation.get("retained_bytes")
    if (observation["status"] != "OK" or not isinstance(retained, bytes)
            or _sha(retained) != observation["revision"]):
        return {"eligible": False, "reason": "no valid reconstructible observation"}
    try:
        now = _sha(document.read_bytes())
    except OSError:
        return {"eligible": False, "reason": "current target unavailable"}
    if now != observation["revision"]:
        return {"eligible": False, "reason": "source changed since observation",
                "observed_revision": observation["revision"], "current_revision": now}
    return {"eligible": True, "mode": "live-current", "revision": now,
            "expected_revision": now, "source_bytes": retained}


def _consumed_revision(produced: ProducedRoutes) -> str:
    """The revision actually consumed, read from producer output only."""
    revisions = {route.document_observation.source_revision.removeprefix("sha256:")
                 for route in produced.routes}
    assert len(revisions) == 1
    (consumed,) = revisions
    assert produced.snapshot_id == f"snapshot:{consumed[:32]}"
    assert consumed in produced.blobs
    return consumed


def _discard(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _live_current_construct(document: Path, staging: Path, *, expected_revision: str) -> dict:
    """Experimental live-current intake over the unmodified path-only producer.

    The digest check runs against the revision the producer actually consumed,
    before any candidate is treated as success. A mismatch discards staging as
    temporary work, not a valid candidate.
    """
    _discard(staging)
    produced = produce_routes(staging, document)
    consumed = _consumed_revision(produced)
    if consumed != expected_revision:
        _discard(staging)
        return {"outcome": "REFUSED", "mode": "live-current", "intake": INTAKE,
                "expected_revision": expected_revision, "consumed_revision": consumed,
                "produced": None, "staging": None}
    return {"outcome": "CONSUMED", "mode": "live-current", "intake": INTAKE,
            "expected_revision": expected_revision, "consumed_revision": consumed,
            "produced": produced, "staging": staging}


def _retained_historical_construct(workdir: Path, observation: dict, *, live: Path) -> dict:
    """Experimental retained-historical intake; the live path is never rewritten."""
    workdir.mkdir(parents=True, exist_ok=True)
    retained = observation.get("retained_bytes")
    declared = observation.get("revision")
    if (observation.get("status") != "OK" or not isinstance(retained, bytes)
            or not isinstance(declared, str) or _sha(retained) != declared):
        return {"outcome": "REFUSED", "mode": "retained-historical", "intake": INTAKE,
                "reason": "retained bytes do not match declared digest",
                "produced": None, "staging": None}
    try:
        routes, spans = _supported_routes(retained)
    except (ValueError, KeyError, TypeError, ConstructionError) as exc:
        return {"outcome": "REFUSED", "mode": "retained-historical", "intake": INTAKE,
                "reason": f"retained evidence failed producer validation: {exc}",
                "produced": None, "staging": None}
    if observation.get("routes") != routes or observation.get("spans") != spans:
        return {"outcome": "REFUSED", "mode": "retained-historical", "intake": INTAKE,
                "reason": "handoff facts do not match retained evidence",
                "produced": None, "staging": None}
    snapshot = workdir / f"retained-{declared}.json"
    snapshot.write_bytes(retained)
    assert _sha(snapshot.read_bytes()) == declared
    staging = workdir / "staging"
    produced = produce_routes(staging, snapshot)
    consumed = _consumed_revision(produced)
    assert consumed == declared
    assert produced.blobs[declared] == retained
    try:
        live_revision = _sha(live.read_bytes())
    except OSError:
        live_revision = "UNAVAILABLE"
    return {"outcome": "CONSUMED", "mode": "retained-historical", "intake": INTAKE,
            "evidence_revision": declared, "consumed_revision": consumed,
            "live_revision_at_construction": live_revision,
            "produced": produced, "staging": staging}


def _seal_candidate(root: Path, staging: Path, produced: ProducedRoutes) -> Path:
    """Cheap fresh publication of a produced candidate for grounding checks."""
    root.mkdir(parents=True, exist_ok=True)
    blobs = dict(produced.blobs)
    evidence = _excerpt(GOVERNANCE, EXPORT, blobs)
    export = next(item for item in produced.routes if item.route_id == "customer-export")
    output = root / "world"
    result = construct_software_governance(
        software_world=staging,
        output=output, profile_id=PROFILE_ID, evidence_blobs=blobs,
        propositions=(PropositionSpec(
            proposition_id=EXPORT_ID, statement=EXPORT,
            domain_relation="customer_export_route", observations=(evidence,),
        ),),
        bindings=(BindingSpec(
            proposition_id=EXPORT_ID, software_subject=export.subject_id,
            support="SOURCE_EXPLICIT", endpoint_resolution="DETERMINISTIC",
            construction_method="intake-integrity fixture binding",
            observations=(evidence,), software_evidence=SOFTWARE_EVIDENCE,
        ),),
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
            basis="only intake-probe correspondences are recorded",
            known_gaps=("intake_probe_only",),
        ),
    )
    assert result.succeeded, result.errors
    return output


def _message(result: dict) -> str:
    if result["outcome"] == "REFUSED" and result.get("mode") == "live-current":
        return (
            f"Observed revision {result['expected_revision'][:12]} was replaced by "
            f"{result['consumed_revision'][:12]} before Construction read the source. "
            "Construction was refused."
        )
    if result["outcome"] == "CONSUMED" and result.get("mode") == "live-current":
        return (
            f"Observed revision {result['consumed_revision'][:12]} is still live. "
            "Construction consumed exactly that revision."
        )
    if result["outcome"] == "CONSUMED":
        return (
            f"Construction consumed retained historical revision "
            f"{result['consumed_revision'][:12]}. Current live source is "
            f"{result['live_revision_at_construction'][:12]}."
        )
    return f"Retained evidence was not accepted: {result.get('reason')}"


def _install_read_hook(monkeypatch: pytest.MonkeyPatch, document: Path, *,
                       after_first=None) -> tuple[list[bytes], dict]:
    """Count producer live-path reads; test-initiated reads stay uncounted.

    The returned guard disables counting around competing-actor writes and
    around the test's own post-construction reads, so ``calls`` holds exactly
    the bytes the producer acquired from the live path.
    """
    original = Path.read_bytes
    calls: list[bytes] = []
    guard = {"enabled": True}

    def hooked(self: Path, *args, **kwargs) -> bytes:
        data = original(self, *args, **kwargs)
        if self == document and guard["enabled"]:
            calls.append(data)
            if after_first is not None and len(calls) == 1:
                guard["enabled"] = False
                try:
                    after_first()
                finally:
                    guard["enabled"] = True
        return data

    monkeypatch.setattr(Path, "read_bytes", hooked)
    return calls, guard


def _grounding_revisions(database: Path) -> set[str]:
    """Every source_revision grounding the staging candidate's route facts."""
    world = ConstructionWorld.open(database, read_only=True)
    try:
        revisions = set()
        store = world._inner._store
        for relation in ("config_member", "config_route"):
            for row in world.relation_rows(relation):
                assertion_id = store.assertion_id_for_tuple(relation, dict(row))
                warrant = world.warrant_for_assertion(assertion_id)
                for base in warrant["bases"]:
                    detail = base.get("detail")
                    if not isinstance(detail, dict):
                        continue
                    for item in detail.get("observations") or []:
                        revisions.add(str(item["source_revision"]))
        return revisions
    finally:
        world.close()


def test_producer_acquires_source_in_one_read(tmp_path, monkeypatch):
    document = _file(tmp_path)
    expected = document.read_bytes()
    calls, guard = _install_read_hook(monkeypatch, document)
    produced = produce_routes(tmp_path / "staging", document)
    guard["enabled"] = False
    assert len(calls) == 1 and calls[0] == expected
    digest = _sha(expected)
    assert _consumed_revision(produced) == digest
    assert produced.blobs[digest] == expected
    for route in produced.routes:
        start, end = _object_span(expected, route.route_id)
        assert route.document_observation.native_location == f"bytes:{start}:{end}"
        assert route.document_observation.source_revision == f"sha256:{digest}"
        assert route.subject_id == f"route:{digest[:16]}:{route.route_id}"
        assert expected[start:end].decode().find(route.path) >= 0
    world = ConstructionWorld.open(tmp_path / "staging" / "world.sqlite", read_only=True)
    try:
        rows = {row["record_id"]: row for row in world.relation_rows("config_route")}
        assert rows["customer-export"]["path"] == "/customers/export"
        assert rows["health"]["path"] == "/health"
    finally:
        world.close()
    assert _grounding_revisions(tmp_path / "staging" / "world.sqlite") == {f"sha256:{digest}"}


def test_raw_producer_silently_consumes_superseding_revision(tmp_path):
    """Control: the accepted path-only producer checks no expected revision."""
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    handoff = _live_handoff(_observe(document), document)
    assert handoff["eligible"] and handoff["expected_revision"] == r1
    _set_path(document, "customer-export", "/other/export")
    r2 = _sha(document.read_bytes())
    assert r2 != r1
    produced = produce_routes(tmp_path / "staging", document)
    assert _consumed_revision(produced) == r2
    export = next(item for item in produced.routes if item.route_id == "customer-export")
    assert export.path == "/other/export"


def test_live_current_refuses_pre_read_race_and_discards_staging(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    observation = _observe(document)
    r1 = observation["revision"]
    assert _live_handoff(observation, document)["eligible"]
    _set_path(document, "customer-export", "/other/export")
    r2 = _sha(document.read_bytes())
    staging = tmp_path / "staging"
    result = _live_current_construct(document, staging, expected_revision=r1)
    assert result["outcome"] == "REFUSED"
    assert result["expected_revision"] == r1 and result["consumed_revision"] == r2
    assert result["produced"] is None and result["staging"] is None
    assert not staging.exists() and list(tmp_path.rglob("world.sqlite")) == []
    assert _sha(document.read_bytes()) == r2
    assert _message(result) == (
        f"Observed revision {r1[:12]} was replaced by {r2[:12]} before "
        "Construction read the source. Construction was refused."
    )


def test_live_current_consumes_revision_still_live(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    result = _live_current_construct(document, tmp_path / "staging", expected_revision=r1)
    assert result["outcome"] == "CONSUMED" and result["consumed_revision"] == r1
    produced = result["produced"]
    export = next(item for item in produced.routes if item.route_id == "customer-export")
    assert export.path == "/internal/export"
    assert _grounding_revisions(result["staging"] / "world.sqlite") == {f"sha256:{r1}"}
    assert _message(result) == (
        f"Observed revision {r1[:12]} is still live. "
        "Construction consumed exactly that revision."
    )


def test_post_acquisition_mutation_cannot_reach_candidate(tmp_path, monkeypatch):
    """R2 written the moment after the producer's read still yields pure R1."""
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    calls, guard = _install_read_hook(
        monkeypatch, document,
        after_first=lambda: _set_path(document, "customer-export", "/other/export"),
    )
    result = _live_current_construct(document, tmp_path / "staging", expected_revision=r1)
    guard["enabled"] = False
    r2 = _sha(document.read_bytes())
    assert len(calls) == 1 and _sha(calls[0]) == r1 and r2 != r1
    assert result["outcome"] == "CONSUMED" and result["consumed_revision"] == r1
    export = next(item for item in result["produced"].routes
                  if item.route_id == "customer-export")
    assert export.path == "/internal/export"
    assert f"route:{r1[:16]}:customer-export" == export.subject_id


def test_mid_construction_mutations_cannot_mix_revisions(tmp_path, monkeypatch):
    """R1 acquisition, then R2 after the read and R3 during span location."""
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    calls, guard = _install_read_hook(
        monkeypatch, document,
        after_first=lambda: _set_path(document, "customer-export", "/other/export"),
    )
    original_span = produce_module._object_span
    spans = []

    def hooked_span(payload: bytes, route_id: str) -> tuple[int, int]:
        spans.append(route_id)
        if len(spans) == 1:
            guard["enabled"] = False
            try:
                _set_path(document, "customer-export", "/third/export")
            finally:
                guard["enabled"] = True
        return original_span(payload, route_id)

    monkeypatch.setattr(produce_module, "_object_span", hooked_span)
    result = _live_current_construct(document, tmp_path / "staging", expected_revision=r1)
    guard["enabled"] = False
    r3 = _sha(document.read_bytes())
    assert len(calls) == 1 and _sha(calls[0]) == r1
    assert r3 != r1 and b"/third/export" in document.read_bytes()
    assert result["outcome"] == "CONSUMED" and result["consumed_revision"] == r1
    produced = result["produced"]
    assert produced.blobs[r1] == calls[0]
    for route in produced.routes:
        assert route.subject_id == f"route:{r1[:16]}:{route.route_id}"
        assert route.document_observation.source_revision == f"sha256:{r1}"
    export = next(item for item in produced.routes if item.route_id == "customer-export")
    assert export.path == "/internal/export"
    assert _grounding_revisions(result["staging"] / "world.sqlite") == {f"sha256:{r1}"}


def test_retained_historical_consumes_r1_while_live_is_r2(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    observation = _observe(document)
    r1 = observation["revision"]
    _set_path(document, "customer-export", "/other/export")
    r2 = _sha(document.read_bytes())
    assert r2 != r1
    result = _retained_historical_construct(tmp_path / "work", observation, live=document)
    assert result["outcome"] == "CONSUMED" and result["consumed_revision"] == r1
    assert result["evidence_revision"] == r1
    assert result["live_revision_at_construction"] == r2
    assert _sha(document.read_bytes()) == r2
    export = next(item for item in result["produced"].routes
                  if item.route_id == "customer-export")
    assert export.path == "/internal/export"
    assert _message(result) == (
        f"Construction consumed retained historical revision {r1[:12]}. "
        f"Current live source is {r2[:12]}."
    )


def test_retained_grounding_reconstructs_without_live_source(tmp_path):
    """Fresh read-only verification uses retained blobs, never the live file."""
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    observation = _observe(document)
    r1 = observation["revision"]
    _set_path(document, "customer-export", "/other/export")
    result = _retained_historical_construct(tmp_path / "work", observation, live=document)
    assert result["outcome"] == "CONSUMED"
    publication = _seal_candidate(tmp_path / "pub", result["staging"], result["produced"])
    document.unlink()
    assert not document.exists()
    view = open_governance_world(publication)
    try:
        subjects = {row["subject"]: row for row in view.world.relation_rows("software_subject")}
        assert subjects
        snapshots = {row["snapshot"] for row in subjects.values()}
        assert snapshots == {f"snapshot:{r1[:32]}"}
        for subject in subjects:
            manifestation = view.local_manifestation_for_subject(subject)
            assert manifestation["status"] == "OK"
        export = next(s for s, row in subjects.items() if s.endswith("customer-export"))
        world = view.world
        assertion_id = world._inner._store.assertion_id_for_tuple(
            "software_subject", dict(next(row for row in world.relation_rows("software_subject")
                                          if row["subject"] == export)))
        warrant = world.warrant_for_assertion(assertion_id)
        texts = []
        for base in warrant["bases"]:
            for item in (base.get("detail") or {}).get("observations") or []:
                text, status = reconstruct_governance_observation(world, item)
                assert status == "OK"
                texts.append(text)
        assert any("/internal/export" in text for text in texts)
        assert all("/other/export" not in text for text in texts)
    finally:
        view.world.close()


def test_producer_signature_needs_a_path_while_output_ignores_which_path(tmp_path):
    assert list(inspect.signature(produce_routes).parameters) == ["world_dir", "document"]
    with pytest.raises(Exception):
        produce_routes(tmp_path / "staging", b"not a path")  # type: ignore[arg-type]
    document_a = _file(tmp_path)
    _set_path(document_a, "customer-export", "/internal/export")
    document_b = tmp_path / "other-name.json"
    document_b.write_bytes(document_a.read_bytes())
    first = produce_routes(tmp_path / "staging-a", document_a)
    second = produce_routes(tmp_path / "staging-b", document_b)
    assert first.snapshot_id == second.snapshot_id
    assert first.routes == second.routes
    assert first.blobs == second.blobs


def test_handoff_facts_never_replace_producer_parsing(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    observation = _observe(document)
    forged = {**observation, "routes": {"customer-export": {
        "path": "/forged", "handler": "Forged"}}}
    live = _live_handoff(observation, document)
    assert live["eligible"]
    result = _live_current_construct(
        document, tmp_path / "staging", expected_revision=live["expected_revision"])
    assert result["outcome"] == "CONSUMED"
    export = next(item for item in result["produced"].routes
                  if item.route_id == "customer-export")
    assert export.path == "/internal/export" != forged["routes"]["customer-export"]["path"]
    refused = _retained_historical_construct(tmp_path / "work", forged, live=document)
    assert refused["outcome"] == "REFUSED"
    assert refused["produced"] is None


def test_unsupported_source_form_rejected_on_both_paths(tmp_path):
    document = _file(tmp_path)
    compact = json.dumps(json.loads(document.read_bytes()),
                         separators=(",", ":")).encode()
    document.write_bytes(compact)
    revision = _sha(compact)
    assert json.loads(compact)["routes"]
    with pytest.raises(ConstructionError):
        produce_routes(tmp_path / "staging", document)
    retained = {"target": str(document), "method": OBSERVER, "status": "OK",
                "revision": revision, "source_locator": f"bytes:0:{len(compact)}",
                "retained_bytes": compact, "routes": {}, "spans": {}}
    refused = _retained_historical_construct(tmp_path / "work", retained, live=document)
    assert refused["outcome"] == "REFUSED"
    assert "producer validation" in refused["reason"]


def test_tampered_retained_evidence_refused(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    observation = _observe(document)
    r1 = observation["revision"]
    altered = observation["retained_bytes"].replace(b"/internal/export", b"/tampered/export")
    assert _sha(altered) != r1
    tampered = {**observation, "retained_bytes": altered}
    refused = _retained_historical_construct(tmp_path / "work", tampered, live=document)
    assert refused["outcome"] == "REFUSED"
    assert refused["produced"] is None
    assert "digest" in refused["reason"]
    mistimed = {**observation, "spans": {"customer-export": "bytes:0:1",
                                        "health": observation["spans"]["health"]}}
    refused_spans = _retained_historical_construct(tmp_path / "work-spans", mistimed,
                                                   live=document)
    assert refused_spans["outcome"] == "REFUSED"
    assert "handoff facts" in refused_spans["reason"]


def test_identical_bytes_at_another_path_are_equivalent_today(tmp_path):
    document_a = _file(tmp_path)
    _set_path(document_a, "customer-export", "/internal/export")
    r1 = _sha(document_a.read_bytes())
    document_b = tmp_path / "substitute.json"
    document_b.write_bytes(document_a.read_bytes())
    handoff = _live_handoff(_observe(document_a), document_a)
    assert handoff["eligible"]
    assert not _live_handoff(_observe(document_a), document_b)["eligible"]
    result = _live_current_construct(document_b, tmp_path / "staging",
                                     expected_revision=handoff["expected_revision"])
    assert result["outcome"] == "CONSUMED" and result["consumed_revision"] == r1
    export = next(item for item in result["produced"].routes
                  if item.route_id == "customer-export")
    assert export.path == "/internal/export"
    assert export.document_observation.native_handle == f"software.json@sha256:{r1}"


def test_candidate_grounding_names_consumed_revision_not_request(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    r2 = _set_path(document, "customer-export", "/other/export")
    r2_digest = _sha(r2)
    staging = tmp_path / "staging"
    produced = produce_routes(staging, document)  # wrapper bypassed on purpose
    assert _consumed_revision(produced) == r2_digest != r1
    assert _grounding_revisions(staging / "world.sqlite") == {f"sha256:{r2_digest}"}
    export = next(item for item in produced.routes if item.route_id == "customer-export")
    assert export.subject_id.startswith(f"route:{r2_digest[:16]}:")


def test_constructed_truth_survives_later_source_change(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    result = _live_current_construct(document, tmp_path / "staging", expected_revision=r1)
    assert result["outcome"] == "CONSUMED"
    _set_path(document, "customer-export", "/other/export")
    r2 = _sha(document.read_bytes())
    honestly_from_r1 = result["consumed_revision"] == r1
    still_aligned = result["consumed_revision"] == r2
    assert honestly_from_r1 and not still_aligned
    message = (
        f"Construction honestly consumed {r1[:12]}. The source changed to {r2[:12]} "
        "after acquisition, so the result is no longer source-aligned but still "
        "accurately records its evidence revision."
    )
    assert "no longer source-aligned but still accurately records" in message


def test_sealed_candidate_keeps_truth_while_losing_alignment(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    r1 = _sha(document.read_bytes())
    result = _live_current_construct(document, tmp_path / "staging", expected_revision=r1)
    assert result["outcome"] == "CONSUMED"
    publication = _seal_candidate(tmp_path / "pub", result["staging"], result["produced"])
    _set_path(document, "customer-export", "/other/export")
    r2 = _sha(document.read_bytes())
    view = open_governance_world(publication)
    try:
        snapshots = {str(row["snapshot"])
                     for row in view.world.relation_rows("software_subject")}
        assert snapshots == {f"snapshot:{r1[:32]}"}
        export = next(str(row["subject"]) for row in view.world.relation_rows("config_route")
                      if row["record_id"] == "customer-export")
        manifestation = view.local_manifestation_for_subject(export)
        assert manifestation["status"] == "OK"
        assert "/internal/export" in manifestation["content"]
    finally:
        view.world.close()
    assert r2 != r1


def test_same_revision_same_candidate_whichever_way_it_was_acquired(tmp_path):
    document = _file(tmp_path)
    _set_path(document, "customer-export", "/internal/export")
    observation = _observe(document)
    r1 = observation["revision"]
    live = _live_current_construct(document, tmp_path / "live", expected_revision=r1)
    _set_path(document, "customer-export", "/other/export")
    historical = _retained_historical_construct(tmp_path / "work", observation, live=document)
    assert live["outcome"] == "CONSUMED" and historical["outcome"] == "CONSUMED"
    assert live["produced"].snapshot_id == historical["produced"].snapshot_id
    assert live["produced"].routes == historical["produced"].routes
    assert live["produced"].blobs == historical["produced"].blobs
