"""Investigation v0 acceptance around sealed Construction worlds and Judgment cases."""

from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.judgment import assemble_case, verify_case
from ontology_author.software_governance.reads import GovernanceView
from profiles.software_governance_config_v0.build import EXPORT_ID, STATUS_ID
from ontology_author.software_governance.investigation import (
    InvestigationBoundary,
    citation_errors,
    expanded_case,
)
from profiles.software_governance_config_v0.investigate import investigate
from profiles.software_governance_config_v0.judge import judge
from tests.software_governance_investigation_fixtures import build_worlds

EXPORT_QUESTION = "Does this route satisfy the stated route rule?"


@pytest.fixture(scope="module")
def worlds(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build_worlds(tmp_path_factory.mktemp("investigation-v0"))


def test_same_world_expansion_then_conforms(worlds: dict[str, Path]) -> None:
    database = worlds["accepted"] / "world.sqlite"
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    view = open_governance_world(worlds["accepted"])
    try:
        subject = _export_subject(view)
        case = _case(view, "export-without-path", EXPORT_ID, subject, omit=frozenset({"config_route"}))
        judgment = judge(case)
        frozen = copy.deepcopy(judgment)
        question = _path_question(case, subject, judgment)
        result = investigate(view, case, question, {})
        assert result["outcome"] == "CASE_EXPANDED"
        expanded = result["case"]
        assert verify_case(view, expanded) == []
        assert expanded["world_id"] == case["world_id"]
        assert expanded["revision"] == case["revision"]
        assert expanded["world_address"] == case["world_address"]
        assert expanded["proposition_ids"] == case["proposition_ids"]
        assert expanded["subject_ids"] == case["subject_ids"]
        assert {fact["assertion_id"] for fact in case["facts"]} < {
            fact["assertion_id"] for fact in expanded["facts"]
        }
        added = [
            fact for fact in expanded["facts"]
            if fact["assertion_id"] in result["receipt"]["added_assertion_ids"]
        ]
        assert {fact["relation"] for fact in added} == {"config_route"}
        later = judge(expanded)
    finally:
        view.world.close()
    assert judgment == frozen
    assert judgment["applicability"]["result"] == "APPLIES"
    assert judgment["conformance"]["result"] == "UNKNOWN"
    assert judgment["context_requests"][0]["need"] == "subject_property"
    assert judgment["context_requests"][0]["property"] == "path"
    assert later["conformance"]["result"] == "CONFORMS"
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert set(expanded) == set(case)
    assert "chain_of_thought" not in result["receipt"]


def test_exploration_is_broader_than_the_judgment_basis(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["accepted"])
    try:
        subject = _export_subject(view)
        case = _case(view, "export-broad", EXPORT_ID, subject, omit=frozenset({"config_route"}))
        judgment = judge(case)
        question = _path_question(case, subject, judgment)
        result = investigate(view, case, question, {})
        expanded = result["case"]
        later = judge(expanded)
        member = next(fact for fact in expanded["facts"] if fact["relation"] == "config_member")
        cited = _cited(later)
    finally:
        view.world.close()
    assert judgment["context_requests"][0]["property"] == "path"
    assert "config_member" in result["receipt"]["inspected_relations"]
    assert "config_route" in result["receipt"]["inspected_relations"]
    assert member["assertion_id"] not in result["receipt"]["added_assertion_ids"]
    assert member["assertion_id"] in {fact["assertion_id"] for fact in expanded["facts"]}
    assert member["assertion_id"] not in cited
    assert later["program_findings"][0]["assertion_ids"]
    assert set(later["program_findings"][0]["assertion_ids"]) < {
        fact["assertion_id"] for fact in expanded["facts"]
    }


def test_unpublished_source_field_cannot_enter_the_case(worlds: dict[str, Path]) -> None:
    database = worlds["unpublished"] / "world.sqlite"
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    view = open_governance_world(worlds["unpublished"])
    try:
        subject = _export_subject(view)
        case = _case(view, "export-source", EXPORT_ID, subject)
        judgment = judge(case)
        frozen = copy.deepcopy(judgment)
        question = _question(
            "approval-field",
            "What approval step is recorded for this route?",
            case,
            subject,
            structured_need={"need": "subject_property", "property": "approval"},
        )
        result = investigate(view, case, question, {"manifestation-text": _manifestation(view)})
        route = next(fact for fact in case["facts"] if fact["relation"] == "config_route")
        invented = {
            "assertion_id": "invented-approval",
            "relation": "config_route",
            "values": {**route["values"], "approval": "manager-signoff"},
            "support": route["support"],
            "support_fingerprint": route["support_fingerprint"],
            "referent_labels": {},
        }
        decorated = copy.deepcopy(route)
        decorated["values"] = {**route["values"], "approval": "manager-signoff"}
        invented_errors = citation_errors(view, case, invented)
        decorated_errors = citation_errors(view, case, decorated)
    finally:
        view.world.close()
    assert judgment == frozen
    assert judgment["conformance"]["result"] == "CONFORMS"
    assert result["outcome"] == "PROPOSAL"
    assert result["case"] is None
    proposal = result["proposal"]
    assert proposal["epistemic_class"] == "mechanical"
    assert proposal["payload"] == {"field": "approval", "value": "manager-signoff"}
    assert "assertion_id" not in proposal
    assert proposal["basis"]["text"]
    assert "manager-signoff" in proposal["basis"]["text"]
    assert "no assertion" in proposal["reason"]
    assert invented_errors
    assert decorated_errors
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_open_question_does_not_need_a_named_property(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["unpublished"])
    try:
        subject = _export_subject(view)
        case = _case(view, "export-open", EXPORT_ID, subject)
        question = _question(
            "approval-open",
            "Determine whether the required approval behavior is represented for this subject.",
            case,
            subject,
        )
        result = investigate(view, case, question, {"manifestation-text": _manifestation(view)})
        assert verify_case(view, case) == []
    finally:
        view.world.close()
    assert "structured_need" not in question
    assert result["outcome"] == "PROPOSAL"
    assert result["proposal"]["payload"]["field"] == "approval"
    assert result["case"] is None
    assert result["receipt"]["added_assertion_ids"] == []


def test_unresolved_investigation_does_not_invent_a_result(worlds: dict[str, Path]) -> None:
    view = open_governance_world(worlds["unpublished"])
    try:
        subject = _export_subject(view)
        case = _case(view, "export-billing", EXPORT_ID, subject)
        question = _question(
            "billing-open",
            "Determine whether a billing-review step is represented for this subject.",
            case,
            subject,
        )
        result = investigate(view, case, question, {"manifestation-text": _manifestation(view)})
    finally:
        view.world.close()
    assert result["outcome"] == "UNRESOLVED"
    assert result["case"] is None
    assert result["proposal"] is None
    assert result["receipt"]["added_assertion_ids"] == []
    assert result["receipt"]["proposal_id"] is None
    rendered = str(result["receipt"])
    assert "manager-signoff" not in rendered
    assert "billing-review is absent" not in rendered


def test_cross_world_assertion_is_rejected(worlds: dict[str, Path]) -> None:
    accepted = open_governance_world(worlds["accepted"])
    conflict = open_governance_world(worlds["conflict"])
    try:
        subject = _export_subject(accepted)
        case = _case(accepted, "export-home", EXPORT_ID, subject)
        other = _case(conflict, "export-other", EXPORT_ID, _export_subject(conflict))
        foreign = next(fact for fact in other["facts"] if fact["relation"] == "config_route")
        home = next(fact for fact in case["facts"] if fact["relation"] == "config_route")
        assert foreign["referent_labels"].get("subject") == home["referent_labels"].get("subject")
        assert foreign["assertion_id"] != home["assertion_id"]
        assert case["world_id"] == other["world_id"]
        assert case["world_address"] != other["world_address"]
        errors = citation_errors(accepted, case, foreign)
        with pytest.raises(InvestigationBoundary, match="publication"):
            expanded_case(conflict, case, case_id="crossed")
    finally:
        accepted.world.close()
        conflict.world.close()
    assert errors


def test_construction_gap_survives_inspection_and_expansion(worlds: dict[str, Path]) -> None:
    database = worlds["accepted"] / "world.sqlite"
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    view = open_governance_world(worlds["accepted"])
    try:
        subject = _export_subject(view)
        case = _case(view, "status-gap", STATUS_ID, subject)
        judgment = judge(case)
        frozen = copy.deepcopy(judgment)
        question = _question(
            "status-binding",
            "Which subject does this proposition govern?",
            case,
            subject,
            structured_need={"need": "established_binding", "property": ""},
            origin_kind="judgment_request",
            request=judgment["context_requests"][0],
        )
        inspected = investigate(view, case, question, {})
        omitted = _case(
            view,
            "status-gap-omitted",
            STATUS_ID,
            subject,
            omit=frozenset({"config_route"}),
        )
        expanded_result = investigate(view, omitted, question, {})
        expanded = expanded_result["case"]
        later = judge(expanded)
        forged = {
            "assertion_id": "forged-binding",
            "relation": "governance_binding",
            "values": {"proposition": STATUS_ID, "software_subject": subject},
            "support": {"origins": [], "bases": [], "reconstructed": []},
            "support_fingerprint": "0" * 64,
            "referent_labels": {},
        }
        forged_errors = citation_errors(view, expanded, forged)
    finally:
        view.world.close()
    assert judgment == frozen
    assert judgment["applicability"]["result"] == "UNKNOWN"
    assert judgment["conformance"] is None
    assert judgment["context_requests"][0]["gap"] == "construction"
    assert judgment["context_requests"][0]["need"] == "established_binding"
    assert inspected["outcome"] == "UNRESOLVED"
    assert inspected["proposal"] is None
    assert expanded_result["outcome"] == "CASE_EXPANDED"
    assert not any(fact["relation"] == "governance_binding" for fact in expanded["facts"])
    assert later["applicability"]["result"] == "UNKNOWN"
    assert later["conformance"] is None
    assert later["context_requests"][0]["need"] == "established_binding"
    assert forged_errors
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_generic_investigation_stays_above_judgment_and_below_profiles() -> None:
    repository = Path(__file__).resolve().parent.parent
    package = repository / "ontology_author" / "software_governance" / "investigation"
    texts = [path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))]
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
        "approval",
        "billing",
        "GovernanceCase",
        "design_checkout",
    )
    assert [name for name in forbidden if any(name in text for text in texts)] == []
    forbidden_imports = (
        "profiles",
        "ontology_author.program_spine",
        "ontology_author.governance",
        "ontology_author.authority",
        "ontology_author.design_checkout",
        "ontology_author.semantic_binding",
    )
    imported = _imported_modules(package)
    assert [
        module
        for module in imported
        if module in forbidden_imports or module.startswith(tuple(f"{name}." for name in forbidden_imports))
    ] == []
    assert any(
        module == "ontology_author.software_governance.judgment"
        or module.startswith("ontology_author.software_governance.judgment.")
        for module in imported
    )
    judgment = repository / "ontology_author" / "software_governance" / "judgment"
    construction = repository / "ontology_author" / "software_governance"
    world = repository / "ontology_author" / "world"
    for root in (judgment, world):
        assert _imports_investigation(_imported_modules(root)) == []
    construction_modules = _imported_modules(construction, exclude=construction / "investigation")
    assert _imports_investigation(construction_modules) == []
    profile = (repository / "profiles/software_governance_config_v0/investigate.py").read_text(encoding="utf-8")
    assert "PUBLISHED_SOURCE_KEYS" in profile
    assert "approval" not in "\n".join(texts)


def _case(
    view: GovernanceView,
    case_id: str,
    proposition: str,
    subject: str,
    omit: frozenset[str] = frozenset(),
) -> dict:
    case = assemble_case(
        view,
        case_id=case_id,
        question=EXPORT_QUESTION,
        proposition_ids=(proposition,),
        subject_ids=(subject,),
        omit_relations=omit,
    )
    if not omit:
        assert verify_case(view, case) == []
    return case


def _export_subject(view: GovernanceView) -> str:
    matches = [
        str(row["subject"])
        for row in view.world.relation_rows("config_route")
        if row["record_id"] == "customer-export"
    ]
    assert len(matches) == 1
    return matches[0]


def _path_question(case: dict, subject: str, judgment: dict) -> dict:
    request = judgment["context_requests"][0]
    return _question(
        f"{case['case_id']}-path",
        "Which path is recorded for this route?",
        case,
        subject,
        structured_need={"need": request["need"], "property": request["property"]},
        origin_kind="judgment_request",
        request=request,
    )


def _question(
    question_id: str,
    text: str,
    case: dict,
    subject: str,
    *,
    structured_need: dict[str, str] | None = None,
    origin_kind: str = "open",
    request: dict | None = None,
) -> dict:
    from ontology_author.software_governance.investigation import make_question

    origin = {"case_id": case["case_id"], "kind": origin_kind}
    if request is not None:
        origin["request"] = request
    return make_question(
        question_id=question_id,
        question=text,
        purpose="experiment",
        proposition=case["proposition_ids"][0],
        subject=subject,
        origin=origin,
        structured_need=structured_need,
    )


def _manifestation(view: GovernanceView):
    def read(subject: str) -> dict:
        return view.local_manifestation_for_subject(subject)

    return read


def _imported_modules(root: Path, exclude: Path | None = None) -> set[str]:
    modules: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        if exclude is not None and (path == exclude or exclude in path.parents):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
    return modules


def _imports_investigation(modules: set[str]) -> list[str]:
    prefix = "ontology_author.software_governance.investigation"
    return sorted(module for module in modules if module == prefix or module.startswith(f"{prefix}."))


def _cited(artifact: dict) -> set[str]:
    cited = set(artifact["applicability"]["assertion_ids"])
    for finding in artifact["program_findings"]:
        cited.update(finding["assertion_ids"])
    if artifact["conformance"]:
        cited.update(artifact["conformance"]["assertion_ids"])
    for request in artifact["context_requests"]:
        cited.update(request.get("assertion_ids") or [])
    return cited
