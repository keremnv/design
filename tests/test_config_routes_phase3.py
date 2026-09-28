"""Phase 3 production acceptance: bounded continuation from an honest UNKNOWN.

A fresh reader with only an exact sealed World investigates a canonical
guarded UNKNOWN through one product call. No hidden session knowledge, no
World mutation, no automatic admission or publication.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ontology_author.config_routes import (
    construct_config_world,
    inspect_config_world,
    investigate_config_world,
    judge_config_world,
    read_investigation_bundle,
    verify_investigation_bundle,
    verify_judgment_bundle,
)
from ontology_author.config_routes.investigate import investigate_bounded_case
from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.investigation import (
    added_assertion_ids,
    expanded_case,
    make_question,
)
from ontology_author.software_governance.judgment import assemble_case

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPORT = "proposition:customer-export-route"
UNKNOWN_ROUTES = [
    {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
    {"id": "other", "path": "/other", "handler": "CustomerExport"},
]
UNKNOWN_PARAGRAPHS = ("Customer export must use the approved customer-export route.",)


def _construct(tmp_path: Path, routes=None, paragraphs=None, name="W0") -> Path:
    workspace = tmp_path / f"workspace-{name}"
    workspace.mkdir(exist_ok=True)
    (workspace / "software.json").write_text(
        json.dumps({"routes": routes if routes is not None else UNKNOWN_ROUTES}) + "\n",
        encoding="utf-8",
    )
    (workspace / "governance.md").write_text(
        "\n\n".join(paragraphs if paragraphs is not None else UNKNOWN_PARAGRAPHS) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / name
    report = construct_config_world(
        software_source=workspace / "software.json",
        governance_source=workspace / "governance.md",
        output=output,
    )
    assert report.succeeded, report.errors
    del report
    return output


def _subject_for_world(world: Path, route_id: str) -> str:
    inventory = inspect_config_world(world)
    matches = [s["subject"] for s in inventory["subjects"] if s.get("route_id") == route_id]
    assert len(matches) == 1
    return matches[0]


def _hash_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(p for p in root.rglob("*") if p.is_file())
    }


def _unknown_subject(world: Path) -> str:
    return _subject_for_world(world, "other")


def test_unknown_continuation_explains_what_is_missing(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    export = _subject_for_world(address, "customer-export")
    judged = judge_config_world(world=address, proposition=EXPORT, subject=other)
    assert judged["artifact"]["applicability"]["result"] == "UNKNOWN"
    before = _hash_tree(address)
    result = investigate_config_world(world=address, proposition=EXPORT, subject=other)
    assert _hash_tree(address) == before
    assert result["outcome"] == "UNRESOLVED"
    assert result["case"] is None
    assert result["proposal"] is None
    assert result["world"]["address"] == str(address.resolve())
    assert result["trigger"]["applicability"] == "UNKNOWN"
    assert result["trigger"]["case_id"] == judged["case"]["case_id"]
    assert result["receipt"]["outcome"] == "UNRESOLVED"
    assert result["receipt"]["parent_case_id"] == judged["case"]["case_id"]
    assert result["receipt"]["added_assertion_ids"] == []
    assert result["receipt"]["proposal_id"] is None
    explanation = result["explanation"]
    assert explanation["established_subjects_for_proposition"] == [export]
    assert explanation["bound_propositions_for_subject"] == []
    assert explanation["coverage"][0]["status"] == "INCOMPLETE"
    assert f"governance_binding({EXPORT}, {other})" in explanation["missing"]
    assert "already cited by the canonical case" in explanation["why"]
    assert "config_route" in explanation["inspected_relations"]
    json.dumps(result)


def test_canonical_parent_has_no_expansion_left(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    judged = judge_config_world(world=address, proposition=EXPORT, subject=other)
    view = open_governance_world(address)
    try:
        child = expanded_case(view, judged["case"], case_id="reassembled")
        assert added_assertion_ids(judged["case"], child) == []
    finally:
        view.world.close()
    result = investigate_config_world(world=address, proposition=EXPORT, subject=other)
    assert result["outcome"] != "CASE_EXPANDED"


def test_focused_unasserted_field_becomes_proposal(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", "owner": "data-platform"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    judged = judge_config_world(world=address, proposition=EXPORT, subject=other)
    assert judged["artifact"]["applicability"]["result"] == "UNKNOWN"
    before = _hash_tree(address)
    bundle_path = tmp_path / "I0.json"
    result = investigate_config_world(
        world=address, proposition=EXPORT, subject=other,
        question_focus="owner", persist_to=bundle_path,
    )
    assert _hash_tree(address) == before
    assert result["outcome"] == "PROPOSAL"
    assert result["case"] is None
    assert result["persisted_to"] == str(bundle_path.resolve())
    proposal = result["proposal"]
    assert proposal["epistemic_class"] == "mechanical"
    assert proposal["payload"] == {"field": "owner", "value": "data-platform"}
    assert "assertion_id" not in proposal
    assert "assertion_id" not in proposal["payload"]
    assert "assertion_id" not in proposal["basis"]
    assert "data-platform" in proposal["basis"]["text"]
    assert "not an assertion" in proposal["reason"]
    assert result["receipt"]["proposal_id"] == proposal["proposal_id"]
    assert result["receipt"]["resulting_case_id"] is None
    assert result["question"]["structured_need"] == {"need": "subject_property", "property": "owner"}
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    assert verify_investigation_bundle(read_investigation_bundle(bundle_path))["verified"] is True
    json.dumps(result)


def test_unasked_extra_field_stays_unresolved(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", "owner": "data-platform"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    result = investigate_config_world(world=address, proposition=EXPORT, subject=other)
    assert result["outcome"] == "UNRESOLVED"
    assert result["proposal"] is None
    assert result["explanation"]["observed_unasserted_fields"] == ["owner"]
    assert "did not ask about" in result["explanation"]["why"]
    absent = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, question_focus="no-such-field"
    )
    assert absent["outcome"] == "UNRESOLVED"
    assert absent["proposal"] is None


def test_decided_and_refused_judgments_are_not_applicable(tmp_path: Path) -> None:
    conflict_routes = [
        {"id": "customer-export", "path": "/internal/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ]
    address = _construct(tmp_path, routes=conflict_routes)
    export = _subject_for_world(address, "customer-export")
    health = _subject_for_world(address, "health")
    conflict = investigate_config_world(world=address, proposition=EXPORT, subject=export)
    assert conflict["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert "APPLIES/CONFLICTS" in conflict["reason"]
    assert conflict["trigger_outcome"] == "JUDGED"
    excluded = investigate_config_world(world=address, proposition=EXPORT, subject=health)
    assert excluded["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert "DOES_NOT_APPLY" in excluded["reason"]
    conforms_world = _construct(tmp_path, name="W1")
    conforms_subject = _subject_for_world(conforms_world, "customer-export")
    conforms = investigate_config_world(world=conforms_world, proposition=EXPORT, subject=conforms_subject)
    assert conforms["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert "APPLIES/CONFORMS" in conforms["reason"]


def test_unsupported_and_unknown_triggers_refuse_distinctly(tmp_path: Path) -> None:
    address = _construct(
        tmp_path,
        routes=[
            {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
            {"id": "orders-export", "path": "/orders/export", "handler": "OrdersExport"},
        ],
        paragraphs=(
            "Customer export must use the approved customer-export route.",
            "Orders export must use the approved orders-export route.",
        ),
    )
    orders_subject = _subject_for_world(address, "orders-export")
    refused = investigate_config_world(
        world=address, proposition="proposition:orders-export-route", subject=orders_subject
    )
    assert refused["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert refused["trigger_outcome"] == "UNSUPPORTED_EVALUATOR"
    assert "UNSUPPORTED_EVALUATOR" in refused["reason"]
    assert "UNKNOWN" not in refused["reason"].replace("UNKNOWN_PROPOSITION", "").replace("UNKNOWN_SUBJECT", "")
    export = _subject_for_world(address, "customer-export")
    unknown_p = investigate_config_world(world=address, proposition="proposition:absent", subject=export)
    assert unknown_p["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert unknown_p["trigger_outcome"] == "UNKNOWN_PROPOSITION"
    unknown_s = investigate_config_world(world=address, proposition=EXPORT, subject="subject:absent")
    assert unknown_s["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert unknown_s["trigger_outcome"] == "UNKNOWN_SUBJECT"
    with pytest.raises(ValueError, match="question_focus"):
        investigate_config_world(world=address, proposition=EXPORT, subject=export, question_focus="")
    with pytest.raises(ValueError, match="does not exist"):
        investigate_config_world(world=tmp_path / "absent", proposition=EXPORT, subject=export)


def test_supplied_judgment_bundle_trigger(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "J0.json"
    judged = judge_config_world(
        world=address, proposition=EXPORT, subject=other, persist_to=bundle_path
    )
    assert judged["outcome"] == "JUDGED"
    direct = investigate_config_world(world=address, proposition=EXPORT, subject=other)
    supplied = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, judgment=bundle_path
    )
    assert supplied["outcome"] == direct["outcome"] == "UNRESOLVED"
    assert supplied["receipt"] == direct["receipt"]
    assert supplied["question"] == direct["question"]
    tampered = json.loads(bundle_path.read_text(encoding="utf-8"))
    tampered["artifact"]["applicability"]["result"] = "APPLIES"
    refused = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, judgment=tampered
    )
    assert refused["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert "did not verify" in refused["reason"]
    assert refused["trigger_verification"]["verified"] is False
    export = _subject_for_world(address, "customer-export")
    export_bundle = tmp_path / "Jexport.json"
    judge_config_world(world=address, proposition=EXPORT, subject=export, persist_to=export_bundle)
    mismatched = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, judgment=export_bundle
    )
    assert mismatched["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert "different proposition/subject" in mismatched["reason"]


def test_persisted_investigation_verifies_and_tamper_fails(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    result = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, persist_to=bundle_path
    )
    assert result["outcome"] == "UNRESOLVED"
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    with pytest.raises(ValueError, match="already exists"):
        investigate_config_world(
            world=address, proposition=EXPORT, subject=other, persist_to=bundle_path
        )
    link = tmp_path / "Ilink.json"
    link.symlink_to(tmp_path / "Itarget.json")
    with pytest.raises(ValueError, match="already exists|not a fresh file"):
        investigate_config_world(
            world=address, proposition=EXPORT, subject=other, persist_to=link
        )
    assert not (tmp_path / "Itarget.json").exists() and link.is_symlink()
    tampered = read_investigation_bundle(bundle_path)
    tampered["receipt"]["outcome"] = "PROPOSAL"
    assert verify_investigation_bundle(tampered)["verified"] is False
    dropped = read_investigation_bundle(bundle_path)
    del dropped["receipt"]
    shaped = verify_investigation_bundle(dropped)
    assert shaped["verified"] is False
    assert shaped["checks"]["shape"] is False
    truncated = tmp_path / "Itrunc.json"
    truncated.write_text('{"format": "config-routes-investigation/v1",', encoding="utf-8")
    garbled = verify_investigation_bundle(truncated)
    assert garbled["verified"] is False
    assert garbled["checks"]["readable"] is False


def test_proposal_tamper_fails_support_check(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", "owner": "data-platform"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    investigate_config_world(
        world=address, proposition=EXPORT, subject=other,
        question_focus="owner", persist_to=bundle_path,
    )
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    forged = read_investigation_bundle(bundle_path)
    forged["proposal"]["payload"]["value"] = "someone-else"
    verdict = verify_investigation_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["support_sound"] is False
    asserted = read_investigation_bundle(bundle_path)
    asserted["proposal"]["payload"]["assertion_id"] = "invented"
    assert verify_investigation_bundle(asserted)["verified"] is False


def test_substitution_onto_other_publication_fails(tmp_path: Path) -> None:
    first = _construct(tmp_path, name="W0")
    second = _construct(tmp_path, name="W1")
    other = _unknown_subject(first)
    bundle_path = tmp_path / "I0.json"
    investigate_config_world(
        world=first, proposition=EXPORT, subject=other, persist_to=bundle_path
    )
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    substituted = verify_investigation_bundle(bundle_path, world=second)
    assert substituted["verified"] is False
    assert substituted["checks"]["exact_address"] is False


def test_damaged_evidence_refuses_investigation(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    investigate_config_world(
        world=address, proposition=EXPORT, subject=other, persist_to=bundle_path
    )
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    revision = inspect_config_world(address)["software_revisions"][0]
    blob = address / "governance_evidence" / revision.removeprefix("sha256:")
    blob.chmod(0o600)
    payload = bytearray(blob.read_bytes())
    payload[0] ^= 0xFF
    blob.write_bytes(bytes(payload))
    blob.chmod(0o444)
    fresh = judge_config_world(world=address, proposition=EXPORT, subject=other)
    assert fresh["outcome"] == "INVALID_CASE"
    refused = investigate_config_world(world=address, proposition=EXPORT, subject=other)
    assert refused["outcome"] == "INVESTIGATION_NOT_APPLICABLE"
    assert refused["trigger_outcome"] == "INVALID_CASE"
    assert verify_investigation_bundle(bundle_path)["verified"] is False


def test_correction_loop_builds_w1_externally(tmp_path: Path) -> None:
    source = (REPOSITORY_ROOT / "ontology_author" / "config_routes" / "investigate.py").read_text(
        encoding="utf-8"
    )
    assert "construct_config_world" not in source
    assert "from ontology_author.config_routes.construct" not in source
    first = _construct(tmp_path, name="W0")
    other = _unknown_subject(first)
    judgment_path = tmp_path / "J0.json"
    judged = judge_config_world(
        world=first, proposition=EXPORT, subject=other, persist_to=judgment_path
    )
    assert judged["artifact"]["applicability"]["result"] == "UNKNOWN"
    before = _hash_tree(first)
    investigation_path = tmp_path / "I0.json"
    unresolved = investigate_config_world(
        world=first, proposition=EXPORT, subject=other, persist_to=investigation_path
    )
    assert unresolved["outcome"] == "UNRESOLVED"
    assert _hash_tree(first) == before
    # The caller — not the Investigation function — corrects legitimate
    # workspace input: the other route actually uses its own handler.
    # This does not resolve W0's missing binding; it produces a later
    # World where the old question no longer applies.
    workspace = tmp_path / "workspace-W1"
    workspace.mkdir()
    (workspace / "software.json").write_text(
        json.dumps({"routes": [
            {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
            {"id": "other", "path": "/other", "handler": "OtherHandler"},
        ]}) + "\n",
        encoding="utf-8",
    )
    (workspace / "governance.md").write_text(UNKNOWN_PARAGRAPHS[0] + "\n", encoding="utf-8")
    second = tmp_path / "W1"
    rebuilt = construct_config_world(
        software_source=workspace / "software.json",
        governance_source=workspace / "governance.md",
        output=second,
    )
    assert rebuilt.succeeded, rebuilt.errors
    assert _hash_tree(first) == before
    assert inspect_config_world(first)["address"] == str(first.resolve())
    assert verify_judgment_bundle(judgment_path)["verified"] is True
    assert verify_investigation_bundle(investigation_path)["verified"] is True
    assert second.resolve() != first.resolve()
    corrected_subject = _subject_for_world(second, "other")
    corrected = judge_config_world(world=second, proposition=EXPORT, subject=corrected_subject)
    assert corrected["artifact"]["applicability"]["result"] == "DOES_NOT_APPLY"
    assert corrected["artifact"]["conformance"] is None
    still = investigate_config_world(world=first, proposition=EXPORT, subject=other)
    assert still["outcome"] == "UNRESOLVED"


_COLD_HANDOFF = '''\
import json
import sys
from ontology_author.config_routes import (
    construct_config_world,
    inspect_config_world,
    investigate_config_world,
    judge_config_world,
)

role = sys.argv[1]
if role == "A":
    base, workspace = sys.argv[2], sys.argv[3]
    report = construct_config_world(
        software_source=f"{workspace}/software.json",
        governance_source=f"{workspace}/governance.md",
        output=f"{base}/W0",
    )
    print(json.dumps({"constructed": report.succeeded}))
elif role == "B":
    address, judgment_path = sys.argv[2], sys.argv[3]
    inventory = inspect_config_world(address)
    other = next(s["subject"] for s in inventory["subjects"] if s.get("route_id") == "other")
    proposition = next(
        p["proposition"] for p in inventory["propositions"] if "customer-export" in p["proposition"]
    )
    judged = judge_config_world(
        world=address, proposition=proposition, subject=other, persist_to=judgment_path
    )
    print(json.dumps({
        "outcome": judged["outcome"],
        "applicability": judged["artifact"]["applicability"]["result"],
        "proposition": proposition,
        "subject": other,
    }))
else:
    address, judgment_path, investigation_path = sys.argv[2], sys.argv[3], sys.argv[4]
    investigation = investigate_config_world(
        world=address,
        proposition="proposition:customer-export-route",
        subject=sys.argv[5],
        judgment=judgment_path,
        persist_to=investigation_path,
    )
    print(json.dumps({
        "outcome": investigation["outcome"],
        "world": investigation["world"]["address"],
    }))
'''


def test_cold_handoff_across_processes(tmp_path: Path) -> None:
    script = tmp_path / "handoff_probe.py"
    script.write_text(_COLD_HANDOFF, encoding="utf-8")
    workspace = tmp_path / "agent-workspace"
    workspace.mkdir()
    (workspace / "software.json").write_text(
        json.dumps({"routes": UNKNOWN_ROUTES}) + "\n", encoding="utf-8")
    (workspace / "governance.md").write_text(UNKNOWN_PARAGRAPHS[0] + "\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(REPOSITORY_ROOT))

    def run(*args: str) -> dict:
        completed = subprocess.run(
            [sys.executable, str(script), *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout)

    assert run("A", str(tmp_path), str(workspace))["constructed"] is True
    judgment_path = tmp_path / "J0.json"
    balloted = run("B", str(tmp_path / "W0"), str(judgment_path))
    assert balloted["outcome"] == "JUDGED"
    assert balloted["applicability"] == "UNKNOWN"
    investigation_path = tmp_path / "I0.json"
    continued = run(
        "C", str(tmp_path / "W0"), str(judgment_path), str(investigation_path), balloted["subject"]
    )
    assert continued["outcome"] == "UNRESOLVED"
    assert continued["world"] == str((tmp_path / "W0").resolve())
    assert verify_investigation_bundle(investigation_path)["verified"] is True


def _review_table_world(tmp_path: Path) -> tuple[Path, str]:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport",
         "owner": "data-platform", "proposition": "governance_binding(P,S)",
         "binding": "yes", "approved": True},
    ]
    address = _construct(tmp_path, routes=routes)
    return address, _unknown_subject(address)


def test_focus_is_exact_and_exclusive(tmp_path: Path) -> None:
    address, other = _review_table_world(tmp_path)
    assert investigate_config_world(world=address, proposition=EXPORT, subject=other)["outcome"] == "UNRESOLVED"
    for focus in ("missing", "subject"):
        unfocused = investigate_config_world(
            world=address, proposition=EXPORT, subject=other, question_focus=focus
        )
        assert unfocused["outcome"] == "UNRESOLVED", focus
        assert unfocused["proposal"] is None
    owned = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, question_focus="owner"
    )
    assert owned["outcome"] == "PROPOSAL"
    assert owned["proposal"]["payload"] == {"field": "owner", "value": "data-platform"}
    named = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, question_focus="proposition"
    )
    assert named["outcome"] == "PROPOSAL"
    assert named["proposal"]["payload"] == {"field": "proposition", "value": "governance_binding(P,S)"}


@pytest.mark.parametrize(
    ("field", "value", "proposes"),
    [("retry", 3, True), ("ratio", 1.5, True), ("flag", True, True),
     ("note", None, True), ("tags", ["a", "b"], False), ("meta", {"owner": "x"}, False)],
)
def test_proposal_value_scope_is_scalar_only(
    tmp_path: Path, field: str, value: object, proposes: bool
) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", field: value},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    result = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, question_focus=field
    )
    if proposes:
        assert result["outcome"] == "PROPOSAL"
        assert result["proposal"]["payload"] == {"field": field, "value": value}
    else:
        assert result["outcome"] == "UNRESOLVED"
        assert result["proposal"] is None


def test_nested_only_key_never_proposes(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", "meta": {"owner": "nested"}},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    nested = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, question_focus="owner"
    )
    assert nested["outcome"] == "UNRESOLVED"
    assert nested["proposal"] is None


def test_escaped_value_proposes_exact_parsed_value(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", "note": 'a"b\\c'},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    result = investigate_config_world(
        world=address, proposition=EXPORT, subject=other,
        question_focus="note", persist_to=bundle_path,
    )
    assert result["outcome"] == "PROPOSAL"
    assert result["proposal"]["payload"] == {"field": "note", "value": 'a"b\\c'}
    assert verify_investigation_bundle(bundle_path)["verified"] is True


def test_same_value_two_keys_stays_bound_to_focus(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport",
         "owner": "shared", "keeper": "shared"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    result = investigate_config_world(
        world=address, proposition=EXPORT, subject=other,
        question_focus="owner", persist_to=bundle_path,
    )
    assert result["proposal"]["payload"] == {"field": "owner", "value": "shared"}
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    forged = read_investigation_bundle(bundle_path)
    forged["proposal"]["payload"]["field"] = "keeper"
    verdict = verify_investigation_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["support_sound"] is False


@pytest.mark.parametrize("reserved", ["assertion_id", "assertion_ids"])
def test_reserved_identity_names_never_propose(tmp_path: Path, reserved: str) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", reserved: "forged-a123"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    result = investigate_config_world(
        world=address, proposition=EXPORT, subject=other, question_focus=reserved
    )
    assert result["outcome"] == "UNRESOLVED"
    assert result["proposal"] is None
    assert reserved in result["explanation"]["observed_unasserted_fields"]
    honest = investigate_config_world(world=address, proposition=EXPORT, subject=other)
    assert honest["outcome"] == "UNRESOLVED"


def test_forged_reserved_payload_fails_support(tmp_path: Path) -> None:
    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport",
         "owner": "data-platform", "assertion_id": "forged-a123"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    investigate_config_world(
        world=address, proposition=EXPORT, subject=other,
        question_focus="owner", persist_to=bundle_path,
    )
    assert verify_investigation_bundle(bundle_path)["verified"] is True
    forged = read_investigation_bundle(bundle_path)
    forged["request"]["question_focus"] = "assertion_id"
    forged["proposal"]["payload"] = {"field": "assertion_id", "value": "forged-a123"}
    verdict = verify_investigation_bundle(forged)
    assert verdict["verified"] is False
    assert verdict["checks"]["support_sound"] is False


def test_installed_rule_matches_fixture_investigator(tmp_path: Path) -> None:
    from profiles.software_governance_config_v0.investigate import investigate as investigate_fixture

    routes = [
        {"id": "customer-export", "path": "/customers/export", "handler": "CustomerExport"},
        {"id": "other", "path": "/other", "handler": "CustomerExport", "owner": "data-platform"},
    ]
    address = _construct(tmp_path, routes=routes)
    other = _unknown_subject(address)
    view = open_governance_world(address)
    try:
        capabilities = {"manifestation-text": lambda name: view.local_manifestation_for_subject(name)}
        full = assemble_case(
            view,
            case_id="cross-full",
            question="Why does no established correspondence resolve this proposition for this subject under incomplete coverage?",
            proposition_ids=(EXPORT,),
            subject_ids=(other,),
        )
        thinned = assemble_case(
            view,
            case_id="cross-thinned",
            question="Why does no established correspondence resolve this proposition for this subject under incomplete coverage?",
            proposition_ids=(EXPORT,),
            subject_ids=(other,),
            omit_relations=frozenset({"config_route"}),
        )
        plans = [
            (full, None, "open", None),
            (full, {"need": "subject_property", "property": "owner"}, "open", None),
            (thinned, None, "open", None),
        ]
        for index, (case, need, origin_kind, request) in enumerate(plans):
            origin: dict = {"case_id": case["case_id"], "kind": origin_kind}
            if request is not None:
                origin["request"] = request
            question = make_question(
                question_id=f"cross-{index}",
                question="Why does no established correspondence resolve this proposition for this subject under incomplete coverage?",
                purpose="cross-check",
                proposition=EXPORT,
                subject=other,
                origin=origin,
                structured_need=need,
            )
            installed = investigate_bounded_case(view, case, question, capabilities)
            fixture = investigate_fixture(view, case, question, capabilities)
            assert installed["outcome"] == fixture["outcome"]
            assert installed["receipt"] == fixture["receipt"]
            assert installed["proposal"] == fixture["proposal"]
            if installed["case"] is None:
                assert fixture["case"] is None
            else:
                assert fixture["case"] is not None
                assert installed["case"] == fixture["case"]
    finally:
        view.world.close()


def _writable_child_world(tmp_path: Path) -> tuple[Path, str]:
    address = _construct(tmp_path)
    child = address / "governance_evidence"
    child.chmod(0o755)
    assert inspect_config_world(address)["address"] == str(address.resolve())
    return address, _unknown_subject(address)


def test_persist_inside_world_is_refused(tmp_path: Path) -> None:
    address, other = _writable_child_world(tmp_path)
    before = _hash_tree(address)
    with pytest.raises(ValueError, match="inside the sealed World"):
        investigate_config_world(
            world=address, proposition=EXPORT, subject=other,
            persist_to=address / "governance_evidence" / "I-inside.json",
        )
    assert _hash_tree(address) == before
    nested = address / "governance_evidence" / "nested"
    nested.mkdir()
    before_nested = _hash_tree(address)
    with pytest.raises(ValueError, match="inside the sealed World"):
        investigate_config_world(
            world=address, proposition=EXPORT, subject=other,
            persist_to=nested / "I-inside.json",
        )
    assert _hash_tree(address) == before_nested


def test_persist_through_symlink_into_world_is_refused(tmp_path: Path) -> None:
    address, other = _writable_child_world(tmp_path)
    before = _hash_tree(address)
    link = tmp_path / "I-link.json"
    link.symlink_to(address / "governance_evidence" / "I-inside.json")
    with pytest.raises(ValueError, match="inside the sealed World"):
        investigate_config_world(
            world=address, proposition=EXPORT, subject=other, persist_to=link,
        )
    assert _hash_tree(address) == before
    assert not (address / "governance_evidence" / "I-inside.json").exists()


def test_persist_relative_into_world_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    address, other = _writable_child_world(tmp_path)
    before = _hash_tree(address)
    monkeypatch.chdir(address / "governance_evidence")
    with pytest.raises(ValueError, match="inside the sealed World"):
        investigate_config_world(
            world=address, proposition=EXPORT, subject=other, persist_to="I-inside.json"
        )
    assert _hash_tree(address) == before


def _malformed_investigation_cases() -> list[tuple[str, object]]:
    return [
        ("address-none", None),
        ("address-list", []),
        ("address-dict", {}),
        ("address-int", 123),
        ("focus-list", ["owner"]),
        ("focus-dict", {"property": "owner"}),
        ("focus-int", 5),
        ("proposal-list", []),
        ("proposal-str", "proposal"),
        ("receipt-none", None),
        ("receipt-list", []),
        ("case-list", []),
        ("case-dict", {}),
        ("case-str", "case"),
        ("added-str", "added"),
        ("outcome-bogus", "BOGUS"),
        ("outcome-int", 7),
        ("outcome-none", None),
    ]


@pytest.mark.parametrize("name,value", _malformed_investigation_cases())
def test_malformed_investigation_bundles_are_structured_failures(
    tmp_path: Path, name: str, value: object
) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    investigate_config_world(
        world=address, proposition=EXPORT, subject=other, persist_to=bundle_path
    )
    forged = read_investigation_bundle(bundle_path)
    if name.startswith("address-"):
        forged["world"]["address"] = value
    elif name.startswith("focus-"):
        forged["request"]["question_focus"] = value
    elif name.startswith("proposal-"):
        forged["proposal"] = value
    elif name.startswith("receipt-"):
        forged["receipt"] = value
    elif name.startswith("case-"):
        forged["case"] = value
    elif name.startswith("added-"):
        forged["receipt"]["added_assertion_ids"] = value
    else:
        forged["receipt"]["outcome"] = value
    for override in (None, address):
        verdict = (
            verify_investigation_bundle(forged)
            if override is None
            else verify_investigation_bundle(forged, world=override)
        )
        assert verdict["verified"] is False, (name, override)
        assert verdict["errors"], (name, override)


def test_missing_trigger_request_fields_are_structured_failures(tmp_path: Path) -> None:
    address = _construct(tmp_path)
    other = _unknown_subject(address)
    bundle_path = tmp_path / "I0.json"
    investigate_config_world(
        world=address, proposition=EXPORT, subject=other, persist_to=bundle_path
    )
    for block, key in (("trigger", "case_id"), ("request", "proposition"), ("world", "revision")):
        forged = read_investigation_bundle(bundle_path)
        del forged[block][key]
        verdict = verify_investigation_bundle(forged)
        assert verdict["verified"] is False
        assert verdict["checks"]["shape"] is False


def test_expanded_child_metadata_compare_is_exact() -> None:
    from ontology_author.config_routes.investigate import _replay_mismatch

    child = {
        "world_id": "config-routes",
        "revision": 3,
        "case_id": "parent-expanded",
        "question": "q",
        "proposition_ids": ["p"],
        "subject_ids": ["s"],
        "world_address": "/w0",
        "inspected_relations": ["config_route"],
        "facts": [{"assertion_id": "a", "relation": "config_route"}],
    }
    replayed = {"outcome": "CASE_EXPANDED", "receipt": {"outcome": "CASE_EXPANDED"},
                "proposal": None, "case": dict(child)}
    stored = {"question": {}, "receipt": {"outcome": "CASE_EXPANDED"},
              "proposal": None, "case": dict(child)}
    assert _replay_mismatch({}, replayed, stored) == []
    altered = json.loads(json.dumps(stored))
    altered["case"]["inspected_relations"] = []
    assert any("inspected relations" in error for error in _replay_mismatch({}, replayed, altered))
    dropped = json.loads(json.dumps(stored))
    del dropped["case"]["inspected_relations"]
    assert _replay_mismatch({}, replayed, dropped)
    renamed = json.loads(json.dumps(stored))
    renamed["case"]["case_id"] = "other-expanded"
    assert any("case_id" in error for error in _replay_mismatch({}, replayed, renamed))
