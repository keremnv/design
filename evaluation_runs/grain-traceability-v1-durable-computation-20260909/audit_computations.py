"""Run the frozen computation bundles on evaluator-only held-out parameters."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORLD_ROOT = ROOT.parent / "grain-traceability-v1-cursor-grok-medium-20260909/construction_runs"
AUTHOR_ROOT = ROOT / "frozen_application_bundles"
TASKS = json.loads((ROOT / "evaluation_tasks.json").read_text())['tasks']
GOLD = {x['task_id']: x for x in json.loads((ROOT / "gold.json").read_text())['answers']}


def ro_tree(path: Path) -> None:
    for p in sorted(path.rglob('*'), reverse=True):
        if p.is_file():
            p.chmod(0o444)
        elif p.is_dir():
            p.chmod(0o555)


def run_bundle(world: str, task: dict, root: Path) -> dict:
    family = task['family']
    computation = family
    params = task['parameters']
    if world == 'OA-G1':
        cmd = ['python3', 'application/run.py', computation, '--params-json', json.dumps(params, separators=(',', ':')), '--world', 'world/world.sqlite']
    else:
        cmd = ['python3', 'application/run', computation, '--json', json.dumps(params, separators=(',', ':'))]
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=60)
    result = None
    if proc.stdout.strip():
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result = {'_stdout': proc.stdout}
    return {'exit_code': proc.returncode, 'stderr': proc.stderr, 'result': result, 'command': cmd}


def classify(task: dict, raw: dict) -> str:
    if raw['exit_code'] != 0 or not isinstance(raw['result'], dict):
        return 'NOT_COVERED'
    result = raw['result']
    if isinstance(result.get('result'), dict):
        result = result['result']
    text = json.dumps(result, sort_keys=True)
    def has_all(*values: str) -> bool:
        return all(value in text for value in values)
    def field_values(name: str) -> list[str]:
        value = result.get(name, [])
        if isinstance(value, list):
            return [x if isinstance(x, str) else json.dumps(x, sort_keys=True) for x in value]
        return [value] if isinstance(value, str) else []
    # Classification is conservative and checks the required semantic consequence,
    # not byte-level output shape.
    tid = task['task_id']
    if tid == 'EVAL-SRC-001':
        ok = has_all('WB-390', 'EF-18') and ('quantity_allocation_established": false' in text or 'source_allocation_unresolved": true' in text or 'unresolved' in text.lower())
    elif tid == 'EVAL-SRC-002':
        ok = str(result.get('source_allocation_unresolved', result.get('allocation_status', ''))).lower() not in {'false', 'resolved'} and not result.get('established_contributing_identities', result.get('contributors', []))
    elif tid == 'EVAL-SRC-003':
        vals = set(result.get('established_contributing_identities', result.get('contributors', [])))
        ok = not vals or vals == {'MCR-118', 'S-52'}
    elif tid == 'EVAL-PROV-001':
        up = result.get('upstream', result)
        ok = 'PGE-OUT-5002' in json.dumps(up) and has_all('FEED-2207') and 'established_named_tickets' in text
    elif tid == 'EVAL-PROV-002':
        ok = 'PGE-OUT-5004' in json.dumps(result) and 'HFM-IN-604' in json.dumps(result) and ('FEED' not in json.dumps(result) or result.get('processing') in (None, {}, []))
    elif tid == 'EVAL-CUST-001':
        owner = json.dumps(result.get('owner', result.get('recorded_owner')))
        custodian = json.dumps(result.get('custodian', result.get('recorded_custodian')))
        ok = 'GrainLink Merchants' in owner and 'Northstar Bulk Transport' in custodian
    elif tid == 'EVAL-CUST-002':
        owner = json.dumps(result.get('owner', result.get('recorded_owner')))
        custodian = json.dumps(result.get('custodian', result.get('recorded_custodian')))
        ok = 'East Fork Co-op' in owner and 'Prairie Gate Elevator' in custodian
    elif tid == 'EVAL-INSP-001':
        ok = all(x in text for x in ('PGE-OUT-5002', 'HFM-IN-602', 'FEED-2207')) and ('unresolved' in text.lower() or 'allocation' in text.lower())
    elif tid == 'EVAL-INSP-002':
        ok = 'PGE-OUT-5004' in text and 'HFM-IN-604' in text and 'FEED' not in text
    elif tid == 'EVAL-INSP-003':
        lower = text.lower()
        ok = 'n3' in lower or 'unresolved' in lower or 'not established' in lower
    else:
        ok = False
    if ok:
        return 'DIRECTLY_SUPPORTED'
    if tid == 'EVAL-PROV-001' and 'PGE-OUT-5002' in text and 'FEED-2207' in text:
        return 'SUPPORTED_VIA_COMPOSITION'
    if tid == 'EVAL-INSP-001' and 'HFM-IN-602' in text:
        return 'SUPPORTED_VIA_COMPOSITION'
    return 'NOT_COVERED'


def main() -> None:
    all_results = []
    with tempfile.TemporaryDirectory(prefix='grain-durable-audit-') as tmp:
        tmp_root = Path(tmp)
        for world in ('OA-G1', 'OA-G2'):
            run_root = tmp_root / world
            run_root.mkdir()
            shutil.copytree(AUTHOR_ROOT / world / 'application', run_root / 'application')
            shutil.copytree(WORLD_ROOT / world / 'grain-trace/world', run_root / 'world')
            ro_tree(run_root / 'application')
            ro_tree(run_root / 'world')
            for task in TASKS:
                raw = run_bundle(world, task, run_root)
                all_results.append({
                    'world': world,
                    'task_id': task['task_id'],
                    'family': task['family'],
                    'parameters': task['parameters'],
                    'classification': classify(task, raw),
                    'execution': raw,
                })
    (ROOT / 'direct_computation_audit.json').write_text(json.dumps({'results': all_results}, indent=2) + '\n')


if __name__ == '__main__':
    main()
