"""Isolated same-purpose refinement probe. Composer 2.5 only. Does not change the product."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/home/kerem/Desktop/Personal Projects/generalauthor")
EXP = REPO / "evaluation_runs/same-purpose-refinement-20260909"
EVIDENCE = REPO / "grain-traceability-v1/host_visible/evidence"
TMP = Path("/tmp/oa-same-purpose-refinement-20260909")
PROJECT = TMP / "project"
SNAPSHOT = TMP / "snapshot"
WORLD = "yard-trace"
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


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def world_state(root: Path) -> dict:
    world = root / ".worlds" / WORLD
    names = []
    worlds_dir = root / ".worlds"
    if worlds_dir.is_dir():
        names = sorted(path.name for path in worlds_dir.iterdir() if path.is_dir())
    return {
        "world_names": names,
        "purpose_sha256": _sha256(world / "PURPOSE.md"),
        "construction_sha256": _sha256(world / "construction.py"),
        "sqlite_sha256": _sha256(world / "world" / "world.sqlite"),
        "diagnostics_exists": (world / "diagnostics.json").is_file(),
    }


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
    created = run([*AUTHOR, "create", WORLD, "--project", str(PROJECT)])
    if created.returncode != 0:
        raise RuntimeError(created.stdout)
    dest = PROJECT / ".worlds" / WORLD
    shutil.copy2(EXP / "worlds" / WORLD / "PURPOSE.md", dest / "PURPOSE.md")
    shutil.copy2(EXP / "worlds" / WORLD / "construction.py", dest / "construction.py")
    rebuilt = run([*AUTHOR, "rebuild", WORLD, "--project", str(PROJECT)], timeout=60)
    if rebuilt.returncode != 0:
        raise RuntimeError(rebuilt.stdout)
    payload = json.loads(rebuilt.stdout.strip().splitlines()[-1])
    if not payload.get("succeeded"):
        raise RuntimeError(f"{WORLD} rebuild failed: {rebuilt.stdout}")
    (EXP / "author_list.json").write_text(
        run([*AUTHOR, "list", "--project", str(PROJECT)]).stdout,
        encoding="utf-8",
    )
    if SNAPSHOT.exists():
        _writable(SNAPSHOT)
        shutil.rmtree(SNAPSHOT)
    shutil.copytree(PROJECT, SNAPSHOT, symlinks=True)
    missing = [
        path
        for path in (
            SNAPSHOT / "README.md",
            SNAPSHOT / "evidence" / "bin_movements.csv",
            SNAPSHOT / "evidence" / "operating_notes.md",
            SNAPSHOT / ".cursor" / "rules" / "ontology-author.mdc",
            SNAPSHOT / ".worlds" / WORLD / "PURPOSE.md",
            SNAPSHOT / ".worlds" / WORLD / "construction.py",
            SNAPSHOT / ".worlds" / WORLD / "world" / "world.sqlite",
        )
        if not path.exists()
    ]
    if missing:
        raise RuntimeError("snapshot missing files: " + ", ".join(str(path) for path in missing))
    (EXP / "snapshot_state.json").write_text(json.dumps(world_state(SNAPSHOT), indent=2) + "\n", encoding="utf-8")
    return PROJECT


def copy_for_task(task_id: str) -> Path:
    dest = Path(f"/tmp/oa-spr-isolated-{task_id}")
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


def capture_after(workspace: Path, out: Path, before: dict) -> dict:
    after = world_state(workspace)
    after_dir = out / "after"
    after_dir.mkdir(exist_ok=True)
    world = workspace / ".worlds" / WORLD
    for name in ("PURPOSE.md", "construction.py", "diagnostics.json"):
        source = world / name
        if source.exists():
            shutil.copy2(source, after_dir / name)
    sqlite = world / "world" / "world.sqlite"
    if sqlite.exists():
        (after_dir / "world.sqlite.sha256").write_text(after["sqlite_sha256"] + "\n", encoding="utf-8")
    after["construction_changed"] = after.get("construction_sha256") != before.get("construction_sha256")
    after["purpose_changed"] = after.get("purpose_sha256") != before.get("purpose_sha256")
    after["sqlite_changed"] = after.get("sqlite_sha256") != before.get("sqlite_sha256")
    after["created_other_worlds"] = after.get("world_names") != [WORLD]
    (out / "after_state.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    return after


def run_task(task: dict) -> dict:
    workspace = copy_for_task(task["id"])
    before = world_state(workspace)
    out = EXP / "consumer_runs" / task["id"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "before_state.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    prompt = task["prompt"]
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            bwrap_command(workspace) + [prompt],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1500,
            cwd=REPO,
        )
        stdout = proc.stdout
        exit_code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        exit_code = 124
        timed_out = True
    ended = datetime.now(timezone.utc)
    (out / "transcript.jsonl").write_text(stdout, encoding="utf-8")
    model = parse_init_model(stdout)
    answer = workspace / "answer.md"
    if answer.exists():
        shutil.copy2(answer, out / "answer.md")
    after = capture_after(workspace, out, before)
    meta = {
        "id": task["id"],
        "case": task["case"],
        "prompt": prompt,
        "started": started.isoformat(),
        "ended": ended.isoformat(),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "workspace": str(workspace),
        "isolated": True,
        "model_requested": MODEL,
        "model_reported": model,
        "model_ok": model == "Composer 2.5" if model else False,
        "construction_changed": after["construction_changed"],
        "purpose_changed": after["purpose_changed"],
        "sqlite_changed": after["sqlite_changed"],
        "created_other_worlds": after["created_other_worlds"],
        "world_names": after.get("world_names"),
    }
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("id", "exit_code", "model_reported", "construction_changed", "sqlite_changed", "created_other_worlds")}), flush=True)
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
