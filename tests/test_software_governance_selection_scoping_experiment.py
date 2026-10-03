"""Test-only probe of Design front doors that may lead to a Judgment Case."""

from __future__ import annotations

import ast
import hashlib
import shutil
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.investigation import make_question
from ontology_author.software_governance.judgment import assemble_case, verify_case
from profiles.software_governance_config_v0.build import EXPORT_ID, STATUS_ID
from profiles.software_governance_config_v0.investigate import investigate
from profiles.software_governance_config_v0.judge import judge as judge_config
from profiles.software_governance_v0.judge import judge as judge_mail
from profiles.software_governance_v0.subjects import call_sites_of, subject_named
from tests.software_governance_judgment_fixtures import build_worlds

MAIL_ID = "proposition:outbound-mail"
MAILER_ID = "proposition:approved-mailer"
REPOSITORY = Path(__file__).resolve().parents[1]
TYPESCRIPT = REPOSITORY / "frontend" / "node_modules" / "typescript"


@pytest.fixture(scope="module")
def worlds(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    if shutil.which("node") is None or not TYPESCRIPT.exists():
        pytest.skip("accepted TypeScript producer requires node and installed TypeScript")
    return build_worlds(tmp_path_factory.mktemp("selection-scoping"))


def _published_id(view, relation: str, role: str, value: str) -> str:
    found = [str(row[role]) for row in view.world.relation_rows(relation)
             if str(row[role]) == value]
    if len(found) != 1:
        raise KeyError((relation, role, value))
    return found[0]


def _case(view, proposition: str, subject: str, *, case_id: str, question: str,
          omit: frozenset[str] = frozenset()) -> dict:
    _published_id(view, "governance_proposition", "proposition", proposition)
    _published_id(view, "software_subject", "subject", subject)
    case = assemble_case(view, case_id=case_id, question=question,
                         proposition_ids=(proposition,), subject_ids=(subject,),
                         omit_relations=omit)
    # Judgment's citation check and the separate exact-address discipline both matter.
    assert case["world_address"] == str(view.world.path.parent)
    assert verify_case(view, case) == []
    return case


def _subject_cases(view, subject: str) -> list[dict]:
    _published_id(view, "software_subject", "subject", subject)
    return [_case(view, proposition, subject, case_id=f"subject-{index}",
                  question="What published governance knowledge may concern this subject?")
            for index, proposition in enumerate(view.propositions_for_subject(subject))]


def _proposition_cases(view, proposition: str) -> list[dict]:
    _published_id(view, "governance_proposition", "proposition", proposition)
    return [_case(view, proposition, subject, case_id=f"proposition-{index}",
                  question="Which subjects does this proposition concern?")
            for index, subject in enumerate(view.subjects_for_proposition(proposition))]


def _route_subject(view, record_id: str) -> str:
    found = [str(row["subject"]) for row in view.world.relation_rows("config_route")
             if row["record_id"] == record_id]
    if len(found) != 1:
        raise KeyError(record_id)
    return found[0]


def _cited_ids(artifact: dict) -> set[str]:
    parts = [artifact["applicability"], *artifact["program_findings"]]
    if artifact["conformance"] is not None:
        parts.append(artifact["conformance"])
    return {
        assertion_id
        for part in parts
        for assertion_id in part["assertion_ids"]
    }


def test_subject_front_door_uses_only_established_bindings(worlds):
    view = open_governance_world(worlds["mail"])
    try:
        subject = view.subjects_for_proposition(MAIL_ID)[0]
        cases = _subject_cases(view, subject)
        assert len(cases) == 1
        assert cases[0]["proposition_ids"] == [MAIL_ID]
        assert any(fact["relation"] == "governance_binding" for fact in cases[0]["facts"])
        assert judge_mail(cases[0])["applicability"]["result"] == "APPLIES"
        # A nearby call in the same owner is not another established binding.
        sibling = next(site["subject"] for site in call_sites_of(view, "sendReceipt")
                       if site["subject"] != subject and "notificationGatewaySend" in site["text"])
        assert view.propositions_for_subject(sibling) == []
        assert not view.absence_is_negative(sibling)
        assert sibling not in {row["subject"] for row in view.world.relation_rows("software_subject")}
        with pytest.raises(KeyError):
            _subject_cases(view, sibling)
    finally:
        view.world.close()


def test_proposition_front_door_is_inverse_read_and_keeps_ambiguity(worlds):
    view = open_governance_world(worlds["mail"])
    try:
        cases = _proposition_cases(view, MAIL_ID)
        assert len(cases) == 1
        assert cases[0]["subject_ids"] == view.subjects_for_proposition(MAIL_ID)
        assert _proposition_cases(view, MAILER_ID) == []
        candidates = view.binding_candidates_for_proposition(MAILER_ID)
        assert len(candidates["candidates"]) == 2
        assert candidates["established_subjects"] == []
        assert candidates["questions"][0]["state"] == "UNRESOLVED"
        # An explicit candidate inquiry can carry the unresolved context;
        # proposition navigation cannot present it as a realization.
        candidate = candidates["candidates"][0]["software_subject"]
        inquiry = _case(view, MAILER_ID, candidate, case_id="candidate-inquiry",
                        question="Does this candidate establish the approved mailer?")
        conclusion = judge_mail(inquiry)
        assert conclusion["applicability"]["result"] == "UNKNOWN"
        assert conclusion["context_requests"][0]["gap"] == "construction"
    finally:
        view.world.close()


def test_direct_inquiry_is_case_assembly_not_prejudgment(worlds):
    view = open_governance_world(worlds["config"])
    try:
        export = _route_subject(view, "customer-export")
        health = _route_subject(view, "health")
        bound = _case(view, EXPORT_ID, export, case_id="direct-export",
                      question="Does this proposition apply to this route?")
        offered = _case(view, EXPORT_ID, health, case_id="direct-health",
                        question="Does this proposition apply to this route?")
        assert judge_config(bound)["conformance"]["result"] == "CONFORMS"
        rejected = judge_config(offered)
        assert rejected["applicability"]["result"] == "DOES_NOT_APPLY"
        assert rejected["conformance"] is None
        with pytest.raises(KeyError):
            _case(view, EXPORT_ID, "invented-subject", case_id="invalid",
                  question="Does this proposition apply to this route?")
        with pytest.raises(KeyError):
            _case(view, "invented-proposition", export, case_id="invalid",
                  question="Does this proposition apply to this route?")
        assert view.propositions_for_subject(health) == []
        assert _subject_cases(view, health) == []
        assert not view.absence_is_negative(health)
    finally:
        view.world.close()


def test_change_event_only_supports_current_world_navigation_when_subject_is_supplied(worlds):
    before = open_governance_world(worlds["config"])
    after = open_governance_world(worlds["config_conflict"])
    try:
        old_subject = _route_subject(before, "customer-export")
        current_subject = _route_subject(after, "customer-export")
        old_route = next(row for row in before.world.relation_rows("config_route")
                         if row["subject"] == old_subject)
        current_route = next(row for row in after.world.relation_rows("config_route")
                             if row["subject"] == current_subject)
        assert old_route["path"] == "/customers/export"
        assert current_route["path"] == "/internal/export"
        assert old_subject != current_subject
        assert before.world.world_id == after.world.world_id
        assert before.world.path.parent != after.world.path.parent
        old_case = _case(before, EXPORT_ID, old_subject, case_id="old",
                         question="What concerned the prior subject?")
        current_cases = _subject_cases(after, current_subject)
        assert len(current_cases) == 1
        assert current_cases[0]["world_address"] == str(after.world.path.parent)
        assert current_cases[0]["proposition_ids"] == [EXPORT_ID]
        assert judge_config(current_cases[0])["conformance"]["result"] == "CONFLICTS"
        # The same source record label is not a certified subject correspondence.
        assert old_case["world_address"] != str(after.world.path.parent)
        assert old_case["subject_ids"] != current_cases[0]["subject_ids"]
        with pytest.raises(KeyError):
            _published_id(after, "software_subject", "subject", old_subject)
        with pytest.raises(KeyError):
            _published_id(before, "software_subject", "subject", current_subject)
        assert all(row["software_subject"] != current_subject
                   for row in before.world.relation_rows("governance_binding"))
        assert all(row["software_subject"] != old_subject
                   for row in after.world.relation_rows("governance_binding"))
    finally:
        before.world.close()
        after.world.close()


def test_investigation_followup_expands_context_but_not_judgment_support(worlds):
    view = open_governance_world(worlds["config"])
    try:
        subject = _route_subject(view, "customer-export")
        first = _case(view, EXPORT_ID, subject, case_id="before-path",
                      question="Does this route satisfy the stated route rule?",
                      omit=frozenset({"config_route"}))
        initial = judge_config(first)
        request = initial["context_requests"][0]
        question = make_question(
            question_id="path-followup", question="Which path is published for this route?",
            purpose="complete the bounded judgment context", proposition=EXPORT_ID,
            subject=subject, origin={"case_id": first["case_id"],
                                     "kind": "judgment_request", "request": request},
            structured_need={"need": request["need"], "property": request["property"]},
        )
        result = investigate(view, first, question, {})
        assert result["outcome"] == "CASE_EXPANDED"
        second = result["case"]
        assert second["world_address"] == first["world_address"]
        assert verify_case(view, second) == []
        later = judge_config(second)
        included = {fact["assertion_id"] for fact in second["facts"]}
        assert _cited_ids(later) < included
        assert any(fact["relation"] == "config_member" and fact["assertion_id"] not in _cited_ids(later)
                   for fact in second["facts"])
        assert initial["conformance"]["result"] == "UNKNOWN"
        assert later["conformance"]["result"] == "CONFORMS"
    finally:
        view.world.close()


def test_probe_has_no_new_state_or_historical_application_imports(worlds):
    forbidden = ("ontology_author.design_checkout", "ontology_author.authority",
                 "ontology_author.governance", "ontology_author.semantic_binding",
                 "profiles.design_checkout")
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
               for alias in node.names]
    imports += [node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module]
    assert not any(name == prefix or name.startswith(prefix + ".")
                   for name in imports for prefix in forbidden)
    for bundle in worlds.values():
        digest = hashlib.sha256((bundle / "world.sqlite").read_bytes()).hexdigest()
        view = open_governance_world(bundle)
        try:
            assert view.world.path.parent == bundle
        finally:
            view.world.close()
        assert hashlib.sha256((bundle / "world.sqlite").read_bytes()).hexdigest() == digest
