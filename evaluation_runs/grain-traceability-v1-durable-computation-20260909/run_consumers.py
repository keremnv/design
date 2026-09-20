"""Run paired held-out SYNOPSIS/DURABLE consumers with Cursor/Grok."""

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
TMP_ROOT = Path("/tmp/grain-traceability-v1-durable-computation-20260909-consumers")
MODEL = "cursor-grok-4.6-medium"


def ro_tree(path: Path) -> None:
    for p in sorted(path.rglob('*'), reverse=True):
        if p.is_file():
            p.chmod(0o555 if (p.stat().st_mode & 0o111) else 0o444)
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


def prepare(world: str, condition: str, rep: int) -> Path:
    run_id = f"{world}-{condition}-{rep}"
    workspace = TMP_ROOT / "workspaces" / run_id
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "grain-traceability-v1/host_visible/PURPOSE.md", workspace / "PURPOSE.md")
    shutil.copy2(EXP / "consumer_instruction.txt", workspace / "INSTRUCTION.md")
    shutil.copy2(EXP / "evaluation_tasks.json", workspace / "evaluation_tasks.json")
    shutil.copy2(CONTEXT_ROOT / f"{world}-world-context.md", workspace / "world-context.md")
    shutil.copytree(WORLD_ROOT / world / "grain-trace/world", workspace / "world", dirs_exist_ok=True)
    ro_tree(workspace / "world")
    if condition == "DURABLE":
        shutil.copytree(EXP / "frozen_application_bundles" / world / "application", workspace / "application", dirs_exist_ok=True)
        ro_tree(workspace / "application")
    return workspace


def parse_transcript(text: str) -> dict:
    usage = None
    tool_events = []
    read_paths = []
    command_texts = []
    for line in text.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get('type') == 'result':
            usage = obj.get('usage')
        if obj.get('type') == 'tool_call' and obj.get('subtype') == 'completed':
            tool_events.append(obj)
            payload = obj.get('tool_call', {})
            for kind, call in payload.items():
                if not isinstance(call, dict):
                    continue
                args = call.get('args', {})
                if isinstance(args, dict):
                    if isinstance(args.get('path'), str):
                        read_paths.append(args['path'])
                    if isinstance(args.get('command'), str):
                        command_texts.append(args['command'])
    unique_paths = sorted(set(read_paths))
    apps = [c for c in command_texts if 'application/run' in c or 'application/run.py' in c]
    sqlite = [c for c in command_texts if 'sqlite' in c.lower() or 'python' in c.lower() and 'sqlite' in c.lower()]
    python = [c for c in command_texts if 'python' in c.lower()]
    schema = [c for c in command_texts if 'sqlite_master' in c or 'pragma' in c.lower() or '.schema' in c]
    ad_hoc = [c for c in command_texts if ('select ' in c.lower() or 'sqlite3' in c.lower()) and 'application/run' not in c]
    return {
        'usage': usage,
        'tool_actions': len(tool_events),
        'read_paths': unique_paths,
        'command_texts': command_texts,
        'application_invocations': len(apps),
        'sqlite_actions': len(sqlite),
        'python_actions': len(python),
        'schema_inspection_actions': len(schema),
        'ad_hoc_semantic_query_actions': len(ad_hoc),
        'native_source_reads': any('/workspace/evidence/' in p for p in unique_paths),
        'catalog_reads': any(p.endswith('/application/catalog.json') for p in unique_paths),
        'computation_source_reads': any('/workspace/application/' in p and not p.endswith('catalog.json') and '/manifests/' not in p for p in unique_paths),
    }


def run_one(world: str, condition: str, rep: int) -> dict:
    run_id = f"{world}-{condition}-{rep}"
    workspace = prepare(world, condition, rep)
    started = datetime.now(timezone.utc)
    prompt = "Read INSTRUCTION.md and evaluation_tasks.json. Complete every held-out task using the available workspace, then write the complete structured answer set to final_answer.md."
    proc = subprocess.run(bwrap_command(workspace), input=prompt + "\n", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1200, cwd=REPO)
    ended = datetime.now(timezone.utc)
    out = EXP / "consumer_runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcript.jsonl").write_text(proc.stdout, encoding='utf-8')
    (out / "stderr.log").write_text(proc.stderr, encoding='utf-8')
    (out / "exit_status").write_text(str(proc.returncode) + '\n', encoding='utf-8')
    final = workspace / 'final_answer.md'
    if final.exists():
        shutil.copy2(final, out / 'final_answer.md')
    (out / 'workspace_files.txt').write_text('\n'.join(str(p.relative_to(workspace)) for p in sorted(workspace.rglob('*')) if p.is_file()) + '\n', encoding='utf-8')
    telemetry = parse_transcript(proc.stdout)
    meta = {
        'run_id': run_id, 'world': world, 'condition': condition, 'replicate': rep,
        'model': MODEL, 'reasoning': 'medium', 'started': started.isoformat(), 'ended': ended.isoformat(),
        'duration_seconds': (ended - started).total_seconds(), 'exit_code': proc.returncode,
        'workspace': str(workspace), 'output': str(out), 'native_sources_visible': False,
        'telemetry': telemetry,
    }
    (out / 'run.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    return meta


def main() -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    jobs = [(w, c, r) for w in ('OA-G1', 'OA-G2') for c in ('SYNOPSIS', 'DURABLE') for r in (1, 2, 3)]
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_one, *job): job for job in jobs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
    results.sort(key=lambda x: x['run_id'])
    (EXP / 'consumer_run_index.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
