"""Judgment v0 acceptance against the two Construction v0 profiles.

The generic package assembles and checks a case. Each profile owns its
evaluator. Neither writes a finding back into the sealed World.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.judgment import (
    assemble_case,
    consumer_reads,
    read_artifact,
    verify_case,
    write_artifact,
)
from ontology_author.software_governance.judgment.artifact import ARTIFACT_FIELDS
from ontology_author.software_governance.judgment.case import facts as facts_named
from ontology_author.world.core.model import RoleType
from profiles.software_governance_config_v0.judge import judge as judge_config
from profiles.software_governance_v0.judge import judge as judge_mail
from profiles.software_governance_v0.subjects import subject_named
from tests.software_governance_judgment_fixtures import build_worlds

MAIL_PROPOSITION = "proposition:outbound-mail"
MAILER_PROPOSITION = "proposition:approved-mailer"
EXPORT_PROPOSITION = "proposition:customer-export-route"
STATUS_PROPOSITION = "proposition:approved-status-route"


@pytest.fixture(scope="module")
def worlds(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build_worlds(tmp_path_factory.mktemp("judgment-v0"))


def test_mail_support_conflict_and_unresolved_target(worlds: dict[str, Path], tmp_path: Path) -> None:
    support = _judge_mail(worlds["mail"], "mail-support", _bound(worlds["mail"], MAIL_PROPOSITION))
    conflict = _judge_mail(worlds["mail_conflict"], "mail-conflict", _bound(worlds["mail_conflict"], MAIL_PROPOSITION))
    ambiguous = _judge_mail(worlds["mail_ambiguous"], "mail-ambiguous", _bound(worlds["mail_ambiguous"], MAIL_PROPOSITION))
    assert support["applicability"]["result"] == "APPLIES"
    assert support["program_findings"][0]["values"]["target"] == "notificationGatewaySend"
    assert support["conformance"]["result"] == "CONFORMS"
    assert support["conformance"]["rule"]["required_target"] == "notificationGatewaySend"
    assert support["method"]["id"] == "mail.outbound_mail_passes"
    assert support["method"]["version"] == "v0"
    assert support["method"]["rule"]["required_target"] == "notificationGatewaySend"
    assert support["method"]["fingerprint"] == conflict["method"]["fingerprint"]
    assert conflict["applicability"]["result"] == "APPLIES"
    assert conflict["program_findings"][0]["values"]["target"] == "smtpClientSend"
    assert conflict["conformance"]["result"] == "CONFLICTS"
    assert ambiguous["applicability"]["result"] == "APPLIES"
    assert ambiguous["program_findings"][0]["status"] == "UNRESOLVED"
    assert ambiguous["program_findings"][0]["values"]["resolution_status"] == "MULTIPLE_CANDIDATES"
    assert ambiguous["conformance"]["result"] == "UNKNOWN"
    assert ambiguous["context_requests"] == []
    assert "context_sufficiency" not in ambiguous
    _assert_shape(support, conflict, ambiguous)
    _assert_readable(worlds["mail"], "mail-support", support, tmp_path)


def test_config_support_conflict_and_missing_property(worlds: dict[str, Path]) -> None:
    export = _bound(worlds["config"], EXPORT_PROPOSITION)
    support = _judge_config(worlds["config"], "config-support", EXPORT_PROPOSITION, (export,))
    conflict_subject = _bound(worlds["config_conflict"], EXPORT_PROPOSITION)
    conflict = _judge_config(worlds["config_conflict"], "config-conflict", EXPORT_PROPOSITION, (conflict_subject,))
    missing = _judge_config(
        worlds["config"],
        "config-missing-path",
        EXPORT_PROPOSITION,
        (export,),
        omit_relations=frozenset({"config_route"}),
    )
    assert support["program_findings"][0]["values"]["path"] == "/customers/export"
    assert support["conformance"]["result"] == "CONFORMS"
    assert support["conformance"]["rule"]["required_path"] == "/customers/export"
    assert conflict["program_findings"][0]["values"]["path"] == "/internal/export"
    assert conflict["conformance"]["result"] == "CONFLICTS"
    assert missing["applicability"]["result"] == "APPLIES"
    assert missing["program_findings"] == []
    assert missing["conformance"]["result"] == "UNKNOWN"
    assert missing["context_requests"] == [
        {
            "gap": "judgment",
            "proposition": EXPORT_PROPOSITION,
            "subject": export,
            "need": "subject_property",
            "property": "path",
            "availability": "ABSENT",
        }
    ]
    _assert_shape(support, conflict, missing)


def test_being_in_the_case_is_not_applicability(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["mail"])
    try:
        callable_subject = subject_named(view, "notificationGatewaySend", "callable")
        case = assemble_case(
            view,
            case_id="mail-definition",
            question="Does the outbound-mail proposition apply to this callable?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(callable_subject,),
        )
    finally:
        view.world.close()
    artifact = judge_mail(case)
    assert case["subject_ids"] == [callable_subject]
    assert artifact["applicability"]["result"] == "DOES_NOT_APPLY"
    assert artifact["applicability"]["rule"] == {
        "excludes_kind": "callable",
        "observed_kind": "callable",
    }
    assert artifact["conformance"] is None
    assert artifact["context_requests"] == []
    health = _record(worlds["config"], "health")
    route_case = _judge_config(worlds["config"], "config-other-route", EXPORT_PROPOSITION, (health,))
    assert route_case["applicability"]["result"] == "DOES_NOT_APPLY"
    assert route_case["applicability"]["rule"] == {
        "required_handler": "CustomerExport",
        "observed_handler": "Health",
    }
    assert route_case["conformance"] is None


def test_construction_gap_is_not_a_judgment_gap(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["mail"])
    try:
        candidates = view.binding_candidates_for_proposition(MAILER_PROPOSITION)
        subjects = tuple(item["software_subject"] for item in candidates["candidates"])
        assert candidates["established_subjects"] == []
        assert len(subjects) == 2
        case = assemble_case(
            view,
            case_id="mail-unbound",
            question="Which subject does the approved-mailer proposition govern?",
            proposition_ids=(MAILER_PROPOSITION,),
            subject_ids=subjects,
        )
    finally:
        view.world.close()
    mail_gap = judge_mail(case)
    status_subjects = _candidate_subjects(worlds["config"], STATUS_PROPOSITION)
    config_gap = _judge_config(
        worlds["config"],
        "config-unbound",
        STATUS_PROPOSITION,
        status_subjects,
    )
    for artifact in (mail_gap, config_gap):
        assert artifact["applicability"]["result"] == "UNKNOWN"
        assert artifact["conformance"] is None
        assert artifact["program_findings"] == []
        assert artifact["context_requests"][0]["gap"] == "construction"
        assert artifact["context_requests"][0]["need"] == "established_binding"
        assert artifact["context_requests"][0]["gap"] != "judgment"


def test_unknown_conformance_is_not_a_conflict(worlds: dict[str, Path]) -> None:
    ambiguous = _judge_mail(worlds["mail_ambiguous"], "mail-unknown", _bound(worlds["mail_ambiguous"], MAIL_PROPOSITION))
    assert ambiguous["conformance"]["result"] == "UNKNOWN"
    assert ambiguous["conformance"]["result"] != "CONFLICTS"
    assert ambiguous["applicability"]["result"] == "APPLIES"


def test_citation_rejects_support_mutations(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["mail"])
    try:
        case = assemble_case(
            view,
            case_id="mail-cite",
            question="Which target does the bound call use?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(_bound(worlds["mail"], MAIL_PROPOSITION),),
        )
        assert verify_case(view, case) == []
        proposition = next(fact for fact in case["facts"] if fact["relation"] == "governance_proposition")
        assert proposition["support"]["reconstructed"]
        mutated = {
            "values": _mutate(proposition, lambda fact: fact["values"].__setitem__("statement", "rewritten")),
            "evidence": _mutate(proposition, lambda fact: fact["support"]["reconstructed"][0].__setitem__("text", "rewritten")),
            "origin": _mutate(proposition, _rewrite_origin),
            "method": _mutate(proposition, _rewrite_method),
            "removed": _mutate(proposition, _remove_observation),
            "invented": _mutate(proposition, _invent_observation),
        }
        for name, fact in mutated.items():
            errors = verify_case(view, _replace_fact(case, fact))
            assert errors, name
        labeled = _mutate(proposition, lambda fact: fact["referent_labels"].__setitem__("proposition", "display only"))
        assert verify_case(view, _replace_fact(case, labeled)) == []
    finally:
        view.world.close()
    assert "ASSERTION" not in {item.value for item in RoleType}


def test_incomplete_coverage_does_not_exclude_a_subject(worlds: dict[str, Path]) -> None:
    from profiles.software_governance_v0.subjects import call_sites_of

    view = open_governance_world(worlds["mail"])
    try:
        bound = _bound(worlds["mail"], MAIL_PROPOSITION)
        other = next(
            site["subject"]
            for site in call_sites_of(view, "sendInvoice")
            if site["resolution"] == "RESOLVED" and site["subject"] != bound
        )
        case = assemble_case(
            view,
            case_id="mail-unbound-call",
            question="Does the outbound-mail proposition exclude this other call?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(other,),
        )
        completeness = facts_named(case, "governance_completeness")
        assert completeness[0]["values"]["status"] == "INCOMPLETE"
        assert not any(fact["relation"] == "governance_binding" for fact in case["facts"])
    finally:
        view.world.close()
    mail_unknown = judge_mail(case)
    assert mail_unknown["applicability"]["result"] == "UNKNOWN"
    assert mail_unknown["context_requests"] == []
    assert mail_unknown["conformance"] is None
    health = _record(worlds["config"], "health")
    config_unknown = _judge_config(
        worlds["config"],
        "config-unbound-route",
        EXPORT_PROPOSITION,
        (health,),
        omit_relations=frozenset({"config_route"}),
    )
    assert config_unknown["applicability"]["result"] == "UNKNOWN"
    assert config_unknown["applicability"]["result"] != "DOES_NOT_APPLY"
    assert config_unknown["context_requests"] == []


def test_indeterminacy_is_not_missing_context(worlds: dict[str, Path]) -> None:
    ambiguous = _judge_mail(
        worlds["mail_ambiguous"],
        "mail-indeterminate",
        _bound(worlds["mail_ambiguous"], MAIL_PROPOSITION),
    )
    view = open_governance_world(worlds["mail_ambiguous"])
    try:
        case = assemble_case(
            view,
            case_id="mail-indeterminate",
            question="What target does this call have?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(_bound(worlds["mail_ambiguous"], MAIL_PROPOSITION),),
        )
    finally:
        view.world.close()
    candidates = [
        fact for fact in case["facts"]
        if fact["relation"] == "program_resolution_candidate"
    ]
    assert len(candidates) >= 2
    assert ambiguous["program_findings"][0]["status"] == "UNRESOLVED"
    assert ambiguous["conformance"]["result"] == "UNKNOWN"
    assert ambiguous["context_requests"] == []
    assert "context_sufficiency" not in ambiguous


def test_case_citation_is_checked_against_the_world(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["config"])
    try:
        subject = _bound(worlds["config"], EXPORT_PROPOSITION)
        case = assemble_case(
            view,
            case_id="config-cite",
            question="Which path does the bound route use?",
            proposition_ids=(EXPORT_PROPOSITION,),
            subject_ids=(subject,),
        )
        assert verify_case(view, case) == []
        tampered = dict(case)
        tampered["facts"] = [dict(fact) for fact in case["facts"]]
        route = next(fact for fact in tampered["facts"] if fact["relation"] == "config_route")
        route["values"] = dict(route["values"])
        route["values"]["path"] = "/somewhere-else"
        assert verify_case(view, tampered)
    finally:
        view.world.close()
    assert "ASSERTION" not in {item.value for item in RoleType}


def test_judgment_does_not_mutate_the_sealed_world(worlds: dict[str, Path], tmp_path: Path) -> None:
    database = worlds["mail"] / "world.sqlite"
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    artifact = _judge_mail(worlds["mail"], "mail-readonly", _bound(worlds["mail"], MAIL_PROPOSITION))
    write_artifact(tmp_path / "judgment.json", artifact)
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert not (worlds["mail"] / "judgment.json").exists()


def test_generic_package_owns_no_profile_or_spine_vocabulary() -> None:
    root = Path(__file__).resolve().parent.parent / "ontology_author" / "software_governance" / "judgment"
    texts = [path.read_text(encoding="utf-8") for path in sorted(root.glob("*.py"))]
    forbidden = (
        "NotificationGateway",
        "outbound_mail",
        "smtpClientSend",
        "notificationGatewaySend",
        "customer-export",
        "customer_export",
        "CustomerExport",
        "config:route",
        "program_invokes",
        "program_resolution",
        "program_entity",
        "config_route",
        "config_member",
        "GovernanceCase",
        "design_checkout",
    )
    found = [name for name in forbidden if any(name in text for text in texts)]
    assert found == []
    forbidden_imports = (
        "profiles",
        "ontology_author.program_spine",
        "ontology_author.governance",
        "ontology_author.authority",
        "ontology_author.design_checkout",
        "ontology_author.semantic_binding",
    )
    imported = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    violations = [
        module
        for module in imported
        if module in forbidden_imports or module.startswith(tuple(f"{name}." for name in forbidden_imports))
    ]
    assert violations == []
    repository = Path(__file__).resolve().parent.parent
    mail = (repository / "profiles/software_governance_v0/judge.py").read_text(encoding="utf-8")
    config = (repository / "profiles/software_governance_config_v0/judge.py").read_text(encoding="utf-8")
    assert "notificationGatewaySend" in mail
    assert "excludes_kind" in mail
    assert "CustomerExport" in config
    assert "/customers/export" in config
    assert "Path(__file__)" not in mail
    assert "Path(__file__)" not in config


def test_consumer_does_not_issue_sql(worlds: dict[str, Path], tmp_path: Path) -> None:
    view = open_governance_world(worlds["mail"])
    try:
        case = assemble_case(
            view,
            case_id="mail-read",
            question="Does this call site conform?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(_bound(worlds["mail"], MAIL_PROPOSITION),),
        )
    finally:
        view.world.close()
    artifact = judge_mail(case)
    path = tmp_path / "judgment.json"
    write_artifact(path, artifact)
    loaded = read_artifact(path)
    report = consumer_reads(case, loaded)
    assert report["proposition"] == ["Outbound email must pass through NotificationGateway."]
    proposition = next(fact for fact in case["facts"] if fact["relation"] == "governance_proposition")
    assert proposition["support"]["reconstructed"][0]["text"].strip() == report["proposition"][0]
    assert proposition["support"]["reconstructed"][0]["status"] == "OK"
    assert report["program_findings"][0]["status"] == "ESTABLISHED"
    assert report["finding_evidence"]
    assert report["conformance"]["result"] == "CONFORMS"
    assert report["world"]["world_id"]
    assert report["world"]["revision"] >= 1
    assert "chain_of_thought" not in loaded


def _mutate(fact: dict, edit) -> dict:
    cloned = copy.deepcopy(fact)
    edit(cloned)
    return cloned


def _rewrite_origin(fact: dict) -> None:
    fact["support"]["origins"] = ["MECHANICAL"]
    for base in fact["support"]["bases"]:
        detail = base["detail"]
        if isinstance(detail, dict) and "construction_origin" in detail:
            detail["construction_origin"] = "MECHANICAL"


def _remove_observation(fact: dict) -> None:
    for base in fact["support"]["bases"]:
        detail = base["detail"]
        if isinstance(detail, dict) and detail.get("observations"):
            detail["observations"].pop()
            break
    fact["support"]["reconstructed"].pop()


def _invent_observation(fact: dict) -> None:
    pointer = {
        "provider": "markdown",
        "native_handle": "invented",
        "source_revision": "sha256:0",
        "native_location": "bytes:0:1",
    }
    for base in fact["support"]["bases"]:
        detail = base["detail"]
        if isinstance(detail, dict) and isinstance(detail.get("observations"), list):
            detail["observations"].append(pointer)
            break
    fact["support"]["reconstructed"].append({
        "native_handle": "invented",
        "native_location": "bytes:0:1",
        "text": "invented",
        "status": "OK",
    })


def _rewrite_method(fact: dict) -> None:
    for base in fact["support"]["bases"]:
        detail = base["detail"]
        if isinstance(detail, dict) and "construction_method" in detail:
            detail["construction_method"] = "rewritten"
            return
    raise AssertionError("no construction method on the cited support")


def _replace_fact(case: dict, fact: dict) -> dict:
    cloned = copy.deepcopy(case)
    cloned["facts"] = [
        fact if item["assertion_id"] == fact["assertion_id"] else item
        for item in cloned["facts"]
    ]
    return cloned


def _judge_mail(world: Path, case_id: str, subject: str) -> dict:
    view = open_governance_world(world)
    try:
        case = assemble_case(
            view,
            case_id=case_id,
            question="Does this call site pass outbound mail through the approved gateway?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(subject,),
        )
        assert verify_case(view, case) == []
    finally:
        view.world.close()
    return judge_mail(case)


def _judge_config(
    world: Path,
    case_id: str,
    proposition: str,
    subjects: tuple[str, ...],
    omit_relations: frozenset[str] = frozenset(),
) -> dict:
    view = open_governance_world(world)
    try:
        case = assemble_case(
            view,
            case_id=case_id,
            question="Does this route satisfy the stated route rule?",
            proposition_ids=(proposition,),
            subject_ids=subjects,
            omit_relations=omit_relations,
        )
        if not omit_relations:
            assert verify_case(view, case) == []
    finally:
        view.world.close()
    return judge_config(case)


def _bound(world: Path, proposition: str) -> str:
    view = open_governance_world(world)
    try:
        subjects = view.subjects_for_proposition(proposition)
    finally:
        view.world.close()
    assert len(subjects) == 1
    return subjects[0]


def _record(world: Path, record_id: str) -> str:
    view = open_governance_world(world)
    try:
        matches = [
            str(row["subject"])
            for row in view.world.relation_rows("config_route")
            if row["record_id"] == record_id
        ]
    finally:
        view.world.close()
    assert len(matches) == 1
    return matches[0]


def _candidate_subjects(world: Path, proposition: str) -> tuple[str, ...]:
    view = open_governance_world(world)
    try:
        candidates = view.binding_candidates_for_proposition(proposition)
    finally:
        view.world.close()
    return tuple(item["software_subject"] for item in candidates["candidates"])


def _assert_shape(*artifacts: dict) -> None:
    for artifact in artifacts:
        assert tuple(artifact) == ARTIFACT_FIELDS
        assert "chain_of_thought" not in artifact
        assert artifact["conformance"] is None or artifact["conformance"]["result"] in {
            "CONFORMS",
            "CONFLICTS",
            "UNKNOWN",
        }


def _assert_readable(world: Path, case_id: str, artifact: dict, tmp_path: Path) -> None:
    view = open_governance_world(world)
    try:
        case = assemble_case(
            view,
            case_id=case_id,
            question="Does this call site conform?",
            proposition_ids=(MAIL_PROPOSITION,),
            subject_ids=(_bound(world, MAIL_PROPOSITION),),
        )
    finally:
        view.world.close()
    path = tmp_path / f"{case_id}.json"
    write_artifact(path, artifact)
    report = consumer_reads(case, read_artifact(path))
    assert report["applicability"]["result"] == "APPLIES"
    assert report["world"]["address"]
