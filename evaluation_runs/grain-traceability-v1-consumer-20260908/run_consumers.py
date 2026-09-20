"""Run isolated fresh RAW/REFERENCE/OA-1/OA-2 consumers."""

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
RUN_ROOT = Path("/tmp/grain-traceability-v1-consumer-20260908")
ATTEMPT_ROOT = RUN_ROOT / "attempt3"
WORLD_ROOT = Path("/tmp/grain-traceability-v1-experiment-final-20260908/sealed")
EVAL_ROOT = REPO / "evaluation_runs/grain-traceability-v1-consumer-20260908"
MODEL = "gpt-6-astra"
REASONING = "medium"


def copy_common(dst: Path) -> None:
    shutil.copy2(BENCHMARK / "host_visible/PURPOSE.md", dst / "PURPOSE.md")
    shutil.copy2(EVAL_ROOT / "consumer_questions.md", dst / "consumer_questions.md")
    shutil.copy2(EVAL_ROOT / "consumer_instruction.txt", dst / "INSTRUCTION.md")


def prepare_workspace(condition: str, rep: int) -> Path:
    dst = ATTEMPT_ROOT / "workspaces" / f"{condition}-{rep}"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    copy_common(dst)

    if condition == "RAW":
        shutil.copy2(BENCHMARK / "host_visible/README.md", dst / "README.md")
        shutil.copytree(BENCHMARK / "host_visible/evidence", dst / "evidence")
    elif condition == "REFERENCE":
        shutil.copytree(RUN_ROOT / "REFERENCE", dst / "reference")
    elif condition in {"OA-1", "OA-2"}:
        shutil.copytree(WORLD_ROOT / condition / "world", dst / "world")
    else:
        raise ValueError(condition)
    return dst


def prepare_codex_home(condition: str, rep: int) -> Path:
    """Provide Codex a writable home while keeping the host home hidden."""
    dst = ATTEMPT_ROOT / "codex-home" / f"{condition}-{rep}"
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
        "/usr/bin/bwrap",
        "--unshare-all",
        "--share-net",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--ro-bind", "/etc", "/etc",
        "--dev", "/dev",
        "--proc", "/proc",
        "--ro-bind", "/sys", "/sys",
        "--ro-bind", "/run/systemd/resolve", "/run/systemd/resolve",
        "--dir", "/home",
        "--dir", "/home/kerem",
        "--dir", "/codex-home",
        "--bind", str(codex_home), "/codex-home",
        "--ro-bind", str(codex_pkg), "/opt/codex-package",
        "--ro-bind", "/home/kerem/.local", "/home/kerem/.local",
        "--bind", str(workspace), "/workspace",
        "--setenv", "HOME", "/home/kerem",
        "--setenv", "CODEX_HOME", "/codex-home",
        "--setenv", "PATH", "/home/kerem/.local/bin:/opt/codex-package/bin:/usr/local/bin:/usr/bin:/bin",
        "--setenv", "TERM", "xterm-256color",
        "--setenv", "NO_COLOR", "1",
        "--chdir", "/workspace",
        "/opt/codex-package/bin/codex",
        "exec",
        "--json",
        "--ephemeral",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "--model", MODEL,
        "--config", f'reasoning_effort="{REASONING}"',
        "-C", "/workspace",
        "-",
    ]


def run_one(condition: str, rep: int) -> dict:
    workspace = prepare_workspace(condition, rep)
    codex_home = prepare_codex_home(condition, rep)
    out_dir = ATTEMPT_ROOT / "runs" / f"{condition}-{rep}"
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Read INSTRUCTION.md and answer every question in consumer_questions.md. "
        "You have only the files mounted in this workspace. Work independently, "
        "use local tools as useful, and finish with the complete answer set."
    )
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(
        bwrap_command(workspace, codex_home),
        input=prompt + "\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=900,
        cwd=REPO,
    )
    (out_dir / "transcript.jsonl").write_text(proc.stdout)
    (out_dir / "workspace_files.txt").write_text(
        "\n".join(str(p.relative_to(workspace)) for p in sorted(workspace.rglob("*")) if p.is_file()) + "\n"
    )
    final = workspace / "final_answer.md"
    if final.exists():
        shutil.copy2(final, out_dir / "final_answer.md")
    meta = {
        "condition": condition,
        "replicate": rep,
        "started": started,
        "ended": datetime.now(timezone.utc).isoformat(),
        "exit_code": proc.returncode,
        "workspace": str(workspace),
        "codex_home": str(codex_home),
        "run_output": str(out_dir),
    }
    (out_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def main() -> None:
    ATTEMPT_ROOT.mkdir(parents=True, exist_ok=True)
    (ATTEMPT_ROOT / "runs").mkdir(exist_ok=True)
    conditions = [(condition, rep) for condition in ("RAW", "REFERENCE", "OA-1", "OA-2") for rep in (1, 2)]
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_one, condition, rep): (condition, rep) for condition, rep in conditions}
        for future in as_completed(futures):
            condition, rep = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"condition": condition, "replicate": rep, "error": repr(exc)}
            results.append(result)
            print(json.dumps(result), flush=True)
    results.sort(key=lambda x: (x["condition"], x["replicate"]))
    (ATTEMPT_ROOT / "consumer_runs.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
