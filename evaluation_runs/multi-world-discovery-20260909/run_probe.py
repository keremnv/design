"""Build the isolated multi-World project and run Composer 2.5 consumer tasks."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/home/kerem/Desktop/Personal Projects/generalauthor")
EXP = REPO / "evaluation_runs/multi-world-discovery-20260909"
EVIDENCE = REPO / "grain-traceability-v1/host_visible/evidence"
TMP = Path("/tmp/oa-multi-world-discovery-20260909")
PROJECT = TMP / "project"
SNAPSHOT = TMP / "snapshot"
MODEL = "composer-2.5"
AUTHOR = ["uv", "run", "--directory", str(REPO), "author"]


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)


def _writable(path: Path) -> None:
    if not path.exists():
        return
    for item in sorted(path.rglob("*"), reverse=True):
        try:
            item.chmod(0o755 if item.is_dir() else 0o644)
        except OSError:
            pass
    path.chmod(0o755)


def prepare_project() -> Path:
    if TMP.exists():
        _writable(TMP)
        shutil.rmtree(TMP)
    PROJECT.mkdir(parents=True)
    shutil.copy2(EXP / "project_readme.md", PROJECT / "README.md")
    shutil.copytree(EVIDENCE, PROJECT / "evidence")
    attach = run([*AUTHOR, "attach", "cursor", "--project", str(PROJECT)])
    if attach.returncode != 0:
        raise RuntimeError(attach.stdout)
    for name in ("grain-flow", "title-custody", "lab-quality"):
        created = run([*AUTHOR, "create", name, "--project", str(PROJECT)])
        if created.returncode != 0:
            raise RuntimeError(attach.stdout + "\n" + created.stdout)
        dest = PROJECT / ".worlds" / name
        shutil.copy2(EXP / "worlds" / name / "PURPOSE.md", dest / "PURPOSE.md")
        shutil.copy2(EXP / "worlds" / name / "construction.py", dest / "construction.py")
        rebuilt = run([*AUTHOR, "rebuild", name, "--project", str(PROJECT)], timeout=60)
        if created.returncode != 0 or rebuilt.returncode != 0:
            raise RuntimeError(created.stdout + "\n" + rebuilt.stdout)
        payload = json.loads(rebuilt.stdout.strip().splitlines()[-1])
        if not payload.get("succeeded"):
            raise RuntimeError(f"{name} rebuild failed: {rebuilt.stdout}")
    listed = run([*AUTHOR, "list", "--project", str(PROJECT)])
    (EXP / "author_list.json").write_text(listed.stdout, encoding="utf-8")
    if SNAPSHOT.exists():
        _writable(SNAPSHOT)
        shutil.rmtree(SNAPSHOT)
    shutil.copytree(PROJECT, SNAPSHOT, symlinks=True)
    missing = [
        path
        for path in (
            SNAPSHOT / "README.md",
            SNAPSHOT / "evidence" / "operating_notes.md",
            SNAPSHOT / ".cursor" / "rules" / "ontology-author.mdc",
            SNAPSHOT / ".worlds" / "grain-flow" / "PURPOSE.md",
            SNAPSHOT / ".worlds" / "grain-flow" / "construction.py",
            SNAPSHOT / ".worlds" / "grain-flow" / "world" / "world.sqlite",
            SNAPSHOT / ".worlds" / "title-custody" / "PURPOSE.md",
            SNAPSHOT / ".worlds" / "lab-quality" / "PURPOSE.md",
        )
        if not path.exists()
    ]
    if missing:
        raise RuntimeError("snapshot missing files: " + ", ".join(str(path) for path in missing))
    return PROJECT


def copy_for_task(task_id: str) -> Path:
    dest = Path(f"/tmp/oa-mwd-isolated-{task_id}")
    if dest.exists():
        _writable(dest)
        shutil.rmtree(dest)
    shutil.copytree(SNAPSHOT, dest, symlinks=True)
    return dest


def bwrap_command(workspace: Path) -> list[str]:
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
        "--dir", "/home/kerem/.config",
        "--dir", "/home/kerem/.config/cursor",
        "--ro-bind", "/home/kerem/.local", "/home/kerem/.local",
        "--ro-bind", "/home/kerem/.config/cursor/auth.json", "/home/kerem/.config/cursor/auth.json",
        "--ro-bind", "/home/kerem/miniconda3", "/home/kerem/miniconda3",
        "--tmpfs", "/tmp",
        "--bind", str(workspace), "/workspace",
        "--setenv", "HOME", "/home/kerem",
        "--setenv", "PATH", "/home/kerem/.local/bin:/home/kerem/miniconda3/bin:/usr/local/bin:/usr/bin:/bin",
        "--setenv", "TERM", "xterm-256color",
        "--setenv", "NO_COLOR", "1",
        "--chdir", "/workspace",
        "/home/kerem/.local/bin/cursor-agent",
        "-p",
        "--yolo",
        "--trust",
        "--sandbox",
        "disabled",
        "--model",
        MODEL,
        "--output-format",
        "stream-json",
        "--workspace",
        "/workspace",
    ]


def parse_init_model(transcript: str) -> str | None:
    for line in transcript.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "system" and obj.get("subtype") == "init":
            return str(obj.get("model") or "")
    return None


def run_task(task: dict) -> dict:
    workspace = copy_for_task(task["id"])
    out = EXP / "consumer_runs" / task["id"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    prompt = task["prompt"]
    started = datetime.now(timezone.utc)
    proc = subprocess.run(
        bwrap_command(workspace) + [prompt],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=1500,
        cwd=REPO,
    )
    ended = datetime.now(timezone.utc)
    (out / "transcript.jsonl").write_text(proc.stdout, encoding="utf-8")
    (out / "stderr_combined.txt").write_text(proc.stdout[-20000:], encoding="utf-8")
    model = parse_init_model(proc.stdout)
    answer = workspace / "answer.md"
    if answer.exists():
        shutil.copy2(answer, out / "answer.md")
    meta = {
        "id": task["id"],
        "relevant_world": task["relevant_world"],
        "probe": task["probe"],
        "prompt": prompt,
        "started": started.isoformat(),
        "ended": ended.isoformat(),
        "exit_code": proc.returncode,
        "workspace": str(workspace),
        "isolated": True,
        "model_requested": MODEL,
        "model_reported": model,
        "model_ok": model == "Composer 2.5" if model else False,
    }
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"id": task["id"], "exit": proc.returncode, "model": model}), flush=True)
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-setup", action="store_true")
    parser.add_argument("--tasks", nargs="*")
    args = parser.parse_args()
    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "consumer_runs").mkdir(exist_ok=True)
    if not args.skip_setup:
        prepare_project()
    elif not SNAPSHOT.exists():
        raise SystemExit("snapshot missing; run without --skip-setup")
    tasks = json.loads((EXP / "tasks.json").read_text(encoding="utf-8"))["tasks"]
    if args.tasks:
        wanted = set(args.tasks)
        tasks = [task for task in tasks if task["id"] in wanted]
    results = [run_task(task) for task in tasks]
    index_path = EXP / "run_index.json"
    existing = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    by_id = {item["id"]: item for item in existing if "id" in item}
    for item in results:
        by_id[item["id"]] = item
    index = [by_id[key] for key in sorted(by_id)]
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    failed_models = [item for item in results if not item.get("model_ok")]
    if failed_models:
        raise SystemExit(f"model check failed: {failed_models}")


if __name__ == "__main__":
    main()
