"""Test-local pressure on a hypothetical persistent key for config.routes/v1.

Nothing here declares persistence for the accepted producer or changes a World.
The conditional key rule is deliberately explicit so key reuse can falsify it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ontology_author.software_governance import (
    BindingSpec, CompletenessSpec, ManifestationSpec, PropositionSpec,
    SoftwareSubjectSpec, construct_software_governance, open_governance_world,
)
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.runtime.world import ConstructionError
from profiles.software_governance_config_v0.build import (
    EXPORT, EXPORT_ID, GOVERNANCE, PROFILE_ID, SOFTWARE_EVIDENCE, _excerpt,
)
from profiles.software_governance_config_v0.produce import (
    CAPABILITY, KIND, SCHEME, VERSION, produce_routes,
)


METHOD = "config.routes.correspondence/v0 (test hypothesis)"
BASE = [
    {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
    {"id": "health", "path": "/health", "handler": "Health"},
]


def _route(route_id: str, path: str, handler: str) -> dict[str, str]:
    return {"id": route_id, "path": path, "handler": handler}


def _publish(root: Path, routes: list[dict], *, binding: bool = False,
             leading: str = "", omit_receipt: str | None = None) -> tuple[Path, Path]:
    """Use the accepted producer and Construction path at a fresh address."""
    root.mkdir(parents=True)
    document = root / "software.json"
    document.write_text(leading + json.dumps({"routes": routes}, indent=2) + "\n", encoding="utf-8")
    staging = root / "producer"
    produced = produce_routes(staging, document)
    blobs = dict(produced.blobs)
    evidence = _excerpt(GOVERNANCE, EXPORT, blobs)
    subjects = tuple(
        SoftwareSubjectSpec(
            subject_id=item.subject_id, snapshot_id=produced.snapshot_id,
            kind=KIND, capability=CAPABILITY, version=VERSION,
            observations=(item.document_observation,),
        ) for item in produced.routes if item.route_id != omit_receipt
    )
    manifestations = tuple(
        ManifestationSpec(
            subject_id=item.subject_id, scheme=SCHEME, location=item.location,
            capability=f"{CAPABILITY}/{VERSION}",
            observations=(item.manifestation_observation,),
        ) for item in produced.routes if item.route_id != omit_receipt
    )
    export = next((item for item in produced.routes if item.route_id == "customer-export"), None)
    bindings = (
        (BindingSpec(
            proposition_id=EXPORT_ID, software_subject=export.subject_id,
            support="SOURCE_EXPLICIT", endpoint_resolution="DETERMINISTIC",
            construction_method="explicit fixture governance binding",
            observations=(evidence,), software_evidence=SOFTWARE_EVIDENCE,
        ),) if binding and export is not None else ()
    )
    output = root / "world"
    result = construct_software_governance(
        software_world=staging, output=output, profile_id=PROFILE_ID,
        evidence_blobs=blobs,
        propositions=(PropositionSpec(
            proposition_id=EXPORT_ID, statement=EXPORT,
            domain_relation="customer_export_route", observations=(evidence,),
        ),),
        bindings=bindings, subjects=subjects, manifestations=manifestations,
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY, status="INCOMPLETE",
            universe=produced.snapshot_id,
            basis="only fixture-supplied governance bindings are recorded",
            known_gaps=("supplied_bindings_only",),
        ),
    )
    assert result.succeeded, result.errors
    assert result.world_dir == output
    return output, document


def _inventory(publication: Path, document: Path) -> dict:
    """Audit extraction and uniqueness separately from persistence.

    The source document is retained by this fixture; the World has no
    producer-declared completeness receipt for route enumeration.
    """
    source = document.read_bytes()
    payload = json.loads(source)
    records = payload.get("routes")
    if not isinstance(records, list) or not records:
        raise ValueError("route universe not completely parsed")
    keys = []
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("unsupported route key")
        if not isinstance(item.get("path"), str) or not isinstance(item.get("handler"), str):
            raise ValueError("unsupported route form")
        keys.append(item["id"])
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate stable-key candidate")

    view = open_governance_world(publication)
    try:
        routes = [dict(row) for row in view.world.relation_rows("config_route")]
        receipts = [dict(row) for row in view.world.relation_rows("software_subject")]
        members = [dict(row) for row in view.world.relation_rows("config_member")]
        expected_snapshot = "snapshot:" + hashlib.sha256(source).hexdigest()[:32]
        if len(routes) != len(records) or len(receipts) != len(records) or len(members) != len(records):
            raise ValueError("published route universe is incomplete")
        by_key = {str(row["record_id"]): row for row in routes}
        if set(by_key) != set(keys):
            raise ValueError("published keys differ from source")
        for record in records:
            row = by_key[record["id"]]
            if (row["path"], row["handler"]) != (record["path"], record["handler"]):
                raise ValueError("published route content differs from source")
        by_subject = {str(row["subject"]): row for row in receipts}
        if set(by_subject) != {str(row["subject"]) for row in routes}:
            raise ValueError("software subject receipt is missing")
        if {str(row["route"]) for row in members} != set(by_subject):
            raise ValueError("snapshot membership is missing")
        for receipt in receipts:
            if (receipt["kind"], receipt["capability"], receipt["version"], receipt["snapshot"]) != (
                KIND, CAPABILITY, VERSION, expected_snapshot,
            ):
                raise ValueError("producer contract or snapshot mismatch")
        return {"publication": str(publication), "snapshot": expected_snapshot,
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "subjects": {key: str(by_key[key]["subject"]) for key in keys},
                "count": len(records), "complete": True,
                "producer": f"{CAPABILITY}/{VERSION}"}
    finally:
        view.world.close()


def _compare(prior: tuple[Path, Path], current: tuple[Path, Path], *,
             source_persistence_contract: bool = False,
             expected_producer_version: str = VERSION) -> dict:
    """A conditional key rule, never an accepted producer implementation."""
    result = {"method": METHOD,
              "prior_publication": str(prior[0]), "current_publication": str(current[0]),
              "basis": "CURRENT_OBSERVATION_ONLY", "pairs": [],
              "no_prior": [], "no_current": [], "state": "UNRESOLVED"}
    try:
        before = _inventory(*prior)
        after = _inventory(*current)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        result.update(state="INVALID_OR_INCOMPLETE", reason=str(exc))
        return result
    result.update(prior_snapshot=before["snapshot"], current_snapshot=after["snapshot"],
                  prior_source_sha256=before["source_sha256"],
                  current_source_sha256=after["source_sha256"],
                  producer=before["producer"], subject_kind=KIND,
                  key_scheme="record_id", comparison_scope="all observed routes")
    if expected_producer_version != VERSION or before["producer"] != after["producer"]:
        result["reason"] = "producer version incompatibility"
        return result
    if not source_persistence_contract:
        result["reason"] = "source and producer declare no persistent key semantics"
        return result
    old, new = before["subjects"], after["subjects"]
    result.update(
        basis="CONDITIONAL_PRODUCER_ESTABLISHED",
        source_contract="hypothetical: record_id is unique, persistent, and never reused",
        state="COVERED",
        pairs=[{"key": key, "prior_subject": old[key], "current_subject": new[key]}
               for key in sorted(old.keys() & new.keys())],
        no_prior=sorted(new.keys() - old.keys()),
        no_current=sorted(old.keys() - new.keys()),
    )
    return result


def _verify_exact(result: dict, prior: tuple[Path, Path], current: tuple[Path, Path]) -> None:
    if result["method"] != METHOD:
        raise ValueError("comparison method mismatch")
    if result["prior_publication"] != str(prior[0]) or result["current_publication"] != str(current[0]):
        raise ValueError("publication address mismatch")
    before, after = _inventory(*prior), _inventory(*current)
    if (result.get("prior_snapshot"), result.get("current_snapshot")) != (before["snapshot"], after["snapshot"]):
        raise ValueError("snapshot mismatch")
    if (result.get("prior_source_sha256"), result.get("current_source_sha256")) != (
        before["source_sha256"], after["source_sha256"],
    ):
        raise ValueError("source revision mismatch")
    for pair in result["pairs"]:
        key = pair["key"]
        if pair["prior_subject"] != before["subjects"].get(key) or pair["current_subject"] != after["subjects"].get(key):
            raise ValueError("subject mismatch")


@pytest.mark.parametrize("name,current_routes,leading", [
    ("exact", BASE, ""),
    ("path", [_route("customer-export", "/internal/export", "CustomerExport"), BASE[1]], ""),
    ("handler", [_route("customer-export", "/customers/export", "OtherHandler"), BASE[1]], ""),
    ("reorder", [BASE[1], BASE[0]], ""),
    ("text_move", BASE, "\n\n"),
])
def test_conditional_key_rule_survives_content_and_location_changes(tmp_path, name, current_routes, leading):
    prior = _publish(tmp_path / "prior", BASE)
    current = _publish(tmp_path / "current", current_routes, leading=leading)
    actual = _compare(prior, current)
    assert actual["state"] == "UNRESOLVED"
    conditional = _compare(prior, current, source_persistence_contract=True)
    assert conditional["state"] == "COVERED"
    assert conditional["basis"] == "CONDITIONAL_PRODUCER_ESTABLISHED"
    assert {pair["key"] for pair in conditional["pairs"]} == {"customer-export", "health"}
    _verify_exact(conditional, prior, current)
    old_view, new_view = open_governance_world(prior[0]), open_governance_world(current[0])
    try:
        old = next(pair["prior_subject"] for pair in conditional["pairs"] if pair["key"] == "customer-export")
        new = next(pair["current_subject"] for pair in conditional["pairs"] if pair["key"] == "customer-export")
        old_m = old_view.local_manifestation_for_subject(old)
        new_m = new_view.local_manifestation_for_subject(new)
        assert old_m["status"] == new_m["status"] == "OK"
        if name in {"path", "handler"}:
            assert old_m["content_digest"] != new_m["content_digest"]
        else:
            assert old_m["content_digest"] == new_m["content_digest"]
        if name == "reorder":
            assert old_m["location"] != new_m["location"]
        if name == "text_move":
            assert old_m["location"] == new_m["location"]
            # Same JSON pointer, different source byte offset.
            needle = b'"id": "customer-export"'
            assert prior[1].read_bytes().find(needle) != current[1].read_bytes().find(needle)
    finally:
        old_view.world.close()
        new_view.world.close()


def test_conditional_complete_universe_licenses_scoped_addition_and_deletion(tmp_path):
    prior = _publish(tmp_path / "prior", BASE)
    current = _publish(tmp_path / "current", [BASE[0], _route("new", "/new", "New")])
    actual = _compare(prior, current)
    assert actual["no_prior"] == actual["no_current"] == []
    conditional = _compare(prior, current, source_persistence_contract=True)
    assert conditional["no_prior"] == ["new"]
    assert conditional["no_current"] == ["health"]
    assert [pair["key"] for pair in conditional["pairs"]] == ["customer-export"]
    _verify_exact(conditional, prior, current)


def test_duplicate_id_destroys_unique_pairing_and_exposes_producer_gap(tmp_path):
    prior = _publish(tmp_path / "prior", BASE)
    root = tmp_path / "duplicate"
    root.mkdir()
    document = root / "software.json"
    document.write_text(json.dumps({"routes": [BASE[0], _route("customer-export", "/other", "Other")]}, indent=2), encoding="utf-8")
    produced = produce_routes(root / "producer", document)
    assert len(produced.routes) == 2
    assert produced.routes[0].subject_id == produced.routes[1].subject_id
    assert produced.routes[0].document_observation == produced.routes[1].document_observation
    duplicate = _publish(tmp_path / "sealed_duplicate", [
        BASE[0], _route("customer-export", "/other", "Other"),
    ])
    assert (duplicate[0] / "world.sqlite").is_file()
    with pytest.raises(ValueError, match="duplicate"):
        _inventory(*duplicate)
    comparison = _compare(prior, duplicate, source_persistence_contract=True)
    assert comparison["state"] == "INVALID_OR_INCOMPLETE"
    assert comparison["pairs"] == comparison["no_current"] == []


@pytest.mark.parametrize("bad", [
    '{"routes": [',
    '{"routes": [{"id": 7, "path": "/x", "handler": "X"}]}',
    '{"routes": [{"id": "x", "handler": "X"}]}',
])
def test_malformed_or_unsupported_input_cannot_license_negative(tmp_path, bad):
    document = tmp_path / "software.json"
    document.write_text(bad, encoding="utf-8")
    with pytest.raises((ConstructionError, KeyError, ValueError, TypeError)):
        produce_routes(tmp_path / "producer", document)


def test_valid_compact_json_is_not_supported_by_current_source_locator(tmp_path):
    document = tmp_path / "software.json"
    document.write_text(json.dumps({"routes": BASE}, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(ConstructionError, match="not in the document bytes"):
        produce_routes(tmp_path / "producer", document)
    # A producer that cannot locate this valid form cannot claim a complete
    # route universe for it, regardless of the parsed JSON values.


def test_missing_published_receipt_and_wrong_version_are_unresolved(tmp_path):
    prior = _publish(tmp_path / "prior", BASE)
    incomplete = _publish(tmp_path / "incomplete", BASE, omit_receipt="health")
    bad = _compare(prior, incomplete, source_persistence_contract=True)
    assert bad["state"] == "INVALID_OR_INCOMPLETE"
    assert bad["pairs"] == bad["no_current"] == []
    compatible = _publish(tmp_path / "compatible", BASE)
    version = _compare(prior, compatible, source_persistence_contract=True,
                       expected_producer_version="v2")
    assert version["state"] == "UNRESOLVED"
    assert version["reason"] == "producer version incompatibility"


def test_key_reuse_falsifies_persistence_as_inference_from_existing_fields(tmp_path):
    prior = _publish(tmp_path / "prior", BASE)
    # Fixture intent: delete the original export route, then introduce an
    # unrelated route that reuses its id. Current source format permits this.
    current = _publish(tmp_path / "current", [
        _route("customer-export", "/unrelated/ping", "UnrelatedPing"), BASE[1],
    ])
    actual = _compare(prior, current)
    assert actual["state"] == "UNRESOLVED"
    conditional = _compare(prior, current, source_persistence_contract=True)
    assert any(pair["key"] == "customer-export" for pair in conditional["pairs"])
    # A declared no-reuse source contract would classify this fixture's
    # stated history as a violation. Fields alone cannot detect that history.
    assert conditional["source_contract"].endswith("never reused")


def test_exact_publication_identity_rejects_substitution(tmp_path):
    prior = _publish(tmp_path / "prior", BASE)
    current = _publish(tmp_path / "current", BASE)
    twin = _publish(tmp_path / "twin", BASE)
    result = _compare(prior, current, source_persistence_contract=True)
    _verify_exact(result, prior, current)
    assert prior[0] != twin[0]
    with pytest.raises(ValueError, match="publication address mismatch"):
        _verify_exact(result, twin, current)
    with pytest.raises(ValueError, match="publication address mismatch"):
        _verify_exact(result, current, prior)
    with pytest.raises(ValueError, match="source revision mismatch"):
        _verify_exact({**result, "prior_source_sha256": "0" * 64}, prior, current)
    with pytest.raises(ValueError, match="comparison method mismatch"):
        _verify_exact({**result, "method": "config.routes.correspondence/v2"}, prior, current)


def _product_read(prior: tuple[Path, Path], current: tuple[Path, Path], comparison: dict) -> dict:
    _verify_exact(comparison, prior, current)
    pair = next(item for item in comparison["pairs"] if item["key"] == "customer-export")
    before, after = open_governance_world(prior[0]), open_governance_world(current[0])
    try:
        return {
            "prior_publication": comparison["prior_publication"],
            "current_publication": comparison["current_publication"],
            "method": comparison["method"], "basis": comparison["basis"],
            "prior_subject": pair["prior_subject"], "current_subject": pair["current_subject"],
            "prior_manifestation": before.local_manifestation_for_subject(pair["prior_subject"]),
            "current_manifestation": after.local_manifestation_for_subject(pair["current_subject"]),
            "historical_governance": before.propositions_for_subject(pair["prior_subject"]),
            "current_governance": after.propositions_for_subject(pair["current_subject"]),
            "current_binding_absence_is_negative": after.absence_is_negative(pair["current_subject"]),
        }
    finally:
        before.world.close()
        after.world.close()


def test_governance_read_separates_historical_current_and_source_state(tmp_path):
    prior = _publish(tmp_path / "prior", BASE, binding=True)
    changed_routes = [_route("customer-export", "/internal/export", "OtherHandler"), BASE[1]]
    current_empty = _publish(tmp_path / "current_empty", changed_routes, binding=False)
    current_bound = _publish(tmp_path / "current_bound", changed_routes, binding=True)
    empty_comparison = _compare(prior, current_empty, source_persistence_contract=True)
    empty = _product_read(prior, current_empty, empty_comparison)
    assert empty["historical_governance"] == [EXPORT_ID]
    assert empty["current_governance"] == []
    assert empty["current_binding_absence_is_negative"] is False
    assert empty["prior_manifestation"]["content_digest"] != empty["current_manifestation"]["content_digest"]
    bound_comparison = _compare(prior, current_bound, source_persistence_contract=True)
    bound = _product_read(prior, current_bound, bound_comparison)
    assert bound["historical_governance"] == bound["current_governance"] == [EXPORT_ID]
    assert bound["prior_publication"] != bound["current_publication"]
    assert current_empty[1].read_bytes() == current_bound[1].read_bytes()
    assert current_empty[0] != current_bound[0]
    assert empty_comparison["current_source_sha256"] == bound_comparison["current_source_sha256"]
    assert empty["current_governance"] != bound["current_governance"]
