"""Opt-in CLI for model-backed GovernanceCase adjudication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .candidate import (
    DEFAULT_POLICY_ID,
    AdoptionPolicy,
    CandidateEvaluationError,
    evaluate_git_candidate,
)
from .model_adjudicator import (
    DEFAULT_MODEL,
    ModelAdjudicationInvocationError,
    ModelAdjudicatorConfig,
    adjudicate_governance_case,
)


def _config(args: argparse.Namespace) -> ModelAdjudicatorConfig:
    return ModelAdjudicatorConfig(
        provider=args.provider,
        model=args.model or DEFAULT_MODEL,
        base_url=args.base_url,
        timeout_seconds=args.timeout,
        max_attempts=args.max_attempts,
    )


def _load_case(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"GovernanceCase must be a JSON object: {path}")
    return payload


def _finding_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": artifact.get("case_id"),
        "context_sufficiency": artifact.get("context_sufficiency"),
        "applicability": [
            {
                "finding_id": item.get("finding_id"),
                "applicability": item.get("applicability"),
            }
            for item in artifact.get("authority_findings") or []
        ],
        "program_findings": [
            {
                "finding_id": item.get("finding_id"),
                "proposition": item.get("proposition"),
                "truth_value": item.get("truth_value"),
                "basis": item.get("basis"),
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
        "validation_result": "VALID",
    }


def _run_one(path: Path, output_dir: Path, config: ModelAdjudicatorConfig) -> dict[str, Any]:
    case = _load_case(path)
    try:
        artifact = adjudicate_governance_case(case, adjudicator_config=config, output_dir=output_dir)
    except ModelAdjudicationInvocationError as exc:
        receipt = exc.receipt
        return {
            "case_id": case.get("case_id"),
            "model/provider": f"{receipt.get('provider')}/{receipt.get('model')}",
            "runtime_status": receipt.get("runtime_status"),
            "validation_result": receipt.get("validation_result"),
            "validation_errors": receipt.get("validation_errors") or [],
            "invocation": receipt,
        }
    result = _finding_summary(artifact)
    result["model/provider"] = f"{config.provider}/{config.model}"
    result["runtime_status"] = "SUCCEEDED"
    result["adjudication_id"] = artifact.get("adjudication_id")
    return result


def _case_files(directory: Path) -> list[Path]:
    if directory.is_file():
        return [directory]
    return sorted(directory.rglob("governance.case.json"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="governance", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    adjudicate = commands.add_parser("adjudicate", help="adjudicate one GovernanceCase with a model")
    adjudicate.add_argument("case", type=Path)
    adjudicate.add_argument("--output-dir", type=Path)
    _add_model_options(adjudicate)

    evaluation = commands.add_parser(
        "adjudication-eval",
        help="run the opt-in model adjudication evaluation over case sidecars",
    )
    evaluation.add_argument("fixture_dir", type=Path)
    evaluation.add_argument("--output-dir", type=Path)
    _add_model_options(evaluation)

    candidate = commands.add_parser(
        "evaluate-candidate",
        help="evaluate an immutable Git candidate against a governed baseline World",
    )
    candidate.add_argument("--repo", type=Path, default=Path("."))
    candidate.add_argument("--baseline", required=True, help="baseline commit or tree")
    candidate.add_argument("--candidate", required=True, help="candidate commit or tree")
    candidate.add_argument("--baseline-world", required=True, type=Path)
    candidate.add_argument("--task", required=True, help="task text or a task-file path")
    candidate.add_argument("--policy", default=DEFAULT_POLICY_ID, help="policy profile name or JSON path")
    candidate.add_argument("--output-dir", type=Path, default=Path("candidate-evaluation"))
    candidate.add_argument("--candidate-iteration", type=int, default=1)
    candidate.add_argument("--parent-candidate-commit")
    candidate.add_argument("--series-baseline-commit")
    candidate.add_argument("--adjudication", type=Path, help="use a prevalidated governance.adjudication.json")
    candidate.add_argument("--purpose", default="")
    _add_model_options(candidate)

    args = parser.parse_args(argv)
    try:
        config = _config(args)
        if args.command == "adjudicate":
            case_path = args.case.resolve()
            output_dir = args.output_dir or case_path.parent
            result = _run_one(case_path, output_dir, config)
            print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
            return 0 if result.get("runtime_status") == "SUCCEEDED" else 1

        if args.command == "evaluate-candidate":
            supplied_adjudication = None
            if args.adjudication is not None:
                supplied_adjudication = args.adjudication
            result = evaluate_git_candidate(
                args.baseline,
                args.candidate,
                args.baseline_world,
                args.task,
                AdoptionPolicy.from_value(args.policy),
                repository=args.repo,
                output_dir=args.output_dir,
                candidate_iteration=args.candidate_iteration,
                parent_candidate_commit=args.parent_candidate_commit,
                series_baseline_commit=args.series_baseline_commit,
                adjudication=supplied_adjudication,
                adjudicator_config=None if supplied_adjudication is not None else config,
                purpose=args.purpose,
            )
            print(
                json.dumps(
                    {
                        "evaluation_id": result.candidate.get("evaluation_id"),
                        "case_id": result.case.get("case_id"),
                        "adjudication_id": result.adjudication.get("adjudication_id"),
                        "adoption_decision_id": result.adoption_decision.get("decision_id"),
                        "outcome": result.adoption_decision.get("outcome"),
                        "revision_brief_id": (result.revision_brief or {}).get("brief_id"),
                        "artifacts": result.artifacts,
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        fixture_dir = args.fixture_dir.resolve()
        output_root = args.output_dir or fixture_dir / "adjudication-eval"
        paths = _case_files(fixture_dir)
        if not paths:
            parser.error(f"no governance.case.json files found under {fixture_dir}")
        results = []
        for path in paths:
            # Keep each case's artifact and receipt separate in an evaluation
            # run, while leaving the input case directory untouched.
            relative = path.parent.relative_to(fixture_dir) if fixture_dir.is_dir() else Path(path.stem)
            results.append(_run_one(path, output_root / relative, config))
        print(json.dumps(results, sort_keys=True, ensure_ascii=False, indent=2))
        return 0 if all(item.get("runtime_status") == "SUCCEEDED" for item in results) else 1
    except ModelAdjudicationInvocationError as error:
        print(json.dumps({"runtime_status": error.receipt.get("runtime_status"), "invocation": error.receipt}, indent=2, sort_keys=True))
        return 1
    except (FileNotFoundError, TypeError, ValueError, OSError, CandidateEvaluationError) as error:
        parser.error(str(error))
    return 2


def _add_model_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-attempts", type=int, default=2)


if __name__ == "__main__":
    raise SystemExit(main())
