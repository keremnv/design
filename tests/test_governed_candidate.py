from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ontology_author.authority import construct_authority_world
from ontology_author.governance import create_governance_adjudication
from ontology_author.governance.candidate import (
    AdoptionPolicy,
    BaselineBindingError,
    CandidateEvaluationError,
    decide_candidate_adoption,
    evaluate_git_candidate,
    validate_candidate_adoption_decision,
)
from ontology_author.governance.model_adjudicator import ModelAdjudicatorConfig
from ontology_author.world.core.model import WorldStoreError
from ontology_author.world.runtime.commit import fingerprint_world
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
from tests.test_model_adjudicator import CASE as MODEL_CASE
from tests.test_model_adjudicator import _candidate as conforming_adjudication

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (Path(__file__).resolve().parents[1] / "frontend" / "node_modules" / "typescript").exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def _git(root: Path, *args: str, check: bool = True) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and process.returncode:
        raise AssertionError(process.stderr)
    return process.stdout.strip()


def _commit(root: Path, message: str, *paths: str, allow_empty: bool = False) -> str:
    _git(root, "add", *paths)
    args = ["commit", "-qm", message]
    if allow_empty:
        args.insert(1, "--allow-empty")
    _git(root, *args)
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def git_candidate_fixture(tmp_path: Path) -> dict[str, Path | str]:
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "baseline-spine")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "governance@example.test")
    _git(tmp_path, "config", "user.name", "Governance Test")
    baseline_commit = _commit(
        tmp_path,
        "baseline",
        "src",
        "docs",
        "tsconfig.json",
    )
    result = construct_authority_world(
        tmp_path / "baseline-spine",
        tmp_path / "baseline-world",
        _universe(tmp_path),
        _build_authority,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert result.succeeded, result.errors
    _write(tmp_path, TS_B)
    candidate_commit = _commit(tmp_path, "candidate", "src")
    return {
        "root": tmp_path,
        "baseline": baseline_commit,
        "candidate": candidate_commit,
        "world": tmp_path / "baseline-world",
    }


def _case_without_adjudication(fixture: dict[str, Path | str], output: Path) -> dict:
    with pytest.raises(CandidateEvaluationError, match="requires --adjudication"):
        evaluate_git_candidate(
            str(fixture["baseline"]),
            str(fixture["candidate"]),
            fixture["world"],
            "Simplify the cancellation flow.",
            repository=fixture["root"],
            output_dir=output,
        )
    return json.loads((output / "governance.case.json").read_text(encoding="utf-8"))


def _retarget_adjudication(case: dict) -> dict:
    observation = case["authority"]["observations"][0]["observation_id"]
    attachment = case["selection"][0]["attachment_assertion_id"]
    relation = case["program_context"]["relation_tuples"][0]["evidence_id"]
    delta = case["change"]["triggering_deltas"][0]["evidence_id"]
    return create_governance_adjudication(
        case,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        authority_findings=[
            {
                "finding_id": "af:retention",
                "observation_ids": [observation],
                "attachment_refs": [attachment],
                "applicability": "APPLIES",
                "interpretation_summary": "The initial action enters retention.",
                "evidence_refs": [{"kind": "authority_observation", "id": observation}],
            }
        ],
        program_findings=[
            {
                "finding_id": "pf:retarget",
                "proposition": "The initial action enters the retention flow.",
                "truth_value": "FALSE",
                "side": "NEW",
                "basis": "MECHANICAL",
                "heuristic_dependence": "NOT_MATERIAL",
                "evidence_refs": [
                    {"kind": "relation_tuple", "id": relation},
                    {"kind": "delta", "id": delta},
                ],
            }
        ],
        conformance_findings=[
            {
                "finding_id": "cf:retarget",
                "authority_finding_refs": ["af:retention"],
                "program_finding_refs": ["pf:retarget"],
                "result": "CONFLICTS",
            }
        ],
        decision_right={
            "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
            "outcome": "CONSTRAINED",
            "authority_basis_refs": ["af:retention"],
            "rationale": "The change is bounded by the retention requirement.",
        },
        rationale=[
            {
                "statement": "The candidate retargets the initial action away from retention.",
                "evidence_refs": [
                    {"kind": "authority_observation", "id": observation},
                    {"kind": "relation_tuple", "id": relation},
                ],
            }
        ],
    )


def test_git_candidate_vertical_slice_emits_revision_and_does_not_mutate(
    git_candidate_fixture: dict[str, Path | str], tmp_path: Path
):
    output = tmp_path / "evaluation"
    case = _case_without_adjudication(git_candidate_fixture, output)
    adjudication = _retarget_adjudication(case)
    baseline_fingerprint = fingerprint_world(Path(git_candidate_fixture["world"]))
    head_before = _git(Path(git_candidate_fixture["root"]), "rev-parse", "HEAD")

    result = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        str(git_candidate_fixture["candidate"]),
        git_candidate_fixture["world"],
        "Simplify the cancellation flow.",
        AdoptionPolicy(),
        repository=git_candidate_fixture["root"],
        output_dir=output,
        adjudication=adjudication,
        candidate_iteration=1,
    )

    assert result.adoption_decision["outcome"] == "REVISION_REQUIRED"
    assert result.revision_brief is not None
    assert result.revision_brief["relevant_authority"][0]["observations"][0]["exact_authoritative_text"].startswith(
        'The initial "Cancel subscription" action'
    )
    assert result.revision_brief["relevant_program_findings"][0]["basis"] == "MECHANICAL"
    assert result.revision_brief["candidate_iteration"] == 1
    assert set(result.artifacts) >= {
        "candidate.json",
        "candidate-program",
        "spine.comparison.json",
        "authority.maintenance.json",
        "authority.impact.json",
        "governance.case.json",
        "governance.adjudication.json",
        "candidate.adoption.json",
        "governance.revision.json",
    }
    candidate_record = json.loads((output / "candidate.json").read_text(encoding="utf-8"))
    assert candidate_record["baseline_tree"] != candidate_record["candidate_tree"]
    assert candidate_record["adjudication_id"] == adjudication["adjudication_id"]
    assert candidate_record["adoption_decision_id"] == result.adoption_decision["decision_id"]
    assert candidate_record["baseline_world_binding"]["binding_validated"] is True
    assert candidate_record["baseline_world_binding"]["program_snapshot_id"] == candidate_record[
        "baseline_program_snapshot_id"
    ]
    assert result.adoption_decision["baseline_snapshot_id"] == candidate_record["baseline_snapshot_id"]
    assert result.adoption_decision["candidate_snapshot_id"] == candidate_record["candidate_snapshot_id"]
    assert _git(Path(git_candidate_fixture["root"]), "rev-parse", "HEAD") == head_before
    assert fingerprint_world(Path(git_candidate_fixture["world"])) == baseline_fingerprint

    candidate_world = ConstructionWorld.open(output / "candidate-program" / "world.sqlite")
    try:
        with pytest.raises(WorldStoreError):
            candidate_world.relation_rows("authority_source")
    finally:
        candidate_world.close()


def test_candidate_model_path_is_opt_in_and_writes_invocation_receipt(
    git_candidate_fixture: dict[str, Path | str], tmp_path: Path
):
    class FixtureTransport:
        def generate(self, request):
            case = json.loads(request.case_json)
            payload = _retarget_adjudication(case)
            payload["adjudicator"] = {
                "kind": "MODEL",
                "identity": "fixture-model",
                "version": "fixture-v0",
                "configuration": {},
            }
            return payload

    output = tmp_path / "model-evaluation"
    result = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        str(git_candidate_fixture["candidate"]),
        git_candidate_fixture["world"],
        "Simplify the cancellation flow.",
        repository=git_candidate_fixture["root"],
        output_dir=output,
        adjudicator_config=ModelAdjudicatorConfig(
            provider="fixture", model="fixture-model", max_attempts=1
        ),
        adjudicator_transport=FixtureTransport(),
    )
    receipt = json.loads(
        (output / "governance.adjudication.invocation.json").read_text(encoding="utf-8")
    )
    assert result.adjudication["adjudicator"]["kind"] == "MODEL"
    assert result.adoption_decision["outcome"] == "REVISION_REQUIRED"
    assert receipt["runtime_status"] == "SUCCEEDED"
    assert receipt["case_id"] == result.case["case_id"]
    assert result.candidate["adjudication_invocation_ref"] == (
        "governance.adjudication.invocation.json"
    )


def test_repeated_materialization_has_stable_case_and_program_identity(
    git_candidate_fixture: dict[str, Path | str], tmp_path: Path
):
    first_output = tmp_path / "first"
    first_case = _case_without_adjudication(git_candidate_fixture, first_output)
    adjudication = _retarget_adjudication(first_case)
    first = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        str(git_candidate_fixture["candidate"]),
        git_candidate_fixture["world"],
        "Simplify the cancellation flow.",
        repository=git_candidate_fixture["root"],
        output_dir=first_output,
        adjudication=adjudication,
    )
    second = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        str(git_candidate_fixture["candidate"]),
        git_candidate_fixture["world"],
        "Simplify the cancellation flow.",
        repository=git_candidate_fixture["root"],
        output_dir=tmp_path / "second",
        adjudication=adjudication,
    )
    assert first.case["case_id"] == second.case["case_id"] == first_case["case_id"]
    assert first.candidate["candidate_snapshot_id"] == second.candidate["candidate_snapshot_id"]
    assert first.comparison["program_delta"] == second.comparison["program_delta"]


def test_dirty_worktree_is_not_candidate_material(git_candidate_fixture: dict[str, Path | str], tmp_path: Path):
    output = tmp_path / "evaluation"
    case = _case_without_adjudication(git_candidate_fixture, output)
    adjudication = _retarget_adjudication(case)
    dirty_file = Path(git_candidate_fixture["root"]) / "src/subscription-page.ts"
    dirty_text = "export function SubscriptionPage(): void { openRetentionFlow(); }\n"
    dirty_file.write_text(dirty_text, encoding="utf-8")
    result = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        str(git_candidate_fixture["candidate"]),
        git_candidate_fixture["world"],
        "Simplify the cancellation flow.",
        repository=git_candidate_fixture["root"],
        output_dir=output,
        adjudication=adjudication,
    )
    assert result.case["case_id"] == case["case_id"]
    assert dirty_file.read_text(encoding="utf-8") == dirty_text
    assert _git(Path(git_candidate_fixture["root"]), "status", "--short")


def test_baseline_binding_and_series_baseline_are_strict(
    git_candidate_fixture: dict[str, Path | str], tmp_path: Path
):
    with pytest.raises(BaselineBindingError, match="content differs|snapshot"):
        evaluate_git_candidate(
            str(git_candidate_fixture["candidate"]),
            str(git_candidate_fixture["candidate"]),
            git_candidate_fixture["world"],
            "task",
            repository=git_candidate_fixture["root"],
            output_dir=tmp_path / "mismatch",
            adjudication={"not": "a valid adjudication"},
        )
    with pytest.raises(CandidateEvaluationError, match="series baseline"):
        evaluate_git_candidate(
            str(git_candidate_fixture["baseline"]),
            str(git_candidate_fixture["candidate"]),
            git_candidate_fixture["world"],
            "task",
            repository=git_candidate_fixture["root"],
            output_dir=tmp_path / "series-mismatch",
            series_baseline_commit=str(git_candidate_fixture["candidate"]),
            adjudication={"not": "a valid adjudication"},
        )


def test_iteration_two_uses_same_baseline_and_commit_history_is_provenance_only(
    git_candidate_fixture: dict[str, Path | str], tmp_path: Path
):
    output = tmp_path / "evaluation"
    case = _case_without_adjudication(git_candidate_fixture, output)
    adjudication = _retarget_adjudication(case)
    first = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        str(git_candidate_fixture["candidate"]),
        git_candidate_fixture["world"],
        "task",
        repository=git_candidate_fixture["root"],
        output_dir=output,
        adjudication=adjudication,
        candidate_iteration=1,
    )
    second_commit = _commit(
        Path(git_candidate_fixture["root"]),
        "candidate workflow event with identical tree",
        allow_empty=True,
    )
    second = evaluate_git_candidate(
        str(git_candidate_fixture["baseline"]),
        second_commit,
        git_candidate_fixture["world"],
        "task",
        repository=git_candidate_fixture["root"],
        output_dir=tmp_path / "iteration-two",
        adjudication=adjudication,
        candidate_iteration=2,
        parent_candidate_commit=str(git_candidate_fixture["candidate"]),
        series_baseline_commit=str(git_candidate_fixture["baseline"]),
    )
    assert first.candidate["baseline_tree"] == second.candidate["baseline_tree"]
    assert second.candidate["baseline_tree"] == first.candidate["baseline_tree"]
    assert second.candidate["candidate_tree"] == first.candidate["candidate_tree"]
    assert second.candidate["candidate_commit"] == second_commit
    assert second.candidate["parent_candidate_commit"] == str(git_candidate_fixture["candidate"])
    assert second.comparison["program_delta"]["old_snapshot"] == second.candidate["baseline_program_snapshot_id"]
    assert second.case["case_id"] == first.case["case_id"]


def test_adoption_policy_maps_rights_without_inference_and_records_fallback():
    conforming = conforming_adjudication()
    adopted = decide_candidate_adoption(MODEL_CASE, conforming, AdoptionPolicy())
    assert adopted.outcome == "ADOPT"
    assert adopted.payload["basis"]["explicit_fallback_policy_used"] is None
    constrained_profile = AdoptionPolicy(on_constrained_conforming="ESCALATE")
    assert decide_candidate_adoption(MODEL_CASE, conforming, constrained_profile).outcome == "ESCALATE"

    no_authority_case = copy.deepcopy(MODEL_CASE)
    no_authority_case["case_result"] = "NO_APPLICABLE_AUTHORITY"
    no_authority_case["selection"] = []
    no_authority_case["assembly"] = {
        "completeness_basis": {"status": "COMPLETE", "known_gaps": []}
    }
    no_authority = create_governance_adjudication(
        no_authority_case,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        decision_right={"outcome": "NOT_ESTABLISHED", "rationale": "No applicable authority was selected."},
    )
    conservative = decide_candidate_adoption(no_authority_case, no_authority, AdoptionPolicy())
    defaulted = decide_candidate_adoption(
        no_authority_case,
        no_authority,
        AdoptionPolicy.default_delegation(),
    )
    assert conservative.outcome == "ESCALATE"
    assert defaulted.outcome == "ADOPT"
    assert defaulted.payload["basis"]["explicit_fallback_policy_used"] == "DEFAULT_DELEGATION"

    tampered = defaulted.to_dict()
    tampered["decision_id"] = "decision:nonempty-but-wrong"
    assert any(
        "decision_id is not the deterministic result" in error
        for error in validate_candidate_adoption_decision(
            tampered, no_authority_case, no_authority, AdoptionPolicy.default_delegation()
        )
    )


def test_policy_handles_approval_context_conflict_unknown_and_constrained_conflict():
    constrained = conforming_adjudication()
    approval = copy.deepcopy(constrained)
    approval["decision_right"]["outcome"] = "APPROVAL_REQUIRED"
    approval["adjudication_id"] = "changed"  # force reconstruction below
    approval = create_governance_adjudication(
        MODEL_CASE,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        authority_findings=constrained["authority_findings"],
        program_findings=constrained["program_findings"],
        conformance_findings=constrained["conformance_findings"],
        decision_right={**constrained["decision_right"], "outcome": "APPROVAL_REQUIRED"},
        rationale=constrained["rationale"],
    )
    assert decide_candidate_adoption(MODEL_CASE, approval).outcome == "APPROVAL_REQUIRED"

    context = create_governance_adjudication(
        MODEL_CASE,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        program_findings=[
            {
                "finding_id": "pf:missing",
                "proposition": "The implementation behavior is established.",
                "truth_value": "UNKNOWN",
                "basis": "INTERPRETIVE",
                "finding_context": "INSUFFICIENT",
                "evidence_refs":[{"kind": "program_source", "id": "psrc:checkout"}],
            }
        ],
        decision_right={"outcome": "UNKNOWN", "rationale": "Implementation evidence is absent."},
        context_requests=[
            {
                "request_id": "request:implementation",
                "reason": "Need implementation source.",
                "program_identities": ["program:checkout"],
                "source_evidence_requested": [{"side": "NEW", "program_entity": "program:checkout", "kind": "IMPLEMENTATION"}],
            }
        ],
    )
    assert decide_candidate_adoption(MODEL_CASE, context).outcome == "CONTEXT_REQUIRED"

    conflict = create_governance_adjudication(
        MODEL_CASE,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        authority_findings=[
            {"finding_id": "af:one", "observation_ids": ["obs:gateway"], "applicability": "APPLIES", "interpretation_summary": "Use the gateway.", "evidence_refs": [{"kind": "authority_observation", "id": "obs:gateway"}]},
            {"finding_id": "af:two", "observation_ids": ["obs:gateway"], "applicability": "APPLIES", "interpretation_summary": "Use a direct provider.", "evidence_refs": [{"kind": "authority_observation", "id": "obs:gateway"}]},
        ],
        authority_conflicts=[{"conflict_id": "conflict:gateway", "authority_finding_refs": ["af:one", "af:two"], "issue": "The authority items disagree."}],
        decision_right={"outcome": "UNKNOWN", "rationale": "Precedence is not established."},
    )
    assert decide_candidate_adoption(MODEL_CASE, conflict).outcome == "ESCALATE"

    constrained_conflict = copy.deepcopy(constrained)
    constrained_conflict["conformance_findings"][0]["result"] = "CONFLICTS"
    constrained_conflict = create_governance_adjudication(
        MODEL_CASE,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        authority_findings=constrained["authority_findings"],
        program_findings=constrained["program_findings"],
        conformance_findings=[{**constrained["conformance_findings"][0], "result": "CONFLICTS"}],
        decision_right=constrained["decision_right"],
        rationale=constrained["rationale"],
    )
    assert decide_candidate_adoption(MODEL_CASE, constrained_conflict).outcome == "REVISION_REQUIRED"


def test_adoption_decision_validation_and_iteration_limit():
    adjudication = conforming_adjudication()
    policy = AdoptionPolicy(max_candidate_iterations=1)
    decision = decide_candidate_adoption(MODEL_CASE, adjudication, policy, candidate={"candidate_iteration": 1})
    assert validate_candidate_adoption_decision(
        decision.payload,
        MODEL_CASE,
        adjudication,
        policy,
    ) == []
    with pytest.raises(CandidateEvaluationError, match="max_candidate_iterations"):
        AdoptionPolicy.from_value({"max_candidate_iterations": 0})
