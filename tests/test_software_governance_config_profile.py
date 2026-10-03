"""Acceptance for governance over a non-spine route producer."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from profiles.software_governance_config_v0.build import (
    EXPORT,
    EXPORT_ID,
    STATUS_ID,
    build_config_profile,
)
from profiles.software_governance_config_v0.produce import KIND, SCHEME

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPOSITORY_ROOT / "ontology_author" / "software_governance"
DOCUMENT = REPOSITORY_ROOT / "profiles" / "software_governance_config_v0" / "software.json"


@pytest.fixture(scope="module")
def sealed(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("config-governance") / "world"
    result = build_config_profile(output)
    assert result.succeeded, result.errors
    assert result.world_dir == output
    return output


def _view(sealed: Path):
    return open_governance_world(sealed)


def _route(view, route_id: str) -> str:
    matches = [
        str(row["subject"])
        for row in view.world.relation_rows("config_route")
        if row["record_id"] == route_id
    ]
    assert len(matches) == 1
    return matches[0]


def test_generic_package_does_not_require_program_spine_relations() -> None:
    forbidden = (
        "program_entity",
        "program_snapshot",
        "program_entity_kind",
        "config:route",
        "customer-export",
        "config_route",
    )
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            if name in text:
                found.append(f"{path.name} contains {name}")
    profile = REPOSITORY_ROOT / "profiles" / "software_governance_config_v0"
    for path in sorted(profile.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                if module == "ontology_author.program_spine" or module.startswith(
                    "ontology_author.program_spine."
                ):
                    found.append(f"{path.name} imports {module}")
    assert found == []


def test_route_producer_needs_no_spine_relations(sealed: Path) -> None:
    view = _view(sealed)
    for relation in ("program_entity", "program_snapshot", "program_invokes", "program_entity_kind"):
        with pytest.raises(Exception):
            view.world.relation_schema(relation)
    export = _route(view, "customer-export")
    assert view.program_relations_for_subject(export)["invokes"] == []


def test_binding_selects_one_route_and_not_the_other(sealed: Path) -> None:
    view = _view(sealed)
    export = _route(view, "customer-export")
    health = _route(view, "health")
    assert view.propositions_for_subject(export) == [EXPORT_ID]
    assert view.propositions_for_subject(health) == []
    assert view.subjects_for_proposition(EXPORT_ID) == [export]
    assert view.inspect_governance_proposition(EXPORT_ID)["semantic_subject"] is None
    binding = view.inspect_governance_binding(EXPORT_ID, export)
    proposition = view.inspect_governance_proposition(EXPORT_ID)
    assert proposition["statement"] == EXPORT
    assert proposition["evidence"][0]["status"] == "OK"
    assert EXPORT in proposition["evidence"][0]["text"]
    assert binding["evidence"][0]["native_handle"] == proposition["evidence"][0]["native_handle"]
    assert binding["endpoint_resolution"] == "DETERMINISTIC"
    assert binding["relation_support"] == "SOURCE_EXPLICIT"
    assert binding["origin"] == "SEMANTIC"
    assert "config_route" not in binding["roles"]


def test_manifestation_is_canonical_record_not_token_range(sealed: Path) -> None:
    view = _view(sealed)
    export = _route(view, "customer-export")
    manifestation = view.local_manifestation_for_subject(export)
    document = DOCUMENT.read_bytes()
    assert manifestation["status"] == "OK"
    assert manifestation["scheme"] == SCHEME
    assert manifestation["scheme"] != "source-token-range"
    assert manifestation["content"] == (
        '{"handler":"CustomerExport","id":"customer-export","path":"/customers/export"}'
    )
    assert manifestation["location"] == "/routes/0"
    assert manifestation["location"] != manifestation["content_digest"]
    assert manifestation["content_digest"] != hashlib.sha256(document).hexdigest()
    assert manifestation["capability"] == "config.routes/v1"
    assert export != manifestation["content_digest"]
    assert export != manifestation["location"]
    receipt = [
        row for row in view.world.relation_rows("software_subject")
        if row["subject"] == export
    ]
    assert receipt[0]["kind"] == KIND


def test_mechanical_facts_are_route_properties(sealed: Path) -> None:
    view = _view(sealed)
    export = _route(view, "customer-export")
    facts = view.mechanical_facts_for_subject(export)
    routes = [fact for fact in facts if fact["relation"] == "config_route"]
    assert len(routes) == 1
    assert routes[0]["values"]["path"] == "/customers/export"
    assert routes[0]["values"]["handler"] == "CustomerExport"
    assert routes[0]["origin"] == ["MECHANICAL"]
    assert any(fact["relation"] == "config_member" for fact in facts)
    assert all(not fact["relation"].startswith("governance_") for fact in facts)
    assert all(fact["relation"] != "program_invokes" for fact in facts)


def test_ambiguous_routes_are_candidates_without_a_binding(sealed: Path) -> None:
    view = _view(sealed)
    report = view.binding_candidates_for_proposition(STATUS_ID)
    labels = {item["label"] for item in report["candidates"]}
    assert labels == {"customer-export", "health"}
    assert report["established_subjects"] == []
    assert report["questions"] == [{
        "state": "UNRESOLVED",
        "question": "Which route is the approved status route?",
    }]
    assert {item["endpoint_resolution"] for item in report["candidates"]} == {"AMBIGUOUS"}
    assert view.subjects_for_proposition(STATUS_ID) == []


def test_incomplete_coverage_is_mechanical_and_not_a_negative(sealed: Path) -> None:
    view = _view(sealed)
    health = _route(view, "health")
    assert view.propositions_for_subject(health) == []
    assert view.absence_is_negative(health) is False
    completeness = view.completeness()
    assert completeness[0]["status"] == "INCOMPLETE"
    assert completeness[0]["origin"] == "MECHANICAL"
    assert completeness[0]["known_gaps"] == ["supplied_correspondences_only"]
    assert completeness[0]["known_gap_origins"]["supplied_correspondences_only"] == "MECHANICAL"
    export = view.inspect_governance_proposition(EXPORT_ID)
    assert export["origin"] == "SEMANTIC"
