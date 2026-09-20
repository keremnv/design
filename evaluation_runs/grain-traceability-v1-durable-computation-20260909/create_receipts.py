from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORLD_ROOT = ROOT.parent / 'grain-traceability-v1-cursor-grok-medium-20260909/construction_runs'
BUNDLE_ROOT = ROOT / 'frozen_application_bundles'
WORLD_HASH = {
    'OA-G1': 'dc2e7e45c1327fc997691b4fa4071c5fd44edb6aed2b57e2d1e4e4c70a471eb8',
    'OA-G2': '24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220',
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def program_hash(world: str) -> str:
    items = []
    for p in sorted((BUNDLE_ROOT / world).rglob('*')):
        if p.is_file():
            items.append((str(p.relative_to(BUNDLE_ROOT / world)), hashlib.sha256(p.read_bytes()).hexdigest()))
    return canonical_hash(items)


def run_app(world: str, computation: str, params: dict, root: Path) -> tuple[int, str, object]:
    if world == 'OA-G1':
        cmd = ['python3', 'application/run.py', computation, '--params-json', json.dumps(params, separators=(',', ':')), '--world', 'world/world.sqlite']
    else:
        cmd = ['python3', 'application/run', computation, '--json', json.dumps(params, separators=(',', ':'))]
    p = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=60)
    try:
        out = json.loads(p.stdout)
    except Exception:
        out = {'stdout': p.stdout, 'stderr': p.stderr}
    return p.returncode, p.stderr, out


def parse_consumer_app_receipts(world: str, run_id: str, ended: str) -> list[dict]:
    path = ROOT / 'consumer_runs' / run_id / 'transcript.jsonl'
    records = []
    for line in path.read_text(errors='replace').splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get('type') != 'tool_call' or obj.get('subtype') != 'completed':
            continue
        for call in obj.get('tool_call', {}).values():
            if not isinstance(call, dict):
                continue
            args = call.get('args', {})
            command = args.get('command', '') if isinstance(args, dict) else ''
            if 'application/run' not in command and './application/run' not in command and '/workspace/application/run' not in command:
                continue
            result = call.get('result', {})
            raw = json.dumps(result, sort_keys=True, separators=(',', ':'))
            records.append({
                'phase': 'durable_consumer', 'run_id': run_id, 'world': world,
                'world_hash': WORLD_HASH[world], 'program_sha256': program_hash(world),
                'parameters_command': command, 'output': result, 'output_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                'execution_status': 'RECORDED', 'timestamp': ended,
            })
    return records


def main() -> None:
    receipts = []
    tasks = json.loads((ROOT / 'development_tasks.json').read_text())['tasks']
    direct = json.loads((ROOT / 'direct_computation_audit.json').read_text())['results']
    with tempfile.TemporaryDirectory(prefix='grain-durable-receipts-') as tmp:
        tmp_root = Path(tmp)
        for world in ('OA-G1', 'OA-G2'):
            run_root = tmp_root / world
            run_root.mkdir()
            import shutil
            shutil.copytree(BUNDLE_ROOT / world / 'application', run_root / 'application')
            shutil.copytree(WORLD_ROOT / world / 'grain-trace/world', run_root / 'world')
            for task in tasks:
                code, err, out = run_app(world, task['family'], task['parameters'], run_root)
                receipts.append({
                    'phase': 'development', 'run_id': f'{world}-{task["task_id"]}', 'world': world,
                    'world_hash': WORLD_HASH[world], 'program_sha256': program_hash(world),
                    'computation': task['family'], 'parameters': task['parameters'], 'output': out,
                    'output_sha256': canonical_hash(out), 'execution_status': 'SUCCESS' if code == 0 else 'ERROR',
                    'stderr': err, 'timestamp': datetime.now(timezone.utc).isoformat(),
                })
    for item in direct:
        out = item['execution']['result']
        receipts.append({
            'phase': 'direct_heldout_audit', 'run_id': f'{item["world"]}-{item["task_id"]}', 'world': item['world'],
            'world_hash': WORLD_HASH[item['world']], 'program_sha256': program_hash(item['world']),
            'computation': item['family'], 'parameters': item['parameters'], 'output': out,
            'output_sha256': canonical_hash(out), 'execution_status': 'SUCCESS' if item['execution']['exit_code'] == 0 else 'ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    for meta in json.loads((ROOT / 'consumer_run_index.json').read_text()):
        if meta['condition'] == 'DURABLE':
            receipts.extend(parse_consumer_app_receipts(meta['world'], meta['run_id'], meta['ended']))
    with (ROOT / 'execution_receipts.jsonl').open('w') as f:
        for rec in receipts:
            f.write(json.dumps(rec, sort_keys=True) + '\n')
    (ROOT / 'execution_receipts_summary.json').write_text(json.dumps({'count': len(receipts), 'by_phase': {phase: sum(1 for r in receipts if r['phase'] == phase) for phase in sorted(set(r['phase'] for r in receipts))}}, indent=2) + '\n')


if __name__ == '__main__':
    main()
