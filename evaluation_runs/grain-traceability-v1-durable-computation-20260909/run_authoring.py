"""Run isolated Cursor/Grok durable-computation authoring hosts."""

from __future__ import annotations

import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/home/kerem/Desktop/Personal Projects/generalauthor")
EXP = REPO / "evaluation_runs/grain-traceability-v1-durable-computation-20260909"
WORLD_ROOT = REPO / "evaluation_runs/grain-traceability-v1-cursor-grok-medium-20260909/construction_runs"
CONTEXT_ROOT = REPO / "evaluation_runs/grain-traceability-v1-cursor-grok-medium-20260909/world_context/contexts"
TMP_ROOT = Path("/tmp/grain-traceability-v1-durable-computation-20260909-authoring")
MODEL = "cursor-grok-4.6-medium"


AUTHORING_INSTRUCTION = """Build a small reusable set of deterministic application computations that supports the supplied development workload over this sealed World.

The computations must accept parameters rather than encode individual task answers and must operate only on the sealed World. You may inspect and query the World freely and choose any SQL/Python structure that is useful. Produce the smallest reusable application interface that captures computations worth reusing across similar future requests.

Create an application/ directory containing executable entrypoints, machine-readable manifests, and a compact catalog. Every computation must be deterministic, parameterized, bound to this World, and callable without reading its source code. It may use only the World and supplied parameters: no native evidence, network, LLM, or World mutation.

Use the development tasks to exercise the interface. Do not look for or assume any held-out tasks or gold. Finish by writing AUTHORING_REPORT.md describing the interface and tests you performed. The final durable output is the application/ directory.
"""


def ro_tree(path: Path) -> None:
    for p in sorted(path.rglob("*"), reverse=True):
        if p.is_file():
            p.chmod(0o444)
        elif p.is_dir():
            p.chmod(0o555)


def bwrap_command(workspace: Path) -> list[str]:
    return [
        "/usr/bin/bwrap", "--unshare-all", "--share-net", "--die-with-parent",
        "--new-session", "--clearenv",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
        "--ro-bind", "/etc", "/etc", "--dev", "/dev", "--proc", "/proc",
        "--ro-bind", "/sys", "/sys", "--ro-bind", "/run/systemd/resolve", "/run/systemd/resolve",
        "--dir", "/home", "--dir", "/home/kerem",
        "--ro-bind", "/home/kerem/.local", "/home/kerem/.local",
        "--dir", "/home/kerem/.config", "--dir", "/home/kerem/.config/cursor",
        "--ro-bind", "/home/kerem/.config/cursor/auth.json", "/home/kerem/.config/cursor/auth.json",
        "--bind", str(workspace), "/workspace",
        "--setenv", "HOME", "/home/kerem",
        "--setenv", "PATH", "/home/kerem/.local/bin:/usr/local/bin:/usr/bin:/bin",
        "--setenv", "TERM", "xterm-256color", "--setenv", "NO_COLOR", "1",
        "--chdir", "/workspace",
        "/home/kerem/.local/bin/agent", "-p", "--yolo",
        "--model", MODEL, "--output-format", "stream-json", "--workspace", "/workspace",
    ]


def prepare(world: str) -> Path:
    workspace = TMP_ROOT / "workspaces" / world
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    shutil.copytree(WORLD_ROOT / world / "grain-trace/world", workspace / "world")
    ro_tree(workspace / "world")
    shutil.copy2(CONTEXT_ROOT / f"{world}-world-context.md", workspace / "world-context.md")
    shutil.copy2(EXP / "development_tasks.json", workspace / "development_tasks.json")
    shutil.copy2(REPO / "grain-traceability-v1/host_visible/PURPOSE.md", workspace / "PURPOSE.md")
    (workspace / "INSTRUCTION.md").write_text(AUTHORING_INSTRUCTION, encoding="utf-8")
    return workspace


def usage_events(lines: list[str]) -> list[dict]:
    events = []
    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "result" or "usage" in obj:
            events.append(obj)
    return events


def run_one(world: str) -> dict:
    workspace = prepare(world)
    started = datetime.now(timezone.utc)
    prompt = "Read INSTRUCTION.md, PURPOSE.md, world-context.md, and development_tasks.json. Build and test the reusable application computation bundle now."
    proc = subprocess.run(
        bwrap_command(workspace), input=prompt + "\n", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1200, cwd=REPO,
    )
    ended = datetime.now(timezone.utc)
    out = EXP / "application_authoring" / world
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "transcript.jsonl").write_text(proc.stdout, encoding="utf-8")
    (out / "stderr.log").write_text(proc.stderr, encoding="utf-8")
    (out / "exit_status").write_text(str(proc.returncode) + "\n", encoding="utf-8")
    files = []
    for p in sorted(workspace.rglob("*")):
        if p.is_file():
            files.append(str(p.relative_to(workspace)))
    (out / "workspace_files.txt").write_text("\n".join(files) + "\n", encoding="utf-8")
    if (workspace / "application").exists():
        shutil.copytree(workspace / "application", out / "application")
    for name in ("AUTHORING_REPORT.md",):
        if (workspace / name).exists():
            shutil.copy2(workspace / name, out / name)
    meta = {
        "run_id": world,
        "world": world,
        "model": MODEL,
        "reasoning": "medium",
        "started": started.isoformat(),
        "ended": ended.isoformat(),
        "duration_seconds": (ended - started).total_seconds(),
        "exit_code": proc.returncode,
        "workspace": str(workspace),
        "output": str(out),
        "stream_usage_events": usage_events(proc.stdout.splitlines()),
    }
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main() -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(run_one, world): world for world in ("OA-G1", "OA-G2")}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
    results.sort(key=lambda x: x["world"])
    (EXP / "application_authoring" / "run_index.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
