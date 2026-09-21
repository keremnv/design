"""Materialize and optionally run the first governance product experiments.

This is an experiment harness, not a governance layer. It reuses the existing
deterministic test fixtures to export bounded GovernanceCase sidecars, invokes
the configured model only when credentials are present, and prepares a manual
coding-agent handoff for the semantic-drift experiment. It never invokes a
coding agent and never promotes a candidate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ontology_author.authority import (
    construct_authority_world,
    write_case,
)
from ontology_author.governance import (
    AdjudicatorRequest,
    AdjudicatorTransportResponse,
    AdoptionPolicy,
    CandidateEvaluationError,
    ModelAdjudicationInvocationError,
    ModelAdjudicatorConfig,
    adjudicate_governance_case,
    create_governance_adjudication,
    decide_candidate_adoption,
    evaluate_git_candidate,
    validate_governance_adjudication,
    write_candidate_adoption,
)
from ontology_author.governance.model_adjudicator import DEFAULT_MODEL
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
from tests.test_authority_maintenance import _direct_callable_build
from tests.test_governance_adjudication import _case, _compare_worlds
from tests.test_model_adjudicator import CASE as PAYMENT_CASE

TASK = "Simplify the subscription cancellation flow and remove unnecessary indirection."
OUTPUT_NAME = "governance-product-20260915"
CURSOR_MODEL = "composer-2.5"


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _remove_tree(path: Path) -> None:
    """Remove a harness-owned sealed tree, including read-only World output."""

    for child in path.rglob("*"):
        try:
            child.chmod(0o700 if child.is_dir() else 0o600)
        except OSError:
            pass

    def on_error(function: Any, name: str, _error: BaseException) -> None:
        os.chmod(name, 0o700)
        function(name)

    shutil.rmtree(path, onerror=on_error)


def _git(root: Path, *args: str, check: bool = True) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and process.returncode:
        raise RuntimeError(process.stderr.strip() or f"git command failed: {args}")
    return process.stdout.strip()


def _commit(root: Path, message: str, *paths: str, allow_empty: bool = False) -> str:
    _git(root, "add", *paths)
    command = ["commit", "-qm", message]
    if allow_empty:
        command.insert(1, "--allow-empty")
    _git(root, *command)
    return _git(root, "rev-parse", "HEAD")


def _cursor_cli_version() -> str:
    process = subprocess.run(
        ["cursor-agent", "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or "cursor-agent --version failed")
    return (process.stdout.strip().splitlines() or [""])[0]


def _cursor_authenticated() -> bool:
    process = subprocess.run(
        ["cursor-agent", "status"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    return process.returncode == 0 and "logged in" in process.stdout.lower()


class CursorCliAdjudicatorTransport:
    """Experiment-only transport for Cursor Composer in an empty workspace.

    The existing model-adjudicator transport boundary remains the integration
    point. Cursor receives only the request instruction, schema, and case; the
    subprocess has no repository checkout, MCP server, or additional directory
    roots. Stream events are parsed in memory and raw output is never retained.
    """

    def __init__(
        self,
        *,
        model: str = CURSOR_MODEL,
        timeout_seconds: float = 240.0,
        cli_version: str = "",
    ) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.cli_version = cli_version or _cursor_cli_version()

    def generate(self, request: AdjudicatorRequest) -> AdjudicatorTransportResponse:
        prompt = (
            request.instruction
            + "\nOutput schema:\n"
            + json.dumps(request.output_schema, sort_keys=True, separators=(",", ":"))
            + "\nGovernanceCase JSON and case-scoped evidence catalog:\n"
            + request.input_text()
            + request.repair_text()
            + "\nReturn exactly one JSON object and no markdown fences."
        )
        with tempfile.TemporaryDirectory(prefix="cursor-governance-empty-") as workspace:
            process = subprocess.run(
                [
                    "cursor-agent",
                    "--print",
                    "--output-format",
                    "stream-json",
                    "--model",
                    self.model,
                    "--mode",
                    "ask",
                    "--sandbox",
                    "enabled",
                    "--trust",
                    "--workspace",
                    workspace,
                    prompt,
                ],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout_seconds,
            )
        events: list[dict[str, Any]] = []
        for line in process.stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
        init = next(
            (event for event in events if event.get("type") == "system" and event.get("subtype") == "init"),
            None,
        )
        if init is None:
            raise RuntimeError(
                "Cursor stream did not contain system/init; "
                + (process.stderr.strip()[-500:] or "no stderr")
            )
        if init.get("model") != "Composer 2.5":
            raise RuntimeError(f"Cursor model identity was {init.get('model')!r}, expected Composer 2.5")
        if process.returncode:
            raise RuntimeError(process.stderr.strip()[-500:] or "cursor-agent failed")
        result = next(
            (event for event in reversed(events) if event.get("type") == "result"),
            None,
        )
        if not isinstance(result, dict) or result.get("subtype") != "success":
            raise RuntimeError("Cursor stream did not contain a successful result event")
        payload = result.get("result")
        if not isinstance(payload, str):
            raise TypeError("Cursor result event did not contain text JSON")
        return AdjudicatorTransportResponse(
            payload=payload,
            metadata={
                "cursor_cli_version": self.cli_version,
                "cursor_model": init.get("model", ""),
                "session_id": init.get("session_id", ""),
                "request_id": result.get("request_id", ""),
                "duration_ms": result.get("duration_ms", 0),
            },
        )


def _retarget_adjudication(case: dict[str, Any]) -> dict[str, Any]:
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


def _minimal_payment_case(case_id: str, authority_text: str, source_text: str) -> dict[str, Any]:
    case = copy.deepcopy(PAYMENT_CASE)
    case["case_id"] = case_id
    case["authority"]["observations"][0]["reconstructed_text"] = authority_text
    case["program_context"]["source_evidence"][0]["reconstructed_text"] = source_text
    return case


def _export_case(
    root: Path,
    fixture: str,
    case: dict[str, Any],
    expectation: dict[str, Any],
) -> None:
    directory = root / "adjudication-a-f" / fixture
    write_case(case, directory)
    _write_json(
        directory / "fixture.json",
        {"fixture": fixture, "case_id": case.get("case_id"), "expectation": expectation},
    )


def _build_full_case(
    root: Path,
    old_files: dict[str, str],
    new_files: dict[str, str],
    build: Any = _build_authority,
) -> dict[str, Any]:
    old, new, comparison = _compare_worlds(root, old_files, new_files, build)
    try:
        _maintenance, _impact, case = _case(old, new, comparison, root)
        return case
    finally:
        old.close()
        new.close()


def materialize_cases(root: Path) -> list[dict[str, Any]]:
    """Export A-F cases from the existing deterministic fixtures."""

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="governance-live-fixtures-") as temporary:
        scratch = Path(temporary)
        cancellation = _build_full_case(scratch / "a", TS_A, TS_B)
        body_old = {
            **TS_A,
            "src/retention.ts": (
                "export function openRetentionFlow(): void {}\n"
                'export function cancelSubscription(): void { console.log("x"); }\n'
            ),
        }
        body_new = body_old
        body_without_source = _build_full_case(
            scratch / "b", TS_A, body_new, _direct_callable_build("cancelSubscription")
        )
        body_without_source["program_context"]["source_evidence"] = []
        bounded_source = _build_full_case(
            scratch / "c",
            {
                **TS_A,
                "src/retention.ts": (
                    "export function openRetentionFlow(): void {}\n"
                    "export function cancelSubscription(confirmed: boolean): void { if (!confirmed) return; }\n"
                ),
            },
            {
                **TS_A,
                "src/retention.ts": (
                    "export function openRetentionFlow(): void {}\n"
                    "export function cancelSubscription(confirmed: boolean): void { if (!confirmed) return; console.log('x'); }\n"
                ),
            },
            _direct_callable_build("cancelSubscription"),
        )
        cases = {
            "A-cancellation-retarget": (
                cancellation,
                {
                    "context_sufficiency": "SUFFICIENT",
                    "applicability": "APPLIES",
                    "program_basis": "MECHANICAL",
                    "conformance": "CONFLICTS",
                },
            ),
            "B-body-change-without-source": (
                body_without_source,
                {
                    "context_sufficiency": "INSUFFICIENT",
                    "program_basis": "UNKNOWN",
                    "conformance": "UNKNOWN",
                    "context_request": "IMPLEMENTATION",
                },
            ),
            "C-body-change-with-bounded-source": (
                bounded_source,
                {"context_sufficiency": "SUFFICIENT", "program_basis": "INTERPRETIVE"},
            ),
            "D-payment-provider-direct-call": (
                _minimal_payment_case(
                    "case:payment-direct-provider",
                    "Checkout must access payment providers through PaymentGateway.",
                    "return stripe.charge();",
                ),
                {"applicability": "APPLIES", "program_basis": "MECHANICAL"},
            ),
            "E-approval-required-provider-change": (
                _minimal_payment_case(
                    "case:payment-approval-required",
                    "Changing payment provider selection requires security approval.",
                    "return paymentGateway.charge();",
                ),
                {"applicability": "APPLIES", "conformance": "CONFORMS", "decision_right": "APPROVAL_REQUIRED"},
            ),
            "F-authority-conflict": (
                _minimal_payment_case(
                    "case:payment-authority-conflict",
                    "Checkout must access payment providers through PaymentGateway.",
                    "return stripe.charge();",
                ),
                {"authority_state": "AUTHORITY_CONFLICT", "precedence": "UNESTABLISHED"},
            ),
        }
        conflict = cases["F-authority-conflict"][0]
        conflict["authority"]["observations"].append(
            {
                "observation_id": "obs:payment-direct-allowed",
                "standing": "AUTHORITATIVE",
                "reconstructed_text": "Checkout may access payment providers directly.",
            }
        )
        for fixture, (case, expectation) in cases.items():
            _export_case(root, fixture, case, expectation)
            results.append({"fixture": fixture, "case_id": case.get("case_id"), "status": "EXPORTED"})
    return results


def _model_config() -> ModelAdjudicatorConfig:
    provider = os.environ.get("GOVERNANCE_MODEL_PROVIDER", "openrouter")
    model = os.environ.get("GOVERNANCE_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("GOVERNANCE_MODEL_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("OPENROUTER_API_KEY") if provider.lower() == "openrouter" else None
    return ModelAdjudicatorConfig(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        max_attempts=2,
    )


def _cursor_model_config(cli_version: str) -> ModelAdjudicatorConfig:
    return ModelAdjudicatorConfig(
        provider="cursor-cli",
        model=CURSOR_MODEL,
        model_version=cli_version,
        base_url="cursor://cli",
        max_attempts=2,
        identity="cursor-cli:composer-2.5",
    )


def _summary(artifact: dict[str, Any], case: dict[str, Any], receipt: dict[str, Any] | None) -> dict[str, Any]:
    errors = validate_governance_adjudication(artifact, case)
    return {
        "case_id": case.get("case_id"),
        "context_sufficiency": artifact.get("context_sufficiency"),
        "applicability_findings": [
            {
                "finding_id": item.get("finding_id"),
                "applicability": item.get("applicability"),
                "finding_context": item.get("finding_context"),
            }
            for item in artifact.get("authority_findings") or []
        ],
        "program_findings": [
            {
                "finding_id": item.get("finding_id"),
                "truth_value": item.get("truth_value"),
                "basis": item.get("basis"),
                "heuristic_dependence": item.get("heuristic_dependence"),
            }
            for item in artifact.get("program_findings") or []
        ],
        "conformance": [
            {"finding_id": item.get("finding_id"), "result": item.get("result")}
            for item in artifact.get("conformance_findings") or []
        ],
        "authority_conflicts": artifact.get("authority_conflicts") or [],
        "decision_right": artifact.get("decision_right"),
        "context_requests": artifact.get("context_requests") or [],
        "top_level_state": artifact.get("adjudication_state"),
        "schema_validation": "VALID" if not errors else "INVALID",
        "evidence_reference_validation": "VALID" if not errors else errors,
        "repair_attempts": (receipt or {}).get("attempt_count", 0),
    }


def run_live_adjudication(root: Path) -> dict[str, Any]:
    cli_available = shutil.which("cursor-agent") is not None
    configured = cli_available and _cursor_authenticated()
    cli_version = ""
    if cli_available:
        try:
            cli_version = _cursor_cli_version()
        except (OSError, RuntimeError, subprocess.SubprocessError):
            cli_version = ""
    config = _cursor_model_config(cli_version or "unknown")
    transport = (
        CursorCliAdjudicatorTransport(model=CURSOR_MODEL, cli_version=cli_version or "unknown")
        if configured
        else None
    )
    outputs: list[dict[str, Any]] = []
    for case_path in sorted((root / "adjudication-a-f").glob("*/governance.case.json")):
        fixture = case_path.parent.name
        case = json.loads(case_path.read_text(encoding="utf-8"))
        directory = case_path.parent
        if not configured:
            for filename in (
                "governance.adjudication.json",
                "governance.adjudication.invocation.json",
            ):
                stale = directory / filename
                if stale.is_file() or stale.is_symlink():
                    stale.unlink()
            result = {
                "fixture": fixture,
                "case_id": case.get("case_id"),
                "status": "NOT_RUN",
                "reason": "model credentials unavailable" if cli_available else "cursor CLI unavailable",
                "model/provider": f"{config.model}/{config.provider}",
            }
            _write_json(directory / "live.result.json", result)
            outputs.append(result)
            continue
        try:
            artifact = adjudicate_governance_case(
                case,
                adjudicator_config=config,
                transport=transport,
                output_dir=directory,
            )
            receipt = json.loads(
                (directory / "governance.adjudication.invocation.json").read_text(encoding="utf-8")
            )
            result = {
                "fixture": fixture,
                "status": "SUCCEEDED",
                "model/provider": f"{config.model}/{config.provider}",
                **_summary(artifact, case, receipt),
            }
        except ModelAdjudicationInvocationError as error:
            receipt = error.receipt
            result = {
                "fixture": fixture,
                "status": receipt.get("runtime_status", "FAILED_PROVIDER"),
                "model/provider": f"{config.model}/{config.provider}",
                "case_id": case.get("case_id"),
                "schema_validation": receipt.get("validation_result"),
                "evidence_reference_validation": receipt.get("validation_errors") or [],
                "repair_attempts": receipt.get("attempt_count", 0),
            }
        _write_json(directory / "live.result.json", result)
        outputs.append(result)
    _write_json(root / "adjudication-a-f" / "benchmark.summary.json", outputs)
    return {"provider": config.provider, "model": config.model, "results": outputs}


def prepare_semantic_drift(root: Path) -> dict[str, Any]:
    directory = root / "semantic-drift"
    repository = directory / "repository"
    if repository.exists():
        _remove_tree(repository)
    repository.mkdir(parents=True, exist_ok=True)
    _write(repository, MD)
    _spine(repository, TS_A, "baseline-spine")
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "governance-experiment@example.test")
    _git(repository, "config", "user.name", "Governance Experiment")
    baseline_commit = _commit(repository, "baseline S0", "src", "docs", "tsconfig.json")
    governed = construct_authority_world(
        repository / "baseline-spine",
        repository / "baseline-world",
        _universe(repository),
        _build_authority,
        construction_id="governance-experiment-baseline-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    if not governed.succeeded:
        raise RuntimeError("baseline governed World construction failed: " + "; ".join(governed.errors))
    baseline_tree = _git(repository, "rev-parse", f"{baseline_commit}^{{tree}}")
    task_path = directory / "TASK.txt"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(TASK + "\n", encoding="utf-8")
    readme = f"""# Semantic-drift experiment handoff

This directory contains the prepared baseline only. No coding agent was
invoked in this run, so `B1`, `C1`, and `C2` are intentionally absent rather
than fabricated.

Baseline commit: `{baseline_commit}`
Baseline tree: `{baseline_tree}`
Governed World: `repository/baseline-world`
Task: `TASK.txt`

Manual boundary:

1. Starting from commit `{baseline_commit}`, run the same coding agent twice
   with the same model, configuration, task, and ordinary project
   instructions. Record the first clean commits as B1 and C1.
2. Run `uv run governance evaluate-candidate` for C1 with baseline
   `{baseline_commit}` and `repository/baseline-world`.
3. If the decision is `REVISION_REQUIRED`, give only the original task and
   `governance.revision.json` to the governed arm, then commit C2.
4. Re-run evaluation for C2 with the same baseline `{baseline_commit}`.

Do not merge, update refs, promote the governed World, or call repository
search from governance. Record model/configuration and test/typecheck output
beside each candidate when the manual run is performed.
"""
    (directory / "README.md").write_text(readme, encoding="utf-8")
    metadata = {
        "status": "PREPARED_MANUAL_AGENT_BOUNDARY",
        "task": TASK,
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline_tree,
        "repository": "repository",
        "baseline_world": "repository/baseline-world",
        "agent_outputs": "NOT_RUN",
    }
    _write_json(directory / "baseline.json", metadata)
    return metadata


def run_local_controls(root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    """Exercise deterministic candidate/adoption controls without a coding agent."""

    repository = root / "semantic-drift" / "repository"
    baseline_world = repository / "baseline-world"
    baseline_commit = baseline["baseline_commit"]
    candidate_dir = root / "semantic-drift" / "governed" / "candidate-1"
    _write(repository, TS_B)
    candidate_commit = _commit(repository, "manual fixture C1 retarget", "src")
    try:
        evaluate_git_candidate(
            baseline_commit,
            candidate_commit,
            baseline_world,
            TASK,
            repository=repository,
            output_dir=candidate_dir,
        )
    except CandidateEvaluationError:
        pass
    case = json.loads((candidate_dir / "governance.case.json").read_text(encoding="utf-8"))
    adjudication = _retarget_adjudication(case)
    result = evaluate_git_candidate(
        baseline_commit,
        candidate_commit,
        baseline_world,
        TASK,
        repository=repository,
        output_dir=candidate_dir,
        adjudication=adjudication,
        candidate_iteration=1,
    )
    cancellation = {
        "status": "DETERMINISTIC_CONTROL_ONLY",
        "candidate_commit": candidate_commit,
        "candidate_tree": result.candidate["candidate_tree"],
        "adoption_outcome": result.adoption_decision["outcome"],
        "revision_brief_id": (result.revision_brief or {}).get("brief_id"),
    }
    _write_json(root / "semantic-drift" / "governed" / "candidate-1" / "control.result.json", cancellation)

    freedom_repo = root / "legitimate-freedom" / "repository"
    if freedom_repo.exists():
        _remove_tree(freedom_repo)
    _git(
        root / "semantic-drift" / "repository",
        "clone",
        "-q",
        str(root / "semantic-drift" / "repository"),
        str(freedom_repo),
    )
    _git(freedom_repo, "checkout", "-q", baseline_commit)
    # Build a separate baseline for this control with an explicitly declared
    # complete universe containing an unrelated helper. The semantic-drift
    # baseline remains unchanged; this keeps the control's completeness basis
    # honest without changing the governance contracts.
    freedom_baseline_files = dict(TS_A)
    freedom_baseline_files["src/retention.ts"] += (
        "export function formatSubscriptionDate(): string { return ''; }\n"
    )
    _spine(freedom_repo, freedom_baseline_files, "baseline-spine")
    freedom_baseline_commit = _commit(
        freedom_repo,
        "freedom control baseline with unrelated helper",
        "src",
        "docs",
        "tsconfig.json",
    )
    freedom_baseline_tree = _git(
        freedom_repo, "rev-parse", f"{freedom_baseline_commit}^{{tree}}"
    )
    freedom_governed = construct_authority_world(
        freedom_repo / "baseline-spine",
        freedom_repo / "baseline-world",
        _universe(freedom_repo),
        _direct_callable_build("cancelSubscription", include_helper_universe=True),
        construction_id="governance-experiment-freedom-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    if not freedom_governed.succeeded:
        raise RuntimeError(
            "legitimate-freedom governed World construction failed: "
            + "; ".join(freedom_governed.errors)
        )
    freedom_candidate_files = dict(freedom_baseline_files)
    freedom_candidate_files["src/retention.ts"] = freedom_candidate_files["src/retention.ts"].replace(
        "export function formatSubscriptionDate(): string { return ''; }",
        'export function formatSubscriptionDate(): string { return "changed"; }',
    )
    _write(freedom_repo, freedom_candidate_files)
    freedom_commit = _commit(freedom_repo, "manual fixture unrelated helper", "src")
    freedom_dir = root / "legitimate-freedom" / "evaluation"
    try:
        evaluate_git_candidate(
            freedom_baseline_commit,
            freedom_commit,
            freedom_repo / "baseline-world",
            "Update the unrelated formatting helper.",
            AdoptionPolicy.default_delegation(),
            repository=freedom_repo,
            output_dir=freedom_dir,
        )
    except CandidateEvaluationError:
        pass
    freedom_case = json.loads((freedom_dir / "governance.case.json").read_text(encoding="utf-8"))
    freedom_adjudication = create_governance_adjudication(
        freedom_case,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        decision_right={"outcome": "NOT_ESTABLISHED", "rationale": "No applicable authority was selected."},
    )
    freedom_result = evaluate_git_candidate(
        freedom_baseline_commit,
        freedom_commit,
        freedom_repo / "baseline-world",
        "Update the unrelated formatting helper.",
        AdoptionPolicy.default_delegation(),
        repository=freedom_repo,
        output_dir=freedom_dir,
        adjudication=freedom_adjudication,
    )
    freedom = {
        "status": "DETERMINISTIC_CONTROL_ONLY",
        "baseline_commit": freedom_baseline_commit,
        "baseline_tree": freedom_baseline_tree,
        "candidate_commit": freedom_commit,
        "candidate_tree": freedom_result.candidate["candidate_tree"],
        "case_result": freedom_result.case["case_result"],
        "fallback": freedom_result.adoption_decision["basis"]["explicit_fallback_policy_used"],
        "adoption_outcome": freedom_result.adoption_decision["outcome"],
    }
    _write_json(root / "legitimate-freedom" / "control.result.json", freedom)

    approval_case = copy.deepcopy(PAYMENT_CASE)
    approval_adjudication = create_governance_adjudication(
        approval_case,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        authority_findings=[
            {
                "finding_id": "af:approval",
                "observation_ids": ["obs:gateway"],
                "attachment_refs": ["attachment:gateway"],
                "applicability": "APPLIES",
                "interpretation_summary": "Provider changes require security approval.",
                "evidence_refs": [{"kind": "authority_observation", "id": "obs:gateway"}],
            }
        ],
        program_findings=[
            {
                "finding_id": "pf:approval",
                "proposition": "The provider is accessed through PaymentGateway.",
                "truth_value": "TRUE",
                "side": "NEW",
                "basis": "MECHANICAL",
                "heuristic_dependence": "NOT_MATERIAL",
                "evidence_refs": [{"kind": "delta", "id": "delta:retarget"}],
            }
        ],
        conformance_findings=[
            {
                "finding_id": "cf:approval",
                "authority_finding_refs": ["af:approval"],
                "program_finding_refs": ["pf:approval"],
                "result": "CONFORMS",
            }
        ],
        decision_right={
            "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
            "outcome": "APPROVAL_REQUIRED",
            "authority_basis_refs": ["af:approval"],
            "rationale": "Authority reserves provider changes for security approval.",
        },
    )
    approval_decision = decide_candidate_adoption(approval_case, approval_adjudication)
    approval_dir = root / "approval" / "evaluation"
    approval_dir.mkdir(parents=True, exist_ok=True)
    _write_json(approval_dir / "governance.case.json", approval_case)
    _write_json(approval_dir / "governance.adjudication.json", approval_adjudication)
    write_candidate_adoption(approval_decision.payload, approval_dir, case=approval_case, adjudication=approval_adjudication)
    approval = {
        "status": "DETERMINISTIC_CONTROL_ONLY",
        "conformance": "CONFORMS",
        "decision_right": "APPROVAL_REQUIRED",
        "adoption_outcome": approval_decision.outcome,
        "candidate_preserved": True,
        "automatic_human_workflow": False,
    }
    _write_json(root / "approval" / "control.result.json", approval)
    return {"cancellation": cancellation, "legitimate_freedom": freedom, "approval": approval}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / OUTPUT_NAME)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    exported = materialize_cases(root)
    live = run_live_adjudication(root)
    baseline = prepare_semantic_drift(root)
    controls = run_local_controls(root, baseline)
    report = {
        "status": "COMPLETED_WITH_LIVE_STATUS_RECORDED",
        "cases": exported,
        "live_adjudication": live,
        "semantic_drift": baseline,
        "offline_controls": controls,
        "coding_agent": "NOT_RUN",
    }
    _write_json(root / "experiment.summary.json", report)
    print(_json(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
