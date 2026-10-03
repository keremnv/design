"""Acceptance for the Software Governance construction path."""

from __future__ import annotations

import ast
import hashlib
import shutil
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.construction import declare_governance_relations
from ontology_author.software_governance.reads import GovernanceView
from ontology_author.software_governance.validation import (
    CONTRACT_ID,
    validate_governance_world,
)
from profiles.software_governance_v0.build import COMPLETENESS_BASIS, COMPLETENESS_GAP
from profiles.software_governance_v0.subjects import call_sites_of
from profiles.software_governance_v0.validate import validate_mail_profile
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld
from profiles.software_governance_v0.build import OUTBOUND, build_mail_profile

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPOSITORY_ROOT / "ontology_author" / "software_governance"
TYPESCRIPT = REPOSITORY_ROOT / "frontend" / "node_modules" / "typescript"
pytestmark_node = pytest.mark.skipif(
    shutil.which("node") is None or not TYPESCRIPT.exists(),
    reason="the TypeScript compiler API dependency is not installed",
)

OUTBOUND_ID = "proposition:outbound-mail"
MAILER_ID = "proposition:approved-mailer"


@pytest.fixture(scope="module")
def sealed(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if shutil.which("node") is None or not TYPESCRIPT.exists():
        pytest.skip("the TypeScript compiler API dependency is not installed")
    output = tmp_path_factory.mktemp("software-governance") / "world"
    result = build_mail_profile(output)
    assert result.succeeded, result.errors
    assert result.world_dir == output
    return output


def _view(sealed: Path):
    return open_governance_world(sealed)


def _receipt_call(view, text: str) -> str:
    matches = [
        site for site in call_sites_of(view, "sendReceipt")
        if site["text"].strip() == text
    ]
    assert len(matches) == 1, [(site["text"], site["resolution"]) for site in call_sites_of(view, "sendReceipt")]
    return str(matches[0]["subject"])


@pytest.mark.usefixtures("sealed")
def test_package_does_not_import_historical_application_machinery() -> None:
    forbidden = (
        "ontology_author.authority",
        "ontology_author.semantic_binding",
        "ontology_author.governance",
        "design_checkout",
        "profiles.design_checkout",
    )
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                if module in forbidden or module.startswith(tuple(f"{item}." for item in forbidden)):
                    found.append(f"{path.name} imports {module}")
        text = path.read_text(encoding="utf-8")
        assert "NotificationGateway" not in text
        assert "PaymentProvider" not in text
        assert "design_checkout" not in text
    assert found == []


def test_constructs_proposition_without_semantic_twin(sealed: Path) -> None:
    view = _view(sealed)
    inspected = view.inspect_governance_proposition(OUTBOUND_ID)
    assert inspected["semantic_subject"] is None
    assert inspected["statement"] == OUTBOUND
    assert inspected["domain_relation"] == "outbound_mail_passes"
    assert view.world.relation_schema("governance_proposition")
    with pytest.raises(Exception):
        view.world.relation_schema("proposition_semantic_subject")


def test_binding_has_checked_proposition_and_software_referents(sealed: Path) -> None:
    view = _view(sealed)
    schema = view.world.relation_schema("governance_binding")
    kinds = {role["name"]: role["type"] for role in schema["roles"]}
    assert kinds == {"proposition": "REFERENT", "software_subject": "REFERENT"}
    call = _receipt_call(view, "notificationGatewaySend(body)")
    inspected = view.inspect_governance_binding(OUTBOUND_ID, call)
    assert inspected["roles"] == ["proposition", "software_subject"]
    assert "target" not in inspected["roles"]
    assert "call_site" not in inspected["roles"]


def test_binding_is_grounded_separately_from_proposition(sealed: Path) -> None:
    view = _view(sealed)
    proposition = view.inspect_governance_proposition(OUTBOUND_ID)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    binding = view.inspect_governance_binding(OUTBOUND_ID, call)
    proposition_handles = {item["native_handle"].split("@", 1)[0] for item in proposition["evidence"]}
    binding_handles = {item["native_handle"].split("@", 1)[0] for item in binding["evidence"]}
    assert proposition_handles == {"policy.md", "runbook.md"}
    assert binding_handles == {"policy.md"}
    assert all(item["status"] == "OK" for item in proposition["evidence"])
    assert OUTBOUND in binding["evidence"][0]["text"]
    assert binding["relation_support"] == "SOURCE_EXPLICIT"
    assert binding["endpoint_resolution"] == "DETERMINISTIC"
    assert binding["construction_method"] == "correspondence to one call-site occurrence"
    assert binding["contract"] == CONTRACT_ID
    digest = proposition["evidence"][0]["native_handle"].rsplit("@sha256:", 1)[1]
    assert (sealed / "governance_evidence" / digest).is_file()
    assert not (sealed / "program_inputs" / digest).exists()


def test_subject_to_proposition_read(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    assert view.propositions_for_subject(call) == [OUTBOUND_ID]


def test_proposition_to_subject_read(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    assert view.subjects_for_proposition(OUTBOUND_ID) == [call]


def test_binding_to_one_call_site_does_not_bind_sibling_or_same_target_elsewhere(sealed: Path) -> None:
    view = _view(sealed)
    bound = _receipt_call(view, "notificationGatewaySend(body)")
    sibling = _receipt_call(view, "notificationGatewaySend(marked)")
    invoice = [
        site for site in call_sites_of(view, "sendInvoice")
        if site["text"].strip() == "notificationGatewaySend(body)"
    ]
    assert len(invoice) == 1
    assert sibling != bound
    assert view.propositions_for_subject(sibling) == []
    assert view.propositions_for_subject(invoice[0]["subject"]) == []
    assert view.subjects_for_proposition(OUTBOUND_ID) == [bound]


def test_program_relation_remains_mechanical_and_outside_binding(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    relations = view.program_relations_for_subject(call)
    assert relations["resolution"]["status"] == "RESOLVED"
    assert len(relations["invokes"]) == 1
    assert relations["invokes"][0]["target_label"] == "notificationGatewaySend"
    binding = view.inspect_governance_binding(OUTBOUND_ID, call)
    assert "program_invokes" not in binding["roles"]
    assert relations["invokes"][0]["origin"] == ["MECHANICAL"]


def test_local_manifestation_is_subject_local_not_file_digest(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    sibling = _receipt_call(view, "notificationGatewaySend(marked)")
    manifestation = view.local_manifestation_for_subject(call)
    sibling_manifestation = view.local_manifestation_for_subject(sibling)
    assert manifestation["status"] == "OK"
    assert manifestation["content"].strip() == "notificationGatewaySend(body)"
    assert manifestation["content_digest"] != manifestation["file_digest"]
    assert manifestation["file_digest"] == sibling_manifestation["file_digest"]
    assert manifestation["content_digest"] != sibling_manifestation["content_digest"]
    assert manifestation["producer"]
    assert manifestation["scheme"] == "source-token-range"
    assert manifestation["capability"] == "spine.source_evidence/v1"


def test_location_is_not_manifestation_identity(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    manifestation = view.local_manifestation_for_subject(call)
    assert manifestation["location"].startswith("bytes:")
    assert manifestation["location"] != manifestation["content_digest"]
    assert manifestation["location"] not in manifestation["content_digest"]


def test_ambiguous_correspondence_records_candidates_without_binding(sealed: Path) -> None:
    view = _view(sealed)
    report = view.binding_candidates_for_proposition(MAILER_ID)
    labels = {item["label"] for item in report["candidates"]}
    assert labels == {"notificationGatewaySend", "smtpClientSend"}
    assert report["established_subjects"] == []
    assert report["questions"] == [{
        "state": "UNRESOLVED",
        "question": "Which software subject is the approved mailer?",
    }]
    assert {item["endpoint_resolution"] for item in report["candidates"]} == {"AMBIGUOUS"}
    assert view.subjects_for_proposition(MAILER_ID) == []


def test_mechanical_multiple_candidates_do_not_create_positive_program_relation(sealed: Path) -> None:
    view = _view(sealed)
    sites = [
        site for site in call_sites_of(view, "sendAmbiguous")
        if "channel.send" in site["text"]
    ]
    assert len(sites) == 1
    site = sites[0]
    assert site["resolution"] == "MULTIPLE_CANDIDATES"
    assert site["invokes"] == []
    assert view.propositions_for_subject(site["subject"]) == []
    relations = view.program_relations_for_subject(site["subject"])
    assert len(relations["resolution"]["candidates"]) >= 2


def test_semantic_binding_origin_is_semantic(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    binding = view.inspect_governance_binding(OUTBOUND_ID, call)
    proposition = view.inspect_governance_proposition(OUTBOUND_ID)
    assert binding["origin"] == "SEMANTIC"
    assert proposition["origin"] == "SEMANTIC"


def test_fresh_consumer_reopens_sealed_world_and_answers_required_reads(sealed: Path) -> None:
    view = _view(sealed)
    call = _receipt_call(view, "notificationGatewaySend(body)")
    assert view.propositions_for_subject(call) == [OUTBOUND_ID]
    assert view.subjects_for_proposition(OUTBOUND_ID) == [call]
    binding = view.inspect_governance_binding(OUTBOUND_ID, call)
    assert binding["endpoint_resolution"] == "DETERMINISTIC"
    assert binding["subject_manifestation"]["content"].strip() == "notificationGatewaySend(body)"
    assert view.program_relations_for_subject(call)["resolution"]["status"] == "RESOLVED"
    unresolved = view.binding_candidates_for_proposition(MAILER_ID)
    assert unresolved["questions"][0]["state"] == "UNRESOLVED"
    assert unresolved["established_subjects"] == []


def test_missing_binding_is_not_read_as_ungoverned_without_completeness(sealed: Path) -> None:
    view = _view(sealed)
    sibling = _receipt_call(view, "notificationGatewaySend(marked)")
    assert view.propositions_for_subject(sibling) == []
    assert view.absence_is_negative(sibling) is False
    completeness = view.completeness()
    assert completeness[0]["status"] == "INCOMPLETE"
    assert completeness[0]["basis"] == COMPLETENESS_BASIS
    assert completeness[0]["known_gaps"] == [COMPLETENESS_GAP]
    assert completeness[0]["origin"] == "MECHANICAL"
    assert completeness[0]["known_gap_origins"][COMPLETENESS_GAP] == "MECHANICAL"


def test_validation_rejects_mechanical_governance_and_ambiguous_binding(tmp_path: Path) -> None:
    world = _sample_world(tmp_path)
    try:
        observation = _authority_observation(world, "policy.md", "A stated requirement.")
        _assert_sample_proposition(world, observation)
        _assert_binding(
            world,
            observation,
            origin=ConstructionOrigin.MECHANICAL,
            support="SOURCE_EXPLICIT",
            resolution="DETERMINISTIC",
            method="mislabeled",
        )
        _assert_completeness(world, observation)
        errors = validate_governance_world(world)
        assert any("recorded as ['MECHANICAL']" in error for error in errors)
        assert not any("governance_completeness" in error for error in errors)
        assert not any("governance_known_gap" in error for error in errors)

        world.retract_tuple("governance_binding", _binding_values())
        _assert_binding(
            world,
            observation,
            origin=ConstructionOrigin.SEMANTIC,
            support="SOURCE_EXPLICIT",
            resolution="AMBIGUOUS",
            method="ambiguous persisted as established",
        )
        errors = validate_governance_world(world)
        assert any("non-positive endpoint resolution 'AMBIGUOUS'" in error for error in errors)
    finally:
        world.close()


def test_software_governance_package_has_no_typescript_producer_import() -> None:
    forbidden = (
        "ontology_author.program_spine",
        "build_typescript_spine",
        "TypeScriptBoundary",
        "profiles",
    )
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
        for module in modules:
            if module in forbidden or module.startswith(tuple(f"{item}." for item in forbidden)):
                found.append(f"{path.name} imports {module}")
        if "typescript" in text.lower():
            found.append(f"{path.name} names typescript")
        if "NotificationGateway" in text:
            found.append(f"{path.name} names the mail fixture")
    assert found == []


def test_generic_schema_is_the_frozen_vocabulary(tmp_path: Path) -> None:
    world = ConstructionWorld.create(tmp_path / "world.sqlite", world_id="governance-schema")
    try:
        declare_governance_relations(world)
        names = [
            str(row["name"])
            for row in world.query("SELECT name FROM _world_relations ORDER BY name")
        ]
    finally:
        world.close()
    assert names == [
        "governance_binding",
        "governance_candidate",
        "governance_completeness",
        "governance_known_gap",
        "governance_proposition",
        "governance_question",
        "software_manifestation",
        "software_subject",
    ]


def test_generic_validation_does_not_require_source_explicit_or_deterministic(tmp_path: Path) -> None:
    world = _sample_world(tmp_path)
    try:
        observation = _authority_observation(world, "policy.md", "A stated requirement.")
        _assert_sample_proposition(world, observation)
        _assert_binding(
            world,
            observation,
            origin=ConstructionOrigin.SEMANTIC,
            support="CROSS_EVIDENCE",
            resolution="AGENT_RESOLVED",
            method="correspondence admitted by a future profile",
        )
        _add_unobserved_subject(world, "subject:other")
        _assert_question(world, observation)
        _assert_completeness(world, observation)
        _assert_candidate(world, observation, subject="subject:other", resolution="AMBIGUOUS")
        errors = validate_governance_world(world)
        assert errors == []
        manifestation = GovernanceView(world).local_manifestation_for_subject("subject:known")
        assert manifestation["status"] == "NOT_PRODUCED"
        assert manifestation["scheme"] == ""
        assert manifestation["content_digest"] == ""

        world.retract_tuple(
            "governance_candidate",
            {"proposition": "proposition:sample", "software_subject": "subject:other"},
        )
        _assert_candidate(world, observation, subject="subject:other", resolution="DETERMINISTIC")
        errors = validate_governance_world(world)
        assert any("endpoint resolution 'DETERMINISTIC'" in error for error in errors)
        assert any("on a candidate" in error for error in errors)
    finally:
        world.close()


def test_mail_profile_requires_reconstructible_source_observations(sealed: Path, tmp_path: Path) -> None:
    view = _view(sealed)
    assert validate_mail_profile(view.world) == []
    world = _sample_world(tmp_path)
    try:
        observation = _authority_observation(world, "policy.md", "A stated requirement.")
        _assert_sample_proposition(world, observation)
        _assert_binding(
            world,
            observation,
            origin=ConstructionOrigin.SEMANTIC,
            support="CROSS_EVIDENCE",
            resolution="AGENT_RESOLVED",
            method="correspondence admitted by a future profile",
        )
        _assert_completeness(world, observation)
        profile_errors = validate_mail_profile(world)
        assert any("reconstructible source observation" in error for error in profile_errors)
        assert any("SOURCE_EXPLICIT" in error for error in profile_errors)
        assert any("DETERMINISTIC" in error for error in profile_errors)
        assert validate_governance_world(world) == []
    finally:
        world.close()


def _sample_world(tmp_path: Path) -> ConstructionWorld:
    world = ConstructionWorld.create(tmp_path / "world.sqlite", world_id="governance-validation")
    declare_governance_relations(world)
    snapshot = "snapshot:test"
    subject = "subject:known"
    proposition = "proposition:sample"
    for referent in (snapshot, subject, proposition):
        world.add_referent(referent, label=referent)
    _assert_subject_receipt(world, subject)
    return world


def _add_unobserved_subject(world: ConstructionWorld, subject: str) -> None:
    world.add_referent(subject, label=subject)
    _assert_subject_receipt(world, subject)


def _assert_subject_receipt(world: ConstructionWorld, subject: str) -> None:
    world.assert_tuple(
        "software_subject",
        {
            "subject": subject,
            "snapshot": "snapshot:test",
            "kind": "coordinate",
            "capability": "future.producer",
            "version": "v0",
        },
        origin=ConstructionOrigin.MECHANICAL,
        grounding=AssertionGrounding(
            (_pointer("note.md", "x"),),
            construction_method="test producer",
            extra={"contract": CONTRACT_ID, "profile_id": "test"},
        ),
    )


def _binding_values() -> dict[str, str]:
    return {"proposition": "proposition:sample", "software_subject": "subject:known"}


def _pointer(name: str, text: str) -> SourceObservation:
    payload = text.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return SourceObservation(
        provider="test",
        native_handle=f"{name}@sha256:{digest}",
        source_revision=f"sha256:{digest}",
        native_location=f"bytes:0:{len(payload)}",
    )


def _assert_sample_proposition(world: ConstructionWorld, observation: SourceObservation) -> None:
    world.assert_tuple(
        "governance_proposition",
        {
            "proposition": "proposition:sample",
            "statement": "A stated requirement.",
            "domain_relation": "sample_requirement",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            (observation,),
            construction_method="proposition",
            extra={"contract": CONTRACT_ID, "profile_id": "test"},
        ),
    )


def _assert_binding(
    world: ConstructionWorld,
    observation: SourceObservation,
    *,
    origin: ConstructionOrigin,
    support: str,
    resolution: str,
    method: str,
) -> None:
    world.assert_tuple(
        "governance_binding",
        _binding_values(),
        origin=origin,
        grounding=AssertionGrounding(
            (observation,),
            construction_method=method,
            extra={
                "contract": CONTRACT_ID,
                "profile_id": "test",
                "relation_support": support,
                "endpoint_resolution": resolution,
                "software_evidence": "declared subject",
            },
        ),
    )


def _assert_candidate(
    world: ConstructionWorld,
    observation: SourceObservation,
    *,
    subject: str,
    resolution: str,
) -> None:
    world.assert_tuple(
        "governance_candidate",
        {"proposition": "proposition:sample", "software_subject": subject},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            (observation,),
            construction_method="candidate",
            extra={
                "contract": CONTRACT_ID,
                "profile_id": "test",
                "relation_support": "CROSS_EVIDENCE",
                "endpoint_resolution": resolution,
                "software_evidence": "declared subject",
            },
        ),
    )


def _assert_question(world: ConstructionWorld, observation: SourceObservation) -> None:
    world.assert_tuple(
        "governance_question",
        {
            "proposition": "proposition:sample",
            "state": "UNRESOLVED",
            "question": "Which subject?",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            (observation,),
            construction_method="question",
            extra={"contract": CONTRACT_ID, "profile_id": "test"},
        ),
    )


def _assert_completeness(world: ConstructionWorld, observation: SourceObservation) -> None:
    world.assert_tuple(
        "governance_completeness",
        {
            "capability": "software_governance.bindings/v0",
            "status": "INCOMPLETE",
            "universe": "snapshot:test",
            "basis": "test basis",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            (observation,),
            construction_method="completeness",
            extra={"contract": CONTRACT_ID, "profile_id": "test"},
        ),
    )
    world.assert_tuple(
        "governance_known_gap",
        {"capability": "software_governance.bindings/v0", "gap": "unsurveyed_subjects"},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            (observation,),
            construction_method="gap",
            extra={"contract": CONTRACT_ID, "profile_id": "test"},
        ),
    )


def _authority_observation(world: ConstructionWorld, name: str, text: str) -> SourceObservation:
    payload = text.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    directory = world.path.parent / "governance_evidence"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / digest).write_bytes(payload)
    return SourceObservation(
        provider="markdown",
        native_handle=f"{name}@sha256:{digest}",
        source_revision=f"sha256:{digest}",
        native_location=f"bytes:0:{len(payload)}",
    )
