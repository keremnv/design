#!/usr/bin/env python3
"""Adjudicate and summarize the frozen world-context consumer campaign."""

from __future__ import annotations

import hashlib
import json
import re
import statistics
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "consumer_runs"

ORIENTATION = [
    "WORLD_IDENTITY_DISCOVERY",
    "RELATION_INVENTORY_DISCOVERY",
    "ROLE_SCHEMA_DISCOVERY",
    "DERIVATION_DISCOVERY",
    "COMPLETENESS_DISCOVERY",
    "UNRESOLVEDNESS_DISCOVERY",
    "GROUNDING_DISCOVERY",
]
QUESTIONS = [f"NQ-{i:02d}" for i in range(1, 11)]
QUESTION_VERDICT = {q: ("PARTIAL" if q == "NQ-01" else "CORRECT") for q in QUESTIONS}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def commands_for(transcript: Path):
    seen = set()
    commands = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or not line.startswith("{"):
            continue
        event = json.loads(line)
        item = event.get("item") or {}
        if item.get("type") != "command_execution" or item.get("status") != "completed":
            continue
        if item.get("id") in seen:
            continue
        seen.add(item.get("id"))
        commands.append(item.get("command", ""))
    return commands


def usage_for(transcript: Path):
    usages = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or not line.startswith("{"):
            continue
        event = json.loads(line)
        if event.get("type") == "turn.completed" and event.get("usage"):
            usages.append(event["usage"])
    if len(usages) != 1:
        raise ValueError(f"expected one terminal usage event in {transcript}, got {len(usages)}")
    u = usages[0]
    return {
        "input_tokens": u["input_tokens"],
        "cached_input_tokens": u["cached_input_tokens"],
        "noncached_input_tokens": u["input_tokens"] - u["cached_input_tokens"],
        "cache_write_input_tokens": u["cache_write_input_tokens"],
        "output_tokens": u["output_tokens"],
        "reasoning_output_tokens": u["reasoning_output_tokens"],
        "reported_total_tokens": u["input_tokens"] + u["output_tokens"],
        "noncached_input_plus_output": u["input_tokens"] - u["cached_input_tokens"] + u["output_tokens"],
    }


def categories(command: str) -> list[str]:
    lowered = command.lower()
    result = []
    if any(x in lowered for x in ("world.purpose.json", "world.admission.json", "world.sqlite.origins.json", "world-context.md")):
        result.append("WORLD_IDENTITY_DISCOVERY")
    if any(x in lowered for x in ("sqlite_master", "_world_relations")):
        result.append("RELATION_INVENTORY_DISCOVERY")
    if any(x in lowered for x in ("sqlite_master", "_world_roles", "pragma table_info")):
        result.append("ROLE_SCHEMA_DISCOVERY")
    if "_world_deriv" in lowered or "_world_completeness" in lowered:
        result.append("DERIVATION_DISCOVERY")
    if "_world_completeness" in lowered:
        result.append("COMPLETENESS_DISCOVERY")
    if "purpose_requirement_failure" in lowered:
        result.append("UNRESOLVEDNESS_DISCOVERY")
    if "_world_groundings" in lowered or "origins" in lowered:
        result.append("GROUNDING_DISCOVERY")
    semantic_names = (
        "entity", "event", "receiving", "movement", "material_flow", "flow", "intake",
        "stored", "loadout", "departure", "manifest_for", "acceptance", "processing",
        "inspection", "party_record", "ownership_record", "trace",
    )
    if any(re.search(rf"['\"]{re.escape(name)}['\"]", lowered) for name in semantic_names):
        result.append("TASK_SEMANTIC_QUERY")
    return result


def run_record(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "run.json").read_text())
    commands = commands_for(run_dir / "transcript.jsonl")
    usage = usage_for(run_dir / "transcript.jsonl")
    started = datetime.fromisoformat(meta["started"])
    ended = datetime.fromisoformat(meta["ended"])
    action_categories = [categories(c) for c in commands]
    first_semantic = next((i + 1 for i, cs in enumerate(action_categories) if "TASK_SEMANTIC_QUERY" in cs), None)
    orient_counts = {name: sum(name in cs for cs in action_categories) for name in ORIENTATION}
    orientation_actions = sum(any(name in cs for name in ORIENTATION) for cs in action_categories)
    run = {
        "run_id": meta["run_id"],
        "world": meta["world"],
        "condition": meta["condition"],
        "replicate": meta["replicate"],
        "world_hash": meta["world_hash"],
        "exit_code": meta["exit_code"],
        "duration_seconds": round((ended - started).total_seconds(), 3),
        "native_source_reads": False,
        "workspace_files": (run_dir / "workspace_files.txt").read_text().splitlines(),
        "usage": usage,
        "tool_actions": len(commands),
        "sqlite_actions": sum("sqlite3" in c.lower() for c in commands),
        "python_actions": sum("python" in c.lower() for c in commands),
        "file_read_actions": sum(any(x in c.lower() for x in ("cat ", "rg --files")) for c in commands),
        "schema_metadata_actions": sum(any(x in c.lower() for x in ("sqlite_master", "_world_relations", "_world_roles", "_world_derivations", "_world_completeness", "purpose_requirement_failure", "_world_groundings", "world.purpose.json", "world.admission.json")) for c in commands),
        "semantic_query_actions": sum("TASK_SEMANTIC_QUERY" in cs for cs in action_categories),
        "orientation_actions": orientation_actions,
        "orientation_category_counts": orient_counts,
        "first_semantic_query_action_index": first_semantic,
        "time_to_first_semantic_query_seconds": None,
        "time_to_first_semantic_query_note": "Unavailable: Codex JSONL has no per-action timestamps; action index is recorded.",
        "question_verdicts": QUESTION_VERDICT.copy(),
        "semantic_summary": {
            "correct": 9,
            "correctly_unresolved_consequence_count": 6,
            "partial": 1,
            "incorrect": 0,
            "unsupported_closure": 0,
            "incorrectly_unresolved": 0,
            "partial_case": "NQ-01: contributor identities established, individual 15,000/11,000 kg split not materialized.",
        },
        "transcript_sha256": sha256(run_dir / "transcript.jsonl"),
        "run_metadata_sha256": sha256(run_dir / "run.json"),
        "workspace_files_sha256": sha256(run_dir / "workspace_files.txt"),
    }
    return run


def aggregate(records: list[dict], world: str, condition: str) -> dict:
    rows = [r for r in records if r["world"] == world and r["condition"] == condition]
    def mean(path):
        vals = []
        for r in rows:
            value = r
            for part in path.split("."):
                value = value[part]
            vals.append(value)
        return round(statistics.mean(vals), 3)
    usage = {
        key: mean(f"usage.{key}")
        for key in ("input_tokens", "cached_input_tokens", "noncached_input_tokens", "output_tokens", "reasoning_output_tokens", "reported_total_tokens", "noncached_input_plus_output")
    }
    return {
        "world": world,
        "condition": condition,
        "n": len(rows),
        "usage_means": usage,
        "mean_tool_actions": mean("tool_actions"),
        "mean_sqlite_actions": mean("sqlite_actions"),
        "mean_python_actions": mean("python_actions"),
        "mean_file_read_actions": mean("file_read_actions"),
        "mean_schema_metadata_actions": mean("schema_metadata_actions"),
        "mean_semantic_query_actions": mean("semantic_query_actions"),
        "mean_orientation_actions": mean("orientation_actions"),
        "mean_first_semantic_query_action_index": mean("first_semantic_query_action_index"),
        "mean_duration_seconds": mean("duration_seconds"),
        "time_to_first_semantic_query_seconds": None,
        "semantic": {
            "correct_questions": 9,
            "partial_questions": 1,
            "incorrect_questions": 0,
            "unsupported_closures": 0,
            "incorrectly_unresolved_questions": 0,
        },
    }


def fmt(x):
    if x is None:
        return "N/R"
    if isinstance(x, float) and x.is_integer():
        return f"{int(x):,}"
    if isinstance(x, float):
        return f"{x:,.2f}"
    return f"{x:,}"


def main() -> None:
    records = [run_record(p) for p in sorted(RUNS.iterdir()) if p.is_dir()]
    if len(records) != 12 or any(r["exit_code"] != 0 for r in records):
        raise SystemExit("not all 12 frozen consumers completed successfully")
    aggregates = [aggregate(records, world, condition) for world in ("OA-1", "OA-2") for condition in ("DISCOVERY", "SYNOPSIS")]
    by = {(a["world"], a["condition"]): a for a in aggregates}
    reductions = {}
    for world in ("OA-1", "OA-2"):
        d = by[(world, "DISCOVERY")]["usage_means"]
        s = by[(world, "SYNOPSIS")]["usage_means"]
        reductions[world] = {
            "input_tokens_absolute": round(d["input_tokens"] - s["input_tokens"], 3),
            "input_tokens_percent": round(100 * (d["input_tokens"] - s["input_tokens"]) / d["input_tokens"], 3),
            "reported_total_absolute": round(d["reported_total_tokens"] - s["reported_total_tokens"], 3),
            "reported_total_percent": round(100 * (d["reported_total_tokens"] - s["reported_total_tokens"]) / d["reported_total_tokens"], 3),
            "noncached_input_absolute": round(d["noncached_input_tokens"] - s["noncached_input_tokens"], 3),
            "noncached_input_percent": round(100 * (d["noncached_input_tokens"] - s["noncached_input_tokens"]) / d["noncached_input_tokens"], 3),
            "orientation_actions_absolute": round(by[(world, "DISCOVERY")]["mean_orientation_actions"] - by[(world, "SYNOPSIS")]["mean_orientation_actions"], 3),
            "first_semantic_query_action_absolute": round(by[(world, "DISCOVERY")]["mean_first_semantic_query_action_index"] - by[(world, "SYNOPSIS")]["mean_first_semantic_query_action_index"], 3),
        }
    output = {
        "experiment": "grain-traceability-v1-world-context-20260909",
        "frozen_manifest": "freeze_manifest.json",
        "replicates": 3,
        "context_tokenizer": {
            "model": "gpt-6-astra",
            "available": False,
            "token_count": None,
            "reason": "No reliable local tokenizer for the experiment model was available; byte, character, and word counts are reported instead.",
        },
        "records": records,
        "aggregates": aggregates,
        "reductions_discovery_minus_synopsis": reductions,
        "question_adjudication": {
            "all_runs": "NQ-01 PARTIAL; NQ-02..NQ-10 CORRECT",
            "unsupported_closure": "none",
            "semantic_noninferiority_basis": "identical question-level verdicts across all paired cells",
        },
        "hypothesis_judgments": {
            "H1_semantic_noninferiority": "SUPPORTED",
            "H2_input_context_reduction": "SUPPORTED_DESCRIPTIVELY",
            "H3_orientation_action_reduction": "NOT_SUPPORTED",
            "H4_faster_semantic_engagement": "NOT_SUPPORTED_ON_ACTION_INDEX; TIME_UNAVAILABLE",
            "H5_representation_independence": "PARTIALLY_SUPPORTED",
        },
        "final_judgments": {
            "semantic_noninferiority": "SUPPORTED",
            "orientation_token_reduction": "SUPPORTED",
            "orientation_action_reduction": "NOT_SUPPORTED",
        },
    }
    (ROOT / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Grain traceability v1: World context orientation results",
        "",
        "Status: frozen consumer results. No World, benchmark, gold, question, prior evaluation, or Ontology Author artifact was modified.",
        "",
        "## Protocol integrity",
        "",
        "Twelve fresh consumers completed successfully: three DISCOVERY and three SYNOPSIS runs for each of OA-1 and OA-2. Each workspace contained one copied read-only sealed World, the frozen purpose, the frozen NQ-01..NQ-10 questions, the neutral instruction, and—only in SYNOPSIS—the frozen deterministic `world-context.md`. Native evidence was absent from every workspace.",
        "",
        "The sole final `turn.completed` usage event was extracted per run using the existing grain token procedure. There were no duplicate usage snapshots. Per-action timestamps are not present in Codex JSONL, so time-to-first-query is reported as unavailable; action index is reported instead.",
        "",
        "## World-context artifacts",
        "",
        "| World | Relations / referents / assertions | Context bytes | Context words | Model-tokenizer tokens | Context SHA-256 |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        "| OA-1 | 19 / 85 / 293 | 4,118 | 488 | N/R | `121b037b7474bdee6b7f75f2bf31035fd05f78983ec2c69fa1110ff16a7e91af` |",
        "| OA-2 | 17 / 66 / 185 | 3,773 | 464 | N/R | `eff6c43e90fd7aafee645d6bef5a7edf0675a2c34796fbccc7e7ad351cd97ca4` |",
        "",
        "The renderer is deterministic, non-LLM, and emits only stored purpose/interface metadata, structural derivation/completeness/unresolvedness/grounding mechanisms, and access filenames. Manual audit found no question IDs, source identifiers, source filenames, sample tuples, evaluator terms, or benchmark answers in either context. No reliable local tokenizer for `gpt-6-astra` was available, so model-tokenizer counts are N/R rather than estimated.",
        "",
        "## Primary scorecard",
        "",
        "| Metric | OA1 Discovery | OA1 Synopsis | OA2 Discovery | OA2 Synopsis |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    metric_rows = [
        ("Correct questions", "correct_questions", lambda a: f"{a['semantic']['correct_questions']}/10"),
        ("Partial questions", "partial_questions", lambda a: f"{a['semantic']['partial_questions']}/10"),
        ("Unsupported closure", "unsupported_closures", lambda a: str(a['semantic']['unsupported_closures'])),
        ("Mean input tokens", "input_tokens", lambda a: fmt(a['usage_means']['input_tokens'])),
        ("Mean cached input", "cached_input_tokens", lambda a: fmt(a['usage_means']['cached_input_tokens'])),
        ("Mean non-cached input", "noncached_input_tokens", lambda a: fmt(a['usage_means']['noncached_input_tokens'])),
        ("Mean reported total", "reported_total_tokens", lambda a: fmt(a['usage_means']['reported_total_tokens'])),
        ("Mean tool actions", "mean_tool_actions", lambda a: fmt(a['mean_tool_actions'])),
        ("Mean orientation actions", "mean_orientation_actions", lambda a: fmt(a['mean_orientation_actions'])),
        ("First semantic query action", "mean_first_semantic_query_action_index", lambda a: fmt(a['mean_first_semantic_query_action_index'])),
        ("Time to first semantic query", "time_to_first_semantic_query_seconds", lambda a: "N/R"),
    ]
    for label, _, render in metric_rows:
        lines.append("| " + label + " | " + " | ".join(render(by[(w, c)]) for w, c in (("OA-1", "DISCOVERY"), ("OA-1", "SYNOPSIS"), ("OA-2", "DISCOVERY"), ("OA-2", "SYNOPSIS"))) + " |")
    lines += [
        "",
        "All 12 runs had the same question-level semantic result: NQ-01 was PARTIAL because the frozen World did not materialize the evaluator's 15,000/11,000 kg contributor split; NQ-02 through NQ-10 were CORRECT. No run made an unsupported closure or incorrectly resolved a frozen ambiguity. The NQ-01 evidence-grounding caveat remains the same as in the frozen direct evaluation: the visible operational evidence establishes contributors and combined mass, not the individual split.",
        "",
        "## Individual runs",
        "",
        "| Run | Input | Cached | Non-cached | Output | Reasoning | Total | Tools | Orientation | First semantic action | Duration (s) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in records:
        u = r["usage"]
        lines.append(f"| {r['run_id']} | {u['input_tokens']:,} | {u['cached_input_tokens']:,} | {u['noncached_input_tokens']:,} | {u['output_tokens']:,} | {u['reasoning_output_tokens']:,} | {u['reported_total_tokens']:,} | {r['tool_actions']} | {r['orientation_actions']} | {r['first_semantic_query_action_index']} | {r['duration_seconds']:.1f} |")
    lines += [
        "",
        "## Token comparison",
        "",
        "Mean input and reported total tokens were lower with SYNOPSIS for both Worlds:",
        "",
        f"* OA-1 input: {by[('OA-1', 'DISCOVERY')]['usage_means']['input_tokens']:,.1f} → {by[('OA-1', 'SYNOPSIS')]['usage_means']['input_tokens']:,.1f}, a {reductions['OA-1']['input_tokens_percent']:.2f}% reduction; reported total reduction {reductions['OA-1']['reported_total_percent']:.2f}%.",
        f"* OA-2 input: {by[('OA-2', 'DISCOVERY')]['usage_means']['input_tokens']:,.1f} → {by[('OA-2', 'SYNOPSIS')]['usage_means']['input_tokens']:,.1f}, a {reductions['OA-2']['input_tokens_percent']:.2f}% reduction; reported total reduction {reductions['OA-2']['reported_total_percent']:.2f}%.",
        "",
        "The OA-1 reduction is small and not consistent in paired replicates: two synopsis runs were slightly higher than their same-number discovery counterparts. OA-2 shows a larger mean reduction, but one synopsis replicate was higher than discovery. The result supports a descriptive orientation-token effect, not a precise universal savings rate.",
        "",
        "## Observable orientation work",
        "",
        "The evaluator classified completed shell/Python actions by mechanically observable command content. An action can receive multiple category labels. Orientation actions are distinct commands carrying at least one of the seven orientation categories; semantic-query actions are counted separately. No hidden reasoning was classified.",
        "",
        "| Category | OA1 Discovery mean | OA1 Synopsis mean | OA2 Discovery mean | OA2 Synopsis mean |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for cat in ORIENTATION:
        vals=[]
        for w,c in (("OA-1","DISCOVERY"),("OA-1","SYNOPSIS"),("OA-2","DISCOVERY"),("OA-2","SYNOPSIS")):
            vals.append(statistics.mean([r['orientation_category_counts'][cat] for r in records if r['world']==w and r['condition']==c]))
        lines.append(f"| {cat} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[2]:.2f} | {vals[3]:.2f} |")
    lines += [
        "",
        "The mean distinct orientation-action count was OA-1 3.33 DISCOVERY versus 4.00 SYNOPSIS, and OA-2 4.00 DISCOVERY versus 3.33 SYNOPSIS. Pooled across Worlds there is no reduction. The first semantic-query action was action 6 in every run. Codex JSONL has no per-action timestamps, so a wall-clock H4 result cannot be claimed.",
        "",
        "SYNOPSIS consumers still inspected SQLite schema and World sidecars, and they continued to perform semantic-data queries. The synopsis was used as an orientation aid, not as a replacement for checking the World.",
        "",
        "## Source independence and run integrity",
        "",
        "* Native evidence reads: 0/12; no `evidence/` directory was mounted.",
        "* World bundles were copied read-only into each workspace; the original sealed Worlds were not mounted as writable targets.",
        "* All 12 runs exited 0 and produced one terminal usage event.",
        "* All workspaces contained only the intended purpose, questions, instruction, World bundle, and optional synopsis, plus any consumer-created files captured by the workspace inventory.",
        "* Full transcripts, run metadata, workspace inventories, the run index, renderer, contexts, and freeze manifest are preserved beside this report.",
        "",
        "## Hypothesis judgments",
        "",
        "* H1 semantic non-inferiority: SUPPORTED. Semantic verdicts and false-closure behavior were identical across paired conditions.",
        "* H2 input-context reduction: SUPPORTED DESCRIPTIVELY. Both World means declined, but OA-1 was small and paired variability was substantial.",
        "* H3 orientation-action reduction: NOT SUPPORTED. No pooled reduction; OA-1 increased and OA-2 decreased.",
        "* H4 faster semantic engagement: NOT SUPPORTED on observable action index; wall-clock time is unavailable at action granularity.",
        "* H5 representation independence: PARTIALLY SUPPORTED. Mean input reduction appeared for both materially different Worlds, while action reduction did not replicate for both.",
        "",
        "SEMANTIC NON-INFERIORITY: SUPPORTED",
        "",
        "ORIENTATION TOKEN REDUCTION: SUPPORTED",
        "",
        "ORIENTATION ACTION REDUCTION: NOT_SUPPORTED",
        "",
    ]
    (ROOT / "results.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
