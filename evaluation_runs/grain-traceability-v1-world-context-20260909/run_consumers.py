"""Run fresh isolated World-context orientation consumers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/home/kerem/Desktop/Personal Projects/generalauthor")
BENCHMARK = REPO / "grain-traceability-v1"
EXPERIMENT = REPO / "evaluation_runs/grain-traceability-v1-world-context-20260909"
ATTEMPT_ROOT = Path("/tmp/grain-traceability-v1-world-context-20260909/attempt1")
WORLD_ROOT = Path("/tmp/grain-traceability-v1-experiment-final-20260908/sealed")
QUESTIONS = REPO / "evaluation_runs/grain-traceability-v1-consumer-20260909/consumer_questions.md"
INSTRUCTION = REPO / "evaluation_runs/grain-traceability-v1-consumer-20260909/consumer_instruction.txt"
CONTEXT_ROOT = EXPERIMENT / "contexts"
MODEL = "gpt-6-astra"
REASONING = "medium"

WORLD_HASHES = {
    "OA-1": "d39faa9ed9e40b03fea7cd329033ae7756664f4dae533ff83a6c7c725006b116",
    "OA-2": "1eebe0f15eacb711080db8826d7bc2bad39da3ff28658afcfa5fb5f30da7e9d3",
}


def make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)


def copy_common(dst: Path) -> None:
    shutil.copy2(BENCHMARK / "host_visible/PURPOSE.md", dst / "PURPOSE.md")
    shutil.copy2(QUESTIONS, dst / "consumer_questions.md")
    shutil.copy2(INSTRUCTION, dst / "INSTRUCTION.md")


def prepare_workspace(world: str, condition: str, rep: int) -> Path:
    run_id = f"{world}-{condition}-{rep}"
    dst = ATTEMPT_ROOT / "workspaces" / run_id
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    copy_common(dst)
    shutil.copytree(WORLD_ROOT / world / "world", dst / "world")
    make_read_only(dst / "world")
    if condition == "SYNOPSIS":
        shutil.copy2(CONTEXT_ROOT / f"{world}-world-context.md", dst / "world-context.md")
        (dst / "world-context.md").chmod(0o444)
    return dst


def prepare_codex_home(run_id: str) -> Path:
    dst = ATTEMPT_ROOT / "codex-home" / run_id
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for name in ("auth.json", "config.toml"):
        source = Path("/home/kerem/.codex") / name
        if source.exists():
            shutil.copy2(source, dst / name)
    return dst


def bwrap_command(workspace: Path, codex_home: Path) -> list[str]:
    codex_pkg = Path("/home/kerem/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl")
    return [
        "/usr/bin/bwrap", "--unshare-all", "--share-net", "--die-with-parent",
        "--new-session", "--clearenv",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
        "--ro-bind", "/etc", "/etc", "--dev", "/dev", "--proc", "/proc",
        "--ro-bind", "/sys", "/sys", "--ro-bind", "/run/systemd/resolve", "/run/systemd/resolve",
        "--dir", "/home", "--dir", "/home/kerem", "--dir", "/codex-home",
        "--bind", str(codex_home), "/codex-home",
        "--ro-bind", str(codex_pkg), "/opt/codex-package",
        "--ro-bind", "/home/kerem/.local", "/home/kerem/.local",
        "--bind", str(workspace), "/workspace",
        "--setenv", "HOME", "/home/kerem", "--setenv", "CODEX_HOME", "/codex-home",
        "--setenv", "PATH", "/home/kerem/.local/bin:/opt/codex-package/bin:/usr/local/bin:/usr/bin:/bin",
        "--setenv", "TERM", "xterm-256color", "--setenv", "NO_COLOR", "1",
        "--chdir", "/workspace", "/opt/codex-package/bin/codex", "exec", "--json",
        "--ephemeral", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check",
        "--model", MODEL, "--config", f'reasoning_effort="{REASONING}"', "-C", "/workspace", "-",
    ]


def run_one(world: str, condition: str, rep: int) -> dict:
    run_id = f"{world}-{condition}-{rep}"
    workspace = prepare_workspace(world, condition, rep)
    codex_home = prepare_codex_home(run_id)
    out_dir = ATTEMPT_ROOT / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Read INSTRUCTION.md and answer every question in consumer_questions.md. "
        "You have only the files mounted in this workspace. Work independently, "
        "use local tools as useful, and finish with the complete answer set."
    )
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(
        bwrap_command(workspace, codex_home),
        input=prompt + "\n", text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=900, cwd=REPO,
    )
    (out_dir / "transcript.jsonl").write_text(proc.stdout, encoding="utf-8")
    (out_dir / "workspace_files.txt").write_text(
        "\n".join(str(p.relative_to(workspace)) for p in sorted(workspace.rglob("*")) if p.is_file()) + "\n",
        encoding="utf-8",
    )
    final = workspace / "final_answer.md"
    if final.exists():
        shutil.copy2(final, out_dir / "final_answer.md")
    meta = {
        "run_id": run_id, "world": world, "condition": condition, "replicate": rep,
        "world_hash": WORLD_HASHES[world], "started": started,
        "ended": datetime.now(timezone.utc).isoformat(), "exit_code": proc.returncode,
        "workspace": str(workspace), "codex_home": str(codex_home),
        "run_output": str(out_dir), "native_sources_visible": False,
        "context_visible": condition == "SYNOPSIS",
    }
    (out_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main() -> None:
    ATTEMPT_ROOT.mkdir(parents=True, exist_ok=True)
    (ATTEMPT_ROOT / "runs").mkdir(exist_ok=True)
    jobs = [(world, condition, rep) for world in ("OA-1", "OA-2")
            for condition in ("DISCOVERY", "SYNOPSIS") for rep in (1, 2, 3)]
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_one, *job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"run_id": "-".join(map(str, job)), "error": repr(exc), "job": job}
            results.append(result)
            print(json.dumps(result), flush=True)
    results.sort(key=lambda x: x.get("run_id", ""))
    (ATTEMPT_ROOT / "run_index.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
