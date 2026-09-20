from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    assemble_governance_case,
    assess_attachment_maintenance,
    assess_authority_change_impact,
    construct_authority_world,
    program_world_fingerprint,
    validate_case_sidecar,
)
from ontology_author.governance import (
    AdjudicationError,
    create_governance_adjudication,
    load_governance_adjudication,
    validate_governance_adjudication,
    write_governance_adjudication,
)
from ontology_author.program_spine import compare_program_spines
from ontology_author.evidence.program_source import PROGRAM_INPUTS_DIR
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import (
    MD,
    PROFILE,
    PURPOSE,
    TS_A,
    TS_B,
    _build_authority,
    _spine,
    _universe,
    _write,
)
from tests.test_authority_maintenance import (
    _close,
    _direct_callable_build,
    _sources,
)


pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (Path(__file__).resolve().parents[1] / "frontend" / "node_modules" / "typescript").exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def _unseal_tree(path: Path) -> None:
    path.chmod(path.stat().st_mode | 0o700)
    for child in path.rglob("*"):
        child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))


def _compare_worlds(tmp_path: Path, old_files: dict[str, str], new_files: dict[str, str], build=_build_authority):
    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        build,
        construction_id="adjudication-fixture",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    return old, new, comparison


def _case(old, new, comparison, tmp_path):
    maintenance = assess_attachment_maintenance(old, new, comparison)
    impact = assess_authority_change_impact(old, new, comparison, maintenance=maintenance)
    case = assemble_governance_case(
        old, new, comparison, _sources(tmp_path), maintenance=maintenance, impact=impact, purpose=PURPOSE
    )
    assert validate_case_sidecar(case, maintenance=maintenance, impact=impact, comparison=comparison) == []
    return maintenance, impact, case


def _obs(case, needle: str) -> str:
    for item in case["authority"]["observations"]:
        if needle in (item.get("reconstructed_text") or ""):
            return str(item["observation_id"])
    raise AssertionError(f"no authority observation containing {needle!r}")


def _adjudicator(kind: str = "HUMAN") -> dict[str, str]:
    return {"kind": kind, "identity": "fixture", "version": "v0"}


def test_retarget_case_is_adjudicable_without_function_bodies(tmp_path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        bodies = "\n".join(item.get("reconstructed_text") or "" for item in case["program_context"]["source_evidence"])
        assert "export function" not in bodies
        obs = _obs(case, "enters the retention flow")
        attachment = case["selection"][0]["attachment_assertion_id"]
        finding = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("DETERMINISTIC_CHECK"),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "attachment_refs": [attachment],
                    "applicability": "APPLIES",
                    "interpretation_summary": "The initial cancel action must enter the retention flow.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            program_findings=[
                {
                    "proposition": "The initial cancellation action enters the retention flow.",
                    "truth_value": "FALSE",
                    "basis": "MECHANICAL",
                    "heuristic_dependence": "NOT_MATERIAL",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [
                        {"kind": "relation_tuple", "id": "program_invokes:retarget"},
                        {"kind": "triggering_delta", "id": "program_invokes"},
                    ],
                }
            ],
            conformance_findings=[
                {
                    "authority_finding_refs": [],
                    "program_finding_refs": [],
                    "result": "CONFLICTS",
                }
            ],
            decision_right={
                "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
                "outcome": "PROHIBITED",
                "rationale": "Applicable authority requires retention entry; the new invoke does not.",
            },
            rationale=[
                {
                    "statement": "Authority requires the initial action to enter retention flow.",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                },
                {
                    "statement": "The new program_invokes relation targets cancelSubscription.",
                    "evidence_refs": [{"kind": "relation_tuple", "id": "program_invokes:retarget"}],
                },
            ],
            case_summary="Call-site retarget conflicts with the retention-entry requirement.",
            validate=False,
        )
        finding["authority_findings"][0]["finding_id"] = "afinding:retention"
        finding["program_findings"][0]["finding_id"] = "pfinding:retention"
        finding["conformance_findings"][0]["finding_id"] = "cfinding:retention"
        finding["conformance_findings"][0]["authority_finding_refs"] = ["afinding:retention"]
        finding["conformance_findings"][0]["program_finding_refs"] = ["pfinding:retention"]
        finding["decision_right"]["authority_basis_refs"] = ["afinding:retention"]
        finding["adjudication_id"] = "adjudication:retention-fixture"
        errors = validate_governance_adjudication(finding, case)
        assert errors == []
        assert finding["authority_findings"][0]["applicability"] == "APPLIES"
        assert finding["program_findings"][0]["truth_value"] == "FALSE"
        assert finding["program_findings"][0]["basis"] == "MECHANICAL"
        assert finding["conformance_findings"][0]["result"] == "CONFLICTS"
        assert finding["decision_right"]["outcome"] == "PROHIBITED"
        assert finding["adjudication_state"] == "RESOLVED"
    finally:
        _close(old, new)


def test_callable_manifestation_includes_bounded_old_new_source_not_whole_file(tmp_path):
    old_files = {**TS_A}
    new_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            'export function cancelSubscription(): void { console.log("x"); }\n'
        ),
    }
    old, new, comparison = _compare_worlds(tmp_path, old_files, new_files, _direct_callable_build("cancelSubscription"))
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        evidence = case["program_context"]["source_evidence"]
        assert evidence
        assert {item["side"] for item in evidence} >= {"OLD", "NEW"}
        assert all(item["reconstruction"] == "OK" for item in evidence)
        for item in evidence:
            text = item["reconstructed_text"]
            assert "cancelSubscription" in text
            assert "openRetentionFlow" not in text
            assert "formatSubscriptionDate" not in text
    finally:
        _close(old, new)


def test_program_source_reconstruction_failure_does_not_search_repo(tmp_path):
    old_files = {**TS_A}
    new_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            'export function cancelSubscription(): void { console.log("x"); }\n'
        ),
    }
    old, new, comparison = _compare_worlds(tmp_path, old_files, new_files, _direct_callable_build("cancelSubscription"))
    try:
        for folder in (tmp_path / "world-governed", tmp_path / "world-spine-b"):
            _unseal_tree(folder)
            blob_dir = folder / PROGRAM_INPUTS_DIR
            if blob_dir.exists():
                shutil.rmtree(blob_dir)
        for path in (tmp_path / "src").rglob("*.ts"):
            path.chmod(0)
        case = assemble_governance_case(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        evidence = case["program_context"]["source_evidence"]
        assert evidence
        assert all(item["reconstruction"] == "FAILED" for item in evidence)
        assert all(not (item.get("reconstructed_text") or "") for item in evidence)
        assert case["uncertainty"]["program_source_reconstruction_failures"]
        assert any("could not be reconstructed" in item for item in case["assembly"]["known_omissions"])
    finally:
        _close(old, new)


def test_body_change_without_source_is_insufficient_context(tmp_path):
    old_files = {**TS_A}
    new_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            'export function cancelSubscription(): void { console.log("x"); }\n'
        ),
    }
    old, new, comparison = _compare_worlds(tmp_path, old_files, new_files, _direct_callable_build("cancelSubscription"))
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        case = json.loads(json.dumps(case))
        case["program_context"]["source_evidence"] = []
        obs = _obs(case, "Cancellation occurs only after confirmation")
        callable_id = case["selection"][0]["attachment_warrant"]["program_entity"]
        payload = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("MODEL"),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "applicability": "APPLIES",
                    "interpretation_summary": "Cancellation requires final confirmation.",
                    "finding_context": "INSUFFICIENT",
                    "context_reasons": ["PROGRAM_SOURCE_NOT_IN_CASE"],
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            program_findings=[
                {
                    "proposition": "The changed implementation still prevents cancellation before confirmation.",
                    "truth_value": "UNKNOWN",
                    "basis": "INTERPRETIVE",
                    "heuristic_dependence": "UNKNOWN",
                    "finding_context": "INSUFFICIENT",
                    "context_reasons": ["PROGRAM_BEHAVIOR_NOT_REPRESENTED"],
                    "evidence_refs": [],
                }
            ],
            conformance_findings=[{"result": "UNKNOWN", "authority_finding_refs": [], "program_finding_refs": []}],
            decision_right={"outcome": "UNKNOWN", "rationale": "Required implementation evidence is missing."},
            context_requests=[
                {
                    "reason": "PROGRAM_SOURCE_NOT_IN_CASE",
                    "program_identities": [callable_id],
                    "source_evidence_requested": [
                        {"side": "NEW", "program_entity": callable_id, "kind": "IMPLEMENTATION"}
                    ],
                    "would_enable": "whether confirmation is still enforced",
                }
            ],
            validate=False,
        )
        payload["authority_findings"][0]["finding_id"] = "afinding:confirm"
        payload["program_findings"][0]["finding_id"] = "pfinding:confirm"
        payload["conformance_findings"][0]["finding_id"] = "cfinding:confirm"
        payload["conformance_findings"][0]["authority_finding_refs"] = ["afinding:confirm"]
        payload["conformance_findings"][0]["program_finding_refs"] = ["pfinding:confirm"]
        payload["decision_right"]["authority_basis_refs"] = ["afinding:confirm"]
        payload["adjudication_id"] = "adjudication:insufficient"
        assert validate_governance_adjudication(payload, case) == []
        assert payload["program_findings"][0]["truth_value"] == "UNKNOWN"
        assert payload["conformance_findings"][0]["result"] == "UNKNOWN"
        assert payload["adjudication_state"] == "INSUFFICIENT_CONTEXT"
        assert payload["context_requests"][0]["source_evidence_requested"][0]["kind"] == "IMPLEMENTATION"
    finally:
        _close(old, new)


def test_bounded_source_is_interpretive_not_mechanical(tmp_path):
    old_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(confirmed: boolean): void { if (!confirmed) return; }\n"
        ),
    }
    new_files = {
        **old_files,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(confirmed: boolean): void { if (!confirmed) return; console.log('x'); }\n"
        ),
    }
    old, new, comparison = _compare_worlds(tmp_path, old_files, new_files, _direct_callable_build("cancelSubscription"))
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        new_source = next(
            item
            for item in case["program_context"]["source_evidence"]
            if item["side"] == "NEW" and item["reconstruction"] == "OK"
        )
        assert "if (!confirmed) return;" in new_source["reconstructed_text"]
        obs = _obs(case, "Cancellation occurs only after confirmation")
        payload = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("HUMAN"),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "applicability": "APPLIES",
                    "interpretation_summary": "Cancellation requires confirmation.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            program_findings=[
                {
                    "proposition": "The changed implementation still prevents cancellation before confirmation.",
                    "truth_value": "TRUE",
                    "basis": "INTERPRETIVE",
                    "heuristic_dependence": "NOT_MATERIAL",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "program_source", "id": new_source["evidence_id"]}],
                }
            ],
            conformance_findings=[{"result": "CONFORMS"}],
            decision_right={
                "outcome": "CONSTRAINED",
                "rationale": "Confirmation bound remains in force.",
            },
            validate=False,
        )
        payload["authority_findings"][0]["finding_id"] = "afinding:body"
        payload["program_findings"][0]["finding_id"] = "pfinding:body"
        payload["conformance_findings"][0]["finding_id"] = "cfinding:body"
        payload["conformance_findings"][0]["authority_finding_refs"] = ["afinding:body"]
        payload["conformance_findings"][0]["program_finding_refs"] = ["pfinding:body"]
        payload["decision_right"]["authority_basis_refs"] = ["afinding:body"]
        payload["adjudication_id"] = "adjudication:interpretive"
        assert validate_governance_adjudication(payload, case) == []
        assert payload["program_findings"][0]["basis"] == "INTERPRETIVE"
        mechanical = json.loads(json.dumps(payload))
        mechanical["program_findings"][0]["basis"] = "MECHANICAL"
        assert any("interpretive program source" in error for error in validate_governance_adjudication(mechanical, case))
    finally:
        _close(old, new)


def test_approval_required_independent_of_conformance(tmp_path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        obs = _obs(case, "enters the retention flow")
        payload = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("HUMAN"),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "applicability": "APPLIES",
                    "interpretation_summary": "Changing the payment provider requires security approval.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            program_findings=[
                {
                    "proposition": "Payment provider selection changed through the permitted abstraction.",
                    "truth_value": "TRUE",
                    "basis": "MECHANICAL",
                    "heuristic_dependence": "NOT_MATERIAL",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "relation_tuple", "id": "provider-change"}],
                }
            ],
            conformance_findings=[{"result": "CONFORMS"}],
            decision_right={
                "outcome": "APPROVAL_REQUIRED",
                "rationale": "Authority reserves provider changes for security approval.",
            },
            validate=False,
        )
        payload["authority_findings"][0]["finding_id"] = "afinding:approval"
        payload["program_findings"][0]["finding_id"] = "pfinding:approval"
        payload["conformance_findings"][0]["finding_id"] = "cfinding:approval"
        payload["conformance_findings"][0]["authority_finding_refs"] = ["afinding:approval"]
        payload["conformance_findings"][0]["program_finding_refs"] = ["pfinding:approval"]
        payload["decision_right"]["authority_basis_refs"] = ["afinding:approval"]
        payload["adjudication_id"] = "adjudication:approval"
        assert validate_governance_adjudication(payload, case) == []
        assert payload["conformance_findings"][0]["result"] == "CONFORMS"
        assert payload["decision_right"]["outcome"] == "APPROVAL_REQUIRED"
    finally:
        _close(old, new)


def test_authority_conflict_is_not_program_conflict(tmp_path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        case = json.loads(json.dumps(case))
        obs_a = _obs(case, "enters the retention flow")
        case["authority"]["observations"].append(
            {
                "observation_id": "obs:enterprise-bypass",
                "provider": "markdown",
                "handle": "docs/subscriptions.md",
                "revision": case["authority"]["observations"][0]["revision"],
                "native_location": "fixture:enterprise-bypass",
                "standing": "AUTHORITATIVE",
                "reconstructed_text": "Enterprise plans bypass retention.",
                "reconstruction": "OK",
                "selected_by": [],
            }
        )
        obs_b = "obs:enterprise-bypass"
        payload = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("HUMAN"),
            authority_findings=[
                {
                    "observation_ids": [obs_a],
                    "applicability": "APPLIES",
                    "interpretation_summary": "Cancellation must always enter retention.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs_a}],
                },
                {
                    "observation_ids": [obs_b],
                    "applicability": "APPLIES",
                    "interpretation_summary": "Enterprise plans bypass retention.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs_b}],
                },
            ],
            program_findings=[],
            conformance_findings=[],
            authority_conflicts=[
                {
                    "authority_finding_refs": ["afinding:a", "afinding:b"],
                    "issue": "retention always vs enterprise bypass",
                    "precedence": "UNESTABLISHED",
                }
            ],
            decision_right={"outcome": "UNKNOWN", "rationale": "Conflicting authoritative items; no precedence."},
            validate=False,
        )
        payload["authority_findings"][0]["finding_id"] = "afinding:a"
        payload["authority_findings"][1]["finding_id"] = "afinding:b"
        payload["authority_conflicts"][0]["authority_finding_refs"] = ["afinding:a", "afinding:b"]
        payload["decision_right"]["authority_basis_refs"] = ["afinding:a", "afinding:b"]
        payload["adjudication_id"] = "adjudication:conflict"
        payload["adjudication_state"] = "AUTHORITY_CONFLICT"
        assert validate_governance_adjudication(payload, case) == []
        assert payload["adjudication_state"] == "AUTHORITY_CONFLICT"
        assert payload["decision_right"]["outcome"] == "UNKNOWN"
        assert not payload["conformance_findings"]
        resolved = json.loads(json.dumps(payload))
        resolved["adjudication_state"] = "RESOLVED"
        assert any("authority conflict hidden" in error for error in validate_governance_adjudication(resolved, case))
    finally:
        _close(old, new)


def test_not_established_is_not_delegated_or_unknown(tmp_path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        obs = _obs(case, "enters the retention flow")
        payload = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("HUMAN"),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "applicability": "DOES_NOT_APPLY",
                    "applicability_basis": "The selected paragraph governs retention entry, not this provider-choice subject.",
                    "interpretation_summary": "Does not govern this decision-right subject.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            conformance_findings=[{"result": "NOT_APPLICABLE"}],
            decision_right={"outcome": "NOT_ESTABLISHED", "rationale": "No applicable authority for this subject."},
            empty_case_note="All presented items positively do not apply to the stated subject.",
            validate=False,
        )
        payload["authority_findings"][0]["finding_id"] = "afinding:na"
        payload["conformance_findings"][0]["finding_id"] = "cfinding:na"
        payload["conformance_findings"][0]["authority_finding_refs"] = ["afinding:na"]
        payload["adjudication_id"] = "adjudication:not-established"
        assert validate_governance_adjudication(payload, case) == []
        assert payload["decision_right"]["outcome"] == "NOT_ESTABLISHED"
        delegated = json.loads(json.dumps(payload))
        delegated["decision_right"]["outcome"] = "DELEGATED"
        delegated["decision_right"]["rationale"] = "empty default"
        assert any("DELEGATED" in error for error in validate_governance_adjudication(delegated, case))
        unknown = json.loads(json.dumps(payload))
        unknown["decision_right"]["outcome"] = "UNKNOWN"
        unknown["decision_right"]["authority_basis_refs"] = ["afinding:na"]
        assert unknown["decision_right"]["outcome"] != "NOT_ESTABLISHED"
        assert validate_governance_adjudication(unknown, case) == []
    finally:
        _close(old, new)


def test_validation_rejects_unknown_propagation_and_forbidden_fields(tmp_path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        old_fp = program_world_fingerprint(tmp_path / "world-governed")
        new_fp = program_world_fingerprint(tmp_path / "world-spine-b")
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        obs = _obs(case, "enters the retention flow")
        base = create_governance_adjudication(
            case,
            adjudicator=_adjudicator("MODEL"),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "applicability": "UNKNOWN",
                    "interpretation_summary": "Cannot tell whether this paragraph governs.",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            program_findings=[
                {
                    "proposition": "The initial action enters retention.",
                    "truth_value": "UNKNOWN",
                    "basis": "MECHANICAL",
                    "heuristic_dependence": "MATERIAL",
                    "finding_context": "SUFFICIENT",
                    "evidence_refs": [{"kind": "relation_tuple", "id": "x"}],
                }
            ],
            conformance_findings=[{"result": "UNKNOWN"}],
            decision_right={"outcome": "UNKNOWN", "rationale": "Applicability unknown."},
            validate=False,
        )
        base["authority_findings"][0]["finding_id"] = "afinding:u"
        base["program_findings"][0]["finding_id"] = "pfinding:u"
        base["conformance_findings"][0]["finding_id"] = "cfinding:u"
        base["conformance_findings"][0]["authority_finding_refs"] = ["afinding:u"]
        base["conformance_findings"][0]["program_finding_refs"] = ["pfinding:u"]
        base["decision_right"]["authority_basis_refs"] = ["afinding:u"]
        base["adjudication_id"] = "adjudication:u"
        assert validate_governance_adjudication(base, case) == []
        conforms = json.loads(json.dumps(base))
        conforms["conformance_findings"][0]["result"] = "CONFLICTS"
        conforms["adjudication_state"] = "RESOLVED"
        errors = validate_governance_adjudication(conforms, case)
        assert any("UNKNOWN required findings" in error for error in errors)
        missing_obs = json.loads(json.dumps(base))
        missing_obs["authority_findings"][0]["observation_ids"] = ["obs:missing"]
        assert any("not in the case" in error for error in validate_governance_adjudication(missing_obs, case))
        supporting = json.loads(json.dumps(base))
        case = json.loads(json.dumps(case))
        case.setdefault("supporting_material", [])
        case["supporting_material"].append(
            {
                "observation_id": "obs:notes-support",
                "standing": "AVAILABLE",
                "reconstructed_text": "Editorial note about cancellation copy.",
                "handle": "docs/notes.md",
                "revision": "fixture",
                "native_location": "fixture",
                "provider": "markdown",
                "reconstruction": "OK",
            }
        )
        supporting["authority_findings"][0]["observation_ids"] = ["obs:notes-support"]
        assert any(
            "supporting material" in error for error in validate_governance_adjudication(supporting, case)
        )
        no_apply = json.loads(json.dumps(base))
        no_apply["authority_findings"][0]["applicability"] = "DOES_NOT_APPLY"
        no_apply["authority_findings"][0]["applicability_basis"] = ""
        no_apply["conformance_findings"][0]["result"] = "NOT_APPLICABLE"
        no_apply["program_findings"][0]["truth_value"] = "TRUE"
        no_apply["program_findings"][0]["heuristic_dependence"] = "NOT_MATERIAL"
        no_apply["adjudication_state"] = "RESOLVED"
        assert any("positive cited basis" in error for error in validate_governance_adjudication(no_apply, case))
        true_without = json.loads(json.dumps(base))
        true_without["program_findings"][0]["truth_value"] = "TRUE"
        true_without["program_findings"][0]["heuristic_dependence"] = "NOT_MATERIAL"
        true_without["program_findings"][0]["evidence_refs"] = []
        true_without["authority_findings"][0]["applicability"] = "APPLIES"
        true_without["conformance_findings"][0]["result"] = "UNKNOWN"
        true_without["adjudication_state"] = "UNRESOLVED"
        assert any("no evidence" in error for error in validate_governance_adjudication(true_without, case))
        forbidden = json.loads(json.dumps(base))
        forbidden["confidence"] = 0.9
        forbidden["verdict"] = "FAIL"
        assert any("forbidden field" in error for error in validate_governance_adjudication(forbidden, case))
        material_true = json.loads(json.dumps(base))
        material_true["program_findings"][0]["truth_value"] = "TRUE"
        material_true["program_findings"][0]["heuristic_dependence"] = "MATERIAL"
        material_true["authority_findings"][0]["applicability"] = "APPLIES"
        assert any("MATERIAL heuristic" in error for error in validate_governance_adjudication(material_true, case))
        prior = json.loads(json.dumps(base))
        prior["authority_findings"][0]["applicability"] = "APPLIES"
        prior["program_findings"][0]["truth_value"] = "FALSE"
        prior["program_findings"][0]["heuristic_dependence"] = "NOT_MATERIAL"
        prior["conformance_findings"][0]["result"] = "CONFLICTS"
        prior["conformance_findings"][0]["prior_state"] = "CONFLICTS"
        prior["adjudication_state"] = "RESOLVED"
        prior["decision_right"]["outcome"] = "PROHIBITED"
        prior["decision_right"]["rationale"] = "Old and new both conflict; old code is not authority."
        assert validate_governance_adjudication(prior, case) == []
        assert prior["conformance_findings"][0]["prior_state"] == "CONFLICTS"
        path = write_governance_adjudication(base, tmp_path / "adj")
        loaded = load_governance_adjudication(path)
        assert loaded == base
        repeat = json.loads(json.dumps(base, sort_keys=True))
        assert repeat == base
        for kind in ("HUMAN", "MODEL", "DETERMINISTIC_CHECK"):
            clone = json.loads(json.dumps(base))
            clone["adjudicator"]["kind"] = kind
            assert validate_governance_adjudication(clone, case) == []
        assert program_world_fingerprint(tmp_path / "world-governed") == old_fp
        assert program_world_fingerprint(tmp_path / "world-spine-b") == new_fp
        with pytest.raises(AdjudicationError):
            create_governance_adjudication(
                case,
                adjudicator=_adjudicator(),
                authority_findings=[{"observation_ids": ["missing"], "applicability": "APPLIES"}],
                decision_right={"outcome": "PROHIBITED", "rationale": "x"},
            )
    finally:
        _close(old, new)


def test_missing_context_request_is_rejected(tmp_path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        obs = _obs(case, "enters the retention flow")
        payload = create_governance_adjudication(
            case,
            adjudicator=_adjudicator(),
            authority_findings=[
                {
                    "observation_ids": [obs],
                    "applicability": "APPLIES",
                    "finding_context": "INSUFFICIENT",
                    "context_reasons": ["PROGRAM_SOURCE_NOT_IN_CASE"],
                    "evidence_refs": [{"kind": "authority_observation", "id": obs}],
                }
            ],
            decision_right={"outcome": "UNKNOWN", "rationale": "need more"},
            context_requests=[],
            validate=False,
        )
        payload["authority_findings"][0]["finding_id"] = "afinding:i"
        payload["decision_right"]["authority_basis_refs"] = ["afinding:i"]
        payload["adjudication_id"] = "adjudication:i"
        payload["adjudication_state"] = "INSUFFICIENT_CONTEXT"
        errors = validate_governance_adjudication(payload, case)
        assert any("missing a ContextRequest" in error for error in errors)
    finally:
        _close(old, new)
