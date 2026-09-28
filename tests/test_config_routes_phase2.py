"""Phase 2 production acceptance: Inspect + guarded Judge.

A fresh reader with only an exact sealed Phase 1 World must discover the
interpreted specification and ask one supported, inspectable Judgment.
Cold tests below use only the product facade and an address string; no
fixture, builder, evaluator-module, or orchestration knowledge.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ontology_author.config_routes import (
    construct_config_world,
    inspect_binding,
    inspect_config_world,
    inspect_proposition,
    inspect_subject,
    judge_config_world,
    read_judgment_bundle,
    verify_judgment_bundle,
)
from ontology_author.config_routes.evaluate import evaluate_route_case
from ontology_author.config_routes.judge import _explain_unknowns
from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.judgment import assemble_case

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPORT = "proposition:customer-export-route"


def _write_software(path: Path, routes: list[dict]) -> None:
    path.write_text(json.dumps({"routes": routes}, indent=2) + "\n", encoding="utf-8")


def _write_governance(path: Path, *paragraphs: str) -> None:
    path.write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")


def _base_routes() -> list[dict]:
    return [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ]


def _construct(tmp_path: Path, routes=None, paragraphs=None, name="W0") -> Path:
    workspace = tmp_path / f"workspace-{name}"
    workspace.mkdir(exist_ok=True)
    software = workspace / "software.json"
    governance = workspace / "governance.md"
    _write_software(software, routes if routes is not None else _base_routes())
    _write_governance(governance, *(paragraphs if paragraphs is not None else (
        "Customer export must use the approved customer-export route.",
        "Status checks must use an approved route.",
    )))
    output = tmp_path / name
    report = construct_config_world(
        software_source=software, governance_source=governance, output=output
    )
    assert report.succeeded, report.errors
    # The product handoff is the address string only; drop the report.
    del report
    return output


def _subject_for_world(world: Path, route_id: str) -> str:
    inventory = inspect_config_world(world)
    matches = [s["subject"] for s in inventory["subjects"] if s.get("route_id") == route_id]
    assert len(matches) == 1
    return matches[0]


def test_cold_reader_discovers_world_from_address_only(tmp_path: Path) -> None:
    address = str(_construct(tmp_path))
    inventory = inspect_config_world(address)
    assert inventory["address"] == str(Path(address).resolve())
    assert inventory["profile_id"] == "config.routes/v1"
    assert len(inventory["subjects"]) == 2
    assert len(inventory["propositions"]) == 2
    assert len(inventory["bindings"]) == 1
    assert len(inventory["candidates"]) == 2
    assert len(inventory["questions"]) == 1
    assert inventory["coverage"][0]["status"] == "INCOMPLETE"
    assert inventory["software_revisions"] and inventory["governance_revisions"]
    export = next(s["subject"] for s in inventory["subjects"] if s.get("route_id") == "customer-export")

    proposition = inspect_proposition(address, EXPORT)
    assert proposition["statement"] == "Customer export must use the approved customer-export route."
    assert all(item["status"] == "OK" for item in proposition["evidence"])
    assert proposition["establishment_rule"] == "config.routes.proposition/v1:specific"
    assert proposition["bound_subjects"] == [export]
    assert proposition["evaluator"]["status"] == "covered"
    assert proposition["evaluator"]["method_id"] == "config.customer_export_route"

    generic_id = next(p["proposition"] for p in inventory["propositions"] if p["proposition"] != EXPORT)
    generic = inspect_proposition(address, generic_id)
    assert generic["bound_subjects"] == []
    assert len(generic["candidates"]) == 2
    assert generic["questions"][0]["state"] == "UNRESOLVED"
    assert generic["evaluator"]["status"] == "unsupported"

    subject = inspect_subject(address, export)
    assert subject["kind"] == "config:route"
    assert subject["producer"] == "config.routes/v1"
    assert any(f["relation"] == "config_route" for f in subject["mechanical_facts"])
    assert subject["manifestation"]["status"] == "OK"
    assert subject["bound_propositions"] == [EXPORT]
    assert "snapshot-local" in subject["identity_scope"]

    binding = inspect_binding(address, EXPORT, export)
    assert len(binding["evidence"]) == 2
    assert all(item["status"] == "OK" for item in binding["evidence"])
    assert "customer-export" in " ".join(item["text"] for item in binding["evidence"])
    assert binding["establishment_rule"] == "config.routes.binding/v1"
    assert binding["relation_support"] == "SOURCE_EXPLICIT"


_COLD_PROBE = '''\
import json
import sys
from ontology_author.config_routes import (
    inspect_binding,
    inspect_config_world,
    inspect_proposition,
    judge_config_world,
)

mode, address = sys.argv[1], sys.argv[2]
inventory = inspect_config_world(address)
export = next(s["subject"] for s in inventory["subjects"] if s.get("route_id") == "customer-export")
proposition = inspect_proposition(address, "proposition:customer-export-route")
binding = inspect_binding(address, "proposition:customer-export-route", export)
payload = {
    "subjects": len(inventory["subjects"]),
    "propositions": len(inventory["propositions"]),
    "evidence_ok": all(item["status"] == "OK" for item in binding["evidence"]),
    "evaluator": proposition["evaluator"]["status"],
}
if mode == "judge":
    result = judge_config_world(world=address, proposition="proposition:customer-export-route", subject=export)
    payload["outcome"] = result["outcome"]
    payload["applicability"] = result["artifact"]["applicability"]["result"]
    payload["conformance"] = result["artifact"]["conformance"]["result"]
print(json.dumps(payload))
'''


def _run_cold_probe(tmp_path: Path, mode: str, address: Path) -> dict:
    script = tmp_path / "cold_probe.py"
    script.write_text(_COLD_PROBE, encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(REPOSITORY_ROOT))
    completed = subprocess.run(
        [sys.executable, str(script), mode, str(address)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_cold_reader_fresh_process(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    payload = _run_cold_probe(tmp_path, "inspect", address)
    assert payload["subjects"] == 2
    assert payload["propositions"] == 2
    assert payload["evidence_ok"] is True
    assert payload["evaluator"] == "covered"


def test_cold_judge_supported_question(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    inventory = inspect_config_world(address)
    export = next(s["subject"] for s in inventory["subjects"] if s.get("route_id") == "customer-export")
    result = judge_config_world(world=address, proposition=EXPORT, subject=export)
    assert result["outcome"] == "JUDGED"
    assert result["world"]["address"] == str(Path(address).resolve())
    assert result["artifact"]["applicability"]["result"] == "APPLIES"
    assert result["artifact"]["conformance"]["result"] == "CONFORMS"
    assert result["artifact"]["method"]["id"] == "config.customer_export_route"
    assert all(result["verification"].values())
    cited = result["artifact"]["applicability"]["assertion_ids"]
    known = {fact["assertion_id"] for fact in result["case"]["facts"]}
    assert cited and set(cited) <= known


def test_cold_judge_fresh_process(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    payload = _run_cold_probe(tmp_path, "judge", address)
    assert payload["outcome"] == "JUDGED"
    assert payload["applicability"] == "APPLIES"
    assert payload["conformance"] == "CONFORMS"


def test_judge_conflict_and_does_not_apply(tmp_path: Path) -> None:
    conflict_routes = [
        {"id": "customer-export", "path": "/internal/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ]
    address = _construct(
        tmp_path,
        routes=conflict_routes,
        paragraphs=("Customer export must use the approved customer-export route.",),
    )
    export = _subject_for_world(address, "customer-export")
    health = _subject_for_world(address, "health")
    conflict = judge_config_world(world=address, proposition=EXPORT, subject=export)
    assert conflict["outcome"] == "JUDGED"
    assert conflict["artifact"]["applicability"]["result"] == "APPLIES"
    assert conflict["artifact"]["conformance"]["result"] == "CONFLICTS"
    assert conflict["artifact"]["conformance"]["rule"]["observed_path"] == "/internal/export"
    excluded = judge_config_world(world=address, proposition=EXPORT, subject=health)
    assert excluded["artifact"]["applicability"]["result"] == "DOES_NOT_APPLY"
    assert excluded["artifact"]["conformance"] is None
    assert excluded["artifact"]["program_findings"] == []


def test_judge_missing_binding_is_unknown_not_conflict(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport"},
    ]
    address = _construct(
        tmp_path,
        routes=routes,
        paragraphs=("Customer export must use the approved customer-export route.",),
    )
    other = _subject_for_world(address, "other")
    result = judge_config_world(world=address, proposition=EXPORT, subject=other)
    assert result["outcome"] == "JUDGED"
    assert result["artifact"]["applicability"]["result"] == "UNKNOWN"
    assert result["artifact"]["conformance"] is None
    assert result["unknowns"]["applicability_unknown"] is True
    assert "incomplete coverage" in result["unknowns"]["applicability_because"]
    inventory = inspect_config_world(address)
    assert inventory["coverage"][0]["status"] == "INCOMPLETE"


def test_constructed_without_evaluator_inspects_but_judge_refuses(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "orders-export", "path": "/orders/export", "handler": "OrdersExport"},
    ]
    address = _construct(
        tmp_path,
        routes=routes,
        paragraphs=(
            "Customer export must use the approved customer-export route.",
            "Orders export must use the approved orders-export route.",
            "Status checks must use an approved route.",
        ),
    )
    orders_id = "proposition:orders-export-route"
    inspected = inspect_proposition(address, orders_id)
    assert len(inspected["bound_subjects"]) == 1
    assert inspected["evaluator"]["status"] == "unsupported"
    orders_subject = _subject_for_world(address, "orders-export")
    refused = judge_config_world(world=address, proposition=orders_id, subject=orders_subject)
    assert refused["outcome"] == "UNSUPPORTED_EVALUATOR"
    assert "orders-export" in refused["reason"]
    assert "artifact" not in refused
    generic_id = next(
        p["proposition"] for p in inspect_config_world(address)["propositions"]
        if p["proposition"].startswith("proposition:approved-")
    )
    generic_refused = judge_config_world(world=address, proposition=generic_id, subject=orders_subject)
    assert generic_refused["outcome"] == "UNSUPPORTED_EVALUATOR"


def test_judge_unknown_ids_and_bad_addresses(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    export = _subject_for_world(address, "customer-export")
    unknown_p = judge_config_world(world=address, proposition="proposition:absent", subject=export)
    assert unknown_p["outcome"] == "UNKNOWN_PROPOSITION"
    unknown_s = judge_config_world(world=address, proposition=EXPORT, subject="subject:absent")
    assert unknown_s["outcome"] == "UNKNOWN_SUBJECT"
    with pytest.raises(ValueError, match="does not exist"):
        inspect_config_world(tmp_path / "absent")
    with pytest.raises(ValueError, match="does not exist"):
        judge_config_world(world=tmp_path / "absent", proposition=EXPORT, subject=export)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="world.sqlite"):
        inspect_config_world(empty)
    with pytest.raises(ValueError, match="no established binding"):
        inspect_binding(address, EXPORT, _subject_for_world(address, "health"))
    with pytest.raises(ValueError, match="unknown proposition"):
        inspect_proposition(address, "proposition:absent")
    with pytest.raises(ValueError, match="unknown software subject"):
        inspect_subject(address, "subject:absent")


def test_unsealed_and_incompatible_worlds_refused(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    loose = tmp_path / "loose"
    shutil.copytree(address, loose)
    for child in loose.rglob("*"):
        child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))
    loose.chmod(loose.stat().st_mode | 0o700)
    with pytest.raises(ValueError, match="not sealed"):
        inspect_config_world(loose)
    with pytest.raises(ValueError, match="not sealed"):
        judge_config_world(world=loose, proposition=EXPORT, subject="subject:x")
    from ontology_author.world.runtime.world import ConstructionWorld
    bare = tmp_path / "bare"
    bare.mkdir()
    world = ConstructionWorld.create(bare / "world.sqlite", world_id="bare")
    world.close()
    (bare / "world.sqlite").chmod(0o444)
    bare.chmod(0o555)
    with pytest.raises(ValueError, match="not a Software Governance World"):
        inspect_config_world(bare)


def test_incompatible_governance_profile_refused(tmp_path: Path) -> None:
    from ontology_author.software_governance import (
        BindingSpec,
        CompletenessSpec,
        PropositionSpec,
        SoftwareSubjectSpec,
        construct_software_governance,
    )
    from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
    from ontology_author.world.core.source import SourceObservation
    from ontology_author.world.runtime.world import ConstructionWorld

    staging = tmp_path / "staging"
    staging.mkdir()
    seed = ConstructionWorld.create(staging / "world.sqlite", world_id="other")
    seed.add_referent("subject:other", label="other")
    seed.add_referent("snapshot:other", label="other snapshot")
    seed.close()
    import hashlib

    payload = b"x"
    digest = hashlib.sha256(payload).hexdigest()
    observation = SourceObservation(
        provider="test",
        native_handle=f"note.md@sha256:{digest}",
        source_revision=f"sha256:{digest}",
        native_location="bytes:0:1",
    )
    result = construct_software_governance(
        software_world=staging,
        output=tmp_path / "Wother",
        profile_id="other.profile/v9",
        evidence_blobs={digest: payload},
        propositions=(
            PropositionSpec(
                proposition_id="proposition:other",
                statement="Other must hold.",
                domain_relation="other_holds",
                observations=(observation,),
            ),
        ),
        bindings=(),
        subjects=(
            SoftwareSubjectSpec(
                subject_id="subject:other",
                snapshot_id="snapshot:other",
                kind="other:thing",
                capability="other.producer",
                version="v9",
                observations=(observation,),
            ),
        ),
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY,
            status="INCOMPLETE",
            universe="snapshot:other",
            basis="other basis",
            known_gaps=("other_gap",),
        ),
    )
    assert result.succeeded, result.errors
    with pytest.raises(ValueError, match="not a config.routes/v1 World"):
        inspect_config_world(tmp_path / "Wother")


def test_persisted_bundle_verifies_and_tamper_fails(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    export = _subject_for_world(address, "customer-export")
    bundle_path = tmp_path / "J0.json"
    result = judge_config_world(
        world=address, proposition=EXPORT, subject=export, persist_to=bundle_path
    )
    assert result["persisted_to"] == str(bundle_path.resolve())
    assert result["world"]["database_fingerprint"] == hashlib.sha256(
        (address / "world.sqlite").read_bytes()
    ).hexdigest()
    assert verify_judgment_bundle(bundle_path)["verified"] is True
    assert verify_judgment_bundle(read_judgment_bundle(bundle_path))["verified"] is True
    with pytest.raises(ValueError, match="already exists"):
        judge_config_world(
            world=address, proposition=EXPORT, subject=export, persist_to=bundle_path
        )
    tampered = read_judgment_bundle(bundle_path)
    tampered["artifact"]["conformance"]["result"] = "CONFLICTS"
    tampered_path = tmp_path / "Jt.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
    flipped = verify_judgment_bundle(tampered_path)
    assert flipped["verified"] is False
    assert flipped["checks"]["verdict_reproduced"] is False
    dropped = read_judgment_bundle(bundle_path)
    dropped["case"]["facts"] = dropped["case"]["facts"][:-1]
    dropped_path = tmp_path / "Jd.json"
    dropped_path.write_text(json.dumps(dropped), encoding="utf-8")
    assert verify_judgment_bundle(dropped_path)["verified"] is False


def test_substitution_onto_other_publication_fails(tmp_path: Path) -> None:
    first = _construct(tmp_path, name="W0")
    second = _construct(tmp_path, name="W1")
    assert first != second
    export = _subject_for_world(first, "customer-export")
    bundle_path = tmp_path / "J0.json"
    result = judge_config_world(
        world=first, proposition=EXPORT, subject=export, persist_to=bundle_path
    )
    assert result["outcome"] == "JUDGED"
    assert verify_judgment_bundle(bundle_path)["verified"] is True
    substituted = verify_judgment_bundle(bundle_path, world=second)
    assert substituted["verified"] is False
    assert substituted["checks"]["exact_address"] is False


def _judged_bundle(tmp_path: Path, name: str = "W0") -> tuple[Path, dict]:
    address = _construct(tmp_path, name=name)
    export = _subject_for_world(address, "customer-export")
    bundle_path = tmp_path / f"{name}.json"
    result = judge_config_world(
        world=address, proposition=EXPORT, subject=export, persist_to=bundle_path
    )
    assert result["outcome"] == "JUDGED"
    return address, read_judgment_bundle(bundle_path)


def _repackage(bundle: dict, case: dict, artifact: dict | None = None) -> dict:
    return {
        "format": "config-routes-judgment/v1",
        "world": dict(bundle["world"]),
        "request": dict(bundle["request"]),
        "case": case,
        "artifact": artifact if artifact is not None else evaluate_route_case(case),
    }


@pytest.mark.parametrize("relation", [
    "config_route",
    "governance_binding",
    "software_subject",
    "software_manifestation",
    "governance_known_gap",
])
def test_verify_rejects_selective_case_with_recomputed_artifact(
    tmp_path: Path, relation: str
) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    assert any(fact["relation"] == relation for fact in bundle["case"]["facts"])
    thinned = dict(bundle["case"])
    thinned["facts"] = [fact for fact in thinned["facts"] if fact["relation"] != relation]
    forged = _repackage(bundle, thinned)
    verdict = verify_judgment_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["canonical_match"] is False
    assert any("omits" in error for error in verdict["errors"])


@pytest.mark.parametrize("relation", ["software_subject", "governance_proposition"])
def test_verify_rejects_duplicated_canonical_fact(
    tmp_path: Path, relation: str
) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    forged = json.loads(json.dumps(bundle))
    duplicate = next(fact for fact in forged["case"]["facts"] if fact["relation"] == relation)
    forged["case"]["facts"].append(json.loads(json.dumps(duplicate)))
    verdict = verify_judgment_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["canonical_match"] is False
    assert any("non-canonical fact occurrence" in error for error in verdict["errors"])


def test_verify_ignores_fact_ordering(tmp_path: Path) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    forged = json.loads(json.dumps(bundle))
    forged["case"]["facts"] = list(reversed(forged["case"]["facts"]))
    assert verify_judgment_bundle(forged)["verified"] is True


@pytest.mark.parametrize("bad_address", [None, [], {}, 123])
def test_malformed_recorded_address_is_structured_failure(
    tmp_path: Path, bad_address: object
) -> None:
    address, bundle = _judged_bundle(tmp_path)
    forged = json.loads(json.dumps(bundle))
    forged["world"]["address"] = bad_address
    override = verify_judgment_bundle(forged, world=address)
    assert override["verified"] is False
    assert override["checks"]["shape"] is False
    assert override["errors"]
    direct = verify_judgment_bundle(json.loads(json.dumps(forged)))
    assert direct["verified"] is False
    assert direct["errors"]


def test_relative_recorded_address_still_verifies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    address, bundle = _judged_bundle(tmp_path)
    forged = json.loads(json.dumps(bundle))
    forged["world"]["address"] = os.path.relpath(address, tmp_path)
    monkeypatch.chdir(tmp_path)
    assert verify_judgment_bundle(forged)["verified"] is True


@pytest.mark.parametrize("field", ["question", "proposition_ids", "subject_ids", "world_address"])
def test_verify_rejects_altered_case_identity(tmp_path: Path, field: str) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    tampered = dict(bundle["case"])
    if field == "question":
        tampered["question"] = "Is this route perhaps fine?"
    elif field == "proposition_ids":
        tampered["proposition_ids"] = ["proposition:absent"]
    elif field == "subject_ids":
        tampered["subject_ids"] = ["subject:absent"]
    else:
        tampered["world_address"] = str(tmp_path / "elsewhere")
    forged = dict(bundle)
    forged["case"] = tampered
    verdict = verify_judgment_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["canonical_match"] is False


def test_verify_rejects_manually_evaluated_unsupported_proposition(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace-W0"
    workspace.mkdir()
    software = workspace / "software.json"
    governance = workspace / "governance.md"
    _write_software(software, [
        {"id": "orders-export", "path": "/orders/export", "handler": "OrdersExport"},
    ])
    _write_governance(governance, "Orders export must use the approved orders-export route.")
    address = tmp_path / "W0"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=address
    )
    assert report.succeeded, report.errors
    proposition = "proposition:orders-export-route"
    subject = _subject_for_world(address, "orders-export")
    refused = judge_config_world(world=address, proposition=proposition, subject=subject)
    assert refused["outcome"] == "UNSUPPORTED_EVALUATOR"
    view = open_governance_world(address)
    try:
        case = assemble_case(
            view,
            case_id="forged",
            question="Does this route satisfy the stated route rule?",
            proposition_ids=(proposition,),
            subject_ids=(subject,),
        )
    finally:
        view.world.close()
    forged = {
        "format": "config-routes-judgment/v1",
        "world": dict(refused["world"]),
        "request": {
            "proposition": proposition,
            "subject": subject,
            "question": "Does this route satisfy the stated route rule?",
            "case_id": "forged",
        },
        "case": case,
        "artifact": evaluate_route_case(case),
    }
    verdict = verify_judgment_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["evaluator_supported"] is False


def _damage_blob(address: Path, digest: str, *, remove: bool = False) -> None:
    blob = address / "governance_evidence" / digest
    blob.chmod(0o600)
    if remove:
        parent = blob.parent
        mode = parent.stat().st_mode
        parent.chmod(mode | 0o700)
        try:
            blob.unlink()
        finally:
            parent.chmod(mode)
    else:
        payload = bytearray(blob.read_bytes())
        payload[0] ^= 0xFF
        blob.write_bytes(bytes(payload))
        blob.chmod(0o444)


def _governance_digest(address: Path) -> str:
    inventory = inspect_config_world(address)
    revision = inventory["governance_revisions"][0]
    return revision.removeprefix("sha256:")


def test_corrupt_governance_blob_fails_judge_and_verify(tmp_path: Path) -> None:
    address, bundle = _judged_bundle(tmp_path)
    _damage_blob(address, _governance_digest(address))
    inspected = inspect_proposition(address, EXPORT)
    assert any(item["status"] == "FAILED" for item in inspected["evidence"])
    export = _subject_for_world(address, "customer-export")
    fresh = judge_config_world(world=address, proposition=EXPORT, subject=export)
    assert fresh["outcome"] == "INVALID_CASE"
    assert any("failed to reconstruct" in error for error in fresh["errors"])
    assert verify_judgment_bundle(bundle)["verified"] is False


def test_missing_governance_blob_fails_judge_and_verify(tmp_path: Path) -> None:
    address, bundle = _judged_bundle(tmp_path)
    _damage_blob(address, _governance_digest(address), remove=True)
    export = _subject_for_world(address, "customer-export")
    fresh = judge_config_world(world=address, proposition=EXPORT, subject=export)
    assert fresh["outcome"] == "INVALID_CASE"
    assert verify_judgment_bundle(bundle)["verified"] is False


def test_corrupt_software_blob_fails_judge_and_verify(tmp_path: Path) -> None:
    address, bundle = _judged_bundle(tmp_path)
    inventory = inspect_config_world(address)
    digest = inventory["software_revisions"][0].removeprefix("sha256:")
    _damage_blob(address, digest)
    export = _subject_for_world(address, "customer-export")
    binding = inspect_binding(address, EXPORT, export)
    assert any(item["status"] == "FAILED" for item in binding["evidence"])
    fresh = judge_config_world(world=address, proposition=EXPORT, subject=export)
    assert fresh["outcome"] == "INVALID_CASE"
    assert verify_judgment_bundle(bundle)["verified"] is False


def test_rewritten_support_cannot_normalize_corruption(tmp_path: Path) -> None:
    address, _bundle = _judged_bundle(tmp_path)
    _damage_blob(address, _governance_digest(address))
    export = _subject_for_world(address, "customer-export")
    view = open_governance_world(address)
    try:
        damaged_case = assemble_case(
            view,
            case_id=f"{EXPORT}::{export}",
            question="Does this route satisfy the stated route rule?",
            proposition_ids=(EXPORT,),
            subject_ids=(export,),
        )
    finally:
        view.world.close()
    assert any(
        item.get("status") == "FAILED"
        for fact in damaged_case["facts"]
        for item in (fact["support"].get("reconstructed") or [])
    )
    refused = judge_config_world(world=address, proposition=EXPORT, subject=export)
    assert refused["outcome"] == "INVALID_CASE"
    forged = {
        "format": "config-routes-judgment/v1",
        "world": dict(refused["world"]),
        "request": {
            "proposition": EXPORT,
            "subject": export,
            "question": "Does this route satisfy the stated route rule?",
            "case_id": f"{EXPORT}::{export}",
        },
        "case": damaged_case,
        "artifact": evaluate_route_case(damaged_case),
    }
    verdict = verify_judgment_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["evidence_ok"] is False


def test_unread_sidecar_mutation_does_not_invalidate(tmp_path: Path) -> None:
    address, bundle = _judged_bundle(tmp_path)
    sidecar = address / "world.admission.json"
    sidecar.chmod(0o600)
    sidecar.write_text('{"mutated": true}\n', encoding="utf-8")
    sidecar.chmod(0o444)
    assert verify_judgment_bundle(bundle)["verified"] is True


def test_persist_refuses_dangling_symlink(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    export = _subject_for_world(address, "customer-export")
    link = tmp_path / "Jlink.json"
    target = tmp_path / "Jtarget.json"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="already exists"):
        judge_config_world(
            world=address, proposition=EXPORT, subject=export, persist_to=link
        )
    assert not target.exists() and link.is_symlink()


def test_malformed_and_misshapen_bundles_are_structured_failures(tmp_path: Path) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    truncated = tmp_path / "Jtrunc.json"
    truncated.write_text('{"format": "config-routes-judgment/v1",', encoding="utf-8")
    garbled = verify_judgment_bundle(truncated)
    assert garbled["verified"] is False
    assert garbled["checks"]["readable"] is False
    misshapen = dict(bundle)
    del misshapen["request"]
    shaped = verify_judgment_bundle(misshapen)
    assert shaped["verified"] is False
    assert shaped["checks"]["shape"] is False


def test_malformed_artifacts_are_structured_failures(tmp_path: Path) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    def missing_key(forged: dict) -> None:
        forged["artifact"].pop("applicability")

    def not_a_dict(forged: dict) -> None:
        forged["artifact"] = [1, 2]

    def bad_findings(forged: dict) -> None:
        forged["artifact"]["program_findings"] = [5]

    def bad_conformance(forged: dict) -> None:
        forged["artifact"]["conformance"] = "CONFORMS"

    def facts_not_a_list(forged: dict) -> None:
        forged["case"]["facts"] = {"not": "a list"}

    variants = {
        "missing-key": missing_key,
        "not-a-dict": not_a_dict,
        "bad-findings": bad_findings,
        "bad-conformance": bad_conformance,
        "facts-not-a-list": facts_not_a_list,
    }
    for name, mutate in variants.items():
        forged = json.loads(json.dumps(bundle))
        mutate(forged)
        verdict = verify_judgment_bundle(forged)
        assert verdict["verified"] is False, name
        assert verdict["errors"], name


def test_tampered_request_block_fails_named_checks(tmp_path: Path) -> None:
    _address, bundle = _judged_bundle(tmp_path)
    wrong_question = json.loads(json.dumps(bundle))
    wrong_question["request"]["question"] = "Is this route perhaps fine?"
    verdict = verify_judgment_bundle(wrong_question)
    assert verdict["verified"] is False
    assert verdict["checks"]["canonical_request"] is False
    absent_proposition = json.loads(json.dumps(bundle))
    absent_proposition["request"]["proposition"] = "proposition:absent"
    verdict = verify_judgment_bundle(absent_proposition)
    assert verdict["verified"] is False
    assert verdict["checks"]["request_valid"] is False


def test_case_artifact_cross_mix_fails(tmp_path: Path) -> None:
    _first, first_bundle = _judged_bundle(tmp_path, name="W0")
    workspace = tmp_path / "workspace-W1"
    workspace.mkdir()
    software = workspace / "software.json"
    governance = workspace / "governance.md"
    _write_software(software, [
        {"id": "customer-export", "path": "/internal/export", "handler": "CustomerExport"},
    ])
    _write_governance(governance, "Customer export must use the approved customer-export route.")
    second = tmp_path / "W1"
    report = construct_config_world(
        software_source=software, governance_source=governance, output=second
    )
    assert report.succeeded, report.errors
    other = _subject_for_world(second, "customer-export")
    other_result = judge_config_world(world=second, proposition=EXPORT, subject=other)
    assert other_result["outcome"] == "JUDGED"
    mixed_case = dict(first_bundle)
    mixed_case["case"] = other_result["case"]
    assert verify_judgment_bundle(mixed_case)["verified"] is False
    mixed_artifact = dict(first_bundle)
    mixed_artifact["artifact"] = other_result["artifact"]
    assert verify_judgment_bundle(mixed_artifact)["verified"] is False


def test_identical_content_case_swap_fails(tmp_path: Path) -> None:
    first, first_bundle = _judged_bundle(tmp_path, name="W0")
    second = _construct(tmp_path, name="W1")
    assert first != second
    export = _subject_for_world(second, "customer-export")
    view = open_governance_world(second)
    try:
        twin_case = assemble_case(
            view,
            case_id=first_bundle["request"]["case_id"],
            question=first_bundle["request"]["question"],
            proposition_ids=(EXPORT,),
            subject_ids=(export,),
        )
    finally:
        view.world.close()
    swapped = dict(first_bundle)
    swapped["case"] = twin_case
    verdict = verify_judgment_bundle(swapped)
    assert verdict["verified"] is False
    assert any("address" in error for error in verdict["errors"])


def test_unknowns_explanation_distinguishes_inapplicable(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    health = _subject_for_world(address, "health")
    excluded = judge_config_world(world=address, proposition=EXPORT, subject=health)
    assert excluded["artifact"]["applicability"]["result"] == "DOES_NOT_APPLY"
    assert excluded["artifact"]["conformance"] is None
    assert excluded["unknowns"]["conformance_unknown"] is False
    assert excluded["unknowns"]["conformance_because"] == ""
    unknown_artifact = {
        "applicability": {"result": "APPLIES"},
        "conformance": {"result": "UNKNOWN", "because": "the route path was not in the case"},
        "context_requests": [],
    }
    explained = _explain_unknowns(None, {"facts": []}, unknown_artifact)
    assert explained["conformance_unknown"] is True


def test_installed_evaluator_matches_fixture_verdicts(tmp_path: Path) -> None:
    from ontology_author.software_governance import open_governance_world
    from ontology_author.software_governance.judgment import assemble_case, verify_case
    from ontology_author.config_routes.evaluate import evaluate_route_case
    from profiles.software_governance_config_v0.build import (
        EXPORT_ID,
        STATUS_ID,
        build_config_profile,
    )
    from profiles.software_governance_config_v0.judge import judge as judge_fixture

    output = tmp_path / "fixture-world"
    built = build_config_profile(output)
    assert built.succeeded, built.errors
    view = open_governance_world(output)
    try:
        by_record = {
            str(row["record_id"]): str(row["subject"])
            for row in view.world.relation_rows("config_route")
        }
        export, health = by_record["customer-export"], by_record["health"]
        candidates = view.binding_candidates_for_proposition(STATUS_ID)["candidates"]
        plans = [
            (EXPORT_ID, (export,), frozenset()),
            (EXPORT_ID, (health,), frozenset()),
            (STATUS_ID, tuple(item["software_subject"] for item in candidates), frozenset()),
        ]
        cases = [
            assemble_case(
                view,
                case_id=f"cross-{index}",
                question="Does this route satisfy the stated route rule?",
                proposition_ids=(proposition,),
                subject_ids=subjects,
            )
            for index, (proposition, subjects, _omit) in enumerate(plans)
        ]
        assert all(verify_case(view, case) == [] for case in cases)
    finally:
        view.world.close()
    for case in cases:
        installed = evaluate_route_case(case)
        fixture = judge_fixture(case)
        assert installed["applicability"] == fixture["applicability"]
        assert installed["program_findings"] == fixture["program_findings"]
        assert installed["conformance"] == fixture["conformance"]
        assert installed["context_requests"] == fixture["context_requests"]
