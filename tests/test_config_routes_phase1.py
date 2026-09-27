"""Phase 1 production acceptance for bounded config.routes/v1 Construction.

A fresh caller provides only workspace/source paths, profile choice, output
destination, and optional expected revisions. The profile derives IDs,
establishes semantics via versioned rules, and publishes a sealed World at
a fresh exclusive address with a machine-readable report.

These tests use temporary external workspaces only. They never import
fixture builders and never read the repository's fixed profile fixture
paths as inputs.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from ontology_author.config_routes import construct_config_world
from ontology_author.config_routes import producer as producer_module
from ontology_author.config_routes.producer import produce_routes
from ontology_author.config_routes.rules import PROFILE_ID
from ontology_author.software_governance import open_governance_world


def _write_software(path: Path, routes: list[dict], *, compact: bool = False) -> bytes:
    if compact:
        payload = json.dumps({"routes": routes}, separators=(",", ":")).encode()
    else:
        payload = (json.dumps({"routes": routes}, indent=2) + "\n").encode()
    path.write_bytes(payload)
    return payload


def _base_routes() -> list[dict]:
    return [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ]


def _write_governance(path: Path, *paragraphs: str) -> bytes:
    payload = ("\n\n".join(paragraphs) + "\n").encode()
    path.write_bytes(payload)
    return payload


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in sorted(root.rglob("*")):
        if item.is_file():
            out[str(item.relative_to(root))] = _sha(item.read_bytes())
    return out


def _route_subject(view, route_id: str) -> str:
    matches = [
        str(row["subject"])
        for row in view.world.relation_rows("config_route")
        if row["record_id"] == route_id
    ]
    assert len(matches) == 1
    return matches[0]


def test_happy_non_fixture_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    software = workspace / "software.json"
    governance = workspace / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance,
        "Customer export must use the approved customer-export route.",
        "Status checks must use an approved route.",
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    assert report.output == str(output.resolve())
    assert output.is_dir()
    assert (output / "world.sqlite").is_file()
    # Caller supplied no snapshot-local or proposition IDs.
    assert report.profile_id == PROFILE_ID
    assert report.consumed_software_revision
    assert report.consumed_governance_revision
    assert len(report.propositions) == 2
    assert len(report.subjects) == 2
    assert len(report.bindings) == 1
    assert report.coverage_status == "INCOMPLETE"
    assert "supplied_correspondences_only" in report.known_gaps
    # No fixture path dependency.
    assert "profiles/software_governance_config_v0" not in report.output
    assert str(workspace) in report.software_source["path"]
    view = open_governance_world(output)
    try:
        export = _route_subject(view, "customer-export")
        health = _route_subject(view, "health")
        assert view.propositions_for_subject(export) == [
            "proposition:customer-export-route"
        ]
        assert view.propositions_for_subject(health) == []
        assert view.absence_is_negative(health) is False
        binding = view.inspect_governance_binding(
            "proposition:customer-export-route", export
        )
        assert binding["endpoint_resolution"] == "DETERMINISTIC"
        assert binding["relation_support"] == "SOURCE_EXPLICIT"
        assert binding["establishment_rule"] == "config.routes.binding/v1"
        assert len(binding["evidence"]) == 2
        assert all(item["status"] == "OK" for item in binding["evidence"])
        texts = " ".join(item["text"] for item in binding["evidence"])
        assert "customer-export" in texts
        assert "Customer export must use" in texts
        assert "record_id=customer-export" in binding["software_evidence"]
        assert export in binding["software_evidence"]
        assert binding["subject_manifestation"]["status"] == "OK"
        proposition = view.inspect_governance_proposition(
            "proposition:customer-export-route"
        )
        assert proposition["establishment_rule"] == (
            "config.routes.proposition/v1:specific"
        )
    finally:
        view.world.close()
    # Sealed: no write bits on the final bundle.
    assert output.stat().st_mode & 0o222 == 0
    assert (output / "world.sqlite").stat().st_mode & 0o222 == 0


def test_compact_json_is_supported(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes(), compact=True)
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    report = construct_config_world(
        software_source=software, governance_source=governance, output=tmp_path / "W0"
    )
    assert report.succeeded, report.errors
    assert len(report.bindings) == 1


def test_duplicate_route_id_is_refused(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, [
        {"id": "customer-export", "path": "/a", "handler": "A"},
        {"id": "customer-export", "path": "/b", "handler": "B"},
    ])
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert "duplicate route id" in " ".join(report.errors).lower()
    assert not os.path.lexists(output)


@pytest.mark.parametrize("payload", [
    b'{"routes": "not-a-list"}',
    b'{"routes": []}',
    b'{"no_routes": []}',
    b'[]',
    b'{"routes": [{"id": "x", "path": "/x"}]}',
    b'{"routes": [{"id": "x", "path": "/x", "handler": 7}]}',
    b'{"routes": [{"id": "", "path": "/x", "handler": "X"}]}',
    b'{"routes": [{"path": "/x", "handler": "X"}]}',
    b'{"routes": ["not-an-object"]}',
    b'{"routes": [',
])
def test_unsupported_software_json_forms_are_refused(tmp_path: Path, payload: bytes) -> None:
    software = tmp_path / "software.json"
    software.write_bytes(payload)
    governance = tmp_path / "governance.md"
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert not os.path.lexists(output)


def test_software_directory_is_refused(tmp_path: Path) -> None:
    governance = tmp_path / "governance.md"
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    report = construct_config_world(
        software_source=tmp_path, governance_source=governance, output=tmp_path / "W0"
    )
    assert not report.succeeded
    assert not os.path.lexists(tmp_path / "W0")


def test_unsupported_governance_forms_are_refused(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    _write_software(software, _base_routes())
    # Non-Markdown suffix is refused even when the text would otherwise match.
    other = tmp_path / "governance.txt"
    other.write_text(
        "Customer export must use the approved customer-export route.\n"
    )
    report = construct_config_world(
        software_source=software, governance_source=other, output=tmp_path / "W0"
    )
    assert not report.succeeded
    assert "not markdown" in " ".join(report.errors).lower()
    assert not os.path.lexists(tmp_path / "W0")
    # Missing file and directory are refused.
    missing = construct_config_world(
        software_source=software,
        governance_source=tmp_path / "absent.md",
        output=tmp_path / "W1",
    )
    assert not missing.succeeded
    assert not os.path.lexists(tmp_path / "W1")
    directory = construct_config_world(
        software_source=software,
        governance_source=tmp_path,
        output=tmp_path / "W2",
    )
    assert not directory.succeeded
    assert not os.path.lexists(tmp_path / "W2")


def test_only_unsupported_governance_text_refuses(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    _write_software(software, _base_routes())
    governance = tmp_path / "governance.md"
    _write_governance(governance, "All systems must be secure.")
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert len(report.unsupported) == 1
    assert not os.path.lexists(output)


def test_supported_plus_unsupported_reports_gap(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    _write_software(software, _base_routes())
    governance = tmp_path / "governance.md"
    _write_governance(
        governance,
        "Customer export must use the approved customer-export route.",
        "All systems must be secure.",
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    assert len(report.propositions) == 1
    assert len(report.unsupported) == 1
    assert "unsupported_governance_statements" in report.known_gaps


def test_missing_binding_endpoint_yields_question_not_binding(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    _write_software(software, _base_routes())
    governance = tmp_path / "governance.md"
    _write_governance(
        governance, "Reports must use the approved reports-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    assert report.bindings == ()
    assert len(report.questions) == 1
    assert report.questions[0]["state"] == "UNRESOLVED"
    assert "missing_route_reports_export" in report.known_gaps
    view = open_governance_world(output)
    try:
        assert list(view.world.relation_rows("governance_binding")) == []
        assert view.subjects_for_proposition("proposition:reports-export-route") == []
    finally:
        view.world.close()


def test_same_looking_route_does_not_bind(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    _write_software(software, [
        {"id": "customer-export-v2", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ])
    governance = tmp_path / "governance.md"
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    assert report.bindings == ()
    assert len(report.questions) == 1
    assert "missing_route_customer_export" in report.known_gaps


def test_ambiguous_generic_yields_candidates_without_binding(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    _write_software(software, _base_routes())
    governance = tmp_path / "governance.md"
    _write_governance(governance, "Status checks must use an approved route.")
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    assert report.bindings == ()
    assert len(report.candidates) == 2
    assert len(report.questions) == 1
    view = open_governance_world(output)
    try:
        proposition = report.propositions[0]["proposition"]
        assert view.subjects_for_proposition(proposition) == []
        detail = view.binding_candidates_for_proposition(proposition)
        assert len(detail["candidates"]) == 2
        assert {item["endpoint_resolution"] for item in detail["candidates"]} == {
            "AMBIGUOUS"
        }
        assert {item["relation_support"] for item in detail["candidates"]} == {
            "SOURCE_GENERIC"
        }
        assert all(
            item["establishment_rule"] == "config.routes.candidate/v1"
            for item in detail["candidates"]
        )
        assert all(len(item["evidence"]) == 2 for item in detail["candidates"])
        assert all(
            all(piece["status"] == "OK" for piece in item["evidence"])
            for item in detail["candidates"]
        )
    finally:
        view.world.close()


def test_expected_software_revision_mismatch_refuses(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    first = _write_software(software, _base_routes())
    r1 = _sha(first)
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    # Advance the live source to R2, then promise R1.
    _write_software(software, [
        {"id": "customer-export", "path": "/other/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ])
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software,
        governance_source=governance,
        output=output,
        expected_software_revision=r1,
    )
    assert not report.succeeded
    assert report.expected_software_revision == r1
    assert report.consumed_software_revision != r1
    assert not os.path.lexists(output)
    # The live R2 promise succeeds and consumes exactly R2.
    r2 = _sha(software.read_bytes())
    assert r2 != r1
    good = construct_config_world(
        software_source=software,
        governance_source=governance,
        output=output,
        expected_software_revision=f"sha256:{r2}",
    )
    assert good.succeeded, good.errors
    assert good.consumed_software_revision == r2


def test_expected_governance_revision_mismatch_refuses(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes())
    first = _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    r1 = _sha(first)
    _write_governance(
        governance, "Customer export must use the approved health route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software,
        governance_source=governance,
        output=output,
        expected_governance_revision=r1,
    )
    assert not report.succeeded
    assert report.consumed_governance_revision != r1
    assert not os.path.lexists(output)


def test_producer_reads_software_once_and_compares_consumed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    software = tmp_path / "software.json"
    payload = _write_software(software, _base_routes())
    original = Path.read_bytes
    calls: list[bytes] = []

    def hooked(self: Path, *args, **kwargs) -> bytes:
        data = original(self, *args, **kwargs)
        if self == software:
            calls.append(data)
        return data

    monkeypatch.setattr(Path, "read_bytes", hooked)
    produced = produce_routes(tmp_path / "staging", software)
    assert len(calls) == 1
    assert calls[0] == payload
    assert produced.consumed_revision == _sha(payload)


def test_post_acquisition_mutation_cannot_reach_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    first = _write_software(software, _base_routes())
    r1 = _sha(first)
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    original = Path.read_bytes
    calls: list[bytes] = []
    guard = {"enabled": True}

    def hooked(self: Path, *args, **kwargs) -> bytes:
        data = original(self, *args, **kwargs)
        if self == software and guard["enabled"]:
            calls.append(data)
            if len(calls) == 1:
                guard["enabled"] = False
                try:
                    _write_software(software, [
                        {"id": "customer-export", "path": "/other/export",
                         "handler": "CustomerExport"},
                        {"id": "health", "path": "/health", "handler": "Health"},
                    ])
                finally:
                    guard["enabled"] = True
        return data

    monkeypatch.setattr(Path, "read_bytes", hooked)
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software,
        governance_source=governance,
        output=output,
        expected_software_revision=r1,
    )
    guard["enabled"] = False
    assert len(calls) == 1
    assert _sha(calls[0]) == r1
    assert report.succeeded, report.errors
    assert report.consumed_software_revision == r1
    assert _sha(software.read_bytes()) != r1


def test_publication_address_already_exists(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    payload = _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    first = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert first.succeeded, first.errors
    before = _hash_tree(output)
    second = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not second.succeeded
    assert "already exists" in " ".join(second.errors).lower()
    assert _hash_tree(output) == before
    assert _sha(software.read_bytes()) == _sha(payload)
    # A pre-existing file (not directory) is also refused without overwrite.
    blocker = tmp_path / "blocker"
    blocker.write_text("do not overwrite", encoding="utf-8")
    third = construct_config_world(
        software_source=software, governance_source=governance, output=blocker
    )
    assert not third.succeeded
    assert blocker.read_text(encoding="utf-8") == "do not overwrite"


def test_exclusive_publish_refuses_empty_directory(tmp_path: Path) -> None:
    from ontology_author.software_governance import construction as construction_module

    software = tmp_path / "software.json"
    _write_software(software, _base_routes())
    staging = tmp_path / "staging"
    produced = produce_routes(staging, software)
    assert produced.routes
    dest = tmp_path / "W0"
    dest.mkdir()
    with pytest.raises(FileExistsError):
        construction_module._exclusive_rename(staging, dest)
    assert dest.is_dir()
    assert list(dest.iterdir()) == []
    assert staging.is_dir()


def test_publication_order_seals_before_exclusive_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ontology_author.software_governance.construction as construction_module

    calls: list[str] = []
    original_seal = construction_module._seal_world
    original_rename = construction_module._exclusive_rename

    def hooked_seal(work: Path) -> None:
        calls.append("seal")
        original_seal(work)

    def hooked_rename(source: Path, dest: Path) -> None:
        calls.append("rename")
        assert os.path.lexists(dest) is False
        original_rename(source, dest)

    monkeypatch.setattr(construction_module, "_seal_world", hooked_seal)
    monkeypatch.setattr(construction_module, "_exclusive_rename", hooked_rename)
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    report = construct_config_world(
        software_source=software, governance_source=governance, output=tmp_path / "W0"
    )
    assert report.succeeded, report.errors
    assert calls == ["seal", "rename"]


def test_validation_failure_leaves_no_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ontology_author.software_governance.construction as construction_module

    monkeypatch.setattr(
        construction_module,
        "validate_governance_world",
        lambda world: ["injected validation failure"],
    )
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert "injected validation failure" in " ".join(report.validation_errors)
    assert not os.path.lexists(output)


def test_seal_failure_leaves_no_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ontology_author.software_governance.construction as construction_module

    def boom(work: Path) -> None:
        raise OSError("injected seal failure")

    monkeypatch.setattr(construction_module, "_seal_world", boom)
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert "injected seal failure" in " ".join(report.errors)
    assert not os.path.lexists(output)


def test_publication_failure_leaves_no_fake_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ontology_author.software_governance.construction as construction_module

    def boom(source: Path, dest: Path) -> None:
        raise OSError("injected publication failure")

    monkeypatch.setattr(construction_module, "_exclusive_rename", boom)
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert "injected publication failure" in " ".join(report.errors)
    assert not os.path.lexists(output)


def test_w0_survives_w1_construction_unchanged(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    software = workspace / "software.json"
    governance = workspace / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    w0 = tmp_path / "W0"
    first = construct_config_world(
        software_source=software, governance_source=governance, output=w0
    )
    assert first.succeeded, first.errors
    before = _hash_tree(w0)
    # Correct the governance source (no Python edit): same grammar, new endpoint.
    _write_governance(governance, "Health checks must use the approved health route.")
    w1 = tmp_path / "W1"
    second = construct_config_world(
        software_source=software, governance_source=governance, output=w1
    )
    assert second.succeeded, second.errors
    assert w1 != w0
    assert _hash_tree(w0) == before
    old = open_governance_world(w0)
    new = open_governance_world(w1)
    try:
        old_export = _route_subject(old, "customer-export")
        assert old.propositions_for_subject(old_export) == [
            "proposition:customer-export-route"
        ]
        old_binding = old.inspect_governance_binding(
            "proposition:customer-export-route", old_export
        )
        assert all(item["status"] == "OK" for item in old_binding["evidence"])
        new_health = _route_subject(new, "health")
        assert new.propositions_for_subject(new_health) == [
            "proposition:health-route"
        ]
        assert new.subjects_for_proposition("proposition:health-route") == [new_health]
        # W1 does not inherit the W0 binding.
        assert new.subjects_for_proposition("proposition:customer-export-route") == []
        assert new.propositions_for_subject(_route_subject(new, "customer-export")) == []
    finally:
        old.world.close()
        new.world.close()


def test_new_snapshot_does_not_inherit_old_binding(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    software = workspace / "software.json"
    governance = workspace / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    w0 = tmp_path / "W0"
    assert construct_config_world(
        software_source=software, governance_source=governance, output=w0
    ).succeeded
    # Remove the bound route. Same governance wording must not carry the binding.
    _write_software(software, [
        {"id": "health", "path": "/health", "handler": "Health"},
    ])
    w1 = tmp_path / "W1"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=w1
    )
    assert report.succeeded, report.errors
    assert report.bindings == ()
    assert "missing_route_customer_export" in report.known_gaps
    view = open_governance_world(w1)
    try:
        assert list(view.world.relation_rows("governance_binding")) == []
    finally:
        view.world.close()


def test_evaluator_coverage_is_explicit(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "orders-export", "path": "/orders/export", "handler": "OrdersExport"},
    ])
    _write_governance(
        governance,
        "Customer export must use the approved customer-export route.",
        "Orders export must use the approved orders-export route.",
    )
    report = construct_config_world(
        software_source=software, governance_source=governance, output=tmp_path / "W0"
    )
    assert report.succeeded, report.errors
    by_proposition = {entry["proposition"]: entry for entry in report.evaluator}
    covered = by_proposition["proposition:customer-export-route"]
    assert covered["status"] == "covered"
    assert covered["method_id"] == "config.customer_export_route"
    assert covered["version"] == "v0"
    assert covered["rule"]["required_path"] == "/customers/export"
    missing = by_proposition["proposition:orders-export-route"]
    assert missing["status"] == "unsupported"
    assert missing["gap"] == "evaluator_rule_not_declared"
    assert "evaluator_rule_not_declared" in report.known_gaps


def test_published_inventory_matches_parsed_source(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    routes = _base_routes()
    _write_software(software, routes)
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    view = open_governance_world(output)
    try:
        published = {
            str(row["record_id"]): (str(row["path"]), str(row["handler"]))
            for row in view.world.relation_rows("config_route")
        }
        assert published == {
            item["id"]: (item["path"], item["handler"]) for item in routes
        }
        receipts = list(view.world.relation_rows("software_subject"))
        members = list(view.world.relation_rows("config_member"))
        assert len(receipts) == len(routes)
        assert len(members) == len(routes)
    finally:
        view.world.close()


def _software_evidence_texts(view, proposition: str, subject: str) -> list[str]:
    binding = view.inspect_governance_binding(proposition, subject)
    return [
        item["text"]
        for item in binding["evidence"]
        if "software.json@" in item["native_handle"]
    ]


@pytest.mark.parametrize("paragraph", [
    "Customer export must use the approved foo route. Health must use the approved bar route.",
    "A must use the approved B must use the approved foo route.",
    "Customer export must use the approved foo route. Status checks must use an approved route.",
    "Status checks must use an approved route. Customer export must use the approved foo route.",
    "Is this the route? Customer export must use the approved foo route.",
])
def test_multi_requirement_paragraphs_fail_closed(tmp_path: Path, paragraph: str) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, [
        {"id": "foo", "path": "/foo", "handler": "Foo"},
        {"id": "bar", "path": "/bar", "handler": "Bar"},
    ])
    _write_governance(
        governance,
        "Health checks must use the approved bar route.",
        paragraph,
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    # Only the valid paragraph yields a proposition; the multi-requirement
    # paragraph is reported unsupported, never split or swallowed.
    assert len(report.propositions) == 1
    assert report.propositions[0]["proposition"] == "proposition:bar-route"
    assert len(report.unsupported) == 1
    assert "unsupported_governance_statements" in report.known_gaps
    assert [(b["proposition"], b["route_id"]) for b in report.bindings] == [
        ("proposition:bar-route", "bar")
    ]
    view = open_governance_world(output)
    try:
        statements = {
            str(row["statement"])
            for row in view.world.relation_rows("governance_proposition")
        }
        assert paragraph not in statements
        assert len(statements) == 1
    finally:
        view.world.close()


def test_only_multi_requirement_paragraph_refuses(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, [
        {"id": "foo", "path": "/foo", "handler": "Foo"},
        {"id": "bar", "path": "/bar", "handler": "Bar"},
    ])
    _write_governance(
        governance,
        "Customer export must use the approved foo route. Health must use the approved bar route.",
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert len(report.unsupported) == 1
    assert not os.path.lexists(output)


@pytest.mark.parametrize("compact", [False, True])
def test_accepted_spans_enclose_route_identity(tmp_path: Path, compact: bool) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    routes = _base_routes()
    payload = _write_software(software, routes, compact=compact)
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    view = open_governance_world(output)
    try:
        export = _route_subject(view, "customer-export")
        texts = _software_evidence_texts(
            view, "proposition:customer-export-route", export
        )
        assert len(texts) == 1
        assert '"customer-export"' in texts[0]
        assert "/customers/export" in texts[0]
    finally:
        view.world.close()
    assert b'"customer-export"' in payload


def test_nested_object_before_id_fails_closed(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    software.write_bytes(
        b'{"routes": [{"meta": {"a": 1}, "id": "x", '
        b'"path": "/x", "handler": "X"}]}'
    )
    governance = tmp_path / "governance.md"
    _write_governance(governance, "Ex must use the approved x route.")
    output = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert not report.succeeded
    assert "span" in " ".join(report.errors).lower()
    assert not os.path.lexists(output)


def test_report_is_machine_readable_json(tmp_path: Path) -> None:
    software = tmp_path / "software.json"
    governance = tmp_path / "governance.md"
    _write_software(software, _base_routes())
    _write_governance(
        governance, "Customer export must use the approved customer-export route."
    )
    report = construct_config_world(
        software_source=software, governance_source=governance, output=tmp_path / "W0"
    )
    assert report.succeeded, report.errors
    payload = json.loads(report.to_json())
    for key in (
        "profile_id", "output", "software_source", "governance_source",
        "consumed_software_revision", "propositions", "subjects", "bindings",
        "candidates", "questions", "coverage_status", "known_gaps",
        "unsupported", "validation_errors",
    ):
        assert key in payload
