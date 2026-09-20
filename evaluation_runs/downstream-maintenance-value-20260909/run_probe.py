"""Downstream value of same-purpose World maintenance. Composer 2.5 only. No product change."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/home/kerem/Desktop/Personal Projects/generalauthor")
EXP = REPO / "evaluation_runs/downstream-maintenance-value-20260909"
EVIDENCE = REPO / "grain-traceability-v1/host_visible/evidence"
TMP = Path("/tmp/oa-downstream-maintenance-value-20260909")
SNAPSHOT = TMP / "snapshot"
WORLD = "yard-trace"
MODEL = "composer-2.5"
AUTHOR = ["uv", "run", "--directory", str(REPO), "author"]
MAINTENANCE = (
    "Answer the question and keep the existing World adequate for future work "
    "within its declared purpose. "
)


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


def world_dir(root: Path) -> Path:
    return root / ".worlds" / WORLD


def world_state(root: Path) -> dict:
    world = world_dir(root)
    names = []
    worlds = root / ".worlds"
    if worlds.is_dir():
        names = sorted(path.name for path in worlds.iterdir() if path.is_dir())
    return {
        "world_names": names,
        "purpose_sha256": _sha256(world / "PURPOSE.md"),
        "construction_sha256": _sha256(world / "construction.py"),
        "sqlite_sha256": _sha256(world / "world" / "world.sqlite"),
        "has_construction": (world / "construction.py").is_file(),
        "has_evidence": (root / "evidence").is_dir(),
        "has_purpose_md": (world / "PURPOSE.md").is_file(),
    }


def inspect_sqlite(path: Path) -> dict:
    if not path.is_file():
        return {}
    con = sqlite3.connect(path)
    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY 1"
            )
        ]
        blob = []
        for table in tables:
            try:
                rows = list(con.execute(f'SELECT * FROM "{table}"'))
            except sqlite3.Error:
                continue
            blob.append(f"{table}:{rows}")
        text = "\n".join(blob)
        unresolved = []
        if "purpose_requirement_failure" in tables:
            cols = [row[1] for row in con.execute("PRAGMA table_info(purpose_requirement_failure)")]
            for row in con.execute("SELECT * FROM purpose_requirement_failure"):
                unresolved.append(dict(zip(cols, row)))
        return {
            "tables": tables,
            "purpose_requirement_failure": unresolved,
            "hopper_named_out5002": ("WB-390" in text and "EF-18" in text and ("OUT-5002" in text or "5002" in text)),
            "unresolved_out5004": (
                "5004" in json.dumps(unresolved)
                or "no individual ticket" in text.lower()
                or "out_5004" in text.lower()
                or "hopper_no_ticket_bm-009" in text.lower()
            ),
            "control_out5001": ("PGE-OUT-5001" in text or "HFM-IN-601" in text) and "MILL-2206" in text,
        }
    finally:
        con.close()


def prepare_coarse_snapshot() -> Path:
    if TMP.exists():
        _writable(TMP)
        shutil.rmtree(TMP)
    project = TMP / "project"
    project.mkdir(parents=True)
    shutil.copy2(EXP / "project_readme.md", project / "README.md")
    shutil.copytree(EVIDENCE, project / "evidence")
    attach = run([*AUTHOR, "attach", "cursor", "--project", str(project)])
    if attach.returncode != 0:
        raise RuntimeError(attach.stdout)
    created = run([*AUTHOR, "create", WORLD, "--project", str(project)])
    if created.returncode != 0:
        raise RuntimeError(created.stdout)
    dest = world_dir(project)
    shutil.copy2(EXP / "worlds" / WORLD / "PURPOSE.md", dest / "PURPOSE.md")
    shutil.copy2(EXP / "worlds" / WORLD / "construction.py", dest / "construction.py")
    rebuilt = run([*AUTHOR, "rebuild", WORLD, "--project", str(project)], timeout=60)
    if rebuilt.returncode != 0:
        raise RuntimeError(rebuilt.stdout)
    payload = json.loads(rebuilt.stdout.strip().splitlines()[-1])
    if not payload.get("succeeded"):
        raise RuntimeError(f"{WORLD} rebuild failed: {rebuilt.stdout}")
    if SNAPSHOT.exists():
        _writable(SNAPSHOT)
        shutil.rmtree(SNAPSHOT)
    shutil.copytree(project, SNAPSHOT, symlinks=True)
    missing = [
        path
        for path in (
            SNAPSHOT / "README.md",
            SNAPSHOT / "evidence" / "bin_movements.csv",
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
    inspect = inspect_sqlite(SNAPSHOT / ".worlds" / WORLD / "world" / "world.sqlite")
    (EXP / "snapshot_inspect.json").write_text(json.dumps(inspect, indent=2) + "\n", encoding="utf-8")
    return SNAPSHOT


def copy_workspace(src: Path, dest: Path) -> Path:
    if dest.exists():
        _writable(dest)
        shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=True)
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


def parse_usage(transcript: str) -> dict | None:
    last = None
    for line in transcript.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "result" and isinstance(obj.get("usage"), dict):
            last = obj["usage"]
    return last


def extract_shell_commands(transcript: str) -> list[str]:
    commands: list[str] = []
    for line in transcript.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "tool_call" or obj.get("subtype") != "started":
            continue
        tool = obj.get("tool_call") or {}
        shell = (tool.get("shellToolCall") or {}).get("args", {}).get("command")
        if shell:
            commands.append(shell)
    return commands


def author_verbs(commands: list[str]) -> list[str]:
    seen: list[str] = []
    for command in commands:
        for verb in ("list", "rebuild", "create", "open"):
            token = f"author {verb}"
            if token in command and token not in seen:
                seen.append(token)
    return seen


def evidence_access(transcript: str, workspace: Path) -> list[str]:
    hits: list[str] = []
    needles = (
        "evidence/bin_movements",
        "evidence/operating_notes",
        "evidence/elevator_receipts",
        "/workspace/evidence",
    )
    for needle in needles:
        if needle in transcript:
            hits.append(needle)
    if (workspace / "evidence").exists():
        hits.append("evidence_dir_present")
    return hits


def save_world_bundle(workspace: Path, dest: Path) -> None:
    if dest.exists():
        _writable(dest)
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    src = world_dir(workspace)
    for name in ("PURPOSE.md", "construction.py", "diagnostics.json"):
        if (src / name).exists():
            shutil.copy2(src / name, dest / name)
    sealed = src / "world"
    if sealed.exists():
        shutil.copytree(sealed, dest / "world", symlinks=True)
    (dest / "world_state.json").write_text(json.dumps(world_state(workspace), indent=2) + "\n", encoding="utf-8")
    sqlite = src / "world" / "world.sqlite"
    inspect = inspect_sqlite(sqlite)
    (dest / "sqlite_inspect.json").write_text(json.dumps(inspect, indent=2) + "\n", encoding="utf-8")


def cursor_agent(workspace: Path, prompt: str, out: Path, timeout: int = 1500) -> dict:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    before = world_state(workspace)
    (out / "before_state.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            bwrap_command(workspace) + [prompt],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
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
    answer = workspace / "answer.md"
    if answer.exists():
        shutil.copy2(answer, out / "answer.md")
        answer.unlink()
    after = world_state(workspace)
    after["construction_changed"] = after.get("construction_sha256") != before.get("construction_sha256")
    after["purpose_changed"] = after.get("purpose_sha256") != before.get("purpose_sha256")
    after["sqlite_changed"] = after.get("sqlite_sha256") != before.get("sqlite_sha256")
    after["sqlite_inspect"] = inspect_sqlite(world_dir(workspace) / "world" / "world.sqlite")
    (out / "after_state.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    shells = extract_shell_commands(stdout)
    meta = {
        "prompt": prompt,
        "started": started.isoformat(),
        "ended": ended.isoformat(),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "workspace": str(workspace),
        "isolated": True,
        "model_requested": MODEL,
        "model_reported": parse_init_model(stdout),
        "usage": parse_usage(stdout),
        "author_commands": author_verbs(shells),
        "shell_commands": shells,
        "evidence_access": evidence_access(stdout, workspace),
        "construction_changed": after["construction_changed"],
        "purpose_changed": after["purpose_changed"],
        "sqlite_changed": after["sqlite_changed"],
        "world_names": after.get("world_names"),
        "sqlite_inspect": after.get("sqlite_inspect"),
    }
    meta["model_ok"] = meta["model_reported"] == "Composer 2.5"
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def with_maintenance(prompt: str, maintain: bool) -> str:
    if not maintain:
        return prompt
    if prompt.endswith("Write the answer to answer.md."):
        return prompt.replace(
            "Write the answer to answer.md.",
            MAINTENANCE + "Write the answer to answer.md.",
        )
    return prompt + " " + MAINTENANCE


def run_upstream(condition: str, maintain: bool, tasks: list[dict]) -> dict:
    workspace = copy_workspace(SNAPSHOT, TMP / f"condition_{condition}")
    results = []
    for task in tasks:
        out = EXP / "upstream" / condition / task["id"]
        prompt = with_maintenance(task["prompt"], maintain)
        meta = cursor_agent(workspace, prompt, out)
        meta["id"] = f"{condition}-{task['id']}"
        meta["condition"] = condition
        meta["task"] = task["id"]
        meta["maintain"] = maintain
        (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "phase": "upstream",
                    "id": meta["id"],
                    "exit_code": meta["exit_code"],
                    "model_reported": meta["model_reported"],
                    "construction_changed": meta["construction_changed"],
                    "sqlite_changed": meta["sqlite_changed"],
                    "author_commands": meta["author_commands"],
                }
            ),
            flush=True,
        )
        results.append(meta)
        if not meta["model_ok"]:
            raise RuntimeError(f"model check failed: {meta['id']} {meta['model_reported']}")
    bundle = EXP / "conditions" / condition
    save_world_bundle(workspace, bundle)
    return {
        "condition": condition,
        "maintain": maintain,
        "workspace": str(workspace),
        "tasks": results,
        "final_state": world_state(workspace),
        "final_inspect": inspect_sqlite(world_dir(workspace) / "world" / "world.sqlite"),
    }


def prepare_sealed(condition: str, task_id: str) -> Path:
    dest = Path(f"/tmp/oa-dmv-down-{condition}-{task_id}")
    if dest.exists():
        _writable(dest)
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    attach = run([*AUTHOR, "attach", "cursor", "--project", str(dest)])
    if attach.returncode != 0:
        raise RuntimeError(attach.stdout)
    shutil.copy2(EXP / "sealed_readme.md", dest / "README.md")
    sealed_src = EXP / "conditions" / condition / "world"
    sealed_dst = dest / ".worlds" / WORLD / "world"
    sealed_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sealed_src, sealed_dst, symlinks=True)
    leaked = [
        path
        for path in (
            dest / "evidence",
            dest / ".worlds" / WORLD / "construction.py",
            dest / ".worlds" / WORLD / "PURPOSE.md",
        )
        if path.exists()
    ]
    if leaked:
        raise RuntimeError("sealed workspace leaked authoring/evidence: " + ", ".join(map(str, leaked)))
    if not (sealed_dst / "world.sqlite").exists():
        raise RuntimeError(f"sealed World missing sqlite for {condition}")
    return dest


def run_downstream(condition: str, task: dict) -> dict:
    workspace = prepare_sealed(condition, task["id"])
    out = EXP / "downstream" / condition / task["id"]
    meta = cursor_agent(workspace, task["prompt"], out)
    meta["id"] = f"{condition}-{task['id']}"
    meta["condition"] = condition
    meta["task"] = task["id"]
    meta["case"] = task["case"]
    meta["gold"] = task.get("gold")
    meta["raw_evidence_unavailable"] = not (workspace / "evidence").exists()
    meta["construction_absent"] = not (world_dir(workspace) / "construction.py").exists()
    answer_text = ""
    if (out / "answer.md").exists():
        answer_text = (out / "answer.md").read_text(encoding="utf-8")
    meta["answer_text"] = answer_text
    meta["score"] = score_answer(task, answer_text)
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "phase": "downstream",
                "id": meta["id"],
                "exit_code": meta["exit_code"],
                "model_reported": meta["model_reported"],
                "score": meta["score"],
                "usage": meta["usage"],
                "evidence_access": meta["evidence_access"],
            }
        ),
        flush=True,
    )
    if not meta["model_ok"]:
        raise RuntimeError(f"model check failed: {meta['id']} {meta['model_reported']}")
    return meta


def score_answer(task: dict, answer: str) -> dict:
    text = answer or ""
    upper = text.upper()
    gold = task.get("gold") or {}
    missing = [item for item in gold.get("must_include", []) if item.upper() not in upper]
    committed = []
    for item in gold.get("must_not_commit", []):
        if item.upper() in upper:
            committed.append(item)
    refused = any(
        token in text.lower()
        for token in (
            "cannot",
            "cannot be certified",
            "not established",
            "unresolved",
            "does not establish",
            "cannot certify",
            "cannot be treated as the sole",
            "not the sole",
            "no individual",
            "do not certify",
            "cannot certify",
        )
    )
    yes_commit = any(
        token in text.lower()
        for token in (
            "can be certified",
            "is the sole",
            "is solely",
            "yes, mcr-118",
            "mcr-118 is the sole",
            "certified as the sole",
        )
    )
    if task["id"] == "D1":
        correct = not missing and "DR-44" not in committed
        unsupported = bool(committed)
    elif task["id"] == "D2":
        correct = refused and not yes_commit
        unsupported = yes_commit
    else:
        correct = not missing
        unsupported = False
    return {
        "correct": correct,
        "missing_required": missing,
        "unsupported_commitments": committed,
        "refused_or_unresolved": refused,
        "yes_commit": yes_commit,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-setup", action="store_true")
    parser.add_argument("--skip-upstream", action="store_true")
    parser.add_argument("--downstream-only", action="store_true")
    args = parser.parse_args()
    spec = json.loads((EXP / "tasks.json").read_text(encoding="utf-8"))
    EXP.mkdir(parents=True, exist_ok=True)
    if not args.skip_setup and not args.downstream_only:
        prepare_coarse_snapshot()
    elif not SNAPSHOT.exists() and not args.downstream_only:
        raise SystemExit("snapshot missing; run without --skip-setup")
    index: dict = {"upstream": [], "downstream": []}
    if not args.downstream_only:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                pool.submit(run_upstream, "A", False, spec["upstream"]): "A",
                pool.submit(run_upstream, "B", True, spec["upstream"]): "B",
            }
            upstream = []
            for future in as_completed(futures):
                upstream.append(future.result())
        upstream.sort(key=lambda item: item["condition"])
        index["upstream"] = upstream
        (EXP / "upstream_index.json").write_text(json.dumps(upstream, indent=2) + "\n", encoding="utf-8")
    downstream_jobs = []
    for condition in ("A", "B"):
        if not (EXP / "conditions" / condition / "world" / "world.sqlite").exists():
            raise SystemExit(f"condition {condition} sealed World missing")
        for task in spec["downstream"]:
            downstream_jobs.append((condition, task))
    results = []
    with ThreadPoolExecutor(max_workers=len(downstream_jobs)) as pool:
        futures = [pool.submit(run_downstream, condition, task) for condition, task in downstream_jobs]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["id"])
    index["downstream"] = results
    (EXP / "run_index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    summary = []
    for item in results:
        summary.append(
            {
                "id": item["id"],
                "case": item["case"],
                "correct": item["score"]["correct"],
                "unsupported": item["score"]["unsupported_commitments"] or item["score"]["yes_commit"],
                "usage": item["usage"],
            }
        )
    (EXP / "score_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"phase": "done", "scores": summary}), flush=True)


if __name__ == "__main__":
    main()
